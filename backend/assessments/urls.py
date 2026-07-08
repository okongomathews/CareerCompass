from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'assessments'

router = DefaultRouter()
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'sessions', views.AssessmentSessionViewSet, basename='assessments-session')
router.register(r'results', views.AssessmentResultViewSet, basename='assessments-result')
router.register(r'personality-types', views.PersonalityTypeViewSet, basename='personality-type')

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Template URLs
    path('start/', views.AssessmentStartView.as_view(), name='assessments-start'),
    path('question/', views.AssessmentQuestionView.as_view(), name='assessments-question'),
    path('results/', views.AssessmentResultsView.as_view(), name='assessments-results'),
    
    # API functions
    path('api/submit_bulk_responses/', views.submit_bulk_responses, name='submit-bulk-responses'),
    path('api/get_next_question/<int:session_id>/', views.get_next_question, name='get-next-question'),
]