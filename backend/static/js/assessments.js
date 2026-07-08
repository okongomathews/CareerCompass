// static/js/assessments.js
class AssessmentEngine {
    constructor() {
        this.questions = [];
        this.currentQuestionIndex = 0;
        this.responses = new Map();
        this.sessionId = null;
        this.isSubmitting = false;
        
        this.initializeElements();
        this.loadQuestions();
    }

    initializeElements() {
        this.questionContainer = document.getElementById('question-container');
        this.loadingSpinner = document.getElementById('loading-spinner');
        this.questionText = document.getElementById('question-text');
        this.answerOptions = document.getElementById('answer-options');
        this.prevBtn = document.getElementById('prev-btn');
        this.nextBtn = document.getElementById('next-btn');
        this.finishBtn = document.getElementById('finish-btn');
        this.progressBar = document.getElementById('progress-bar');
        this.progressText = document.getElementById('progress-text');
        this.errorMessage = document.getElementById('error-message');
        this.errorText = document.getElementById('error-text');
        
        // The scrollable container for questions
        this.scrollContainer = document.getElementById('scrollable-questions');

        console.log('Elements initialized:', {
            container: !!this.questionContainer,
            scrollContainer: !!this.scrollContainer
        });

        this.bindEvents();
    }

    bindEvents() {
        this.prevBtn.addEventListener('click', () => this.previousQuestion());
        this.nextBtn.addEventListener('click', () => this.nextQuestion());
        this.finishBtn.addEventListener('click', () => this.finishAssessment());
    }

    async loadQuestions() {
        try {
            console.log('Loading questions from API...');
            this.showLoading('Loading assessment questions...');
            
            const response = await fetch('/assessments/api/questions/');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            this.questions = await response.json();
            console.log(`Loaded ${this.questions.length} questions`);
            
            if (this.questions.length === 0) throw new Error('No questions available');
            
            await this.initializeSession();
            this.hideLoading();
            this.showQuestion(0);
        } catch (error) {
            console.error('Error loading questions:', error);
            this.showError('Failed to load questions. Please refresh the page or contact support.');
        }
    }

