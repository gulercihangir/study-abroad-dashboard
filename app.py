import os
import csv
import io
import secrets
from functools import wraps
from datetime import datetime, timedelta
import requests
import resend
from google import genai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)

default_sqlite_path = os.path.join(BASE_DIR, "instance", "universities.db")
database_url = os.environ.get("DATABASE_URL", f"sqlite:///{default_sqlite_path}")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-to-something-random")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB per upload
db = SQLAlchemy(app)

ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}


def allowed_document(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_DOCUMENT_EXTENSIONS


def student_upload_dir(student_id):
    path = os.path.join(app.instance_path, "uploads", str(student_id))
    os.makedirs(path, exist_ok=True)
    return path

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

gemini_client = genai.Client()
resend.api_key = os.environ.get("RESEND_API_KEY")
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL")

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
    social_scene = db.Column(db.Text)

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


class Consultant(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)

    students = db.relationship("Student", backref="consultant", lazy=True, foreign_keys="Student.consultant_id")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def verify_reset_token(self, token):
        return (
            self.reset_token == token
            and self.reset_token_expiry
            and self.reset_token_expiry > datetime.utcnow()
        )

    def get_id(self):
        return f"c-{self.id}"

    def __repr__(self):
        return f"{self.name} ({self.email})"


class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    consultant_id = db.Column(db.Integer, db.ForeignKey("consultant.id"), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def verify_reset_token(self, token):
        return (
            self.reset_token == token
            and self.reset_token_expiry
            and self.reset_token_expiry > datetime.utcnow()
        )

    def get_id(self):
        return f"s-{self.id}"

    def __repr__(self):
        return f"{self.name} ({self.email})"


class ConsultationLead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    message = db.Column(db.Text)
    program_interest = db.Column(db.String(300))
    submitted_at = db.Column(db.DateTime, server_default=db.func.now())

    student = db.relationship("Student", backref="consultation_leads")

    def __repr__(self):
        return f"{self.name} ({self.email})"


class SavedAnswers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    major = db.Column(db.String(200))
    max_budget = db.Column(db.Float)
    region = db.Column(db.String(200))
    learning_style = db.Column(db.String(50))
    career_goal = db.Column(db.String(50))
    campus_type = db.Column(db.String(50))
    social_scene = db.Column(db.String(50))
    priority_major = db.Column(db.Float)
    priority_cost = db.Column(db.Float)
    priority_region = db.Column(db.Float)
    diploma_type = db.Column(db.String(50))
    saved_at = db.Column(db.DateTime, server_default=db.func.now())

    student = db.relationship("Student", backref="saved_answers")

    def __repr__(self):
        return f"{self.major} for {self.student.name if self.student else '?'}"


class ChecklistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    done = db.Column(db.Boolean, default=False)
    visible_to_student = db.Column(db.Boolean, default=True)
    due_date = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    student = db.relationship("Student", backref="checklist_items")

    def __repr__(self):
        return self.title


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())

    student = db.relationship("Student", backref="documents")

    def __repr__(self):
        return self.original_filename


@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("s-"):
        return Student.query.get(int(user_id[2:]))
    if user_id.startswith("c-"):
        return Consultant.query.get(int(user_id[2:]))
    return None


def consultant_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(*args, **kwargs):
        if not isinstance(current_user, Consultant):
            return redirect("/")
        return view_func(*args, **kwargs)
    return wrapper


def student_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(*args, **kwargs):
        if not isinstance(current_user, Student):
            return redirect("/")
        return view_func(*args, **kwargs)
    return wrapper


class ConsultantAccessMixin:
    def is_accessible(self):
        return isinstance(current_user, Consultant) and current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect("/consultant/login")


class SecureAdminIndexView(ConsultantAccessMixin, AdminIndexView):
    pass


class SecureModelView(ConsultantAccessMixin, ModelView):
    pass


class UniversityAdmin(ConsultantAccessMixin, ModelView):
    form_choices = {
        "campus_type": [
            ("large_urban", "Large urban university"),
            ("medium", "Mid-size campus"),
            ("small_liberal", "Small liberal arts college"),
            ("online", "Online or hybrid"),
        ],
        "social_scene": [
            ("lively", "Lively & social"),
            ("moderate", "Balanced"),
            ("quiet", "Quiet & studious"),
        ],
    }
    column_list = ["name", "city", "region", "cost_of_living_monthly", "rent_estimate_monthly", "campus_type", "social_scene"]
    form_excluded_columns = ["programs"]


class ProgramAdmin(ConsultantAccessMixin, ModelView):
    form_choices = {
        "numerus_fixus": [
            ("yes", "Yes — restricted enrollment"),
            ("no", "No — open enrollment"),
        ]
    }
    column_list = ["major", "university", "application_deadline", "numerus_fixus"]


class StudentAdmin(ConsultantAccessMixin, ModelView):
    column_list = ["name", "email", "consultant", "created_at"]
    form_columns = ["name", "email", "consultant"]


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

SOCIAL_SCENE_KEYWORDS = {
    "lively": ["lively", "vibrant", "nightlife", "student associations", "party", "social"],
    "quiet": ["quiet", "studious", "calm", "peaceful", "academic focus"],
}


def score_program(program, university, answers):
    reasons = []
    scores = {}

    desired_major = (answers.get("major") or "").strip().lower()
    program_major = (program.major or "").lower()
    if desired_major and desired_major == program_major:
        scores["major"] = 100
        reasons.append(f"Exact match for '{answers.get('major')}'")
    elif desired_major and desired_major in program_major:
        scores["major"] = 60
        reasons.append(f"'{answers.get('major')}' is part of this program, but it's not a dedicated program")
    else:
        scores["major"] = 0
        reasons.append(f"Could not confirm this program matches '{answers.get('major')}'")

    try:
        budget = float(answers.get("max_budget", 0) or 0)
    except (ValueError, TypeError):
        budget = 0
    total_cost = (university.cost_of_living_monthly or 0) + (university.rent_estimate_monthly or 0)
    if budget > 0 and total_cost > 0:
        if total_cost <= budget:
            savings_ratio = (budget - total_cost) / budget
            scores["cost"] = 65 + min(savings_ratio * 35, 35)
            reasons.append(f"Estimated monthly cost (€{total_cost:.0f}) fits within your €{budget:.0f} budget")
        else:
            over_ratio = (total_cost - budget) / budget
            penalty = min(over_ratio * 100, 65)
            scores["cost"] = max(65 - penalty, 0)
            reasons.append(f"Estimated monthly cost (€{total_cost:.0f}) exceeds your €{budget:.0f} budget")
    else:
        scores["cost"] = 50
        reasons.append("Cost data incomplete for this university")

    preferred_region = (answers.get("region") or "").strip().lower()
    uni_region = (university.region or "").lower()
    if not preferred_region or preferred_region == "no preference":
        scores["region"] = 100
        reasons.append("No region preference specified")
    elif preferred_region in uni_region:
        scores["region"] = 100
        reasons.append(f"Located in your preferred region ({university.region})")
    else:
        scores["region"] = 20
        reasons.append(f"Located in {university.region}, outside your stated preference")

    transport = university.transport_score or 5
    scores["transport"] = transport * 10
    reasons.append(f"Transport accessibility score: {transport}/10")

    learning_style = answers.get("learning_style")
    if learning_style:
        keywords = TEACHING_STYLE_KEYWORDS.get(learning_style, [])
        text = (university.teaching_style or "").lower()
        if any(kw in text for kw in keywords):
            scores["teaching_style"] = 100
            reasons.append("Matches your preferred learning style")
        else:
            scores["teaching_style"] = 30
            reasons.append("Could not confirm a match for your learning style preference")
    else:
        scores["teaching_style"] = 100
        reasons.append("No learning style preference specified")

    career_goal = answers.get("career_goal")
    if career_goal:
        keywords = CAREER_FOCUS_KEYWORDS.get(career_goal, [])
        text = (university.career_focus or "").lower()
        if any(kw in text for kw in keywords):
            scores["career_focus"] = 100
            reasons.append("Matches your career goal")
        else:
            scores["career_focus"] = 30
            reasons.append("Could not confirm a match for your stated career goal")
    else:
        scores["career_focus"] = 100
        reasons.append("No career goal specified")

    campus_pref = (answers.get("campus_type") or "").strip().lower()
    uni_campus = (university.campus_type or "").strip().lower()
    if not campus_pref:
        scores["campus_type"] = 100
        reasons.append("No campus environment preference specified")
    elif campus_pref == uni_campus:
        scores["campus_type"] = 100
        reasons.append("Matches your preferred campus environment")
    else:
        scores["campus_type"] = 30
        reasons.append("Different campus environment than your preference")

    social_pref = answers.get("social_scene")
    if social_pref and social_pref != "no_preference":
        keywords = SOCIAL_SCENE_KEYWORDS.get(social_pref, [])
        text = (university.social_scene or "").lower()
        if any(kw in text for kw in keywords):
            scores["social_scene"] = 100
            reasons.append("Matches your preferred student-life vibe")
        else:
            scores["social_scene"] = 40
            reasons.append("Could not confirm a match for your preferred student-life vibe")
    else:
        scores["social_scene"] = 100
        reasons.append("No student-life preference specified")

    fixed_dims = ["transport", "teaching_style", "career_focus", "campus_type", "social_scene"]
    fixed_weight_each = 40 / len(fixed_dims)

    try:
        p_major = float(answers.get("priority_major", 5) or 5)
        p_cost = float(answers.get("priority_cost", 5) or 5)
        p_region = float(answers.get("priority_region", 5) or 5)
    except (ValueError, TypeError):
        p_major, p_cost, p_region = 5, 5, 5

    slider_sum = p_major + p_cost + p_region
    if slider_sum <= 0:
        p_major, p_cost, p_region, slider_sum = 1, 1, 1, 3

    weight_major = 60 * (p_major / slider_sum)
    weight_cost = 60 * (p_cost / slider_sum)
    weight_region = 60 * (p_region / slider_sum)

    total_score = (
        scores["major"] * (weight_major / 100)
        + scores["cost"] * (weight_cost / 100)
        + scores["region"] * (weight_region / 100)
        + sum(scores[d] * (fixed_weight_each / 100) for d in fixed_dims)
    )

    return {"program": program, "university": university, "score": round(total_score, 1), "reasons": reasons}


@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/find-university")
def home():
    return render_template("index.html")


@app.route("/api/find-universities", methods=["POST"])
def find_universities():
    answers = request.json
    programs = Program.query.options(joinedload(Program.university)).all()

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


@app.route("/api/save-answers", methods=["POST"])
@login_required
def save_answers():
    data = request.json
    saved = SavedAnswers(
        student_id=current_user.id,
        major=data.get("major"),
        max_budget=data.get("max_budget"),
        region=data.get("region"),
        learning_style=data.get("learning_style"),
        career_goal=data.get("career_goal"),
        campus_type=data.get("campus_type"),
        social_scene=data.get("social_scene"),
        priority_major=data.get("priority_major"),
        priority_cost=data.get("priority_cost"),
        priority_region=data.get("priority_region"),
        diploma_type=data.get("diploma_type"),
    )
    db.session.add(saved)
    db.session.commit()
    return jsonify({"status": "saved"})


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


@app.route("/api/consultation-interest", methods=["POST"])
def consultation_interest():
    data = request.json
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    program_interest = (data.get("program_interest") or "").strip()

    if not name or not email:
        return jsonify({"error": "Please provide your name and email."}), 400

    lead = ConsultationLead(
        name=name,
        email=email,
        message=message,
        program_interest=program_interest,
        student_id=current_user.id if current_user.is_authenticated and isinstance(current_user, Student) else None,
    )
    db.session.add(lead)
    db.session.commit()

    if resend.api_key and NOTIFICATION_EMAIL:
        try:
            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": NOTIFICATION_EMAIL,
                "subject": f"New consultation interest: {name}",
                "html": f"""
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Interested program:</strong> {program_interest or 'Not specified'}</p>
                    <p><strong>Message:</strong> {message or '(none)'}</p>
                """,
            })
        except Exception as e:
            print("Email notification failed (lead was still saved):", e)

    return jsonify({"status": "received"})


