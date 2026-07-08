# career_compass/coaching/admin.py
from django.contrib import admin
from .models import (
    CoachingPlan, UserCoachingSubscription, CoachingSession,
    CareerGoal, ActionItem, ResourceRecommendation
)

@admin.register(CoachingPlan)
class CoachingPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price_kes', 'duration', 'is_active']
    list_filter = ['plan_type', 'is_active', 'duration']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'price_kes']

@admin.register(UserCoachingSubscription)
class UserCoachingSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'is_active']
    list_filter = ['status', 'plan', 'auto_renew']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['stripe_subscription_id']

@admin.register(CoachingSession)
class CoachingSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_type', 'title', 'status', 'scheduled_time']
    list_filter = ['session_type', 'status', 'coach']
    search_fields = ['user__email', 'title', 'description']
    date_hierarchy = 'scheduled_time'

@admin.register(CareerGoal)
class CareerGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'goal_type', 'status', 'progress_percentage', 'target_date']
    list_filter = ['goal_type', 'status', 'priority']
    search_fields = ['user__email', 'title', 'description']

@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'coaching_session', 'priority', 'due_date', 'completed']
    list_filter = ['priority', 'completed']
    search_fields = ['title', 'description']

@admin.register(ResourceRecommendation)
class ResourceRecommendationAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'coaching_session', 'is_free', 'is_local']
    list_filter = ['resource_type', 'is_free', 'is_local']
    search_fields = ['title', 'description', 'url']