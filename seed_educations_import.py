"""
Seeds the database with universities and programs sourced from an
educations.com listing (Aug/Sep 2026), cross-checked against each
institution's own official admissions pages before import. Safe to
re-run — skips any university that already exists by name, and skips
any program that already exists for that university by major.

Three items found in the source listing were deliberately left out:
- Amsterdam Fashion Academy (both programs) — its degree is validated
  by Bucks New University (UK), not NVAO-accredited as Dutch; doesn't
  match what "study in the Netherlands" implies for this platform.
- Saxion's 3 "short degree" programs (Int'l Business, Civil
  Engineering, Int'l Finance & Accounting) — these require 3 years of
  prior higher education already completed, so they're not viable for
  a first-time applicant straight out of Lise, and the wizard has no
  way to filter for that.

Two institutions (United School for Liberal Studies, United
International Business School) are NOT recognized by any national
Ministry of Education — included per product decision, but flagged
loudly in every program's prerequisites field. Read that field before
recommending either to a student.

Usage:
    venv/Scripts/python.exe seed_educations_import.py
"""

from app import app, db, University, Program

NEW_UNIVERSITIES = [
    # ─── Italy ──────────────────────────────────────────────────────────────
    {
        "name": "John Cabot University",
        "country": "Italy",
        "city": "Rome",
        "region": "Lazio",
        "cost_of_living_monthly": 320.0,
        "rent_estimate_monthly": 800.0,
        "transport_score": 7,
        "website_url": "https://www.johncabot.edu",
        "teaching_style": "Small-class, US-style liberal arts seminars and discussion-based courses",
        "career_focus": "Strong ties to international NGOs, embassies, and multinational firms in Rome; US-accredited degree recognized globally",
        "campus_type": "small_liberal",
        "social_scene": "American-style campus community in the heart of Rome, large international student body",
        "programs": [
            {
                "major": "Art History",
                "application_deadline": "Rolling: EA 15 Nov, Reg 1 Mar",
                "numerus_fixus": "no",
                "prerequisites": "Rolling holistic admission (Early Action/Regular/Late rounds). Secondary school diploma; English proficiency.",
                "required_documents": "Diploma, transcript, personal statement, English test score (or interview)",
            },
        ],
    },
    {
        "name": "Scuola Politecnica di Design SPD",
        "country": "Italy",
        "city": "Milan",
        "region": "Lombardy",
        "cost_of_living_monthly": 380.0,
        "rent_estimate_monthly": 950.0,
        "transport_score": 8,
        "website_url": "https://www.scuoladesign.com",
        "teaching_style": "Studio-based design education with industry-linked projects",
        "career_focus": "Strong ties to Milan's design and fashion industry",
        "campus_type": "small_liberal",
        "social_scene": "Small, design-focused international student community in Milan",
        "programs": [
            {
                "major": "Communication, Culture and Business",
                "application_deadline": "Rolling — courses start October",
                "numerus_fixus": "no",
                "prerequisites": "Interview, portfolio, and motivation letter required (not a competitive quota). Degree awarded via Teesside University (UK) partnership, not an independent Italian university degree — verify recognition in your home country.",
                "required_documents": "Diploma, transcript, motivation letter, portfolio, interview",
            },
        ],
    },
    {
        "name": "Ca' Foscari University of Venice",
        "country": "Italy",
        "city": "Venice",
        "region": "Veneto",
        "cost_of_living_monthly": 340.0,
        "rent_estimate_monthly": 850.0,
        "transport_score": 7,
        "website_url": "https://www.unive.it/en",
        "teaching_style": "Lecture and lab-based coursework in a historic island-campus setting",
        "career_focus": "Growing ties to Veneto's tech and cultural-heritage sectors",
        "campus_type": "medium",
        "social_scene": "Unique historic Venice setting, sizable international student population",
        "programs": [
            {
                "major": "Computer Science - Data Science",
                "application_deadline": "Non-EU window: 1 Jul-30 Sep 2026",
                "numerus_fixus": "unclear",
                "prerequisites": "Restricted-entry status unclear — one source cites a 30-seat non-EU quota with entrance test, official page currently shows open admission; verify current-cycle status before applying. Strong secondary school math grades recommended.",
                "required_documents": "Diploma, transcript, English test score, check current admission procedure",
            },
        ],
    },
    {
        "name": "University of Milan",
        "country": "Italy",
        "city": "Milan",
        "region": "Lombardy",
        "cost_of_living_monthly": 380.0,
        "rent_estimate_monthly": 950.0,
        "transport_score": 8,
        "website_url": "https://www.unimi.it/en",
        "teaching_style": "Large lecture-based courses, strong humanities and sciences tradition",
        "career_focus": "One of Italy's largest and most comprehensive universities, broad employer network",
        "campus_type": "large_urban",
        "social_scene": "Large, diverse student population in central Milan",
        "programs": [
            {
                "major": "Ancient Civilizations for the Contemporary World",
                "application_deadline": "Check apps.unimi.it manifesto",
                "numerus_fixus": "yes",
                "prerequisites": "Limited enrollment with mandatory admission test. Joint programme taught across both Milan and Ca' Foscari Venice campuses.",
                "required_documents": "Diploma, transcript, admission test result, check official requirements",
            },
        ],
    },
    {
        "name": "University of Parma",
        "country": "Italy",
        "city": "Parma",
        "region": "Emilia-Romagna",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 550.0,
        "transport_score": 6,
        "website_url": "https://www.unipr.it/en",
        "teaching_style": "Traditional lecture-based Italian university teaching",
        "career_focus": "Regional employer ties, notable strength in food science and law",
        "campus_type": "medium",
        "social_scene": "Compact, affordable university city in Emilia-Romagna",
        "programs": [
            {
                "major": "Law (Single Cycle Degree)",
                "application_deadline": "Non-EU window ~mid-Apr/early-Jun",
                "numerus_fixus": "unclear",
                "prerequisites": "Italian-taught, 5-year single-cycle degree. Exact programme-level deadline not confirmed — verify via admissions.unipr.it.",
                "required_documents": "Diploma, transcript, Italian language proficiency, check official requirements",
            },
            {
                "major": "Gastronomic Sciences",
                "application_deadline": "Non-EU window ~mid-Apr/early-Jun",
                "numerus_fixus": "unclear",
                "prerequisites": "Italian-taught. Not to be confused with the separate University of Gastronomic Sciences (UNISG) in Pollenzo. Exact deadline not confirmed — verify via admissions.unipr.it.",
                "required_documents": "Diploma, transcript, Italian language proficiency, check official requirements",
            },
        ],
    },
    {
        "name": "Accademia Italiana (Rome)",
        "country": "Italy",
        "city": "Rome",
        "region": "Lazio",
        "cost_of_living_monthly": 320.0,
        "rent_estimate_monthly": 800.0,
        "transport_score": 7,
        "website_url": "https://www.accademiaitaliana.com",
        "teaching_style": "Studio and portfolio-based design/fashion education, MIUR-recognized (AFAM system)",
        "career_focus": "Strong ties to Italian fashion and design industry",
        "campus_type": "small_liberal",
        "social_scene": "Small international design-student community in Rome",
        "programs": [
            {
                "major": "Photography",
                "application_deadline": "Rolling — programs start September",
                "numerus_fixus": "no",
                "prerequisites": "Bilingual Italian/English, MIUR-recognized (AFAM system) private academy, not a public university — legally-recognized bachelor's-equivalent diploma. Standard secondary-diploma admission.",
                "required_documents": "Diploma, transcript, portfolio, motivation letter",
            },
            {
                "major": "Fashion Design",
                "application_deadline": "Rolling — programs start September",
                "numerus_fixus": "no",
                "prerequisites": "Bilingual Italian/English, MIUR-recognized (AFAM system) private academy, not a public university — legally-recognized bachelor's-equivalent diploma. Standard secondary-diploma admission.",
                "required_documents": "Diploma, transcript, portfolio, motivation letter",
            },
            {
                "major": "Communication Design",
                "application_deadline": "Rolling — programs start September",
                "numerus_fixus": "no",
                "prerequisites": "Bilingual Italian/English, MIUR-recognized (AFAM system) private academy, not a public university — legally-recognized bachelor's-equivalent diploma. Standard secondary-diploma admission.",
                "required_documents": "Diploma, transcript, portfolio, motivation letter",
            },
            {
                "major": "Interior and Product Design",
                "application_deadline": "Rolling — programs start September",
                "numerus_fixus": "no",
                "prerequisites": "Bilingual Italian/English, MIUR-recognized (AFAM system) private academy, not a public university — legally-recognized bachelor's-equivalent diploma. Standard secondary-diploma admission.",
                "required_documents": "Diploma, transcript, portfolio, motivation letter",
            },
        ],
    },
    {
        "name": "Accademia Italiana (Florence)",
        "country": "Italy",
        "city": "Florence",
        "region": "Tuscany",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 700.0,
        "transport_score": 6,
        "website_url": "https://www.accademiaitaliana.com",
        "teaching_style": "Studio and portfolio-based design/fashion education, MIUR-recognized (AFAM system)",
        "career_focus": "Strong ties to Italian fashion and design industry",
        "campus_type": "small_liberal",
        "social_scene": "Small international design-student community in Florence",
        "programs": [
            {
                "major": "Photography",
                "application_deadline": "Rolling — programs start September",
                "numerus_fixus": "no",
                "prerequisites": "Bilingual Italian/English, MIUR-recognized (AFAM system) private academy, not a public university — legally-recognized bachelor's-equivalent diploma. Standard secondary-diploma admission.",
                "required_documents": "Diploma, transcript, portfolio, motivation letter",
            },
            {
                "major": "Fashion Design",
                "application_deadline": "Rolling — programs start September",
                "numerus_fixus": "no",
                "prerequisites": "Bilingual Italian/English, MIUR-recognized (AFAM system) private academy, not a public university — legally-recognized bachelor's-equivalent diploma. Standard secondary-diploma admission.",
                "required_documents": "Diploma, transcript, portfolio, motivation letter",
            },
        ],
    },
    {
        "name": "Luiss Guido Carli",
        "country": "Italy",
        "city": "Rome",
        "region": "Lazio",
        "cost_of_living_monthly": 320.0,
        "rent_estimate_monthly": 800.0,
        "transport_score": 7,
        "website_url": "https://www.luiss.edu",
        "teaching_style": "Case-study and seminar-heavy, English-taught international programs",
        "career_focus": "Elite placement in law, business, and international affairs across Europe",
        "campus_type": "medium",
        "social_scene": "Selective, career-focused student body in central Rome",
        "programs": [
            {
                "major": "Global Law",
                "application_deadline": "Test windows: Oct-Feb, Mar-May",
                "numerus_fixus": "yes",
                "prerequisites": "English-taught international law programme (the source listing referenced Luiss's separate Italian-taught LLB — Global Law is the real fit for an English-speaking applicant). Entrance: Luiss Test, or SAT 1200+/ACT 25+/IB 36+.",
                "required_documents": "Diploma, transcript, Luiss Test or SAT/ACT/IB score, English test score",
            },
        ],
    },
    {
        "name": 'University of Campania "Luigi Vanvitelli"',
        "country": "Italy",
        "city": "Caserta",
        "region": "Campania",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 480.0,
        "transport_score": 5,
        "website_url": "https://international.unicampania.it",
        "teaching_style": "Lecture-based with clinical/lab components for health and technical programs",
        "career_focus": "Regional public-sector and healthcare employer ties",
        "campus_type": "medium",
        "social_scene": "Smaller southern Italian university city, lower cost of living",
        "programs": [
            {
                "major": "Nursing",
                "application_deadline": "Applications open 1 Aug",
                "numerus_fixus": "yes",
                "prerequisites": "Nationally numero-chiuso via mandatory national entrance exam — standard Italian health-profession policy, not university-specific.",
                "required_documents": "Diploma, transcript, national entrance exam result, English test score",
            },
            {
                "major": "Data Analytics",
                "application_deadline": "Applications open 1 Aug",
                "numerus_fixus": "yes",
                "prerequisites": "Restricted entry, admission test required. Optional joint-degree track with Université Paris 13.",
                "required_documents": "Diploma, transcript, admission test result, English test score",
            },
        ],
    },
    {
        "name": "IULM - International University of Languages and Media",
        "country": "Italy",
        "city": "Milan",
        "region": "Lombardy",
        "cost_of_living_monthly": 380.0,
        "rent_estimate_monthly": 950.0,
        "transport_score": 8,
        "website_url": "https://www.iulm.it/en",
        "teaching_style": "Bilingual lecture-based courses in communication and media",
        "career_focus": "Ties to Milan's media, marketing, and communications industry",
        "campus_type": "medium",
        "social_scene": "Media and communications-focused international student community in Milan",
        "programs": [
            {
                "major": "Corporate Communication and Public Relations",
                "application_deadline": "CLOSED for 2026/27 - check next cycle",
                "numerus_fixus": "yes",
                "prerequisites": "2026/27 English-taught intake is at full capacity and closed to new applications — check for a later intake or waitlist before recommending to a student.",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Scuola Superiore per Mediatori Linguistici di Pisa",
        "country": "Italy",
        "city": "Pisa",
        "region": "Tuscany",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 650.0,
        "transport_score": 6,
        "website_url": "https://www.universitaly.it",
        "teaching_style": "Language-intensive, small-class instruction, MUR-accredited (Class L-12)",
        "career_focus": "Ties to translation, mediation, and international relations sectors",
        "campus_type": "small_liberal",
        "social_scene": "Small, historic university town with a strong academic tradition",
        "programs": [
            {
                "major": "Linguistic Mediation Sciences",
                "application_deadline": "B2 Italian required; Foundation Yr",
                "numerus_fixus": "no",
                "prerequisites": "MUR-accredited (Class L-12), legitimate higher-ed institution despite non-'university' name. Requires B2 Italian; Foundation Year available if below that level.",
                "required_documents": "Diploma, transcript, Italian language proficiency (B2)",
            },
        ],
    },
    # ─── Belgium ────────────────────────────────────────────────────────────
    {
        "name": "UCLL University of Applied Sciences",
        "country": "Belgium",
        "city": "Leuven",
        "region": "Flemish Brabant",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 650.0,
        "transport_score": 7,
        "website_url": "https://www.ucll.be/en",
        "teaching_style": "Practice-oriented, applied learning with international exchange tracks",
        "career_focus": "Strong regional business ties, international placement options",
        "campus_type": "medium",
        "social_scene": "Applied-sciences student community in Leuven",
        "programs": [
            {
                "major": "International Business Management, Marketing",
                "application_deadline": "Non-EEA: 1 Apr; EEA: 31 Aug 2026",
                "numerus_fixus": "no",
                "prerequisites": "Two tracks available: 'Track in Belgium' or 'Track across Europe' (multi-country exchange). Strong English proficiency.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Artevelde University of Applied Sciences",
        "country": "Belgium",
        "city": "Ghent",
        "region": "East Flanders",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 650.0,
        "transport_score": 7,
        "website_url": "https://www.arteveldehogeschool.be/en",
        "teaching_style": "Practice-oriented, project-based applied learning",
        "career_focus": "Regional business and communications industry ties",
        "campus_type": "medium",
        "social_scene": "Applied-sciences student community in Ghent",
        "programs": [
            {
                "major": "International Business Management",
                "application_deadline": "Non-EU: 1 May; pay by 30 Jun 2026",
                "numerus_fixus": "no",
                "prerequisites": "Standard secondary diploma; English proficiency.",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "International Communication Management",
                "application_deadline": "Int'l: 1 Jun 2026; EU: 1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "NVAO-accredited programme. Standard secondary diploma; English proficiency.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "University of Antwerp",
        "country": "Belgium",
        "city": "Antwerp",
        "region": "Antwerp",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 700.0,
        "transport_score": 8,
        "website_url": "https://www.uantwerpen.be/en",
        "teaching_style": "Lecture-based with research integration",
        "career_focus": "Strong ties to Antwerp's port, logistics, and business sectors",
        "campus_type": "large_urban",
        "social_scene": "Large, diverse student population in Belgium's second city",
        "programs": [
            {
                "major": "Social-Economic Sciences",
                "application_deadline": "Non-EU international: 1 Mar 2026",
                "numerus_fixus": "no",
                "prerequisites": "Standard secondary diploma; English proficiency.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Thomas More University of Applied Sciences",
        "country": "Belgium",
        "city": "Mechelen",
        "region": "Antwerp",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 600.0,
        "transport_score": 6,
        "website_url": "https://thomasmore.be/en",
        "teaching_style": "Practice-oriented applied learning",
        "career_focus": "Regional media and communications industry ties",
        "campus_type": "medium",
        "social_scene": "Compact applied-sciences campus in Mechelen",
        "programs": [
            {
                "major": "International Communication and Media",
                "application_deadline": "Non-EEA: 17 Jun (Sep)/10 Nov (Feb)",
                "numerus_fixus": "no",
                "prerequisites": "Two intakes per year (September and February). No fixed deadline for EEA applicants.",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Public and Corporate Affairs",
                "application_deadline": "Non-EEA: 17 Jun (Sep)/10 Nov (Feb)",
                "numerus_fixus": "no",
                "prerequisites": "Two intakes per year (September and February). No fixed deadline for EEA applicants.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "United School for Liberal Studies",
        "country": "Belgium",
        "city": "Brussels",
        "region": "Brussels-Capital",
        "cost_of_living_monthly": 360.0,
        "rent_estimate_monthly": 900.0,
        "transport_score": 9,
        "website_url": "https://www.weuni.com",
        "teaching_style": "Seminar-based liberal arts and international relations coursework",
        "career_focus": "Private international degree (HQ Zurich, Switzerland) - NOT recognized by Belgium's Ministry of Education. Verify recognition value in your home country and career path before enrolling.",
        "campus_type": "medium",
        "social_scene": "Small international student body across multiple European campuses",
        "programs": [
            {
                "major": "International Relations",
                "application_deadline": "Check official site - rolling",
                "numerus_fixus": "no",
                "prerequisites": "NOT recognized by Belgium's Ministry of Education - this is a private international degree conferred by the school's Zurich (Switzerland) headquarters. Confirm the credential's value for your intended country/career before applying.",
                "required_documents": "Diploma, transcript, motivation letter - verify with school directly",
            },
            {
                "major": "Liberal Studies",
                "application_deadline": "Check official site - rolling",
                "numerus_fixus": "no",
                "prerequisites": "NOT recognized by Belgium's Ministry of Education - this is a private international degree conferred by the school's Zurich (Switzerland) headquarters. Confirm the credential's value for your intended country/career before applying.",
                "required_documents": "Diploma, transcript, motivation letter - verify with school directly",
            },
            {
                "major": "Communication Studies",
                "application_deadline": "Check official site - rolling",
                "numerus_fixus": "no",
                "prerequisites": "NOT recognized by Belgium's Ministry of Education - this is a private international degree conferred by the school's Zurich (Switzerland) headquarters. Confirm the credential's value for your intended country/career before applying.",
                "required_documents": "Diploma, transcript, motivation letter - verify with school directly",
            },
        ],
    },
    {
        "name": "United International Business School",
        "country": "Belgium",
        "city": "Antwerp",
        "region": "Antwerp",
        "cost_of_living_monthly": 280.0,
        "rent_estimate_monthly": 700.0,
        "transport_score": 8,
        "website_url": "https://www.uibs.org",
        "teaching_style": "Case-study and seminar-based international business coursework",
        "career_focus": "Accredited only by ACBSP (a private US business accreditor) - NOT recognized by any national Ministry of Education where it operates. Verify recognition value before enrolling.",
        "campus_type": "medium",
        "social_scene": "Small international business-student body across multiple European campuses",
        "programs": [
            {
                "major": "Business Studies",
                "application_deadline": "Check official site - rolling",
                "numerus_fixus": "no",
                "prerequisites": "Accredited only by ACBSP (a private US business accreditor) - NOT recognized by any national Ministry of Education. Confirm the credential's value for your intended country/career before applying.",
                "required_documents": "Diploma, transcript, motivation letter - verify with school directly",
            },
            {
                "major": "International Management - Hospitality Management",
                "application_deadline": "Check official site - rolling",
                "numerus_fixus": "no",
                "prerequisites": "Accredited only by ACBSP (a private US business accreditor) - NOT recognized by any national Ministry of Education. Confirm the credential's value for your intended country/career before applying.",
                "required_documents": "Diploma, transcript, motivation letter - verify with school directly",
            },
        ],
    },
]

# Programs to add to universities that already exist in the database —
# only "name" is used to look them up; other university fields are ignored.
EXISTING_UNIVERSITY_PROGRAMS = [
    {
        "name": "Vrije Universiteit Brussel",
        "programs": [
            {
                "major": "Multilingual Linguistics and Literary Studies",
                "application_deadline": "Non-EEA: 31 Mar 2026",
                "numerus_fixus": "no",
                "prerequisites": "Strong English proficiency and interest in comparative literature/linguistics.",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Business Economics",
                "application_deadline": "Non-EEA: 1 Apr; EEA: 1 Aug 2026",
                "numerus_fixus": "no",
                "prerequisites": "Strong secondary school math grades.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "KU Leuven",
        "programs": [
            {
                "major": "Theology and Religious Studies",
                "application_deadline": "Non-EEA: 1 Mar; EEA: 1 Jun 2026",
                "numerus_fixus": "yes",
                "prerequisites": "Restricted entry (numerus fixus). Strong English proficiency; interest in religious/theological studies.",
                "required_documents": "Diploma, transcript, motivation letter, English test score",
            },
        ],
    },
    {
        "name": "Sapienza Università di Roma",
        "programs": [
            {
                "major": "Classics",
                "application_deadline": "Non-EU: 15 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Deadline matches the 15 May pattern already verified for Sapienza's Engineering and Economics programmes.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Radboud Universiteit Nijmegen",
        "programs": [
            {
                "major": "International Business Administration",
                "application_deadline": "Non-EU: 1 Apr; EU: 1 Jul 2026",
                "numerus_fixus": "no",
                "prerequisites": "Strong secondary school math grades; English proficiency.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Avans University of Applied Sciences",
        "programs": [
            {
                "major": "Environmental Science for Sustainability, Ecosystems and Technology",
                "application_deadline": "Non-EU: 1 May; EU: 1 Jun 2026",
                "numerus_fixus": "no",
                "prerequisites": "Secondary school biology/chemistry recommended; English proficiency.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Erasmus Universiteit Rotterdam",
        "programs": [
            {
                "major": "Communication and Media",
                "application_deadline": "15 Mar 2026 (single deadline)",
                "numerus_fixus": "no",
                "prerequisites": "International Bachelor track at Erasmus School of History, Culture and Communication.",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "History (International Bachelor)",
                "application_deadline": "Non-EEA: 1 Apr; EEA: 1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "International Bachelor track at Erasmus School of History, Culture and Communication.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Zuyd University of Applied Sciences",
        "programs": [
            {
                "major": "Circular Cities and Communities",
                "application_deadline": "Non-EU: 1 May; EU: 1 Jun 2026",
                "numerus_fixus": "no",
                "prerequisites": "Offered at Zuyd's Heerlen campus.",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Music (Conservatorium Maastricht)",
                "application_deadline": "Non-EU: 1 Mar; EU: up to 1 May",
                "numerus_fixus": "yes",
                "prerequisites": "Audition-based restricted entry (+ possible theory test), not academic numerus fixus. Offered at Conservatorium Maastricht.",
                "required_documents": "Diploma, transcript, audition recording/live audition",
            },
        ],
    },
    {
        "name": "Rijksuniversiteit Groningen",
        "programs": [
            {
                "major": "Spatial Planning and Design",
                "application_deadline": "Non-EU: 1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "EU/EEA deadline is later (exact date not confirmed — check official site).",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Communication and Information Studies",
                "application_deadline": "Non-EU: 1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "EU/EEA deadline is later (exact date not confirmed — check official site).",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Astronomy",
                "application_deadline": "Non-EU: 1 May 2026; EUR100 fee",
                "numerus_fixus": "no",
                "prerequisites": "Early Bird track: apply 1 Oct-28 Feb for a decision within 1 month. EUR100 non-refundable fee for non-Dutch diplomas.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "NHL Stenden University of Applied Sciences",
        "programs": [
            {
                "major": "Green Chemistry",
                "application_deadline": "Non-EU: 31 May; EU: 15 Aug 2026",
                "numerus_fixus": "no",
                "prerequisites": "Offered at NHL Stenden's Emmen campus. Requires VWO-equivalent diploma with math and chemistry — standard for Turkish Fen/Anadolu Lisesi diplomas.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Maastricht University",
        "programs": [
            {
                "major": "European Studies",
                "application_deadline": "Non-EU: 1 Apr; EU: 1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Faculty of Arts and Social Sciences.",
                "required_documents": "Diploma, transcript, English test score",
            },
            {
                "major": "Urban Sustainability Studies",
                "application_deadline": "Non-EU: 1 Apr; EU: 1 May 2026",
                "numerus_fixus": "no",
                "prerequisites": "Faculty of Science and Engineering. Final documents due 31 Aug 2026.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
    {
        "name": "Hanze University of Applied Sciences",
        "programs": [
            {
                "major": "Electrical and Electronic Engineering (Mechatronics)",
                "application_deadline": "Non-EU: 1 Jun; EU: 15 Aug 2026",
                "numerus_fixus": "no",
                "prerequisites": "Requires HAVO-level diploma with math and physics.",
                "required_documents": "Diploma, transcript, English test score",
            },
        ],
    },
]


def seed():
    with app.app_context():
        created_unis = 0
        created_programs = 0
        skipped_unis = []

        for uni_data in NEW_UNIVERSITIES:
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

        for entry in EXISTING_UNIVERSITY_PROGRAMS:
            university = University.query.filter_by(name=entry["name"]).first()
            if not university:
                skipped_unis.append(entry["name"])
                continue
            for prog_data in entry["programs"]:
                exists = Program.query.filter_by(
                    university_id=university.id, major=prog_data["major"]
                ).first()
                if not exists:
                    db.session.add(Program(university_id=university.id, **prog_data))
                    created_programs += 1

        db.session.commit()
        print(f"Done. Added {created_unis} new universities and {created_programs} new programs.")
        if skipped_unis:
            print(f"WARNING: could not find these universities to attach programs to: {skipped_unis}")
        print(f"Totals now: {University.query.count()} universities, {Program.query.count()} programs.")


if __name__ == "__main__":
    seed()
