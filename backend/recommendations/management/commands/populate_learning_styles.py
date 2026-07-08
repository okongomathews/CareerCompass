from django.core.management.base import BaseCommand
from recommendations.models import LearningStyle

class Command(BaseCommand):
    help = 'Populate learning styles data'
    
    def handle(self, *args, **options):
        learning_styles = [
            {
                'name': 'visual',
                'description': 'Learn through seeing and visual aids',
                'study_recommendations': 'Use diagrams, mind maps, color coding, and visual presentations'
            },
            {
                'name': 'auditory', 
                'description': 'Learn through listening and verbal instruction',
                'study_recommendations': 'Record lectures, participate in discussions, use verbal repetition'
            },
            {
                'name': 'reading',
                'description': 'Learn through reading and writing',
                'study_recommendations': 'Take detailed notes, read textbooks, write summaries'
            },
            {
                'name': 'kinesthetic',
                'description': 'Learn through hands-on experience and movement',
                'study_recommendations': 'Use hands-on activities, take breaks to move, create physical models'
            },
        ]
        
        for style_data in learning_styles:
            LearningStyle.objects.get_or_create(
                name=style_data['name'],
                defaults=style_data
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created learning styles')
        )