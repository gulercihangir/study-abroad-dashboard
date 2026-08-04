import os
import requests
from google import genai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme

load_dotenv()

app = Flask(__name__)
database_url = os.environ.get("DATABASE_URL", "sqlite:///universities.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-to-something-random")
db = SQLAlchemy(app)

gemini_client = genai.Client()  # reads GEMINI_API_KEY from .env automatically

_COST_OF_LIVING_CACHE = None


def get_cost_of_living_data():
    global _COST_OF_LIVING_CACHE
    if _COST_OF_LIVING_CACHE is not None:
        return _COST_OF_LIVING_CACHE
    try:
        response = requests.get("https://getwherenext.com/api/data/cost-of-living", timeout=5)
        response.raise_for_status()
        _COST_OF_LIVING_CACHE = response.json()
        return _COST_OF_LIVING_CACHE
    except requests.RequestException as e:
        print("Could not fetch cost-of-living data:", e)
        return None


def get_purchasing_power_context(country_name="Netherlands"):
    col_data = get_cost_of_living_data()
    if not col_data or "data" not in col_data:
        return None
    for country in col_data["data"]:
        if country.get("country", "").lower() == country_name.lower():
            return {
                "country": country["country"],
                "cost_index": country["cost_index"],
                "monthly_estimate_usd": country["monthly_estimate_usd"],
                "grocery_index": country["grocery_index"],
                "rent_index": country["rent_index"],
                "utilities_index": country["utilities_index"],
                "transport_index": country["transport_index"],
                "source": "WhereNext (getwherenext.com), based on World Bank ICP data, CC BY 4.0",
            }
    return None


def evaluate_motivation_letter(letter_text):
    """
    Gives GENERAL, first-look feedback only — structure, clarity, completeness.
    Deliberately not a deep, personalized, application-specific review —
    that's reserved for the paid consulting service.
    Uses Gemini (gemini-2.5-flash) — check aistudio.google.com for current
    free-tier model eligibility if you swap the model name later.
    """
    prompt = f"""You are giving a student general, first-look feedback on their university
motivation letter / personal statement draft. This is a light structural and clarity
check, NOT a deep personalized review.

Evaluate the letter below and give feedback in 4 short sections:
1. Structure — does it have a clear introduction, body, and conclusion?
2. Clarity — is the writing clear and well-organized?
3. Completeness — does it address: why this field of study, relevant motivation/experience, and future goals?
4. One or two general suggestions for improvement

Keep the tone constructive and encouraging. Do not rewrite the letter. Do not invent
facts about the student. Keep the whole response under 300 words.

Letter:
{letter_text}
"""
    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )
    return response.text


# ─── Models ─────────────────────────────────────────────────────────────────

class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100))
    region = db.Column(db.String(100))
    cost_of_living_monthly = db.Column(db.Float)
    rent_estimate_monthly = db.Column(db.Float)
    transport_score = db.Column(db.Integer)
    website_url = db.Column(db.String(300))
    teaching_style = db.Column(db.Text)
    career_focus = db.Column(db.Text)
    campus_type = db.Column(db.String(50))

    programs = db.relationship("Program", backref="university", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return self.name


class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey("university.id"), nullable=False)
    major = db.Column(db.String(200), nullable=False)
    application_deadline = db.Column(db.String(50))
    numerus_fixus = db.Column(db.String(10))
    prerequisites = db.Column(db.Text)
    required_documents = db.Column(db.Text)

    def __repr__(self):
        return f"{self.major} @ {self.university.name if self.university else '?'}"


class UniversityAdmin(ModelView):
    form_choices = {
        "campus_type": [
            ("large_urban", "Large urban university"),
            ("medium", "Mid-size campus"),
            ("small_liberal", "Small liberal arts college"),
            ("online", "Online or hybrid"),
        ]
    }
    column_list = ["name", "city", "region", "cost_of_living_monthly", "rent_estimate_monthly", "campus_type"]
    form_excluded_columns = ["programs"]


class ProgramAdmin(ModelView):
    form_choices = {
        "numerus_fixus": [
            ("yes", "Yes — restricted enrollment"),
            ("no", "No — open enrollment"),
        ]
    }
    column_list = ["major", "university", "application_deadline", "numerus_fixus"]


TEACHING_STYLE_KEYWORDS = {
    "hands_on": ["hands-on", "hands on", "project-based", "labs", "practical"],
    "lectures": ["lecture", "theory", "theoretical", "academic rigor"],
    "collaborative": ["group work", "team", "collaborative", "seminar"],
    "self_paced": ["independent", "self-paced", "research-driven", "autonomous"],
}

CAREER_FOCUS_KEYWORDS = {
    "industry": ["industry", "corporate", "company", "job market", "employers"],
    "academia": ["research", "graduate school", "phd", "academic career"],
    "entrepreneurship": ["entrepreneur", "startup", "incubator", "innovation"],
    "public_service": ["public sector", "government", "ngo", "nonprofit", "social impact"],
}


