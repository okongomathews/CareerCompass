from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, StudentProfile, School


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'email', 'full_name', 'user_type', 'is_staff', 'is_active', 'date_joined')
    list_filter   = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering      = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')}),
        ('Role', {
            'fields': ('user_type',),
            'description': (
                '<strong>Note:</strong> Setting User Type to <em>Admin</em> '
                'automatically grants Staff access to the Django admin panel.'
            ),
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name',
                       'user_type', 'password1', 'password2'),
        }),
    )

    def full_name(self, obj):
        name = obj.get_full_name()
        return name if name.strip() else '—'
    full_name.short_description = 'Full Name'

    def save_model(self, request, obj, form, change):
        """Ensure is_staff is always synced with user_type when saving via admin."""
        if obj.user_type == 'admin':
            obj.is_staff = True
        super().save_model(request, obj, form, change)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'full_name', 'school', 'grade_level', 'has_assessment', 'created_at')
    list_filter   = ('grade_level', 'school__county', 'school')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'school__name')
    filter_horizontal = ('subjects',)
    raw_id_fields = ('user',)
    ordering      = ('-created_at',)

    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Name'

    def has_assessment(self, obj):
        has = hasattr(obj, 'assessmentresult') and obj.assessmentresult is not None
        icon = '✅' if has else '❌'
        return format_html('<span title="{}">{}</span>',
                           'Completed' if has else 'Not yet taken', icon)
    has_assessment.short_description = 'Assessment'


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display  = ('name', 'code', 'county', 'type', 'is_active', 'student_count')
    list_filter   = ('type', 'county', 'is_active')
    search_fields = ('name', 'code', 'county')
    ordering      = ('name',)

    def student_count(self, obj):
        return obj.studentprofile_set.count()
    student_count.short_description = '# Students'
