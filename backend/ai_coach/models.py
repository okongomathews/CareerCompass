# ai_coach/models.py - ENHANCED
from django.db import models
from users.models import StudentProfile
from assessments.models import PersonalityType
from recommendations.models import LearningStyle

class Conversation(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default='Career Guidance Session')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.student.user.username}"
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_from_ai = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']

class CoachingPlan(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='coachingplan')
    personality_type = models.ForeignKey(PersonalityType, on_delete=models.CASCADE)
    learning_style = models.ForeignKey(LearningStyle, on_delete=models.CASCADE)
    
    # Goals (structured as JSON)
    short_term_goals = models.JSONField(default=list)  # Next 3 months
    medium_term_goals = models.JSONField(default=list)  # Next 6-12 months
    long_term_goals = models.JSONField(default=list)    # Next 2-5 years
    
    # Challenges and strengths
    identified_challenges = models.JSONField(default=list)
    key_strengths = models.JSONField(default=list)
    
    # Action plan
    action_items = models.JSONField(default=list)
    
    # Progress tracking
    progress_milestones = models.JSONField(default=list)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Coaching Plan for {self.student.user.username}"
    
    class Meta:
        ordering = ['-updated_at']
    
    def calculate_progress(self):
        """Calculate overall progress percentage.

        action_items may be a list of strings (new format) or dicts with a
        'completed' key (old format).  Handles both gracefully.
        """
        total_items = len(self.action_items)
        if total_items == 0:
            return 0

        completed_items = sum(
            1 for item in self.action_items
            if (isinstance(item, dict) and item.get('completed', False))
        )
        self.completion_percentage = (completed_items / total_items) * 100
        self.save()
        return self.completion_percentage

class ResourceRecommendation(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('article', 'Article'),
        ('video', 'Video'),
        ('book', 'Book'),
        ('course', 'Online Course'),
        ('tool', 'Tool/Software'),
        ('kenyan_resource', 'Kenyan Resource'),
        ('scholarship', 'Scholarship'),
    ]
    
    coaching_plan = models.ForeignKey(CoachingPlan, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField(blank=True)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPE_CHOICES)
    relevance_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Kenyan context
    is_kenyan_specific = models.BooleanField(default=False)
    cost_in_kes = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=100, blank=True)  # e.g., "2 weeks", "6 months"
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-relevance_score']

class AICoachLog(models.Model):
    """Log AI coach interactions for improvement"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True)
    user_message = models.TextField()
    ai_response = models.TextField()
    response_time_ms = models.IntegerField()  # Time taken to generate response
    satisfaction_score = models.IntegerField(null=True, blank=True)  # 1-5 rating
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']