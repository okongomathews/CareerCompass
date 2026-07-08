from django.contrib import admin
from .models import Career, Subject, StudentRecommendation, LearningStyle, CareerPersonalityMatch

class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 0

class RequiredSubjectsInline(admin.TabularInline):
    model = Career.required_subjects.through
    extra = 1
    verbose_name = "Required Subject"
    verbose_name_plural = "Required Subjects"

class RecommendedSubjectsInline(admin.TabularInline):
    model = Career.recommended_subjects.through
    extra = 1
    verbose_name = "Recommended Subject"
    verbose_name_plural = "Recommended Subjects"

class CareerAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'kenyan_market_demand', 'average_salary')
    list_filter = ('category', 'kenyan_market_demand', 'market_demand_trend')  # Changed 'job_outlook' to 'market_demand_trend'
    search_fields = ('name', 'description')
    inlines = [RequiredSubjectsInline, RecommendedSubjectsInline]
    exclude = ('required_subjects', 'recommended_subjects')

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'difficulty_level')
    list_filter = ('category', 'difficulty_level')
    search_fields = ('name', 'code')

class StudentRecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'career', 'overall_score', 'created_at')
    list_filter = ('created_at', 'career__category')
    search_fields = ('student__user__username', 'career__name')
    readonly_fields = ('created_at',)

class LearningStyleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

class CareerPersonalityMatchAdmin(admin.ModelAdmin):
    list_display = ('career', 'personality_type', 'match_score')  # Changed 'compatibility_score' to 'match_score'
    list_filter = ('personality_type',)
    search_fields = ('career__name', 'personality_type__mbti_type')

admin.site.register(Career, CareerAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(StudentRecommendation, StudentRecommendationAdmin)
admin.site.register(LearningStyle, LearningStyleAdmin)
admin.site.register(CareerPersonalityMatch, CareerPersonalityMatchAdmin)