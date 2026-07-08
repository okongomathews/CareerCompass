# recommendations/services.py - UNIVERSAL ENHANCED VERSION
"""
Dynamic career recommendation engine with multi-factor scoring
Combines features from both versions with enhanced capabilities
"""
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.db.models import Q
from assessments.models import AssessmentResult
from .models import (
    Career, CareerPersonalityMatch, StudentRecommendation, 
    Subject, CareerSubject, CareerLearningStyle, LearningStyle
)
from users.models import StudentProfile
import math

# Import ML models at the top
try:
    from .ml_models import CareerSuccessPredictor, MarketTrendAnalyzer, PersonalizedLearningPathOptimizer
except ImportError:
    # Define placeholder classes if ml_models is not available
    class CareerSuccessPredictor:
        def predict_success_probability(self, student, career):
            return 0.5
    
    class MarketTrendAnalyzer:
        def predict_future_demand(self, career, months_ahead=6):
            return career.kenyan_market_demand
    
    class PersonalizedLearningPathOptimizer:
        def __init__(self, student):
            self.student = student
        
        def optimize_learning_path(self, career, current_path):
            return current_path

class RecommendationEngine:
    def __init__(self, student):
        self.student = student
        self.student_profile = student
        self.personality_type = None
        self.subjects = []
        self.grade_level = 0
        self.learning_style = None
        self.academic_performance = 'average'
        
        # Get personality assessment result
        try:
            self.assessment_result = student.assessmentresult
            self.personality_type = self.assessment_result.personality_type
        except AssessmentResult.DoesNotExist:
            self.assessment_result = None
        
        # Get student's subjects and academic information
        try:
            self.subjects = list(student.subjects.all())
            # Convert grade_level to integer safely
            raw_grade = student.grade_level
            try:
                self.grade_level = int(raw_grade) if raw_grade else 0
            except (ValueError, TypeError):
                self.grade_level = 0
            self.academic_performance = student.academic_performance or 'average'
        except:
            self.subjects = []
            self.grade_level = 0
        
        # Get learning style from coaching plan
        try:
            from ai_coach.models import CoachingPlan
            coaching_plan = CoachingPlan.objects.get(student=student)
            self.learning_style = coaching_plan.learning_style
        except:
            self.learning_style = None
    
    def calculate_personality_match_score(self, career):
        """Calculate personality compatibility (0-1) - ENHANCED VERSION"""
        if not self.personality_type:
            return 0.5  # Neutral if no personality assessment
        
        try:
            # Get personality match from CareerPersonalityMatch model
            match = CareerPersonalityMatch.objects.get(
                career=career,
                personality_type=self.personality_type
            )
            return float(match.match_score) / 100.0  # Convert from 0-100 to 0-1
        except CareerPersonalityMatch.DoesNotExist:
            # Fallback to trait-based calculation
            return self._calculate_based_on_traits(career)
    
    def calculate_personality_match(self, career):
        """Legacy method - for backward compatibility"""
        return self.calculate_personality_match_score(career)
    
    def _calculate_based_on_traits(self, career):
        """Calculate personality match based on MBTI traits"""
        # Enhanced trait matching with more detailed categories
        career_categories = {
            'engineering': {'preferred': ['T', 'N', 'J', 'I'], 'neutral': ['E', 'S', 'F', 'P']},
            'technology': {'preferred': ['T', 'N', 'P', 'I'], 'neutral': ['E', 'S', 'F', 'J']},
            'medicine': {'preferred': ['S', 'F', 'J', 'E'], 'neutral': ['I', 'N', 'T', 'P']},
            'healthcare': {'preferred': ['F', 'S', 'J', 'E'], 'neutral': ['T', 'N', 'I', 'P']},
            'business': {'preferred': ['E', 'T', 'J', 'S'], 'neutral': ['I', 'N', 'F', 'P']},
            'finance': {'preferred': ['T', 'S', 'J', 'I'], 'neutral': ['E', 'N', 'F', 'P']},
            'arts': {'preferred': ['N', 'F', 'P', 'I'], 'neutral': ['E', 'S', 'T', 'J']},
            'design': {'preferred': ['N', 'F', 'P', 'S'], 'neutral': ['E', 'T', 'I', 'J']},
            'education': {'preferred': ['F', 'J', 'E', 'N'], 'neutral': ['T', 'S', 'I', 'P']},
            'research': {'preferred': ['I', 'N', 'T', 'P'], 'neutral': ['E', 'S', 'F', 'J']},
            'law': {'preferred': ['T', 'J', 'E', 'S'], 'neutral': ['I', 'N', 'F', 'P']},
            'public_service': {'preferred': ['F', 'J', 'E', 'S'], 'neutral': ['I', 'N', 'T', 'P']},
        }
        
        # Determine career category
        career_category = self._categorize_career(career)
        category_info = career_categories.get(career_category, {'preferred': [], 'neutral': []})
        
        # Calculate match with weighted scoring
        match_score = 0.5  # Base score
        personality_traits = list(self.personality_type.mbti_type)
        
        # Enhanced scoring with different weights
        for trait in personality_traits:
            if trait in category_info['preferred']:
                match_score += 0.12  # Higher bonus for preferred traits
            elif trait in category_info['neutral']:
                match_score += 0.03  # Smaller bonus for neutral traits
        
        # Adjust based on specific career name patterns
        career_name = career.name.lower()
        
        # Additional adjustments for specific careers
        if 'data' in career_name or 'analyst' in career_name:
            if 'N' in personality_traits and 'T' in personality_traits:
                match_score += 0.1
        elif 'nurse' in career_name or 'care' in career_name:
            if 'F' in personality_traits:
                match_score += 0.1
        elif 'engineer' in career_name:
            if 'T' in personality_traits and ('J' in personality_traits or 'P' in personality_traits):
                match_score += 0.1
        
        return min(max(match_score, 0), 1)  # Ensure 0-1 range
    
    def calculate_academic_match_score(self, career):
        """Calculate academic compatibility based on subjects - ENHANCED"""
        if not self.subjects:
            return 0.5  # Neutral if no subjects
        
        try:
            required_subjects = CareerSubject.objects.filter(career=career, importance='required')
            recommended_subjects = CareerSubject.objects.filter(career=career, importance='recommended')
            beneficial_subjects = CareerSubject.objects.filter(career=career, importance='beneficial')
            
            student_subject_names = {s.name.lower() for s in self.subjects}
            
            # Calculate required subject match (CRITICAL)
            required_match = 0
            if required_subjects.exists():
                matches = sum(1 for rs in required_subjects 
                            if rs.subject.name.lower() in student_subject_names)
                required_match = matches / required_subjects.count()
            
            # Calculate recommended subject match (IMPORTANT)
            recommended_match = 0
            if recommended_subjects.exists():
                matches = sum(1 for rs in recommended_subjects 
                            if rs.subject.name.lower() in student_subject_names)
                recommended_match = (matches / recommended_subjects.count()) * 0.3
            
            # Calculate beneficial subject match (BONUS)
            beneficial_match = 0
            if beneficial_subjects.exists():
                matches = sum(1 for rs in beneficial_subjects 
                            if rs.subject.name.lower() in student_subject_names)
                beneficial_match = (matches / beneficial_subjects.count()) * 0.2
            
            total_match = required_match + recommended_match + beneficial_match
            
            # Adjust based on academic performance
            performance_boost = 0
            if self.academic_performance == 'excellent':
                performance_boost = 0.1
            elif self.academic_performance == 'good':
                performance_boost = 0.05
            elif self.academic_performance == 'below_average':
                performance_boost = -0.1
            
            final_score = min(total_match + performance_boost, 1.0)
            return max(final_score, 0)  # Ensure non-negative
            
        except Exception as e:
            print(f"Error calculating academic match: {e}")
            return 0.5
    
    def calculate_academic_match(self, career):
        """Legacy method - for backward compatibility"""
        score = self.calculate_academic_match_score(career)
        return score  # Return as float between 0-1
    
    def calculate_market_demand_score(self, career):
        """Convert market demand to numeric score with Kenyan context"""
        demand_mapping = {
            'very_high': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4,
            'very_low': 0.2
        }
        base_score = demand_mapping.get(career.kenyan_market_demand, 0.5)
        
        # Adjust based on growth projections and Kenyan economy
        growth_boost = 0
        if hasattr(career, 'growth_projection'):
            if '30%' in career.growth_projection or '40%' in career.growth_projection:
                growth_boost = 0.15
            elif '20%' in career.growth_projection or '25%' in career.growth_projection:
                growth_boost = 0.1
            elif '10%' in career.growth_projection or '15%' in career.growth_projection:
                growth_boost = 0.05
        
        return min(base_score + growth_boost, 1.0)
    
    def calculate_learning_style_score(self, career):
        """Match career learning requirements with student's learning style"""
        if not self.learning_style:
            return 0.5
        
        try:
            # Get learning style match from CareerLearningStyle model
            match = CareerLearningStyle.objects.get(
                career=career,
                learning_style=self.learning_style
            )
            return float(match.match_score) / 100.0
        except CareerLearningStyle.DoesNotExist:
            # Enhanced default matching
            return self._enhanced_learning_style_match(career)
    
    def _enhanced_learning_style_match(self, career):
        """Enhanced learning style matching with more detailed categories"""
        career_name = career.name.lower()
        career_category = career.category.lower() if career.category else ''
        
        # Detailed learning style to career mapping
        style_career_mapping = {
            'visual': {
                'keywords': ['design', 'art', 'architecture', 'graphic', 'web', 'ui', 'ux', 'interior', 'fashion'],
                'fields': ['Design', 'Arts', 'Architecture', 'Visual Arts', 'Graphic Design']
            },
            'auditory': {
                'keywords': ['music', 'teaching', 'counseling', 'sales', 'therapist', 'customer', 'service', 'broadcast'],
                'fields': ['Education', 'Counseling', 'Sales', 'Customer Service', 'Broadcasting']
            },
            'reading': {
                'keywords': ['research', 'writing', 'law', 'academia', 'library', 'editor', 'journalist', 'author'],
                'fields': ['Research', 'Law', 'Academia', 'Writing', 'Publishing']
            },
            'kinesthetic': {
                'keywords': ['sports', 'medicine', 'construction', 'manufacturing', 'mechanic', 'surgeon', 'dentist', 'engineer'],
                'fields': ['Medicine', 'Construction', 'Manufacturing', 'Sports', 'Engineering']
            }
        }
        
        if self.learning_style.name in style_career_mapping:
            mapping = style_career_mapping[self.learning_style.name]
            
            # Check keywords in career name
            for keyword in mapping['keywords']:
                if keyword in career_name:
                    return 0.85
            
            # Check career category/field
            for field in mapping['fields']:
                if field.lower() in career_name or field.lower() in career_category:
                    return 0.75
            
            # Check if career requires the learning style
            if self._career_requires_learning_style(career, self.learning_style.name):
                return 0.65
        
        return 0.5
    
    def _career_requires_learning_style(self, career, learning_style):
        """Check if career typically requires specific learning style"""
        # Medical careers often require kinesthetic learning
        if learning_style == 'kinesthetic' and any(word in career.name.lower() 
                                                   for word in ['doctor', 'nurse', 'surgeon', 'dentist', 'therapist']):
            return True
        
        # Design careers often require visual learning
        if learning_style == 'visual' and any(word in career.name.lower() 
                                              for word in ['designer', 'artist', 'architect', 'graphic']):
            return True
        
        # Teaching careers often require auditory learning
        if learning_style == 'auditory' and any(word in career.name.lower() 
                                                for word in ['teacher', 'professor', 'lecturer', 'trainer']):
            return True
        
        return False
    
    def calculate_grade_level_boost(self, career):
        """Adjust recommendation based on student's grade level"""
        if not self.grade_level:
            return 0

        try:
            grade = int(self.grade_level)  # ensure integer
        except (ValueError, TypeError):
            grade = 0
    
        career_complexity = self._estimate_career_complexity(career)
        
        # Enhanced grade level adjustments
        if self.grade_level >= 11:  # Form 4 & above
            if career_complexity == 'very_high':
                return 0.25
            elif career_complexity == 'high':
                return 0.15
            elif career_complexity == 'medium':
                return 0.05
        
        elif self.grade_level >= 9:  # Form 2 & 3
            if career_complexity == 'medium':
                return 0.1
            elif career_complexity == 'high':
                return -0.05
            elif career_complexity == 'very_high':
                return -0.15
        
        elif self.grade_level <= 8:  # Form 1 & below
            if career_complexity in ['high', 'very_high']:
                return -0.2
            elif career_complexity == 'medium':
                return -0.1
        
        return 0
    
    def _estimate_career_complexity(self, career):
        """Estimate career complexity based on multiple factors"""
        career_name = career.name.lower()
        
        # Very high complexity careers
        if any(word in career_name for word in ['surgeon', 'neurosurgeon', 'cardiologist', 'specialist', 'architect', 'aerospace']):
            return 'very_high'
        
        # High complexity careers
        elif any(word in career_name for word in ['doctor', 'engineer', 'lawyer', 'dentist', 'pharmacist', 'pilot']):
            return 'high'
        
        # Medium complexity careers
        elif any(word in career_name for word in ['nurse', 'teacher', 'accountant', 'analyst', 'manager', 'developer']):
            return 'medium'
        
        # Low complexity careers
        else:
            return 'low'
    
    def calculate_interests_match(self, career):
        """Calculate match based on student interests (if available)"""
        try:
            if hasattr(self.student, 'interests') and self.student.interests:
                student_interests = set(interest.lower() for interest in self.student.interests)
                
                # Map interests to career keywords
                interest_keywords = {
                    'technology': ['software', 'programming', 'coding', 'tech', 'computer', 'data', 'ai', 'cyber'],
                    'health': ['doctor', 'nurse', 'medical', 'health', 'hospital', 'medicine', 'pharmacy'],
                    'business': ['business', 'management', 'entrepreneur', 'marketing', 'sales', 'finance'],
                    'arts': ['art', 'design', 'music', 'creative', 'writing', 'drama', 'theater'],
                    'science': ['science', 'research', 'laboratory', 'physics', 'chemistry', 'biology'],
                    'education': ['teaching', 'education', 'lecturer', 'professor', 'tutor'],
                    'engineering': ['engineering', 'construction', 'mechanical', 'electrical', 'civil'],
                    'law': ['law', 'legal', 'justice', 'attorney', 'advocate']
                }
                
                match_score = 0
                for interest in student_interests:
                    if interest in interest_keywords:
                        for keyword in interest_keywords[interest]:
                            if keyword in career.name.lower() or (career.category and keyword in career.category.lower()):
                                match_score += 0.1
                                break
                
                return min(match_score, 0.3)  # Cap at 0.3 to not overpower other factors
        except:
            pass
        
        return 0
    
    def generate_career_recommendations(self, top_n=10, save_to_db=True):
        """Generate dynamic career recommendations with enhanced scoring"""
        all_careers = Career.objects.all()
        recommendations = []
        
        for career in all_careers:
            # Calculate individual scores using enhanced methods
            personality_score = self.calculate_personality_match_score(career)
            academic_score = self.calculate_academic_match_score(career)
            market_score = self.calculate_market_demand_score(career)
            learning_score = self.calculate_learning_style_score(career)
            grade_boost = self.calculate_grade_level_boost(career)
            interests_boost = self.calculate_interests_match(career)
            
            # Personality-first weighted overall score.
            # Market demand is stored on the record for display/filtering ONLY
            # — it does NOT influence compatibility.  This ensures introverted,
            # artistic, or niche-field students are not crowded out by high-demand
            # tech careers that dominate when market_score is included.
            overall_score = (
                personality_score * 0.55 +    # Personality match (55%) — primary driver
                academic_score * 0.30 +       # Academic fit (30%)
                learning_score * 0.10 +       # Learning style (10%)
                interests_boost * 0.05        # Interest alignment (5%)
            ) + grade_boost                   # Grade level adjustment (additive)
            
            # Ensure score is between 0 and 1
            overall_score = max(0, min(1, overall_score))
            
            # Generate detailed reasoning
            reasoning = self.generate_reasoning(career, personality_score, academic_score, 
                                                market_score, learning_score, overall_score)
            
            recommendations.append({
                'career': career,
                'overall_score': overall_score,
                'personality_match_score': personality_score,
                'academic_match_score': academic_score,
                'market_demand_score': market_score,
                'learning_style_score': learning_score,
                'grade_boost': grade_boost,
                'interests_boost': interests_boost,
                'reasoning': reasoning
            })
        
        # Sort by overall score
        recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
        top_recommendations = recommendations[:top_n]
        
        # Save to database if requested
        if save_to_db:
            self.save_recommendations(top_recommendations)
        
        return top_recommendations
    
    def generate_reasoning(self, career, personality_score, academic_score, 
                          market_score, learning_score, overall_score):
        """Generate human-readable reasoning for recommendation"""
        reasons = []
        
        # Personality reasoning
        if personality_score >= 0.8:
            reasons.append(f"Excellent match with your {self.personality_type.mbti_type} personality type")
        elif personality_score >= 0.7:
            reasons.append(f"Strong alignment with your {self.personality_type.mbti_type} personality")
        elif personality_score >= 0.6:
            reasons.append(f"Good compatibility with your personality traits")
        elif personality_score >= 0.5:
            reasons.append(f"Moderate personality fit")
        else:
            reasons.append(f"Personality match could be improved")
        
        # Academic reasoning
        if academic_score >= 0.9:
            reasons.append("Outstanding academic preparation for this career")
        elif academic_score >= 0.8:
            reasons.append("Excellent academic foundation")
        elif academic_score >= 0.7:
            reasons.append("Strong alignment with your current subjects")
        elif academic_score >= 0.6:
            reasons.append("Good academic match with room for improvement")
        else:
            reasons.append("Consider additional subject preparation")
        
        # Market reasoning with Kenyan context
        if market_score >= 0.8:
            reasons.append("Very high demand in the Kenyan job market")
        elif market_score >= 0.7:
            reasons.append("High growth potential in Kenya")
        elif market_score >= 0.6:
            reasons.append("Stable career opportunities in Kenya")
        elif market_score >= 0.5:
            reasons.append("Moderate market demand")
        else:
            reasons.append("Limited market opportunities - consider alternative paths")
        
        # Learning style reasoning
        if learning_score >= 0.8:
            reasons.append(f"Perfectly aligns with your {self.learning_style.name} learning style")
        elif learning_score >= 0.7:
            reasons.append(f"Strong match with your preferred learning methods")
        elif learning_score >= 0.6:
            reasons.append(f"Compatible with your learning preferences")
        
        # Add career-specific insights
        if 'tech' in career.category.lower() or 'software' in career.name.lower():
            reasons.append("Technology sector is rapidly growing in Kenya")
        elif 'health' in career.category.lower() or 'medical' in career.name.lower():
            reasons.append("Healthcare professionals are always in demand in Kenya")
        elif 'education' in career.category.lower() or 'teacher' in career.name.lower():
            reasons.append("Education sector offers stable employment in Kenya")
        
        return ". ".join(reasons) + f" (Overall compatibility: {overall_score*100:.1f}%)"
    
    def save_recommendations(self, recommendations):
        """Save recommendations to database with enhanced data"""
        for rec in recommendations:
            # Get or create the recommendation
            student_rec, created = StudentRecommendation.objects.update_or_create(
                student=self.student,
                career=rec['career'],
                defaults={
                    'personality_match_score': rec['personality_match_score'],
                    'academic_match_score': rec['academic_match_score'],
                    'overall_score': rec['overall_score'],
                    'reasoning': rec['reasoning'],
                    'market_demand_score': rec['market_demand_score'],
                    'learning_style_score': rec['learning_style_score'],
                    'grade_boost': rec['grade_boost']
                }
            )
            
            # Add recommended subjects
            try:
                # Get subjects that are required or recommended for this career
                career_subjects = CareerSubject.objects.filter(career=rec['career']).select_related('subject')
                recommended_subject_ids = [cs.subject.id for cs in career_subjects]
                student_rec.recommended_subjects.set(recommended_subject_ids)
            except:
                pass
    
    def _categorize_career(self, career):
        """Categorize career for trait matching"""
        name_lower = career.name.lower()
        category_lower = career.category.lower() if career.category else ''
        
        # Check career name
        if any(word in name_lower for word in ['engineer', 'engineering', 'mechanical', 'civil', 'electrical']):
            return 'engineering'
        elif any(word in name_lower for word in ['doctor', 'nurse', 'surgeon', 'medical', 'health', 'pharmacist']):
            return 'medicine'
        elif any(word in name_lower for word in ['business', 'manager', 'entrepreneur', 'marketing', 'sales', 'executive']):
            return 'business'
        elif any(word in name_lower for word in ['artist', 'designer', 'writer', 'musician', 'actor', 'creative']):
            return 'arts'
        elif any(word in name_lower for word in ['teacher', 'professor', 'educator', 'lecturer', 'tutor']):
            return 'education'
        elif any(word in name_lower for word in ['data', 'analyst', 'scientist', 'tech', 'software', 'developer', 'programmer']):
            return 'technology'
        elif any(word in name_lower for word in ['lawyer', 'attorney', 'legal', 'judge', 'advocate']):
            return 'law'
        elif any(word in name_lower for word in ['accountant', 'finance', 'banker', 'auditor', 'cpa']):
            return 'finance'
        elif any(word in name_lower for word in ['researcher', 'scientist', 'lab', 'physics', 'chemistry', 'biology']):
            return 'research'
        
        # Check career category as fallback
        if 'engineering' in category_lower:
            return 'engineering'
        elif 'health' in category_lower or 'medical' in category_lower:
            return 'medicine'
        elif 'business' in category_lower or 'commerce' in category_lower:
            return 'business'
        elif 'art' in category_lower or 'design' in category_lower:
            return 'arts'
        elif 'education' in category_lower or 'teaching' in category_lower:
            return 'education'
        elif 'technology' in category_lower or 'it' in category_lower:
            return 'technology'
        
        return 'general'
    
    def generate_learning_path(self, career, student):
        """Generate learning path suggestions for a specific career"""
        path = {
            'career': career.name,
            'phases': [],
            'estimated_duration': '',
            'key_milestones': []
        }
        
        # Determine complexity and create appropriate path
        complexity = self._estimate_career_complexity(career)
        
        if complexity in ['very_high', 'high']:
            path['phases'] = [
                {'phase': 'Foundation (1-2 years)', 'focus': ['KCSE preparation', 'Core subject mastery', 'Basic skills']},
                {'phase': 'Undergraduate (3-5 years)', 'focus': ['University degree', 'Internships', 'Professional skills']},
                {'phase': 'Specialization (1-3 years)', 'focus': ['Postgraduate studies', 'Certifications', 'Practical experience']},
                {'phase': 'Professional (Ongoing)', 'focus': ['Continuous learning', 'Networking', 'Career advancement']}
            ]
            path['estimated_duration'] = '5-10 years'
        else:
            path['phases'] = [
                {'phase': 'Foundation (1-2 years)', 'focus': ['KCSE preparation', 'Relevant subjects', 'Basic training']},
                {'phase': 'Training (1-3 years)', 'focus': ['College diploma', 'Vocational training', 'Internships']},
                {'phase': 'Entry-Level (1-2 years)', 'focus': ['First job', 'Skill development', 'Networking']},
                {'phase': 'Growth (Ongoing)', 'focus': ['Experience building', 'Additional certifications', 'Career progression']}
            ]
            path['estimated_duration'] = '3-5 years'
        
        # Add Kenyan-specific milestones
        path['key_milestones'] = [
            'Complete KCSE with required grades',
            'Apply through KUCCPS for relevant courses',
            'Secure university/college admission',
            'Complete internship/practical training',
            'Obtain professional certification if required',
            'Build professional network in Kenya'
        ]
        
        return path

