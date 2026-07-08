from django.db import models
from users.models import StudentProfile


class MBTIDimension(models.Model):
    DIMENSION_CHOICES = [
        ('EI', 'Extraversion vs Introversion'),
        ('SN', 'Sensing vs Intuition'),
        ('TF', 'Thinking vs Feeling'),
        ('JP', 'Judging vs Perceiving'),
    ]
    code = models.CharField(max_length=2, choices=DIMENSION_CHOICES, unique=True)
    dimension_a = models.CharField(max_length=50)
    dimension_b = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return f"{self.dimension_a} vs {self.dimension_b}"


class Question(models.Model):
    CATEGORY_CHOICES = [
        ('EI', 'Extraversion/Introversion'),
        ('SN', 'Sensing/Intuition'),
        ('TF', 'Thinking/Feeling'),
        ('JP', 'Judging/Perceiving'),
    ]
    text = models.TextField()
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES)
    dimension_a_weight = models.IntegerField(default=1)  # 1=A-pole question, 0=B-pole question
    dimension_b_weight = models.IntegerField(default=0)

    def __str__(self):
        pole = "A" if self.dimension_a_weight == 1 else "B"
        return f"[{self.category}/{pole}] {self.text[:60]}"


class AnswerChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    value = models.IntegerField()

    def __str__(self):
        return f"{self.text} ({self.value:+d})"


class AssessmentSession(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Session - {self.student.user.username}"

    def progress_percent(self):
        total = Question.objects.count()
        if not total:
            return 0
        return int((self.responses.count() / total) * 100)


class QuestionResponse(models.Model):
    session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(AnswerChoice, on_delete=models.CASCADE)
    response_time = models.IntegerField(default=0)

    class Meta:
        unique_together = ['session', 'question']


class PersonalityType(models.Model):
    mbti_type = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    strengths = models.TextField()
    weaknesses = models.TextField()
    career_recommendations = models.TextField()

    def __str__(self):
        return f"{self.mbti_type} - {self.name}"

    def get_color(self):
        colors = {
            "INTJ": "#1e3a5f", "INTP": "#1e4280", "ENTJ": "#1e5f6b", "ENTP": "#1e5f40",
            "INFJ": "#6b21a8", "INFP": "#7c3aed", "ENFJ": "#9333ea", "ENFP": "#a855f7",
            "ISTJ": "#065f46", "ISFJ": "#047857", "ESTJ": "#059669", "ESFJ": "#10b981",
            "ISTP": "#92400e", "ISFP": "#b45309", "ESTP": "#d97706", "ESFP": "#f59e0b",
        }
        return colors.get(self.mbti_type, "#374151")

    def get_temperament_label(self):
        t1 = self.mbti_type[1]
        t3 = self.mbti_type[3]
        if t1 == 'N' and self.mbti_type[2] == 'T':
            return "Analyst"
        if t1 == 'N' and self.mbti_type[2] == 'F':
            return "Diplomat"
        if t1 == 'S' and t3 == 'J':
            return "Sentinel"
        if t1 == 'S' and t3 == 'P':
            return "Explorer"
        return "Undefined"


class AssessmentResult(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='assessmentresult')
    personality_type = models.ForeignKey(PersonalityType, on_delete=models.PROTECT)
    ei_score = models.DecimalField(max_digits=6, decimal_places=2)
    sn_score = models.DecimalField(max_digits=6, decimal_places=2)
    tf_score = models.DecimalField(max_digits=6, decimal_places=2)
    jp_score = models.DecimalField(max_digits=6, decimal_places=2)
    confidence = models.DecimalField(max_digits=4, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_dimension_scores(self):
        return {
            'EI': float(self.ei_score),
            'SN': float(self.sn_score),
            'TF': float(self.tf_score),
            'JP': float(self.jp_score),
        }

    @staticmethod
    def _score_to_poles(score: float):
        """Convert [-100,+100] → (a_pct, b_pct). +100=100%A, 0=50/50, -100=100%B"""
        a_pct = round((float(score) + 100) / 2, 1)
        b_pct = round(100 - a_pct, 1)
        return a_pct, b_pct

    def get_pole_percentages(self):
        dims = [
            ('EI', 'Extraversion', 'Introversion', 'E', 'I', float(self.ei_score)),
            ('SN', 'Sensing',      'Intuition',    'S', 'N', float(self.sn_score)),
            ('TF', 'Thinking',     'Feeling',      'T', 'F', float(self.tf_score)),
            ('JP', 'Judging',      'Perceiving',   'J', 'P', float(self.jp_score)),
        ]
        result = {}
        for code, a_label, b_label, a_letter, b_letter, score in dims:
            a_pct, b_pct = self._score_to_poles(score)
            dominant = a_letter if score >= 0 else b_letter
            dominant_pct = a_pct if score >= 0 else b_pct
            result[code] = {
                'a_label': a_label, 'b_label': b_label,
                'a_letter': a_letter, 'b_letter': b_letter,
                'a_pct': a_pct, 'b_pct': b_pct,
                'dominant': dominant, 'dominant_pct': dominant_pct,
                'score': score,
            }
        return result

    def get_confidence_percent(self):
        return round(float(self.confidence) * 100)

    def __str__(self):
        return f"{self.student.user.username} - {self.personality_type.mbti_type}"
