from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('user',    'General User'),    # non-student: professionals, career-changers, etc.
        ('student', 'Student'),         # has school affiliation, academic subjects
        ('admin',   'Administrator'),   # staff access to admin panel
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    
    # Additional contact information
    address = models.TextField(blank=True)
    county = models.CharField(max_length=100, blank=True)
    sub_county = models.CharField(max_length=100, blank=True)
    town = models.CharField(max_length=100, blank=True)
    
    # Account status
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Add related_name to avoid clash with default User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='customuser_set',
        related_query_name='customuser',
    )
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class StudentProfile(models.Model):
    GRADE_LEVEL_CHOICES = [
        # Pre-secondary
        ('class7',  'Class 7 / Junior Secondary'),
        ('class8',  'Class 8 / Junior Secondary (Final)'),
        # Secondary
        ('form1',   'Form 1'),
        ('form2',   'Form 2'),
        ('form3',   'Form 3'),
        ('form4',   'Form 4 (KCSE Candidate)'),
        # Post-secondary / Transitioning
        ('form4_complete', 'Completed Form 4 — Awaiting Results'),
        ('gap_year',       'Gap Year — Deciding Next Steps'),
        # Higher education
        ('diploma',        'Diploma / Certificate Programme'),
        ('year1',          'University — Year 1'),
        ('year2',          'University — Year 2'),
        ('year3',          'University — Year 3'),
        ('year4',          'University — Year 4 / Final Year'),
        ('postgrad',       'Postgraduate (Masters / PhD)'),
        # Working / returning
        ('working',        'Working — Considering Returning to School'),
        ('career_change',  'Career Change — Re-evaluating Direction'),
        ('recent_graduate','Recent Graduate — Job Seeking'),
    ]
    
    ACADEMIC_PERFORMANCE_CHOICES = [
        ('excellent', 'Excellent (A / 80-100%)'),
        ('good', 'Good (B / 65-79%)'),
        ('average', 'Average (C / 50-64%)'),
        ('below_average', 'Below Average (D / 40-49%)'),
        ('poor', 'Poor (E / 0-39%)'),
        ('not_applicable', 'Not Applicable / Haven\'t Started'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='studentprofile')
    school = models.ForeignKey('School', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Academic Information
    grade_level = models.CharField(
        max_length=20, 
        choices=GRADE_LEVEL_CHOICES, 
        default='form4_complete',
        verbose_name='Current Grade Level'
    )
    
    academic_performance = models.CharField(
        max_length=20,
        choices=ACADEMIC_PERFORMANCE_CHOICES,
        default='good',
        verbose_name='Overall Academic Performance',
        help_text='Select your average academic performance level'
    )
    
    # Subjects and Education
    subjects = models.ManyToManyField('recommendations.Subject', blank=True)
    career_aspirations = models.TextField(
        blank=True,
        help_text='Describe your career goals and interests'
    )
    
    # Exam Scores
    kcpe_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='KCPE Score',
        help_text='Enter your KCPE score (0-500)'
    )
    
    kcse_score = models.CharField(
        max_length=10, 
        blank=True,
        verbose_name='KCSE Grade',
        help_text='Enter your KCSE grade (e.g., A, B+, C)'
    )
    
    # Academic Strengths
    strongest_subjects = models.ManyToManyField(
        'recommendations.Subject', 
        related_name='strong_for_students',
        blank=True,
        verbose_name='Strongest Subjects',
        help_text='Subjects you excel in'
    )
    
    weakest_subjects = models.ManyToManyField(
        'recommendations.Subject', 
        related_name='weak_for_students',
        blank=True,
        verbose_name='Challenging Subjects',
        help_text='Subjects you find difficult'
    )
    
    # Learning Preferences
    prefers_group_study = models.BooleanField(
        default=False,
        verbose_name='Prefers Group Study',
        help_text='Do you prefer studying in groups?'
    )
    
    prefers_individual_study = models.BooleanField(
        default=True,
        verbose_name='Prefers Individual Study',
        help_text='Do you prefer studying alone?'
    )
    
    learns_best_morning = models.BooleanField(
        default=False,
        verbose_name='Learns Best in Morning',
        help_text='Are you most productive in the morning?'
    )
    
    learns_best_evening = models.BooleanField(
        default=False,
        verbose_name='Learns Best in Evening',
        help_text='Are you most productive in the evening?'
    )
    
    # Extracurricular Activities
    extracurricular_activities = models.TextField(
        blank=True,
        verbose_name='Extracurricular Activities',
        help_text='Clubs, sports, or other activities you participate in'
    )
    
    # Career Interests
    career_interests = models.TextField(
        blank=True,
        verbose_name='Career Interests',
        help_text='Specific careers or fields you are interested in'
    )
    
    # Profile Management
    profile_completion = models.IntegerField(
        default=0,
        verbose_name='Profile Completion (%)',
        help_text='Percentage of profile completion'
    )
    
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    last_profile_update = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Student Profile: {self.user.username}"
    
    def get_grade_level_display(self):
        return dict(self.GRADE_LEVEL_CHOICES).get(self.grade_level, self.grade_level)
    
    def get_academic_performance_display(self):
        return dict(self.ACADEMIC_PERFORMANCE_CHOICES).get(
            self.academic_performance, 
            self.academic_performance
        )
    
    def calculate_profile_completion(self):
        """Calculate profile completion percentage – safe for unsaved instances."""
        if not self.pk:
            self.profile_completion = 0
            return 0

        total_fields = 0
        completed_fields = 0

        personal_fields = [
            (self.user.first_name, 'First Name'),
            (self.user.last_name, 'Last Name'),
            (self.user.email, 'Email'),
        ]
        academic_fields = [
            (self.school, 'School'),
            (self.grade_level, 'Grade Level'),
            (self.academic_performance, 'Academic Performance'),
        ]
        important_fields = [
            (self.career_aspirations, 'Career Aspirations'),
        ]

        for field_value, field_name in personal_fields + academic_fields:
            total_fields += 1
            if field_value:
                if field_name == 'Career Aspirations':
                    if field_value.strip():
                        completed_fields += 1
                else:
                    completed_fields += 1

        # ManyToMany – safe because we have a pk now
        total_fields += 1
        if self.subjects.exists():
            completed_fields += 1

        if total_fields > 0:
            completion_percentage = int((completed_fields / total_fields) * 100)
            self.profile_completion = min(completion_percentage, 100)
        else:
            self.profile_completion = 0

        return self.profile_completion

    def save(self, *args, **kwargs):
        # 1. Save first to get an ID
        super().save(*args, **kwargs)
        
        # 2. Now calculate completion (safe)
        self.calculate_profile_completion()
        
        # 3. Persist the updated completion value (avoid recursion)
        self.__class__.objects.filter(pk=self.pk).update(
            profile_completion=self.profile_completion
        )
    
    def get_academic_summary(self):
        return {
            'grade_level': self.get_grade_level_display(),
            'academic_performance': self.get_academic_performance_display(),
            'kcpe_score': float(self.kcpe_score) if self.kcpe_score else None,
            'kcse_grade': self.kcse_score if self.kcse_score else 'Not Available',
            'subjects_count': self.subjects.count(),
            'profile_completion': self.profile_completion,
            'strong_subjects': list(self.strongest_subjects.values_list('name', flat=True)),
            'weak_subjects': list(self.weakest_subjects.values_list('name', flat=True)),
        }
    
    def get_learning_preferences(self):
        preferences = []
        if self.prefers_group_study:
            preferences.append('Group Study')
        if self.prefers_individual_study:
            preferences.append('Individual Study')
        if self.learns_best_morning:
            preferences.append('Morning Learning')
        if self.learns_best_evening:
            preferences.append('Evening Learning')
        return preferences
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'


class School(models.Model):
    SCHOOL_TYPE_CHOICES = [
        ('national', 'National School'),
        ('county', 'County School'),
        ('private', 'Private School'),
        ('boarding', 'Boarding School'),
        ('day', 'Day School'),
        ('mixed', 'Mixed Day & Boarding'),
        ('boys', 'Boys Only'),
        ('girls', 'Girls Only'),
        ('special_needs', 'Special Needs School'),
        ('international', 'International School'),
    ]
    
    SCHOOL_CATEGORY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('faith_based', 'Faith-Based'),
        ('community', 'Community'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='School Name')
    code = models.CharField(max_length=20, unique=True, verbose_name='School Code')
    
    # Location Information
    county = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100, blank=True)
    constituency = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    physical_address = models.TextField(blank=True)
    
    # School Type
    type = models.CharField(
        max_length=50, 
        choices=SCHOOL_TYPE_CHOICES,
        default='county',
        verbose_name='School Type'
    )
    
    category = models.CharField(
        max_length=50,
        choices=SCHOOL_CATEGORY_CHOICES,
        default='public',
        verbose_name='School Category'
    )
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    principal_name = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Academic Information
    average_kcse_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='Average KCSE Score'
    )
    
    university_transition_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='University Transition Rate (%)'
    )
    
    # Facilities
    has_computer_lab = models.BooleanField(default=False)
    has_science_lab = models.BooleanField(default=False)
    has_library = models.BooleanField(default=False)
    has_internet = models.BooleanField(default=False)
    boarding_capacity = models.IntegerField(null=True, blank=True)
    day_scholar_capacity = models.IntegerField(null=True, blank=True)
    
    # Subjects Offered
    subjects_offered = models.ManyToManyField('recommendations.Subject', blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    established_year = models.IntegerField(null=True, blank=True)
    
    # Additional Details
    mission_statement = models.TextField(blank=True)
    vision_statement = models.TextField(blank=True)
    motto = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code}) - {self.county}"
    
    def get_school_type_display(self):
        return dict(self.SCHOOL_TYPE_CHOICES).get(self.type, self.type)
    
    def get_school_category_display(self):
        return dict(self.SCHOOL_CATEGORY_CHOICES).get(self.category, self.category)
    
    def get_full_address(self):
        address_parts = []
        if self.physical_address:
            address_parts.append(self.physical_address)
        if self.ward:
            address_parts.append(f"{self.ward} Ward")
        if self.constituency:
            address_parts.append(f"{self.constituency} Constituency")
        if self.sub_county:
            address_parts.append(f"{self.sub_county} Sub-County")
        address_parts.append(f"{self.county} County")
        return ", ".join(address_parts)
    
    def get_facilities(self):
        facilities = []
        if self.has_computer_lab:
            facilities.append('Computer Lab')
        if self.has_science_lab:
            facilities.append('Science Lab')
        if self.has_library:
            facilities.append('Library')
        if self.has_internet:
            facilities.append('Internet Access')
        return facilities
    
    def total_capacity(self):
        total = 0
        if self.boarding_capacity:
            total += self.boarding_capacity
        if self.day_scholar_capacity:
            total += self.day_scholar_capacity
        return total if total > 0 else None
    
    class Meta:
        ordering = ['name']
        verbose_name = 'School'
        verbose_name_plural = 'Schools'
        indexes = [
            models.Index(fields=['county']),
            models.Index(fields=['type']),
            models.Index(fields=['is_active']),
        ]