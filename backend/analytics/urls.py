from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/',                        views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('reports/students/',                 views.student_report_list,          name='student_report_list'),
    path('reports/career/<int:student_id>/',  views.generate_career_report_pdf,   name='career_report_pdf'),
    path('reports/assessment/',               views.assessment_report,            name='assessment_report'),
    path('api/stats/',                        views.analytics_api,                name='analytics_api'),
    path('admin/approve/<int:admin_id>/',     views.approve_admin,                name='approve_admin'),
    path('admin/revoke/<int:admin_id>/',      views.revoke_admin,                 name='revoke_admin'),
]
