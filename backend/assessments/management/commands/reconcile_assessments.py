"""
Reconcile completed AssessmentSessions that have no AssessmentResult.

ROOT CAUSE (now fixed):
    Running `python manage.py load_mbti_data` previously called
    PersonalityType.objects.all().delete() which cascaded via the FK and
    silently deleted every AssessmentResult in the database.

    This command detects those orphaned sessions and re-runs MBTICalculator
    to recreate the missing results, then regenerates career recommendations.

Usage:
    python manage.py reconcile_assessments          # dry-run — shows what would change
    python manage.py reconcile_assessments --fix    # recreate missing results
"""
import logging
from django.core.management.base import BaseCommand
from assessments.models import AssessmentSession, AssessmentResult

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recreate missing AssessmentResult records for completed sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            default=False,
            help='Actually recreate missing AssessmentResult records (default: dry-run)',
        )

    def handle(self, *args, **options):
        fix = options['fix']

        orphaned = (
            AssessmentSession.objects
            .filter(is_completed=True)
            .exclude(student__assessmentresult__isnull=False)
            .select_related('student__user')
            .order_by('completed_at')
        )

        if not orphaned.exists():
            self.stdout.write(self.style.SUCCESS(
                'No orphaned sessions found — all completed sessions have an AssessmentResult.'
            ))
            return

        self.stdout.write(self.style.WARNING(
            f'\nFound {orphaned.count()} completed session(s) with no AssessmentResult:'
        ))
        for session in orphaned:
            answered = session.responses.count()
            self.stdout.write(
                f'  Session #{session.id} | Student: {session.student.user.username} '
                f'| Answers: {answered} | Completed: {session.completed_at}'
            )

        if not fix:
            self.stdout.write(
                '\nDry-run only. Add --fix to recreate the missing results.\n'
                'Note: this was caused by load_mbti_data deleting PersonalityType\n'
                'records, which cascaded to AssessmentResult. Now fixed in the\n'
                'new version of load_mbti_data (safe mode by default).'
            )
            return

        from assessments.services import MBTICalculator

        fixed = 0
        errors = 0
        for session in orphaned:
            username = session.student.user.username
            try:
                calc   = MBTICalculator(session)
                result = calc.generate_result()
                self.stdout.write(self.style.SUCCESS(
                    f'  Recreated result for {username}: '
                    f'{result.personality_type.mbti_type} '
                    f'(confidence: {result.get_confidence_percent()}%)'
                ))
                fixed += 1

                # Also regenerate career recommendations
                try:
                    from recommendations.services import RecommendationEngine
                    from recommendations.models import StudentRecommendation
                    from django.db import transaction

                    engine = RecommendationEngine(session.student)
                    recs   = engine.generate_career_recommendations(top_n=15)
                    with transaction.atomic():
                        StudentRecommendation.objects.filter(student=session.student).delete()
                        for r in recs:
                            StudentRecommendation.objects.create(
                                student=session.student,
                                career=r['career'],
                                overall_score=r['overall_score'],
                                personality_match_score=r['personality_match_score'],
                                academic_match_score=r['academic_match_score'],
                                market_demand_score=r['market_demand_score'],
                                learning_style_score=r['learning_style_score'],
                                grade_boost=r['grade_boost'],
                                reasoning=r['reasoning'],
                            )
                    self.stdout.write(
                        f'    -> {len(recs)} career recommendations regenerated for {username}'
                    )
                except Exception as rec_err:
                    self.stdout.write(self.style.WARNING(
                        f'    -> Could not regenerate recommendations for {username}: {rec_err}'
                    ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  FAILED for {username}: {e}'
                ))
                errors += 1

        self.stdout.write(
            f'\nDone. Recreated: {fixed}  |  Errors: {errors}\n'
            f'Students can now see results at /assessments/results/\n'
            f'and recommendations at /recommendations/'
        )
