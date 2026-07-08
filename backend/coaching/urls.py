# career_compass/coaching/urls.py
from django.urls import path
from . import views

app_name = 'coaching'

urlpatterns = [
    path('dashboard/', views.coaching_dashboard, name='coaching_dashboard'),
    path('plans/', views.plan_selection, name='plan_selection'),
    path('plans/subscribe/<int:plan_id>/', views.subscribe_to_plan, name='subscribe_to_plan'),
    path('ai-chat/', views.ai_coaching_chat, name='ai_coaching_chat'),
    path('ai-message/', views.ai_coaching_message, name='ai_coaching_message'),
    path('book-session/', views.book_human_session, name='book_human_session'),
    path('career-goals/', views.career_goals, name='career_goals'),
    path('career-assessment/', views.career_assessment, name='career_assessment'),
    path('learning-path/', views.generate_learning_path, name='generate_learning_path'),
]