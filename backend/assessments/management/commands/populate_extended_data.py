"""
Comprehensive data population script for CareerCompass Kenya.
Fixes the INTJ bias and creates complete dataset.
Run: python manage.py populate_extended_data
"""
from django.core.management.base import BaseCommand
import random
from datetime import datetime

from django.contrib.auth import get_user_model
from users.models import School, StudentProfile, CustomUser
from assessments.models import (
    MBTIDimension, Question, AnswerChoice, PersonalityType
)
from recommendations.models import (
    Career, Subject, LearningStyle, CareerPersonalityMatch,
    CareerLearningStyle, CareerSubject
)

class Command(BaseCommand):
    help = 'Populates comprehensive extended data for CareerCompass Kenya including MBTI dimensions, questions, careers, and relationships'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + "="*70))
        self.stdout.write(self.style.SUCCESS("COMPREHENSIVE DATA POPULATION FOR CAREERCOMPASS KENYA"))
        self.stdout.write(self.style.SUCCESS("Fixing INTJ bias and creating complete dataset"))
        self.stdout.write(self.style.SUCCESS("="*70))
        
        start_time = datetime.now()
        
        # Execute all population functions
        self.create_mbti_dimensions()
        self.create_personality_types()
        self.create_balanced_mbti_questions()
        self.create_learning_styles()
        self.create_kcse_subjects()
        self.create_kenyan_careers()
        self.create_career_personality_matches()
        self.create_career_learning_style_matches()
        self.create_kenyan_schools()
        self.create_admin_user()
        self.create_demo_student()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*70))
        self.stdout.write(self.style.SUCCESS("DATA POPULATION COMPLETE!"))
        self.stdout.write(self.style.SUCCESS("="*70))
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f"\n📊 DATABASE SUMMARY:"))
        self.stdout.write(f"   • MBTI Dimensions: {MBTIDimension.objects.count()}")
        self.stdout.write(f"   • Personality Types: {PersonalityType.objects.count()}")
        self.stdout.write(f"   • MBTI Questions: {Question.objects.count()}")
        self.stdout.write(f"   • Answer Choices: {AnswerChoice.objects.count()}")
        self.stdout.write(f"   • Learning Styles: {LearningStyle.objects.count()}")
        self.stdout.write(f"   • KCSE Subjects: {Subject.objects.count()}")
        self.stdout.write(f"   • Kenyan Careers: {Career.objects.count()}")
        self.stdout.write(f"   • Career-Personality Matches: {CareerPersonalityMatch.objects.count()}")
        self.stdout.write(f"   • Career-Learning Style Matches: {CareerLearningStyle.objects.count()}")
        self.stdout.write(f"   • Kenyan Schools: {School.objects.count()}")
        
        self.stdout.write(self.style.SUCCESS(f"\n⏱️  Execution time: {duration.total_seconds():.2f} seconds"))
        
        self.stdout.write(self.style.SUCCESS(f"\n🔑 LOGIN CREDENTIALS:"))
        self.stdout.write(f"   • Admin: admin / admin")
        self.stdout.write(f"   • Demo Student: demo_student / Demo@1234")
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ The INTJ bias issue has been fixed by:"))
        self.stdout.write(f"   1. Creating 64 balanced MBTI questions (16 per dimension)")
        self.stdout.write(f"   2. Using 7-point Likert scale for nuanced responses")
        self.stdout.write(f"   3. Balanced weighting for all personality dimensions")
        self.stdout.write(f"   4. Research-based career-personality compatibility scores")
        self.stdout.write(f"   5. Comprehensive dataset with accurate Kenyan context")
        
        self.stdout.write(self.style.SUCCESS(f"\n🚀 Next steps:"))
        self.stdout.write(f"   1. Run: python manage.py runserver")
        self.stdout.write(f"   2. Visit: http://127.0.0.1:8000/admin")
        self.stdout.write(f"   3. Login with admin credentials")
        self.stdout.write(f"   4. Test the assessment system")
    
    def print_step(self, message):
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"STEP: {message}")
        self.stdout.write('='*60)

    def create_mbti_dimensions(self):
        """Create scientifically balanced MBTI dimensions"""
        self.print_step("Creating MBTI Dimensions")
        
        dimensions = [
            {
                'code': 'EI',
                'dimension_a': 'Extraversion',
                'dimension_b': 'Introversion',
                'description': 'Where you direct your energy and attention'
            },
            {
                'code': 'SN',
                'dimension_a': 'Sensing',
                'dimension_b': 'Intuition',
                'description': 'How you take in and process information'
            },
            {
                'code': 'TF',
                'dimension_a': 'Thinking',
                'dimension_b': 'Feeling',
                'description': 'How you make decisions and judgments'
            },
            {
                'code': 'JP',
                'dimension_a': 'Judging',
                'dimension_b': 'Perceiving',
                'description': 'How you approach the outside world'
            }
        ]
        
        for dim in dimensions:
            MBTIDimension.objects.get_or_create(
                code=dim['code'],
                defaults=dim
            )
        self.stdout.write(self.style.SUCCESS("✓ Created 4 MBTI Dimensions"))

    def create_personality_types(self):
        """Create all 16 MBTI personality types with accurate descriptions"""
        self.print_step("Creating Personality Types")
        
        personality_types = [
            {
                'mbti_type': 'INTJ',
                'name': 'The Architect',
                'description': 'Strategic thinkers who enjoy complex problems and long-term planning.',
                'strengths': 'Strategic, independent, determined, insightful, original',
                'weaknesses': 'Arrogant, dismissive of emotions, overly critical, socially awkward',
                'career_recommendations': 'Strategic Planner, Research Scientist, Systems Analyst, University Professor',
                'population_percentage': 2.1
            },
            {
                'mbti_type': 'INTP',
                'name': 'The Logician',
                'description': 'Innovative inventors with an unquenchable thirst for knowledge.',
                'strengths': 'Analytical, original, open-minded, curious, objective',
                'weaknesses': 'Insensitive, absent-minded, condescending, socially clueless',
                'career_recommendations': 'Software Developer, Mathematician, Philosopher, Research Scientist',
                'population_percentage': 3.3
            },
            {
                'mbti_type': 'ENTJ',
                'name': 'The Commander',
                'description': 'Bold, imaginative and strong-willed leaders.',
                'strengths': 'Efficient, energetic, self-confident, strong-willed, strategic',
                'weaknesses': 'Stubborn, dominating, impatient, intolerant',
                'career_recommendations': 'CEO, Corporate Executive, Lawyer, Judge, Military Officer',
                'population_percentage': 1.8
            },
            {
                'mbti_type': 'ENTP',
                'name': 'The Debater',
                'description': 'Smart and curious thinkers who enjoy intellectual challenges.',
                'strengths': 'Knowledgeable, quick-thinking, original, excellent brainstormer',
                'weaknesses': 'Argumentative, insensitive, intolerant, unfocused',
                'career_recommendations': 'Entrepreneur, Lawyer, Psychologist, Engineer, Journalist',
                'population_percentage': 3.2
            },
            {
                'mbti_type': 'INFJ',
                'name': 'The Advocate',
                'description': 'Quiet and mystical, yet inspiring idealists.',
                'strengths': 'Creative, insightful, principled, passionate, altruistic',
                'weaknesses': 'Sensitive to criticism, perfectionistic, prone to burnout',
                'career_recommendations': 'Counselor, Psychologist, Writer, Teacher, Social Worker',
                'population_percentage': 1.5
            },
            {
                'mbti_type': 'INFP',
                'name': 'The Mediator',
                'description': 'Poetic, kind and altruistic helpers.',
                'strengths': 'Empathetic, creative, idealistic, open-minded, flexible',
                'weaknesses': 'Unrealistic, self-critical, impractical, emotionally vulnerable',
                'career_recommendations': 'Writer, Artist, Counselor, Psychologist, Librarian',
                'population_percentage': 4.4
            },
            {
                'mbti_type': 'ENFJ',
                'name': 'The Protagonist',
                'description': 'Charismatic and inspiring leaders.',
                'strengths': 'Charismatic, empathetic, natural leader, organized, reliable',
                'weaknesses': 'Overly idealistic, too selfless, fluctuating self-esteem',
                'career_recommendations': 'Teacher, Counselor, Politician, Human Resources, Event Planner',
                'population_percentage': 2.5
            },
            {
                'mbti_type': 'ENFP',
                'name': 'The Campaigner',
                'description': 'Enthusiastic, creative and sociable free spirits.',
                'strengths': 'Curious, perceptive, enthusiastic, excellent communicator',
                'weaknesses': 'Poor practical skills, unfocused, overly accommodating',
                'career_recommendations': 'Journalist, Actor, Designer, Social Worker, Public Relations',
                'population_percentage': 8.1
            },
            {
                'mbti_type': 'ISTJ',
                'name': 'The Logistician',
                'description': 'Practical and fact-minded individuals.',
                'strengths': 'Honest, direct, responsible, calm, practical',
                'weaknesses': 'Stubborn, insensitive, judgmental, unimaginative',
                'career_recommendations': 'Accountant, Auditor, Police Officer, Administrator, Military Officer',
                'population_percentage': 11.6
            },
            {
                'mbti_type': 'ISFJ',
                'name': 'The Defender',
                'description': 'Very dedicated and warm protectors.',
                'strengths': 'Supportive, reliable, patient, practical, hardworking',
                'weaknesses': 'Overly humble, overload themselves, reluctant to change',
                'career_recommendations': 'Nurse, Teacher, Librarian, Social Worker, Accountant',
                'population_percentage': 13.8
            },
            {
                'mbti_type': 'ESTJ',
                'name': 'The Executive',
                'description': 'Excellent administrators and managers.',
                'strengths': 'Dedicated, strong-willed, direct, loyal, hardworking',
                'weaknesses': 'Inflexible, bossy, insensitive, stubborn',
                'career_recommendations': 'Manager, Administrator, Police Officer, Judge, Project Manager',
                'population_percentage': 8.7
            },
            {
                'mbti_type': 'ESFJ',
                'name': 'The Consul',
                'description': 'Caring, social and popular helpers.',
                'strengths': 'Practical, caring, sociable, popular, strong practical skills',
                'weaknesses': 'Worry too much, overly sensitive, inflexible',
                'career_recommendations': 'Teacher, Nurse, Social Worker, Human Resources, Sales',
                'population_percentage': 12.3
            },
            {
                'mbti_type': 'ISTP',
                'name': 'The Virtuoso',
                'description': 'Bold and practical experimenters.',
                'strengths': 'Optimistic, creative, spontaneous, practical, rational',
                'weaknesses': 'Easily bored, risky, private, insensitive',
                'career_recommendations': 'Mechanic, Engineer, Pilot, Athlete, Computer Technician',
                'population_percentage': 5.4
            },
            {
                'mbti_type': 'ISFP',
                'name': 'The Adventurer',
                'description': 'Flexible and charming artists.',
                'strengths': 'Charming, sensitive to others, imaginative, artistic, practical',
                'weaknesses': 'Easily stressed, overly competitive, unpredictable',
                'career_recommendations': 'Artist, Designer, Chef, Nurse, Physical Therapist',
                'population_percentage': 8.8
            },
            {
                'mbti_type': 'ESTP',
                'name': 'The Entrepreneur',
                'description': 'Smart, energetic and perceptive risk-takers.',
                'strengths': 'Bold, practical, original, perceptive, direct',
                'weaknesses': 'Impatient, risk-prone, unstructured, insensitive',
                'career_recommendations': 'Entrepreneur, Salesperson, Police Officer, Athlete, Marketing',
                'population_percentage': 4.3
            },
            {
                'mbti_type': 'ESFP',
                'name': 'The Entertainer',
                'description': 'Spontaneous, energetic and enthusiastic entertainers.',
                'strengths': 'Enthusiastic, practical, observant, excellent at networking',
                'weaknesses': 'Sensitive, conflict-avoidant, easily bored, poor planners',
                'career_recommendations': 'Actor, Event Planner, Teacher, Nurse, Customer Service',
                'population_percentage': 8.5
            }
        ]
        
        for pt in personality_types:
            PersonalityType.objects.get_or_create(
                mbti_type=pt['mbti_type'],
                defaults={
                    'name': pt['name'],
                    'description': pt['description'],
                    'strengths': pt['strengths'],
                    'weaknesses': pt['weaknesses'],
                    'career_recommendations': pt['career_recommendations']
                }
            )
        self.stdout.write(self.style.SUCCESS(f"✓ Created 16 Personality Types"))

    def create_balanced_mbti_questions(self):
        """Create 64 scientifically balanced MBTI questions (16 per dimension)"""
        self.print_step("Creating Balanced MBTI Questions")
        
        # First, delete existing questions to avoid duplicates
        Question.objects.all().delete()
        
        # =============== EI DIMENSION (Extraversion vs Introversion) ===============
        ei_questions = [
            # Questions favoring Extraversion (8 questions)
            {
                'text': 'You feel energized after spending time with a large group of people',
                'category': 'EI',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You enjoy being the center of attention in social situations',
                'category': 'EI',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You are talkative and outgoing in group settings',
                'category': 'EI',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You prefer working in teams rather than alone',
                'category': 'EI',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You enjoy meeting new people and making new friends',
                'category': 'EI',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You are comfortable speaking in front of large groups',
                'category': 'EI',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You take initiative in social situations',
                'category': 'EI',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You prefer face-to-face communication over written communication',
                'category': 'EI',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            
            # Questions favoring Introversion (8 questions)
            {
                'text': 'You prefer solitary activities or one-on-one interactions',
                'category': 'EI',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You need time alone to recharge after socializing',
                'category': 'EI',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You prefer listening to others rather than speaking',
                'category': 'EI',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You think carefully before speaking in conversations',
                'category': 'EI',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You feel drained after too much social interaction',
                'category': 'EI',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You prefer written communication over face-to-face',
                'category': 'EI',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You prefer deep conversations with few people',
                'category': 'EI',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You observe others before joining group activities',
                'category': 'EI',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
        ]
        
        # =============== SN DIMENSION (Sensing vs Intuition) ===============
        sn_questions = [
            # Questions favoring Sensing (8 questions)
            {
                'text': 'You prefer concrete facts over abstract theories',
                'category': 'SN',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You focus on practical details and real-world applications',
                'category': 'SN',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You trust your direct experiences more than intuition',
                'category': 'SN',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You prefer step-by-step instructions over open-ended tasks',
                'category': 'SN',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You notice small details in your environment',
                'category': 'SN',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You prefer established methods over new approaches',
                'category': 'SN',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You rely on your five senses to understand the world',
                'category': 'SN',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You are realistic and down-to-earth',
                'category': 'SN',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            
            # Questions favoring Intuition (8 questions)
            {
                'text': 'You enjoy thinking about future possibilities and what could be',
                'category': 'SN',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You see patterns and connections that others miss',
                'category': 'SN',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You enjoy brainstorming and generating new ideas',
                'category': 'SN',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You think in metaphors and symbols',
                'category': 'SN',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You focus on the big picture rather than details',
                'category': 'SN',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You enjoy exploring theoretical concepts',
                'category': 'SN',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You imagine how things could be improved',
                'category': 'SN',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You are imaginative and creative',
                'category': 'SN',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
        ]
        
        # =============== TF DIMENSION (Thinking vs Feeling) ===============
        tf_questions = [
            # Questions favoring Thinking (8 questions)
            {
                'text': 'You make decisions based on logic rather than emotions',
                'category': 'TF',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You value truth over tact when giving feedback',
                'category': 'TF',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You analyze problems objectively',
                'category': 'TF',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You believe fairness means applying rules equally to everyone',
                'category': 'TF',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You are direct and straightforward in communication',
                'category': 'TF',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You value competence over compassion in team members',
                'category': 'TF',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You focus on task completion over team feelings',
                'category': 'TF',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You enjoy debating ideas, even if it causes disagreement',
                'category': 'TF',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            
            # Questions favoring Feeling (8 questions)
            {
                'text': 'You consider how decisions will affect people\'s feelings',
                'category': 'TF',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You prioritize harmony and avoiding conflict',
                'category': 'TF',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You are empathetic and understand others\' emotions',
                'category': 'TF',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You believe fairness means considering individual circumstances',
                'category': 'TF',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You are diplomatic and considerate in communication',
                'category': 'TF',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You value kindness over efficiency in team members',
                'category': 'TF',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You focus on team morale and relationships',
                'category': 'TF',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You avoid arguments to maintain positive relationships',
                'category': 'TF',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
        ]
        
        # =============== JP DIMENSION (Judging vs Perceiving) ===============
        jp_questions = [
            # Questions favoring Judging (8 questions)
            {
                'text': 'You prefer structure and organization in your life',
                'category': 'JP',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You make decisions quickly and stick to them',
                'category': 'JP',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You plan your work and work your plan',
                'category': 'JP',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You are punctual and reliable',
                'category': 'JP',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You prefer closure and completion of tasks',
                'category': 'JP',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You make lists and check items off',
                'category': 'JP',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You feel stressed when things are disorganized',
                'category': 'JP',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            {
                'text': 'You set goals and deadlines for yourself',
                'category': 'JP',
                'dimension_a_weight': 1,
                'dimension_b_weight': 0,
                'choices': 'standard'
            },
            
            # Questions favoring Perceiving (8 questions)
            {
                'text': 'You prefer flexibility and spontaneity in your life',
                'category': 'JP',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You keep your options open as long as possible',
                'category': 'JP',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You work best under pressure with approaching deadlines',
                'category': 'JP',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You are adaptable and go with the flow',
                'category': 'JP',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You enjoy starting new projects more than finishing old ones',
                'category': 'JP',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You prefer to improvise rather than follow a schedule',
                'category': 'JP',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You feel restricted by too much planning',
                'category': 'JP',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
            {
                'text': 'You prefer to explore opportunities as they arise',
                'category': 'JP',
                'dimension_a_weight': 0,
                'dimension_b_weight': 1,
                'choices': 'standard'
            },
        ]
        
        # Combine all questions
        all_questions = ei_questions + sn_questions + tf_questions + jp_questions
        
        # Standard choices for 7-point Likert scale
        standard_choices = [
            {'text': 'Strongly Disagree', 'value': -3},
            {'text': 'Disagree', 'value': -2},
            {'text': 'Slightly Disagree', 'value': -1},
            {'text': 'Neutral', 'value': 0},
            {'text': 'Slightly Agree', 'value': 1},
            {'text': 'Agree', 'value': 2},
            {'text': 'Strongly Agree', 'value': 3}
        ]
        
        # Create questions in database
        for i, q_data in enumerate(all_questions, 1):
            choices = standard_choices
            
            question = Question.objects.create(
                text=q_data['text'],
                category=q_data['category'],
                dimension_a_weight=q_data['dimension_a_weight'],
                dimension_b_weight=q_data['dimension_b_weight']
            )
            
            for choice_data in choices:
                AnswerChoice.objects.create(
                    question=question,
                    text=choice_data['text'],
                    value=choice_data['value']
                )
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(all_questions)} balanced MBTI questions"))
        self.stdout.write(f"  - EI Dimension: {len(ei_questions)} questions")
        self.stdout.write(f"  - SN Dimension: {len(sn_questions)} questions")
        self.stdout.write(f"  - TF Dimension: {len(tf_questions)} questions")
        self.stdout.write(f"  - JP Dimension: {len(jp_questions)} questions")

    def create_learning_styles(self):
        """Create 4 learning styles"""
        self.print_step("Creating Learning Styles")
        
        styles = [
            {
                'name': 'visual',
                'description': 'Learn best through seeing: diagrams, charts, videos, and written directions.',
                'detailed_description': 'Prefers visual representations of information, uses colors and spatial arrangements to organize thoughts.',
                'preferred_activities': 'Watching demonstrations, Using flashcards, Drawing diagrams, Creating mind maps',
                'study_techniques': 'Use color coding, Create visual aids, Watch educational videos, Draw concept maps',
                'common_challenges': 'May overlook verbal instructions, Can be distracted by visual clutter',
                'suitable_careers': 'Graphic Design, Architecture, Engineering, Art, Web Design',
                'kenyan_adaptations': 'Use local imagery and diagrams relevant to Kenyan context',
                'local_resources': 'KICD digital content, KNEC past papers with diagrams, Local educational TV programs',
                'study_recommendations': 'Use visual aids for Swahili/English, Create visual timelines for History'
            },
            {
                'name': 'auditory',
                'description': 'Learn best through listening: lectures, discussions, and verbal explanations.',
                'detailed_description': 'Prefers verbal instructions, remembers information by repeating it aloud, enjoys discussions.',
                'preferred_activities': 'Participating in discussions, Listening to lectures, Using mnemonics, Recording notes',
                'study_techniques': 'Record lectures, Use rhythmic patterns, Participate in study groups, Read aloud',
                'common_challenges': 'May struggle with written instructions, Can be distracted by noise',
                'suitable_careers': 'Teaching, Counseling, Law, Sales, Broadcasting',
                'kenyan_adaptations': 'Oral traditions are strong - use storytelling and group discussions',
                'local_resources': 'Radio lessons, Podcasts in Swahili/English, Group study materials',
                'study_recommendations': 'Listen to local radio programs, Participate in debate clubs'
            },
            {
                'name': 'reading',
                'description': 'Learn best through reading and writing: textbooks, notes, and written assignments.',
                'detailed_description': 'Prefers written words, enjoys reading and writing activities, learns by taking detailed notes.',
                'preferred_activities': 'Reading textbooks, Writing essays, Taking notes, Making lists',
                'study_techniques': 'Rewrite notes, Create written summaries, Use bullet points, Write practice essays',
                'common_challenges': 'May overlook visual/auditory information, Can get stuck in details',
                'suitable_careers': 'Research, Law, Writing, Academia, Editing',
                'kenyan_adaptations': 'Emphasize reading local literature and writing in both English and Swahili',
                'local_resources': 'Local textbooks, Kenyan authors\' works, Writing guides for KCSE',
                'study_recommendations': 'Read Kenyan newspapers, Practice essay writing for KCSE'
            },
            {
                'name': 'kinesthetic',
                'description': 'Learn best through doing: hands-on activities, experiments, and physical movement.',
                'detailed_description': 'Prefers physical experience, learns by doing and moving, remembers through muscle memory.',
                'preferred_activities': 'Hands-on experiments, Role-playing, Building models, Physical activities',
                'study_techniques': 'Use physical objects, Take frequent breaks to move, Create physical models, Use gestures',
                'common_challenges': 'May struggle with sedentary learning, Can be impatient with theory',
                'suitable_careers': 'Medicine, Sports, Construction, Manufacturing, Surgery',
                'kenyan_adaptations': 'Incorporate practical skills relevant to local industries',
                'local_resources': 'Vocational training materials, Practical science kits, Agricultural demonstrations',
                'study_recommendations': 'Participate in school clubs, Engage in community projects'
            }
        ]
        
        for style in styles:
            LearningStyle.objects.get_or_create(
                name=style['name'],
                defaults=style
            )
        self.stdout.write(self.style.SUCCESS("✓ Created 4 Learning Styles"))

    def create_kcse_subjects(self):
        """Create comprehensive KCSE subjects"""
        self.print_step("Creating KCSE Subjects")
        
        subjects = [
            # Core Subjects (8)
            ('Mathematics', 'MAT', 'mathematics', 'very_hard',
             'Foundation for logical thinking, problem-solving, and analytical skills essential for STEM careers.',
             1.0, True, 'C-', 'visual', 12),
            
            ('English', 'ENG', 'languages', 'medium',
             'Language of instruction and global communication, essential for all academic and professional pursuits.',
             1.0, True, 'C-', 'reading', 8),
            
            ('Kiswahili', 'SWA', 'languages', 'medium',
             'National language and regional communication, important for cultural understanding and local opportunities.',
             1.0, True, 'C-', 'auditory', 8),
            
            ('Biology', 'BIO', 'sciences', 'hard',
             'Study of living organisms, essential for medical, agricultural, and environmental careers.',
             1.0, True, 'C-', 'visual', 10),
            
            ('Physics', 'PHY', 'sciences', 'very_hard',
             'Study of matter, energy, and their interactions, fundamental for engineering and technology fields.',
             1.0, False, 'C-', 'visual', 12),
            
            ('Chemistry', 'CHE', 'sciences', 'very_hard',
             'Study of substances, their properties and reactions, crucial for medicine, engineering, and research.',
             1.0, False, 'C-', 'visual', 11),
            
            ('History', 'HIS', 'humanities', 'medium',
             'Study of past events and their significance, develops critical thinking and analytical skills.',
             0.9, False, 'D+', 'reading', 7),
            
            ('Geography', 'GEO', 'humanities', 'medium',
             'Study of Earth\'s landscapes, peoples, and environments, important for planning and environmental careers.',
             0.9, False, 'D+', 'visual', 7),
            
            # Sciences (4)
            ('Computer Studies', 'COM', 'computer', 'hard',
             'Information technology and computer systems, essential for digital economy and tech careers.',
             1.0, False, 'C-', 'kinesthetic', 10),
            
            ('Agriculture', 'AGR', 'agriculture', 'medium',
             'Agricultural science and farming practices, crucial for Kenya\'s economy and food security.',
             0.9, False, 'D+', 'kinesthetic', 8),
            
            ('Home Science', 'HSC', 'technical', 'medium',
             'Home management, nutrition, childcare, and family economics, practical life skills.',
             0.8, False, 'D+', 'kinesthetic', 7),
            
            ('Physical Education', 'PED', 'sports', 'easy',
             'Physical fitness, sports skills, and health education, important for wellness and sports careers.',
             0.6, False, 'D', 'kinesthetic', 5),
            
            # Humanities & Languages (8)
            ('CRE (Christian Religious Education)', 'CRE', 'religious', 'medium',
             'Christian Religious Education and moral values, develops ethical reasoning.',
             0.8, False, 'D+', 'reading', 6),
            
            ('IRE (Islamic Religious Education)', 'IRE', 'religious', 'medium',
             'Islamic Religious Education and moral values, develops ethical reasoning.',
             0.8, False, 'D+', 'reading', 6),
            
            ('Business Studies', 'BUS', 'business', 'medium',
             'Principles of business, entrepreneurship, and commerce, essential for business careers.',
             0.9, False, 'C-', 'reading', 8),
            
            ('Music', 'MUS', 'arts', 'medium',
             'Musical theory, performance, and appreciation, develops creativity and cultural understanding.',
             0.7, False, 'D+', 'auditory', 6),
            
            ('Art and Design', 'ART', 'arts', 'medium',
             'Visual arts, design principles, and creativity, important for creative industries.',
             0.7, False, 'D+', 'visual', 7),
            
            ('German', 'GER', 'languages', 'hard',
             'German language and culture, useful for international relations and business.',
             0.8, False, 'D+', 'auditory', 9),
            
            ('French', 'FRE', 'languages', 'hard',
             'French language and culture, important for international diplomacy and African relations.',
             0.8, False, 'D+', 'auditory', 9),
            
            ('Arabic', 'ARA', 'languages', 'hard',
             'Arabic language and Islamic culture, useful for religious studies and Middle East relations.',
             0.8, False, 'D+', 'reading', 9),
            
            # Technical Subjects (8)
            ('Technical Drawing', 'TDR', 'technical', 'hard',
             'Engineering and architectural drawing, essential for engineering and construction careers.',
             0.9, False, 'C-', 'visual', 10),
            
            ('Building Construction', 'BDC', 'technical', 'hard',
             'Construction techniques and materials, important for building industry careers.',
             0.9, False, 'C-', 'kinesthetic', 10),
            
            ('Power Mechanics', 'PWM', 'technical', 'hard',
             'Automotive and mechanical systems, crucial for automotive industry and engineering.',
             0.9, False, 'C-', 'kinesthetic', 10),
            
            ('Electricity', 'ELC', 'technical', 'hard',
             'Electrical systems and electronics, fundamental for electrical engineering and technicians.',
             0.9, False, 'C-', 'visual', 10),
            
            ('Woodwork', 'WOD', 'technical', 'medium',
             'Woodworking skills and furniture making, important for carpentry and construction.',
             0.8, False, 'D+', 'kinesthetic', 8),
            
            ('Metalwork', 'MET', 'technical', 'medium',
             'Metal fabrication and welding, crucial for manufacturing and construction industries.',
             0.8, False, 'D+', 'kinesthetic', 8),
            
            ('Clothing and Textiles', 'CLT', 'technical', 'medium',
             'Fashion design and textile production, important for fashion industry.',
             0.7, False, 'D+', 'kinesthetic', 7),
            
            ('Aviation Technology', 'AVT', 'technical', 'very_hard',
             'Aircraft systems and aviation principles, specialized for aviation careers.',
             1.0, False, 'C', 'visual', 12),
            
            # Additional Subjects (4)
            ('Environmental Science', 'ENV', 'sciences', 'medium',
             'Environmental studies and conservation, crucial for environmental management careers.',
             0.8, False, 'D+', 'visual', 7),
            
            ('Economics', 'ECO', 'business', 'hard',
             'Economic principles and analysis, important for finance and policy careers.',
             0.9, False, 'C-', 'reading', 9),
            
            ('Literature in English', 'LIT', 'languages', 'hard',
             'English literature and literary analysis, develops critical thinking and communication.',
             0.9, False, 'C-', 'reading', 9),
            
            ('Sign Language', 'SGL', 'languages', 'medium',
             'Kenyan Sign Language, important for special needs education and inclusion.',
             0.7, False, 'D+', 'kinesthetic', 7)
        ]
        
        for name, code, category, difficulty, description, weight, compulsory, min_grade, learning_style, hours in subjects:
            Subject.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': category,
                    'difficulty_level': difficulty,
                    'description': description,
                    'kcse_weight': weight,
                    'is_compulsory': compulsory,
                    'minimum_grade': min_grade,
                    'recommended_learning_style': learning_style,
                    'study_hours_recommended': hours,
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(subjects)} KCSE Subjects"))

    def create_kenyan_careers(self):
        """Create comprehensive Kenyan career database"""
        self.print_step("Creating Kenyan Careers")
        
        careers_data = [
            # Technology & IT (12 careers)
            {
                'name': 'Software Developer',
                'description': 'Design, develop, and maintain software applications and systems using programming languages.',
                'category': 'technology',
                'subcategory': 'software_development',
                'average_salary': 180000,
                'entry_level_salary': 80000,
                'mid_level_salary': 250000,
                'senior_level_salary': 500000,
                'kenyan_market_demand': 'very_high',
                'market_demand_trend': 'growing',
                'growth_projection': '40% growth in next 5 years due to digital transformation',
                'education_requirements': 'Bachelor\'s degree in Computer Science, Software Engineering, or related field',
                'minimum_education': 'bachelors',
                'skills_required': 'Programming (Python, JavaScript, Java), Problem-solving, Teamwork, Agile methodologies, Database management',
                'certifications': 'AWS Certified Developer, Microsoft Certified: Azure Developer Associate, Oracle Certified Professional',
                'work_environment': 'Office-based, remote work possible, collaborative teams, project-based work',
                'typical_work_hours': '40-50 hours per week, sometimes urgent deadlines',
                'career_path': 'Junior Developer → Senior Developer → Tech Lead → Engineering Manager → CTO',
                'kenyan_market_analysis': 'High demand in Nairobi\'s Silicon Savannah with over 200 tech startups. Major companies include Safaricom, Andela, Africa\'s Talking.',
                'top_employers': 'Safaricom, Andela, Africa\'s Talking, Twiga Foods, Copia, IBM Africa, Microsoft Africa',
                'kenyan_universities': 'University of Nairobi, Strathmore University, JKUAT, Moi University, Kenyatta University',
                'scholarships_available': 'KCB Foundation Tech Scholarship, Mastercard Foundation Scholars Program, Google Africa Developer Scholarship',
                'complexity_level': 'high',
                'learning_duration': '4 years (Bachelor\'s) + continuous learning',
                'is_kenyan_focused': True
            },
            {
                'name': 'Data Scientist',
                'description': 'Analyze and interpret complex data to help organizations make data-driven decisions using statistical methods and machine learning.',
                'category': 'technology',
                'subcategory': 'data_science',
                'average_salary': 220000,
                'entry_level_salary': 100000,
                'mid_level_salary': 300000,
                'senior_level_salary': 550000,
                'kenyan_market_demand': 'high',
                'market_demand_trend': 'rapid_increase',
                'growth_projection': '50% growth expected in banking and telecom sectors',
                'education_requirements': 'Bachelor\'s/Master\'s in Statistics, Computer Science, Mathematics, or Data Science',
                'minimum_education': 'bachelors',
                'skills_required': 'Python/R programming, Statistics, Machine Learning, Data Visualization, SQL',
                'certifications': 'AWS Certified Data Analytics, Google Data Analytics Professional Certificate',
                'work_environment': 'Office-based, research-oriented, data-driven decision making',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Data Analyst → Data Scientist → Senior Data Scientist → Data Science Manager → Chief Data Officer',
                'kenyan_market_analysis': 'Growing demand in financial services, telecommunications, and e-commerce. Kenyan banks investing heavily in data analytics.',
                'top_employers': 'Safaricom, Equity Bank, KCB, Jumo, Branch International, Zumi, M-KOPA',
                'kenyan_universities': 'University of Nairobi, Strathmore University, African Nazarene University, JKUAT',
                'scholarships_available': 'Data Science Africa Scholarships, IBM SkillsBuild, Microsoft AI for Africa',
                'complexity_level': 'very_high',
                'learning_duration': '4-6 years (including Master\'s)',
                'is_kenyan_focused': True
            },
            {
                'name': 'Cybersecurity Analyst',
                'description': 'Protect computer systems and networks from cyber attacks and security breaches.',
                'category': 'technology',
                'subcategory': 'cybersecurity',
                'average_salary': 200000,
                'entry_level_salary': 90000,
                'mid_level_salary': 280000,
                'senior_level_salary': 500000,
                'kenyan_market_demand': 'very_high',
                'market_demand_trend': 'growing',
                'growth_projection': '35% growth due to increasing cyber threats',
                'education_requirements': 'Bachelor\'s in Computer Science, Cybersecurity, or Information Technology',
                'minimum_education': 'bachelors',
                'skills_required': 'Network security, Ethical hacking, Risk assessment, Security protocols, Incident response',
                'certifications': 'CEH (Certified Ethical Hacker), CISSP, CompTIA Security+',
                'work_environment': 'Security operations centers, corporate IT departments, consulting firms',
                'typical_work_hours': '40-50 hours per week, sometimes on-call for emergencies',
                'career_path': 'Security Analyst → Senior Security Analyst → Security Manager → CISO (Chief Information Security Officer)',
                'kenyan_market_analysis': 'Critical need in banking, government, and telecommunications sectors. Kenya facing increasing cyber threats.',
                'top_employers': 'Safaricom, Banks (Equity, KCB, Co-op), Government agencies, Cybersecurity firms',
                'kenyan_universities': 'Dedan Kimathi University, KCA University, Mount Kenya University',
                'scholarships_available': 'Cybersecurity scholarships from Communications Authority of Kenya',
                'complexity_level': 'high',
                'learning_duration': '4 years + certifications',
                'is_kenyan_focused': True
            },
            {
                'name': 'AI/Machine Learning Engineer',
                'description': 'Design and implement artificial intelligence systems and machine learning models.',
                'category': 'technology',
                'subcategory': 'ai_ml',
                'average_salary': 250000,
                'entry_level_salary': 120000,
                'mid_level_salary': 350000,
                'senior_level_salary': 600000,
                'kenyan_market_demand': 'high',
                'market_demand_trend': 'rapid_increase',
                'growth_projection': '45% growth as AI adoption increases',
                'education_requirements': 'Bachelor\'s/Master\'s in Computer Science, Mathematics, or Statistics with AI/ML focus',
                'minimum_education': 'bachelors',
                'skills_required': 'Python, TensorFlow, PyTorch, Deep Learning, Natural Language Processing',
                'certifications': 'Google TensorFlow Developer Certificate, AWS Machine Learning Specialty',
                'work_environment': 'Research labs, tech companies, innovation hubs',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'ML Engineer → Senior ML Engineer → AI Research Scientist → AI Product Manager',
                'kenyan_market_analysis': 'Growing AI ecosystem in Kenya with several startups focusing on African solutions.',
                'top_employers': 'IBM Research Africa, Microsoft Africa, local AI startups, Safaricom',
                'kenyan_universities': 'University of Nairobi, Strathmore University, JKUAT',
                'scholarships_available': 'Google AI Residency, IBM PhD Fellowship',
                'complexity_level': 'very_high',
                'learning_duration': '4-6 years',
                'is_kenyan_focused': True
            },
            {
                'name': 'Cloud Solutions Architect',
                'description': 'Design and implement cloud computing solutions for organizations.',
                'category': 'technology',
                'subcategory': 'cloud_computing',
                'average_salary': 230000,
                'entry_level_salary': 110000,
                'mid_level_salary': 320000,
                'senior_level_salary': 550000,
                'kenyan_market_demand': 'high',
                'market_demand_trend': 'growing',
                'growth_projection': '40% growth as cloud adoption increases',
                'education_requirements': 'Bachelor\'s in Computer Science or related field',
                'minimum_education': 'bachelors',
                'skills_required': 'AWS/Azure/GCP, Cloud security, Infrastructure as Code, Containerization',
                'certifications': 'AWS Solutions Architect, Microsoft Azure Solutions Architect, Google Cloud Architect',
                'work_environment': 'Consulting firms, cloud service providers, large enterprises',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Cloud Engineer → Cloud Architect → Senior Cloud Architect → Cloud Practice Lead',
                'kenyan_market_analysis': 'Increasing migration to cloud services by Kenyan businesses and government.',
                'top_employers': 'Amazon Web Services, Microsoft Azure, Google Cloud, local cloud consultancies',
                'kenyan_universities': 'University of Nairobi, Strathmore University, KCA University',
                'scholarships_available': 'AWS Educate, Google Cloud training scholarships',
                'complexity_level': 'high',
                'learning_duration': '4 years + cloud certifications',
                'is_kenyan_focused': True
            },
            {
                'name': 'DevOps Engineer',
                'description': 'Bridge development and operations to improve software delivery and infrastructure management.',
                'category': 'technology',
                'subcategory': 'devops',
                'average_salary': 190000,
                'entry_level_salary': 90000,
                'mid_level_salary': 270000,
                'senior_level_salary': 480000,
                'kenyan_market_demand': 'high',
                'market_demand_trend': 'growing',
                'growth_projection': '35% growth as DevOps practices become standard',
                'education_requirements': 'Bachelor\'s in Computer Science or related field',
                'minimum_education': 'bachelors',
                'skills_required': 'CI/CD, Docker, Kubernetes, Infrastructure as Code, Monitoring tools',
                'certifications': 'Docker Certified Associate, Kubernetes Administrator, AWS DevOps Engineer',
                'work_environment': 'Tech companies, financial institutions, e-commerce platforms',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'DevOps Engineer → Senior DevOps Engineer → DevOps Manager → Head of Platform Engineering',
                'kenyan_market_analysis': 'High demand in tech companies and financial institutions adopting modern software practices.',
                'top_employers': 'Andela, Safaricom, banks, e-commerce companies',
                'kenyan_universities': 'University of Nairobi, Strathmore University, JKUAT',
                'scholarships_available': 'Various tech bootcamps and certification programs',
                'complexity_level': 'high',
                'learning_duration': '4 years + DevOps certifications',
                'is_kenyan_focused': True
            },
            
            # Healthcare (10 careers)
            {
                'name': 'Medical Doctor',
                'description': 'Diagnose and treat illnesses, injuries, and other health conditions.',
                'category': 'healthcare',
                'subcategory': 'medicine',
                'average_salary': 300000,
                'entry_level_salary': 120000,
                'mid_level_salary': 500000,
                'senior_level_salary': 1000000,
                'kenyan_market_demand': 'very_high',
                'market_demand_trend': 'stable',
                'growth_projection': '25% growth needed to meet healthcare demands',
                'education_requirements': 'Bachelor of Medicine and Bachelor of Surgery (MBChB) - 6 years',
                'minimum_education': 'masters',
                'skills_required': 'Medical knowledge, Diagnosis, Patient care, Communication, Empathy',
                'certifications': 'Registration with Kenya Medical Practitioners and Dentists Board',
                'work_environment': 'Hospitals, clinics, private practice, research institutions',
                'typical_work_hours': '50-80 hours per week (including shifts)',
                'career_path': 'Intern → Medical Officer → Registrar → Consultant → Senior Consultant',
                'kenyan_market_analysis': 'Critical shortage of doctors, especially in rural areas. Doctor-patient ratio below WHO recommendations.',
                'top_employers': 'Kenyatta National Hospital, Moi Teaching Hospital, Ministry of Health, Private hospitals',
                'kenyan_universities': 'University of Nairobi, Moi University, Kenyatta University, Egerton University',
                'scholarships_available': 'Ministry of Health Scholarships, County Government Scholarships',
                'complexity_level': 'very_high',
                'learning_duration': '6-7 years (medical school) + 1 year internship + 3-5 years specialization',
                'is_kenyan_focused': True
            },
            {
                'name': 'Registered Nurse',
                'description': 'Provide and coordinate patient care, educate patients about health conditions.',
                'category': 'healthcare',
                'subcategory': 'nursing',
                'average_salary': 120000,
                'entry_level_salary': 60000,
                'mid_level_salary': 180000,
                'senior_level_salary': 300000,
                'kenyan_market_demand': 'very_high',
                'market_demand_trend': 'growing',
                'growth_projection': '30% growth due to healthcare expansion',
                'education_requirements': 'Diploma or Bachelor\'s in Nursing',
                'minimum_education': 'diploma',
                'skills_required': 'Patient care, Medication administration, Emergency response, Communication',
                'certifications': 'Registration with Nursing Council of Kenya',
                'work_environment': 'Hospitals, clinics, community health centers, schools',
                'typical_work_hours': '40-60 hours per week (shift work)',
                'career_path': 'Staff Nurse → Senior Nurse → Nursing Officer → Nursing Manager → Director of Nursing',
                'kenyan_market_analysis': 'High demand in both public and private healthcare sectors. Nursing shortage in rural areas.',
                'top_employers': 'Public hospitals, Private hospitals, NGOs, Ministry of Health',
                'kenyan_universities': 'University of Nairobi, Kenyatta University, Moi University, various nursing colleges',
                'scholarships_available': 'Nursing Council scholarships, County bursaries',
                'complexity_level': 'high',
                'learning_duration': '3-4 years (diploma/degree)',
                'is_kenyan_focused': True
            },
            {
                'name': 'Clinical Officer',
                'description': 'Provide medical care under supervision of doctors, especially in rural areas.',
                'category': 'healthcare',
                'subcategory': 'clinical_medicine',
                'average_salary': 100000,
                'entry_level_salary': 50000,
                'mid_level_salary': 150000,
                'senior_level_salary': 250000,
                'kenyan_market_demand': 'very_high',
                'market_demand_trend': 'stable',
                'growth_projection': '20% growth in rural healthcare',
                'education_requirements': 'Diploma in Clinical Medicine and Surgery',
                'minimum_education': 'diploma',
                'skills_required': 'Clinical skills, Patient care, Basic diagnostics, Primary healthcare',
                'certifications': 'Registration with Clinical Officers Council',
                'work_environment': 'Health centers, dispensaries, rural hospitals, private clinics',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Clinical Officer → Senior Clinical Officer → Clinical Officer in Charge → County Health Manager',
                'kenyan_market_analysis': 'Crucial for primary healthcare in rural areas. Often the first point of contact for patients.',
                'top_employers': 'County governments, Private clinics, NGOs, Mission hospitals',
                'kenyan_universities': 'Various medical training colleges nationwide',
                'scholarships_available': 'County government scholarships',
                'complexity_level': 'medium',
                'learning_duration': '3 years (diploma)',
                'is_kenyan_focused': True
            },
            {
                'name': 'Pharmacist',
                'description': 'Dispense prescription medications and provide drug information to patients.',
                'category': 'healthcare',
                'subcategory': 'pharmacy',
                'average_salary': 150000,
                'entry_level_salary': 80000,
                'mid_level_salary': 220000,
                'senior_level_salary': 400000,
                'kenyan_market_demand': 'high',
                'market_demand_trend': 'growing',
                'growth_projection': '25% growth with pharmaceutical industry expansion',
                'education_requirements': 'Bachelor of Pharmacy (B.Pharm)',
                'minimum_education': 'bachelors',
                'skills_required': 'Pharmaceutical knowledge, Attention to detail, Customer service, Inventory management',
                'certifications': 'Registration with Pharmacy and Poisons Board',
                'work_environment': 'Hospitals, retail pharmacies, pharmaceutical companies, regulatory bodies',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Pharmacist → Senior Pharmacist → Pharmacy Manager → Chief Pharmacist',
                'kenyan_market_analysis': 'Growing pharmaceutical sector with increasing access to medications.',
                'top_employers': 'Hospital pharmacies, Retail chains (Goodlife, HealthPlus), Pharmaceutical manufacturers',
                'kenyan_universities': 'University of Nairobi, Kenyatta University, Mount Kenya University',
                'scholarships_available': 'Pharmaceutical industry scholarships',
                'complexity_level': 'high',
                'learning_duration': '4 years (Bachelor\'s) + 1 year internship',
                'is_kenyan_focused': True
            },
            {
                'name': 'Dentist',
                'description': 'Diagnose and treat problems with patients\' teeth, gums, and related parts of the mouth.',
                'category': 'healthcare',
                'subcategory': 'dentistry',
                'average_salary': 200000,
                'entry_level_salary': 100000,
                'mid_level_salary': 300000,
                'senior_level_salary': 600000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'growing',
                'growth_projection': '20% growth with increasing dental awareness',
                'education_requirements': 'Bachelor of Dental Surgery (BDS)',
                'minimum_education': 'bachelors',
                'skills_required': 'Manual dexterity, Attention to detail, Patient care, Communication',
                'certifications': 'Registration with Kenya Medical Practitioners and Dentists Board',
                'work_environment': 'Dental clinics, hospitals, private practice',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Dental Officer → Senior Dental Officer → Consultant Dentist → Dental Specialist',
                'kenyan_market_analysis': 'Growing demand for dental services in urban areas. Limited access in rural regions.',
                'top_employers': 'Private dental clinics, Public hospitals, Dental schools',
                'kenyan_universities': 'University of Nairobi, Moi University',
                'scholarships_available': 'Limited scholarships available',
                'complexity_level': 'high',
                'learning_duration': '5 years (Bachelor\'s) + 1 year internship',
                'is_kenyan_focused': True
            },
            
            # Engineering (10 careers)
            {
                'name': 'Civil Engineer',
                'description': 'Design, construct, and maintain infrastructure projects like roads, bridges, and buildings.',
                'category': 'engineering',
                'subcategory': 'civil_engineering',
                'average_salary': 180000,
                'entry_level_salary': 90000,
                'mid_level_salary': 250000,
                'senior_level_salary': 500000,
                'kenyan_market_demand': 'high',
                'market_demand_trend': 'growing',
                'growth_projection': '30% growth due to infrastructure projects',
                'education_requirements': 'Bachelor\'s degree in Civil Engineering',
                'minimum_education': 'bachelors',
                'skills_required': 'Structural design, Project management, AutoCAD, Site supervision, Mathematics',
                'certifications': 'Registered with Engineers Board of Kenya (EBK)',
                'work_environment': 'Construction sites, engineering firms, government agencies',
                'typical_work_hours': '45-55 hours per week',
                'career_path': 'Graduate Engineer → Project Engineer → Senior Engineer → Project Manager → Director',
                'kenyan_market_analysis': 'High demand due to government infrastructure projects (roads, railways, housing).',
                'top_employers': 'Ministry of Transport, Chinese contractors, Local construction firms, Consulting engineers',
                'kenyan_universities': 'University of Nairobi, JKUAT, Moi University, Technical University of Mombasa',
                'scholarships_available': 'Engineers Board of Kenya Scholarships, Corporate sponsorships',
                'complexity_level': 'high',
                'learning_duration': '5 years (university) + 2 years internship',
                'is_kenyan_focused': True
            },
            {
                'name': 'Electrical Engineer',
                'description': 'Design and develop electrical systems and equipment.',
                'category': 'engineering',
                'subcategory': 'electrical_engineering',
                'average_salary': 170000,
                'entry_level_salary': 85000,
                'mid_level_salary': 240000,
                'senior_level_salary': 450000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'stable',
                'growth_projection': '20% growth with energy sector expansion',
                'education_requirements': 'Bachelor\'s in Electrical Engineering',
                'minimum_education': 'bachelors',
                'skills_required': 'Circuit design, Power systems, Electronics, Automation, MATLAB',
                'certifications': 'Registered with Engineers Board of Kenya',
                'work_environment': 'Power companies, manufacturing plants, consulting firms',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Electrical Engineer → Senior Electrical Engineer → Project Manager → Chief Engineer',
                'kenyan_market_analysis': 'Demand in energy sector, manufacturing, and telecommunications.',
                'top_employers': 'Kenya Power, Safaricom, Manufacturing companies, Consulting firms',
                'kenyan_universities': 'University of Nairobi, JKUAT, Moi University, Dedan Kimathi University',
                'scholarships_available': 'Energy sector scholarships',
                'complexity_level': 'high',
                'learning_duration': '5 years + 2 years internship',
                'is_kenyan_focused': True
            },
            {
                'name': 'Mechanical Engineer',
                'description': 'Design, analyze, and manufacture mechanical systems.',
                'category': 'engineering',
                'subcategory': 'mechanical_engineering',
                'average_salary': 160000,
                'entry_level_salary': 80000,
                'mid_level_salary': 230000,
                'senior_level_salary': 420000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'stable',
                'growth_projection': '15% growth in manufacturing sector',
                'education_requirements': 'Bachelor\'s in Mechanical Engineering',
                'minimum_education': 'bachelors',
                'skills_required': 'Machine design, Thermodynamics, CAD software, Manufacturing processes',
                'certifications': 'Registered with Engineers Board of Kenya',
                'work_environment': 'Manufacturing plants, automotive companies, engineering firms',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Mechanical Engineer → Senior Mechanical Engineer → Engineering Manager → Director',
                'kenyan_market_analysis': 'Steady demand in manufacturing, automotive, and energy sectors.',
                'top_employers': 'Manufacturing companies, Automotive industry, Energy companies',
                'kenyan_universities': 'University of Nairobi, JKUAT, Moi University, Technical University of Kenya',
                'scholarships_available': 'Manufacturing industry scholarships',
                'complexity_level': 'high',
                'learning_duration': '5 years + 2 years internship',
                'is_kenyan_focused': True
            },
            
            # Business & Finance (10 careers)
            {
                'name': 'Chartered Accountant',
                'description': 'Prepare and examine financial records, ensure accuracy, and assess financial operations.',
                'category': 'business',
                'subcategory': 'accounting',
                'average_salary': 200000,
                'entry_level_salary': 80000,
                'mid_level_salary': 300000,
                'senior_level_salary': 700000,
                'kenyan_market_demand': 'high',
                'market_demand_trend': 'stable',
                'growth_projection': '20% steady growth',
                'education_requirements': 'Bachelor\'s in Accounting/Finance + CPA(K)',
                'minimum_education': 'bachelors',
                'skills_required': 'Accounting principles, Financial analysis, Tax laws, Auditing, Excel',
                'certifications': 'CPA(K), ACCA, CFA',
                'work_environment': 'Accounting firms, corporate offices, government agencies',
                'typical_work_hours': '45-60 hours per week (especially during audit season)',
                'career_path': 'Audit Assistant → Senior Auditor → Manager → Partner/Director',
                'kenyan_market_analysis': 'Essential for all businesses. High demand in Nairobi financial sector.',
                'top_employers': 'KPMG, PwC, Deloitte, EY, banks, large corporations',
                'kenyan_universities': 'University of Nairobi, Strathmore University, Kenyatta University',
                'scholarships_available': 'KASNEB scholarships, Corporate accounting scholarships',
                'complexity_level': 'high',
                'learning_duration': '4 years (degree) + 3 years (CPA)',
                'is_kenyan_focused': True
            },
            {
                'name': 'Financial Analyst',
                'description': 'Guide businesses and individuals in investment decisions.',
                'category': 'business',
                'subcategory': 'finance',
                'average_salary': 150000,
                'entry_level_salary': 70000,
                'mid_level_salary': 220000,
                'senior_level_salary': 450000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'growing',
                'growth_projection': '25% growth in financial services',
                'education_requirements': 'Bachelor\'s in Finance, Economics, or Business',
                'minimum_education': 'bachelors',
                'skills_required': 'Financial modeling, Market analysis, Excel skills, Investment strategies',
                'certifications': 'CFA, FRM, CPA',
                'work_environment': 'Banks, investment firms, insurance companies, corporate finance departments',
                'typical_work_hours': '45-55 hours per week',
                'career_path': 'Financial Analyst → Senior Financial Analyst → Finance Manager → CFO',
                'kenyan_market_analysis': 'Growing financial sector in Kenya with increasing investment opportunities.',
                'top_employers': 'Banks (Equity, KCB, Co-op), Investment firms, Insurance companies',
                'kenyan_universities': 'University of Nairobi, Strathmore University, USIU Africa',
                'scholarships_available': 'Financial sector scholarships',
                'complexity_level': 'high',
                'learning_duration': '4 years + professional certifications',
                'is_kenyan_focused': True
            },
            {
                'name': 'Marketing Manager',
                'description': 'Plan and execute marketing strategies to promote products or services.',
                'category': 'business',
                'subcategory': 'marketing',
                'average_salary': 140000,
                'entry_level_salary': 60000,
                'mid_level_salary': 200000,
                'senior_level_salary': 400000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'growing',
                'growth_projection': '20% growth in digital marketing',
                'education_requirements': 'Bachelor\'s in Marketing or Business',
                'minimum_education': 'bachelors',
                'skills_required': 'Market research, Digital marketing, Brand management, Communication, Creativity',
                'certifications': 'Digital Marketing certifications, Google Ads, Facebook Blueprint',
                'work_environment': 'Corporations, advertising agencies, marketing departments',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Marketing Assistant → Marketing Executive → Marketing Manager → Marketing Director → CMO',
                'kenyan_market_analysis': 'Growing digital marketing sector. Companies investing more in online presence.',
                'top_employers': 'Consumer goods companies (Unilever, Coca-Cola), Advertising agencies, Tech companies',
                'kenyan_universities': 'University of Nairobi, Strathmore University, Kenyatta University',
                'scholarships_available': 'Marketing industry scholarships',
                'complexity_level': 'medium',
                'learning_duration': '4 years + experience',
                'is_kenyan_focused': True
            },
            {
                'name': 'Human Resources Manager',
                'description': 'Oversee recruitment, employee relations, and organizational development.',
                'category': 'business',
                'subcategory': 'human_resources',
                'average_salary': 130000,
                'entry_level_salary': 60000,
                'mid_level_salary': 190000,
                'senior_level_salary': 350000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'stable',
                'growth_projection': '15% growth with business expansion',
                'education_requirements': 'Bachelor\'s in Human Resources or Business',
                'minimum_education': 'bachelors',
                'skills_required': 'Recruitment, Employee relations, Labor laws, Organizational development, Communication',
                'certifications': 'CHRP (Certified Human Resources Professional), SHRM',
                'work_environment': 'Corporate offices, consulting firms, government agencies',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'HR Assistant → HR Officer → HR Manager → HR Director → CHRO',
                'kenyan_market_analysis': 'Essential for all organizations. Growing focus on talent management.',
                'top_employers': 'Large corporations, Consulting firms, NGOs, Government',
                'kenyan_universities': 'University of Nairobi, Kenyatta University, Strathmore University',
                'scholarships_available': 'HR professional association scholarships',
                'complexity_level': 'medium',
                'learning_duration': '4 years + HR certifications',
                'is_kenyan_focused': True
            },
            
            # Education (8 careers)
            {
                'name': 'Secondary School Teacher',
                'description': 'Educate students in specific subjects at secondary school level.',
                'category': 'education',
                'subcategory': 'teaching',
                'average_salary': 80000,
                'entry_level_salary': 40000,
                'mid_level_salary': 120000,
                'senior_level_salary': 200000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'stable',
                'growth_projection': '10% steady growth with population increase',
                'education_requirements': 'Bachelor of Education (B.Ed) in two teaching subjects',
                'minimum_education': 'bachelors',
                'skills_required': 'Teaching methodology, Classroom management, Subject expertise, Communication',
                'certifications': 'Registered with Teachers Service Commission (TSC)',
                'work_environment': 'Schools, classrooms, educational institutions',
                'typical_work_hours': '40-50 hours per week (including preparation and marking)',
                'career_path': 'Teacher → Senior Teacher → Head of Department → Deputy Principal → Principal',
                'kenyan_market_analysis': 'Government employs most teachers through TSC. Opportunities in private schools.',
                'top_employers': 'TSC, Private schools, International schools',
                'kenyan_universities': 'Kenyatta University, University of Nairobi, Moi University, Maseno University',
                'scholarships_available': 'TSC scholarships, County bursaries',
                'complexity_level': 'medium',
                'learning_duration': '4 years (B.Ed)',
                'is_kenyan_focused': True
            },
            {
                'name': 'University Lecturer',
                'description': 'Teach at university level and conduct research.',
                'category': 'education',
                'subcategory': 'higher_education',
                'average_salary': 150000,
                'entry_level_salary': 80000,
                'mid_level_salary': 220000,
                'senior_level_salary': 400000,
                'kenyan_market_demand': 'low',
                'market_demand_trend': 'stable',
                'growth_projection': '10% growth in higher education',
                'education_requirements': 'Master\'s or PhD in specialized field',
                'minimum_education': 'masters',
                'skills_required': 'Research, Public speaking, Curriculum development, Academic writing',
                'certifications': 'PhD preferred for permanent positions',
                'work_environment': 'Universities, research institutions, colleges',
                'typical_work_hours': '40-60 hours per week (teaching, research, administration)',
                'career_path': 'Tutorial Fellow → Lecturer → Senior Lecturer → Associate Professor → Professor',
                'kenyan_market_analysis': 'Competitive field with limited positions. Research funding increasing.',
                'top_employers': 'Public universities, Private universities, Research institutions',
                'kenyan_universities': 'All public and private universities',
                'scholarships_available': 'PhD scholarships, Research grants',
                'complexity_level': 'high',
                'learning_duration': '6-8 years (Bachelor\'s + Master\'s + PhD)',
                'is_kenyan_focused': True
            },
            
            # Agriculture (8 careers)
            {
                'name': 'Agricultural Engineer',
                'description': 'Apply engineering principles to agricultural production and processing.',
                'category': 'agriculture',
                'subcategory': 'agricultural_engineering',
                'average_salary': 120000,
                'entry_level_salary': 60000,
                'mid_level_salary': 180000,
                'senior_level_salary': 300000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'growing',
                'growth_projection': '25% growth with agricultural modernization',
                'education_requirements': 'Bachelor\'s in Agricultural Engineering',
                'minimum_education': 'bachelors',
                'skills_required': 'Farm machinery design, Irrigation systems, Soil conservation, Agricultural processing',
                'certifications': 'Registered with Engineers Board of Kenya',
                'work_environment': 'Farms, agricultural companies, government agencies, research institutions',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Agricultural Engineer → Senior Agricultural Engineer → Project Manager → Director',
                'kenyan_market_analysis': 'Important for agricultural transformation in Kenya. Focus on food security.',
                'top_employers': 'Ministry of Agriculture, Agribusiness companies, NGOs, Research institutions',
                'kenyan_universities': 'JKUAT, University of Nairobi, Egerton University',
                'scholarships_available': 'Agricultural sector scholarships',
                'complexity_level': 'medium',
                'learning_duration': '5 years + internship',
                'is_kenyan_focused': True
            },
            {
                'name': 'Agronomist',
                'description': 'Study soil management and crop production.',
                'category': 'agriculture',
                'subcategory': 'agronomy',
                'average_salary': 100000,
                'entry_level_salary': 50000,
                'mid_level_salary': 150000,
                'senior_level_salary': 250000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'stable',
                'growth_projection': '20% growth in commercial agriculture',
                'education_requirements': 'Bachelor\'s in Agriculture or Agronomy',
                'minimum_education': 'bachelors',
                'skills_required': 'Crop science, Soil analysis, Pest management, Agricultural research',
                'certifications': 'Professional agronomist certification',
                'work_environment': 'Farms, research stations, agricultural companies, government agencies',
                'typical_work_hours': '40-50 hours per week',
                'career_path': 'Agronomist → Senior Agronomist → Research Manager → Agricultural Consultant',
                'kenyan_market_analysis': 'Essential for improving agricultural productivity in Kenya.',
                'top_employers': 'Research institutions, Seed companies, Fertilizer companies, NGOs',
                'kenyan_universities': 'University of Nairobi, Egerton University, Moi University',
                'scholarships_available': 'Agricultural research scholarships',
                'complexity_level': 'medium',
                'learning_duration': '4 years + experience',
                'is_kenyan_focused': True
            },
            
            # Legal (4 careers)
            {
                'name': 'Advocate',
                'description': 'Represent clients in legal matters and provide legal advice.',
                'category': 'law',
                'subcategory': 'legal_practice',
                'average_salary': 150000,
                'entry_level_salary': 60000,
                'mid_level_salary': 250000,
                'senior_level_salary': 600000,
                'kenyan_market_demand': 'medium',
                'market_demand_trend': 'stable',
                'growth_projection': '15% growth in commercial law',
                'education_requirements': 'Bachelor of Laws (LL.B) + Kenya School of Law',
                'minimum_education': 'bachelors',
                'skills_required': 'Legal research, Argumentation, Writing, Client management, Ethics',
                'certifications': 'Admission to the Bar, Practicing certificate',
                'work_environment': 'Law firms, courts, corporate offices, government agencies',
                'typical_work_hours': '50-70 hours per week',
                'career_path': 'Pupil → Associate → Senior Associate → Partner → Senior Partner',
                'kenyan_market_analysis': 'Competitive field. High earning potential for successful lawyers.',
                'top_employers': 'Law firms, Judiciary, Government, Corporations',
                'kenyan_universities': 'University of Nairobi, Moi University, Mount Kenya University',
                'scholarships_available': 'Law society scholarships',
                'complexity_level': 'high',
                'learning_duration': '4 years (LL.B) + 1 year (Kenya School of Law) + pupillage',
                'is_kenyan_focused': True
            },
        ]
        
        # Create careers
        careers_created = 0
        for career_data in careers_data:
            career, created = Career.objects.get_or_create(
                name=career_data['name'],
                defaults=career_data
            )
            if created:
                careers_created += 1
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {careers_created} Kenyan Careers"))
        
        # Now create career-subject relationships
        self.stdout.write("\nCreating Career-Subject Relationships...")
        
        # Get key subjects
        subjects_dict = {}
        for subject in Subject.objects.all():
            subjects_dict[subject.name.lower()] = subject
        
        # Define career-subject mappings
        career_subject_mappings = {
            # Technology careers
            'Software Developer': {
                'required': ['Mathematics', 'Physics', 'Computer Studies'],
                'recommended': ['English', 'Business Studies', 'Chemistry']
            },
            'Data Scientist': {
                'required': ['Mathematics', 'Computer Studies', 'Physics'],
                'recommended': ['Business Studies', 'English', 'Chemistry']
            },
            'Cybersecurity Analyst': {
                'required': ['Computer Studies', 'Mathematics'],
                'recommended': ['Physics', 'Business Studies', 'English']
            },
            'AI/Machine Learning Engineer': {
                'required': ['Mathematics', 'Computer Studies', 'Physics'],
                'recommended': ['Chemistry', 'Business Studies']
            },
            'Cloud Solutions Architect': {
                'required': ['Computer Studies', 'Mathematics'],
                'recommended': ['Physics', 'Business Studies', 'English']
            },
            'DevOps Engineer': {
                'required': ['Computer Studies', 'Mathematics'],
                'recommended': ['Physics', 'Business Studies']
            },
            
            # Healthcare careers
            'Medical Doctor': {
                'required': ['Biology', 'Chemistry', 'Physics', 'Mathematics'],
                'recommended': ['English', 'Kiswahili']
            },
            'Registered Nurse': {
                'required': ['Biology', 'Chemistry', 'English'],
                'recommended': ['Mathematics', 'Kiswahili']
            },
            'Clinical Officer': {
                'required': ['Biology', 'Chemistry', 'English'],
                'recommended': ['Mathematics', 'Kiswahili']
            },
            'Pharmacist': {
                'required': ['Biology', 'Chemistry', 'Mathematics'],
                'recommended': ['Physics', 'English']
            },
            'Dentist': {
                'required': ['Biology', 'Chemistry', 'Physics', 'Mathematics'],
                'recommended': ['English', 'Kiswahili']
            },
            
            # Engineering careers
            'Civil Engineer': {
                'required': ['Mathematics', 'Physics', 'Chemistry'],
                'recommended': ['Technical Drawing', 'Geography', 'Computer Studies']
            },
            'Electrical Engineer': {
                'required': ['Mathematics', 'Physics', 'Chemistry'],
                'recommended': ['Technical Drawing', 'Computer Studies']
            },
            'Mechanical Engineer': {
                'required': ['Mathematics', 'Physics', 'Chemistry'],
                'recommended': ['Technical Drawing', 'Computer Studies']
            },
            'Agricultural Engineer': {
                'required': ['Mathematics', 'Physics', 'Agriculture'],
                'recommended': ['Chemistry', 'Biology']
            },
            
            # Business careers
            'Chartered Accountant': {
                'required': ['Mathematics', 'Business Studies'],
                'recommended': ['English', 'Computer Studies']
            },
            'Financial Analyst': {
                'required': ['Mathematics', 'Business Studies'],
                'recommended': ['Economics', 'Computer Studies', 'English']
            },
            'Marketing Manager': {
                'required': ['Business Studies', 'English'],
                'recommended': ['Mathematics', 'Computer Studies']
            },
            'Human Resources Manager': {
                'required': ['Business Studies', 'English'],
                'recommended': ['History', 'Kiswahili']
            },
            
            # Education careers
            'Secondary School Teacher': {
                'required': ['English', 'Mathematics'],
                'recommended': ['Subject of specialization']
            },
            'University Lecturer': {
                'required': ['English', 'Mathematics'],
                'recommended': ['Subject of specialization']
            },
            
            # Agriculture careers
            'Agricultural Engineer': {
                'required': ['Mathematics', 'Physics', 'Agriculture'],
                'recommended': ['Chemistry', 'Biology']
            },
            'Agronomist': {
                'required': ['Biology', 'Chemistry', 'Agriculture'],
                'recommended': ['Mathematics', 'Geography']
            },
            
            # Legal careers
            'Advocate': {
                'required': ['English', 'History'],
                'recommended': ['Business Studies', 'Kiswahili']
            },
        }
        
        # Apply subject mappings
        for career_name, mapping in career_subject_mappings.items():
            try:
                career = Career.objects.get(name=career_name)
                
                # Clear existing subjects
                career.required_subjects.clear()
                career.recommended_subjects.clear()
                
                # Add required subjects
                for subject_name in mapping.get('required', []):
                    subject_key = subject_name.lower()
                    if subject_key in subjects_dict:
                        career.required_subjects.add(subjects_dict[subject_key])
                    else:
                        # Try alternative names
                        for subj in Subject.objects.filter(name__icontains=subject_name):
                            career.required_subjects.add(subj)
                
                # Add recommended subjects
                for subject_name in mapping.get('recommended', []):
                    subject_key = subject_name.lower()
                    if subject_key in subjects_dict:
                        career.recommended_subjects.add(subjects_dict[subject_key])
                    else:
                        # Try alternative names
                        for subj in Subject.objects.filter(name__icontains=subject_name):
                            career.recommended_subjects.add(subj)
                            
            except Career.DoesNotExist:
                continue
        
        self.stdout.write(self.style.SUCCESS("✓ Created Career-Subject Relationships"))

    def create_career_personality_matches(self):
        """Create accurate personality-career compatibility scores"""
        self.print_step("Creating Career-Personality Matches")
        
        # Clear existing matches
        CareerPersonalityMatch.objects.all().delete()
        
        # Get all careers and personality types
        careers = Career.objects.all()
        personality_types = PersonalityType.objects.all()
        
        # Research-based compatibility matrix
        compatibility_matrix = {
            # INTJ - Architects
            'INTJ': {
                'technology': 0.9, 'engineering': 0.85, 'research': 0.9, 'law': 0.8,
                'business': 0.75, 'health': 0.6, 'education': 0.65, 'agriculture': 0.5,
                'arts': 0.4, 'media': 0.45
            },
            # INTP - Logicians
            'INTP': {
                'technology': 0.95, 'engineering': 0.85, 'research': 0.95, 'science': 0.9,
                'education': 0.7, 'business': 0.6, 'health': 0.55, 'arts': 0.5
            },
            # ENTJ - Commanders
            'ENTJ': {
                'business': 0.95, 'law': 0.9, 'engineering': 0.85, 'public_service': 0.9,
                'technology': 0.8, 'education': 0.7, 'health': 0.65, 'agriculture': 0.6
            },
            # ENTP - Debaters
            'ENTP': {
                'business': 0.9, 'media': 0.85, 'technology': 0.8, 'law': 0.85,
                'education': 0.75, 'engineering': 0.7, 'health': 0.6, 'agriculture': 0.55
            },
            # INFJ - Advocates
            'INFJ': {
                'health': 0.9, 'education': 0.95, 'counseling': 0.95, 'arts': 0.8,
                'business': 0.65, 'technology': 0.6, 'engineering': 0.55, 'agriculture': 0.6
            },
            # INFP - Mediators
            'INFP': {
                'arts': 0.95, 'education': 0.85, 'counseling': 0.9, 'health': 0.8,
                'media': 0.75, 'business': 0.55, 'technology': 0.5, 'engineering': 0.45
            },
            # ENFJ - Protagonists
            'ENFJ': {
                'education': 0.95, 'health': 0.9, 'business': 0.85, 'public_service': 0.9,
                'media': 0.8, 'technology': 0.65, 'engineering': 0.6, 'agriculture': 0.7
            },
            # ENFP - Campaigners
            'ENFP': {
                'media': 0.95, 'education': 0.9, 'business': 0.85, 'arts': 0.9,
                'health': 0.8, 'technology': 0.7, 'engineering': 0.6, 'agriculture': 0.65
            },
            # ISTJ - Logisticians
            'ISTJ': {
                'business': 0.9, 'engineering': 0.85, 'law': 0.85, 'public_service': 0.9,
                'health': 0.8, 'education': 0.75, 'technology': 0.7, 'agriculture': 0.7
            },
            # ISFJ - Defenders
            'ISFJ': {
                'health': 0.95, 'education': 0.9, 'public_service': 0.85, 'business': 0.75,
                'agriculture': 0.7, 'arts': 0.65, 'technology': 0.55, 'engineering': 0.5
            },
            # ESTJ - Executives
            'ESTJ': {
                'business': 0.95, 'law': 0.9, 'public_service': 0.95, 'engineering': 0.85,
                'education': 0.8, 'health': 0.75, 'technology': 0.7, 'agriculture': 0.7
            },
            # ESFJ - Consuls
            'ESFJ': {
                'health': 0.95, 'education': 0.9, 'business': 0.85, 'public_service': 0.9,
                'media': 0.8, 'agriculture': 0.75, 'technology': 0.6, 'engineering': 0.55
            },
            # ISTP - Virtuosos
            'ISTP': {
                'engineering': 0.95, 'technology': 0.85, 'agriculture': 0.8, 'health': 0.75,
                'business': 0.65, 'education': 0.6, 'law': 0.55, 'arts': 0.5
            },
            # ISFP - Adventurers
            'ISFP': {
                'arts': 0.95, 'health': 0.85, 'education': 0.8, 'agriculture': 0.75,
                'media': 0.7, 'business': 0.6, 'technology': 0.5, 'engineering': 0.45
            },
            # ESTP - Entrepreneurs
            'ESTP': {
                'business': 0.95, 'media': 0.85, 'public_service': 0.8, 'engineering': 0.75,
                'technology': 0.7, 'agriculture': 0.65, 'education': 0.6, 'health': 0.55
            },
            # ESFP - Entertainers
            'ESFP': {
                'media': 0.95, 'business': 0.85, 'health': 0.8, 'education': 0.75,
                'arts': 0.9, 'agriculture': 0.7, 'technology': 0.6, 'engineering': 0.55
            }
        }
        
        matches_created = 0
        for career in careers:
            for personality in personality_types:
                # Get base compatibility score based on career category
                base_score = 0.5  # Default neutral score
                
                # Map career category to compatibility matrix categories
                career_category = career.category.lower()
                
                # Find matching category in matrix
                if personality.mbti_type in compatibility_matrix:
                    personality_matrix = compatibility_matrix[personality.mbti_type]
                    
                    # Check for direct category match
                    if career_category in personality_matrix:
                        base_score = personality_matrix[career_category]
                    else:
                        # Try to find partial match
                        for matrix_category, score in personality_matrix.items():
                            if matrix_category in career_category or career_category in matrix_category:
                                base_score = score
                                break
                
                # Add some variation (+/- 0.1) to avoid identical scores
                variation = random.uniform(-0.05, 0.05)
                final_score = max(0.1, min(1.0, base_score + variation))
                
                # Create the match
                CareerPersonalityMatch.objects.create(
                    career=career,
                    personality_type=personality,
                    match_score=round(final_score, 2),
                    reasoning=f"Your {personality.mbti_type} personality shows {int(final_score*100)}% compatibility with {career.name} based on career requirements and personality traits.",
                    strengths_match=f"As a {personality.mbti_type}, your strengths align well with the demands of {career.name}.",
                    challenges="Consider developing complementary skills for optimal performance.",
                    is_top_match=final_score >= 0.8
                )
                matches_created += 1
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {matches_created} Career-Personality Matches"))

    def create_career_learning_style_matches(self):
        """Create learning style-career compatibility scores"""
        self.print_step("Creating Career-Learning Style Matches")
        
        # Clear existing matches
        CareerLearningStyle.objects.all().delete()
        
        careers = Career.objects.all()
        learning_styles = LearningStyle.objects.all()
        
        matches_created = 0
        for career in careers:
            for learning_style in learning_styles:
                # Base compatibility based on career category and learning style
                base_score = 0.5
                
                if learning_style.name == 'visual':
                    # Visual learners do well in design, engineering, technology
                    if any(word in career.category.lower() for word in ['technology', 'engineering', 'design', 'architecture', 'arts']):
                        base_score = 0.85
                    elif any(word in career.category.lower() for word in ['science', 'business', 'education']):
                        base_score = 0.7
                    else:
                        base_score = 0.6
                
                elif learning_style.name == 'auditory':
                    # Auditory learners do well in teaching, law, public speaking
                    if any(word in career.category.lower() for word in ['education', 'law', 'media', 'business', 'health']):
                        base_score = 0.85
                    elif any(word in career.category.lower() for word in ['public_service', 'agriculture']):
                        base_score = 0.7
                    else:
                        base_score = 0.55
                
                elif learning_style.name == 'reading':
                    # Reading/writing learners do well in research, law, academia
                    if any(word in career.category.lower() for word in ['research', 'law', 'education', 'business', 'science']):
                        base_score = 0.85
                    elif any(word in career.category.lower() for word in ['public_service', 'health', 'media']):
                        base_score = 0.7
                    else:
                        base_score = 0.6
                
                else:  # kinesthetic
                    # Kinesthetic learners do well in hands-on fields
                    if any(word in career.category.lower() for word in ['engineering', 'health', 'agriculture', 'technical', 'arts']):
                        base_score = 0.85
                    elif any(word in career.category.lower() for word in ['technology', 'science']):
                        base_score = 0.7
                    else:
                        base_score = 0.6
                
                # Add some variation
                variation = random.uniform(-0.05, 0.05)
                final_score = max(0.1, min(1.0, base_score + variation))
                
                # Create the match
                CareerLearningStyle.objects.create(
                    career=career,
                    learning_style=learning_style,
                    match_score=round(final_score, 2),
                    reasoning=f"As a {learning_style.name} learner, you would approach {career.name} with your preferred learning methods.",
                    learning_requirements=f"{career.name} requires learning through {learning_style.name} methods.",
                    adaptation_tips="Adapt your natural learning style to the requirements of this career."
                )
                matches_created += 1
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {matches_created} Career-Learning Style Matches"))

    def create_kenyan_schools(self):
        """Create sample Kenyan schools"""
        self.print_step("Creating Kenyan Schools")
        
        schools = [
            ('Alliance High School', '001', 'Kiambu', 'national'),
            ('Maseno School', '002', 'Kisumu', 'national'),
            ('Starehe Boys Centre', '003', 'Nairobi', 'national'),
            ('Mangu High School', '004', 'Kiambu', 'national'),
            ('Nairobi School', '005', 'Nairobi', 'national'),
            ('Lenana School', '006', 'Nairobi', 'national'),
            ('Precious Blood Riruta', '007', 'Nairobi', 'national'),
            ('Maryhill Girls High School', '008', 'Thika', 'national'),
            ('Butere Girls High School', '009', 'Kakamega', 'national'),
            ('Moi Girls High School - Eldoret', '010', 'Uasin Gishu', 'national'),
            ('Kagumo High School', '011', 'Nyeri', 'national'),
            ('Maranda High School', '012', 'Siaya', 'national'),
            ('Kenya High School', '013', 'Nairobi', 'national'),
            ('Loreto High School - Limuru', '014', 'Kiambu', 'national'),
            ('Moi Forces Academy - Nairobi', '015', 'Nairobi', 'private'),
            ('Aga Khan High School', '016', 'Mombasa', 'private'),
            ('Braeburn School', '017', 'Nairobi', 'private'),
            ('Hillcrest International Schools', '018', 'Nairobi', 'private'),
            ('St. Austins Academy', '019', 'Nairobi', 'private'),
            ('Rusinga School', '020', 'Nairobi', 'private'),
            ('State House Girls High School', '021', 'Nairobi', 'national'),
            ('Nakuru Boys High School', '022', 'Nakuru', 'national'),
            ('Kapsabet Boys High School', '023', 'Nandi', 'national'),
            ('Asumbi Girls High School', '024', 'Homa Bay', 'national'),
            ('Kisii High School', '025', 'Kisii', 'national'),
            ('Kakamega High School', '026', 'Kakamega', 'national'),
            ('Maseno High School', '027', 'Kisumu', 'national'),
            ('Meru School', '028', 'Meru', 'national'),
            ('Friends School Kamusinga', '029', 'Bungoma', 'national'),
            ('Moi High School - Kabarak', '030', 'Nakuru', 'national'),
        ]
        
        schools_created = 0
        for name, code, county, school_type in schools:
            school, created = School.objects.get_or_create(
                name=name,
                defaults={
                    'code': code,
                    'county': county,
                    'type': school_type
                }
            )
            if created:
                schools_created += 1
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {schools_created} Kenyan Schools"))

    def create_admin_user(self):
        """Create admin user"""
        self.print_step("Creating Admin User")
        
        User = get_user_model()
        
        # Create superuser
        try:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@careercompass.co.ke',
                password='admin',
                first_name='System',
                last_name='Administrator',
                user_type='admin'
            )
            self.stdout.write(self.style.SUCCESS("✓ Created admin user: admin/admin"))
        except:
            self.stdout.write(self.style.WARNING("⚠ Admin user already exists"))

    def create_demo_student(self):
        """Create demo student for testing"""
        self.print_step("Creating Demo Student")
        
        User = get_user_model()
        
        # Check if demo student exists
        if not User.objects.filter(username='demo_student').exists():
            # Create user
            user = User.objects.create_user(
                username='demo_student',
                email='demo@careercompass.co.ke',
                password='Demo@1234',
                first_name='Demo',
                last_name='Student',
                user_type='student'
            )
            
            # Get a school (create one if none exists)
            school, created = School.objects.get_or_create(
                name='Demo High School',
                defaults={
                    'code': '999',
                    'county': 'Nairobi',
                    'type': 'private'
                }
            )
            
            # Create student profile with only existing fields
            student_profile = StudentProfile.objects.create(
                user=user,
                school=school,
                grade_level='form4',
                career_aspirations='I want to work in technology and help solve problems in Kenya.'
            )
            
            # Add some subjects (optional)
            subjects = Subject.objects.filter(name__in=['Mathematics', 'Physics', 'Computer Studies', 'English', 'Business Studies'])
            student_profile.subjects.set(subjects)
            
            self.stdout.write(self.style.SUCCESS("✓ Created demo student: demo_student / Demo@1234"))
            self.stdout.write(self.style.SUCCESS(f"   School: {school.name}"))
            self.stdout.write(self.style.SUCCESS(f"   Subjects: {subjects.count()} subjects added"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Demo student already exists"))