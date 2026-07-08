# recommendations/views.py - COMPLETELY REGENERATED
from rest_framework import viewsets, status, generics, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Avg, Subquery, OuterRef
from django.db import transaction, models
from django.http import JsonResponse
from django.core.cache import cache
import json
from .models import (
    Career, Subject, StudentRecommendation, LearningStyle,
    CareerPersonalityMatch, CareerSubject, CareerLearningStyle,
    RecommendationAnalytics
)

from .serializers import (
    CareerSerializer, SubjectSerializer, StudentRecommendationSerializer,
    LearningStyleSerializer, CareerRecommendationSerializer,
    CareerPersonalityMatchSerializer, CareerDetailSerializer,
    SubjectRecommendationSerializer,
    CareerLearningStyleSerializer,
    RecommendationAnalyticsSerializer,
    CareerComparisonSerializer, LearningPathSerializer
)
from .services import RecommendationEngine, SubjectRecommender, MLEnhancedRecommendationEngine
from .ml_models import CareerSuccessPredictor, MarketTrendAnalyzer, PersonalizedLearningPathOptimizer, AdaptiveAssessmentSystem
from users.models import StudentProfile
from assessments.models import AssessmentResult, PersonalityType

# ==================== API VIEWSETS ====================
class CareerViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for careers with enhanced filtering"""
    serializer_class = CareerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Career.objects.prefetch_related(
            'required_subjects', 'recommended_subjects'
        ).select_related('category').all()

        # Apply filters
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__iexact=category)

        demand = self.request.query_params.get('demand')
        if demand:
            queryset = queryset.filter(kenyan_market_demand=demand)

        min_salary = self.request.query_params.get('min_salary')
        if min_salary:
            queryset = queryset.filter(average_salary__gte=min_salary)

        max_salary = self.request.query_params.get('max_salary')
        if max_salary:
            queryset = queryset.filter(average_salary__lte=max_salary)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search) |
                Q(skills_required__icontains=search)
            )

        # Sort by different criteria
        sort_by = self.request.query_params.get('sort_by', 'name')
        if sort_by == 'salary_desc':
            queryset = queryset.order_by('-average_salary')
        elif sort_by == 'salary_asc':
            queryset = queryset.order_by('average_salary')
        elif sort_by == 'demand':
            # Custom ordering for market demand
            demand_order = {'very_high': 0, 'high': 1, 'medium': 2, 'low': 3, 'very_low': 4}
            queryset = sorted(queryset, key=lambda x: demand_order.get(x.kenyan_market_demand, 5))
        elif sort_by == 'popularity':
            # Get careers sorted by recommendation count
            popular_careers = Career.objects.annotate(
                recommendation_count=Count('studentrecommendation')
            ).order_by('-recommendation_count')
            queryset = popular_careers
        else:
            queryset = queryset.order_by('name')

        return queryset

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of all career categories"""
        categories = Career.objects.values_list('category', flat=True).distinct()
        return Response(list(categories))

    @action(detail=False, methods=['get'])
    def market_stats(self, request):
        """Get market statistics for careers"""
        stats = {
            'total_careers': Career.objects.count(),
            'by_demand': dict(Career.objects.values_list('kenyan_market_demand').annotate(count=Count('id'))),
            'avg_salary': Career.objects.aggregate(Avg('average_salary'))['average_salary__avg'],
            'highest_paying': Career.objects.order_by('-average_salary').values('name', 'average_salary')[:5],
            'most_in_demand': Career.objects.filter(kenyan_market_demand__in=['very_high', 'high']).values('name', 'kenyan_market_demand')[:5]
        }
        return Response(stats)

    @action(detail=True, methods=['get'])
    def compatibility_score(self, request, pk=None):
        """Get compatibility score for current user with this career"""
        career = self.get_object()
        student_profile = request.user.studentprofile

        engine = RecommendationEngine(student_profile)

        # Calculate individual scores
        personality_score = engine.calculate_personality_match_score(career)
        academic_score = engine.calculate_academic_match_score(career)
        market_score = engine.calculate_market_demand_score(career)
        learning_score = engine.calculate_learning_style_score(career)
        grade_boost = engine.calculate_grade_level_boost(career)

        # Overall score
        overall_score = (
            personality_score * 0.40 +
            academic_score * 0.30 +
            market_score * 0.20 +
            learning_score * 0.10
        ) + grade_boost

        overall_score = max(0, min(1, overall_score))  # Ensure 0-1 range

        return Response({
            'career': CareerSerializer(career).data,
            'scores': {
                'overall': round(overall_score * 100, 1),
                'personality': round(personality_score * 100, 1),
                'academic': round(academic_score * 100, 1),
                'market': round(market_score * 100, 1),
                'learning_style': round(learning_score * 100, 1),
                'grade_boost': round(grade_boost * 100, 1)
            },
            'reasoning': engine._generate_recommendation_reasoning(
                career, personality_score, academic_score,
                market_score, learning_score, overall_score
            )
        })

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for subjects"""
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    queryset = Subject.objects.all()
    pagination_class = None

    @action(detail=False, methods=['get'])
    def by_career(self, request):
        """Get subjects required/recommended for specific careers"""
        career_ids = request.query_params.getlist('career_ids[]')
        subjects = Subject.objects.filter(
            careers_requiring__id__in=career_ids
        ).distinct().order_by('name')
        serializer = self.get_serializer(subjects, many=True)
        return Response(serializer.data)

class StudentRecommendationViewSet(viewsets.ModelViewSet):
    """API endpoint for student career recommendations"""
    permission_classes = [IsAuthenticated]
    serializer_class = StudentRecommendationSerializer

    def get_queryset(self):
        return StudentRecommendation.objects.filter(
            student=self.request.user.studentprofile
        ).select_related('career').prefetch_related(
            'recommended_subjects'
        ).order_by('-overall_score', '-created_at')

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.studentprofile)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate new career recommendations with dynamic scoring"""
        student_profile = request.user.studentprofile

        # Check if assessment is completed
        try:
            assessment_result = student_profile.assessmentresult
        except AssessmentResult.DoesNotExist:
            return Response(
                {'error': 'Complete personality assessment first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use caching to avoid recomputation
        cache_key = f'student_recommendations_{student_profile.id}'
        cached_recommendations = cache.get(cache_key)

        if cached_recommendations and not request.GET.get('force_refresh'):
            return Response(cached_recommendations)

        engine = RecommendationEngine(student_profile)
        recommendations_data = engine.generate_career_recommendations(top_n=15)

        with transaction.atomic():
            # Clear old recommendations
            StudentRecommendation.objects.filter(student=student_profile).delete()

            # Create new recommendations
            created_recommendations = []
            for rec_data in recommendations_data:
                recommendation = StudentRecommendation.objects.create(
                    student=student_profile,
                    career=rec_data['career'],
                    overall_score=rec_data['overall_score'],
                    personality_match_score=rec_data['personality_match_score'],
                    academic_match_score=rec_data['academic_match_score'],
                    market_demand_score=rec_data['market_demand_score'],
                    learning_style_score=rec_data['learning_style_score'],
                    grade_boost=rec_data['grade_boost'],
                    reasoning=rec_data['reasoning']
                )

                # Add recommended subjects
                try:
                    # Get subjects for this career
                    from .services import SubjectRecommender
                    subject_rec = SubjectRecommender(student_profile)
                    subjects = subject_rec.get_subjects_for_career(rec_data['career'])
                    recommendation.recommended_subjects.set(subjects)
                except:
                    pass

                created_recommendations.append(recommendation)

        # Serialize and cache results
        serializer = self.get_serializer(created_recommendations, many=True)
        cache.set(cache_key, serializer.data, 3600)  # Cache for 1 hour

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def compatibility_summary(self, request):
        """Get summary of compatibility scores"""
        student_profile = request.user.studentprofile

        recommendations = self.get_queryset()

        if not recommendations.exists():
            return Response({
                'message': 'No recommendations yet. Generate recommendations first.',
                'summary': None
            })

        summary = {
            'total_recommendations': recommendations.count(),
            'avg_overall_score': recommendations.aggregate(avg=Avg('overall_score'))['avg'],
            'avg_personality_score': recommendations.aggregate(avg=Avg('personality_match_score'))['avg'],
            'avg_academic_score': recommendations.aggregate(avg=Avg('academic_match_score'))['avg'],
            'avg_market_score': recommendations.aggregate(avg=Avg('market_demand_score'))['avg'],
            'top_careers': [
                {
                    'name': rec.career.name,
                    'overall_score': rec.overall_score,
                    'category': rec.career.category,
                    'market_demand': rec.career.get_kenyan_market_demand_display(),
                    'salary': rec.career.average_salary
                }
                for rec in recommendations[:5]
            ],
            'compatibility_distribution': {
                'high': recommendations.filter(overall_score__gte=0.7).count(),
                'medium': recommendations.filter(overall_score__gte=0.5, overall_score__lt=0.7).count(),
                'low': recommendations.filter(overall_score__lt=0.5).count()
            }
        }

        return Response(summary)

class LearningStyleViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for learning styles"""
    serializer_class = LearningStyleSerializer
    permission_classes = [IsAuthenticated]
    queryset = LearningStyle.objects.all()
    pagination_class = None

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Get recommended learning style for current user"""
        student_profile = request.user.studentprofile

        try:
            from ai_coach.services import AICoachService
            coach = AICoachService(student_profile)
            learning_style = coach.get_learning_style_recommendation()
            serializer = self.get_serializer(learning_style)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Could not determine learning style: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class CareerPersonalityMatchViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for career-personality matches"""
    serializer_class = CareerPersonalityMatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CareerPersonalityMatch.objects.select_related(
            'career', 'personality_type'
        ).all()

        personality_type = self.request.query_params.get('personality_type')
        if personality_type:
            queryset = queryset.filter(personality_type__mbti_type=personality_type)

        min_score = self.request.query_params.get('min_score')
        if min_score:
            queryset = queryset.filter(match_score__gte=min_score)

        return queryset.order_by('-match_score')

# ==================== TEMPLATE VIEWS ====================

class CareerRecommendationsView(LoginRequiredMixin, TemplateView):
    """View to display personalized career recommendations with dynamic scoring"""
    template_name = 'recommendations/career_recommendations.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_profile = self.request.user.studentprofile

        # ── Query params for filtering & sorting ──────────────────────────
        request      = self.request
        demand_filter = request.GET.get('demand', '')   # '' = all, 'very_high', 'high', etc.
        sort_mode     = request.GET.get('sort', 'personality')  # 'personality' | 'demand' | 'salary'

        # ── Get or generate recommendations ───────────────────────────────
        recs_qs = StudentRecommendation.objects.filter(
            student=student_profile
        ).select_related('career').order_by('-overall_score')

        if not recs_qs.exists():
            try:
                engine = RecommendationEngine(student_profile)
                recs_data = engine.generate_career_recommendations(top_n=20)
                with transaction.atomic():
                    for r in recs_data:
                        StudentRecommendation.objects.create(
                            student=student_profile,
                            career=r['career'],
                            overall_score=r['overall_score'],
                            personality_match_score=r['personality_match_score'],
                            academic_match_score=r['academic_match_score'],
                            market_demand_score=r['market_demand_score'],
                            learning_style_score=r['learning_style_score'],
                            grade_boost=r['grade_boost'],
                            reasoning=r['reasoning'],
                        )
                recs_qs = StudentRecommendation.objects.filter(
                    student=student_profile
                ).select_related('career').order_by('-overall_score')
            except Exception as e:
                import traceback; traceback.print_exc()
                recs_qs = StudentRecommendation.objects.none()

        # ── Apply demand filter ────────────────────────────────────────────
        _DEMAND_ORDER = {'very_high': 0, 'high': 1, 'medium': 2, 'low': 3, 'very_low': 4}
        recommendations = list(recs_qs)

        if demand_filter:
            recommendations = [r for r in recommendations
                                if r.career.kenyan_market_demand == demand_filter]

        # ── Apply sort mode ────────────────────────────────────────────────
        if sort_mode == 'demand':
            recommendations.sort(
                key=lambda r: _DEMAND_ORDER.get(r.career.kenyan_market_demand, 5)
            )
        elif sort_mode == 'salary':
            recommendations.sort(
                key=lambda r: float(r.career.average_salary or 0), reverse=True
            )
        # default 'personality' already sorted by overall_score DESC

        # ── Tier categorisation ───────────────────────────────────────────
        high_compatibility   = [r for r in recommendations if r.overall_score >= 0.70]
        medium_compatibility = [r for r in recommendations if 0.50 <= r.overall_score < 0.70]
        low_compatibility    = [r for r in recommendations if r.overall_score < 0.50]

        # ── Supporting context ────────────────────────────────────────────
        personality_type = None
        try:
            personality_type = student_profile.assessmentresult.personality_type
        except Exception:
            pass

        learning_style = None
        try:
            from ai_coach.models import CoachingPlan
            learning_style = CoachingPlan.objects.get(student=student_profile).learning_style
        except Exception:
            pass

        try:
            subject_recommender = SubjectRecommender(student_profile)
            recommended_subjects = subject_recommender.recommend_subjects()
        except Exception:
            recommended_subjects = []

        market_stats = {
            'total_careers': Career.objects.count(),
            'high_demand':   Career.objects.filter(kenyan_market_demand__in=['very_high', 'high']).count(),
            'avg_salary':    Career.objects.aggregate(Avg('average_salary'))['average_salary__avg'] or 0,
        }

        context.update({
            'recommendations':      recommendations,
            'high_compatibility':   high_compatibility,
            'medium_compatibility': medium_compatibility,
            'low_compatibility':    low_compatibility,
            'recommended_subjects': recommended_subjects,
            'learning_style':       learning_style,
            'personality_type':     personality_type,
            'market_stats':         market_stats,
            'student':              student_profile,
            'has_recommendations':  bool(recommendations),
            'completion_percentage': min(100, len(recommendations) * 10),
            'all_recommendations':  recommendations,
            # Filter / sort state (passed back to template for active-state UI)
            'demand_filter':  demand_filter,
            'sort_mode':      sort_mode,
            'demand_choices': Career.MARKET_DEMAND_CHOICES,
        })
        return context

class CareerDetailView(LoginRequiredMixin, DetailView):
    """View to display detailed information about a specific career"""
    model = Career
    template_name = 'recommendations/career_detail.html'
    context_object_name = 'career'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.studentprofile

        # Calculate compatibility scores
        engine = RecommendationEngine(student)

        personality_score = engine.calculate_personality_match_score(self.object)
        academic_score = engine.calculate_academic_match_score(self.object)
        market_score = engine.calculate_market_demand_score(self.object)
        learning_score = engine.calculate_learning_style_score(self.object)
        grade_boost = engine.calculate_grade_level_boost(self.object)

        overall_score = (
            personality_score * 0.40 +
            academic_score * 0.30 +
            market_score * 0.20 +
            learning_score * 0.10
        ) + grade_boost

        overall_score = max(0, min(1, overall_score))

        # Get or create recommendation
        recommendation, created = StudentRecommendation.objects.get_or_create(
            student=student,
            career=self.object,
            defaults={
                'overall_score': overall_score,
                'personality_match_score': personality_score,
                'academic_match_score': academic_score,
                'market_demand_score': market_score,
                'learning_style_score': learning_score,
                'grade_boost': grade_boost,
                'reasoning': engine.generate_reasoning(   # correct public method
                    self.object, personality_score, academic_score,
                    market_score, learning_score, overall_score
                )
            }
        )

        # Get required and recommended subjects
        required_subjects = CareerSubject.objects.filter(
            career=self.object, importance='required'
        ).select_related('subject')

        recommended_subjects = CareerSubject.objects.filter(
            career=self.object, importance='recommended'
        ).select_related('subject')

        # Get student's current subjects
        student_subjects = list(student.subjects.values_list('name', flat=True))

        # Check subject matches
        subject_matches = []
        for req_subject in required_subjects:
            subject_matches.append({
                'subject': req_subject.subject,
                'required': True,
                'student_has': req_subject.subject.name in student_subjects
            })

        for rec_subject in recommended_subjects:
            subject_matches.append({
                'subject': rec_subject.subject,
                'required': False,
                'student_has': rec_subject.subject.name in student_subjects
            })

        # Get learning path suggestions
        learning_path = engine.generate_learning_path(self.object, student)

        # Get related careers
        related_careers = Career.objects.filter(
            Q(category=self.object.category) |
            Q(required_subjects__in=self.object.required_subjects.all())
        ).distinct().exclude(id=self.object.id)[:6]

        # Get Kenyan context information
        kenyan_context = {
            'universities_offering': self._get_kenyan_universities(self.object),
            'scholarships': self._get_scholarship_info(self.object),
            'companies_hiring': self._get_kenyan_companies(self.object)
        }

        context.update({
            'recommendation': recommendation,
            'scores': {
                'overall': round(overall_score * 100, 1),
                'personality': round(personality_score * 100, 1),
                'academic': round(academic_score * 100, 1),
                'market': round(market_score * 100, 1),
                'learning_style': round(learning_score * 100, 1),
                'grade_boost': round(grade_boost * 100, 1)
            },
            'subject_matches': subject_matches,
            'learning_path': learning_path,
            'related_careers': related_careers,
            'kenyan_context': kenyan_context,
            'student': student,
            'student_subjects': student_subjects,
            'compatibility_level': self._get_compatibility_level(overall_score)
        })

        return context

    def _get_compatibility_level(self, score):
        """Get human-readable compatibility level"""
        if score >= 0.8:
            return 'Excellent Match'
        elif score >= 0.7:
            return 'Great Match'
        elif score >= 0.6:
            return 'Good Match'
        elif score >= 0.5:
            return 'Moderate Match'
        else:
            return 'Potential Match'

    def _get_kenyan_universities(self, career):
        """Get Kenyan universities offering this career"""
        universities_map = {
            'Software Developer': ['University of Nairobi', 'Strathmore University', 'JKUAT', 'Moi University', 'Kenyatta University'],
            'Data Scientist': ['University of Nairobi', 'Strathmore University', 'African Nazarene University'],
            'Medical Doctor': ['University of Nairobi', 'Kenyatta University', 'Moi University', 'Egerton University'],
            'Civil Engineer': ['University of Nairobi', 'JKUAT', 'Moi University', 'Technical University of Mombasa'],
            'Accountant': ['University of Nairobi', 'Strathmore University', 'Kenyatta University', 'Mount Kenya University'],
            'Teacher': ['Kenyatta University', 'University of Nairobi', 'Moi University', 'Maseno University'],
        }
        return universities_map.get(career.name, ['Various Kenyan Universities'])

    def _get_scholarship_info(self, career):
        """Get scholarship information for this career"""
        scholarships = {
            'STEM': ['KCB Foundation Scholarship', 'Mastercard Foundation Scholarship', 'Equity Wings to Fly'],
            'Healthcare': ['Ministry of Health Scholarships', 'AMREF Scholarships', 'County Government Scholarships'],
            'Education': ['Teachers Service Commission Scholarships', 'County Bursaries'],
            'Engineering': ['Engineers Board of Kenya Scholarships', 'Corporate Sponsorships']
        }

        for category, scholarship_list in scholarships.items():
            if category.lower() in career.category.lower():
                return scholarship_list

        return ['HELB Loans', 'County Bursaries', 'University Scholarships']

    def _get_kenyan_companies(self, career):
        """Get Kenyan companies hiring for this career"""
        companies_map = {
            'Software Developer': ['Safaricom', 'Andela', 'Africa\'s Talking', 'Copia', 'Twiga Foods'],
            'Data Scientist': ['Safaricom', 'IBM Africa', 'Zumi', 'Jumo', 'Branch'],
            'Medical Doctor': ['Kenyatta National Hospital', 'Moi Teaching Hospital', 'Ministry of Health', 'Private Hospitals'],
            'Civil Engineer': ['Ministry of Transport', 'Chinese Road & Bridge Corp', 'Local Contractors'],
            'Accountant': ['KPMG', 'PwC', 'Deloitte', 'EY', 'Local Accounting Firms'],
            'Teacher': ['Ministry of Education', 'Private Schools', 'International Schools'],
        }
        return companies_map.get(career.name, ['Various Kenyan Companies'])

class CareerListView(LoginRequiredMixin, ListView):
    """View to browse all available careers with enhanced filtering"""
    model = Career
    template_name = 'recommendations/career_list.html'
    context_object_name = 'careers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Career.objects.prefetch_related(
            'required_subjects', 'recommended_subjects'
        ).all()   # ✅ Removed invalid select_related('category')

        # Apply filters (same as before)
        category = self.request.GET.get('category')
        if category and category != 'all':
            queryset = queryset.filter(category__iexact=category)

        demand = self.request.GET.get('demand')
        if demand and demand != 'all':
            queryset = queryset.filter(kenyan_market_demand=demand)

        min_salary = self.request.GET.get('min_salary')
        if min_salary:
            queryset = queryset.filter(average_salary__gte=int(min_salary))

        max_salary = self.request.GET.get('max_salary')
        if max_salary:
            queryset = queryset.filter(average_salary__lte=int(max_salary))

        # Personality match filter
        personality_filter = self.request.GET.get('personality_match')
        if personality_filter and personality_filter != 'all':
            try:
                student = self.request.user.studentprofile
                assessment_result = student.assessmentresult
                personality_type = assessment_result.personality_type

                high_match_careers = CareerPersonalityMatch.objects.filter(
                    personality_type=personality_type,
                    match_score__gte=80
                ).values_list('career_id', flat=True)

                queryset = queryset.filter(id__in=high_match_careers)
            except:
                pass

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search) |
                Q(skills_required__icontains=search)
            )

        # Sorting (same as before)
        sort_by = self.request.GET.get('sort_by', 'name')
        if sort_by == 'salary_desc':
            queryset = queryset.order_by('-average_salary')
        elif sort_by == 'salary_asc':
            queryset = queryset.order_by('average_salary')
        elif sort_by == 'demand':
            demand_order = {'very_high': 0, 'high': 1, 'medium': 2, 'low': 3, 'very_low': 4}
            queryset = sorted(queryset, key=lambda x: demand_order.get(x.kenyan_market_demand, 5))
        elif sort_by == 'popularity':
            popular_careers = Career.objects.annotate(
                recommendation_count=Count('studentrecommendation')
            ).order_by('-recommendation_count')
            queryset = popular_careers
        else:
            queryset = queryset.order_by('name')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filter options
        categories = Career.objects.values_list('category', flat=True).distinct()
        demand_levels = Career.objects.values_list('kenyan_market_demand', flat=True).distinct()

        # Get student's personality type for filtering
        personality_type = None
        try:
            student = self.request.user.studentprofile
            assessment_result = student.assessmentresult
            personality_type = assessment_result.personality_type
        except:
            pass

        context.update({
            'categories': sorted(set(categories)),
            'demand_levels': sorted(set(demand_levels)),
            'personality_type': personality_type,
            'current_filters': {
                'category': self.request.GET.get('category', ''),
                'demand': self.request.GET.get('demand', ''),
                'min_salary': self.request.GET.get('min_salary', ''),
                'max_salary': self.request.GET.get('max_salary', ''),
                'personality_match': self.request.GET.get('personality_match', ''),
                'search': self.request.GET.get('search', ''),
                'sort_by': self.request.GET.get('sort_by', 'name')
            },
            'total_careers': Career.objects.count(),
            'high_demand_count': Career.objects.filter(kenyan_market_demand__in=['very_high', 'high']).count(),
            'avg_salary': Career.objects.aggregate(Avg('average_salary'))['average_salary__avg'] or 0
        })

        if 'demand_choices' not in context:
            context['demand_choices'] = [
                ('very_high', 'Very High',  'bg-red-100 text-red-700'),
                ('high',      'High',       'bg-orange-100 text-orange-700'),
                ('medium',    'Medium',     'bg-blue-100 text-blue-700'),
                ('low',       'Low',        'bg-gray-100 text-gray-600'),
            ]
        return context

class SubjectListView(LoginRequiredMixin, ListView):
    """View to browse available subjects with recommendations"""
    model = Subject
    template_name = 'recommendations/subject_list.html'
    context_object_name = 'subjects'

    def get_queryset(self):
        return Subject.objects.annotate(
            career_count=Count('careers_requiring')
        ).order_by('-career_count', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.studentprofile

        # Get subject recommendations for this student
        try:
            subject_recommender = SubjectRecommender(student)
            recommended_subjects = subject_recommender.recommend_subjects()

            # Get detailed subject information
            subject_details = []
            for subject in self.object_list:
                is_recommended = subject in recommended_subjects

                # Get careers requiring this subject
                requiring_careers = Career.objects.filter(
                    Q(required_subjects=subject) | Q(recommended_subjects=subject)
                ).distinct()[:5]

                # Get match reasons if recommended
                match_reasons = []
                if is_recommended:
                    try:
                        match_reasons = subject_recommender.get_subject_match_reasons(subject)
                    except:
                        pass

                subject_details.append({
                    'subject': subject,
                    'is_recommended': is_recommended,
                    'career_count': subject.career_count,
                    'requiring_careers': requiring_careers,
                    'match_reasons': match_reasons
                })

            context['subject_details'] = subject_details
            context['recommended_subjects'] = recommended_subjects

        except Exception as e:
            print(f"Error getting subject recommendations: {e}")
            context['subject_details'] = []
            context['recommended_subjects'] = []

        # Get student's current subjects
        try:
            student_subjects = list(student.subjects.values_list('name', flat=True))
            context['student_subjects'] = student_subjects
        except:
            context['student_subjects'] = []

        return context

# ==================== AJAX/API VIEWS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_career_interest(request, career_id):
    """Save user interest in a career"""
    try:
        career = Career.objects.get(id=career_id)
        student = request.user.studentprofile

        # Update or create recommendation with interest flag
        recommendation, created = StudentRecommendation.objects.update_or_create(
            student=student,
            career=career,
            defaults={
                'is_interested': True,
                'interest_level': request.data.get('interest_level', 5)  # 1-10 scale
            }
        )

        return Response({
            'success': True,
            'message': 'Career interest saved',
            'is_interested': recommendation.is_interested
        })

    except Career.DoesNotExist:
        return Response(
            {'error': 'Career not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compare_careers(request):
    """Compare multiple careers side by side"""
    career_ids = request.data.get('career_ids', [])

    if not career_ids or len(career_ids) > 5:
        return Response(
            {'error': 'Please select 1-5 careers to compare'},
            status=status.HTTP_400_BAD_REQUEST
        )

    careers = Career.objects.filter(id__in=career_ids).prefetch_related(
        'required_subjects', 'recommended_subjects'
    )

    comparison_data = []
    student = request.user.studentprofile
    engine = RecommendationEngine(student)

    for career in careers:
        # Calculate scores
        personality_score = engine.calculate_personality_match_score(career)
        academic_score = engine.calculate_academic_match_score(career)
        market_score = engine.calculate_market_demand_score(career)
        learning_score = engine.calculate_learning_style_score(career)
        grade_boost = engine.calculate_grade_level_boost(career)

        overall_score = (
            personality_score * 0.40 +
            academic_score * 0.30 +
            market_score * 0.20 +
            learning_score * 0.10
        ) + grade_boost

        comparison_data.append({
            'career': CareerSerializer(career).data,
            'scores': {
                'overall': round(overall_score * 100, 1),
                'personality': round(personality_score * 100, 1),
                'academic': round(academic_score * 100, 1),
                'market': round(market_score * 100, 1),
                'learning_style': round(learning_score * 100, 1)
            },
            'details': {
                'salary': career.average_salary,
                'market_demand': career.get_kenyan_market_demand_display(),
                'education_required': career.education_requirements,
                'required_subjects': list(career.required_subjects.values_list('name', flat=True)),
                'recommended_subjects': list(career.recommended_subjects.values_list('name', flat=True))
            }
        })

    return Response(comparison_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def career_path_suggestions(request, career_id):
    """Get learning path suggestions for a specific career"""
    try:
        career = Career.objects.get(id=career_id)
        student = request.user.studentprofile

        engine = RecommendationEngine(student)

        # Generate learning path
        learning_path = engine._generate_learning_path_suggestions(career, student)

        # Get resource recommendations
        from ai_coach.services import AICoachService
        coach = AICoachService(student)
        resources = coach.generate_resource_recommendations_for_career(career)

        return Response({
            'career': career.name,
            'learning_path': learning_path,
            'resources': resources,
            'next_steps': [
                'Research universities offering this program',
                'Talk to professionals in this field',
                'Take related online courses',
                'Develop required skills through projects'
            ]
        })

    except Career.DoesNotExist:
        return Response(
            {'error': 'Career not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendation_analytics(request):
    """Get analytics about recommendations"""
    student = request.user.studentprofile

    # Get all recommendations
    recommendations = StudentRecommendation.objects.filter(
        student=student
    ).select_related('career')

    if not recommendations.exists():
        return Response({
            'message': 'No recommendations yet. Generate recommendations first.'
        })

    # Calculate analytics
    analytics = {
        'distribution': {
            'by_category': dict(recommendations.values_list('career__category').annotate(count=Count('id'))),
            'by_compatibility': {
                'high': recommendations.filter(overall_score__gte=0.7).count(),
                'medium': recommendations.filter(overall_score__gte=0.5, overall_score__lt=0.7).count(),
                'low': recommendations.filter(overall_score__lt=0.5).count()
            }
        },
        'stats': {
            'total': recommendations.count(),
            'avg_score': recommendations.aggregate(avg=Avg('overall_score'))['avg'],
            'highest_score': recommendations.order_by('-overall_score').first().overall_score,
            'most_popular_category': recommendations.values_list('career__category').annotate(
                count=Count('id')
            ).order_by('-count').first()
        },
        'top_recommendations': [
            {
                'career': rec.career.name,
                'score': rec.overall_score,
                'category': rec.career.category,
                'market_demand': rec.career.kenyan_market_demand
            }
            for rec in recommendations.order_by('-overall_score')[:5]
        ]
    }

    return Response(analytics)

# Add to recommendations/views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ml_enhanced_recommendations(request):
    """Get ML-enhanced recommendations"""
    student = request.user.studentprofile

    try:
        engine = MLEnhancedRecommendationEngine(student)
        recommendations = engine.generate_enhanced_recommendations(top_n=10)

        serialized_recommendations = []
        for rec in recommendations:
            serialized_recommendations.append({
                'career': CareerSerializer(rec['career']).data,
                'overall_score': rec['overall_score'],
                'base_score': rec['base_score'],
                'success_probability': rec['success_probability'],
                'future_demand': rec['future_demand'],
                'reasoning': rec['reasoning'],
                'optimized_learning_path': rec['optimized_learning_path']
            })

        return Response(serialized_recommendations)
    except Exception as e:
        return Response(
            {'error': f'Error generating ML-enhanced recommendations: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ml_analytics(request):
    """Get ML analytics insights"""
    student = request.user.studentprofile
    analyzer = MarketTrendAnalyzer()

    # Get personal trends
    from django.db.models.functions import TruncMonth
    from django.db.models import Count, Avg

    personal_trends = StudentRecommendation.objects.filter(
        student=student
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id'),
        avg_score=Avg('overall_score')
    ).order_by('-month')[:6]

    # Get market trends
    market_trends = analyzer.analyze_career_trends()

    # Get top recommendations with ML insights
    from .ml_models import CareerSuccessPredictor
    predictor = CareerSuccessPredictor()

    recommendations = StudentRecommendation.objects.filter(
        student=student
    ).select_related('career').order_by('-overall_score')[:5]

    ml_insights = []
    for rec in recommendations:
        success_prob = predictor.predict_success_probability(student, rec.career)
        ml_insights.append({
            'career': rec.career.name,
            'compatibility': float(rec.overall_score),
            'success_probability': success_prob,
            'risk_level': 'low' if success_prob >= 0.7 else 'medium' if success_prob >= 0.5 else 'high'
        })

    return Response({
        'personal_trends': list(personal_trends),
        'market_trends': market_trends,
        'ml_insights': ml_insights,
        'recommendation_count': StudentRecommendation.objects.filter(student=student).count(),
        'avg_compatibility': StudentRecommendation.objects.filter(
            student=student
        ).aggregate(avg=Avg('overall_score'))['avg'] or 0
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def adaptive_assessment(request):
    """Get adaptive assessment configuration"""
    student = request.user.studentprofile

    # Get previous assessment responses
    from assessments.models import AssessmentResponse
    previous_responses = AssessmentResponse.objects.filter(
        student=student
    ).values('question', 'response_time', 'is_correct')[:10]

    # Use adaptive system
    from .ml_models import AdaptiveAssessmentSystem
    adapter = AdaptiveAssessmentSystem()
    assessment_config = adapter.adapt_assessment(list(previous_responses))

    return Response({
        'student_level': assessment_config,
        'previous_attempts': len(previous_responses),
        'recommended_approach': _get_recommended_approach(assessment_config)
    })

def _get_recommended_approach(config):
    """Get recommended approach based on assessment config"""
    if config['question_difficulty'] == 'high':
        return {
            'difficulty': 'Advanced',
            'focus': 'Complex problem-solving and critical thinking',
            'time_management': 'Focus on quality over quantity'
        }
    elif config['question_difficulty'] == 'medium':
        return {
            'difficulty': 'Standard',
            'focus': 'Balanced mix of knowledge and application',
            'time_management': 'Pace yourself evenly'
        }
    else:
        return {
            'difficulty': 'Foundation',
            'focus': 'Building core concepts and fundamentals',
            'time_management': 'Take your time to understand each concept'
        }

# ==================== PUBLIC VIEWS ====================

class PublicCareerListView(ListView):
    """Public view to browse careers (no login required)"""
    model = Career
    template_name = 'recommendations/public_career_list.html'
    context_object_name = 'careers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Career.objects.filter(is_active=True).prefetch_related(
            'required_subjects'
        ).order_by('name')

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_careers'] = Career.objects.filter(is_active=True).count()
        context['top_careers'] = Career.objects.filter(
            is_active=True, kenyan_market_demand__in=['very_high', 'high']
        )[:10]
        return context

class PublicCareerDetailView(DetailView):
    """Public view for career details (no login required)"""
    model = Career
    template_name = 'recommendations/public_career_detail.html'
    context_object_name = 'career'

    def get_queryset(self):
        return Career.objects.filter(is_active=True).prefetch_related(
            'required_subjects', 'recommended_subjects'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get related careers
        related_careers = Career.objects.filter(
            Q(category=self.object.category) |
            Q(required_subjects__in=self.object.required_subjects.all())
        ).distinct().exclude(id=self.object.id).filter(is_active=True)[:6]

        context['related_careers'] = related_careers
        return context

class CareerComparisonView(LoginRequiredMixin, TemplateView):
    """View for comparing multiple careers side by side"""
    template_name = 'recommendations/career_comparison.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.studentprofile

        # Get career IDs from query parameters
        career_ids = self.request.GET.getlist('career_ids')
        careers = Career.objects.filter(id__in=career_ids).prefetch_related(
            'required_subjects', 'recommended_subjects'
        )

        # Calculate compatibility scores for each career
        engine = RecommendationEngine(student)
        comparison_data = []

        for career in careers:
            personality_score = engine.calculate_personality_match_score(career)
            academic_score = engine.calculate_academic_match_score(career)
            market_score = engine.calculate_market_demand_score(career)
            learning_score = engine.calculate_learning_style_score(career)
            grade_boost = engine.calculate_grade_level_boost(career)

            overall_score = (
                personality_score * 0.40 +
                academic_score * 0.30 +
                market_score * 0.20 +
                learning_score * 0.10
            ) + grade_boost

            comparison_data.append({
                'career': career,
                'overall_score': overall_score,
                'personality_score': personality_score,
                'academic_score': academic_score,
                'market_score': market_score,
                'learning_score': learning_score,
                'salary': career.average_salary,
                'demand': career.get_kenyan_market_demand_display(),
                'required_subjects': list(career.required_subjects.values_list('name', flat=True))
            })

        context.update({
            'careers': careers,
            'comparison_data': comparison_data,
            'student': student
        })
        return context

class LearningPathView(LoginRequiredMixin, DetailView):
    """View for displaying learning path for a career"""
    model = Career
    template_name = 'recommendations/learning_path.html'
    context_object_name = 'career'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.studentprofile

        # Generate learning path using RecommendationEngine
        engine = RecommendationEngine(student)
        learning_path = engine.generate_learning_path(self.object, student)

        # Get student's current subjects
        student_subjects = list(student.subjects.values_list('name', flat=True))

        # Get recommended resources
        from ai_coach.services import AICoachService
        coach = AICoachService(student)
        resources = coach.generate_resource_recommendations_for_career(self.object)

        context.update({
            'learning_path': learning_path,
            'student_subjects': student_subjects,
            'resources': resources,
            'engine': engine
        })
        return context

class RecommendationAnalyticsDashboard(LoginRequiredMixin, TemplateView):
    """View for recommendation analytics dashboard"""
    template_name = 'recommendations/analytics_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.studentprofile

        # Get all recommendations for this student
        recommendations = StudentRecommendation.objects.filter(
            student=student
        ).select_related('career').order_by('-created_at')

        # Calculate statistics
        total_recommendations = recommendations.count()
        if total_recommendations > 0:
            avg_score = recommendations.aggregate(models.Avg('overall_score'))['overall_score__avg']
            high_match = recommendations.filter(overall_score__gte=0.7).count()
            medium_match = recommendations.filter(overall_score__gte=0.5, overall_score__lt=0.7).count()
            low_match = recommendations.filter(overall_score__lt=0.5).count()
        else:
            avg_score = 0
            high_match = medium_match = low_match = 0

        # Get category distribution
        category_distribution = recommendations.values('career__category').annotate(
            count=models.Count('id'),
            avg_score=models.Avg('overall_score')
        ).order_by('-count')

        # Get market demand distribution
        market_distribution = recommendations.values('career__kenyan_market_demand').annotate(
            count=models.Count('id')
        ).order_by('-count')

        # Get time-based trends
        from django.utils import timezone
        from django.db.models.functions import TruncMonth

        monthly_trends = recommendations.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=models.Count('id'),
            avg_score=models.Avg('overall_score')
        ).order_by('month')[:12]

        context.update({
            'student': student,
            'recommendations': recommendations[:10],
            'total_recommendations': total_recommendations,
            'avg_score': avg_score,
            'high_match': high_match,
            'medium_match': medium_match,
            'low_match': low_match,
            'category_distribution': category_distribution,
            'market_distribution': market_distribution,
            'monthly_trends': monthly_trends,
            'has_recommendations': total_recommendations > 0
        })
        return context

# Add to recommendations/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_ml_models(request):
    """Train ML models (admin only)"""
    # Check if user is admin
    if not request.user.is_staff:
        return Response(
            {'error': 'Only administrators can train models'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        from .management.commands.train_ml_models import Command
        cmd = Command()

        # Run training
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            cmd.handle(model='all')

        output = f.getvalue()

        return Response({
            'success': True,
            'message': 'ML models trained successfully',
            'output': output
        })
    except Exception as e:
        return Response(
            {'error': f'Error training models: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Add these ViewSets to recommendations/views.py after the existing ViewSets

class CareerLearningStyleViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for career-learning style matches"""
    serializer_class = CareerLearningStyleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = CareerLearningStyle.objects.select_related(
            'career', 'learning_style'
        ).all()

        learning_style = self.request.query_params.get('learning_style')
        if learning_style:
            queryset = queryset.filter(learning_style__name=learning_style)

        min_score = self.request.query_params.get('min_score')
        if min_score:
            queryset = queryset.filter(match_score__gte=min_score)

        return queryset.order_by('-match_score')

class CareerLearningStyleSerializer(serializers.ModelSerializer):
    """Serializer for CareerLearningStyle model"""
    career = CareerSerializer(read_only=True)
    learning_style = LearningStyleSerializer(read_only=True)

    class Meta:
        model = CareerLearningStyle
        fields = ['id', 'career', 'learning_style', 'match_score', 'reasoning',
                  'learning_requirements', 'adaptation_tips']
        read_only_fields = fields

class RecommendationAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for recommendation analytics"""
    serializer_class = RecommendationAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RecommendationAnalytics.objects.filter(
            student=self.request.user.studentprofile
        )

    @action(detail=False, methods=['get'])
    def update_stats(self, request):
        """Update analytics statistics"""
        student = request.user.studentprofile

        # Get or create analytics object
        analytics, created = RecommendationAnalytics.objects.get_or_create(
            student=student
        )

        # Update statistics
        analytics.update_statistics()

        serializer = self.get_serializer(analytics)
        return Response(serializer.data)

# ==================== MISSING VIEW FUNCTIONS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def career_compatibility_score(request, career_id):
    """Get compatibility score for a specific career"""
    try:
        career = Career.objects.get(id=career_id)
        student_profile = request.user.studentprofile

        engine = RecommendationEngine(student_profile)

        # Calculate individual scores
        personality_score = engine.calculate_personality_match_score(career)
        academic_score = engine.calculate_academic_match_score(career)
        market_score = engine.calculate_market_demand_score(career)
        learning_score = engine.calculate_learning_style_score(career)
        grade_boost = engine.calculate_grade_level_boost(career)

        # Overall score
        overall_score = (
            personality_score * 0.40 +
            academic_score * 0.30 +
            market_score * 0.20 +
            learning_score * 0.10
        ) + grade_boost

        overall_score = max(0, min(1, overall_score))  # Ensure 0-1 range

        return Response({
            'career': CareerSerializer(career).data,
            'scores': {
                'overall': round(overall_score * 100, 1),
                'personality': round(personality_score * 100, 1),
                'academic': round(academic_score * 100, 1),
                'market': round(market_score * 100, 1),
                'learning_style': round(learning_score * 100, 1),
                'grade_boost': round(grade_boost * 100, 1)
            },
            'reasoning': engine.generate_reasoning(
                career, personality_score, academic_score,
                market_score, learning_score, overall_score
            )
        })
    except Career.DoesNotExist:
        return Response(
            {'error': 'Career not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def career_learning_path(request, career_id):
    """Get learning path for a specific career"""
    try:
        career = Career.objects.get(id=career_id)
        student_profile = request.user.studentprofile

        engine = RecommendationEngine(student_profile)
        learning_path = engine.generate_learning_path(career, student_profile)

        return Response({
            'career': CareerSerializer(career).data,
            'learning_path': learning_path
        })
    except Career.DoesNotExist:
        return Response(
            {'error': 'Career not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def career_resources(request, career_id):
    """Get resources for a specific career"""
    try:
        career = Career.objects.get(id=career_id)

        resources = {
            'career': CareerSerializer(career).data,
            'kenyan_resources': {
                'universities': career.kenyan_universities,
                'scholarships': career.scholarships_available,
                'employers': career.top_employers
            },
            'online_resources': [
                {'name': 'Online courses', 'url': '#', 'description': 'Coursera, edX, Udemy'},
                {'name': 'Professional bodies', 'url': '#', 'description': 'Kenyan professional associations'},
                {'name': 'Industry reports', 'url': '#', 'description': 'Kenyan market analysis'}
            ]
        }

        return Response(resources)
    except Career.DoesNotExist:
        return Response(
            {'error': 'Career not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_subjects(request):
    """Get recommended subjects for current user"""
    student_profile = request.user.studentprofile

    try:
        subject_recommender = SubjectRecommender(student_profile)
        recommended = subject_recommender.recommend_subjects()

        # Get subject objects
        subjects = Subject.objects.filter(name__in=recommended)

        subject_data = []
        for subject in subjects:
            subject_data.append({
                'subject': SubjectSerializer(subject).data,
                'is_recommended': True,
                'match_reasons': subject_recommender.get_subject_match_reasons(subject),
                'career_relevance': subject.career_count,
                'difficulty_assessment': subject.get_difficulty_level_display()
            })

        return Response(subject_data)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendation_analytics(request):
    """Get analytics about recommendations"""
    student = request.user.studentprofile

    # Get all recommendations
    recommendations = StudentRecommendation.objects.filter(
        student=student
    ).select_related('career')

    if not recommendations.exists():
        return Response({
            'message': 'No recommendations yet. Generate recommendations first.'
        })

    # Calculate analytics
    analytics = {
        'distribution': {
            'by_category': dict(recommendations.values_list('career__category').annotate(count=Count('id'))),
            'by_compatibility': {
                'high': recommendations.filter(overall_score__gte=0.7).count(),
                'medium': recommendations.filter(overall_score__gte=0.5, overall_score__lt=0.7).count(),
                'low': recommendations.filter(overall_score__lt=0.5).count()
            }
        },
        'stats': {
            'total': recommendations.count(),
            'avg_score': recommendations.aggregate(avg=Avg('overall_score'))['avg'],
            'highest_score': recommendations.order_by('-overall_score').first().overall_score,
            'most_popular_category': recommendations.values_list('career__category').annotate(
                count=Count('id')
            ).order_by('-count').first()
        },
        'top_recommendations': [
            {
                'career': rec.career.name,
                'score': rec.overall_score,
                'category': rec.career.category,
                'market_demand': rec.career.kenyan_market_demand
            }
            for rec in recommendations.order_by('-overall_score')[:5]
        ]
    }

    return Response(analytics)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def regenerate_recommendations(request):
    """Regenerate recommendations for current user"""
    student_profile = request.user.studentprofile

    try:
        engine = RecommendationEngine(student_profile)
        recommendations = engine.generate_career_recommendations(top_n=15, save_to_db=True)

        serializer = CareerRecommendationSerializer(recommendations, many=True)
        return Response({
            'success': True,
            'message': f'Generated {len(recommendations)} recommendations',
            'recommendations': serializer.data
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_career_interest(request, career_id):
    """Track user interest in a career"""
    try:
        career = Career.objects.get(id=career_id)
        student = request.user.studentprofile

        # Get or create recommendation
        recommendation, created = StudentRecommendation.objects.get_or_create(
            student=student,
            career=career
        )

        # Update interest
        recommendation.is_interested = True
        recommendation.interest_level = request.data.get('interest_level', 5)
        recommendation.save()

        # Update career interest count
        career.interest_count = StudentRecommendation.objects.filter(
            career=career, is_interested=True
        ).count()
        career.save()

        return Response({
            'success': True,
            'is_interested': True,
            'interest_level': recommendation.interest_level
        })
    except Career.DoesNotExist:
        return Response(
            {'error': 'Career not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def career_market_stats(request):
    """Get market statistics for careers"""
    stats = {
        'total_careers': Career.objects.count(),
        'by_demand': dict(Career.objects.values_list('kenyan_market_demand').annotate(count=Count('id'))),
        'by_category': dict(Career.objects.values_list('category').annotate(count=Count('id'))),
        'avg_salary': Career.objects.aggregate(Avg('average_salary'))['average_salary__avg'] or 0,
        'highest_paying': Career.objects.order_by('-average_salary').values('name', 'average_salary')[:5],
        'most_in_demand': Career.objects.filter(
            kenyan_market_demand__in=['very_high', 'high']
        ).values('name', 'kenyan_market_demand')[:10]
    }

    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def career_filter_options(request):
    """Get filter options for careers"""
    options = {
        'categories': sorted(set(Career.objects.values_list('category', flat=True).distinct())),
        'demand_levels': sorted(set(Career.objects.values_list('kenyan_market_demand', flat=True).distinct())),
        'complexity_levels': sorted(set(Career.objects.values_list('complexity_level', flat=True).distinct())),
        'salary_ranges': [
            {'label': 'KES 0-50,000', 'min': 0, 'max': 50000},
            {'label': 'KES 50,001-100,000', 'min': 50001, 'max': 100000},
            {'label': 'KES 100,001-200,000', 'min': 100001, 'max': 200000},
            {'label': 'KES 200,001+', 'min': 200001, 'max': None}
        ]
    }

    return Response(options)

# ==================== TEMPLATE VIEWS ====================

class MarketTrendsView(TemplateView):
    """View for market trends"""
    template_name = 'recommendations/market_trends.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        analyzer = MarketTrendAnalyzer()
        trends = analyzer.analyze_career_trends()

        context.update({
            'market_trends': trends,
            'top_growing': sorted(trends.items(), key=lambda x: x[1].get('growth_rate', 0), reverse=True)[:5],
            'top_demand': Career.objects.filter(
                kenyan_market_demand__in=['very_high', 'high']
            ).order_by('-recommendation_count')[:10]
        })
        return context


class SubjectRecommendationForCampusView(LoginRequiredMixin, TemplateView):
    template_name = 'recommendations/subject_recommendations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.studentprofile
        recommender = SubjectRecommender(student)
        recommended = recommender.recommend_subjects()
        
        # For campus: recommend based on chosen career (if any) or general
        chosen_career_id = self.request.GET.get('career')
        if chosen_career_id:
            career = get_object_or_404(Career, id=chosen_career_id)
            subjects_for_career = CareerSubject.objects.filter(career=career).select_related('subject')
            context['career_specific'] = subjects_for_career
            context['chosen_career'] = career
        
        context['recommended_subjects'] = recommended
        return context