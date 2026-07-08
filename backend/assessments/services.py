from django.db import transaction
from .models import AssessmentSession, AssessmentResult, PersonalityType


class MBTICalculator:
    """
    Computes MBTI dimension scores from assessment responses.

    Question encoding:
      dimension_a_weight = 1  → A-pole question  (answer value already oriented to A-pole)
      dimension_b_weight = 1  → B-pole question  (answer value already flipped to B-pole)

    Raw score per dimension = sum of (answer.value) across all questions in that category.
    Positive raw score → A-pole (E/S/T/J)
    Negative raw score → B-pole (I/N/F/P)

    Normalisation: scale to [-100, +100] relative to the theoretical maximum.
    """

    def __init__(self, assessment_session):
        self.session = assessment_session

    def calculate_scores(self):
        """Return dict of dimension → normalised score in [-100, 100].

        Scoring methodology (bias-corrected):
          Each question is keyed to a pole (A or B) by its position in the list.
          Odd group-index (0,2,4…) = A-pole; even group-index (1,3,5…) = B-pole.
          A-pole answers contribute positive raw score; B-pole answers are negated.

          Normalisation uses SEPARATE max-possible values for A and B counts so
          that an unequal number of A vs B questions never structurally advantages
          one pole over the other.  The final score sits in [-100, +100]:
            +100 = every A-pole answer was 'strongly agree' (+3) and every B-pole
                   answer was 'strongly disagree' (–3) → maximum A-pole preference.
            –100 = opposite → maximum B-pole preference.
            0    = perfectly balanced.
        """
        raw_a = {'EI': 0, 'SN': 0, 'TF': 0, 'JP': 0}
        raw_b = {'EI': 0, 'SN': 0, 'TF': 0, 'JP': 0}
        cnt_a = {'EI': 0, 'SN': 0, 'TF': 0, 'JP': 0}
        cnt_b = {'EI': 0, 'SN': 0, 'TF': 0, 'JP': 0}
        # Track group-index per category to determine pole
        grp_idx = {'EI': 0, 'SN': 0, 'TF': 0, 'JP': 0}

        responses = self.session.responses.select_related(
            'question', 'answer').all()

        for resp in responses:
            cat   = resp.question.category
            g_idx = grp_idx[cat]
            val   = resp.answer.value   # already signed: +3…+1 or -1…-3

            if g_idx % 2 == 0:          # A-pole question
                raw_a[cat] += val
                cnt_a[cat] += 1
            else:                        # B-pole question (value is pre-negated)
                raw_b[cat] += val
                cnt_b[cat] += 1
            grp_idx[cat] += 1

        # Normalise A and B contributions independently, then combine
        scores = {}
        for cat in raw_a:
            max_a = cnt_a[cat] * 3 if cnt_a[cat] else 1
            max_b = cnt_b[cat] * 3 if cnt_b[cat] else 1
            a_norm = (raw_a[cat] / max_a) * 100   # [-100, +100] → positive = E/S/T/J
            b_norm = (raw_b[cat] / max_b) * 100   # [-100, +100] → negative = I/N/F/P
            scores[cat] = round((a_norm + b_norm) / 2, 2)

        return scores

    def determine_personality_type(self, scores):
        """Convert dimension scores to 4-letter MBTI code."""
        code = ""
        code += 'E' if scores['EI'] >= 0 else 'I'
        code += 'S' if scores['SN'] >= 0 else 'N'
        code += 'T' if scores['TF'] >= 0 else 'F'
        code += 'J' if scores['JP'] >= 0 else 'P'
        return code

    def calculate_confidence(self, scores):
        """
        Confidence = average |score|/100 across all 4 dimensions.
        0.0 = completely undecided on every dimension.
        1.0 = maximum decisiveness on every dimension.
        """
        decisiveness = [abs(v) / 100.0 for v in scores.values()]
        return round(sum(decisiveness) / len(decisiveness), 2)

    def generate_result(self):
        """Calculate, save, and return AssessmentResult."""
        scores = self.calculate_scores()
        mbti_code = self.determine_personality_type(scores)
        confidence = self.calculate_confidence(scores)

        try:
            personality_type = PersonalityType.objects.get(mbti_type=mbti_code)
        except PersonalityType.DoesNotExist:
            raise ValueError(
                f"Personality type '{mbti_code}' not found. "
                "Run: python manage.py load_mbti_data"
            )

        result, _ = AssessmentResult.objects.update_or_create(
            student=self.session.student,
            defaults={
                'personality_type': personality_type,
                'ei_score': scores['EI'],
                'sn_score': scores['SN'],
                'tf_score': scores['TF'],
                'jp_score': scores['JP'],
                'confidence': confidence,
            },
        )
        return result