class SubjectRecommender:
    def __init__(self, student):
        self.student = student
        try:
            self.assessment_result = AssessmentResult.objects.get(student=student)
            self.personality_type = self.assessment_result.personality_type
        except AssessmentResult.DoesNotExist:
            self.assessment_result = None
            self.personality_type = None
    
    def recommend_subjects(self):
        """Recommend subjects based on personality and career goals - ENHANCED"""
        if not self.personality_type:
            return self._get_default_subjects()
        
        # Enhanced personality-based subject preferences with Kenyan context
        personality_preferences = {
            'INTJ': {
                'core': ['Mathematics', 'Physics', 'Computer Studies'],
                'supporting': ['Chemistry', 'Business Studies', 'Geography'],
                'elective': ['Technical Drawing', 'German', 'Arabic']
            },
            'INTP': {
                'core': ['Mathematics', 'Physics', 'Computer Studies'],
                'supporting': ['Chemistry', 'Biology', 'Geography'],
                'elective': ['Agriculture', 'Home Science', 'Music']
            },
            'ENTJ': {
                'core': ['Business Studies', 'Mathematics', 'History'],
                'supporting': ['Computer Studies', 'Geography', 'CRE'],
                'elective': ['German', 'French', 'Music']
            },
            'ENTP': {
                'core': ['Computer Studies', 'Physics', 'Geography'],
                'supporting': ['Business Studies', 'History', 'CRE'],
                'elective': ['Drama', 'Music', 'Art']
            },
            'INFJ': {
                'core': ['Languages', 'History', 'Biology'],
                'supporting': ['CRE', 'Geography', 'Business Studies'],
                'elective': ['Music', 'Art', 'Home Science']
            },
            'INFP': {
                'core': ['Languages', 'Literature', 'Art'],
                'supporting': ['Music', 'History', 'Biology'],
                'elective': ['Home Science', 'CRE', 'Geography']
            },
            'ENFJ': {
                'core': ['Languages', 'History', 'Business Studies'],
                'supporting': ['CRE', 'Geography', 'Biology'],
                'elective': ['Music', 'Drama', 'Home Science']
            },
            'ENFP': {
                'core': ['Languages', 'Geography', 'Business Studies'],
                'supporting': ['Drama', 'Music', 'History'],
                'elective': ['Art', 'CRE', 'Home Science']
            },
            'ISTJ': {
                'core': ['Mathematics', 'Chemistry', 'Business Studies'],
                'supporting': ['Geography', 'Physics', 'Computer Studies'],
                'elective': ['Technical Drawing', 'Agriculture', 'Home Science']
            },
            'ISFJ': {
                'core': ['Biology', 'Home Science', 'Languages'],
                'supporting': ['CRE', 'Geography', 'Business Studies'],
                'elective': ['Music', 'Art', 'Agriculture']
            },
            'ESTJ': {
                'core': ['Business Studies', 'Mathematics', 'Geography'],
                'supporting': ['History', 'Computer Studies', 'Physics'],
                'elective': ['Technical Drawing', 'German', 'Arabic']
            },
            'ESFJ': {
                'core': ['Languages', 'Home Science', 'Business Studies'],
                'supporting': ['CRE', 'Music', 'Biology'],
                'elective': ['Art', 'Agriculture', 'Geography']
            },
            'ISTP': {
                'core': ['Physics', 'Chemistry', 'Technical Drawing'],
                'supporting': ['Computer Studies', 'Mathematics', 'Geography'],
                'elective': ['Agriculture', 'German', 'Arabic']
            },
            'ISFP': {
                'core': ['Art', 'Music', 'Home Science'],
                'supporting': ['Biology', 'Languages', 'Geography'],
                'elective': ['CRE', 'Business Studies', 'Agriculture']
            },
            'ESTP': {
                'core': ['Business Studies', 'Physical Education', 'Geography'],
                'supporting': ['Computer Studies', 'Mathematics', 'History'],
                'elective': ['Technical Drawing', 'German', 'Music']
            },
            'ESFP': {
                'core': ['Music', 'Drama', 'Business Studies'],
                'supporting': ['Languages', 'Geography', 'Home Science'],
                'elective': ['Art', 'CRE', 'Physical Education']
            }
        }
        
        # Get base subjects from personality preferences
        preferences = personality_preferences.get(self.personality_type.mbti_type, 
                                                 {'core': [], 'supporting': [], 'elective': []})
        
        base_subjects = preferences['core'] + preferences['supporting'][:2]  # Core + 2 supporting
        
        # Add career-aligned subjects
        try:
            engine = RecommendationEngine(self.student)
            career_recs = engine.generate_career_recommendations(top_n=3, save_to_db=False)
            
            career_subjects = set()
            for rec in career_recs:
                # Get required and recommended subjects for each career
                career_subjects.update(
                    rec['career'].required_subjects.values_list('name', flat=True)
                )
                career_subjects.update(
                    rec['career'].recommended_subjects.values_list('name', flat=True)
                )
        except:
            career_subjects = set()
        
        # Combine subjects with priority to personality-based ones
        all_subjects = list(set(base_subjects + list(career_subjects)))
        
        # Ensure we have a balanced mix (max 8 subjects)
        if len(all_subjects) > 8:
            # Prioritize: personality core > career required > personality supporting > career recommended
            priority_list = []
            for subject in all_subjects:
                if subject in preferences['core']:
                    priority_list.append((subject, 4))
                elif subject in career_subjects and subject in rec['career'].required_subjects.values_list('name', flat=True):
                    priority_list.append((subject, 3))
                elif subject in preferences['supporting']:
                    priority_list.append((subject, 2))
                else:
                    priority_list.append((subject, 1))
            
            priority_list.sort(key=lambda x: x[1], reverse=True)
            all_subjects = [subject for subject, _ in priority_list[:8]]
        
        return all_subjects[:8]
    
    def _get_default_subjects(self):
        """Return default subjects for students without personality assessment"""
        return [
            'Mathematics', 'English', 'Kiswahili', 'Biology',
            'Physics', 'Chemistry', 'Geography', 'History'
        ]
    
    def get_subject_match_reasons(self, subject):
        """Get reasons why a subject is recommended"""
        reasons = []
        
        # Check personality alignment
        if self.personality_type:
            personality_preferences = {
                'INTJ': ['Mathematics', 'Physics', 'Computer Studies'],
                'INTP': ['Mathematics', 'Physics', 'Computer Studies'],
                'ENTJ': ['Business Studies', 'Mathematics', 'History'],
                # ... add all personality types
            }
            
            if subject.name in personality_preferences.get(self.personality_type.mbti_type, []):
                reasons.append(f"Aligns well with your {self.personality_type.mbti_type} personality traits")
        
        # Check career alignment
        try:
            engine = RecommendationEngine(self.student)
            career_recs = engine.generate_career_recommendations(top_n=3, save_to_db=False)
            
            for rec in career_recs:
                if subject.name in rec['career'].required_subjects.values_list('name', flat=True):
                    reasons.append(f"Required for {rec['career'].name}")
                elif subject.name in rec['career'].recommended_subjects.values_list('name', flat=True):
                    reasons.append(f"Recommended for {rec['career'].name}")
        except:
            pass
        
        if not reasons:
            reasons.append("Important for general academic development")
        
        return reasons
    
    def get_subjects_for_career(self, career):
        """Get recommended subjects for a specific career"""
        subjects = []
        
        # Add required subjects
        subjects.extend(career.required_subjects.all())
        
        # Add recommended subjects (limit to 3 to avoid overwhelming)
        subjects.extend(career.recommended_subjects.all()[:3])
        
        return subjects

