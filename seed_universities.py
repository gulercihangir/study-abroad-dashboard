"""
Seeds the database with a broader set of Dutch universities and their programs
(admission requirements). Safe to re-run — skips any university that already
exists by name, and skips any program that already exists for that university
by major.

Usage:
    venv/Scripts/python.exe seed_universities.py
"""

from app import app, db, University, Program

UNIVERSITIES = [
    {
        "name": "Erasmus Universiteit Rotterdam",
        "city": "Rotterdam",
        "region": "Zuid-Holland",
        "cost_of_living_monthly": 2000.0,
        "rent_estimate_monthly": 1250.0,
        "transport_score": 9,
        "website_url": "https://www.eur.nl/en",
        "teaching_style": "Problem-based learning, small group work, collaborative seminars",
        "career_focus": "Strong industry ties in finance and consulting, active career services, internship placements",
        "campus_type": "large_urban",
        "social_scene": "Lively student associations and a vibrant nightlife scene close to campus",
        "programs": [
            {
                "major": "Business Administration",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Strong secondary school math grades; English proficiency (IELTS 6.5+)",
                "required_documents": "Diploma, transcript, motivation letter, CV, English test score",
            },
            {
                "major": "Economics",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math (advanced level recommended)",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Technische Universiteit Delft",
        "city": "Delft",
        "region": "Zuid-Holland",
        "cost_of_living_monthly": 1900.0,
        "rent_estimate_monthly": 1100.0,
        "transport_score": 8,
        "website_url": "https://www.tudelft.nl/en",
        "teaching_style": "Hands-on labs, project-based learning, practical engineering studios",
        "career_focus": "Deep industry partnerships in engineering and tech, strong job market outcomes with major employers",
        "campus_type": "medium",
        "social_scene": "Balanced mix of academic focus and active student associations",
        "programs": [
            {
                "major": "Computer Science",
                "application_deadline": "15 January 2026",
                "numerus_fixus": "no",
                "prerequisites": "Advanced mathematics, physics recommended",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Electrical Engineering",
                "application_deadline": "15 January 2026",
                "numerus_fixus": "no",
                "prerequisites": "Advanced mathematics and physics required",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Mechanical Engineering",
                "application_deadline": "15 January 2026",
                "numerus_fixus": "no",
                "prerequisites": "Advanced mathematics and physics required",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Universiteit van Amsterdam",
        "city": "Amsterdam",
        "region": "Noord-Holland",
        "cost_of_living_monthly": 2300.0,
        "rent_estimate_monthly": 1450.0,
        "transport_score": 10,
        "website_url": "https://www.uva.nl/en",
        "teaching_style": "Lecture-based theory combined with academic rigor and research seminars",
        "career_focus": "Strong ties to research and graduate school pipelines, growing corporate recruitment presence",
        "campus_type": "large_urban",
        "social_scene": "Vibrant nightlife, big student events, active social calendar",
        "programs": [
            {
                "major": "Psychology",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Secondary school biology and math recommended",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Computer Science",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Advanced mathematics required",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Political Science",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "None specific; strong writing sample recommended",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Vrije Universiteit Amsterdam",
        "city": "Amsterdam",
        "region": "Noord-Holland",
        "cost_of_living_monthly": 2250.0,
        "rent_estimate_monthly": 1400.0,
        "transport_score": 9,
        "website_url": "https://vu.nl/en",
        "teaching_style": "Collaborative seminars, group work, and team-based projects",
        "career_focus": "Strong industry ties in finance, corporate recruitment, active career services",
        "campus_type": "medium",
        "social_scene": "Balanced social life with a mix of academic focus and student events",
        "programs": [
            {
                "major": "Business Administration",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Artificial Intelligence",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Advanced mathematics required, programming experience recommended",
                "required_documents": "Diploma, transcript, motivation letter, CV, English test score",
            },
        ],
    },
    {
        "name": "Technische Universiteit Eindhoven",
        "city": "Eindhoven",
        "region": "Noord-Brabant",
        "cost_of_living_monthly": 1700.0,
        "rent_estimate_monthly": 950.0,
        "transport_score": 7,
        "website_url": "https://www.tue.nl/en",
        "teaching_style": "Hands-on labs, project-based learning, practical engineering studios",
        "career_focus": "Deep industry partnerships with major tech employers, strong internship and job market outcomes",
        "campus_type": "medium",
        "social_scene": "Quiet, studious atmosphere with a calm academic focus",
        "programs": [
            {
                "major": "Computer Science",
                "application_deadline": "15 January 2026",
                "numerus_fixus": "no",
                "prerequisites": "Advanced mathematics required",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Electrical Engineering",
                "application_deadline": "15 January 2026",
                "numerus_fixus": "no",
                "prerequisites": "Advanced mathematics and physics required",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Industrial Design",
                "application_deadline": "15 January 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Portfolio submission required",
                "required_documents": "Diploma, transcript, portfolio, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Universiteit Utrecht",
        "city": "Utrecht",
        "region": "Utrecht",
        "cost_of_living_monthly": 2100.0,
        "rent_estimate_monthly": 1300.0,
        "transport_score": 9,
        "website_url": "https://www.uu.nl/en",
        "teaching_style": "Lecture-based theory with strong academic rigor and research-driven, independent study options",
        "career_focus": "Research and graduate school career paths, active PhD pipeline, academic career support",
        "campus_type": "medium",
        "social_scene": "Balanced student life with active associations and a calm study environment",
        "programs": [
            {
                "major": "Psychology",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Secondary school math and biology recommended",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Biology",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school biology and chemistry required",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Rijksuniversiteit Groningen",
        "city": "Groningen",
        "region": "Groningen",
        "cost_of_living_monthly": 1600.0,
        "rent_estimate_monthly": 850.0,
        "transport_score": 7,
        "website_url": "https://www.rug.nl/",
        "teaching_style": "Lectures combined with self-paced, independent and research-driven study",
        "career_focus": "Active career services with growing industry and corporate employer partnerships",
        "campus_type": "medium",
        "social_scene": "Lively student city with a large student population and active nightlife",
        "programs": [
            {
                "major": "International Business",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Secondary school math",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Computer Science",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Advanced mathematics recommended",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Universiteit Leiden",
        "city": "Leiden",
        "region": "Zuid-Holland",
        "cost_of_living_monthly": 2000.0,
        "rent_estimate_monthly": 1200.0,
        "transport_score": 8,
        "website_url": "https://www.universiteitleiden.nl/en",
        "teaching_style": "Academic rigor, lecture-based theory, small research seminars",
        "career_focus": "Strong research and graduate school career paths, active PhD and academic career pipeline",
        "campus_type": "small_liberal",
        "social_scene": "Quiet, studious atmosphere with a tight-knit academic community",
        "programs": [
            {
                "major": "Political Science",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Strong writing sample recommended",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Law",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "None specific",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Maastricht University",
        "city": "Maastricht",
        "region": "Limburg",
        "cost_of_living_monthly": 1750.0,
        "rent_estimate_monthly": 900.0,
        "transport_score": 6,
        "website_url": "https://www.maastrichtuniversity.nl/",
        "teaching_style": "Problem-based learning in small collaborative tutorial groups",
        "career_focus": "International corporate recruitment, strong internship placement, industry employer network",
        "campus_type": "small_liberal",
        "social_scene": "Balanced social life with a mix of international student events and academic focus",
        "programs": [
            {
                "major": "International Business",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Psychology",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Secondary school biology recommended",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Tilburg University",
        "city": "Tilburg",
        "region": "Noord-Brabant",
        "cost_of_living_monthly": 1550.0,
        "rent_estimate_monthly": 800.0,
        "transport_score": 6,
        "website_url": "https://www.tilburguniversity.edu/",
        "teaching_style": "Lecture-based theory with collaborative group work and seminars",
        "career_focus": "Strong industry ties in finance and consulting, active corporate recruitment and career services",
        "campus_type": "small_liberal",
        "social_scene": "Quiet, studious atmosphere with a calm, focused campus culture",
        "programs": [
            {
                "major": "Economics",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math (advanced level recommended)",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Business Administration",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school math",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Wageningen University",
        "city": "Wageningen",
        "region": "Gelderland",
        "cost_of_living_monthly": 1500.0,
        "rent_estimate_monthly": 750.0,
        "transport_score": 5,
        "website_url": "https://www.wur.nl/en",
        "teaching_style": "Hands-on labs, project-based fieldwork, and practical research studios",
        "career_focus": "Strong research career paths plus industry ties in agriculture, food, and environmental sectors",
        "campus_type": "small_liberal",
        "social_scene": "Quiet, studious atmosphere with a close-knit international student community",
        "programs": [
            {
                "major": "Environmental Sciences",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school biology and chemistry required",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
            {
                "major": "Biotechnology",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school biology and chemistry required",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Radboud Universiteit Nijmegen",
        "city": "Nijmegen",
        "region": "Gelderland",
        "cost_of_living_monthly": 1600.0,
        "rent_estimate_monthly": 800.0,
        "transport_score": 6,
        "website_url": "https://www.ru.nl/en",
        "teaching_style": "Lecture-based theory combined with collaborative seminars and group work",
        "career_focus": "Research and graduate school pipeline, growing industry partnerships in tech and health",
        "campus_type": "medium",
        "social_scene": "Balanced social life with active student associations and a calm study environment",
        "programs": [
            {
                "major": "Computer Science",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Advanced mathematics recommended",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Psychology",
                "application_deadline": "1 May 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Secondary school biology recommended",
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