def score_program(program, university, answers):
    score = 0
    max_score = 0
    reasons = []

    max_score += 25
    desired_major = (answers.get("major") or "").strip().lower()
    program_major = (program.major or "").lower()
    if desired_major and desired_major == program_major:
        score += 25
        reasons.append(f"Exact match for '{answers.get('major')}'")
    elif desired_major and desired_major in program_major:
        score += 15
        reasons.append(f"'{answers.get('major')}' is part of this program, but it's not a dedicated program")
    else:
        reasons.append(f"Could not confirm this program matches '{answers.get('major')}'")

    max_score += 20
    try:
        budget = float(answers.get("max_budget", 0) or 0)
    except (ValueError, TypeError):
        budget = 0
    total_cost = (university.cost_of_living_monthly or 0) + (university.rent_estimate_monthly or 0)

    if budget > 0 and total_cost > 0:
        if total_cost <= budget:
            savings_ratio = (budget - total_cost) / budget
            score += 13 + min(savings_ratio * 7, 7)
            reasons.append(f"Estimated monthly cost (€{total_cost:.0f}) fits within your €{budget:.0f} budget")
        else:
            over_ratio = (total_cost - budget) / budget
            penalty = min(over_ratio * 20, 20)
            score += max(13 - penalty, 0)
            reasons.append(f"Estimated monthly cost (€{total_cost:.0f}) exceeds your €{budget:.0f} budget")
    else:
        reasons.append("Cost data incomplete for this university")

    max_score += 10
    preferred_region = (answers.get("region") or "").strip().lower()
    uni_region = (university.region or "").lower()
    if not preferred_region or preferred_region == "no preference":
        score += 10
        reasons.append("No region preference specified")
    elif preferred_region in uni_region:
        score += 10
        reasons.append(f"Located in your preferred region ({university.region})")
    else:
        reasons.append(f"Located in {university.region}, outside your stated preference")

    max_score += 15
    transport = university.transport_score or 5
    score += (transport / 10) * 15
    reasons.append(f"Transport accessibility score: {transport}/10")

    max_score += 10
    learning_style = answers.get("learning_style")
    if learning_style:
        keywords = TEACHING_STYLE_KEYWORDS.get(learning_style, [])
        text = (university.teaching_style or "").lower()
        if any(kw in text for kw in keywords):
            score += 10
            reasons.append("Matches your preferred learning style")
        else:
            reasons.append("Could not confirm a match for your learning style preference")
    else:
        score += 10
        reasons.append("No learning style preference specified")

    max_score += 10
    career_goal = answers.get("career_goal")
    if career_goal:
        keywords = CAREER_FOCUS_KEYWORDS.get(career_goal, [])
        text = (university.career_focus or "").lower()
        if any(kw in text for kw in keywords):
            score += 10
            reasons.append("Matches your career goal")
        else:
            reasons.append("Could not confirm a match for your stated career goal")
    else:
        score += 10
        reasons.append("No career goal specified")

    max_score += 10
    campus_pref = (answers.get("campus_type") or "").strip().lower()
    uni_campus = (university.campus_type or "").strip().lower()
    if not campus_pref:
        score += 10
        reasons.append("No campus environment preference specified")
    elif campus_pref == uni_campus:
        score += 10
        reasons.append("Matches your preferred campus environment")
    else:
        reasons.append("Different campus environment than your preference")

    percentage_score = round((score / max_score) * 100, 1) if max_score else 0

    return {"program": program, "university": university, "score": percentage_score, "reasons": reasons}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/find-universities", methods=["POST"])
def find_universities():
    answers = request.json
    programs = Program.query.all()

    results = [score_program(p, p.university, answers) for p in programs]
    results.sort(key=lambda r: r["score"], reverse=True)
    top_matches = results[:5]

    return jsonify({
        "results": [
            {
                "university_name": r["university"].name,
                "program_name": r["program"].major,
                "city": r["university"].city,
                "region": r["university"].region,
                "score": r["score"],
                "reasons": r["reasons"],
                "website_url": r["university"].website_url,
                "cost_of_living_monthly": r["university"].cost_of_living_monthly,
                "rent_estimate_monthly": r["university"].rent_estimate_monthly,
                "application_deadline": r["program"].application_deadline,
                "numerus_fixus": r["program"].numerus_fixus,
                "prerequisites": r["program"].prerequisites,
            }
            for r in top_matches
        ],
        "purchasing_power": get_purchasing_power_context("Netherlands"),
    })


@app.route("/api/evaluate-letter", methods=["POST"])
def evaluate_letter():
    data = request.json
    letter_text = (data.get("letter_text") or "").strip()

    if not letter_text:
        return jsonify({"error": "No letter text provided"}), 400
    if len(letter_text) < 50:
        return jsonify({"error": "Letter seems too short to evaluate meaningfully — paste a fuller draft."}), 400

    try:
        feedback = evaluate_motivation_letter(letter_text)
        return jsonify({"feedback": feedback})
    except Exception as e:
        print("Error evaluating letter:", e)
        return jsonify({"error": "Something went wrong generating feedback. Check your API key and try again."}), 500


admin = Admin(app, name="Study Abroad Dashboard Admin", theme=Bootstrap4Theme())
admin.add_view(UniversityAdmin(University, db.session))
admin.add_view(ProgramAdmin(Program, db.session))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)