class AdvancedRecommendationEngine(RecommendationEngine):
    """Advanced recommendation engine with ML capabilities"""
    
    def __init__(self, student):
        super().__init__(student)
        self.career_vectors = {}
        self.student_vector = None
    
    def build_career_vectors(self):
        """Build vector representations of careers for similarity calculations"""
        careers = Career.objects.all()
        
        for career in careers:
            # Create a feature vector for each career
            vector = {
                'personality_traits': self._extract_personality_traits(career),
                'academic_requirements': self._extract_academic_requirements(career),
                'market_demand': self._market_demand_to_numeric(career.kenyan_market_demand),
                'salary_level': career.average_salary / 100000,  # Normalize
                'complexity': self._complexity_to_numeric(career)
            }
            self.career_vectors[career.id] = vector
        
        return self.career_vectors
    
    def build_student_vector(self):
        """Build vector representation of student"""
        if not self.student_vector:
            self.student_vector = {
                'personality_traits': self._extract_student_personality_traits(),
                'academic_profile': self._extract_student_academic_profile(),
                'grade_level': self.grade_level / 12,  # Normalize
                'learning_style': self._learning_style_to_numeric(),
                'interests': self._extract_student_interests()
            }
        return self.student_vector
    
    def calculate_cosine_similarity(self, career):
        """Calculate cosine similarity between student and career vectors"""
        if not self.career_vectors:
            self.build_career_vectors()
        
        if not self.student_vector:
            self.build_student_vector()
        
        # Convert vectors to arrays for similarity calculation
        career_vector = self._vector_to_array(self.career_vectors[career.id])
        student_vector = self._vector_to_array(self.student_vector)
        
        # Calculate cosine similarity
        similarity = cosine_similarity([career_vector], [student_vector])[0][0]
        
        return max(0, min(1, similarity))  # Ensure 0-1 range
    
    def generate_ml_recommendations(self, top_n=10):
        """Generate recommendations using ML similarity"""
        if not self.career_vectors:
            self.build_career_vectors()
        
        if not self.student_vector:
            self.build_student_vector()
        
        similarities = []
        for career_id, career_vector in self.career_vectors.items():
            career = Career.objects.get(id=career_id)
            
            # Calculate similarity
            similarity = self.calculate_cosine_similarity(career)
            
            # Combine with traditional scores for robustness
            traditional_score = self.calculate_academic_match_score(career) * 0.5 + \
                              self.calculate_personality_match_score(career) * 0.5
            
            combined_score = (similarity * 0.7) + (traditional_score * 0.3)
            
            similarities.append({
                'career': career,
                'ml_similarity': similarity,
                'traditional_score': traditional_score,
                'combined_score': combined_score
            })
        
        # Sort by combined score
        similarities.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Format results
        recommendations = []
        for item in similarities[:top_n]:
            recommendations.append({
                'career': item['career'],
                'overall_score': item['combined_score'],
                'ml_similarity': item['ml_similarity'],
                'traditional_score': item['traditional_score'],
                'reasoning': f"ML similarity: {item['ml_similarity']*100:.1f}%, Traditional match: {item['traditional_score']*100:.1f}%"
            })
        
        return recommendations
    
    def _extract_personality_traits(self, career):
        """Extract personality traits for a career"""
        traits = []
        
        # Get personality matches for this career
        matches = CareerPersonalityMatch.objects.filter(career=career)
        
        for match in matches:
            traits.extend(list(match.personality_type.mbti_type))
        
        # Convert to one-hot encoding-like representation
        all_traits = ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']
        trait_vector = [1 if trait in traits else 0 for trait in all_traits]
        
        return trait_vector
    
    def _extract_student_personality_traits(self):
        """Extract student's personality traits"""
        if self.personality_type:
            return [1 if trait in self.personality_type.mbti_type else 0 
                   for trait in ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']]
        return [0] * 8
    
    def _extract_academic_requirements(self, career):
        """Extract academic requirements for a career"""
        # Get required subjects and convert to vector
        all_subjects = Subject.objects.all()
        subject_names = [s.name.lower() for s in all_subjects]
        
        required_subjects = career.required_subjects.values_list('name', flat=True)
        recommended_subjects = career.recommended_subjects.values_list('name', flat=True)
        
        vector = []
        for subject in subject_names:
            if subject in [s.lower() for s in required_subjects]:
                vector.append(2)  # Required
            elif subject in [s.lower() for s in recommended_subjects]:
                vector.append(1)  # Recommended
            else:
                vector.append(0)  # Not relevant
        
        return vector
    
    def _extract_student_academic_profile(self):
        """Extract student's academic profile"""
        all_subjects = Subject.objects.all()
        subject_names = [s.name.lower() for s in all_subjects]
        
        student_subjects = [s.name.lower() for s in self.subjects]
        
        vector = []
        for subject in subject_names:
            if subject in student_subjects:
                vector.append(1)
            else:
                vector.append(0)
        
        return vector
    
    def _market_demand_to_numeric(self, demand):
        """Convert market demand to numeric value"""
        mapping = {
            'very_high': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4,
            'very_low': 0.2
        }
        return mapping.get(demand, 0.5)
    
    def _complexity_to_numeric(self, career):
        """Convert career complexity to numeric value"""
        complexity = self._estimate_career_complexity(career)
        mapping = {
            'very_high': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        return mapping.get(complexity, 0.5)
    
    def _learning_style_to_numeric(self):
        """Convert learning style to numeric vector"""
        if self.learning_style:
            styles = ['visual', 'auditory', 'reading', 'kinesthetic']
            return [1 if style == self.learning_style.name else 0 for style in styles]
        return [0.25] * 4  # Equal distribution if unknown
    
    def _extract_student_interests(self):
        """Extract student interests as vector"""
        # This would be implemented based on your interests model
        return []  # Placeholder
    
    def _vector_to_array(self, vector_dict):
        """Convert vector dictionary to flat array"""
        array = []
        
        for key, value in vector_dict.items():
            if isinstance(value, list):
                array.extend(value)
            elif isinstance(value, (int, float)):
                array.append(value)
        
        return np.array(array)

class MLEnhancedRecommendationEngine(RecommendationEngine):
    """Enhanced recommendation engine with ML capabilities"""
    
    def __init__(self, student):
        super().__init__(student)
        self.success_predictor = CareerSuccessPredictor()
        self.trend_analyzer = MarketTrendAnalyzer()
        self.path_optimizer = PersonalizedLearningPathOptimizer(student)
        
    def generate_enhanced_recommendations(self, top_n=10):
        """Generate recommendations with ML enhancements"""
        # Get base recommendations
        base_recommendations = super().generate_career_recommendations(top_n=top_n, save_to_db=True)
        
        enhanced_recommendations = []
        for rec in base_recommendations:
            career = rec['career']
            
            # Get ML predictions
            success_probability = self.success_predictor.predict_success_probability(self.student, career)
            future_demand = self.trend_analyzer.predict_future_demand(career)
            
            # Adjust score based on ML predictions
            ml_adjusted_score = rec['overall_score'] * 0.7 + success_probability * 0.3
            
            # Generate optimized learning path
            learning_path = self._generate_learning_path_suggestions(career, self.student)
            optimized_path = self.path_optimizer.optimize_learning_path(career, learning_path)
            
            enhanced_recommendations.append({
                'career': career,
                'overall_score': ml_adjusted_score,
                'base_score': rec['overall_score'],
                'success_probability': success_probability,
                'future_demand': future_demand,
                'optimized_learning_path': optimized_path,
                'reasoning': self._generate_enhanced_reasoning(
                    career, rec, success_probability, future_demand
                )
            })
        
        # Sort by enhanced score
        enhanced_recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
        return enhanced_recommendations[:top_n]
    
    def _generate_enhanced_reasoning(self, career, base_rec, success_prob, future_demand):
        """Generate enhanced reasoning with ML insights"""
        base_reasoning = base_rec['reasoning']
        
        ml_insights = []
        
        if success_prob >= 0.8:
            ml_insights.append(f"High success probability ({success_prob*100:.0f}%) based on similar student profiles")
        elif success_prob >= 0.6:
            ml_insights.append(f"Good success probability ({success_prob*100:.0f}%)")
        
        if future_demand != career.kenyan_market_demand:
            ml_insights.append(f"Expected future demand: {future_demand.replace('_', ' ').title()}")
        
        if ml_insights:
            return f"{base_reasoning}. ML Insights: {'; '.join(ml_insights)}"
        return base_reasoning