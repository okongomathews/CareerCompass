"""
recommendations/ml_models.py

Machine Learning Models for CareerCompass Kenya
================================================
Provides predictive analytics, market trend analysis, personalized
learning path optimization, and adaptive assessment capabilities.

Author: CareerCompass Kenya Development Team
Version: 1.0.0
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class CareerSuccessPredictor:
    """
    Predicts the probability of a student succeeding in a given career
    based on their personality profile, academic performance, and
    Kenyan market conditions.

    Uses a weighted multi-factor scoring model:
    - Personality alignment: 35%
    - Academic performance: 30%
    - Market demand: 20%
    - Learning style fit: 15%
    """

    WEIGHTS = {
        'personality_match': 0.35,
        'academic_performance': 0.30,
        'market_demand': 0.20,
        'learning_style_fit': 0.15,
    }

    PERFORMANCE_MAP = {
        'excellent': 1.0,
        'good': 0.80,
        'average': 0.60,
        'below_average': 0.40,
        'poor': 0.20,
        'not_applicable': 0.50,
    }

    DEMAND_MAP = {
        'very_high': 1.0,
        'high': 0.80,
        'medium': 0.60,
        'low': 0.40,
        'very_low': 0.20,
    }

    def predict_success_probability(self, student, career):
        """
        Predict success probability (0.0 – 1.0) for a student-career pair.

        Args:
            student (StudentProfile): The student's profile instance.
            career (Career): The career model instance.

        Returns:
            float: Probability score between 0 and 1.
        """
        try:
            personality_score = self._personality_component(student, career)
            academic_score = self._academic_component(student, career)
            market_score = self._market_component(career)
            learning_score = self._learning_component(student, career)

            total = (
                personality_score * self.WEIGHTS['personality_match']
                + academic_score * self.WEIGHTS['academic_performance']
                + market_score * self.WEIGHTS['market_demand']
                + learning_score * self.WEIGHTS['learning_style_fit']
            )

            return round(min(max(total, 0.0), 1.0), 4)

        except Exception as exc:
            logger.error("CareerSuccessPredictor error: %s", exc, exc_info=True)
            return 0.5

    # ------------------------------------------------------------------ #
    #  Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _personality_component(self, student, career):
        """Return personality-career compatibility score (0-1)."""
        try:
            from assessments.models import AssessmentResult
            from recommendations.models import CareerPersonalityMatch

            assessment = AssessmentResult.objects.get(student=student)
            match = CareerPersonalityMatch.objects.get(
                career=career,
                personality_type=assessment.personality_type,
            )
            # match_score is stored as 0.00 – 1.00 per model definition
            return float(match.match_score)
        except Exception:
            return 0.5

    def _academic_component(self, student, career):
        """Return academic-fitness score based on subjects and performance."""
        try:
            base = self.PERFORMANCE_MAP.get(
                getattr(student, 'academic_performance', 'average'), 0.5
            )

            student_subjects = set(
                student.subjects.values_list('name', flat=True)
            )
            required_subjects = set(
                career.required_subjects.values_list('name', flat=True)
            )

            if required_subjects:
                overlap = len(student_subjects & required_subjects)
                alignment = overlap / len(required_subjects)
                base = (base + alignment) / 2.0

            return min(base, 1.0)
        except Exception:
            return 0.5

    def _market_component(self, career):
        """Return Kenyan market demand score (0-1)."""
        return self.DEMAND_MAP.get(
            getattr(career, 'kenyan_market_demand', 'medium'), 0.5
        )

    def _learning_component(self, student, career):
        """Return learning-style alignment score (0-1)."""
        try:
            from ai_coach.models import CoachingPlan
            from recommendations.models import CareerLearningStyle

            plan = CoachingPlan.objects.get(student=student)
            match = CareerLearningStyle.objects.get(
                career=career,
                learning_style=plan.learning_style,
            )
            return float(match.match_score)
        except Exception:
            return 0.5


# ====================================================================== #
#  Market Trend Analyzer                                                   #
# ====================================================================== #

class MarketTrendAnalyzer:
    """
    Analyzes Kenyan job-market trends and produces short-term demand
    forecasts. Data is based on published Kenyan labour-market reports
    (Kenya National Bureau of Statistics, World Bank Kenya Reports).
    """

    # Sector growth rates are annual percentages based on 2023-2024 data
    SECTOR_TRENDS = {
        'technology': {
            'growth_rate': 0.30,
            'trajectory': 'rising',
            'key_skills': ['Python', 'Data Science', 'Cloud Computing', 'AI/ML', 'Cybersecurity'],
            'top_employers': ['Safaricom', 'Andela', "Africa's Talking", 'Copia', 'NCBA Bank'],
            'avg_salary_kes': 150_000,
        },
        'healthcare': {
            'growth_rate': 0.25,
            'trajectory': 'rising',
            'key_skills': ['Clinical Practice', 'Patient Care', 'Medical Research', 'Public Health'],
            'top_employers': [
                'Kenyatta National Hospital', 'Ministry of Health',
                'Aga Khan Hospital', 'MP Shah Hospital',
            ],
            'avg_salary_kes': 100_000,
        },
        'finance': {
            'growth_rate': 0.20,
            'trajectory': 'stable',
            'key_skills': ['CPA', 'Financial Analysis', 'Risk Management', 'FinTech'],
            'top_employers': ['KCB', 'Equity Bank', 'KPMG', 'Deloitte', 'PwC'],
            'avg_salary_kes': 130_000,
        },
        'education': {
            'growth_rate': 0.15,
            'trajectory': 'stable',
            'key_skills': ['Teaching', 'Curriculum Design', 'Assessment', 'EdTech'],
            'top_employers': ['TSC', 'Universities', 'Private Schools', 'NGOs'],
            'avg_salary_kes': 60_000,
        },
        'agriculture': {
            'growth_rate': 0.20,
            'trajectory': 'rising',
            'key_skills': ['Agronomy', 'Food Science', 'Supply Chain', 'AgriTech'],
            'top_employers': [
                'Ministry of Agriculture', 'Cooperatives',
                'Twiga Foods', 'Farm-to-Market Alliance',
            ],
            'avg_salary_kes': 80_000,
        },
        'engineering': {
            'growth_rate': 0.22,
            'trajectory': 'rising',
            'key_skills': ['Project Management', 'CAD', 'Technical Design', 'Renewable Energy'],
            'top_employers': ['KENHA', 'KPLC', 'KETRACO', 'Large Construction Firms'],
            'avg_salary_kes': 120_000,
        },
        'tourism': {
            'growth_rate': 0.18,
            'trajectory': 'recovering',
            'key_skills': ['Hospitality', 'Tour Guiding', 'Event Management', 'Marketing'],
            'top_employers': [
                'Kenya Tourism Board', 'Sarova Hotels',
                'Fairmont Hotels', 'Tour Operators',
            ],
            'avg_salary_kes': 70_000,
        },
        'law': {
            'growth_rate': 0.12,
            'trajectory': 'stable',
            'key_skills': ['Legal Research', 'Advocacy', 'Contract Law', 'Litigation'],
            'top_employers': [
                'Kenya Law Reform Commission', 'Law Firms',
                'Corporate Legal Departments', 'Judiciary',
            ],
            'avg_salary_kes': 110_000,
        },
        'default': {
            'growth_rate': 0.10,
            'trajectory': 'stable',
            'key_skills': ['Communication', 'Problem Solving', 'Leadership', 'Digital Literacy'],
            'top_employers': ['Various Kenyan organisations'],
            'avg_salary_kes': 65_000,
        },
    }

    DEMAND_ORDER = ['very_low', 'low', 'medium', 'high', 'very_high']

    def predict_future_demand(self, career, months_ahead=12):
        """
        Project future market demand level for a career.

        Args:
            career (Career): Career model instance.
            months_ahead (int): Forecast horizon in months.

        Returns:
            str: Predicted demand level key (e.g. 'high').
        """
        try:
            current_demand = getattr(career, 'kenyan_market_demand', 'medium')
            trend = self._find_trend(career)

            current_idx = self.DEMAND_ORDER.index(current_demand) \
                if current_demand in self.DEMAND_ORDER else 2

            annual_growth = trend.get('growth_rate', 0.10)
            period_growth = annual_growth * (months_ahead / 12.0)

            if period_growth >= 0.25:
                shift = 2
            elif period_growth >= 0.15:
                shift = 1
            else:
                shift = 0

            new_idx = min(current_idx + shift, len(self.DEMAND_ORDER) - 1)
            return self.DEMAND_ORDER[new_idx]

        except Exception as exc:
            logger.error("MarketTrendAnalyzer error: %s", exc, exc_info=True)
            return getattr(career, 'kenyan_market_demand', 'medium')

    def analyze_career_trends(self):
        """
        Return a dictionary of sector-level market trends.

        Returns:
            dict: Sector → trend data mapping.
        """
        return {
            sector: {
                'growth_rate': data['growth_rate'],
                'trajectory': data['trajectory'],
                'key_skills': data['key_skills'],
                'average_salary_kes': data['avg_salary_kes'],
            }
            for sector, data in self.SECTOR_TRENDS.items()
            if sector != 'default'
        }

    def get_sector_insights(self, career):
        """Return sector-specific insights for a career."""
        return self._find_trend(career)

    # ------------------------------------------------------------------ #
    #  Private helper                                                       #
    # ------------------------------------------------------------------ #

    def _find_trend(self, career):
        """Locate the matching sector trend for a career."""
        category = getattr(career, 'category', '').lower()
        career_name = career.name.lower()

        for sector, data in self.SECTOR_TRENDS.items():
            if sector == 'default':
                continue
            if sector in category or sector in career_name:
                return data

        return self.SECTOR_TRENDS['default']


# ====================================================================== #
#  Personalised Learning Path Optimizer                                    #
# ====================================================================== #

class PersonalizedLearningPathOptimizer:
    """
    Generates and optimises personalised learning paths for students
    targeting specific careers in the Kenyan context.
    """

    COMPLEXITY_YEARS = {
        'very_high': (7, 10),
        'high': (5, 7),
        'medium': (3, 5),
        'low': (1, 3),
    }

    def __init__(self, student):
        self.student = student
        self._profile = self._build_profile()

    def optimize_learning_path(self, career, current_path):
        """
        Return an enriched, Kenya-contextualised learning path.

        Args:
            career (Career): Target career.
            current_path (dict | list): Existing path structure to enrich.

        Returns:
            dict: Optimised learning path.
        """
        return {
            'career': career.name,
            'student_snapshot': self._profile,
            'phases': self._build_phases(career),
            'quick_wins': self._quick_wins(career),
            'kenyan_resources': self._kenyan_resources(career),
            'estimated_duration': self._estimate_duration(career),
            'key_milestones': self._milestones(career),
            'scholarship_options': self._scholarships(),
        }

    # ------------------------------------------------------------------ #

    def _build_profile(self):
        profile = {
            'grade_level': getattr(self.student, 'grade_level', 'form4'),
            'academic_performance': getattr(self.student, 'academic_performance', 'good'),
            'subjects': [],
            'personality_type': None,
            'learning_style': None,
        }
        try:
            profile['subjects'] = list(
                self.student.subjects.values_list('name', flat=True)
            )
        except Exception:
            pass
        try:
            profile['personality_type'] = (
                self.student.assessmentresult.personality_type.mbti_type
            )
        except Exception:
            pass
        try:
            from ai_coach.models import CoachingPlan
            plan = CoachingPlan.objects.get(student=self.student)
            profile['learning_style'] = (
                plan.learning_style.name if plan.learning_style else None
            )
        except Exception:
            pass
        return profile

    def _build_phases(self, career):
        complexity = getattr(career, 'complexity_level', 'medium')

        if complexity in ('very_high', 'high'):
            phases = [
                {
                    'phase': 'Academic Foundation (Years 1-2)',
                    'focus': [
                        'Achieve target KCSE grade',
                        f'Master prerequisite subjects for {career.name}',
                        'Attend university open days',
                    ],
                    'priority': 'CRITICAL',
                },
                {
                    'phase': 'Undergraduate Studies (Years 3-6)',
                    'focus': [
                        'Complete degree programme',
                        'Secure industrial attachment / internship',
                        'Join professional student associations',
                        'Build a portfolio or research record',
                    ],
                    'priority': 'HIGH',
                },
                {
                    'phase': 'Professional Certification (Years 6-8)',
                    'focus': [
                        'Obtain mandatory licences or certifications',
                        'First full-time employment',
                        'Build a professional network',
                    ],
                    'priority': 'HIGH',
                },
                {
                    'phase': 'Career Growth (Year 8 onwards)',
                    'focus': [
                        'Pursue postgraduate studies if required',
                        'Take leadership roles',
                        'Mentor upcoming professionals',
                        'Consider entrepreneurship',
                    ],
                    'priority': 'MEDIUM',
                },
            ]
        else:
            phases = [
                {
                    'phase': 'Skills Foundation (Year 1)',
                    'focus': [
                        'Complete KCSE',
                        'Identify practical training institutions',
                        'Develop digital literacy',
                    ],
                    'priority': 'CRITICAL',
                },
                {
                    'phase': 'Vocational / Diploma Training (Years 2-3)',
                    'focus': [
                        'Enrol at a TVET or college',
                        'Complete attachment / work placement',
                        'Obtain industry certifications',
                    ],
                    'priority': 'HIGH',
                },
                {
                    'phase': 'Entry-Level Employment (Year 4)',
                    'focus': [
                        'Apply for entry-level positions',
                        'Build experience portfolio',
                        'Join relevant industry associations',
                    ],
                    'priority': 'HIGH',
                },
                {
                    'phase': 'Career Advancement (Year 5+)',
                    'focus': [
                        'Upgrade qualifications (degree top-up)',
                        'Pursue specialisation',
                        'Grow professional network',
                    ],
                    'priority': 'MEDIUM',
                },
            ]

        # Personalise tips based on learning style
        style = self._profile.get('learning_style')
        style_tips = {
            'visual': 'Use mind maps, diagrams, and video resources.',
            'auditory': 'Form study groups and listen to recorded lectures.',
            'reading': 'Take detailed notes and read widely beyond class materials.',
            'kinesthetic': 'Prioritise practical labs, internships, and projects.',
        }
        tip = style_tips.get(style, 'Experiment to discover your best study methods.')
        for phase in phases:
            phase['learning_tip'] = tip

        return phases

    def _quick_wins(self, career):
        """Return a list of immediately actionable steps."""
        wins = [
            'Research the career on LinkedIn and reach out to 3 professionals.',
            'Visit your school/university career guidance office this week.',
            'Identify 2 universities or colleges offering relevant programmes.',
            'Subscribe to a free online course related to this career (Coursera, edX).',
        ]
        name_lower = career.name.lower()
        if any(k in name_lower for k in ('software', 'data', 'tech', 'cyber', 'ai', 'it')):
            wins.append('Create a free GitHub account and start a beginner project today.')
        elif any(k in name_lower for k in ('doctor', 'nurse', 'medical', 'health', 'pharma')):
            wins.append('Volunteer at a local dispensary or county hospital.')
        elif any(k in name_lower for k in ('business', 'finance', 'accountant', 'banker')):
            wins.append('Register for CPA Part 1 examinations via KASNEB.')
        elif any(k in name_lower for k in ('teacher', 'lecturer', 'educator')):
            wins.append('Apply to TSC for a temporary teaching licence.')
        return wins[:5]

    def _kenyan_resources(self, career):
        return {
            'government_programmes': [
                'Youth Enterprise Development Fund (YEDF)',
                'Kenya Youth Employment & Opportunities Project (KYEOP)',
                'TVET Authority accredited programmes',
                'National Industrial Training Authority (NITA)',
            ],
            'scholarships': [
                'Higher Education Loans Board (HELB)',
                'Equity Wings to Fly',
                'Mastercard Foundation Scholars Programme',
                'County Government Bursaries (check your specific county)',
                'KCB Foundation Scholarship',
            ],
            'online_platforms': [
                'Coursera – financial aid available',
                'edX Africa',
                'Alison (free certificates)',
                'Khan Academy',
                'YouTube channels by Kenyan educators',
            ],
            'local_institutions': [
                'Kenya Institute of Management (KIM)',
                'Strathmore University continuing education',
                'Kenya National Examinations Council (KNEC) resources',
                'Public Universities open learning programmes',
            ],
        }

    def _estimate_duration(self, career):
        complexity = getattr(career, 'complexity_level', 'medium')
        lo, hi = self.COMPLEXITY_YEARS.get(complexity, (3, 5))
        return f'{lo}–{hi} years to full career readiness in Kenya'

    def _milestones(self, career):
        return [
            f'Achieve KCSE grade required for {career.name} programmes.',
            'Gain admission through KUCCPS or direct entry.',
            'Complete Year 1 with a minimum GPA that maintains scholarship eligibility.',
            'Secure first internship or industrial attachment.',
            f'Graduate with the relevant qualification for {career.name}.',
            'Obtain required professional registration / certification.',
            'Land first full-time position in the field.',
            'Complete 2 years of post-qualification experience.',
            'Begin specialisation or postgraduate studies.',
        ]

    def _scholarships(self):
        return [
            {'name': 'HELB Loan & Bursary', 'url': 'https://www.helb.co.ke'},
            {'name': 'Equity Wings to Fly', 'url': 'https://www.equitygroupfoundation.com'},
            {
                'name': 'Mastercard Foundation Scholars',
                'url': 'https://mastercardfdn.org/all/scholars/',
            },
        ]


# ====================================================================== #
#  Adaptive Assessment System                                              #
# ====================================================================== #

class AdaptiveAssessmentSystem:
    """
    Adapts assessment parameters (difficulty, pacing hints) based on
    a student's prior response patterns, ensuring a fairer and more
    accurate personality profiling experience.
    """

    LEVELS = {
        'foundation': {
            'question_difficulty': 'standard',
            'time_guidance_seconds': 45,
            'description': 'Take your time – there is no rush.',
        },
        'intermediate': {
            'question_difficulty': 'moderate',
            'time_guidance_seconds': 30,
            'description': 'Aim for thoughtful but reasonably paced answers.',
        },
        'advanced': {
            'question_difficulty': 'nuanced',
            'time_guidance_seconds': 20,
            'description': 'Trust your instincts – you are doing great.',
        },
    }

    def adapt_assessment(self, previous_responses):
        """
        Return an adapted assessment configuration dict.

        Args:
            previous_responses (list[dict]): Each dict may contain
                'response_time' (seconds) and optional 'is_correct' keys.

        Returns:
            dict: Configuration with level, guidance, and personalisation.
        """
        if not previous_responses:
            return self._config('foundation')

        avg_time = self._avg_time(previous_responses)
        consistency = self._consistency(previous_responses)

        if avg_time < 10 and consistency > 0.80:
            level = 'advanced'
        elif avg_time < 25 and consistency > 0.60:
            level = 'intermediate'
        else:
            level = 'foundation'

        cfg = self._config(level)
        cfg['personalisation'] = {
            'avg_response_time_seconds': round(avg_time, 1),
            'consistency_score': round(consistency, 2),
            'pacing_advice': self._pacing_advice(avg_time),
        }
        return cfg

    # ------------------------------------------------------------------ #

    def _config(self, level):
        data = self.LEVELS[level].copy()
        data['level'] = level
        return data

    def _avg_time(self, responses):
        times = [r['response_time'] for r in responses if r.get('response_time')]
        return (sum(times) / len(times)) if times else 15.0

    def _consistency(self, responses):
        """Lower variance relative to mean → higher consistency."""
        times = [r['response_time'] for r in responses if r.get('response_time')]
        if len(times) < 3:
            return 0.5
        mean = sum(times) / len(times)
        variance = sum((t - mean) ** 2 for t in times) / len(times)
        std = variance ** 0.5
        return max(0.0, min(1.0, 1.0 - std / (mean + 1.0)))

    def _pacing_advice(self, avg_time):
        if avg_time < 5:
            return 'You are answering very quickly. Take a moment to reflect on each question.'
        if avg_time > 60:
            return 'Trust your first instinct – overthinking can reduce accuracy.'
        return 'Your response pace is good. Keep it up!'