    async initializeSession() {
        try {
            console.log('Initializing assessment session...');
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) throw new Error('CSRF token not available');
            
            const response = await fetch('/assessments/api/sessions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({}),
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, response: ${errorText}`);
            }
            
            const session = await response.json();
            this.sessionId = session.id;
            console.log('Session initialized with ID:', this.sessionId);
        } catch (error) {
            console.error('Error initializing session:', error);
            this.sessionId = 'temp-' + Date.now();
            console.log('Using temporary session ID:', this.sessionId);
        }
    }

    showQuestion(index) {
        if (index < 0 || index >= this.questions.length) {
            console.error('Invalid question index:', index);
            return;
        }

        this.currentQuestionIndex = index;
        const question = this.questions[index];

        console.log(`Showing question ${index + 1}/${this.questions.length}:`, question.id);

        this.questionText.textContent = question.text;
        this.renderAnswerOptions(question);
        this.updateProgress();
        this.updateNavigation();
        
        // Scroll the scrollable container to the top
        this.scrollToQuestionTop();
    }

    renderAnswerOptions(question) {
        this.answerOptions.innerHTML = '';

        if (!question.choices || question.choices.length === 0) {
            this.answerOptions.innerHTML = '<p class="text-red-500 text-center py-4">No answer options available for this question</p>';
            return;
        }

        question.choices.forEach(choice => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'answer-option w-full text-left p-4 border-2 border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition duration-200 cursor-pointer';
            
            if (this.responses.get(question.id) === choice.id) {
                optionDiv.classList.add('bg-blue-50', 'border-blue-300', 'selected');
            }

            optionDiv.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="flex-1 text-gray-800 text-left text-lg">${choice.text}</span>
                    <div class="flex items-center space-x-2">
                        <span class="text-xs text-gray-500 px-2 py-1 bg-gray-100 rounded">
                            Value: ${choice.value > 0 ? '+' : ''}${choice.value}
                        </span>
                        <i class="fas fa-chevron-right text-blue-500 ml-2"></i>
                    </div>
                </div>
            `;

            optionDiv.addEventListener('click', () => this.selectAnswer(question.id, choice.id));
            this.answerOptions.appendChild(optionDiv);
        });
    }

    async selectAnswer(questionId, choiceId) {
        console.log(`Selected answer for question ${questionId}: ${choiceId}`);
        
        this.responses.set(questionId, choiceId);
        
        await this.saveResponse(questionId, choiceId);
        
        // Update UI for current question (highlight selected)
        this.renderAnswerOptions(this.questions[this.currentQuestionIndex]);
        this.updateProgress();
        this.updateNavigation();
        
        // Immediately move to next question if not last
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.nextQuestion(); // This calls showQuestion, which triggers scrollToQuestionTop
        }
    }

    async saveResponse(questionId, choiceId) {
        if (!this.sessionId || this.isSubmitting) return;
        this.isSubmitting = true;
        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) throw new Error('CSRF token not available');
            
            const response = await fetch(`/assessments/api/sessions/${this.sessionId}/submit_response/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    question_id: questionId,
                    answer_id: choiceId,
                    response_time: Math.floor(Math.random() * 10) + 1
                }),
                credentials: 'same-origin'
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, response: ${errorText}`);
            }

            const result = await response.json();
            console.log('Response saved successfully:', result);
        } catch (error) {
            console.error('Error saving response:', error);
        } finally {
            this.isSubmitting = false;
        }
    }

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.showQuestion(this.currentQuestionIndex - 1);
        }
    }

    nextQuestion() {
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.showQuestion(this.currentQuestionIndex + 1);
        } else {
            this.showCompletionOptions();
        }
    }

    showCompletionOptions() {
        const answeredCount = this.responses.size;
        const totalQuestions = this.questions.length;
        const completionPercent = Math.round((answeredCount / totalQuestions) * 100);
        
        // Replace question card content with completion screen
        this.questionContainer.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg p-8 text-center">
                <div class="mb-6">
                    <i class="fas fa-check-circle text-green-500 text-6xl mb-4"></i>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">Assessment Complete!</h2>
                    <p class="text-gray-600 mb-4">
                        You've answered ${answeredCount} out of ${totalQuestions} questions.
                    </p>
                    <div class="w-full bg-gray-200 rounded-full h-3 mt-4">
                        <div class="bg-green-600 h-3 rounded-full" style="width: ${completionPercent}%"></div>
                    </div>
                    <p class="text-sm text-gray-500 mt-2">${completionPercent}% Complete</p>
                </div>
                
                <div class="space-y-4 max-w-md mx-auto">
                    <button onclick="assessmentEngine.finishAssessment()" 
                            class="w-full bg-green-600 hover:bg-green-700 text-white py-3 px-6 rounded-lg font-semibold transition duration-200 shadow-md">
                        <i class="fas fa-chart-bar mr-2"></i>View My Results
                    </button>
                    
                    <button onclick="assessmentEngine.showQuestion(0)" 
                            class="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg font-semibold transition duration-200">
                        <i class="fas fa-redo mr-2"></i>Review Answers
                    </button>
                    
                    <button onclick="location.reload()" 
                            class="w-full bg-gray-600 hover:bg-gray-700 text-white py-3 px-6 rounded-lg font-semibold transition duration-200">
                        <i class="fas fa-sync mr-2"></i>Restart Assessment
                    </button>
                </div>
            </div>
        `;
    }

    updateProgress() {
        const answeredCount = this.responses.size;
        const totalQuestions = this.questions.length;
        const progress = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;

        if (this.progressBar) {
            this.progressBar.style.width = `${progress}%`;
        }
        if (this.progressText) {
            this.progressText.textContent = `${Math.round(progress)}%`;
        }

        const questionCounter = document.getElementById('question-counter');
        if (questionCounter && totalQuestions > 0) {
            questionCounter.textContent = `Question ${this.currentQuestionIndex + 1} of ${totalQuestions}`;
        }
    }

    updateNavigation() {
        if (!this.prevBtn || !this.nextBtn || !this.finishBtn) return;

        this.prevBtn.disabled = this.currentQuestionIndex === 0;
        if (this.currentQuestionIndex === 0) {
            this.prevBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            this.prevBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }

        const isLastQuestion = this.currentQuestionIndex === this.questions.length - 1;
        
        if (this.nextBtn) {
            this.nextBtn.style.display = isLastQuestion ? 'none' : 'block';
        }
        if (this.finishBtn) {
            this.finishBtn.style.display = isLastQuestion ? 'block' : 'none';
            this.finishBtn.disabled = this.responses.size < this.questions.length;
            if (this.finishBtn.disabled) {
                this.finishBtn.classList.add('opacity-50', 'cursor-not-allowed');
            } else {
                this.finishBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        }
    }

    /**
     * Scroll the scrollable container to the top.
     */
    scrollToQuestionTop() {
        if (!this.scrollContainer) return;

        // Small delay to ensure DOM layout is complete
        setTimeout(() => {
            this.scrollContainer.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
            console.log('Scrolled scroll container to top');
        }, 50);
    }

    async finishAssessment() {
        const answeredCount = this.responses.size;
        const totalQuestions = this.questions.length;

        if (answeredCount < 5) {
            const proceed = confirm(`You have only answered ${answeredCount} questions. We recommend answering at least 5 questions for accurate results. Are you sure you want to finish?`);
            if (!proceed) return;
        }

        this.showLoading('Generating your personality assessment results...');

        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) throw new Error('CSRF token not available');

            console.log('Completing assessment for session:', this.sessionId);
            
            const response = await fetch(`/assessments/api/sessions/${this.sessionId}/complete_assessment/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            console.log('Complete assessment response status:', response.status);
            
            if (response.ok) {
                const result = await response.json();
                console.log('Assessment completed successfully:', result);
                window.location.href = '/assessments/results/';
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error('Error completing assessment:', error);
            this.showError(`Failed to complete assessment: ${error.message}`);
        }
    }

    hideLoading() {
        if (this.loadingSpinner) this.loadingSpinner.style.display = 'none';
        if (this.questionContainer) this.questionContainer.style.display = 'block';
        if (this.errorMessage) this.errorMessage.style.display = 'none';
    }

    showLoading(message = 'Loading...') {
        if (this.loadingSpinner) {
            this.loadingSpinner.innerHTML = `
                <div class="text-center py-12">
                    <div class="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-4"></div>
                    <p class="text-gray-600 text-lg font-medium">${message}</p>
                    <p class="text-gray-500 text-sm mt-2">Please wait...</p>
                </div>
            `;
            this.loadingSpinner.style.display = 'flex';
        }
        if (this.questionContainer) this.questionContainer.style.display = 'none';
        if (this.errorMessage) this.errorMessage.style.display = 'none';
    }

    showError(message) {
        if (this.loadingSpinner) this.loadingSpinner.style.display = 'none';
        if (this.questionContainer) this.questionContainer.style.display = 'none';
        if (this.errorMessage && this.errorText) {
            this.errorText.textContent = message;
            this.errorMessage.style.display = 'block';
        } else {
            alert('Error: ' + message);
        }
    }

    getCsrfToken() {
        let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!csrfToken) {
            const cookieValue = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
            if (cookieValue) csrfToken = cookieValue;
        }
        console.log('CSRF Token available:', !!csrfToken);
        return csrfToken;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing assessment engine...');
    if (document.getElementById('question-container')) {
        window.assessmentEngine = new AssessmentEngine();
        console.log('Assessment engine initialized successfully');
    } else {
        console.log('No assessment container found on this page');
    }
});