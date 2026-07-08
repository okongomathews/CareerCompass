# career_compass/ai/career_coach_model.py
"""
Career Coach AI Model - Custom-trained model for personalized career guidance
"""
import numpy as np
import pandas as pd
import pickle
import json
from typing import Dict, List, Tuple, Optional
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class CareerCoachDataset:
    """Dataset handler for career coaching data"""
    
    def __init__(self):
        self.data = None
        self.features = None
        self.labels = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def load_sample_data(self):
        """Load sample career data for initial training"""
        # Sample career paths for Kenya context
        sample_data = {
            'age': [22, 25, 30, 28, 35, 24, 27, 32, 29, 26],
            'education_level': ['Bachelors', 'Masters', 'Bachelors', 'PhD', 'Diploma', 
                               'Bachelors', 'Masters', 'Diploma', 'Bachelors', 'Masters'],
            'years_experience': [0, 2, 5, 3, 10, 1, 4, 8, 3, 2],
            'skills': ['Python,SQL', 'Java,Spring', 'Python,ML,DL', 'Research,Data Analysis',
                      'Management,Leadership', 'JavaScript,React', 'Python,Django',
                      'Project Management', 'Data Science,R', 'Java,Microservices'],
            'interests': ['Technology', 'Finance', 'Research', 'Education', 'Management',
                         'Design', 'Startups', 'Consulting', 'AI', 'Cloud'],
            'industry_preference': ['Tech', 'Banking', 'Academia', 'Education', 'Corporate',
                                   'Tech', 'Startup', 'Consulting', 'Tech', 'Fintech'],
            'salary_expectation': [50000, 80000, 150000, 120000, 250000, 60000, 90000,
                                  180000, 100000, 85000],
            'location_preference': ['Nairobi', 'Mombasa', 'Nairobi', 'Kisumu', 'Nairobi',
                                   'Remote', 'Nairobi', 'Remote', 'Nairobi', 'Mombasa'],
            'career_path': ['Software Engineer', 'Java Developer', 'Data Scientist',
                           'Researcher', 'Manager', 'Frontend Developer', 'Backend Developer',
                           'Project Manager', 'Data Analyst', 'Software Architect']
        }
        
        self.data = pd.DataFrame(sample_data)
        return self.data
    
    def preprocess_features(self):
        """Preprocess features for model training"""
        if self.data is None:
            raise ValueError("Data not loaded. Call load_sample_data() first.")
        
        # Encode categorical features
        categorical_cols = ['education_level', 'location_preference', 'industry_preference']
        for col in categorical_cols:
            le = LabelEncoder()
            self.data[col] = le.fit_transform(self.data[col])
            self.label_encoders[col] = le
        
        # Process skills (convert to binary features)
        all_skills = set()
        for skills_str in self.data['skills']:
            skills = [s.strip() for s in skills_str.split(',')]
            all_skills.update(skills)
        
        for skill in all_skills:
            self.data[f'skill_{skill}'] = self.data['skills'].apply(
                lambda x: 1 if skill in x else 0
            )
        
        # Process interests similarly
        for interest in set(self.data['interests']):
            self.data[f'interest_{interest}'] = self.data['interests'].apply(
                lambda x: 1 if interest == x else 0
            )
        
        # Select features
        feature_cols = ['age', 'education_level', 'years_experience', 'salary_expectation',
                       'location_preference', 'industry_preference']
        feature_cols += [f'skill_{skill}' for skill in all_skills]
        feature_cols += [f'interest_{interest}' for interest in set(self.data['interests'])]
        
        self.features = self.data[feature_cols].values
        self.features = self.scaler.fit_transform(self.features)
        
        # Encode labels (career paths)
        self.label_encoder = LabelEncoder()
        self.labels = self.label_encoder.fit_transform(self.data['career_path'])
        
        return self.features, self.labels


class CareerCoachModel(nn.Module):
    """Neural Network model for career path prediction"""
    
    def __init__(self, input_size, hidden_size, output_size):
        super(CareerCoachModel, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, output_size)
        )
        
    def forward(self, x):
        return self.network(x)


