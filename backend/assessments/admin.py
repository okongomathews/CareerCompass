from django.contrib import admin
from .models import (
    MBTIDimension, Question, AnswerChoice, 
    AssessmentSession, QuestionResponse, 
    PersonalityType, AssessmentResult
)

class AnswerChoiceInline(admin.TabularInline):
    model = AnswerChoice
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'category', 'dimension_a_weight', 'dimension_b_weight')
    list_filter = ('category',)
    search_fields = ('text',)
    inlines = [AnswerChoiceInline]
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question Text'

class QuestionResponseInline(admin.TabularInline):
    model = QuestionResponse
    extra = 0
    readonly_fields = ('question', 'answer', 'response_time')

class AssessmentSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'started_at', 'completed_at', 'is_completed')
    list_filter = ('is_completed', 'started_at')
    search_fields = ('student__user__username', 'student__user__email')
    inlines = [QuestionResponseInline]

class PersonalityTypeAdmin(admin.ModelAdmin):
    list_display = ('mbti_type', 'name')
    search_fields = ('mbti_type', 'name')

class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'personality_type', 'confidence', 'created_at')
    list_filter = ('personality_type', 'created_at')
    search_fields = ('student__user__username', 'student__user__email')

admin.site.register(MBTIDimension)
admin.site.register(Question, QuestionAdmin)
admin.site.register(AssessmentSession, AssessmentSessionAdmin)
admin.site.register(PersonalityType, PersonalityTypeAdmin)
admin.site.register(AssessmentResult, AssessmentResultAdmin)