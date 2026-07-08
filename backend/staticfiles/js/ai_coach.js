// static/js/ai_coach.js

class AICoach {
    constructor() {
        this.chatContainer = document.getElementById('chat-container');
        this.messagesContainer = document.getElementById('messages-container');
        this.messageInput = document.getElementById('message-input');
        this.chatForm = document.getElementById('chat-form');
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Form submission
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Quick questions
        document.querySelectorAll('.quick-question').forEach(button => {
            button.addEventListener('click', (e) => {
                this.messageInput.value = e.target.textContent;
                this.sendMessage();
            });
        });

        // Enter key to send
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/ai-coach/api/chat/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            if (data.success) {
                this.addMessage(data.response, 'assistant');
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
            }
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.removeTypingIndicator();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex items-start space-x-3 ${sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`;
        
        const avatar = sender === 'user' ? 
            '<div class="bg-green-100 text-green-800 rounded-full p-2"><i class="fas fa-user"></i></div>' :
            '<div class="bg-blue-100 text-blue-800 rounded-full p-2"><i class="fas fa-robot"></i></div>';
        
        const bubbleClass = sender === 'user' ? 
            'bg-green-500 text-white rounded-lg p-4 max-w-3/4' :
            'bg-blue-50 rounded-lg p-4 max-w-3/4';
        
        messageDiv.innerHTML = `
            ${avatar}
            <div class="${bubbleClass}">
                <p class="break-words">${this.escapeHtml(content)}</p>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'flex items-start space-x-3';
        typingDiv.innerHTML = `
            <div class="bg-blue-100 text-blue-800 rounded-full p-2">
                <i class="fas fa-robot"></i>
            </div>
            <div class="bg-blue-50 rounded-lg p-4">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
            </div>
        `;
        
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Initialize AI Coach when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('chat-container')) {
        window.aiCoach = new AICoach();
    }
});