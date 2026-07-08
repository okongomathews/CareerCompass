// static/js/common.js - All common JavaScript functions

// ========== DOM READY FUNCTION ==========
document.addEventListener('DOMContentLoaded', function() {
    // Initialize mobile menu
    initMobileMenu();
    
    // Initialize tab functionality
    initTabs();
    
    // Initialize form loading states
    initFormLoading();
    
    // Initialize password strength checkers
    initPasswordStrength();
    
    // Initialize filter functionality
    initFilters();
    
    // Initialize tooltips
    initTooltips();
});

// ========== MOBILE MENU FUNCTIONS ==========
function initMobileMenu() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (!mobileMenuButton || !mobileMenu) return;
    
    mobileMenuButton.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleMobileMenu(mobileMenu, mobileMenuButton);
    });
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!mobileMenu.contains(event.target) && !mobileMenuButton.contains(event.target)) {
            closeMobileMenu(mobileMenu, mobileMenuButton);
        }
    });
    
    // Close mobile menu when clicking a link
    mobileMenu.querySelectorAll('a, button').forEach(element => {
        element.addEventListener('click', function() {
            closeMobileMenu(mobileMenu, mobileMenuButton);
        });
    });
}

function toggleMobileMenu(menu, button) {
    menu.classList.toggle('hidden');
    const icon = button.querySelector('i');
    icon.className = menu.classList.contains('hidden') ? 'fas fa-bars' : 'fas fa-times';
}

function closeMobileMenu(menu, button) {
    menu.classList.add('hidden');
    const icon = button.querySelector('i');
    icon.className = 'fas fa-bars';
}

// ========== TAB FUNCTIONS ==========
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabButtons.length === 0) return;
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab') || this.getAttribute('onclick')?.match(/showTab\('(\w+)'\)/)?.[1];
            
            if (tabId) {
                // Update active button
                tabButtons.forEach(btn => {
                    btn.classList.remove('active', 'text-blue-600', 'border-blue-500');
                    btn.classList.add('text-gray-500');
                });
                this.classList.add('active', 'text-blue-600', 'border-blue-500');
                this.classList.remove('text-gray-500');
                
                // Show active tab content
                tabContents.forEach(content => {
                    content.classList.add('hidden');
                });
                const targetTab = document.getElementById(`${tabId}-tab`) || document.getElementById(`${tabId}-content`);
                if (targetTab) {
                    targetTab.classList.remove('hidden');
                }
            }
        });
    });
    
    // Initialize first tab as active
    if (tabButtons.length > 0 && !document.querySelector('.tab-button.active')) {
        tabButtons[0].click();
    }
}

// Universal tab function
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
        button.classList.remove('border-blue-500', 'text-blue-600');
        button.classList.add('border-transparent', 'text-gray-500');
    });
    
    // Show selected tab
    const tabContent = document.getElementById(`tab-${tabName}-content`) || document.getElementById(`${tabName}-tab`);
    const tabButton = document.getElementById(`tab-${tabName}`) || document.querySelector(`[onclick*="showTab('${tabName}')"]`);
    
    if (tabContent) {
        tabContent.classList.remove('hidden');
        tabContent.classList.add('active');
    }
    
    if (tabButton) {
        tabButton.classList.add('active', 'border-blue-500', 'text-blue-600');
        tabButton.classList.remove('border-transparent', 'text-gray-500');
    }
}

// ========== FORM FUNCTIONS ==========
function initFormLoading() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = `
                    <i class="fas fa-spinner fa-spin mr-2"></i>
                    Loading...
                `;
                submitBtn.disabled = true;
                
                // Re-enable after 5 seconds if something goes wrong
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });
}

function initPasswordStrength() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        // Add password toggle
        const toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.className = 'absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500';
        toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
        
        const parent = input.parentNode;
        if (parent && !parent.querySelector('.password-toggle')) {
            parent.style.position = 'relative';
            toggleBtn.classList.add('password-toggle');
            parent.appendChild(toggleBtn);
            
            toggleBtn.addEventListener('click', function() {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
            });
        }
    });
}

// Password strength checker
function checkPasswordStrength(password) {
    let score = 0;
    
    if (password.length >= 8) score += 20;
    if (password.length >= 12) score += 10;
    if (/[A-Z]/.test(password)) score += 20;
    if (/[a-z]/.test(password)) score += 20;
    if (/[0-9]/.test(password)) score += 20;
    if (/[^A-Za-z0-9]/.test(password)) score += 10;
    
    return score;
}

// ========== FILTER FUNCTIONS ==========
function initFilters() {
    const filterElements = document.querySelectorAll('.resource-type, input[name="relevance"]');
    
    filterElements.forEach(element => {
        element.addEventListener('change', function() {
            const container = this.closest('.filter-container') || document;
            const items = container.querySelectorAll('.resource-item, .filterable-item');
            
            if (items.length > 0) {
                filterResources();
            }
        });
    });
}

