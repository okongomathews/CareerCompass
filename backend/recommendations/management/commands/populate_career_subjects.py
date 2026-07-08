"""
Populate CareerSubject mappings for all careers.

Maps Kenyan KCSE subjects to careers with importance levels:
required / recommended / beneficial.

Without this data, calculate_academic_match_score() always returns 0.5
(the neutral fallback), making the Academic bar permanently stuck at 50%.

Run:
    python manage.py populate_career_subjects
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from recommendations.models import Career, Subject, CareerSubject


# ── KCSE Subject definitions ───────────────────────────────────────────────────
# Each entry: (display_name, code, category, is_compulsory)
KCSE_SUBJECTS = [
    ('Mathematics',                    'MATH',   'mathematics', True),
    ('English',                        'ENG',    'languages',   True),
    ('Kiswahili',                      'KIS',    'languages',   True),
    ('Biology',                        'BIO',    'sciences',    False),
    ('Chemistry',                      'CHEM',   'sciences',    False),
    ('Physics',                        'PHY',    'sciences',    False),
    ('History & Government',           'HIST',   'humanities',  False),
    ('Geography',                      'GEO',    'humanities',  False),
    ('Christian Religious Education',  'CRE',    'religious',   False),
    ('Islamic Religious Education',    'IRE',    'religious',   False),
    ('Business Studies',               'BST',    'business',    False),
    ('Economics',                      'ECON',   'business',    False),
    ('Accounting',                     'ACC',    'business',    False),
    ('Computer Studies',               'CS',     'computer',    False),
    ('Agriculture',                    'AGRI',   'agriculture', False),
    ('Home Science',                   'HSC',    'sciences',    False),
    ('Art & Design',                   'ART',    'arts',        False),
    ('Music',                          'MUS',    'arts',        False),
    ('Physical Education',             'PE',     'arts',        False),
    ('French',                         'FRE',    'languages',   False),
    ('German',                         'GER',    'languages',   False),
    ('Arabic',                         'ARB',    'languages',   False),
    ('Technical Drawing',              'TECH',   'technical',   False),
    ('Building Construction',          'BUILD',  'technical',   False),
    ('Metal Work',                     'METAL',  'technical',   False),
    ('Wood Work',                      'WOOD',   'technical',   False),
    ('Electricity',                    'ELEC',   'technical',   False),
    ('Power Mechanics',                'POWER',  'technical',   False),
    ('Aviation Technology',            'AVTN',   'technical',   False),
]

# Short aliases used in CAREER_SUBJECTS below
_M = 'Mathematics'; _E = 'English'; _K = 'Kiswahili'
_BIO = 'Biology'; _CH = 'Chemistry'; _PH = 'Physics'
_HI = 'History & Government'; _GE = 'Geography'
_CR = 'Christian Religious Education'; _IR = 'Islamic Religious Education'
_BS = 'Business Studies'; _EC = 'Economics'; _AC = 'Accounting'
_CS = 'Computer Studies'; _AG = 'Agriculture'; _HS = 'Home Science'
_AR = 'Art & Design'; _MU = 'Music'; _PE = 'Physical Education'
_FR = 'French'; _GR = 'German'; _AA = 'Arabic'
_TD = 'Technical Drawing'; _BD = 'Building Construction'
_ME = 'Metal Work'; _WD = 'Wood Work'; _EL = 'Electricity'
_PW = 'Power Mechanics'; _AV = 'Aviation Technology'

# ── Career → subject mappings ──────────────────────────────────────────────────
# Format: {'match': <fragment in Career.name>, 'req': [...], 'rec': [...], 'ben': [...]}
# fragment is matched case-insensitively against Career.name
CAREER_SUBJECTS = [
    # ── Technology ────────────────────────────────────────────────────────────
    {'match': 'Software',         'req': [_M, _CS],          'rec': [_PH, _E],          'ben': [_EC]},
    {'match': 'Data Scientist',   'req': [_M, _CS],          'rec': [_PH, _EC],         'ben': [_BIO]},
    {'match': 'Data Analyst',     'req': [_M, _CS],          'rec': [_EC, _E],          'ben': [_BS]},
    {'match': 'Cybersecurity',    'req': [_M, _CS],          'rec': [_PH, _E],          'ben': [_EC]},
    {'match': 'Network',          'req': [_M, _CS, _PH],     'rec': [_E],               'ben': [_EL]},
    {'match': 'Web Developer',    'req': [_M, _CS],          'rec': [_AR, _E],          'ben': [_BS]},
    {'match': 'Mobile App',       'req': [_M, _CS],          'rec': [_E, _PH],          'ben': []},
    {'match': 'Database',         'req': [_M, _CS],          'rec': [_E],               'ben': [_BS]},
    {'match': 'AI Engineer',      'req': [_M, _CS, _PH],     'rec': [_E],               'ben': [_BIO]},
    {'match': 'Machine Learning', 'req': [_M, _CS, _PH],     'rec': [_E],               'ben': []},
    {'match': 'IT Support',       'req': [_CS, _M],          'rec': [_E, _PH],          'ben': []},
    {'match': 'Systems Analyst',  'req': [_M, _CS],          'rec': [_BS, _E],          'ben': [_EC]},
    {'match': 'Cloud',            'req': [_M, _CS],          'rec': [_PH, _E],          'ben': []},
    {'match': 'DevOps',           'req': [_M, _CS],          'rec': [_PH, _E],          'ben': []},
    {'match': 'UI/UX',            'req': [_CS, _AR],         'rec': [_E, _M],           'ben': [_MU]},
    {'match': 'Game Developer',   'req': [_M, _CS],          'rec': [_PH, _AR],         'ben': []},
    {'match': 'Blockchain',       'req': [_M, _CS],          'rec': [_PH, _E],          'ben': [_EC]},
    {'match': 'GIS',              'req': [_M, _CS],          'rec': [_GE, _PH],         'ben': []},
    {'match': 'Drone',            'req': [_M, _PH],          'rec': [_CS, _AV],         'ben': []},
    {'match': 'Robotics',         'req': [_M, _PH, _EL],     'rec': [_CS, _TD],         'ben': []},
    {'match': 'Digital Marketing','req': [_E, _BS],          'rec': [_EC, _M],          'ben': [_AR]},
    {'match': 'Technical Writer', 'req': [_E, _CS],          'rec': [_M],               'ben': []},
    {'match': 'Mobile Money',     'req': [_M, _CS],          'rec': [_E, _BS],          'ben': []},
    {'match': 'Fintech',          'req': [_M, _CS, _EC],     'rec': [_E, _BS],          'ben': []},
    {'match': 'E-Commerce',       'req': [_BS, _CS],         'rec': [_EC, _E],          'ben': []},

    # ── Engineering ───────────────────────────────────────────────────────────
    {'match': 'Civil Engineer',   'req': [_M, _PH],          'rec': [_CH, _TD],         'ben': [_GE]},
    {'match': 'Mechanical',       'req': [_M, _PH],          'rec': [_CH, _TD],         'ben': [_ME]},
    {'match': 'Electrical',       'req': [_M, _PH, _EL],     'rec': [_TD, _CS],         'ben': []},
    {'match': 'Chemical Eng',     'req': [_M, _CH, _PH],     'rec': [_BIO, _E],         'ben': []},
    {'match': 'Structural',       'req': [_M, _PH],          'rec': [_TD, _CH],         'ben': [_GE]},
    {'match': 'Aerospace',        'req': [_M, _PH],          'rec': [_CH, _TD],         'ben': [_CS]},
    {'match': 'Petroleum',        'req': [_M, _CH, _PH],     'rec': [_GE],              'ben': []},
    {'match': 'Mining',           'req': [_M, _PH, _CH],     'rec': [_GE],              'ben': [_TD]},
    {'match': 'Environmental Eng','req': [_M, _CH, _BIO],    'rec': [_PH, _GE],         'ben': []},
    {'match': 'Agricultural Eng', 'req': [_M, _AG, _BIO],    'rec': [_CH, _PH],         'ben': []},
    {'match': 'Biomedical',       'req': [_M, _PH, _BIO],    'rec': [_CH, _CS],         'ben': []},
    {'match': 'Marine Eng',       'req': [_M, _PH],          'rec': [_CH, _GE],         'ben': []},
    {'match': 'Mechatronics',     'req': [_M, _PH, _EL],     'rec': [_CS, _TD],         'ben': []},
    {'match': 'Water Eng',        'req': [_M, _PH],          'rec': [_GE, _CH],         'ben': []},
    {'match': 'Renewable Energy', 'req': [_M, _PH, _EL],     'rec': [_CH, _TD],         'ben': []},
    {'match': 'Telecom',          'req': [_M, _PH, _EL],     'rec': [_CS, _TD],         'ben': []},
    {'match': 'Railway',          'req': [_M, _PH],          'rec': [_TD, _EL],         'ben': []},
    {'match': 'Geotechnical',     'req': [_M, _PH, _GE],     'rec': [_CH],              'ben': []},
    {'match': 'Irrigation',       'req': [_M, _AG],          'rec': [_PH, _GE],         'ben': []},

    # ── Health & Medicine ──────────────────────────────────────────────────────
    {'match': 'Doctor',           'req': [_BIO, _CH, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Physician',        'req': [_BIO, _CH, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Surgeon',          'req': [_BIO, _CH, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Nurse',            'req': [_BIO, _CH],        'rec': [_M, _E],           'ben': [_PH]},
    {'match': 'Pharmacist',       'req': [_CH, _BIO, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Dentist',          'req': [_BIO, _CH, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Physiotherapist',  'req': [_BIO, _CH],        'rec': [_PH, _M],          'ben': [_PE]},
    {'match': 'Clinical Officer', 'req': [_BIO, _CH, _M],    'rec': [_PH],              'ben': [_E]},
    {'match': 'Laboratory',       'req': [_BIO, _CH, _M],    'rec': [_PH, _CS],         'ben': []},
    {'match': 'Radiograph',       'req': [_PH, _M, _BIO],    'rec': [_CH],              'ben': [_CS]},
    {'match': 'Optometrist',      'req': [_PH, _BIO, _M],    'rec': [_CH],              'ben': []},
    {'match': 'Dietitian',        'req': [_BIO, _CH, _HS],   'rec': [_M],               'ben': [_E]},
    {'match': 'Nutritionist',     'req': [_BIO, _HS],        'rec': [_CH, _M],          'ben': [_E]},
    {'match': 'Psychiatrist',     'req': [_BIO, _CH, _M],    'rec': [_E, _PH],          'ben': [_CR]},
    {'match': 'Psychologist',     'req': [_BIO, _E],         'rec': [_M, _HI],          'ben': [_CR]},
    {'match': 'Veterinarian',     'req': [_BIO, _CH, _M],    'rec': [_PH, _AG],         'ben': []},
    {'match': 'Public Health',    'req': [_BIO, _M],         'rec': [_CH, _EC],         'ben': [_GE]},
    {'match': 'Epidemiologist',   'req': [_BIO, _M, _CH],    'rec': [_GE, _CS],         'ben': []},
    {'match': 'Cardiologist',     'req': [_BIO, _CH, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Paediatrician',    'req': [_BIO, _CH, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Gynaecologist',    'req': [_BIO, _CH, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Oncologist',       'req': [_BIO, _CH, _M],    'rec': [_PH, _E],          'ben': []},
    {'match': 'Radiologist',      'req': [_PH, _M, _BIO],    'rec': [_CH],              'ben': []},
    {'match': 'Anaesthesiologist','req': [_BIO, _CH, _M],    'rec': [_PH],              'ben': []},
    {'match': 'Speech Therapist', 'req': [_BIO, _E],         'rec': [_M],               'ben': []},
    {'match': 'Audiologist',      'req': [_PH, _BIO, _M],    'rec': [_CH],              'ben': []},
    {'match': 'Biostatistician',  'req': [_M, _BIO],         'rec': [_CS, _EC],         'ben': []},
    {'match': 'Occupational',     'req': [_BIO, _CH],        'rec': [_M, _E],           'ben': [_PE]},
    {'match': 'Sports Physio',    'req': [_BIO, _PE],        'rec': [_CH, _M],          'ben': []},
    {'match': 'Mental Health',    'req': [_BIO, _E],         'rec': [_HI, _CR],         'ben': []},

    # ── Business & Finance ─────────────────────────────────────────────────────
    {'match': 'Accountant',       'req': [_M, _AC, _BS],     'rec': [_EC, _E],          'ben': [_CS]},
    {'match': 'CPA',              'req': [_M, _AC, _BS],     'rec': [_EC, _E],          'ben': [_CS]},
    {'match': 'Auditor',          'req': [_M, _AC, _BS],     'rec': [_EC, _E],          'ben': [_CS]},
    {'match': 'Financial Anal',   'req': [_M, _EC, _BS],     'rec': [_AC, _E],          'ben': [_CS]},
    {'match': 'Investment',       'req': [_M, _EC],          'rec': [_BS, _AC],         'ben': [_E]},
    {'match': 'Banker',           'req': [_M, _EC, _BS],     'rec': [_AC, _E],          'ben': [_CS]},
    {'match': 'Insurance',        'req': [_M, _BS],          'rec': [_EC, _E],          'ben': [_AC]},
    {'match': 'Actuary',          'req': [_M, _EC],          'rec': [_PH, _CS],         'ben': [_BS]},
    {'match': 'Economist',        'req': [_M, _EC],          'rec': [_BS, _HI],         'ben': [_GE]},
    {'match': 'Business Anal',    'req': [_M, _BS, _EC],     'rec': [_E, _CS],          'ben': []},
    {'match': 'Entrepreneur',     'req': [_BS, _EC],         'rec': [_M, _E],           'ben': [_CS]},
    {'match': 'Marketing',        'req': [_BS, _E],          'rec': [_EC, _M],          'ben': [_AR]},
    {'match': 'Human Resources',  'req': [_BS, _E],          'rec': [_EC, _HI],         'ben': [_M]},
    {'match': 'Supply Chain',     'req': [_BS, _M],          'rec': [_EC, _GE],         'ben': [_CS]},
    {'match': 'Logistics',        'req': [_BS, _M],          'rec': [_GE, _EC],         'ben': []},
    {'match': 'Procurement',      'req': [_BS, _M],          'rec': [_EC, _E],          'ben': []},
    {'match': 'Project Manager',  'req': [_M, _BS],          'rec': [_EC, _E],          'ben': [_CS]},
    {'match': 'Tax Consultant',   'req': [_M, _AC, _BS],     'rec': [_EC, _E],          'ben': []},
    {'match': 'Microfinance',     'req': [_M, _BS],          'rec': [_EC, _E],          'ben': []},
    {'match': 'Real Estate',      'req': [_BS, _M, _EC],     'rec': [_E, _GE],          'ben': []},
    {'match': 'Management Cons',  'req': [_M, _BS, _EC],     'rec': [_E],               'ben': [_CS]},
    {'match': 'Brand Manager',    'req': [_BS, _E],          'rec': [_EC, _M],          'ben': [_AR]},
    {'match': 'Financial Plann',  'req': [_M, _EC, _BS],     'rec': [_AC],              'ben': []},

    # ── Education ──────────────────────────────────────────────────────────────
    {'match': 'Teacher',          'req': [_E, _K],           'rec': [_HI, _M],          'ben': [_CR]},
    {'match': 'Lecturer',         'req': [_E, _M],           'rec': [_HI, _EC],         'ben': []},
    {'match': 'Professor',        'req': [_E, _M],           'rec': [_HI, _EC],         'ben': []},
    {'match': 'Education Off',    'req': [_E, _HI],          'rec': [_M, _BS],          'ben': []},
    {'match': 'School Principal', 'req': [_E, _HI, _BS],     'rec': [_M],               'ben': []},
    {'match': 'Special Needs',    'req': [_E, _BIO],         'rec': [_HI, _CR],         'ben': []},
    {'match': 'Early Childhood',  'req': [_E, _HS],          'rec': [_HI, _CR],         'ben': []},
    {'match': 'Curriculum',       'req': [_E, _M],           'rec': [_HI, _CS],         'ben': []},
    {'match': 'TVET',             'req': [_E, _M],           'rec': [_CS, _TD],         'ben': []},
    {'match': 'School Counsell',  'req': [_E, _BIO],         'rec': [_HI, _CR],         'ben': []},
    {'match': 'EdTech',           'req': [_E, _CS],          'rec': [_M, _AR],          'ben': []},
    {'match': 'Educational Tech', 'req': [_E, _CS],          'rec': [_M, _AR],          'ben': []},

    # ── Law & Governance ───────────────────────────────────────────────────────
    {'match': 'Lawyer',           'req': [_E, _HI],          'rec': [_K, _EC],          'ben': [_CR, _IR]},
    {'match': 'Advocate',         'req': [_E, _HI],          'rec': [_K, _EC],          'ben': [_CR, _IR]},
    {'match': 'Judge',            'req': [_E, _HI],          'rec': [_K, _EC],          'ben': [_CR]},
    {'match': 'Magistrate',       'req': [_E, _HI],          'rec': [_K],               'ben': [_CR]},
    {'match': 'Paralegal',        'req': [_E, _HI],          'rec': [_K, _BS],          'ben': []},
    {'match': 'Police',           'req': [_E, _K],           'rec': [_HI, _PE],         'ben': [_CR]},
    {'match': 'Diplomat',         'req': [_E, _HI, _K],      'rec': [_EC, _GE],         'ben': [_FR, _AA]},
    {'match': 'Public Admin',     'req': [_E, _HI],          'rec': [_EC, _M],          'ben': [_BS]},
    {'match': 'Policy',           'req': [_E, _HI, _EC],     'rec': [_M, _GE],          'ben': []},
    {'match': 'Compliance',       'req': [_E, _BS],          'rec': [_EC, _M],          'ben': []},
    {'match': 'Land Economist',   'req': [_M, _EC, _GE],     'rec': [_BS],              'ben': []},
    {'match': 'Military',         'req': [_M, _PH],          'rec': [_E, _HI],          'ben': [_PE]},

    # ── Agriculture & Environment ──────────────────────────────────────────────
    {'match': 'Agronomist',       'req': [_AG, _BIO, _CH],   'rec': [_M, _GE],          'ben': []},
    {'match': 'Horticultur',      'req': [_AG, _BIO],        'rec': [_CH, _GE],         'ben': [_M]},
    {'match': 'Animal Sci',       'req': [_BIO, _AG, _CH],   'rec': [_M],               'ben': [_GE]},
    {'match': 'Farm Manager',     'req': [_AG, _BS],         'rec': [_BIO, _M],         'ben': [_GE]},
    {'match': 'Food Scientist',   'req': [_CH, _BIO, _HS],   'rec': [_M, _AG],          'ben': []},
    {'match': 'Environmental Sci','req': [_BIO, _CH, _GE],   'rec': [_M, _PH],          'ben': []},
    {'match': 'Conservation',     'req': [_BIO, _GE],        'rec': [_CH, _AG],         'ben': []},
    {'match': 'Forestry',         'req': [_BIO, _GE, _AG],   'rec': [_CH, _M],          'ben': []},
    {'match': 'Marine Biol',      'req': [_BIO, _CH, _GE],   'rec': [_M, _PH],          'ben': []},
    {'match': 'Climate',          'req': [_GE, _M, _PH],     'rec': [_CH, _BIO],        'ben': []},
    {'match': 'Environmental Con','req': [_BIO, _CH, _GE],   'rec': [_M],               'ben': []},
    {'match': 'Wildlife',         'req': [_BIO, _GE],        'rec': [_AG, _CH],         'ben': []},
    {'match': 'Hydrologist',      'req': [_GE, _M, _CH],     'rec': [_PH, _BIO],        'ben': []},
    {'match': 'Waste',            'req': [_CH, _BIO],        'rec': [_M, _GE],          'ben': []},
    {'match': 'Aquaculture',      'req': [_BIO, _AG],        'rec': [_CH, _M],          'ben': []},
    {'match': 'Soil Scientist',   'req': [_AG, _CH, _BIO],   'rec': [_M, _GE],          'ben': []},

    # ── Media, Arts & Creative ─────────────────────────────────────────────────
    {'match': 'Journalist',       'req': [_E, _K],           'rec': [_HI, _GE],         'ben': [_CS]},
    {'match': 'Editor',           'req': [_E],               'rec': [_K, _HI],          'ben': [_CS]},
    {'match': 'Author',           'req': [_E],               'rec': [_HI, _K],          'ben': [_CR]},
    {'match': 'Graphic Designer', 'req': [_AR, _CS],         'rec': [_M, _E],           'ben': []},
    {'match': 'Photographer',     'req': [_AR],              'rec': [_PH, _E],          'ben': [_CS]},
    {'match': 'Film',             'req': [_AR, _E],          'rec': [_CS, _HI],         'ben': [_MU]},
    {'match': 'Musician',         'req': [_MU, _E],          'rec': [_M, _K],           'ben': []},
    {'match': 'Interior Design',  'req': [_AR, _M],          'rec': [_TD, _E],          'ben': [_BD]},
    {'match': 'Fashion',          'req': [_AR, _HS],         'rec': [_M, _E],           'ben': []},
    {'match': 'Broadcaster',      'req': [_E, _K],           'rec': [_HI, _AR],         'ben': [_CS]},
    {'match': 'Public Relations', 'req': [_E, _BS],          'rec': [_K, _HI],          'ben': [_AR]},
    {'match': 'Advertising',      'req': [_E, _BS],          'rec': [_AR, _EC],         'ben': [_CS]},
    {'match': 'Architect',        'req': [_M, _PH, _AR],     'rec': [_TD, _BD],         'ben': [_GE]},
    {'match': 'Social Media',     'req': [_E, _BS],          'rec': [_AR, _EC],         'ben': [_CS]},
    {'match': 'Content Creator',  'req': [_E],               'rec': [_CS, _AR],         'ben': [_BS]},
    {'match': 'Translator',       'req': [_E, _K],           'rec': [_FR, _AA],         'ben': [_HI]},
    {'match': 'Art Director',     'req': [_AR, _E],          'rec': [_CS, _BS],         'ben': []},
    {'match': 'Event Manager',    'req': [_E, _BS],          'rec': [_M, _EC],          'ben': [_AR]},

    # ── Tourism & Hospitality ──────────────────────────────────────────────────
    {'match': 'Tourism',          'req': [_GE, _E],          'rec': [_HI, _K],          'ben': [_FR]},
    {'match': 'Hotel',            'req': [_E, _HS, _BS],     'rec': [_EC, _M],          'ben': [_FR]},
    {'match': 'Chef',             'req': [_HS, _E],          'rec': [_CH, _BS],         'ben': []},
    {'match': 'Hospitality',      'req': [_E, _HS],          'rec': [_BS, _K],          'ben': [_FR]},
    {'match': 'Travel Agent',     'req': [_E, _GE],          'rec': [_BS, _HI],         'ben': [_FR]},

    # ── Transport & Aviation ───────────────────────────────────────────────────
    {'match': 'Pilot',            'req': [_M, _PH],          'rec': [_CH, _AV],         'ben': [_E]},
    {'match': 'Air Traffic',      'req': [_M, _PH, _E],      'rec': [_AV, _CS],         'ben': []},
    {'match': 'Shipping',         'req': [_M, _PH, _GE],     'rec': [_E, _BS],          'ben': []},

    # ── Construction & Real Estate ─────────────────────────────────────────────
    {'match': 'Quantity Surv',    'req': [_M, _PH, _BD],     'rec': [_TD, _EC],         'ben': []},
    {'match': 'Land Surv',        'req': [_M, _PH, _GE],     'rec': [_TD],              'ben': [_CS]},
    {'match': 'Urban Plan',       'req': [_GE, _M, _AR],     'rec': [_EC, _PH],         'ben': [_CS]},
    {'match': 'Property',         'req': [_BS, _M],          'rec': [_EC, _GE],         'ben': []},
    {'match': 'Construction',     'req': [_M, _PH, _BD],     'rec': [_TD, _BS],         'ben': []},

    # ── Science & Research ─────────────────────────────────────────────────────
    {'match': 'Research Sci',     'req': [_M, _CH, _BIO],    'rec': [_PH, _E],          'ben': [_CS]},
    {'match': 'Chemist',          'req': [_CH, _M, _PH],     'rec': [_BIO, _E],         'ben': []},
    {'match': 'Physicist',        'req': [_PH, _M, _CH],     'rec': [_CS, _E],          'ben': []},
    {'match': 'Biologist',        'req': [_BIO, _CH, _M],    'rec': [_PH, _GE],         'ben': []},
    {'match': 'Geologist',        'req': [_GE, _M, _CH],     'rec': [_PH, _BIO],        'ben': []},
    {'match': 'Astronomer',       'req': [_PH, _M],          'rec': [_CH, _CS],         'ben': []},
    {'match': 'Statistician',     'req': [_M, _EC],          'rec': [_CS, _PH],         'ben': [_BIO]},
    {'match': 'Mathematician',    'req': [_M, _PH],          'rec': [_CS, _EC],         'ben': []},

    # ── Social Sciences & NGO ──────────────────────────────────────────────────
    {'match': 'Social Worker',    'req': [_E, _HI],          'rec': [_CR, _K],          'ben': [_BIO]},
    {'match': 'Counsellor',       'req': [_E, _BIO],         'rec': [_HI, _CR],         'ben': []},
    {'match': 'Community Dev',    'req': [_E, _GE],          'rec': [_HI, _EC],         'ben': [_AG]},
    {'match': 'NGO',              'req': [_E, _HI],          'rec': [_EC, _GE],         'ben': [_K]},
    {'match': 'Sociologist',      'req': [_E, _HI],          'rec': [_GE, _EC],         'ben': [_M]},
    {'match': 'Anthropologist',   'req': [_E, _HI],          'rec': [_GE, _K],          'ben': []},
    {'match': 'Political',        'req': [_HI, _E],          'rec': [_EC, _GE],         'ben': []},
    {'match': 'Development Work', 'req': [_E, _HI],          'rec': [_EC, _GE],         'ben': []},
    {'match': 'Gender',           'req': [_E, _HI],          'rec': [_EC],              'ben': []},
    {'match': 'Humanitarian',     'req': [_E, _GE],          'rec': [_HI, _BS],         'ben': []},
    {'match': 'County Gov',       'req': [_E, _HI],          'rec': [_BS, _EC],         'ben': []},

    # ── Security & Military ────────────────────────────────────────────────────
    {'match': 'Security Anal',    'req': [_M, _CS],          'rec': [_PH, _E],          'ben': []},
    {'match': 'Fire',             'req': [_PH, _CH, _M],     'rec': [_BIO, _E],         'ben': [_PE]},
    {'match': 'Solar',            'req': [_PH, _M, _EL],     'rec': [_CH, _TD],         'ben': []},

    # ── Sports ────────────────────────────────────────────────────────────────
    {'match': 'Sports Coach',     'req': [_PE, _BIO],        'rec': [_E, _M],           'ben': [_HI]},
    {'match': 'Physical Train',   'req': [_PE, _BIO],        'rec': [_CH, _M],          'ben': []},
    {'match': 'Sports Manager',   'req': [_PE, _BS],         'rec': [_E, _M],           'ben': []},
    {'match': 'Athletics',        'req': [_PE, _BIO],        'rec': [_M, _E],           'ben': []},
    {'match': 'Recreation',       'req': [_PE, _BS],         'rec': [_E, _M],           'ben': []},
]


class Command(BaseCommand):
    help = 'Populate CareerSubject subject-to-career mappings for academic scoring'

    def handle(self, *args, **options):
        # ── Step 1: Deduplicate existing Subject records ──────────────────
        self._deduplicate_subjects()

        # ── Step 2: Ensure all KCSE subjects exist with correct fields ────
        subj_map = self._ensure_subjects()
        self.stdout.write(f'Subjects ready: {len(subj_map)}')

        # ── Step 3: Match careers and create CareerSubject records ─────────
        all_careers   = list(Career.objects.all())
        total_created = 0
        total_matched = 0
        matched_ids   = set()

        with transaction.atomic():
            for entry in CAREER_SUBJECTS:
                fragment = entry['match'].lower()
                matched  = [c for c in all_careers if fragment in c.name.lower()]

                for career in matched:
                    matched_ids.add(career.id)
                    total_matched += 1
                    for subj_name in entry.get('req', []):
                        subj = subj_map.get(subj_name)
                        if subj:
                            _, created = CareerSubject.objects.get_or_create(
                                career=career, subject=subj,
                                defaults={'importance': 'required'}
                            )
                            if created:
                                total_created += 1

                    for subj_name in entry.get('rec', []):
                        subj = subj_map.get(subj_name)
                        if subj:
                            _, created = CareerSubject.objects.get_or_create(
                                career=career, subject=subj,
                                defaults={'importance': 'recommended'}
                            )
                            if created:
                                total_created += 1

                    for subj_name in entry.get('ben', []):
                        subj = subj_map.get(subj_name)
                        if subj:
                            _, created = CareerSubject.objects.get_or_create(
                                career=career, subject=subj,
                                defaults={'importance': 'beneficial'}
                            )
                            if created:
                                total_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {total_created} new CareerSubject records created '
            f'across {total_matched} career-entry matches.\n'
            f'Total CareerSubject records: {CareerSubject.objects.count()}'
        ))

        unmatched = [c.name for c in all_careers if c.id not in matched_ids]
        if unmatched:
            self.stdout.write(self.style.WARNING(
                f'\n{len(unmatched)} careers without subject mappings:'
            ))
            for name in sorted(unmatched)[:20]:
                self.stdout.write(f'  - {name}')

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _deduplicate_subjects(self):
        """
        Remove duplicate Subject records that have the same name.
        Keeps the record with the lowest pk and re-points any CareerSubject
        FK references before deleting duplicates.
        """
        from django.db.models import Count
        dupes = (
            Subject.objects
            .values('name')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
        )
        removed = 0
        for d in dupes:
            records = list(Subject.objects.filter(name=d['name']).order_by('id'))
            keeper = records[0]
            for stale in records[1:]:
                # Re-point CareerSubject rows to the keeper
                CareerSubject.objects.filter(subject=stale).update(subject=keeper)
                stale.delete()
                removed += 1
        if removed:
            self.stdout.write(self.style.WARNING(
                f'Deduplicated {removed} duplicate Subject record(s).'
            ))

    def _ensure_subjects(self):
        """
        Create or update all KCSE subjects, return a {name: Subject} map.
        Uses filter().first() so duplicates never cause MultipleObjectsReturned.
        """
        subj_map = {}
        for name, code, category, is_compulsory in KCSE_SUBJECTS:
            # Try to find by code first (guaranteed unique), then by name
            obj = Subject.objects.filter(code=code).first()
            if obj is None:
                obj = Subject.objects.filter(name=name).first()

            if obj is None:
                obj = Subject.objects.create(
                    name=name, code=code,
                    category=category,
                    is_compulsory=is_compulsory,
                    description=f'KCSE subject: {name}',
                    difficulty_level='medium',
                )
            else:
                # Update fields in case they're stale
                updated = False
                if obj.code != code:
                    obj.code = code; updated = True
                if obj.category != category:
                    obj.category = category; updated = True
                if updated:
                    obj.save()

            subj_map[name] = obj
        return subj_map
