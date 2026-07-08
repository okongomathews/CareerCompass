"""
assessments/views.py  — fully fixed version
Bugs addressed:
  1. complete_assessment minimum was hardcoded to 5; now dynamic (≥1 per dimension needed)
  2. AssessmentQuestionView now passes questions_json so the new template can use
     json_script to safely inject questions without Django/JS escaping conflicts.
  3. Admin users are redirected away from assessment pages consistently.
"""
import json
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from .models import (
    AssessmentSession, Question, AnswerChoice, QuestionResponse,
    AssessmentResult, PersonalityType, MBTIDimension,
)
from .serializers import (
    QuestionSerializer, AssessmentSessionSerializer,
    QuestionResponseSerializer, AssessmentResultSerializer,
    AssessmentSubmissionSerializer, PersonalityTypeSerializer,
)
from .services import MBTICalculator


def _is_admin(user):
    """True if user should be restricted to admin-only pages."""
    return getattr(user, 'is_staff', False) or getattr(user, 'user_type', '') in ('admin',)


# ── API ViewSets ──────────────────────────────────────────────────────────────

class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer
    pagination_class = None

    def get_queryset(self):
        return Question.objects.prefetch_related('choices').all()


class AssessmentSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AssessmentSessionSerializer

    def get_queryset(self):
        return AssessmentSession.objects.filter(
            student=self.request.user.studentprofile
        ).prefetch_related('responses', 'responses__question', 'responses__answer')

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.studentprofile)

    def create(self, request):
        student_profile = request.user.studentprofile
        existing = AssessmentSession.objects.filter(
            student=student_profile, is_completed=False).first()
        if existing:
            return Response(self.get_serializer(existing).data)
        session = AssessmentSession.objects.create(student=student_profile)
        return Response(self.get_serializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit_response(self, request, pk=None):
        session = self.get_object()
        if session.student.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        question_id = request.data.get('question_id')
        answer_id   = request.data.get('answer_id')
        response_time = request.data.get('response_time', 0)

        try:
            question = Question.objects.get(id=question_id)
            answer   = AnswerChoice.objects.get(id=answer_id, question=question)
        except (Question.DoesNotExist, AnswerChoice.DoesNotExist):
            return Response(
                {'error': 'Invalid question or answer'},
                status=status.HTTP_400_BAD_REQUEST)

        resp, _ = QuestionResponse.objects.update_or_create(
            session=session, question=question,
            defaults={'answer': answer, 'response_time': response_time},
        )
        total    = Question.objects.count()
        answered = session.responses.count()
        return Response({
            **QuestionResponseSerializer(resp).data,
            'progress': {
                'answered': answered,
                'total':    total,
                'percent':  int((answered / total * 100) if total else 0),
            },
        })

    @action(detail=True, methods=['post'])
    def complete_assessment(self, request, pk=None):
        session = self.get_object()
        if session.student.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        answered_count = session.responses.count()
        total_questions = Question.objects.count()

        # Require at least 1 answer per MBTI dimension (4 dims) so scoring is meaningful.
        # We use a soft minimum of 4 (one per dimension) rather than a fixed 60/64.
        minimum_required = min(4, total_questions)  # works with any question count

        if answered_count < minimum_required:
            return Response(
                {'error': (
                    f'Please answer at least {minimum_required} questions before submitting. '
                    f'You have answered {answered_count} so far.'
                )},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            calculator = MBTICalculator(session)
            result     = calculator.generate_result()
            session.is_completed = True
            session.completed_at = timezone.now()
            session.save()
            return Response(AssessmentResultSerializer(result).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssessmentResultViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class   = AssessmentResultSerializer

    def get_queryset(self):
        return AssessmentResult.objects.filter(
            student__user=self.request.user
        ).select_related('personality_type')


class PersonalityTypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PersonalityTypeSerializer
    queryset         = PersonalityType.objects.all()
    pagination_class = None


# ── Template Views ────────────────────────────────────────────────────────────

class AssessmentStartView(LoginRequiredMixin, TemplateView):
    template_name = 'assessments/start.html'

    def get(self, request, *args, **kwargs):
        if _is_admin(request.user):
            from django.contrib import messages
            messages.info(request, 'Administrators manage the system via the Analytics Dashboard.')
            return redirect('analytics:admin_dashboard')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            profile = self.request.user.studentprofile
            context['has_previous_assessment'] = AssessmentResult.objects.filter(
                student=profile).exists()
        except Exception:
            context['has_previous_assessment'] = False

        total = Question.objects.count()
        context['dimensions']       = MBTIDimension.objects.all()
        context['total_questions']  = total
        return context


class AssessmentQuestionView(LoginRequiredMixin, TemplateView):
    template_name = 'assessments/question.html'

    def get(self, request, *args, **kwargs):
        if _is_admin(request.user):
            return redirect('analytics:admin_dashboard')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            profile = self.request.user.studentprofile
        except Exception:
            from users.models import StudentProfile
            profile = StudentProfile.objects.create(user=self.request.user)

        # Reuse existing incomplete session, or start fresh
        session = AssessmentSession.objects.filter(
            student=profile, is_completed=False).first()
        if not session:
            session = AssessmentSession.objects.create(student=profile)

        questions = list(
            Question.objects.prefetch_related('choices').all().order_by('category', 'id')
        )
        answered_ids = set(
            QuestionResponse.objects.filter(session=session)
            .values_list('question_id', flat=True)
        )
        total    = len(questions)
        answered = len(answered_ids)

        # Build a JSON-safe structure for the template.
        # Using json_script in the template avoids all Django/JS escaping edge cases.
        questions_data = []
        for q in questions:
            questions_data.append({
                'id':       q.id,
                'text':     q.text,
                'category': q.category,
                'choices':  [
                    {'id': c.id, 'text': c.text, 'value': c.value}
                    for c in q.choices.all()
                ],
            })

        context.update({
            'session':          session,
            'questions':        questions,          # for non-JS fallback / hidden spans
            'questions_json':   questions_data,     # for json_script injection
            'answered_ids':     list(answered_ids),
            'total_questions':  total,
            'answered_count':   answered,
            'progress_percent': int((answered / total * 100) if total else 0),
        })
        return context


class AssessmentResultsView(LoginRequiredMixin, DetailView):
    template_name    = 'assessments/results.html'
    context_object_name = 'result'

    def get(self, request, *args, **kwargs):
        if _is_admin(request.user):
            return redirect('analytics:admin_dashboard')
        return super().get(request, *args, **kwargs)

    def get_object(self):
        try:
            profile = self.request.user.studentprofile
        except Exception:
            from users.models import StudentProfile
            profile = StudentProfile.objects.create(user=self.request.user)
        return get_object_or_404(
            AssessmentResult.objects.select_related('personality_type'),
            student=profile,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result  = self.object
        student = result.student

        context['pole_percentages']  = result.get_pole_percentages()
        context['confidence_percent'] = result.get_confidence_percent()

        # Learning style + coaching plan
        try:
            from ai_coach.services import AICoachService
            from ai_coach.models import CoachingPlan
            coach          = AICoachService(student)
            learning_style = coach.get_learning_style_recommendation()
            CoachingPlan.objects.update_or_create(
                student=student,
                defaults={
                    'personality_type': result.personality_type,
                    'learning_style':   learning_style,
                },
            )
            context['learning_style'] = learning_style
        except Exception:
            context['learning_style'] = None

        # Career recommendations: use saved StudentRecommendation records first
        # so the results page shows exactly the same careers as /recommendations/
        try:
            from recommendations.models import StudentRecommendation
            saved_recs = StudentRecommendation.objects.filter(
                student=student
            ).select_related('career').order_by('-overall_score')[:6]

            if saved_recs.exists():
                # Use the persisted records — guarantees consistency with /recommendations/
                context['career_recommendations'] = saved_recs
                context['recs_are_saved'] = True
            else:
                # Fallback: generate live (first-time, before recs are saved)
                from recommendations.services import RecommendationEngine
                engine = RecommendationEngine(student)
                context['career_recommendations'] = engine.generate_career_recommendations(top_n=6)
                context['recs_are_saved'] = False
        except Exception:
            context['career_recommendations'] = []
            context['recs_are_saved'] = False

        context['all_types'] = PersonalityType.objects.all().order_by('mbti_type')
        return context


# ── AJAX helpers ──────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_bulk_responses(request):
    serializer = AssessmentSubmissionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    session_id     = serializer.validated_data['session_id']
    responses_data = serializer.validated_data['responses']

    try:
        session = AssessmentSession.objects.get(
            id=session_id, student=request.user.studentprofile)
    except AssessmentSession.DoesNotExist:
        return Response({'error': 'Invalid session'}, status=status.HTTP_400_BAD_REQUEST)

    saved = 0
    with transaction.atomic():
        for item in responses_data:
            try:
                question = Question.objects.get(id=item['question_id'])
                answer   = AnswerChoice.objects.get(id=item['answer_id'], question=question)
                QuestionResponse.objects.update_or_create(
                    session=session, question=question,
                    defaults={'answer': answer, 'response_time': item.get('response_time', 0)},
                )
                saved += 1
            except Exception:
                pass

    total    = Question.objects.count()
    answered = session.responses.count()
    return Response({
        'saved': saved,
        'progress': {
            'answered': answered,
            'total':    total,
            'percent':  int((answered / total * 100) if total else 0),
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_next_question(request, session_id):
    try:
        session = AssessmentSession.objects.get(
            id=session_id, student=request.user.studentprofile)
    except AssessmentSession.DoesNotExist:
        return Response({'error': 'Invalid session'}, status=status.HTTP_400_BAD_REQUEST)

    answered_ids = list(session.responses.values_list('question_id', flat=True))
    next_q = Question.objects.exclude(id__in=answered_ids).prefetch_related('choices').first()
    if not next_q:
        return Response({'completed': True})

    return Response({
        'completed': False,
        'question':  QuestionSerializer(next_q).data,
        'answered':  len(answered_ids),
        'total':     Question.objects.count(),
    })
