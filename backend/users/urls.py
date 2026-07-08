from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'student-profiles', views.StudentProfileViewSet, basename='studentprofile')
router.register(r'schools', views.SchoolViewSet, basename='school')

urlpatterns = [
    # API URLs (for programmatic access)
    path('api/', include(router.urls)),
    path('api/register/', views.RegisterView.as_view(), name='api-register'),
    path('api/login/', views.LoginView.as_view(), name='api-login'),
    path('api/logout/', views.LogoutView.as_view(), name='api-logout'),
    path('api/check-username/', views.check_username_api, name='check_username_api'),
    path('api/check-email/', views.check_email_api, name='check_email_api'),
    
    # HTML Template URLs (for browser access)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('login/', views.HTMLLoginView.as_view(), name='login'),
    path('register/', views.HTMLRegisterView.as_view(), name='register'),
    path('logout/', views.HTMLLogoutView.as_view(), name='logout'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
    
    # Help & FAQ
    path('help/', views.HelpFAQView.as_view(), name='help_faq'),

    # Password Reset URLs
    # OTP-based password reset (recommended over link-based for Kenya mobile users)
    path('otp-reset/', views.OTPPasswordResetView.as_view(), name='otp_reset_request'),
    path('otp-reset/verify/', views.OTPPasswordResetVerifyView.as_view(), name='otp_reset_verify'),
    path('otp-reset/password/', views.OTPPasswordResetSetView.as_view(), name='otp_reset_password'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]