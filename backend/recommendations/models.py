from django.db import models
from assessments.models import PersonalityType
from users.models import StudentProfile

class Career(models.Model):
    CATEGORY_CHOICES = [
        ('stem', 'STEM'),
        ('arts', 'Arts & Humanities'),
        ('business', 'Business & Commerce'),
        ('health', 'Health Sciences'),
        ('education', 'Education'),
        ('technical', 'Technical & Vocational'),
        ('engineering', 'Engineering'),
        ('technology', 'Technology'),
        ('research', 'Research & Development'),
        ('public_service', 'Public Service'),
        ('law', 'Law & Justice'),
        ('media', 'Media & Communication'),
        ('agriculture', 'Agriculture'),
        ('tourism', 'Tourism & Hospitality'),
    ]
    
    MARKET_DEMAND_CHOICES = [
        ('very_high', 'Very High Demand'),
        ('high', 'High Demand'),
        ('medium', 'Medium Demand'),
        ('low', 'Low Demand'),
        ('very_low', 'Very Low Demand'),
    ]
    
    COMPLEXITY_CHOICES = [
        ('very_high', 'Very High Complexity'),
        ('high', 'High Complexity'),
        ('medium', 'Medium Complexity'),
        ('low', 'Low Complexity'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True, help_text="Short description for cards and lists")
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=100, blank=True, help_text="More specific category e.g., Software Engineering, Pediatrics")
    
    # Salary Information (Kenyan Context)
    average_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    entry_level_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mid_level_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    senior_level_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Market Information
    kenyan_market_demand = models.CharField(max_length=50, choices=MARKET_DEMAND_CHOICES, default='medium')
    market_demand_trend = models.CharField(max_length=50, choices=[
        ('growing', 'Growing'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
    ], default='stable')
    growth_projection = models.CharField(max_length=200, blank=True, help_text="e.g., 30% growth in next 5 years")
    
    # Education & Skills
    education_requirements = models.TextField(blank=True)
    minimum_education = models.CharField(max_length=100, blank=True, help_text="e.g., KCSE C+, Diploma, Bachelor's")
    skills_required = models.TextField(blank=True, help_text="Comma-separated list of required skills")
    certifications = models.TextField(blank=True, help_text="Required certifications in Kenya")
    
    # Career Details
    work_environment = models.TextField(blank=True)
    typical_work_hours = models.CharField(max_length=100, blank=True)
    career_path = models.TextField(blank=True, help_text="Typical career progression path")
    
    # Kenyan Context
    kenyan_market_analysis = models.TextField(blank=True)
    top_employers = models.TextField(blank=True, help_text="Top employers in Kenya for this career")
    kenyan_universities = models.TextField(blank=True, help_text="Universities offering relevant programs in Kenya")
    scholarships_available = models.TextField(blank=True, help_text="Scholarship opportunities for Kenyan students")
    
    # Complexity & Learning
    complexity_level = models.CharField(max_length=50, choices=COMPLEXITY_CHOICES, default='medium')
    learning_duration = models.CharField(max_length=100, blank=True, help_text="e.g., 4 years for Bachelor's")
    is_kenyan_focused = models.BooleanField(default=True, help_text="Is this career particularly relevant to Kenya?")
    
    # Statistics
    recommendation_count = models.IntegerField(default=0, help_text="Number of times recommended")
    interest_count = models.IntegerField(default=0, help_text="Number of students interested")
    
    # Subjects
    required_subjects = models.ManyToManyField('Subject', related_name='careers_requiring')
    recommended_subjects = models.ManyToManyField('Subject', related_name='careers_recommending')
    beneficial_subjects = models.ManyToManyField('Subject', related_name='careers_beneficial', blank=True)
    
    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['kenyan_market_demand']),
            models.Index(fields=['average_salary']),
            models.Index(fields=['is_active']),
        ]
    
    def update_recommendation_count(self):
        """Update recommendation count from StudentRecommendation"""
        self.recommendation_count = StudentRecommendation.objects.filter(career=self).count()
        self.save()
    
    def get_salary_range(self):
        """Get formatted salary range"""
        if self.entry_level_salary and self.senior_level_salary:
            return f"KES {self.entry_level_salary:,.0f} - KES {self.senior_level_salary:,.0f}"
        elif self.average_salary:
            return f"KES {self.average_salary:,.0f}"
        return "Not specified"
    
    def get_market_demand_display(self):
        """Get human-readable market demand"""
        return dict(self.MARKET_DEMAND_CHOICES).get(self.kenyan_market_demand, self.kenyan_market_demand)
    
    def get_skills_list(self):
        """Get list of required skills"""
        if self.skills_required:
            return [skill.strip() for skill in self.skills_required.split(',')]
        return []

