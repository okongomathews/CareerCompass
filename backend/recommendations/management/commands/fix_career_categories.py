"""
Fix Career category casing inconsistency.

The populate_careers command historically saved Title-Case category values
(e.g. 'Technology', 'Healthcare') while Career.CATEGORY_CHOICES uses lowercase
keys (e.g. 'technology', 'health').  This caused the analytics bar chart to
show duplicate bars (e.g. both 'Technology' and 'technology').

Run once after upgrade:
    python manage.py fix_career_categories
"""
from django.core.management.base import BaseCommand
from recommendations.models import Career


# Maps every known freetext / Title-Case value → canonical lowercase key
_NORMALISE = {
    # Direct title-case → lowercase key
    'Technology':     'technology',
    'Healthcare':     'health',
    'Health':         'health',
    'Business':       'business',
    'Finance':        'business',
    'Engineering':    'engineering',
    'Agriculture':    'agriculture',
    'Education':      'education',
    'Media':          'media',
    'Law':            'law',
    'Tourism':        'tourism',
    'Hospitality':    'tourism',
    'Construction':   'construction',
    'Environment':    'environment',
    'Science':        'stem',
    'Mathematics':    'stem',
    'STEM':           'stem',
    'NGO':            'public_service',
    'Security':       'technical',
    'Transport':      'technical',
    'Social Sciences':'education',
    'Creative Arts':  'arts',
    'Sports':         'arts',
    # Already-correct lowercase keys (no-op, but listed for completeness)
    'technology': 'technology', 'health': 'health', 'business': 'business',
    'engineering': 'engineering', 'agriculture': 'agriculture',
    'education': 'education', 'media': 'media', 'law': 'law',
    'tourism': 'tourism', 'construction': 'construction',
    'environment': 'environment', 'stem': 'stem',
    'public_service': 'public_service', 'technical': 'technical',
    'arts': 'arts', 'research': 'research',
}


class Command(BaseCommand):
    help = 'Normalise Career.category values to lowercase canonical keys'

    def handle(self, *args, **options):
        total_fixed = 0
        for raw, canonical in _NORMALISE.items():
            if raw == canonical:
                continue  # already correct
            updated = Career.objects.filter(category=raw).update(category=canonical)
            if updated:
                self.stdout.write(
                    self.style.WARNING(f"  '{raw}' → '{canonical}': {updated} career(s) updated")
                )
                total_fixed += updated

        if total_fixed:
            self.stdout.write(self.style.SUCCESS(
                f'\nDone. {total_fixed} career(s) had their category normalised.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                'All career categories are already correctly normalised — nothing to do.'
            ))