class AICareerCoach:
    """Main AI Career Coach Class"""
    
    def __init__(self):
        self.dataset = CareerCoachDataset()
        self.model = None
        self.is_trained = False
        self.career_paths = []
        
    def train_model(self, epochs=100, learning_rate=0.001):
        """Train the career coach model"""
        print("Loading and preprocessing data...")
        self.dataset.load_sample_data()
        X, y = self.dataset.preprocess_features()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Convert to PyTorch tensors
        X_train_tensor = torch.FloatTensor(X_train)
        y_train_tensor = torch.LongTensor(y_train)
        X_test_tensor = torch.FloatTensor(X_test)
        y_test_tensor = torch.LongTensor(y_test)
        
        # Initialize model
        input_size = X_train.shape[1]
        hidden_size = 64
        output_size = len(np.unique(y))
        
        self.model = CareerCoachModel(input_size, hidden_size, output_size)
        
        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        print(f"Training Career Coach AI with {epochs} epochs...")
        
        # Training loop
        for epoch in range(epochs):
            # Forward pass
            outputs = self.model(X_train_tensor)
            loss = criterion(outputs, y_train_tensor)
            
            # Backward pass and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 20 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
        
        # Test accuracy
        with torch.no_grad():
            test_outputs = self.model(X_test_tensor)
            _, predicted = torch.max(test_outputs, 1)
            accuracy = (predicted == y_test_tensor).sum().item() / y_test_tensor.size(0)
            print(f'Test Accuracy: {accuracy:.2%}')
        
        self.is_trained = True
        self.career_paths = self.dataset.label_encoder.classes_.tolist()
        
        return accuracy
    
    def predict_career_path(self, user_profile: Dict) -> Dict:
        """Predict career path for a user profile"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train_model() first.")
        
        # Prepare features from user profile
        features = self._prepare_user_features(user_profile)
        features_tensor = torch.FloatTensor(features)
        
        # Make prediction
        with torch.no_grad():
            outputs = self.model(features_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            top_probs, top_indices = torch.topk(probabilities, 3)
            
        # Get career path recommendations
        recommendations = []
        for i in range(3):
            career_path = self.career_paths[top_indices[0][i].item()]
            confidence = top_probs[0][i].item()
            
            # Get career details
            details = self._get_career_details(career_path, user_profile)
            
            recommendations.append({
                'career_path': career_path,
                'confidence': round(confidence * 100, 2),
                'details': details
            })
        
        return {
            'user_profile': user_profile,
            'recommendations': recommendations,
            'skills_gap_analysis': self._analyze_skills_gap(user_profile, recommendations[0]),
            'learning_path': self._generate_learning_path(recommendations[0], user_profile)
        }
    
    def _prepare_user_features(self, profile: Dict) -> np.ndarray:
        """Prepare user profile features for prediction"""
        # This is a simplified version - in production, this would be more comprehensive
        features = []
        
        # Numerical features
        features.append(profile.get('age', 25))
        features.append(self._encode_education(profile.get('education_level', 'Bachelors')))
        features.append(profile.get('years_experience', 2))
        features.append(profile.get('salary_expectation', 80000))
        
        # Location preference (simplified)
        locations = ['Nairobi', 'Mombasa', 'Kisumu', 'Remote']
        loc = profile.get('location_preference', 'Nairobi')
        features.append(locations.index(loc) if loc in locations else 0)
        
        # Industry preference
        industries = ['Tech', 'Banking', 'Academia', 'Education', 'Corporate', 
                     'Startup', 'Consulting', 'Fintech']
        industry = profile.get('industry_preference', 'Tech')
        features.append(industries.index(industry) if industry in industries else 0)
        
        # Skills (binary features)
        user_skills = profile.get('skills', [])
        all_skills = ['Python', 'Java', 'JavaScript', 'SQL', 'ML', 'DL', 
                     'React', 'Django', 'Spring', 'R', 'Data Science']
        for skill in all_skills:
            features.append(1 if skill in user_skills else 0)
        
        # Interests
        user_interests = profile.get('interests', [])
        all_interests = ['Technology', 'Finance', 'Research', 'Education', 
                        'Management', 'Design', 'Startups', 'Consulting', 'AI', 'Cloud']
        for interest in all_interests:
            features.append(1 if interest in user_interests else 0)
        
        return np.array(features).reshape(1, -1)
    
    def _encode_education(self, education: str) -> int:
        """Encode education level"""
        education_levels = {
            'Diploma': 1,
            'Bachelors': 2,
            'Masters': 3,
            'PhD': 4
        }
        return education_levels.get(education, 2)
    
    def _get_career_details(self, career_path: str, user_profile: Dict) -> Dict:
        """Get detailed information about a career path"""
        details = {
            'description': self._get_career_description(career_path),
            'average_salary_kes': self._get_average_salary(career_path),
            'growth_outlook': self._get_growth_outlook(career_path),
            'required_skills': self._get_required_skills(career_path),
            'companies_in_kenya': self._get_companies_in_kenya(career_path),
            'training_resources': self._get_training_resources(career_path)
        }
        return details
    
    def _get_career_description(self, career_path: str) -> str:
        """Get career description"""
        descriptions = {
            'Software Engineer': 'Design, develop, and maintain software applications. High demand in Kenya\'s growing tech ecosystem.',
            'Data Scientist': 'Analyze and interpret complex data to help companies make decisions. Growing field in Nairobi\'s tech scene.',
            'Java Developer': 'Specialize in Java-based applications. Popular in enterprise and banking sectors.',
            'Project Manager': 'Oversee projects from conception to completion. Essential in all industries.',
            'Data Analyst': 'Interpret data and provide actionable insights. Entry point into data careers.',
            'Software Architect': 'Design high-level software structures. Senior role requiring extensive experience.',
            'Frontend Developer': 'Build user interfaces and client-side applications. High demand for React/Vue developers.',
            'Backend Developer': 'Develop server-side logic and databases. Python/Django and Java/Spring are popular.'
        }
        return descriptions.get(career_path, 'A promising career path with growing opportunities in Kenya.')
    
    def _get_average_salary(self, career_path: str) -> Dict:
        """Get average salary in Kenya"""
        salaries = {
            'Software Engineer': {'entry': 80000, 'mid': 150000, 'senior': 300000},
            'Data Scientist': {'entry': 100000, 'mid': 200000, 'senior': 400000},
            'Java Developer': {'entry': 70000, 'mid': 130000, 'senior': 250000},
            'Project Manager': {'entry': 90000, 'mid': 180000, 'senior': 350000},
            'Data Analyst': {'entry': 60000, 'mid': 120000, 'senior': 220000},
            'Software Architect': {'entry': 120000, 'mid': 250000, 'senior': 500000},
            'Frontend Developer': {'entry': 65000, 'mid': 140000, 'senior': 280000},
            'Backend Developer': {'entry': 75000, 'mid': 160000, 'senior': 320000}
        }
        return salaries.get(career_path, {'entry': 50000, 'mid': 100000, 'senior': 200000})
    
    def _get_growth_outlook(self, career_path: str) -> str:
        """Get growth outlook for the career"""
        outlooks = {
            'Software Engineer': 'Very High (30% growth expected in next 5 years)',
            'Data Scientist': 'High (40% growth expected)',
            'Java Developer': 'Moderate (15% growth expected)',
            'Project Manager': 'High (25% growth expected)',
            'Data Analyst': 'Very High (35% growth expected)',
            'Software Architect': 'High (20% growth expected)',
            'Frontend Developer': 'High (30% growth expected)',
            'Backend Developer': 'High (28% growth expected)'
        }
        return outlooks.get(career_path, 'Moderate growth expected')
    
    def _get_required_skills(self, career_path: str) -> List[str]:
        """Get required skills for the career"""
        skills_map = {
            'Software Engineer': ['Python/Java', 'Git', 'Databases', 'Problem Solving', 'System Design'],
            'Data Scientist': ['Python/R', 'Statistics', 'Machine Learning', 'SQL', 'Data Visualization'],
            'Java Developer': ['Java', 'Spring Framework', 'REST APIs', 'Microservices', 'Databases'],
            'Project Manager': ['Leadership', 'Communication', 'Agile/Scrum', 'Risk Management', 'Budgeting'],
            'Data Analyst': ['Excel', 'SQL', 'Python/R', 'Data Visualization', 'Statistical Analysis'],
            'Software Architect': ['System Design', 'Cloud Architecture', 'Security', 'Scalability', 'Multiple Programming Languages'],
            'Frontend Developer': ['JavaScript', 'React/Vue/Angular', 'HTML/CSS', 'Responsive Design', 'State Management'],
            'Backend Developer': ['Python/Java/Node.js', 'API Design', 'Database Design', 'Authentication', 'Cloud Services']
        }
        return skills_map.get(career_path, ['Technical Skills', 'Problem Solving', 'Communication'])
    
    def _get_companies_in_kenya(self, career_path: str) -> List[str]:
        """Get companies hiring for this role in Kenya"""
        companies = {
            'Software Engineer': ['Safaricom', 'Andela', 'Africa\'s Talking', 'Copia', 'Twiga Foods'],
            'Data Scientist': ['Safaricom', 'IBM Africa', 'Zumi', 'Jumo', 'Branch'],
            'Java Developer': ['Equity Bank', 'KCB', 'Co-operative Bank', 'Safaricom', 'Craft Silicon'],
            'Project Manager': ['All major corporates', 'NGOs', 'Government projects', 'Construction firms'],
            'Data Analyst': ['Various startups', 'Banks', 'Telecom companies', 'E-commerce companies'],
            'Software Architect': ['Large tech companies', 'Banks', 'Telecom providers', 'Enterprise software companies'],
            'Frontend Developer': ['Tech startups', 'Digital agencies', 'E-commerce companies', 'Media companies'],
            'Backend Developer': ['Fintech companies', 'Logistics startups', 'Payment processors', 'API companies']
        }
        return companies.get(career_path, ['Various Kenyan companies'])
    
    def _get_training_resources(self, career_path: str) -> List[Dict]:
        """Get training resources for the career path"""
        resources = {
            'Software Engineer': [
                {'name': 'ALX Software Engineering', 'type': 'Bootcamp', 'duration': '12 months'},
                {'name': 'Moringa School', 'type': 'Bootcamp', 'duration': '6 months'},
                {'name': 'FreeCodeCamp', 'type': 'Online', 'duration': 'Self-paced'}
            ],
            'Data Scientist': [
                {'name': 'Africa Data School', 'type': 'Bootcamp', 'duration': '6 months'},
                {'name': 'Coursera Data Science', 'type': 'Online', 'duration': '8 months'},
                {'name': 'IBM Data Science Professional', 'type': 'Certificate', 'duration': '10 months'}
            ],
            'Java Developer': [
                {'name': 'Oracle Java Certification', 'type': 'Certification', 'duration': '3 months'},
                {'name': 'Udemy Java Masterclass', 'type': 'Online', 'duration': '60 hours'},
                {'name': 'Campus-based CS degrees', 'type': 'University', 'duration': '4 years'}
            ]
        }
        return resources.get(career_path, [
            {'name': 'Online courses on Coursera/Udemy', 'type': 'Online', 'duration': 'Varies'},
            {'name': 'University degrees in relevant fields', 'type': 'University', 'duration': '3-4 years'}
        ])
    
    def _analyze_skills_gap(self, user_profile: Dict, recommendation: Dict) -> Dict:
        """Analyze skills gap between user and recommended career"""
        user_skills = set(user_profile.get('skills', []))
        required_skills = set(recommendation['details']['required_skills'])
        
        # Simple skills gap analysis
        missing_skills = required_skills - user_skills
        existing_skills = user_skills.intersection(required_skills)
        
        return {
            'missing_skills': list(missing_skills)[:5],  # Top 5 missing skills
            'existing_skills': list(existing_skills),
            'gap_percentage': len(missing_skills) / max(len(required_skills), 1) * 100
        }
    
    def _generate_learning_path(self, recommendation: Dict, user_profile: Dict) -> Dict:
        """Generate personalized learning path"""
        career_path = recommendation['career_path']
        
        # Define learning paths based on career
        learning_paths = {
            'Software Engineer': [
                {'phase': 'Foundation', 'duration': '3 months', 
                 'topics': ['Python/Java basics', 'Git & GitHub', 'Basic algorithms']},
                {'phase': 'Web Development', 'duration': '4 months',
                 'topics': ['HTML/CSS/JavaScript', 'Framework (React/Django)', 'Databases']},
                {'phase': 'Advanced', 'duration': '5 months',
                 'topics': ['System Design', 'Cloud Deployment', 'Testing & DevOps']}
            ],
            'Data Scientist': [
                {'phase': 'Statistics & Math', 'duration': '2 months',
                 'topics': ['Probability', 'Linear Algebra', 'Statistical Analysis']},
                {'phase': 'Programming', 'duration': '3 months',
                 'topics': ['Python for Data Science', 'Pandas & NumPy', 'Data Visualization']},
                {'phase': 'Machine Learning', 'duration': '4 months',
                 'topics': ['Supervised Learning', 'Unsupervised Learning', 'Deep Learning']}
            ]
        }
        
        # Default learning path
        default_path = [
            {'phase': 'Phase 1: Foundation', 'duration': '3 months', 
             'topics': ['Basic concepts', 'Core skills', 'Fundamental knowledge']},
            {'phase': 'Phase 2: Intermediate', 'duration': '4 months',
             'topics': ['Advanced topics', 'Practical projects', 'Industry tools']},
            {'phase': 'Phase 3: Advanced', 'duration': '5 months',
             'topics': ['Specialization', 'Portfolio building', 'Interview preparation']}
        ]
        
        return {
            'career_path': career_path,
            'phases': learning_paths.get(career_path, default_path),
            'estimated_completion': '12 months',
            'resources': recommendation['details']['training_resources']
        }
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        save_data = {
            'model_state_dict': self.model.state_dict(),
            'scaler': self.dataset.scaler,
            'label_encoder': self.dataset.label_encoder,
            'career_paths': self.career_paths,
            'input_size': self.model.network[0].in_features
        }
        
        torch.save(save_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        save_data = torch.load(filepath)
        
        input_size = save_data['input_size']
        hidden_size = 64
        output_size = len(save_data['career_paths'])
        
        self.model = CareerCoachModel(input_size, hidden_size, output_size)
        self.model.load_state_dict(save_data['model_state_dict'])
        
        self.dataset.scaler = save_data['scaler']
        self.dataset.label_encoder = save_data['label_encoder']
        self.career_paths = save_data['career_paths']
        self.is_trained = True
        
        print(f"Model loaded from {filepath}")


# Utility function to initialize and train the model
def initialize_career_coach():
    """Initialize and train the AI Career Coach"""
    coach = AICareerCoach()
    accuracy = coach.train_model(epochs=50)
    coach.save_model('career_coach_model.pth')
    return coach


if __name__ == "__main__":
    # Example usage
    coach = initialize_career_coach()
    
    # Test prediction
    test_profile = {
        'age': 24,
        'education_level': 'Bachelors',
        'years_experience': 1,
        'skills': ['Python', 'SQL'],
        'interests': ['Technology', 'AI'],
        'industry_preference': 'Tech',
        'salary_expectation': 80000,
        'location_preference': 'Nairobi'
    }
    
    prediction = coach.predict_career_path(test_profile)
    print("\nCareer Recommendations:")
    for rec in prediction['recommendations']:
        print(f"- {rec['career_path']} ({rec['confidence']}% confidence)")