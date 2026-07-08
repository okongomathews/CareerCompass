# recommendations/management/commands/train_ml_models.py
"""
Management command to train ML models
"""
from django.core.management.base import BaseCommand
from recommendations.ml_models import CareerSuccessPredictor, MarketTrendAnalyzer
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Train machine learning models for CareerCompass Kenya'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            default='all',
            help='Model to train: success, trends, or all'
        )
    
    def handle(self, *args, **options):
        model_type = options['model']
        
        self.stdout.write(self.style.SUCCESS('Starting ML model training...'))
        
        # Create models directory if it doesn't exist
        models_dir = os.path.join(settings.BASE_DIR, 'models')
        os.makedirs(models_dir, exist_ok=True)
        
        if model_type in ['success', 'all']:
            self.stdout.write('Training Career Success Predictor...')
            predictor = CareerSuccessPredictor()
            success = predictor.train()
            if success:
                self.stdout.write(self.style.SUCCESS('✓ Career Success Predictor trained successfully'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Insufficient data for Career Success Predictor'))
        
        if model_type in ['trends', 'all']:
            self.stdout.write('Analyzing Market Trends...')
            analyzer = MarketTrendAnalyzer()
            trends = analyzer.analyze_career_trends()
            
            # Save trends to file
            trends_file = os.path.join(models_dir, 'market_trends.json')
            import json
            with open(trends_file, 'w') as f:
                json.dump(trends, f, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Market trends analyzed and saved to {trends_file}'))
            
            # Print top trends
            self.stdout.write('\nTop Growing Categories:')
            for category, data in sorted(trends.items(), key=lambda x: x[1].get('growth_rate', 0), reverse=True)[:5]:
                self.stdout.write(f'  {category}: {data.get("growth_rate", 0):.1f}% growth')
        
        self.stdout.write(self.style.SUCCESS('\nML model training completed!'))