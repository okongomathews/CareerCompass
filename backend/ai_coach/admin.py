from django.contrib import admin
from .models import Conversation, Message, CoachingPlan, ResourceRecommendation

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('timestamp',)
    fields = ('content', 'is_from_ai', 'timestamp')

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'student__user__username')
    inlines = [MessageInline]
    readonly_fields = ('created_at', 'updated_at')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'content_preview', 'is_from_ai', 'timestamp')
    list_filter = ('is_from_ai', 'timestamp')
    search_fields = ('content', 'conversation__title')
    readonly_fields = ('timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Message'

class ResourceRecommendationInline(admin.TabularInline):
    model = ResourceRecommendation
    extra = 0

class CoachingPlanAdmin(admin.ModelAdmin):
    list_display = ('student', 'personality_type', 'learning_style', 'created_at')
    list_filter = ('created_at', 'personality_type', 'learning_style')
    search_fields = ('student__user__username',)
    inlines = [ResourceRecommendationInline]
    readonly_fields = ('created_at', 'updated_at')

class ResourceRecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'coaching_plan', 'resource_type', 'relevance_score')
    list_filter = ('resource_type', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(CoachingPlan, CoachingPlanAdmin)
admin.site.register(ResourceRecommendation, ResourceRecommendationAdmin)