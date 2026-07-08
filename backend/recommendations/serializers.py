from rest_framework import serializers
from .models import (
    Career, Subject, StudentRecommendation, LearningStyle,
    CareerPersonalityMatch, CareerSubject, CareerLearningStyle,
    RecommendationAnalytics
)
from assessments.models import PersonalityType

class SubjectSerializer(serializers.ModelSerializer):
    """Enhanced Subject Serializer"""
    career_count = serializers.IntegerField(read_only=True, help_text="Number of careers requiring this subject")
    is_compulsory_display = serializers.CharField(source='get_is_compulsory_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_level_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'code', 'category', 'category_display',
            'difficulty_level', 'difficulty_display',
            'description', 'kcse_weight', 'is_compulsory', 'is_compulsory_display',
            'minimum_grade', 'recommended_learning_style', 'study_hours_recommended',
            'career_count', 'is_active', 'created_at'
        ]
        read_only_fields = ['career_count', 'created_at']

class PersonalityTypeSerializer(serializers.ModelSerializer):
    """Personality Type Serializer"""
    class Meta:
        model = PersonalityType
        fields = ['id', 'mbti_type', 'name', 'description', 'strengths', 'weaknesses', 'career_recommendations']

class CareerSubjectSerializer(serializers.ModelSerializer):
    """Career-Subject Relationship Serializer"""
    subject = SubjectSerializer(read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    
    class Meta:
        model = CareerSubject
        fields = ['id', 'subject', 'importance', 'importance_display', 'weight']

class CareerSerializer(serializers.ModelSerializer):
    """Enhanced Career Serializer"""
    # Relationships
    required_subjects = SubjectSerializer(many=True, read_only=True)
    recommended_subjects = SubjectSerializer(many=True, read_only=True)
    beneficial_subjects = SubjectSerializer(many=True, read_only=True)
    
    # Enhanced fields
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    market_demand_display = serializers.CharField(source='get_market_demand_display', read_only=True)
    complexity_display = serializers.CharField(source='get_complexity_level_display', read_only=True)
    market_trend_display = serializers.CharField(source='get_market_demand_trend_display', read_only=True)
    
    # Calculated fields
    salary_range = serializers.SerializerMethodField()
    skills_list = serializers.SerializerMethodField()
    is_popular = serializers.SerializerMethodField()
    
    class Meta:
        model = Career
        fields = [
            'id', 'name', 'description', 'short_description',
            'category', 'category_display', 'subcategory',
            
            # Salary Information
            'average_salary', 'entry_level_salary', 'mid_level_salary', 
            'senior_level_salary', 'salary_range',
            
            # Market Information
            'kenyan_market_demand', 'market_demand_display',
            'market_demand_trend', 'market_trend_display',
            'growth_projection',
            
            # Education & Skills
            'education_requirements', 'minimum_education',
            'skills_required', 'skills_list', 'certifications',
            
            # Career Details
            'work_environment', 'typical_work_hours', 'career_path',
            
            # Kenyan Context
            'kenyan_market_analysis', 'top_employers',
            'kenyan_universities', 'scholarships_available',
            
            # Complexity & Learning
            'complexity_level', 'complexity_display',
            'learning_duration', 'is_kenyan_focused',
            
            # Statistics
            'recommendation_count', 'interest_count',
            'is_popular',
            
            # Subjects
            'required_subjects', 'recommended_subjects', 'beneficial_subjects',
            
            # Meta
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['recommendation_count', 'interest_count', 'created_at', 'updated_at']
    
    def get_salary_range(self, obj):
        return obj.get_salary_range()
    
    def get_skills_list(self, obj):
        return obj.get_skills_list()
    
    def get_is_popular(self, obj):
        return obj.recommendation_count > 10  # Define popularity threshold

class CareerDetailSerializer(CareerSerializer):
    """Detailed Career Serializer with enhanced relationships"""
    career_subjects = CareerSubjectSerializer(source='careersubject_set', many=True, read_only=True)
    personality_matches = serializers.SerializerMethodField()
    learning_style_matches = serializers.SerializerMethodField()
    
    class Meta(CareerSerializer.Meta):
        fields = CareerSerializer.Meta.fields + [
            'career_subjects', 'personality_matches', 'learning_style_matches'
        ]
    
    def get_personality_matches(self, obj):
        """Get top personality matches for this career"""
        matches = CareerPersonalityMatch.objects.filter(
            career=obj, 
            is_top_match=True
        ).select_related('personality_type')[:5]
        
        return CareerPersonalityMatchSerializer(matches, many=True).data
    
    def get_learning_style_matches(self, obj):
        """Get learning style matches for this career"""
        matches = CareerLearningStyle.objects.filter(
            career=obj
        ).select_related('learning_style').order_by('-match_score')[:3]
        
        return CareerLearningStyleSerializer(matches, many=True).data

class LearningStyleSerializer(serializers.ModelSerializer):
    """Enhanced Learning Style Serializer"""
    name_display = serializers.CharField(source='get_name_display', read_only=True)
    
    class Meta:
        model = LearningStyle
        fields = [
            'id', 'name', 'name_display', 'description', 'detailed_description',
            'preferred_activities', 'study_techniques', 'common_challenges',
            'suitable_careers', 'kenyan_adaptations', 'local_resources',
            'study_recommendations', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class CareerPersonalityMatchSerializer(serializers.ModelSerializer):
    """Enhanced Career-Personality Match Serializer"""
    career = CareerSerializer(read_only=True)
    personality_type = PersonalityTypeSerializer(read_only=True)
    match_score_display = serializers.SerializerMethodField()
    trait_alignment = serializers.JSONField()
    
    class Meta:
        model = CareerPersonalityMatch
        fields = [
            'id', 'career', 'personality_type', 'match_score', 'match_score_display',
            'trait_alignment', 'reasoning', 'strengths_match', 'challenges',
            'is_top_match', 'popularity_rank', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_match_score_display(self, obj):
        return f"{obj.match_score * 100:.0f}%"

class CareerLearningStyleSerializer(serializers.ModelSerializer):
    """Career-Learning Style Compatibility Serializer"""
    career = CareerSerializer(read_only=True)
    learning_style = LearningStyleSerializer(read_only=True)
    match_score_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CareerLearningStyle
        fields = [
            'id', 'career', 'learning_style', 'match_score', 'match_score_display',
            'reasoning', 'learning_requirements', 'adaptation_tips'
        ]
    
    def get_match_score_display(self, obj):
        return f"{obj.match_score * 100:.0f}%"

class StudentRecommendationSerializer(serializers.ModelSerializer):
    """Enhanced Student Recommendation Serializer"""
    career = CareerSerializer(read_only=True)
    recommended_subjects = SubjectSerializer(many=True, read_only=True)
    
    # Enhanced fields
    compatibility_level = serializers.SerializerMethodField()
    score_breakdown = serializers.SerializerMethodField()
    days_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentRecommendation
        fields = [
            'id', 'career', 
            
            # Scores
            'overall_score', 'personality_match_score', 'academic_match_score',
            'market_demand_score', 'learning_style_score', 'interests_boost', 'grade_boost',
            
            # Analysis
            'reasoning', 'detailed_analysis', 'strengths_alignment', 'improvement_areas',
            'compatibility_level', 'score_breakdown',
            
            # Student Interaction
            'is_interested', 'is_bookmarked', 'interest_level', 'viewed_count',
            
            # Learning Path
            'recommended_subjects', 'skill_gaps', 'learning_path',
            
            # Meta
            'days_ago', 'is_active', 'is_generated', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_compatibility_level(self, obj):
        return obj.calculate_compatibility_level()
    
    def get_score_breakdown(self, obj):
        return obj.get_score_breakdown()
    
    def get_days_ago(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        return delta.days

class StudentRecommendationDetailSerializer(StudentRecommendationSerializer):
    """Detailed Student Recommendation with enhanced data"""
    career = CareerDetailSerializer(read_only=True)
    
    # Additional analysis
    market_insights = serializers.SerializerMethodField()
    learning_path_suggestions = serializers.SerializerMethodField()
    related_careers = serializers.SerializerMethodField()
    
    class Meta(StudentRecommendationSerializer.Meta):
        fields = StudentRecommendationSerializer.Meta.fields + [
            'market_insights', 'learning_path_suggestions', 'related_careers'
        ]
    
    def get_market_insights(self, obj):
        """Get market insights for this career recommendation"""
        career = obj.career
        return {
            'demand_level': career.get_market_demand_display(),
            'growth_projection': career.growth_projection,
            'top_employers': career.top_employers,
            'kenyan_universities': career.kenyan_universities,
            'salary_range': career.get_salary_range()
        }
    
    def get_learning_path_suggestions(self, obj):
        """Get learning path suggestions from recommendation or generate default"""
        if obj.learning_path:
            return obj.learning_path
        
        # Generate default learning path based on career complexity
        career = obj.career
        if career.complexity_level in ['very_high', 'high']:
            return [
                {'phase': 'Foundation (1-2 years)', 'focus': ['KCSE preparation', 'Core subjects mastery']},
                {'phase': 'Undergraduate (3-5 years)', 'focus': ['University degree', 'Internships']},
                {'phase': 'Professional Development (1-3 years)', 'focus': ['Certifications', 'Work experience']}
            ]
        else:
            return [
                {'phase': 'Training (1-2 years)', 'focus': ['College diploma', 'Basic skills']},
                {'phase': 'Entry Level (1-2 years)', 'focus': ['Work experience', 'Skill development']},
                {'phase': 'Career Growth (Ongoing)', 'focus': ['Specialization', 'Advanced training']}
            ]
    
    def get_related_careers(self, obj):
        """Get related careers based on category and subjects"""
        career = obj.career
        
        # Get careers in same category
        related = Career.objects.filter(
            category=career.category,
            is_active=True
        ).exclude(id=career.id)[:4]
        
        return CareerSerializer(related, many=True).data

class CareerRecommendationSerializer(serializers.Serializer):
    """Serializer for generated recommendations (not saved) with enhanced fields"""
    career = CareerSerializer()
    
    # Individual factor scores
    overall_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    personality_match_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    academic_match_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    market_demand_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    learning_style_score = serializers.DecimalField(max_digits=3, decimal_places=2)
    grade_boost = serializers.DecimalField(max_digits=3, decimal_places=2)
    interests_boost = serializers.DecimalField(max_digits=3, decimal_places=2)
    
    # Analysis
    reasoning = serializers.CharField()
    score_breakdown = serializers.DictField()
    compatibility_level = serializers.CharField()
    
    class Meta:
        fields = [
            'career', 'overall_score', 'personality_match_score', 
            'academic_match_score', 'market_demand_score', 'learning_style_score',
            'grade_boost', 'interests_boost', 'reasoning', 'score_breakdown',
            'compatibility_level'
        ]

class SubjectRecommendationSerializer(serializers.Serializer):
    """Serializer for subject recommendations"""
    subject = SubjectSerializer()
    is_recommended = serializers.BooleanField()
    match_reasons = serializers.ListField(child=serializers.CharField())
    career_relevance = serializers.IntegerField(min_value=0, max_value=100)
    difficulty_assessment = serializers.CharField()
    
    class Meta:
        fields = ['subject', 'is_recommended', 'match_reasons', 
                 'career_relevance', 'difficulty_assessment']

class RecommendationAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for recommendation analytics"""
    student = serializers.StringRelatedField()
    compatibility_distribution = serializers.JSONField()
    category_distribution = serializers.JSONField()
    generation_frequency = serializers.SerializerMethodField()
    engagement_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = RecommendationAnalytics
        fields = [
            'id', 'student', 'total_recommendations', 'recommendations_viewed',
            'recommendations_interested', 'average_compatibility_score',
            'compatibility_distribution', 'category_distribution',
            'generation_frequency', 'engagement_rate',
            'last_generated', 'generation_count', 'average_generation_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_generation_frequency(self, obj):
        """Calculate generation frequency"""
        if obj.generation_count > 0 and obj.last_generated:
            from django.utils import timezone
            days_since_creation = (timezone.now() - obj.created_at).days
            if days_since_creation > 0:
                return obj.generation_count / days_since_creation
        return 0
    
    def get_engagement_rate(self, obj):
        """Calculate engagement rate"""
        if obj.total_recommendations > 0:
            return (obj.recommendations_viewed / obj.total_recommendations) * 100
        return 0

class CareerComparisonSerializer(serializers.Serializer):
    """Serializer for comparing multiple careers"""
    careers = CareerSerializer(many=True)
    comparison_data = serializers.ListField(
        child=serializers.DictField()
    )
    student_scores = serializers.DictField()
    recommendations = serializers.ListField(child=serializers.CharField())
    
    class Meta:
        fields = ['careers', 'comparison_data', 'student_scores', 'recommendations']

class LearningPathSerializer(serializers.Serializer):
    """Serializer for learning path suggestions"""
    career = CareerSerializer()
    phases = serializers.ListField(
        child=serializers.DictField()
    )
    estimated_duration = serializers.CharField()
    key_milestones = serializers.ListField(child=serializers.CharField())
    resources = serializers.ListField(
        child=serializers.DictField()
    )
    
    class Meta:
        fields = ['career', 'phases', 'estimated_duration', 
                 'key_milestones', 'resources']
