from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'careers', views.CareerViewSet, basename='career')
router.register(r'subjects', views.SubjectViewSet, basename='subject')
router.register(r'recommendations', views.StudentRecommendationViewSet, basename='studentrecommendation')
router.register(r'learning-styles', views.LearningStyleViewSet, basename='learningstyle')
router.register(r'career-matches', views.CareerPersonalityMatchViewSet, basename='careerpersonalitymatch')
router.register(r'career-learning-styles', views.CareerLearningStyleViewSet, basename='careerlearningstyle')
router.register(r'analytics', views.RecommendationAnalyticsViewSet, basename='recommendationanalytics')

app_name = 'recommendations'

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    
    # Enhanced API endpoints - ONLY KEEP EXISTING ONES
    path('api/compare-careers/', views.compare_careers, name='compare_careers'),
    path('api/career/<int:career_id>/compatibility/', views.career_compatibility_score, name='career_compatibility'),
    path('api/subjects/recommended/', views.recommended_subjects, name='recommended_subjects'),
    path('api/recommendations/analytics/', views.recommendation_analytics, name='recommendation_analytics'),
    path('api/recommendations/regenerate/', views.regenerate_recommendations, name='regenerate_recommendations'),
    path('api/recommendations/track-interest/<int:career_id>/', views.track_career_interest, name='track_career_interest'),
    path('api/careers/market-stats/', views.career_market_stats, name='career_market_stats'),
    path('api/careers/filter-options/', views.career_filter_options, name='career_filter_options'),
    
    # Template URLs
    path('', views.CareerRecommendationsView.as_view(), name='my_recommendations'),
    path('careers/', views.CareerListView.as_view(), name='career_list'),
    path('careers/<int:pk>/', views.CareerDetailView.as_view(), name='career_detail'),
    path('careers/compare/', views.CareerComparisonView.as_view(), name='career_comparison'),
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subject-recommendations/', views.SubjectRecommendationForCampusView.as_view(), name='subject_recommendations'),
    path('analytics/dashboard/', views.RecommendationAnalyticsDashboard.as_view(), name='analytics_dashboard'),
    
    # Public URLs (no authentication required)
    path('public/careers/', views.PublicCareerListView.as_view(), name='public_career_list'),
    path('public/careers/<int:pk>/', views.PublicCareerDetailView.as_view(), name='public_career_detail'),
    path('public/market-trends/', views.MarketTrendsView.as_view(), name='market_trends'),
    
    # ML & Analytics endpoints
    path('api/ml/recommendations/', views.ml_enhanced_recommendations, name='ml_recommendations'),
    path('api/ml/analytics/', views.ml_analytics, name='ml_analytics'),
    path('api/ml/adaptive-assessment/', views.adaptive_assessment, name='adaptive_assessment'),
    path('api/ml/train/', views.train_ml_models, name='train_ml_models'),
]