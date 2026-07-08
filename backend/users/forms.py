"""
users/forms.py — CareerCompass Kenya registration form.
Three roles: General User, Student, Admin.
Student fields (school, grade, subjects) only appear for 'student' role.
All academic fields are optional — the form is accessible to everyone.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, StudentProfile, School

IC = ("w-full px-4 py-3 border border-gray-300 rounded-xl "
      "focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition text-sm")
SC = ("w-full px-4 py-3 border border-gray-300 rounded-xl "
      "focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white transition text-sm")


class RoleRegistrationForm(UserCreationForm):
    ROLES = [
        ('user',    'General User — I want to explore careers'),
        ('student', 'Student — I am currently enrolled in school/university'),
    ]

    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': IC, 'placeholder': 'your.email@example.com', 'autocomplete': 'email'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': IC, 'placeholder': 'First name', 'autocomplete': 'given-name'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': IC, 'placeholder': 'Last name', 'autocomplete': 'family-name'}))
    role = forms.ChoiceField(choices=ROLES, widget=forms.Select(attrs={
        'class': SC, 'id': 'id_role', 'onchange': 'toggleStudentFields(this.value)'}))
    phone_number = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': IC, 'placeholder': '+254 700 000 000 (optional)'}))

    # ── Student-only optional fields ─────────────────────────────────────────
    grade_level = forms.ChoiceField(
        choices=[('', '-- Select current level --')] + StudentProfile.GRADE_LEVEL_CHOICES,
        required=False, widget=forms.Select(attrs={'class': SC}))
    school_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': IC, 'placeholder': 'School / University / College (optional)'}))
    kcse_score = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': IC, 'placeholder': 'KCSE grade e.g. A, B+, C (optional)'}))

    class Meta:
        model  = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name',
                  'phone_number', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = IC
        self.fields['username'].widget.attrs.update(
            {'class': IC, 'placeholder': 'Choose a username', 'autocomplete': 'username'})
        self.fields['password1'].widget.attrs.update(
            {'class': IC, 'placeholder': 'Create a strong password', 'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update(
            {'class': IC, 'placeholder': 'Confirm password', 'autocomplete': 'new-password'})

    def clean_username(self):
        u = self.cleaned_data.get('username', '').strip()
        if CustomUser.objects.filter(username=u).exists():
            raise forms.ValidationError('This username is already taken.')
        return u

    def clean_email(self):
        e = self.cleaned_data.get('email', '').strip().lower()
        if CustomUser.objects.filter(email__iexact=e).exists():
            raise forms.ValidationError('This email is already registered. Please log in.')
        return e

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email        = self.cleaned_data['email']
        user.first_name   = self.cleaned_data['first_name']
        user.last_name    = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.user_type    = self.cleaned_data.get('role', 'user')
        # Admin flag handled by signal; regular users do not get is_staff
        if commit:
            user.save()
        return user


EnhancedUserCreationForm = RoleRegistrationForm  # backward compat alias


class EnhancedAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': IC, 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': IC, 'placeholder': '••••••••'})


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model  = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number',
                  'county', 'sub_county', 'town', 'date_of_birth']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({'class': IC})
            f.required = False


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model  = StudentProfile
        fields = [
            'school', 'grade_level', 'academic_performance',
            'subjects', 'career_aspirations', 'kcpe_score', 'kcse_score',
            'extracurricular_activities', 'career_interests',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.required = False
            if hasattr(f.widget, 'attrs'):
                f.widget.attrs.update({'class': IC})


class AdminCreateUserForm(forms.ModelForm):
    """Admin-only form to create any user type including other admins."""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': IC}))

    class Meta:
        model  = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.update({'class': IC})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if user.user_type == 'admin':
            user.is_staff = True
        if commit:
            user.save()
        return user
