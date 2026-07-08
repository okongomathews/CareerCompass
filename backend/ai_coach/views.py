from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView
from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

from .models import Conversation, Message, CoachingPlan, ResourceRecommendation
from .serializers import (
    ConversationSerializer, MessageSerializer, 
    CoachingPlanSerializer, ChatMessageSerializer
)
from .services import AICoachService
from users.models import StudentProfile
from assessments.models import AssessmentResult

# ==================== API VIEWSETS ====================

class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        return Conversation.objects.filter(
            student=self.request.user.studentprofile
        ).prefetch_related('messages')
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user.studentprofile)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a conversation"""
        conversation = self.get_object()
        serializer = ChatMessageSerializer(data=request.data)
        
        if serializer.is_valid():
            message_content = serializer.validated_data['message']
            
            # Save user message
            user_message = Message.objects.create(
                conversation=conversation,
                content=message_content,
                is_from_ai=False
            )
            
            # Generate AI response
            coach_service = AICoachService(conversation.student)
            ai_response = coach_service.generate_ai_response(
                message_content,
                conversation_history=conversation.messages.all()
            )
            
            # Save AI response
            ai_message = Message.objects.create(
                conversation=conversation,
                content=ai_response,
                is_from_ai=True
            )
            
            # Update conversation title if it's the first message
            if conversation.messages.count() == 2:  # User + AI message
                conversation.title = message_content[:50] + "..."
                conversation.save()
            
            return Response({
                'user_message': MessageSerializer(user_message).data,
                'ai_message': MessageSerializer(ai_message).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CoachingPlanViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CoachingPlanSerializer
    
    def get_queryset(self):
        return CoachingPlan.objects.filter(
            student=self.request.user.studentprofile
        )
    
    @action(detail=False, methods=['post'])
    def generate_plan(self, request):
        """Generate or update coaching plan"""
        student_profile = request.user.studentprofile

        try:
            assessment_result = student_profile.assessmentresult
        except Exception:
            return Response(
                {'error': 'Complete personality assessment first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        coach_service  = AICoachService(student_profile)
        learning_style = coach_service.get_learning_style_recommendation()

        plan, created = CoachingPlan.objects.update_or_create(
            student=student_profile,
            defaults={
                'personality_type': assessment_result.personality_type,
                'learning_style':   learning_style,
            }
        )

        # Apply any goal data sent in the request body
        for field in ('short_term_goals', 'medium_term_goals', 'long_term_goals'):
            if field in request.data:
                val = request.data[field]
                if isinstance(val, list):
                    setattr(plan, field, [g for g in val if g])
        plan.save()

        # Generate AI plan content
        coach_service.generate_coaching_plan(plan)

        serializer = self.get_serializer(plan)
        return Response(serializer.data)

# ==================== TEMPLATE VIEWS ====================

class AICoachChatView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_coach/chat.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.studentprofile
        
        # Get conversation ID from URL or get/create one
        conversation_id = self.kwargs.get('conversation_id')
        
        if conversation_id:
            conversation = get_object_or_404(
                Conversation, 
                id=conversation_id, 
                student=student_profile
            )
        else:
            # Get or create a conversation
            conversation, created = Conversation.objects.get_or_create(
                student=student_profile,
                is_active=True,
                defaults={'title': 'Career Guidance Session'}
            )
        
        # Get or create coaching plan
        try:
            coaching_plan = student_profile.coachingplan
            context['coaching_plan'] = coaching_plan
        except CoachingPlan.DoesNotExist:
            context['coaching_plan'] = None
        
        # Get recent conversations for sidebar
        conversations = Conversation.objects.filter(
            student=student_profile
        ).order_by('-updated_at')[:5]
        
        context.update({
            'conversation': conversation,
            'conversations': conversations,
            'student': student_profile,
            'quick_prompts': [
                'What careers suit my personality?',
                'How should I prepare for KCSE exams?',
                'What subjects do I need for engineering?',
                'Best universities in Kenya for medicine?',
                'How can I improve my study habits?',
                'What are the highest-paying careers in Kenya?',
                'Explain my MBTI personality type',
                'How do I apply through KUCCPS?',
            ],
        })
        return context

class ConversationListView(LoginRequiredMixin, TemplateView):
    """View to list all conversations"""
    template_name = 'ai_coach/conversations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.studentprofile
        
        conversations = Conversation.objects.filter(
            student=student_profile
        ).order_by('-updated_at')
        context['conversations'] = conversations
        context['student'] = student_profile
        return context

class CoachingPlanView(LoginRequiredMixin, TemplateView):
    """View to display and manage the student coaching plan, including goal-setting UI."""
    template_name = 'ai_coach/coaching_plan.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.studentprofile

        # Check for completed assessment
        from assessments.models import AssessmentResult
        try:
            assessment_result = AssessmentResult.objects.select_related(
                'personality_type'
            ).get(student=student_profile)
            context['has_assessment']    = True
            context['assessment_result'] = assessment_result
        except AssessmentResult.DoesNotExist:
            context['has_assessment']    = False
            context['assessment_result'] = None
            context['coaching_plan']     = None
            context['goal_sections']     = []
            return context

        # Try to get existing coaching plan
        try:
            coaching_plan = CoachingPlan.objects.get(student=student_profile)
        except CoachingPlan.DoesNotExist:
            coaching_plan = None

        goal_sections = []
        if coaching_plan:
            def to_list(val):
                if isinstance(val, list): return val
                if isinstance(val, dict): return list(val.values())
                if isinstance(val, str) and val.strip(): return [val]
                return []

            # 6-tuple: label, goals, colour, icon, timeframe, field_name
            sections = [
                ('Short-Term',  to_list(coaching_plan.short_term_goals),
                 '#10b981', 'fas fa-seedling',  '0–3 months',  'short_term_goals'),
                ('Medium-Term', to_list(coaching_plan.medium_term_goals),
                 '#3b82f6', 'fas fa-flag',      '3–12 months', 'medium_term_goals'),
                ('Long-Term',   to_list(coaching_plan.long_term_goals),
                 '#8b5cf6', 'fas fa-mountain',  '1–5 years',   'long_term_goals'),
            ]
            goal_sections = sections

        context.update({
            'coaching_plan': coaching_plan,
            'student':        student_profile,
            'goal_sections':  goal_sections,
        })
        return context

class LearningResourcesView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_coach/resources.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.studentprofile
        
        try:
            coaching_plan = student_profile.coachingplan
            resources = ResourceRecommendation.objects.filter(
                coaching_plan=coaching_plan
            )
            context['resources'] = resources
        except CoachingPlan.DoesNotExist:
            context['resources'] = []
        
        context['student'] = student_profile
        context['default_resources'] = [
            ('Khan Academy', 'Free world-class education — Maths, Science, Computing for KCSE prep',
             'course', 'https://www.khanacademy.org', 'Visit Free', False),
            ('KUCCPS Portal', 'Official Kenya Universities and Colleges Central Placement Service',
             'tool', 'https://kuccps.ac.ke', 'Visit KUCCPS', True),
            ('Ajira Digital', 'Government digital skills platform — free training for Kenyan youth',
             'course', 'https://ajiradigital.go.ke', 'Enrol Free', True),
            ('KNEC Past Papers', 'Official KNEC KCSE past papers and marking schemes',
             'article', 'https://www.knec.ac.ke', 'Download', True),
            ('freeCodeCamp', 'Learn web development, Python, and data science for free',
             'course', 'https://www.freecodecamp.org', 'Start Learning', False),
            ('Google Career Certificates', 'Industry-recognised certificates in IT, Data, UX',
             'course', 'https://grow.google/certificates', 'Apply Free', False),
            ('Coursera', 'University courses from global top institutions, many with financial aid',
             'course', 'https://www.coursera.org', 'Browse Courses', False),
            ('HELB Portal', 'Kenya Higher Education Loans Board — student loan applications',
             'tool', 'https://www.helb.co.ke', 'Apply for Loan', True),
        ]
        # AFTER (4-tuples — matches the template)
        context['resource_types'] = [
            ('all',         'All Resources',  'fas fa-th-large',  'blue'),
            ('article',     'Articles',       'fas fa-newspaper', 'gray'),
            ('course',      'Online Courses', 'fas fa-laptop',    'purple'),
            ('book',        'Books',          'fas fa-book',      'green'),
            ('tool',        'Tools',          'fas fa-tools',     'orange'),
            ('scholarship', 'Scholarships',   'fas fa-award',     'yellow'),
        ]
        try:
            context['coaching_plan'] = student_profile.coachingplan
        except Exception:
            context['coaching_plan'] = None
        return context

# ==================== API VIEWS FOR TEMPLATES ====================

class AICoachAPIView(LoginRequiredMixin, View):
    """API endpoint for AI coach interactions (for templates)"""

    def post(self, request, conversation_id=None):
        try:
            data    = json.loads(request.body)
            message = data.get('message', '')

            if not message.strip():
                return JsonResponse({'error': 'Message is required'}, status=400)

            # Get or create StudentProfile for any authenticated user
            # Admin users and non-students can also use the AI coach
            try:
                student = request.user.studentprofile
            except Exception:
                from users.models import StudentProfile
                from users.signals import _ensure_default_school
                student, _ = StudentProfile.objects.get_or_create(
                    user=request.user,
                    defaults={'school': _ensure_default_school()}
                )

            # Get or create conversation
            if conversation_id:
                conversation = get_object_or_404(
                    Conversation, id=conversation_id, student=student
                )
            else:
                conversation, _ = Conversation.objects.get_or_create(
                    student=student,
                    is_active=True,
                    defaults={'title': 'Career Guidance Session'}
                )

            # Save user message
            Message.objects.create(
                conversation=conversation,
                content=message,
                is_from_ai=False
            )

            # Generate AI response
            ai_coach = AICoachService(student)
            previous_messages = Message.objects.filter(
                conversation=conversation
            ).order_by('timestamp')[:10]

            ai_response_text = ai_coach.generate_ai_response(
                message,
                conversation_history=previous_messages
            )

            # Clean excessive markdown before saving/returning
            ai_response_text = _clean_ai_response(ai_response_text)

            # Save AI response
            ai_message = Message.objects.create(
                conversation=conversation,
                content=ai_response_text,
                is_from_ai=True
            )

            # Update conversation title on first exchange
            if (conversation.title == 'Career Guidance Session'
                    and Message.objects.filter(conversation=conversation).count() <= 3):
                conversation.title = f"{message[:35]}..."
                conversation.save(update_fields=['title'])

            return JsonResponse({
                'success':         True,
                'response':        ai_response_text,
                'message_id':      ai_message.id,
                'conversation_id': conversation.id,
            })

        except Exception as e:
            logger.exception("AICoachAPIView error")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _clean_ai_response(text):
    """
    Convert markdown-style formatting to clean HTML for display in the chat bubble.
    Removes excessive asterisks, converts **bold** to <strong>, bullet points, etc.
    """
    if not text:
        return text
    import re

    # Convert **bold** to <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Convert *italic* (single asterisks) — just remove them, don't need italic in chat
    text = re.sub(r'\*([^\*\n]+)\*', r'\1', text)
    # Remove any remaining lone asterisks
    text = text.replace('*', '')
    # Convert markdown bullet points (• or - or *) to readable format
    text = re.sub(r'^[\s]*[-•]\s+', '→ ', text, flags=re.MULTILINE)
    # Convert numbered lists
    text = re.sub(r'^(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)
    # Collapse 3+ newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

class UpdateGoalsView(LoginRequiredMixin, View):
    """Save individual goal fields and optionally regenerate the coaching plan via AI."""

    _ALLOWED_FIELDS = {'short_term_goals', 'medium_term_goals', 'long_term_goals'}

    def post(self, request):
        try:
            data    = json.loads(request.body)
            student = request.user.studentprofile

            # Require a completed assessment
            from assessments.models import AssessmentResult
            try:
                assessment = AssessmentResult.objects.select_related(
                    'personality_type'
                ).get(student=student)
            except AssessmentResult.DoesNotExist:
                return JsonResponse(
                    {'error': 'Complete the personality assessment first.'},
                    status=400
                )

            coaching_plan, _ = CoachingPlan.objects.get_or_create(
                student=student,
                defaults={'personality_type': assessment.personality_type},
            )

            # Update whichever goal fields were sent
            updated_any = False
            for field in self._ALLOWED_FIELDS:
                if field in data:
                    val = data[field]
                    if not isinstance(val, list):
                        val = [str(val)] if val else []
                    # Filter out blanks
                    val = [g.strip() for g in val if str(g).strip()]
                    setattr(coaching_plan, field, val)
                    updated_any = True

            # Also support the initial create-form payload keys
            for src, dst in (('short_term', 'short_term_goals'),
                             ('medium_term', 'medium_term_goals'),
                             ('long_term', 'long_term_goals')):
                if src in data:
                    val = [g.strip() for g in data[src] if str(g).strip()]
                    setattr(coaching_plan, dst, val)
                    updated_any = True

            if updated_any:
                coaching_plan.save()

            # Regenerate plan content via AI if requested or on first creation
            if data.get('generate', False) or not coaching_plan.short_term_goals:
                try:
                    from .services import AICoachService
                    svc    = AICoachService(student)
                    result = svc.generate_coaching_plan(coaching_plan)
                    if result:
                        coaching_plan.refresh_from_db()
                except Exception as gen_err:
                    logger.warning(f'AI plan generation failed (non-fatal): {gen_err}')

            return JsonResponse({'success': True, 'message': 'Goals updated successfully'})

        except Exception as e:
            logger.error(f'UpdateGoalsView error: {e}')
            return JsonResponse({'error': str(e)}, status=500)