class Subject(models.Model):
    CATEGORY_CHOICES = [
        ('sciences', 'Sciences'),
        ('humanities', 'Humanities'),
        ('languages', 'Languages'),
        ('technical', 'Technical'),
        ('business', 'Business'),
        ('mathematics', 'Mathematics'),
        ('arts', 'Arts'),
        ('computer', 'Computer Studies'),
        ('agriculture', 'Agriculture'),
        ('religious', 'Religious Education'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('very_easy', 'Very Easy'),
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('very_hard', 'Very Hard'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)  # KCSE subject code
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    description = models.TextField(blank=True)
    
    # KCSE Specific
    kcse_weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0, 
                                     help_text="Weight in KCSE calculation")
    is_compulsory = models.BooleanField(default=False, help_text="Is this a compulsory subject?")
    minimum_grade = models.CharField(max_length=2, blank=True, help_text="Minimum grade for university consideration")
    
    # Career Relevance
    high_demand_careers = models.ManyToManyField(Career, related_name='high_demand_subjects', blank=True)
    career_count = models.IntegerField(default=0, help_text="Number of careers requiring this subject")
    
    # Learning Information
    recommended_learning_style = models.CharField(max_length=50, choices=[
        ('visual', 'Visual'),
        ('auditory', 'Auditory'),
        ('reading', 'Reading/Writing'),
        ('kinesthetic', 'Kinesthetic'),
        ('mixed', 'Mixed'),
    ], default='mixed')
    study_hours_recommended = models.IntegerField(default=5, help_text="Recommended study hours per week")
    
    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['difficulty_level']),
            models.Index(fields=['is_compulsory']),
        ]
    
    def update_career_count(self):
        """Update count of careers requiring this subject"""
        self.career_count = Career.objects.filter(
            models.Q(required_subjects=self) | 
            models.Q(recommended_subjects=self) | 
            models.Q(beneficial_subjects=self)
        ).distinct().count()
        self.save()

class CareerSubject(models.Model):
    """Intermediate model for career-subject relationships with importance levels"""
    IMPORTANCE_CHOICES = [
        ('required', 'Required'),
        ('recommended', 'Recommended'),
        ('beneficial', 'Beneficial'),
        ('optional', 'Optional'),
    ]
    
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    importance = models.CharField(max_length=20, choices=IMPORTANCE_CHOICES, default='recommended')
    weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0, 
                                help_text="Weight in academic match calculation")
    
    class Meta:
        unique_together = ['career', 'subject']
        ordering = ['career', '-weight']
    
    def __str__(self):
        return f"{self.career.name} - {self.subject.name} ({self.get_importance_display()})"

class CareerPersonalityMatch(models.Model):
    """Personality type to career compatibility scores"""
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    personality_type = models.ForeignKey(PersonalityType, on_delete=models.CASCADE)
    
    # Enhanced scoring fields
    match_score = models.DecimalField(max_digits=3, decimal_places=2, help_text="0.00-1.00 compatibility score")  # Renamed from compatibility_score
    trait_alignment = models.JSONField(default=dict, help_text="Specific MBTI trait alignments")
    
    # Detailed reasoning
    reasoning = models.TextField()
    strengths_match = models.TextField(blank=True, help_text="How career matches personality strengths")
    challenges = models.TextField(blank=True, help_text="Potential challenges for this personality")
    
    # Statistics
    is_top_match = models.BooleanField(default=False, help_text="Is this a top match for this personality?")
    popularity_rank = models.IntegerField(default=0, help_text="Popularity rank for this personality type")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['career', 'personality_type']
        ordering = ['personality_type', '-match_score']
        indexes = [
            models.Index(fields=['personality_type', 'match_score']),
            models.Index(fields=['is_top_match']),
        ]
    
    def __str__(self):
        return f"{self.personality_type.mbti_type} → {self.career.name} ({self.match_score})"

class LearningStyle(models.Model):
    STYLE_CHOICES = [
        ('visual', 'Visual'),
        ('auditory', 'Auditory'),
        ('reading', 'Reading/Writing'),
        ('kinesthetic', 'Kinesthetic'),
        ('multimodal', 'Multimodal'),
    ]
    
    name = models.CharField(max_length=50, choices=STYLE_CHOICES)
    description = models.TextField()
    detailed_description = models.TextField(blank=True, help_text="More detailed explanation")
    
    # Learning Characteristics
    preferred_activities = models.TextField(blank=True, help_text="Preferred learning activities")
    study_techniques = models.TextField(blank=True, help_text="Effective study techniques")
    common_challenges = models.TextField(blank=True, help_text="Common learning challenges")
    
    # Career Implications
    suitable_careers = models.TextField(blank=True, help_text="Careers that match this learning style")
    
    # Kenyan Context
    kenyan_adaptations = models.TextField(blank=True, help_text="How to adapt this style in Kenyan context")
    local_resources = models.TextField(blank=True, help_text="Local resources for this learning style")
    
    # Meta
    study_recommendations = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class CareerLearningStyle(models.Model):
    """Learning style to career compatibility"""
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    learning_style = models.ForeignKey(LearningStyle, on_delete=models.CASCADE)
    match_score = models.DecimalField(max_digits=3, decimal_places=2, help_text="0.00-1.00 compatibility score")
    
    # Reasoning
    reasoning = models.TextField()
    learning_requirements = models.TextField(blank=True, help_text="How this career requires this learning style")
    adaptation_tips = models.TextField(blank=True, help_text="Tips for adapting if learning style doesn't match")
    
    class Meta:
        unique_together = ['career', 'learning_style']
        ordering = ['career', '-match_score']
    
    def __str__(self):
        return f"{self.learning_style.name} → {self.career.name} ({self.match_score})"

