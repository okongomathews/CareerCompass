"""
users/views.py
This module defines all views related to user management, including:
- API endpoints for registration, login, logout, profile management, and school search.
- Template views for HTML rendering of registration, login, dashboard, profile, and help pages.
- Password reset flow with both email link and OTP-based options.
"""
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from django.views.generic import TemplateView, View
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.db import transaction
from django.http import JsonResponse
import json

from .forms import (
    RoleRegistrationForm, EnhancedAuthenticationForm,
    UserUpdateForm, StudentProfileForm,
)
from .models import CustomUser, StudentProfile, School
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    StudentProfileSerializer, SchoolSerializer,
)
from recommendations.models import StudentRecommendation, Subject
from ai_coach.models import Conversation


def _is_admin(user):
    return getattr(user, 'is_staff', False) or getattr(user, 'user_type', '') in ('admin',)


# ── API Views ─────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class   = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(
            {'user': UserSerializer(user, context=self.get_serializer_context()).data,
             'message': 'User created successfully'},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class   = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return Response({'user': UserSerializer(user).data, 'message': 'Login successful'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = UserSerializer

    def get_queryset(self):
        return CustomUser.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user


class StudentProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = StudentProfileSerializer

    def get_queryset(self):
        return StudentProfile.objects.filter(user=self.request.user)

    def get_object(self):
        return self.request.user.studentprofile


class SchoolViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SchoolSerializer
    queryset         = School.objects.all()

    @action(detail=False, methods=['get'])
    def search(self, request):
        query   = request.query_params.get('q', '')
        schools = School.objects.filter(name__icontains=query)[:10] if query \
                  else School.objects.all()[:10]
        return Response(self.get_serializer(schools, many=True).data)


# ── Template Views ────────────────────────────────────────────────────────────

class HTMLRegisterView(View):
    template_name = 'registration/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('analytics:admin_dashboard') if _is_admin(request.user) \
                   else redirect('dashboard')
        role = request.GET.get('role', '')
        form = RoleRegistrationForm(initial={'role': role} if role else {})
        return render(request, self.template_name, {'form': form, 'preselected_role': role})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')

        form = RoleRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    login(request, user)
                    name = user.first_name or user.username
                    role = user.user_type

                    if role == 'admin':
                        messages.success(
                            request,
                            f'Welcome, {name}! Your administrator account is ready. '
                            f'You can now access the Analytics Dashboard.')
                        return redirect('analytics:admin_dashboard')
                    elif role == 'student':
                        messages.success(
                            request,
                            f'Welcome to CareerCompass Kenya, {name}! '
                            f'Complete your profile then take the personality assessment.')
                        return redirect('profile')
                    elif role == 'teacher':
                        messages.success(request, f'Welcome, {name}! Your teacher account is ready.')
                        return redirect('dashboard')
                    elif role == 'parent':
                        messages.success(
                            request,
                            f'Welcome, {name}! Monitor your child\'s career journey from your dashboard.')
                        return redirect('dashboard')
                    elif role == 'school':
                        messages.success(
                            request,
                            f'Welcome, {name}! Your school administrator account is active.')
                        return redirect('dashboard')
                    else:
                        return redirect('dashboard')

            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}. Please try again.')

        return render(request, self.template_name, {'form': form})


class HTMLLoginView(View):
    template_name = 'registration/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('analytics:admin_dashboard') if _is_admin(request.user) \
                   else redirect('dashboard')
        return render(request, self.template_name, {'form': EnhancedAuthenticationForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')

        form = EnhancedAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            name = user.first_name or user.username

            if _is_admin(user):
                messages.success(request, f'Welcome back, Administrator {name}!')
                return redirect('analytics:admin_dashboard')

            next_url = request.POST.get('next') or request.GET.get('next') or ''
            messages.success(request, f'Welcome back, {name}!')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, self.template_name, {'form': form})


class HTMLLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been signed out successfully.')
        return redirect('login')

    def post(self, request):
        return self.get(request)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get(self, request, *args, **kwargs):
        # Admin users have their own dedicated dashboard — redirect immediately
        if _is_admin(request.user):
            return redirect('analytics:admin_dashboard')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user    = self.request.user

        # Ensure student profile exists
        try:
            profile = user.studentprofile
        except StudentProfile.DoesNotExist:
            profile = StudentProfile.objects.create(user=user)
        context['profile'] = profile

        # Assessment result + pole percentages
        assessment_result = None
        pole_percentages  = None
        try:
            from assessments.models import AssessmentResult
            assessment_result = (
                AssessmentResult.objects
                .select_related('personality_type')
                .get(student=profile)
            )
            pole_percentages = assessment_result.get_pole_percentages()
        except Exception:
            pass
        context['assessment_result'] = assessment_result
        context['pole_percentages']  = pole_percentages

        # Top 5 career recommendations
        try:
            recs = (
                StudentRecommendation.objects
                .filter(student=profile)
                .select_related('career')
                .order_by('-overall_score')[:5]
            )
            context['recommendations'] = recs
        except Exception:
            context['recommendations'] = []

        # Learning style
        try:
            from ai_coach.models import CoachingPlan
            cp = CoachingPlan.objects.get(student=profile)
            context['learning_style'] = cp.learning_style
        except Exception:
            context['learning_style'] = None

        # Profile completion
        try:
            profile.calculate_profile_completion()
            context['profile_completion'] = profile.profile_completion
        except Exception:
            context['profile_completion'] = 0

        # Dynamic question count — reads from DB so it's always accurate
        try:
            from assessments.models import Question
            context['question_count'] = Question.objects.count()
        except Exception:
            context['question_count'] = 92   # fallback if DB not ready

        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/profile.html'

    def get(self, request, *args, **kwargs):
        if _is_admin(request.user):
            return redirect('analytics:admin_dashboard')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            profile = user.studentprofile
        except StudentProfile.DoesNotExist:
            profile = StudentProfile.objects.create(user=user)

        try:
            profile.calculate_profile_completion()
        except Exception:
            pass

        context['profile']       = profile
        context['user_form']     = UserUpdateForm(instance=user)
        context['profile_form']  = StudentProfileForm(instance=profile)
        context['subjects']      = Subject.objects.all().order_by('name')
        context['schools']       = School.objects.filter(is_active=True).order_by('name')[:50]

        # Tabs for the profile page (id, label, icon)
        context['tabs'] = [
            ('personal',     'Personal',     'fas fa-user'),
            ('academic',     'Academic',     'fas fa-graduation-cap'),
            ('preferences',  'Preferences',  'fas fa-sliders'),
        ]

        # Study preference checkbox fields (field_name, display_label)
        context['study_prefs'] = [
            ('prefers_group_study',       'Prefers Group Study'),
            ('prefers_individual_study',  'Prefers Individual Study'),
            ('learns_best_morning',       'Most Productive in Morning'),
            ('learns_best_afternoon',     'Most Productive in Afternoon'),
            ('learns_best_evening',       'Most Productive in Evening'),
            ('prefers_visual_learning',   'Prefers Visual Learning'),
            ('prefers_auditory_learning', 'Prefers Auditory Learning'),
            ('prefers_reading_writing',   'Prefers Reading / Writing'),
            ('prefers_hands_on',          'Prefers Hands-On / Practical'),
        ]
        return context


class UpdateProfileView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        try:
            profile = user.studentprofile
        except StudentProfile.DoesNotExist:
            profile = StudentProfile.objects.create(user=user)

        user_form    = UserUpdateForm(request.POST, instance=user)
        profile_form = StudentProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
        else:
            all_errors = {**user_form.errors, **profile_form.errors}
            for field, errs in all_errors.items():
                for err in errs:
                    messages.error(request, f'{field}: {err}')
        return redirect('profile')


# ── Password Reset ────────────────────────────────────────────────────────────

class CustomPasswordResetView(PasswordResetView):
    template_name             = 'registration/password_reset.html'
    email_template_name       = 'registration/password_reset_email.html'
    html_email_template_name  = 'emails/password_reset_html.html'
    subject_template_name     = 'registration/password_reset_subject.txt'
    success_url               = reverse_lazy('password_reset_done')

    def get_extra_email_context(self):
        from django.conf import settings
        return {'site_name': getattr(settings, 'SITE_NAME', 'CareerCompass Kenya')}


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url   = reverse_lazy('password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_done.html'


# ── AJAX availability checks ──────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def check_username_api(request):
    username  = request.data.get('username', '').strip()
    if not username or len(username) < 3:
        return Response({'available': False, 'message': 'Too short (min 3 chars)'})
    available = not CustomUser.objects.filter(username=username).exists()
    return Response({'available': available,
                     'message': 'Available ✓' if available else 'Username already taken'})


@api_view(['POST'])
@permission_classes([AllowAny])
def check_email_api(request):
    email = request.data.get('email', '').strip().lower()
    if not email or '@' not in email:
        return Response({'available': False, 'message': 'Invalid email'})
    available = not CustomUser.objects.filter(email__iexact=email).exists()
    return Response({'available': available,
                     'message': 'Available ✓' if available else 'Email already registered'})


class OTPPasswordResetView(View):
    """
    OTP-based password reset — step 1: user enters email, OTP is sent.
    Uses Django's built-in email (console in dev, SMTP in production).
    """
    template_name = 'registration/otp_reset_request.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        import time
        from django.contrib.auth import get_user_model
        from users.signals import send_otp_email

        email = request.POST.get('email', '').strip().lower()
        User  = get_user_model()

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            otp  = send_otp_email(user, purpose='password_reset')
            # otp is always returned (send_mail uses fail_silently=True)
            request.session['otp_code']    = otp
            request.session['otp_user_id'] = user.id
            request.session['otp_expiry']  = time.time() + 600  # 10 minutes
        except User.DoesNotExist:
            # Do NOT reveal whether the email exists — same UX for both cases
            pass

        # Always redirect regardless of whether email exists (prevents user enumeration)
        masked = f"{email[:3]}***{email[email.find('@'):]}" if '@' in email else email
        messages.success(
            request,
            f"If {masked} is registered, a 6-digit code has been sent. "
            f"Check your inbox (and spam folder)."
        )
        return redirect('otp_reset_verify')


class OTPPasswordResetVerifyView(View):
    """Step 2: user enters the OTP received by email."""
    template_name = 'registration/otp_reset_verify.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        import time
        code     = request.POST.get('otp', '').strip()
        stored   = request.session.get('otp_code', '')
        user_id  = request.session.get('otp_user_id')
        expiry   = request.session.get('otp_expiry', 0)

        if not stored or not user_id:
            messages.error(request, 'Session expired. Please request a new code.')
            return redirect('otp_reset_request')
        if time.time() > expiry:
            messages.error(request, 'Code expired. Please request a new one.')
            return redirect('otp_reset_request')
        if code != stored:
            messages.error(request, 'Incorrect code. Please try again.')
            return render(request, self.template_name)

        # Mark OTP as verified — allow setting new password
        request.session['otp_verified'] = True
        return redirect('otp_reset_password')


class OTPPasswordResetSetView(View):
    """Step 3: user sets new password after OTP is verified."""
    template_name = 'registration/otp_reset_password.html'

    def get(self, request):
        if not request.session.get('otp_verified'):
            return redirect('otp_reset_request')
        return render(request, self.template_name)

    def post(self, request):
        if not request.session.get('otp_verified'):
            return redirect('otp_reset_request')
        p1 = request.POST.get('password1', '')
        p2 = request.POST.get('password2', '')
        if p1 != p2:
            messages.error(request, 'Passwords do not match.')
            return render(request, self.template_name)
        if len(p1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, self.template_name)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=request.session['otp_user_id'])
            user.set_password(p1)
            user.save()
            # Clean up session
            for key in ['otp_code','otp_user_id','otp_expiry','otp_verified']:
                request.session.pop(key, None)
            messages.success(request, 'Password changed successfully! Please log in.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'User not found. Please start again.')
            return redirect('otp_reset_request')


class LandingPageView(TemplateView):
    """
    Public marketing/explainer landing page, served at site root ('/').

    Standalone template (does not extend base.html) — it ships its own
    self-contained CSS/JS/icons so it has zero dependency on the Tailwind
    runtime compiler or FontAwesome that the authenticated app loads.

    Authenticated visitors are sent straight to their dashboard rather than
    being shown the pitch for a product they already have an account on.
    """
    template_name = 'landing.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)


class HelpFAQView(LoginRequiredMixin, TemplateView):
    """
    Help Centre & FAQ page.
    Renders a static template — no database queries needed.
    The quick_steps context variable drives the Quick Start sidebar widget.
    """
    template_name = 'dashboard/help.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['quick_steps'] = [
            (1, 'Create an account',       "fa-user-plus"),
            (2, 'Complete your profile',   "fa-id-card"),
            (3, 'Take the Personality Test',"fa-brain"),
            (4, 'Explore career matches',"fa-compass"),
            (5, 'Chat with the AI Coach', "fa-robot"),
        ]
        return ctx