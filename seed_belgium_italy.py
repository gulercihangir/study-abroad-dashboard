"""
Seeds the database with a set of Belgian and Italian universities and their
programs (admission requirements). Safe to re-run — skips any university that
already exists by name, and skips any program that already exists for that
university by major.

Application deadlines, admission-test requirements, and cost estimates below
are starting points based on general knowledge of each institution and should
be verified against the university's own admissions page before being relied
on by students — use the admin panel or the CSV import tool to correct any
entry once verified.

Usage:
    venv/Scripts/python.exe seed_belgium_italy.py
"""

from app import app, db, University, Program

UNIVERSITIES = [
    # ─── Belgium ────────────────────────────────────────────────────────────
    {
        "name": "KU Leuven",
        "country": "Belgium",
        "city": "Leuven",
        "region": "Flemish Brabant",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 650.0,
        "transport_score": 7,
        "website_url": "https://www.kuleuven.be/english",
        "teaching_style": "Lecture-based with strong research integration, seminar discussion groups",
        "career_focus": "Strong ties to European engineering, tech, and finance employers, active alumni network",
        "campus_type": "medium",
        "social_scene": "Historic student town with a large international student population and active student clubs",
        "programs": [
            {
                "major": "Business Engineering",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Strong secondary school math grades; English proficiency (IELTS 6.5+ or equivalent)",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Computer Science",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math; prior programming exposure recommended",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Ghent University",
        "country": "Belgium",
        "city": "Ghent",
        "region": "East Flanders",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 650.0,
        "transport_score": 7,
        "website_url": "https://www.ugent.be/en",
        "teaching_style": "Mix of lectures and lab-based coursework, research-driven faculty",
        "career_focus": "Solid regional industry ties in biotech, engineering, and the public sector",
        "campus_type": "medium",
        "social_scene": "Compact historic city center with a lively student population",
        "programs": [
            {
                "major": "Economics",
                "application_deadline": "1 June 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math recommended",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Biomedical Sciences",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Strong secondary school biology and chemistry grades",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Université libre de Bruxelles",
        "country": "Belgium",
        "city": "Brussels",
        "region": "Brussels-Capital",
        "cost_of_living_monthly": 360.0,
        "rent_estimate_monthly": 900.0,
        "transport_score": 9,
        "website_url": "https://www.ulb.be/en",
        "teaching_style": "Lecture-based with seminar discussion; mostly French-medium with growing English-taught tracks",
        "career_focus": "Close to EU institutions and international organizations, strong for policy and business careers",
        "campus_type": "large_urban",
        "social_scene": "International capital-city setting with a large expat and diplomatic community",
        "programs": [
            {
                "major": "International Business",
                "application_deadline": "31 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "English or French proficiency depending on the program track",
                "required_documents": "Diploma, transcript, motivation letter, language test score",
            },
            {
                "major": "Political Science",
                "application_deadline": "31 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school humanities/social science background recommended",
                "required_documents": "Diploma, transcript, motivation letter",
            },
        ],
    },
    {
        "name": "Vrije Universiteit Brussel",
        "country": "Belgium",
        "city": "Brussels",
        "region": "Brussels-Capital",
        "cost_of_living_monthly": 360.0,
        "rent_estimate_monthly": 900.0,
        "transport_score": 9,
        "website_url": "https://www.vub.be/en",
        "teaching_style": "English-taught international programs, project-based coursework",
        "career_focus": "Strong tech and engineering placement, EU-adjacent policy and business network",
        "campus_type": "large_urban",
        "social_scene": "Diverse international student body in a multicultural capital city",
        "programs": [
            {
                "major": "Computer Science",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math; programming exposure helpful",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Business Engineering",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Strong secondary school math grades",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    # ─── Italy ──────────────────────────────────────────────────────────────
    {
        "name": "Politecnico di Milano",
        "country": "Italy",
        "city": "Milan",
        "region": "Lombardy",
        "cost_of_living_monthly": 380.0,
        "rent_estimate_monthly": 950.0,
        "transport_score": 8,
        "website_url": "https://www.polimi.it/en",
        "teaching_style": "Rigorous lecture and lab-based engineering curriculum with project work",
        "career_focus": "Top-tier engineering employer ties across Italy and Europe, strong design/tech crossover",
        "campus_type": "large_urban",
        "social_scene": "Fast-paced international city with a large exchange and international student community",
        "programs": [
            {
                "major": "Computer Science and Engineering",
                "application_deadline": "Admission test — check current cycle",
                "numerus_fixus": "yes",
                "prerequisites": "Strong secondary school math grades; admission test required",
                "required_documents": "Diploma, transcript, motivation letter, English test score, admission test result",
            },
            {
                "major": "Management Engineering",
                "application_deadline": "Admission test — check current cycle",
                "numerus_fixus": "yes",
                "prerequisites": "Strong secondary school math grades; admission test required",
                "required_documents": "Diploma, transcript, motivation letter, English test score, admission test result",
            },
        ],
    },
    {
        "name": "Bocconi University",
        "country": "Italy",
        "city": "Milan",
        "region": "Lombardy",
        "cost_of_living_monthly": 380.0,
        "rent_estimate_monthly": 950.0,
        "transport_score": 8,
        "website_url": "https://www.unibocconi.eu",
        "teaching_style": "English-taught, case-study and seminar-heavy business curriculum",
        "career_focus": "Elite finance and consulting placement across Europe, strong on-campus corporate recruiting",
        "campus_type": "medium",
        "social_scene": "Selective, career-focused student body with an active international exchange network",
        "programs": [
            {
                "major": "Economics and Management",
                "application_deadline": "Rolling rounds — check current cycle",
                "numerus_fixus": "yes",
                "prerequisites": "Strong academic record; Bocconi admission test or SAT/ACT",
                "required_documents": "Diploma, transcript, motivation letter, admission test score, English test score",
            },
            {
                "major": "International Business",
                "application_deadline": "Rolling rounds — check current cycle",
                "numerus_fixus": "yes",
                "prerequisites": "Strong academic record; admission test required",
                "required_documents": "Diploma, transcript, motivation letter, admission test score, English test score",
            },
        ],
    },
    {
        "name": "Sapienza Università di Roma",
        "country": "Italy",
        "city": "Rome",
        "region": "Lazio",
        "cost_of_living_monthly": 320.0,
        "rent_estimate_monthly": 800.0,
        "transport_score": 6,
        "website_url": "https://www.uniroma1.it/en",
        "teaching_style": "Large lecture-based courses with a growing number of English-taught programs",
        "career_focus": "Broad public and private sector ties across central Italy",
        "campus_type": "large_urban",
        "social_scene": "One of Europe's largest universities, set in a major historic capital city",
        "programs": [
            {
                "major": "Engineering",
                "application_deadline": "Admission test — check current cycle",
                "numerus_fixus": "yes",
                "prerequisites": "Strong secondary school math and physics grades; entrance test required",
                "required_documents": "Diploma, transcript, English test score, admission test result",
            },
            {
                "major": "Economics",
                "application_deadline": "1 June 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math recommended",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Università di Bologna",
        "country": "Italy",
        "city": "Bologna",
        "region": "Emilia-Romagna",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 650.0,
        "transport_score": 7,
        "website_url": "https://www.unibo.it/en",
        "teaching_style": "Historic academic tradition mixing lecture and seminar formats",
        "career_focus": "Strong regional employer network plus growing international program placement",
        "campus_type": "medium",
        "social_scene": "Large, lively student population that shapes the whole city's culture",
        "programs": [
            {
                "major": "International Business and Management",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Strong academic record; English test required",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Computer Science",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math recommended",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
]


def seed():
    with app.app_context():
        created_unis = 0
        created_programs = 0

        for uni_data in UNIVERSITIES:
            programs_data = uni_data.pop("programs")
            university = University.query.filter_by(name=uni_data["name"]).first()

            if not university:
                university = University(**uni_data)
                db.session.add(university)
                db.session.flush()
                created_unis += 1

            for prog_data in programs_data:
                exists = Program.query.filter_by(
                    university_id=university.id, major=prog_data["major"]
                ).first()
                if not exists:
                    db.session.add(Program(university_id=university.id, **prog_data))
                    created_programs += 1

        db.session.commit()
        print(f"Done. Added {created_unis} new universities and {created_programs} new programs.")
        print(f"Totals now: {University.query.count()} universities, {Program.query.count()} programs.")


if __name__ == "__main__":
    seed()