class StudentRecommendation(models.Model):
    """Enhanced student career recommendations with multiple scoring factors"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    career = models.ForeignKey(Career, on_delete=models.CASCADE)
    
    # Enhanced scoring fields
    overall_score = models.DecimalField(max_digits=3, decimal_places=2, help_text="Overall compatibility score 0.00-1.00")
    
    # Individual factor scores
    personality_match_score = models.DecimalField(max_digits=3, decimal_places=2)
    academic_match_score = models.DecimalField(max_digits=3, decimal_places=2)
    market_demand_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    learning_style_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    interests_boost = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    grade_boost = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Detailed reasoning
    reasoning = models.TextField()
    detailed_analysis = models.JSONField(default=dict, blank=True, help_text="Detailed breakdown of scoring factors")
    strengths_alignment = models.TextField(blank=True, help_text="How career aligns with student strengths")
    improvement_areas = models.TextField(blank=True, help_text="Areas needing improvement")
    
    # Student interaction
    is_interested = models.BooleanField(default=False, help_text="Student expressed interest")
    is_bookmarked = models.BooleanField(default=False, help_text="Student saved for later")
    interest_level = models.IntegerField(default=0, help_text="Interest level 1-10")
    viewed_count = models.IntegerField(default=0, help_text="Number of times viewed")
    
    # Learning path
    recommended_subjects = models.ManyToManyField(Subject, blank=True)
    skill_gaps = models.JSONField(default=list, blank=True, help_text="Identified skill gaps")
    learning_path = models.JSONField(default=list, blank=True, help_text="Suggested learning path")
    
    # Meta
    is_active = models.BooleanField(default=True)
    is_generated = models.BooleanField(default=True, help_text="Was this generated by the system?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'career']
        ordering = ['-overall_score', '-created_at']
        indexes = [
            models.Index(fields=['student', 'overall_score']),
            models.Index(fields=['student', 'is_interested']),
            models.Index(fields=['student', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.user.username} - {self.career.name} ({self.overall_score})"
    
    def update_view_count(self):
        """Increment view count"""
        self.viewed_count += 1
        self.save()
    
    def calculate_compatibility_level(self):
        """Get human-readable compatibility level"""
        if self.overall_score >= 0.8:
            return "Excellent Match"
        elif self.overall_score >= 0.7:
            return "Great Match"
        elif self.overall_score >= 0.6:
            return "Good Match"
        elif self.overall_score >= 0.5:
            return "Moderate Match"
        else:
            return "Potential Match"
    
    def get_score_breakdown(self):
        """Get detailed score breakdown"""
        return {
            'overall': float(self.overall_score),
            'personality': float(self.personality_match_score),
            'academic': float(self.academic_match_score) if self.academic_match_score else 0,
            'market': float(self.market_demand_score) if self.market_demand_score else 0,
            'learning_style': float(self.learning_style_score) if self.learning_style_score else 0,
            'interests': float(self.interests_boost),
            'grade_adjustment': float(self.grade_boost)
        }

class RecommendationAnalytics(models.Model):
    """Analytics for recommendation system"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    
    # Statistics
    total_recommendations = models.IntegerField(default=0)
    recommendations_viewed = models.IntegerField(default=0)
    recommendations_interested = models.IntegerField(default=0)
    average_compatibility_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Distribution
    compatibility_distribution = models.JSONField(default=dict, help_text="Distribution by compatibility level")
    category_distribution = models.JSONField(default=dict, help_text="Distribution by career category")
    
    # Trends
    last_generated = models.DateTimeField(null=True, blank=True)
    generation_count = models.IntegerField(default=0)
    average_generation_time = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, 
                                                 help_text="Average generation time in seconds")
    
    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Recommendation Analytics"
    
    def __str__(self):
        return f"Analytics for {self.student.user.username}"
    
    def update_statistics(self):
        """Update statistics from student recommendations"""
        recommendations = StudentRecommendation.objects.filter(student=self.student)
        
        self.total_recommendations = recommendations.count()
        self.recommendations_viewed = recommendations.filter(viewed_count__gt=0).count()
        self.recommendations_interested = recommendations.filter(is_interested=True).count()
        
        if self.total_recommendations > 0:
            avg_score = recommendations.aggregate(models.Avg('overall_score'))['overall_score__avg']
            self.average_compatibility_score = avg_score or 0.0
        
        self.save()