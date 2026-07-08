from rest_framework import serializers
from .models import (
    MBTIDimension, Question, AnswerChoice, AssessmentSession,
    QuestionResponse, PersonalityType, AssessmentResult
)

class MBTIDimensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MBTIDimension
        fields = ['id', 'code', 'dimension_a', 'dimension_b', 'description']

class AnswerChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = ['id', 'text', 'value']

class QuestionSerializer(serializers.ModelSerializer):
    choices = AnswerChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'category', 'choices', 'dimension_a_weight', 'dimension_b_weight']

class QuestionResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    answer_text = serializers.CharField(source='answer.text', read_only=True)
    
    class Meta:
        model = QuestionResponse
        fields = ['id', 'question', 'question_text', 'answer', 'answer_text', 'response_time']

class AssessmentSessionSerializer(serializers.ModelSerializer):
    responses = QuestionResponseSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = AssessmentSession
        fields = ['id', 'student', 'started_at', 'completed_at', 'is_completed', 'responses', 'progress']
        read_only_fields = ['started_at', 'completed_at', 'is_completed']
    
    def get_progress(self, obj):
        total_questions = Question.objects.count()
        if total_questions == 0:
            return 0
        responses_count = obj.responses.count()
        return min(100, int((responses_count / total_questions) * 100))

class PersonalityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalityType
        fields = ['id', 'mbti_type', 'name', 'description', 'strengths', 'weaknesses', 'career_recommendations']

class AssessmentResultSerializer(serializers.ModelSerializer):
    personality_type = PersonalityTypeSerializer(read_only=True)
    personality_type_id = serializers.PrimaryKeyRelatedField(
        queryset=PersonalityType.objects.all(), 
        source='personality_type',
        write_only=True
    )
    
    class Meta:
        model = AssessmentResult
        fields = [
            'id', 'student', 'personality_type', 'personality_type_id',
            'ei_score', 'sn_score', 'tf_score', 'jp_score', 
            'confidence', 'created_at'
        ]
        read_only_fields = ['created_at']

class AssessmentSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting assessment responses"""
    session_id = serializers.IntegerField()
    responses = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    
    def validate_responses(self, value):
        for response in value:
            if 'question_id' not in response or 'answer_id' not in response:
                raise serializers.ValidationError("Each response must contain question_id and answer_id")
        return value

class QuickAssessmentSerializer(serializers.Serializer):
    """Serializer for quick personality assessment (if needed)"""
    answers = serializers.ListField(
        child=serializers.ChoiceField(choices=[-3, -2, -1, 0, 1, 2, 3]),
        min_length=20,
        max_length=100
    )