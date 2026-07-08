# career_compass/coaching/models.py
"""
Coaching Plan Models for CareerCompass
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class CoachingPlan(models.Model):
    """Main coaching plan model"""
    
    PLAN_TYPES = [
        ('basic', 'Basic Coaching'),
        ('premium', 'Premium Coaching'),
        ('enterprise', 'Enterprise Coaching'),
    ]
    
    DURATION_CHOICES = [
        ('1_month', '1 Month'),
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('12_months', '12 Months'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    price_kes = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    is_active = models.BooleanField(default=True)
    features = models.JSONField(default=list)  # List of feature descriptions
    ai_sessions_per_month = models.IntegerField(default=0)
    human_sessions_per_month = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - KES {self.price_kes}/month"
    
    class Meta:
        ordering = ['price_kes']


class UserCoachingSubscription(models.Model):
    """User subscription to coaching plans"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending Payment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaching_subscriptions')
    plan = models.ForeignKey(CoachingPlan, on_delete=models.SET_NULL, null=True, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    # Usage tracking
    ai_sessions_used = models.IntegerField(default=0)
    human_sessions_used = models.IntegerField(default=0)
    last_reset_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
    def is_active(self):
        return self.status == 'active' and timezone.now() < self.end_date
    
    def reset_monthly_usage(self):
        """Reset monthly usage counters"""
        self.ai_sessions_used = 0
        self.human_sessions_used = 0
        self.last_reset_date = timezone.now()
        self.save()
    
    def can_use_ai_session(self):
        """Check if user can use AI session"""
        if not self.is_active():
            return False
        return self.ai_sessions_used < self.plan.ai_sessions_per_month
    
    def can_use_human_session(self):
        """Check if user can use human session"""
        if not self.is_active():
            return False
        return self.human_sessions_used < self.plan.human_sessions_per_month
    
    def use_ai_session(self):
        """Record AI session usage"""
        if self.can_use_ai_session():
            self.ai_sessions_used += 1
            self.save()
            return True
        return False
    
    def use_human_session(self):
        """Record human session usage"""
        if self.can_use_human_session():
            self.human_sessions_used += 1
            self.save()
            return True
        return False


class CoachingSession(models.Model):
    """Individual coaching sessions"""
    
    SESSION_TYPES = [
        ('ai', 'AI Coaching Session'),
        ('human', 'Human Coach Session'),
        ('hybrid', 'Hybrid Session'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaching_sessions')
    subscription = models.ForeignKey(UserCoachingSubscription, on_delete=models.CASCADE, 
                                     related_name='sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Session details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_time = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    
    # AI-specific fields
    ai_model_used = models.CharField(max_length=100, blank=True)
    ai_response = models.JSONField(default=dict, blank=True)
    user_input = models.TextField(blank=True)
    
    # Human coach fields
    coach = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                              related_name='coaching_sessions_conducted')
    coach_notes = models.TextField(blank=True)
    rating = models.IntegerField(null=True, blank=True)  # 1-5
    feedback = models.TextField(blank=True)
    
    # Recording/transcript
    recording_url = models.URLField(blank=True)
    transcript = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.title} - {self.get_session_type_display()}"
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-scheduled_time']


class CareerGoal(models.Model):
    """User career goals tied to coaching"""
    
    GOAL_TYPES = [
        ('skill', 'Skill Development'),
        ('promotion', 'Get Promotion'),
        ('career_switch', 'Career Switch'),
        ('salary', 'Salary Increase'),
        ('leadership', 'Leadership Role'),
        ('entrepreneurship', 'Start Business'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='career_goals')
    goal_type = models.CharField(max_length=50, choices=GOAL_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority = models.IntegerField(default=3)  # 1-5, 1 being highest
    
    # Progress tracking
    progress_percentage = models.IntegerField(default=0)
    milestones = models.JSONField(default=list)  # List of milestone objects
    
    # Coaching integration
    coaching_sessions = models.ManyToManyField(CoachingSession, blank=True, 
                                               related_name='related_goals')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    class Meta:
        ordering = ['priority', 'target_date']


class ActionItem(models.Model):
    """Action items from coaching sessions"""
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    coaching_session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE, 
                                         related_name='action_items')
    career_goal = models.ForeignKey(CareerGoal, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='action_items')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, default='pending')
    
    # Completion tracking
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_priority_display()}"
    
    class Meta:
        ordering = ['priority', 'due_date']


class ResourceRecommendation(models.Model):
    """Learning resources recommended by AI or coaches"""
    
    RESOURCE_TYPES = [
        ('course', 'Online Course'),
        ('book', 'Book'),
        ('article', 'Article'),
        ('video', 'Video'),
        ('podcast', 'Podcast'),
        ('tool', 'Tool/Software'),
        ('event', 'Event/Conference'),
        ('community', 'Community/Forum'),
    ]
    
    coaching_session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE,
                                        related_name='resource_recommendations')
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField()
    estimated_hours = models.IntegerField(null=True, blank=True)
    
    # Cost information
    is_free = models.BooleanField(default=False)
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='KES')
    
    # Kenyan context
    is_local = models.BooleanField(default=False)
    provider = models.CharField(max_length=100, blank=True)
    
    # Completion tracking
    completed_by_user = models.BooleanField(default=False)
    user_rating = models.IntegerField(null=True, blank=True)  # 1-5
    user_feedback = models.TextField(blank=True)
    
    recommended_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_resource_type_display()}"
    
    class Meta:
        ordering = ['-recommended_at']