# ─── Student auth ───────────────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="Please fill in all fields.")

        if Student.query.filter_by(email=email).first():
            return render_template("register.html", error="An account with this email already exists.")

        student = Student(name=name, email=email)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()

        login_user(student)
        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        student = Student.query.filter_by(email=email).first()
        if student and student.check_password(password):
            login_user(student)
            return redirect("/")

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        student = Student.query.filter_by(email=email).first()

        if student:
            token = student.generate_reset_token()
            db.session.commit()
            reset_url = f"{request.host_url}reset-password/{token}"

            if resend.api_key:
                try:
                    resend.Emails.send({
                        "from": "onboarding@resend.dev",
                        "to": student.email,
                        "subject": "Reset your password",
                        "html": f"<p>Click to reset your password (expires in 1 hour):</p><p><a href='{reset_url}'>{reset_url}</a></p>",
                    })
                except Exception as e:
                    print("Password reset email failed:", e)

        return render_template("student_forgot_password.html", message="If that email is registered, a reset link has been sent.")

    return render_template("student_forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    student = Student.query.filter_by(reset_token=token).first()

    if not student or not student.verify_reset_token(token):
        return render_template("student_reset_password.html", error="This reset link is invalid or has expired.", invalid=True)

    if request.method == "POST":
        password = request.form.get("password", "")
        if not password:
            return render_template("student_reset_password.html", error="Please enter a new password.", token=token)

        student.set_password(password)
        student.reset_token = None
        student.reset_token_expiry = None
        db.session.commit()
        return redirect("/login")

    return render_template("student_reset_password.html", token=token)


# ─── Consultant password reset ──────────────────────────────────────────────

@app.route("/consultant/forgot-password", methods=["GET", "POST"])
def consultant_forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        consultant = Consultant.query.filter_by(email=email).first()

        if consultant:
            token = consultant.generate_reset_token()
            db.session.commit()
            reset_url = f"{request.host_url}consultant/reset-password/{token}"

            if resend.api_key:
                try:
                    resend.Emails.send({
                        "from": "onboarding@resend.dev",
                        "to": consultant.email,
                        "subject": "Reset your password",
                        "html": f"<p>Click to reset your password (expires in 1 hour):</p><p><a href='{reset_url}'>{reset_url}</a></p>",
                    })
                except Exception as e:
                    print("Password reset email failed:", e)

        return render_template("consultant_forgot_password.html", message="If that email is registered, a reset link has been sent.")

    return render_template("consultant_forgot_password.html")


@app.route("/consultant/reset-password/<token>", methods=["GET", "POST"])
def consultant_reset_password(token):
    consultant = Consultant.query.filter_by(reset_token=token).first()

    if not consultant or not consultant.verify_reset_token(token):
        return render_template("consultant_reset_password.html", error="This reset link is invalid or has expired.", invalid=True)

    if request.method == "POST":
        password = request.form.get("password", "")
        if not password:
            return render_template("consultant_reset_password.html", error="Please enter a new password.", token=token)

        consultant.set_password(password)
        consultant.reset_token = None
        consultant.reset_token_expiry = None
        db.session.commit()
        return redirect("/consultant/login")

    return render_template("consultant_reset_password.html", token=token)


# ─── Consultant auth + dashboard ────────────────────────────────────────────

DUE_DATE_FORMATS = ("%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y")


def parse_due_date(due_date_str):
    if not due_date_str:
        return None
    for fmt in DUE_DATE_FORMATS:
        try:
            return datetime.strptime(due_date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def get_consultant_overview(consultant):
    students = Student.query.filter_by(consultant_id=consultant.id).order_by(Student.name.asc()).all()
    student_ids = [s.id for s in students]

    if not student_ids:
        return [], {"total_students": 0, "profiles_completed": 0, "checklists_complete": 0, "due_this_week": 0}

    profile_student_ids = {
        row[0] for row in
        db.session.query(SavedAnswers.student_id)
        .filter(SavedAnswers.student_id.in_(student_ids))
        .distinct()
    }

    checklist_counts = {
        student_id: (total, done or 0)
        for student_id, total, done in (
            db.session.query(
                ChecklistItem.student_id,
                db.func.count(ChecklistItem.id),
                db.func.sum(db.case((ChecklistItem.done.is_(True), 1), else_=0)),
            )
            .filter(ChecklistItem.student_id.in_(student_ids))
            .group_by(ChecklistItem.student_id)
        )
    }

    undone_items = ChecklistItem.query.filter(
        ChecklistItem.student_id.in_(student_ids), ChecklistItem.done.is_(False)
    ).all()
    week_from_now = datetime.utcnow() + timedelta(days=7)
    due_this_week = sum(
        1 for item in undone_items
        if (due := parse_due_date(item.due_date)) and datetime.utcnow() <= due <= week_from_now
    )

    student_cards = []
    profiles_completed = 0
    checklists_complete = 0

    for student in students:
        has_profile = student.id in profile_student_ids
        checklist_total, checklist_done = checklist_counts.get(student.id, (0, 0))

        if has_profile:
            profiles_completed += 1
        if checklist_total > 0 and checklist_done == checklist_total:
            checklists_complete += 1

        student_cards.append({
            "student": student,
            "has_profile": has_profile,
            "checklist_total": checklist_total,
            "checklist_done": checklist_done,
        })

    stats = {
        "total_students": len(students),
        "profiles_completed": profiles_completed,
        "checklists_complete": checklists_complete,
        "due_this_week": due_this_week,
    }

    return student_cards, stats


@app.route("/consultant/register", methods=["GET", "POST"])
def consultant_register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("consultant_register.html", error="Please fill in all fields.")

        if Consultant.query.filter_by(email=email).first():
            return render_template("consultant_register.html", error="An account with this email already exists.")

        consultant = Consultant(name=name, email=email)
        consultant.set_password(password)
        db.session.add(consultant)
        db.session.commit()

        login_user(consultant)
        return redirect("/consultant/dashboard")

    return render_template("consultant_register.html")


@app.route("/consultant/login", methods=["GET", "POST"])
def consultant_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        consultant = Consultant.query.filter_by(email=email).first()
        if consultant and consultant.check_password(password):
            login_user(consultant)
            return redirect("/consultant/dashboard")

        return render_template("consultant_login.html", error="Invalid email or password.")

    return render_template("consultant_login.html")


@app.route("/consultant/logout")
@login_required
def consultant_logout():
    logout_user()
    return redirect("/consultant/login")


@app.route("/consultant/dashboard")
@consultant_required
def consultant_dashboard():
    student_cards, stats = get_consultant_overview(current_user)
    return render_template("consultant_dashboard.html", student_cards=student_cards, stats=stats, active_student_id=None)


@app.route("/consultant/student/<int:student_id>", methods=["GET", "POST"])
@consultant_required
def consultant_student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    if student.consultant_id != current_user.id:
        return "Not authorized to view this student.", 403

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        due_date = request.form.get("due_date", "").strip()
        if title:
            item = ChecklistItem(student_id=student.id, title=title, due_date=due_date, visible_to_student=True)
            db.session.add(item)
            db.session.commit()
        return redirect(f"/consultant/student/{student_id}")

    latest_profile = (
        SavedAnswers.query.filter_by(student_id=student.id)
        .order_by(SavedAnswers.saved_at.desc())
        .first()
    )
    checklist = ChecklistItem.query.filter_by(student_id=student.id).order_by(ChecklistItem.created_at.asc()).all()
    documents = Document.query.filter_by(student_id=student.id).order_by(Document.uploaded_at.desc()).all()

    student_cards, stats = get_consultant_overview(current_user)

    return render_template(
        "consultant_student_detail.html",
        student=student,
        profile=latest_profile,
        checklist=checklist,
        documents=documents,
        student_cards=student_cards,
        stats=stats,
        active_student_id=student.id,
    )


@app.route("/consultant/checklist/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle_checklist_item(item_id):
    if not isinstance(current_user, Consultant):
        return jsonify({"error": "Not authorized"}), 403

    item = ChecklistItem.query.get_or_404(item_id)
    if item.student.consultant_id != current_user.id:
        return jsonify({"error": "Not authorized"}), 403

    item.done = not item.done
    db.session.commit()
    return jsonify({"status": "ok", "done": item.done})


@app.route("/consultant/checklist/<int:item_id>/visibility", methods=["POST"])
@login_required
def toggle_checklist_visibility(item_id):
    if not isinstance(current_user, Consultant):
        return jsonify({"error": "Not authorized"}), 403

    item = ChecklistItem.query.get_or_404(item_id)
    if item.student.consultant_id != current_user.id:
        return jsonify({"error": "Not authorized"}), 403

    item.visible_to_student = not item.visible_to_student
    db.session.commit()
    return jsonify({"status": "ok", "visible_to_student": item.visible_to_student})


# ─── Student's own checklist view ───────────────────────────────────────────

@app.route("/my-checklist")
@student_required
def my_checklist():
    items = (
        ChecklistItem.query.filter_by(student_id=current_user.id, visible_to_student=True)
        .order_by(ChecklistItem.created_at.asc())
        .all()
    )
    return render_template("my_checklist.html", items=items)


# ─── Student's own documents ─────────────────────────────────────────────────

@app.route("/my-documents", methods=["GET", "POST"])
@student_required
def my_documents():
    error = None
    if request.method == "POST":
        file = request.files.get("document")
        if not file or not file.filename:
            error = "Choose a file first."
        elif not allowed_document(file.filename):
            error = "Unsupported file type. Allowed: PDF, DOC, DOCX, JPG, PNG."
        else:
            ext = file.filename.rsplit(".", 1)[1].lower()
            stored_name = f"{secrets.token_hex(16)}.{ext}"
            file.save(os.path.join(student_upload_dir(current_user.id), stored_name))
            db.session.add(Document(
                student_id=current_user.id,
                filename=stored_name,
                original_filename=secure_filename(file.filename),
            ))
            db.session.commit()
            return redirect("/my-documents")

    documents = (
        Document.query.filter_by(student_id=current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return render_template("my_documents.html", documents=documents, error=error)


@app.route("/my-documents/<int:doc_id>/delete", methods=["POST"])
@student_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.student_id != current_user.id:
        return "Not authorized", 403

    path = os.path.join(student_upload_dir(doc.student_id), doc.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(doc)
    db.session.commit()
    return redirect("/my-documents")


@app.route("/documents/<int:doc_id>/download")
@login_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if isinstance(current_user, Student):
        if doc.student_id != current_user.id:
            return "Not authorized", 403
    elif isinstance(current_user, Consultant):
        if doc.student.consultant_id != current_user.id:
            return "Not authorized", 403
    else:
        return redirect("/")

    return send_from_directory(
        student_upload_dir(doc.student_id),
        doc.filename,
        as_attachment=True,
        download_name=doc.original_filename,
    )


# ─── Bulk university import/export (consultant only) ───────────────────────

UNIVERSITY_CSV_COLUMNS = [
    "action", "university_name", "city", "region", "cost_of_living_monthly",
    "rent_estimate_monthly", "transport_score", "website_url", "teaching_style",
    "career_focus", "campus_type", "social_scene", "major", "application_deadline",
    "numerus_fixus", "prerequisites", "required_documents",
]


@app.route("/consultant/universities-template.csv")
@consultant_required
def universities_csv_template():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=UNIVERSITY_CSV_COLUMNS)
    writer.writeheader()
    writer.writerow({
        "action": "", "university_name": "Erasmus Universiteit Rotterdam", "city": "Rotterdam",
        "region": "Zuid-Holland", "cost_of_living_monthly": "2000", "rent_estimate_monthly": "1250",
        "transport_score": "9", "website_url": "https://www.eur.nl/en",
        "teaching_style": "Problem-based learning, small group work, collaborative seminars",
        "career_focus": "Strong industry ties in finance and consulting, active career services, internship placements",
        "campus_type": "large_urban",
        "social_scene": "Lively student associations and a vibrant nightlife scene close to campus",
        "major": "Business Administration", "application_deadline": "1 May 2026",
        "numerus_fixus": "yes", "prerequisites": "Strong secondary school math grades; English proficiency (IELTS 6.5+)",
        "required_documents": "Diploma, transcript, motivation letter, CV, English test score",
    })
    writer.writerow({
        "action": "delete", "university_name": "Old University To Remove", "city": "", "region": "",
        "cost_of_living_monthly": "", "rent_estimate_monthly": "", "transport_score": "", "website_url": "",
        "teaching_style": "", "career_focus": "", "campus_type": "", "social_scene": "",
        "major": "", "application_deadline": "", "numerus_fixus": "", "prerequisites": "", "required_documents": "",
    })

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=universities_template.csv"},
    )


def _parse_float(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_int(value):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


@app.route("/consultant/import-universities", methods=["GET", "POST"])
@consultant_required
def import_universities():
    if request.method != "POST":
        return render_template("import_universities.html")

    file = request.files.get("csv_file")
    if not file or not file.filename:
        return render_template("import_universities.html", error="Choose a CSV file first.")
    if not file.filename.lower().endswith(".csv"):
        return render_template("import_universities.html", error="File must be a .csv (in Excel/Sheets: File → Download/Export → CSV).")

    try:
        raw = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return render_template("import_universities.html", error="Could not read the file — save it as UTF-8 CSV and try again.")

    reader = csv.DictReader(io.StringIO(raw))
    if "university_name" not in (reader.fieldnames or []):
        return render_template(
            "import_universities.html",
            error="Missing required column: university_name. Download the template to see the expected format.",
        )

    universities_created = 0
    universities_updated = 0
    programs_created = 0
    programs_updated = 0
    deleted_count = 0
    errors = []

    for i, row in enumerate(reader, start=2):  # row 1 is the header
        name = (row.get("university_name") or "").strip()
        if not name:
            errors.append(f"Row {i}: missing university_name, skipped.")
            continue

        action = (row.get("action") or "").strip().lower()
        major = (row.get("major") or "").strip()

        if action == "delete":
            university = University.query.filter_by(name=name).first()
            if not university:
                errors.append(f"Row {i}: '{name}' not found, nothing to delete.")
                continue
            if major:
                program = Program.query.filter_by(university_id=university.id, major=major).first()
                if program:
                    db.session.delete(program)
                    deleted_count += 1
                else:
                    errors.append(f"Row {i}: program '{major}' not found at '{name}'.")
            else:
                db.session.delete(university)  # cascades to its programs
                deleted_count += 1
            continue

        university = University.query.filter_by(name=name).first()
        uni_fields = {
            "city": (row.get("city") or "").strip() or None,
            "region": (row.get("region") or "").strip() or None,
            "cost_of_living_monthly": _parse_float(row.get("cost_of_living_monthly")),
            "rent_estimate_monthly": _parse_float(row.get("rent_estimate_monthly")),
            "transport_score": _parse_int(row.get("transport_score")),
            "website_url": (row.get("website_url") or "").strip() or None,
            "teaching_style": (row.get("teaching_style") or "").strip() or None,
            "career_focus": (row.get("career_focus") or "").strip() or None,
            "campus_type": (row.get("campus_type") or "").strip() or None,
            "social_scene": (row.get("social_scene") or "").strip() or None,
        }

        if not university:
            university = University(name=name, **uni_fields)
            db.session.add(university)
            db.session.flush()
            universities_created += 1
        else:
            for field, value in uni_fields.items():
                if value is not None:
                    setattr(university, field, value)
            universities_updated += 1

        if major:
            program = Program.query.filter_by(university_id=university.id, major=major).first()
            prog_fields = {
                "application_deadline": (row.get("application_deadline") or "").strip() or None,
                "numerus_fixus": (row.get("numerus_fixus") or "").strip().lower() or None,
                "prerequisites": (row.get("prerequisites") or "").strip() or None,
                "required_documents": (row.get("required_documents") or "").strip() or None,
            }
            if not program:
                db.session.add(Program(university_id=university.id, major=major, **prog_fields))
                programs_created += 1
            else:
                for field, value in prog_fields.items():
                    if value is not None:
                        setattr(program, field, value)
                programs_updated += 1

    db.session.commit()

    summary = (
        f"{universities_created} universities added, {universities_updated} updated — "
        f"{programs_created} programs added, {programs_updated} updated — {deleted_count} deleted."
    )
    return render_template("import_universities.html", summary=summary, errors=errors)


admin = Admin(
    app,
    name="Study Abroad Dashboard Admin",
    theme=Bootstrap4Theme(swatch="darkly"),
    index_view=SecureAdminIndexView(),
)
admin.add_view(UniversityAdmin(University, db.session))
admin.add_view(ProgramAdmin(Program, db.session))
admin.add_view(SecureModelView(ConsultationLead, db.session))
admin.add_view(StudentAdmin(Student, db.session))
admin.add_view(SecureModelView(Consultant, db.session))
admin.add_view(SecureModelView(SavedAnswers, db.session))
admin.add_view(SecureModelView(ChecklistItem, db.session))
admin.add_view(SecureModelView(Document, db.session))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)