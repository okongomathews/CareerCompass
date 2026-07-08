"""
analytics/views.py

Auth: replaced @staff_member_required with a custom decorator that accepts
BOTH is_staff=True (Django convention) AND user_type='admin' (our convention).
This prevents the 403/redirect loop that admin users (who may not have
is_staff=True set on old accounts) were experiencing.
"""
import json
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Count, Avg
from django.db.models.functions import TruncMonth

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from users.models import CustomUser, StudentProfile
from assessments.models import AssessmentResult, PersonalityType
from recommendations.models import Career, StudentRecommendation
from ai_coach.models import Conversation, Message


# ── Custom admin-check decorator ──────────────────────────────────────────────
def admin_required(view_func):
    """
    Allows access if the user is authenticated AND is either:
      • is_staff = True  (Django staff / superuser)
      • user_type = 'admin' (our custom role)
    Falls back to a user-friendly redirect with an error message instead of
    the generic Django /admin/login/ page.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/users/login/?next={request.path}')
        if request.user.is_staff or getattr(request.user, 'user_type', '') == 'admin':
            return view_func(request, *args, **kwargs)
        messages.error(request, 'You need administrator privileges to access this page.')
        return redirect('dashboard')
    return _wrapped


def admin_required_cbv(cls):
    """Class-based-view version of admin_required."""
    cls.dispatch = method_decorator(admin_required)(cls.dispatch)
    return cls


# ── Helpers ───────────────────────────────────────────────────────────────────
def _safe_float(val, multiplier=1):
    """Convert possibly-None decimal to rounded float."""
    try:
        return round(float(val) * multiplier, 1) if val is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


# ── Views ─────────────────────────────────────────────────────────────────────

@admin_required_cbv
class AdminDashboardView(TemplateView):
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ── KPI counts ────────────────────────────────────────────────────────
        # total_users counts ALL registered accounts (matches the Recent Registrations table below)
        ctx['total_users']         = CustomUser.objects.count()
        ctx['total_students']      = CustomUser.objects.filter(user_type='student').count()
        ctx['total_general_users'] = CustomUser.objects.filter(user_type='user').count()
        # AssessmentResult is OneToOne per StudentProfile — count() directly = distinct students assessed
        ctx['active_assessments']  = AssessmentResult.objects.count()
        ctx['total_careers']       = Career.objects.count()

        # ── Personality distribution ──────────────────────────────────────────
        personality_counts = list(
            AssessmentResult.objects.values('personality_type__mbti_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        ctx['personality_counts'] = json.dumps(personality_counts)

        # ── Average compatibility scores (stored as 0-1 floats) ───────────────
        agg = StudentRecommendation.objects.aggregate(
            avg_personality=Avg('personality_match_score'),
            avg_academic=Avg('academic_match_score'),
            avg_market=Avg('market_demand_score'),
            avg_overall=Avg('overall_score'),
        )
        # Convert to percentages for direct use in JS/template
        ctx['avg_scores'] = {
            'avg_personality': _safe_float(agg['avg_personality'], 100),
            'avg_academic':    _safe_float(agg['avg_academic'],    100),
            'avg_market':      _safe_float(agg['avg_market'],      100),
            'avg_overall':     _safe_float(agg['avg_overall'],     100),
        }

        # ── Monthly user growth — last 12 months with zero-fill ──────────────
        from datetime import date, timedelta
        import calendar
        today  = date.today()
        # Build list of 12 month labels (YYYY-MM) oldest→newest
        months_12 = []
        y, m = today.year, today.month
        for _ in range(12):
            months_12.insert(0, f"{y:04d}-{m:02d}")
            m -= 1
            if m == 0:
                m = 12; y -= 1

        monthly_raw = {}
        for r in (CustomUser.objects
                  .annotate(month=TruncMonth('date_joined'))
                  .values('month')
                  .annotate(count=Count('id'))):
            if r['month']:
                key = r['month'].strftime('%Y-%m')
                monthly_raw[key] = r['count']

        monthly_users = [{'month': mo, 'count': monthly_raw.get(mo, 0)} for mo in months_12]
        ctx['monthly_users'] = json.dumps(monthly_users)

        # ── Top recommended careers (with category for filter) ────────────────
        top_raw = list(
            StudentRecommendation.objects
            .values('career__name', 'career__category')
            .annotate(count=Count('id'))
            .order_by('-count')[:20]
        )
        ctx['top_careers'] = top_raw  # for template {% for %} loop

        top_full = [
            {
                'name':     r['career__name'] or '',
                'category': r['career__category'] or '',
                'area':     r['career__category'] or 'Uncategorised',
                'count':    r['count'],
            }
            for r in top_raw
        ]
        ctx['top_careers_full'] = json.dumps(top_full)

        # ── Recommendations by career area — deduplicated & normalised ────────
        # The DB may hold either the lowercase choice key (e.g. 'technology') or a
        # Title-Case freetext value (e.g. 'Technology') depending on how data was
        # loaded.  We normalise everything to lowercase before merging so the bar
        # chart never shows two bars for the same field.
        _CATEGORY_DISPLAY = {
            'technology': 'Technology', 'health': 'Health', 'healthcare': 'Health',
            'business': 'Business', 'engineering': 'Engineering',
            'agriculture': 'Agriculture', 'education': 'Education',
            'media': 'Media', 'law': 'Law', 'tourism': 'Tourism',
            'stem': 'STEM', 'arts': 'Arts & Humanities',
            'technical': 'Technical & Vocational', 'research': 'Research',
            'public_service': 'Public Service',
            # Free-text values used by populate_careers.py
            'construction': 'Construction', 'environment': 'Environment',
            'finance': 'Finance', 'hospitality': 'Hospitality',
            'mathematics': 'Mathematics', 'ngo': 'NGO / Non-profit',
            'science': 'Science', 'security': 'Security',
            'social sciences': 'Social Sciences', 'sports': 'Sports',
            'transport': 'Transport', 'creative arts': 'Creative Arts',
        }

        area_raw = list(
            StudentRecommendation.objects
            .values('career__category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        area_merged = {}
        for r in area_raw:
            raw = (r['career__category'] or '').strip()
            # Normalise: lowercase key → canonical display label
            key = raw.lower()
            label = _CATEGORY_DISPLAY.get(key, raw.title() if raw else 'Uncategorised')
            area_merged[label] = area_merged.get(label, 0) + r['count']

        area_scores = [
            {'area': label, 'count': cnt}
            for label, cnt in sorted(area_merged.items(), key=lambda x: -x[1])
            if label
        ]
        ctx['area_scores']  = json.dumps(area_scores)
        ctx['career_areas'] = sorted({
            a['area'] for a in area_scores if a['area'] != 'Uncategorised'
        })

        # ── AI engagement ─────────────────────────────────────────────────────
        total_msgs  = Message.objects.count()
        with_chats  = Conversation.objects.values('student').distinct().count()
        ctx['avg_messages_per_student'] = round(total_msgs / with_chats, 1) if with_chats else 0

        # Pre-built KPI cards for the template loop
        ctx['kpi_cards'] = [
            ('Total Users',       ctx['total_users'],         '#3b82f6', 'fas fa-users'),
            ('Students',          ctx['total_students'],      '#10b981', 'fas fa-user-graduate'),
            ('Assessments Done',  ctx['active_assessments'],  '#8b5cf6', 'fas fa-brain'),
            ('Careers in DB',     ctx['total_careers'],       '#f59e0b', 'fas fa-briefcase'),
        ]
        # ── Market demand distribution ─────────────────────────────────────
        demand_raw = list(
            Career.objects.values('kenyan_market_demand').annotate(count=Count('id')).order_by('-count')
        )
        ctx['demand_data'] = json.dumps(demand_raw)

        # ── Recent registrations — all roles, including legacy ones ──────────
        ctx['recent_users'] = (
            CustomUser.objects
            .order_by('-date_joined')
            .values('username', 'user_type', 'date_joined', 'first_name', 'last_name')[:10]
        )

        # ── Admin management ──────────────────────────────────────────────────
        # All admin users — show their superuser status so current superadmin can see who can access /admin/
        ctx['admin_users'] = CustomUser.objects.filter(
            user_type='admin'
        ).order_by('-is_superuser', '-date_joined').values(
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_staff', 'is_superuser', 'is_active', 'date_joined'
        )
        # Pending admin accounts: is_staff but NOT is_superuser (can't access /admin/ content yet)
        ctx['pending_admins'] = CustomUser.objects.filter(
            user_type='admin', is_superuser=False
        ).values('id', 'username', 'first_name', 'last_name', 'email', 'date_joined')

        return ctx


@admin_required
def analytics_api(request):
    from django.http import JsonResponse
    data = {
        'personality_distribution': list(
            AssessmentResult.objects
            .values('personality_type__mbti_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
        'recommendation_scores': list(
            StudentRecommendation.objects
            .values('career__category')
            .annotate(avg_score=Avg('overall_score'))
            .order_by('-avg_score')[:8]
        ),
        'market_demand': list(
            Career.objects
            .values('kenyan_market_demand')
            .annotate(count=Count('id'))
            .order_by('-count')
        ),
    }
    return JsonResponse(data)


@admin_required
def approve_admin(request, admin_id):
    """
    Grant superuser (full Django admin panel) access to a staff admin user.
    Only existing superusers can call this endpoint.
    """
    from django.contrib import messages
    from django.shortcuts import redirect
    if not request.user.is_superuser:
        messages.error(request, 'Only a superuser admin can approve other administrators.')
        return redirect('analytics:admin_dashboard')
    if request.method == 'POST':
        target = get_object_or_404(CustomUser, id=admin_id, user_type='admin')
        target.is_superuser = True
        target.is_staff     = True
        target.save(update_fields=['is_superuser', 'is_staff'])
        messages.success(
            request,
            f'{target.get_full_name() or target.username} has been granted full admin access.'
        )
    return redirect('analytics:admin_dashboard')


@admin_required
def revoke_admin(request, admin_id):
    """Revoke superuser status from an admin (keeps is_staff so they can still log in to /admin/)."""
    from django.contrib import messages
    from django.shortcuts import redirect
    if not request.user.is_superuser:
        messages.error(request, 'Only a superuser admin can revoke administrator access.')
        return redirect('analytics:admin_dashboard')
    if request.method == 'POST':
        target = get_object_or_404(CustomUser, id=admin_id, user_type='admin')
        if target == request.user:
            messages.error(request, 'You cannot revoke your own superuser access.')
            return redirect('analytics:admin_dashboard')
        target.is_superuser = False
        target.save(update_fields=['is_superuser'])
        messages.success(
            request,
            f'{target.get_full_name() or target.username} superuser access revoked.'
        )
    return redirect('analytics:admin_dashboard')


@admin_required
def generate_career_report_pdf(request, student_id):
    """Generate a polished A4 PDF career report for a specific student."""
    student = get_object_or_404(StudentProfile, id=student_id)
    recs    = (
        StudentRecommendation.objects
        .filter(student=student)
        .select_related('career')
        .order_by('-overall_score')[:10]
    )

    response = HttpResponse(content_type='application/pdf')
    fname    = f"career_report_{student.user.username}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{fname}"'

    doc    = SimpleDocTemplate(response, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Styles ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=22, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1E3A8A'),
        alignment=TA_CENTER, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#6B7280'),
        alignment=TA_CENTER, spaceAfter=14,
    )
    section_style = ParagraphStyle(
        'SectionHead', parent=styles['Heading2'],
        fontSize=13, fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=14, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, leading=14,
    )

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph('CareerCompass Kenya', title_style))
    story.append(Paragraph('Personalised Career Report', subtitle_style))
    story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#1E3A8A')))
    story.append(Spacer(1, 10))

    full_name = student.user.get_full_name() or student.user.username
    story.append(Paragraph(f'<b>Student:</b> {full_name}', body_style))
    story.append(Paragraph(f'<b>Username:</b> {student.user.username}', body_style))
    if student.school:
        story.append(Paragraph(f'<b>School:</b> {student.school.name}', body_style))
    if student.grade_level:
        story.append(Paragraph(
            f'<b>Grade Level:</b> {student.get_grade_level_display()}', body_style))

    # ── Personality type ──────────────────────────────────────────────────────
    try:
        ar = student.assessmentresult
        story.append(Spacer(1, 10))
        story.append(Paragraph('Personality Profile', section_style))

        pp = ar.get_pole_percentages()
        type_data = [['Dimension', 'A Pole', 'Strength', 'B Pole', 'Strength']]
        for code, dim in pp.items():
            a_pct = f"{dim['a_pct']}%"
            b_pct = f"{dim['b_pct']}%"
            type_data.append([
                f"{dim['a_label']} / {dim['b_label']}",
                dim['a_letter'], a_pct,
                dim['b_letter'], b_pct,
            ])

        type_table = Table(type_data,
                           colWidths=[5*cm, 1.5*cm, 2.5*cm, 1.5*cm, 2.5*cm])
        type_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#EFF6FF')]),
            ('GRID',          (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(Paragraph(
            f'<b>Type:</b> {ar.personality_type.mbti_type} — {ar.personality_type.name}  '
            f'| Confidence: {ar.get_confidence_percent()}%',
            body_style))
        story.append(Spacer(1, 6))
        story.append(type_table)
    except Exception:
        story.append(Paragraph(
            'No personality assessment completed yet.', body_style))

    # ── Career recommendations table ──────────────────────────────────────────
    story.append(Spacer(1, 12))
    story.append(Paragraph('Top Career Recommendations', section_style))

    if recs:
        tdata = [['Career', 'Field', 'Overall', 'Personality', 'Academic', 'Market Demand']]
        for rec in recs:
            tdata.append([
                rec.career.name,
                rec.career.category or '—',
                f"{round(float(rec.overall_score) * 100)}%",
                f"{round(float(rec.personality_match_score) * 100)}%",
                f"{round(float(rec.academic_match_score) * 100)}%",
                rec.career.get_kenyan_market_demand_display(),
            ])

        rec_table = Table(tdata,
                          colWidths=[4.5*cm, 2.5*cm, 1.8*cm, 2*cm, 2*cm, 2.5*cm])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 8),
            ('ALIGN',         (2,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#EFF6FF')]),
            ('GRID',          (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(rec_table)
    else:
        story.append(Paragraph('No career recommendations generated yet.', body_style))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#CBD5E1')))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        'CareerCompass Kenya — Egerton University COMP 493 Systems Project | '
        'Samuel Mathews S13/07776/22',
        ParagraphStyle('Footer', parent=styles['Normal'],
                       fontSize=8, textColor=colors.HexColor('#9CA3AF'),
                       alignment=TA_CENTER)
    ))

    doc.build(story)
    return response


@admin_required
def student_report_list(request):
    """
    Admin page that lists all students with completed assessments.
    Admins select a student here before generating a PDF career report.
    Supports filter query parameters: school, grade_level, mbti_type, username.
    """
    from django.db.models import Q

    profiles_qs = StudentProfile.objects.filter(
        assessmentresult__isnull=False
    ).select_related('user', 'school', 'assessmentresult__personality_type').distinct()

    # ── Filters ────────────────────────────────────────────────────────────────
    search      = request.GET.get('q', '').strip()
    school_id   = request.GET.get('school', '').strip()
    grade       = request.GET.get('grade', '').strip()
    mbti        = request.GET.get('mbti', '').strip()

    if search:
        profiles_qs = profiles_qs.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    if school_id:
        profiles_qs = profiles_qs.filter(school_id=school_id)
    if grade:
        profiles_qs = profiles_qs.filter(grade_level=grade)
    if mbti:
        profiles_qs = profiles_qs.filter(assessmentresult__personality_type__mbti_type=mbti)

    from users.models import School
    from assessments.models import PersonalityType
    schools     = School.objects.filter(is_active=True).order_by('name')
    mbti_types  = PersonalityType.objects.values_list('mbti_type', flat=True).order_by('mbti_type')
    grade_choices = StudentProfile._meta.get_field('grade_level').choices or []

    return render(request, 'analytics/student_report_list.html', {
        'profiles':      profiles_qs.order_by('user__last_name', 'user__first_name'),
        'schools':       schools,
        'mbti_types':    mbti_types,
        'grade_choices': grade_choices,
        'search':        search,
        'selected_school': school_id,
        'selected_grade':  grade,
        'selected_mbti':   mbti,
    })


@admin_required
def assessment_report(request):
    """
    HTML analytics report for assessments with full filter support.
    Filters: school, grade_level, mbti_type, date_from, date_to, student search.
    Also generates a downloadable PDF when ?format=pdf is passed.
    """
    from django.db.models import Q
    from datetime import datetime
    from users.models import School

    # ── Collect filter params ─────────────────────────────────────────────────
    school_id   = request.GET.get('school', '').strip()
    grade       = request.GET.get('grade', '').strip()
    mbti        = request.GET.get('mbti', '').strip()
    date_from   = request.GET.get('date_from', '').strip()
    date_to     = request.GET.get('date_to', '').strip()
    search      = request.GET.get('q', '').strip()

    # ── Base querysets ────────────────────────────────────────────────────────
    results_qs = AssessmentResult.objects.select_related(
        'student__user', 'student__school', 'personality_type'
    )
    recs_qs = StudentRecommendation.objects.select_related('student__user', 'career')

    # ── Apply filters ─────────────────────────────────────────────────────────
    if school_id:
        results_qs = results_qs.filter(student__school_id=school_id)
        recs_qs    = recs_qs.filter(student__school_id=school_id)
    if grade:
        results_qs = results_qs.filter(student__grade_level=grade)
        recs_qs    = recs_qs.filter(student__grade_level=grade)
    if mbti:
        results_qs = results_qs.filter(personality_type__mbti_type=mbti)
        recs_qs    = recs_qs.filter(student__assessmentresult__personality_type__mbti_type=mbti)
    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d')
            results_qs = results_qs.filter(created_at__date__gte=df)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            results_qs = results_qs.filter(created_at__date__lte=dt)
        except ValueError:
            pass
    if search:
        results_qs = results_qs.filter(
            Q(student__user__username__icontains=search) |
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search)
        )

    # ── Aggregate stats ────────────────────────────────────────────────────────
    total       = results_qs.count()
    counts      = list(
        results_qs.values('personality_type__mbti_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Confidence: stored as 0-1 float
    avg_conf_raw = results_qs.aggregate(Avg('confidence'))['confidence__avg']
    avg_conf_pct = round(float(avg_conf_raw) * 100, 1) if avg_conf_raw else 0

    agg = recs_qs.aggregate(
        avg_p=Avg('personality_match_score'),
        avg_a=Avg('academic_match_score'),
        avg_m=Avg('market_demand_score'),
        avg_o=Avg('overall_score'),
    )
    avg_scores = {k: _safe_float(v, 100) for k, v in agg.items()}

    total_students = StudentProfile.objects.count()
    if school_id:
        total_students = StudentProfile.objects.filter(school_id=school_id).count()
    if grade:
        total_students = StudentProfile.objects.filter(grade_level=grade).count()

    completion_rate = round(
        (total / total_students * 100) if total_students else 0, 1
    )

    score_bars = [
        ('Personality (P)', avg_scores['avg_p'], '#8b5cf6'),
        ('Academic (A)',    avg_scores['avg_a'], '#3b82f6'),
        ('Market (M)',      avg_scores['avg_m'], '#10b981'),
        ('Overall',         avg_scores['avg_o'], '#f59e0b'),
    ]

    # Top careers in filtered set
    top_careers = list(
        recs_qs.values('career__name', 'career__category')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Recent results for the table
    # AssessmentResult has no completed_at — use created_at (auto-set on save)
    recent_results = results_qs.order_by('-created_at')[:20]

    # Filter options for the form
    schools     = School.objects.filter(is_active=True).order_by('name')
    mbti_types  = PersonalityType.objects.values_list('mbti_type', flat=True).order_by('mbti_type')
    grade_choices = StudentProfile._meta.get_field('grade_level').choices or []

    ctx = {
        'total_assessments':        total,
        'personality_counts':       counts,
        'avg_confidence':           avg_conf_pct,
        'avg_scores':               avg_scores,
        'score_bars':               score_bars,
        'students_with_assessment': total,
        'total_students':           total_students,
        'completion_rate':          completion_rate,
        'top_careers':              top_careers,
        'recent_results':           recent_results,
        # Filter state
        'schools':                  schools,
        'mbti_types':               mbti_types,
        'grade_choices':            grade_choices,
        'selected_school':          school_id,
        'selected_grade':           grade,
        'selected_mbti':            mbti,
        'selected_date_from':       date_from,
        'selected_date_to':         date_to,
        'search':                   search,
        'active_filters':           any([school_id, grade, mbti, date_from, date_to, search]),
    }

    # ── PDF export ────────────────────────────────────────────────────────────
    if request.GET.get('format') == 'pdf':
        return _generate_aggregate_report_pdf(ctx)

    return render(request, 'analytics/assessment_report.html', ctx)


def _generate_aggregate_report_pdf(ctx):
    """
    Generate an aggregate PDF report for the current filtered assessment data.
    """
    from reportlab.platypus import PageBreak

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="assessment_report.pdf"'

    doc    = SimpleDocTemplate(response, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    title_s = ParagraphStyle('T', parent=styles['Heading1'], fontSize=20,
                              fontName='Helvetica-Bold',
                              textColor=colors.HexColor('#1E3A8A'),
                              alignment=TA_CENTER, spaceAfter=4)
    sub_s   = ParagraphStyle('S', parent=styles['Normal'], fontSize=10,
                              textColor=colors.HexColor('#6B7280'),
                              alignment=TA_CENTER, spaceAfter=12)
    sec_s   = ParagraphStyle('SC', parent=styles['Heading2'], fontSize=12,
                              fontName='Helvetica-Bold',
                              textColor=colors.HexColor('#1E3A8A'),
                              spaceBefore=12, spaceAfter=6)
    body_s  = ParagraphStyle('B', parent=styles['Normal'], fontSize=9, leading=13)

    story.append(Paragraph('CareerCompass Kenya', title_s))
    story.append(Paragraph('Aggregate Assessment Report', sub_s))
    story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#1E3A8A')))
    story.append(Spacer(1, 10))

    # Applied filters summary
    filters = []
    if ctx['selected_school']:    filters.append(f"School ID: {ctx['selected_school']}")
    if ctx['selected_grade']:     filters.append(f"Grade: {ctx['selected_grade']}")
    if ctx['selected_mbti']:      filters.append(f"MBTI: {ctx['selected_mbti']}")
    if ctx['selected_date_from']: filters.append(f"From: {ctx['selected_date_from']}")
    if ctx['selected_date_to']:   filters.append(f"To: {ctx['selected_date_to']}")
    if ctx['search']:             filters.append(f"Search: {ctx['search']}")
    filter_text = ', '.join(filters) if filters else 'No filters applied (all students)'
    story.append(Paragraph(f'<b>Filters applied:</b> {filter_text}', body_s))
    story.append(Spacer(1, 8))

    # KPI summary table
    story.append(Paragraph('Summary Statistics', sec_s))
    kpi_data = [
        ['Metric', 'Value'],
        ['Total Assessments Completed', str(ctx['total_assessments'])],
        ['Total Students in Filter', str(ctx['total_students'])],
        ['Completion Rate', f"{ctx['completion_rate']}%"],
        ['Average Assessment Confidence', f"{ctx['avg_confidence']}%"],
        ['Avg Personality Match Score', f"{ctx['avg_scores']['avg_p']}%"],
        ['Avg Academic Match Score',    f"{ctx['avg_scores']['avg_a']}%"],
        ['Avg Market Demand Score',     f"{ctx['avg_scores']['avg_m']}%"],
        ['Avg Overall Score',           f"{ctx['avg_scores']['avg_o']}%"],
    ]
    kpi_t = Table(kpi_data, colWidths=[10*cm, 4*cm])
    kpi_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('ALIGN',         (1,0), (1,-1), 'CENTER'),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#EFF6FF')]),
        ('GRID',          (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(kpi_t)

    # Personality distribution
    if ctx['personality_counts']:
        story.append(Spacer(1, 10))
        story.append(Paragraph('Personality Type Distribution', sec_s))
        pdata = [['MBTI Type', 'Count', '% of Assessed']]
        total = ctx['total_assessments'] or 1
        for row in ctx['personality_counts']:
            pct = round(row['count'] / total * 100, 1)
            pdata.append([
                row['personality_type__mbti_type'] or '—',
                str(row['count']),
                f"{pct}%",
            ])
        pt = Table(pdata, colWidths=[5*cm, 3*cm, 3*cm])
        pt.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#EFF6FF')]),
            ('GRID',          (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(pt)

    # Top careers
    if ctx['top_careers']:
        story.append(Spacer(1, 10))
        story.append(Paragraph('Top Recommended Careers', sec_s))
        cdata = [['Career', 'Field / Category', 'Recommendation Count']]
        for row in ctx['top_careers']:
            cdata.append([
                row['career__name'] or '—',
                row['career__category'] or '—',
                str(row['count']),
            ])
        ct = Table(cdata, colWidths=[6*cm, 4*cm, 3*cm])
        ct.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('ALIGN',         (2,0), (2,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, colors.HexColor('#EFF6FF')]),
            ('GRID',          (0,0), (-1,-1), 0.4, colors.HexColor('#CBD5E1')),
            ('TOPPADDING',    (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(ct)

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#CBD5E1')))
    story.append(Spacer(1, 6))
    from django.utils import timezone
    story.append(Paragraph(
        f'Generated: {timezone.now().strftime("%d %B %Y %H:%M")}  |  '
        'CareerCompass Kenya — Egerton University COMP 493',
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#9CA3AF'), alignment=TA_CENTER)
    ))

    doc.build(story)
    return response