function filterResources() {
    const selectedTypes = [];
    document.querySelectorAll('.resource-type:checked').forEach(checkbox => {
        selectedTypes.push(checkbox.value);
    });
    
    const minRelevance = parseFloat(document.querySelector('input[name="relevance"]:checked')?.value || 0);
    
    const resources = document.querySelectorAll('.resource-item');
    let visibleCount = 0;
    
    resources.forEach(resource => {
        const type = resource.dataset.type;
        const relevance = parseFloat(resource.dataset.relevance) || 0;
        
        const typeMatch = selectedTypes.length === 0 || selectedTypes.includes(type);
        const relevanceMatch = relevance >= minRelevance;
        
        if (typeMatch && relevanceMatch) {
            resource.style.display = 'block';
            visibleCount++;
        } else {
            resource.style.display = 'none';
        }
    });
    
    const noResults = document.getElementById('no-results');
    if (noResults) {
        if (visibleCount === 0 && resources.length > 0) {
            noResults.classList.remove('hidden');
        } else {
            noResults.classList.add('hidden');
        }
    }
}

function resetFilters() {
    document.querySelectorAll('.resource-type').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    const relevanceInput = document.querySelector('input[name="relevance"][value="0.7"]') || 
                          document.querySelector('input[name="relevance"]');
    if (relevanceInput) {
        relevanceInput.checked = true;
    }
    
    filterResources();
}

// ========== TOOLTIP FUNCTIONS ==========
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this);
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip(this);
        });
    });
}

function showTooltip(element) {
    const tooltipText = element.getAttribute('data-tooltip');
    if (!tooltipText) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'absolute z-50 px-2 py-1 text-sm bg-gray-900 text-white rounded shadow-lg';
    tooltip.textContent = tooltipText;
    tooltip.id = 'dynamic-tooltip';
    
    const rect = element.getBoundingClientRect();
    tooltip.style.top = (rect.top - 30) + 'px';
    tooltip.style.left = (rect.left + (rect.width / 2)) + 'px';
    tooltip.style.transform = 'translateX(-50%)';
    
    document.body.appendChild(tooltip);
}

function hideTooltip() {
    const tooltip = document.getElementById('dynamic-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// ========== UTILITY FUNCTIONS ==========
function scrollToBottom(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollTop = element.scrollHeight;
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    });
}

// ========== AJAX HELPER ==========
async function sendAjaxRequest(url, data, method = 'POST') {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    const headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    };
    
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: headers,
            body: JSON.stringify(data)
        });
        
        return await response.json();
    } catch (error) {
        console.error('AJAX request failed:', error);
        return { success: false, error: 'Network error' };
    }
}

// ========== MODAL FUNCTIONS ==========
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

// Close modal on ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(modal => {
            if (!modal.classList.contains('hidden')) {
                closeModal(modal.id);
            }
        });
    }
});

// ========== PASSWORD MATCH CHECKER ==========
function checkPasswordMatch(password1Id, password2Id, matchElementId) {
    const password1 = document.getElementById(password1Id)?.value || '';
    const password2 = document.getElementById(password2Id)?.value || '';
    const matchElement = document.getElementById(matchElementId);
    
    if (!matchElement) return;
    
    if (password1 && password2) {
        if (password1 === password2) {
            matchElement.className = 'text-sm text-green-600 mt-1';
            matchElement.innerHTML = '<i class="fas fa-check-circle mr-1"></i> Passwords match';
        } else {
            matchElement.className = 'text-sm text-red-600 mt-1';
            matchElement.innerHTML = '<i class="fas fa-times-circle mr-1"></i> Passwords do not match';
        }
        matchElement.classList.remove('hidden');
    } else {
        matchElement.classList.add('hidden');
    }
}

// ========== GOALS MANAGEMENT ==========
let goalCount = 0;

function editGoals() {
    document.getElementById('goals-display')?.classList.add('hidden');
    document.getElementById('goals-editor')?.classList.remove('hidden');
    
    const goalsForm = document.getElementById('goals-fields');
    if (goalsForm) {
        goalsForm.innerHTML = '';
        addGoalField();
    }
}

function addGoalField(title = '', description = '') {
    goalCount++;
    const goalsForm = document.getElementById('goals-fields');
    if (!goalsForm) return;
    
    const field = document.createElement('div');
    field.className = 'border border-gray-200 rounded-lg p-4 mb-3';
    field.innerHTML = `
        <div class="mb-3">
            <label class="block text-sm font-medium text-gray-700 mb-1">Goal Title</label>
            <input type="text" name="goal_titles[]" 
                   value="${title}" 
                   placeholder="e.g., Improve Mathematics"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg">
        </div>
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Goal Description</label>
            <textarea name="goal_descriptions[]" 
                      placeholder="Describe your goal..."
                      rows="2"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg">${description}</textarea>
        </div>
    `;
    goalsForm.appendChild(field);
}

function cancelEditGoals() {
    document.getElementById('goals-display')?.classList.remove('hidden');
    document.getElementById('goals-editor')?.classList.add('hidden');
}

// ========== QUICK SUGGESTION FUNCTIONS ==========
function suggestQuestion(button) {
    const messageInput = document.getElementById('message-input');
    if (messageInput && button.textContent) {
        messageInput.value = button.textContent.trim();
        messageInput.focus();
    }
}

// ========== CHAT SPECIFIC FUNCTIONS ==========
function scrollToBottomChat() {
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

window.addEventListener('load', scrollToBottomChat);