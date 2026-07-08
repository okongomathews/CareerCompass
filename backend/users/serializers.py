from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, StudentProfile, School

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name', 'code', 'county', 'type']

class StudentProfileSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.all(),
        source='school',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'school', 'school_id', 'grade_level', 
            'subjects', 'career_aspirations', 'kcpe_score', 'kcse_score'
        ]

class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'user_type', 'phone_number', 'date_of_birth', 'student_profile'
        ]
        read_only_fields = ['user_type']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    # Student profile fields
    grade_level = serializers.CharField(write_only=True)
    school_id = serializers.IntegerField(write_only=True, required=False)
    career_aspirations = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'grade_level', 'school_id', 'career_aspirations'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_username(self, value):
        if CustomUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value
    
    def create(self, validated_data):
        # Extract student profile data
        grade_level = validated_data.pop('grade_level')
        school_id = validated_data.pop('school_id', None)
        career_aspirations = validated_data.pop('career_aspirations', '')
        
        # Create user
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            date_of_birth=validated_data.get('date_of_birth'),
            user_type='student'
        )
        
        # Get or create student profile
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                pass
        
        # Use get_or_create to avoid duplicates
        profile, created = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                'school': school,
                'grade_level': grade_level,
                'career_aspirations': career_aspirations
            }
        )
        
        # Update if profile already existed
        if not created:
            if school:
                profile.school = school
            profile.grade_level = grade_level
            profile.career_aspirations = career_aspirations
            profile.save()
        
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('Account disabled')
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError('Must include username and password')