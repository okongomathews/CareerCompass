from django.core.management.base import BaseCommand
from ai_coach.models import ResourceRecommendation
from users.models import StudentProfile

class Command(BaseCommand):
    help = 'Populate learning resources'

    def handle(self, *args, **options):
        resources = [
            {'title': 'KCSE Revision Guide: Mathematics', 'description': 'Comprehensive revision notes and past papers for KCSE Mathematics.', 'resource_type': 'book', 'relevance_score': 0.9, 'is_kenyan_specific': True},
            {'title': 'Introduction to Programming (Python) for Kenyan Students', 'description': 'Free online course tailored for beginners with local examples.', 'resource_type': 'course', 'relevance_score': 0.95, 'is_kenyan_specific': True, 'url': 'https://www.youtube.com/playlist?list=PL6gx4Cwl9DGAKIXv8Yr6nhGJ9Vlcjyymq'},
            {'title': 'Top 10 Careers in Kenya 2024', 'description': 'Article about fastest-growing careers and required subjects.', 'resource_type': 'article', 'relevance_score': 0.85, 'is_kenyan_specific': True, 'url': '#'},
            {'title': 'How to Choose Your University Course via KUCCPS', 'description': 'Video tutorial explaining the placement process.', 'resource_type': 'video', 'relevance_score': 0.9, 'is_kenyan_specific': True},
            {'title': 'Coursera: Career Success Specialization', 'description': 'Build soft skills for any career.', 'resource_type': 'course', 'relevance_score': 0.7, 'url': 'https://www.coursera.org/specializations/career-success'},
        ]
        # Create a dummy coaching plan to attach resources (or modify model to allow global resources)
        # For simplicity, we attach to a placeholder student profile (first active student)
        student = StudentProfile.objects.first()
        if student:
            coaching_plan, _ = ai_coach.models.CoachingPlan.objects.get_or_create(student=student)
            for res in resources:
                ResourceRecommendation.objects.get_or_create(
                    coaching_plan=coaching_plan,
                    title=res['title'],
                    defaults={
                        'description': res['description'],
                        'resource_type': res['resource_type'],
                        'relevance_score': res['relevance_score'],
                        'is_kenyan_specific': res.get('is_kenyan_specific', False),
                        'url': res.get('url', '')
                    }
                )
        self.stdout.write(self.style.SUCCESS('Resources populated successfully'))