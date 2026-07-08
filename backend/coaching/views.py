# career_compass/coaching/views.py
"""
Views for AI Career Coaching
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging
from datetime import timedelta

from .models import (
    CoachingPlan, UserCoachingSubscription, CoachingSession,
    CareerGoal, ActionItem, ResourceRecommendation
)
from ai_coach.career_coach_model import AICareerCoach

logger = logging.getLogger(__name__)
ai_coach = None


def get_ai_coach():
    """Get or initialize AI coach"""
    global ai_coach
    if ai_coach is None:
        try:
            ai_coach = AICareerCoach()
            ai_coach.load_model('career_coach_model.pth')
        except:
            # If model doesn't exist, create a dummy one for development
            ai_coach = AICareerCoach()
            # In production, you would train it here
    return ai_coach


@login_required
def coaching_dashboard(request):
    """Main coaching dashboard"""
    try:
        subscription = UserCoachingSubscription.objects.filter(
            user=request.user, status='active'
        ).first()
        
        # Get upcoming sessions
        upcoming_sessions = CoachingSession.objects.filter(
            user=request.user,
            status='scheduled'
        ).order_by('scheduled_time')[:5]
        
        # Get active goals
        active_goals = CareerGoal.objects.filter(
            user=request.user,
            status='in_progress'
        ).order_by('-priority')[:3]
        
        # Get pending action items
        pending_actions = ActionItem.objects.filter(
            coaching_session__user=request.user,
            completed=False
        ).order_by('priority', 'due_date')[:5]
        
        context = {
            'subscription': subscription,
            'upcoming_sessions': upcoming_sessions,
            'active_goals': active_goals,
            'pending_actions': pending_actions,
            'plans': CoachingPlan.objects.filter(is_active=True)
        }
        
        return render(request, 'coaching/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Error loading coaching dashboard: {str(e)}")
        messages.error(request, "Error loading coaching dashboard")
        return redirect('home')


@login_required
def plan_selection(request):
    """View for selecting coaching plans"""
    plans = CoachingPlan.objects.filter(is_active=True).order_by('price_kes')
    
    # Check if user already has active subscription
    active_subscription = UserCoachingSubscription.objects.filter(
        user=request.user, status='active'
    ).first()
    
    context = {
        'plans': plans,
        'active_subscription': active_subscription,
        'page_title': 'Choose Your Coaching Plan'
    }
    
    return render(request, 'coaching/plan_selection.html', context)


@login_required
@require_POST
def subscribe_to_plan(request, plan_id):
    """Subscribe to a coaching plan"""
    try:
        plan = get_object_or_404(CoachingPlan, id=plan_id, is_active=True)
        
        # Check for existing active subscription
        existing_active = UserCoachingSubscription.objects.filter(
            user=request.user, status='active'
        ).first()
        
        if existing_active:
            messages.warning(request, "You already have an active subscription.")
            return redirect('coaching_dashboard')
        
        # Create subscription (in production, integrate with payment gateway)
        subscription = UserCoachingSubscription.objects.create(
            user=request.user,
            plan=plan,
            status='active',  # In production, this would be 'pending' until payment
            # Set end date based on duration
            # For simplicity, we'll set it to 30 days from now
            end_date=timezone.now() + timedelta(days=30)
        )
        
        messages.success(request, 
            f"Successfully subscribed to {plan.name}! You can now book coaching sessions.")
        
        # Send welcome email (implement email sending)
        
        return redirect('coaching_dashboard')
    
    except Exception as e:
        logger.error(f"Subscription error: {str(e)}")
        messages.error(request, "Error processing subscription. Please try again.")
        return redirect('plan_selection')


@login_required
def ai_coaching_chat(request):
    """AI coaching chat interface"""
    subscription = UserCoachingSubscription.objects.filter(
        user=request.user, status='active'
    ).first()
    
    if not subscription or not subscription.can_use_ai_session():
        messages.warning(request, 
            "You need an active subscription with available AI sessions.")
        return redirect('coaching_dashboard')
    
    # Get previous sessions
    previous_sessions = CoachingSession.objects.filter(
        user=request.user,
        session_type='ai'
    ).order_by('-created_at')[:10]
    
    context = {
        'subscription': subscription,
        'previous_sessions': previous_sessions,
        'ai_sessions_remaining': subscription.plan.ai_sessions_per_month - subscription.ai_sessions_used
    }
    
    return render(request, 'coaching/ai_chat.html', context)


@login_required
@csrf_exempt
@require_POST
def ai_coaching_message(request):
    """Handle AI coaching message"""
    try:
        subscription = UserCoachingSubscription.objects.filter(
            user=request.user, status='active'
        ).first()
        
        if not subscription or not subscription.can_use_ai_session():
            return JsonResponse({
                'error': 'No available AI sessions. Please upgrade your plan.'
            }, status=403)
        
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Get or create session
        if session_id:
            session = get_object_or_404(CoachingSession, id=session_id, user=request.user)
        else:
            session = CoachingSession.objects.create(
                user=request.user,
                subscription=subscription,
                session_type='ai',
                title=f"AI Coaching Session - {timezone.now().strftime('%d/%m/%Y')}",
                scheduled_time=timezone.now(),
                duration_minutes=30,
                user_input=user_message,
                status='completed'
            )
        
        # Use AI coach to generate response
        ai_coach = get_ai_coach()
        
        # Prepare user profile from session history
        user_profile = {
            'age': request.user.profile.age if hasattr(request.user, 'profile') else 25,
            'education_level': request.user.profile.education_level if hasattr(request.user, 'profile') else 'Bachelors',
            'skills': request.user.profile.skills.split(',') if hasattr(request.user, 'profile') and request.user.profile.skills else [],
            'interests': request.user.profile.interests.split(',') if hasattr(request.user, 'profile') and request.user.profile.interests else []
        }
        
        # Generate AI response
        ai_response = {
            'message': ai_coach._generate_ai_response(user_message, user_profile),
            'recommendations': [],
            'action_items': [],
            'resources': []
        }
        
        # Record session usage
        subscription.use_ai_session()
        
        # Save AI response to session
        session.ai_response = ai_response
        session.save()
        
        return JsonResponse({
            'response': ai_response,
            'session_id': session.id,
            'sessions_remaining': subscription.plan.ai_sessions_per_month - subscription.ai_sessions_used
        })
        
    except Exception as e:
        logger.error(f"AI coaching error: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
def book_human_session(request):
    """Book a session with human coach"""
    subscription = UserCoachingSubscription.objects.filter(
        user=request.user, status='active'
    ).first()
    
    if not subscription or not subscription.can_use_human_session():
        messages.warning(request, 
            "You need an active subscription with available human coaching sessions.")
        return redirect('coaching_dashboard')
    
    if request.method == 'POST':
        try:
            # Create coaching session
            session = CoachingSession.objects.create(
                user=request.user,
                subscription=subscription,
                session_type='human',
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                scheduled_time=request.POST.get('scheduled_time'),
                duration_minutes=request.POST.get('duration', 60),
                status='scheduled'
            )
            
            messages.success(request, "Session booked successfully!")
            return redirect('coaching_dashboard')
            
        except Exception as e:
            logger.error(f"Session booking error: {str(e)}")
            messages.error(request, "Error booking session. Please try again.")
    
    context = {
        'subscription': subscription,
        'human_sessions_remaining': subscription.plan.human_sessions_per_month - subscription.human_sessions_used
    }
    
    return render(request, 'coaching/book_session.html', context)


@login_required
def career_goals(request):
    """Manage career goals"""
    if request.method == 'POST':
        try:
            goal = CareerGoal.objects.create(
                user=request.user,
                goal_type=request.POST.get('goal_type'),
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                target_date=request.POST.get('target_date'),
                priority=request.POST.get('priority', 3)
            )
            
            messages.success(request, "Career goal created successfully!")
            return redirect('career_goals')
            
        except Exception as e:
            logger.error(f"Goal creation error: {str(e)}")
            messages.error(request, "Error creating goal. Please try again.")
    
    goals = CareerGoal.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'goals': goals,
        'goal_types': CareerGoal.GOAL_TYPES
    }
    
    return render(request, 'coaching/career_goals.html', context)


@login_required
def career_assessment(request):
    """AI-powered career assessment"""
    try:
        ai_coach = get_ai_coach()
        
        if request.method == 'POST':
            # Collect user data from form
            user_profile = {
                'age': int(request.POST.get('age', 25)),
                'education_level': request.POST.get('education_level'),
                'years_experience': int(request.POST.get('years_experience', 2)),
                'skills': request.POST.get('skills', '').split(','),
                'interests': request.POST.get('interests', '').split(','),
                'industry_preference': request.POST.get('industry_preference'),
                'salary_expectation': int(request.POST.get('salary_expectation', 80000)),
                'location_preference': request.POST.get('location_preference')
            }
            
            # Get AI career recommendations
            recommendations = ai_coach.predict_career_path(user_profile)
            
            # Save to user profile if exists
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                profile.career_assessment_data = recommendations
                profile.save()
            
            context = {
                'recommendations': recommendations,
                'user_profile': user_profile
            }
            
            return render(request, 'coaching/assessment_results.html', context)
        
        # GET request - show assessment form
        return render(request, 'coaching/career_assessment.html')
        
    except Exception as e:
        logger.error(f"Career assessment error: {str(e)}")
        messages.error(request, "Error processing career assessment. Please try again.")
        return redirect('coaching_dashboard')


@login_required
def generate_learning_path(request):
    """Generate personalized learning path"""
    if request.method == 'POST':
        try:
            career_path = request.POST.get('career_path')
            current_skills = request.POST.get('current_skills', '').split(',')
            
            ai_coach = get_ai_coach()
            
            # Generate learning path
            learning_path = ai_coach._generate_learning_path({
                'career_path': career_path,
                'details': {
                    'required_skills': ai_coach._get_required_skills(career_path)
                }
            }, {
                'skills': current_skills
            })
            
            context = {
                'learning_path': learning_path,
                'career_path': career_path
            }
            
            return render(request, 'coaching/learning_path.html', context)
            
        except Exception as e:
            logger.error(f"Learning path generation error: {str(e)}")
            messages.error(request, "Error generating learning path. Please try again.")
            return redirect('coaching_dashboard')
    
    return redirect('coaching_dashboard')