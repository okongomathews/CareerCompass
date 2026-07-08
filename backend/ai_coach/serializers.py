from rest_framework import serializers
from .models import Conversation, Message, CoachingPlan, ResourceRecommendation
from users.models import StudentProfile
from assessments.models import PersonalityType
from recommendations.models import LearningStyle

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'is_from_ai', 'timestamp']
        read_only_fields = ['is_from_ai', 'timestamp']

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'student', 'is_active', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['student', 'created_at', 'updated_at']

class ChatMessageSerializer(serializers.Serializer):
    """Serializer for chat message input"""
    message = serializers.CharField(max_length=1000)

class ResourceRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceRecommendation
        fields = ['id', 'title', 'description', 'url', 'resource_type', 'relevance_score', 'created_at']

class CoachingPlanSerializer(serializers.ModelSerializer):
    personality_type = serializers.StringRelatedField()
    learning_style = serializers.StringRelatedField()
    resources = ResourceRecommendationSerializer(many=True, read_only=True)
    
    class Meta:
        model = CoachingPlan
        fields = [
            'id', 'personality_type', 'learning_style', 
            'goals', 'challenges', 'strengths', 'improvement_areas',
            'resources', 'created_at', 'updated_at'
        ]