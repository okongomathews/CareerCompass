from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'coaching-plans', views.CoachingPlanViewSet, basename='coachingplan')

app_name = 'ai_coach'

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Template URLs
    path('', views.AICoachChatView.as_view(), name='chat'),
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<int:conversation_id>/', views.AICoachChatView.as_view(), name='conversation_detail'),
    path('coaching-plan/', views.CoachingPlanView.as_view(), name='coaching_plan'),
    path('resources/', views.LearningResourcesView.as_view(), name='learning_resources'),
    
    # API endpoints for templates
    path('api/send-message/', views.AICoachAPIView.as_view(), name='send_message'),
    path('api/send-message/<int:conversation_id>/', views.AICoachAPIView.as_view(), name='send_message_conversation'),
    path('api/update-goals/', views.UpdateGoalsView.as_view(), name='update_goals'),
]