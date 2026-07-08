"""
Fix duplicate questions and missing answer choices.

Run: python manage.py fix_assessment_questions
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from assessments.models import Question, AnswerChoice

# The standard 7‑point Likert choices
STANDARD_CHOICES = [
    {"text": "Strongly Agree",    "value": 3},
    {"text": "Agree",             "value": 2},
    {"text": "Slightly Agree",    "value": 1},
    {"text": "Neutral",           "value": 0},
    {"text": "Slightly Disagree", "value": -1},
    {"text": "Disagree",          "value": -2},
    {"text": "Strongly Disagree", "value": -3},
]

class Command(BaseCommand):
    help = "Remove duplicate questions, recreate missing answer choices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without applying changes",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete responses that reference stale answer choices (use with caution)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write("🔍 Analysing question duplicates...")
        duplicates = self.find_duplicates()
        if duplicates:
            self.stdout.write(self.style.WARNING(f"Found {len(duplicates)} duplicate groups"))
            for text, qs in duplicates.items():
                self.stdout.write(f"  '{text}' appears {len(qs)} times (ids: {[q.id for q in qs]})")
        else:
            self.stdout.write(self.style.SUCCESS("No duplicate questions found."))

        if dry_run:
            self.stdout.write("\n⚠️  DRY RUN – no changes applied.")
            return

        with transaction.atomic():
            # 1. Deduplicate questions
            deleted = 0
            kept = []
            for text, q_list in duplicates.items():
                # Sort by number of answer choices (most complete first)
                q_list.sort(key=lambda q: q.choices.count(), reverse=True)
                keeper = q_list[0]
                kept.append(keeper)
                for stale in q_list[1:]:
                    self.stdout.write(f"  Deleting duplicate question id={stale.id} ('{text}')")
                    # Re‑point any QuestionResponse that may point to the stale question
                    # (very rare, but safe)
                    stale.responses.update(question=keeper)
                    stale.delete()
                    deleted += 1
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} duplicate questions."))

            # 2. Ensure each question has exactly the 7 answer choices
            all_questions = Question.objects.all().prefetch_related("choices")
            fixed_count = 0
            for q in all_questions:
                existing_choices = list(q.choices.all())
                if len(existing_choices) != 7:
                    self.stdout.write(f"  Repairing question id={q.id} '{q.text[:60]}' – has {len(existing_choices)} choices")
                    # If force is given, delete all existing choices (and any responses that point to them)
                    if force:
                        # Responses that used stale choices become invalid – we need to delete those responses
                        # or re‑point to new choices? Since we are recreating identical text, better to delete responses.
                        from assessments.models import QuestionResponse
                        deleted_responses, _ = QuestionResponse.objects.filter(question=q).delete()
                        if deleted_responses:
                            self.stdout.write(self.style.WARNING(f"    Deleted {deleted_responses} stale responses for question {q.id}"))
                    # Wipe old choices
                    q.choices.all().delete()
                    # Create new choices
                    for choice_data in STANDARD_CHOICES:
                        # Flip value sign if the question is a B‑pole question (dimension_b_weight=1)
                        # The original loader flips values for B‑pole, but we want to store raw values
                        # as per `dimension_a_weight`/`dimension_b_weight` – scoring flips later.
                        # However, for consistency, we store the exact value from the list.
                        # Use the pole from the weights later during scoring, so do NOT flip here.
                        value = choice_data["value"]
                        AnswerChoice.objects.create(
                            question=q,
                            text=choice_data["text"],
                            value=value,
                        )
                    fixed_count += 1
            self.stdout.write(self.style.SUCCESS(f"Fixed {fixed_count} questions with missing/incomplete choices."))

            # 3. (Optional) Remove questions beyond the intended 92
            #    This is less invasive – only do if you know the exact set.
            intended_texts = self.get_intended_question_texts()
            if intended_texts:
                extra = Question.objects.exclude(text__in=intended_texts)
                extra_count = extra.count()
                if extra_count:
                    self.stdout.write(self.style.WARNING(f"Found {extra_count} questions not in the intended list."))
                    if force:
                        extra.delete()
                        self.stdout.write(self.style.SUCCESS(f"Deleted {extra_count} extra questions."))
                    else:
                        self.stdout.write("  Use --force to delete them.")

        self.stdout.write(self.style.SUCCESS("\n✅ Fix completed."))
        self.stdout.write(f"Total questions now: {Question.objects.count()}")
        self.stdout.write(f"Total answer choices: {AnswerChoice.objects.count()}")

    def find_duplicates(self):
        """Return dict {question_text: [list of Question objects with same text]}"""
        from collections import defaultdict
        dup_map = defaultdict(list)
        for q in Question.objects.all():
            dup_map[q.text].append(q)
        return {text: qs for text, qs in dup_map.items() if len(qs) > 1}

    def get_intended_question_texts(self):
        """Return the set of question texts that should exist (from load_mbti_data)."""
        # If you want to enforce exactly the 92 questions, copy the texts from your loader.
        # For now, return None to skip this step.
        return None