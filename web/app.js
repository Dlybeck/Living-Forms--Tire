class ProfessionalTireFormsApp {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.messageCount = 0;

        this.initializeElements();
        this.setupEventListeners();
        this.loadInitialForm();
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }

    initializeElements() {
        this.formWorkspace = document.getElementById('form-workspace');
        this.loading = document.getElementById('loading');

        this.notepadSidebar = document.getElementById('notepad-sidebar');
        this.notepadContent = document.getElementById('notepad-content');
        this.notepadToggle = document.getElementById('notepad-toggle');
        this.notepadIndicator = document.getElementById('notepad-indicator');
        this.conversationHistory = [];
    }

    setupEventListeners() {
        // Form submission handling with event delegation
        this.formWorkspace.addEventListener('submit', (e) => {
            if (e.target.tagName === 'FORM') {
                e.preventDefault();
                this.handleFormSubmission(e.target);
            }
        });

        // Notepad toggle functionality
        this.notepadToggle.addEventListener('click', () => {
            this.toggleNotepad();
        });

        this.notepadIndicator.addEventListener('click', () => {
            this.showNotepad();
        });
        
        // Backup click handler for submit buttons
        this.formWorkspace.addEventListener('click', (e) => {
            if (e.target.type === 'submit' && e.target.closest('form')) {
                const form = e.target.closest('form');
                if (form && !form.dataset.disabled) {
                    e.preventDefault();
                    this.handleFormSubmission(form);
                }
            }
        });
    }

    toggleNotepad() {
        const isVisible = !this.notepadSidebar.classList.contains('notepad-hidden');
        if (isVisible) {
            this.hideNotepad();
        } else {
            this.showNotepad();
        }
    }

    showNotepad() {
        this.notepadSidebar.classList.remove('notepad-hidden');
        this.notepadToggle.textContent = 'Hide';
        this.notepadIndicator.style.display = 'none';
    }

    hideNotepad() {
        this.notepadSidebar.classList.add('notepad-hidden');
        this.notepadToggle.textContent = 'Show';
        this.notepadIndicator.style.display = 'block';
    }

    updateNotepad(content) {
        if (content && content.trim() && content !== 'No information recorded yet.') {
            // The backend should send plain text, we'll format it here
            const formattedContent = this.formatNotepadContent(content);
            this.notepadContent.innerHTML = DOMPurify.sanitize(formattedContent);
            // Show indicator if notepad is hidden on mobile
            if (window.innerWidth <= 600 || this.notepadSidebar.classList.contains('notepad-hidden')) {
                this.notepadIndicator.style.display = 'block';
            }
        } else {
            this.notepadContent.innerHTML = '<em>Your AI assistant is ready to help. Information gathered during our conversation will appear here...</em>';
        }
    }

    formatNotepadContent(text) {
        // Always start with plain text and format it consistently
        let formatted = this.escapeHtml(text);
        
        // Convert line breaks to <br> tags
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #ecf0f1; font-weight: 600;">$1</strong>');
        
        // Convert ### headers to <h3>
        formatted = formatted.replace(/^### (.*?)$/gm, '<h3 style="color: #3498db; margin: 15px 0 10px 0; font-size: 16px; font-weight: 600;">$1</h3>');
        
        // Convert ## headers to <h2>
        formatted = formatted.replace(/^## (.*?)$/gm, '<h2 style="color: #ecf0f1; margin: 15px 0 10px 0; font-size: 18px; font-weight: 600;">$1</h2>');
        
        // Convert # headers to <h1>
        formatted = formatted.replace(/^# (.*?)$/gm, '<h1 style="color: #ecf0f1; margin: 15px 0 10px 0; font-size: 20px; font-weight: 600;">$1</h1>');
        
        // Convert numbered lists (1. item)
        formatted = formatted.replace(/^(\d+)\. (.*?)$/gm, '<div style="margin:8px 0;"><strong style="color: #3498db;">$1.</strong> $2</div>');
        
        // Convert bullet points (- item or • item)
        formatted = formatted.replace(/^[•-] (.*?)$/gm, '<div style="margin:8px 0;margin-left:15px;color: #bdc3c7;">• $1</div>');
        
        // Convert code blocks (`code`)
        formatted = formatted.replace(/`(.*?)`/g, '<code style="background: #4a5f7a; padding: 2px 6px; border-radius: 4px; font-size: 12px; color: #ecf0f1;">$1</code>');
        
        // Convert horizontal rules (---)
        formatted = formatted.replace(/^---$/gm, '<hr style="border: none; border-top: 2px solid #4a5f7a; margin: 15px 0;">');
        
        // Handle special formatting for Memory Display and Memory Wall sections
        formatted = formatted.replace(/Memory Display shows:/gi, '<strong style="color: #3498db;">Memory Display shows:</strong>');
        formatted = formatted.replace(/Memory Wall holds:/gi, '<strong style="color: #3498db;">Memory Wall holds:</strong>');
        
        // Handle emotion names with proper styling
        formatted = formatted.replace(/(Logic|Empathy|Urgency|Curiosity|Fear|Joy|Productivity)(\s*\([^)]*\))?:/g, '<strong style="color: #e74c3c;">$1$2:</strong>');
        
        return formatted;
    }

    async loadInitialForm() {
        // Welcome form is already in HTML, no need to generate it
        // Just ensure it's visible
        const welcomeSection = document.getElementById('welcome-form-section');
        if (welcomeSection) {
            welcomeSection.style.display = 'block';
        }
    }

    async handleFormSubmission(form) {
        // Prevent multiple submissions
        if (form.dataset.submitting === 'true' || form.dataset.disabled === 'true') {
            return;
        }
        form.dataset.submitting = 'true';
        
        const formData = new FormData(form);
        const formObject = {};
        
        formData.forEach((value, key) => {
            if (formObject[key]) {
                if (Array.isArray(formObject[key])) {
                    formObject[key].push(value);
                } else {
                    formObject[key] = [formObject[key], value];
                }
            } else {
                formObject[key] = value;
            }
        });
        
        // Add context for initial form
        if (form.id === 'welcome-form' && formObject.user_request) {
            formObject['_context'] = {
                'selected_label': 'User request',
                'selected_description': formObject.user_request,
                'user_context': 'Initial user request for tire search',
                'is_initial_form': true
            };
        }
        
        // Basic validation for required fields
        if (form.id === 'welcome-form' && !formObject.user_request?.trim()) {
            this.showFormError(form, 'Please tell us what you\'re looking for to get started.');
            form.dataset.submitting = 'false';
            return;
        }
        
        // Mark form as completed and disable
        this.markFormCompleted(form, formObject);
        
        // Scroll to loading indicator
        this.scrollToBottom();
        
        this.showLoading();
        try {
            const response = await this.callChatAPI('Form submission', formObject);
            this.hideLoading();
            this.addNewFormSection(response);

        } catch (error) {
            console.error('Form submission error:', error);
            this.hideLoading();
            this.showFormError(form, 'Sorry, there was an error processing your request. Please try again.');
            this.enableForm(form);
        } finally {
            form.dataset.submitting = 'false';
        }
    }

    markFormCompleted(form, formData) {
        form.dataset.disabled = 'true';
        
        // Disable ALL form inputs regardless of content
        const allInputs = form.querySelectorAll('input, textarea, select');
        allInputs.forEach(input => {
            // Fill in the value if it exists in formData
            const fieldName = input.name;
            if (fieldName && formData[fieldName] !== undefined) {
                input.value = formData[fieldName];
            }
            
            // Disable the input
            input.disabled = true;
            input.style.background = '#f8f9fa';
        });
        
        // Disable submit button
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '✅ Submitted';
            submitButton.style.background = '#28a745';
        }
        
        // Add completed styling to form section
        const formSection = form.closest('.form-section');
        if (formSection) {
            formSection.classList.add('completed');
        }
        
        // Store in history
        this.conversationHistory.push({
            type: 'user',
            content: formData,
            timestamp: new Date()
        });
    }

    enableForm(form) {
        form.dataset.disabled = 'false';
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.disabled = false;
            input.style.background = '';
        });
        
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.style.background = '';
        }
    }

    showFormError(form, message) {
        // Remove existing error if any
        const existingError = form.querySelector('.form-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.style.cssText = `
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #f5c6cb;
            border-radius: 8px;
            padding: 12px;
            margin-top: 15px;
            font-weight: 500;
        `;
        errorDiv.textContent = message;
        
        const formActions = form.querySelector('.form-actions');
        if (formActions) {
            formActions.parentNode.insertBefore(errorDiv, formActions);
        } else {
            form.appendChild(errorDiv);
        }
        
        // Remove error after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    async callChatAPI(message, formData = null) {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                request_type: message,
                session_id: this.sessionId,
                form_data: formData
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    }

    addNewFormSection(response) {
        let html = '';
        
        // Show form HTML if present (prioritize this over plain response to avoid duplication)
        if (response.form_html) {
            html += `<div class="form-section">${response.form_html}</div>`;
        }
        // Only show AI response if there's no form HTML
        else if (response.response && response.response.trim()) {
            const isBlockHtml = /^\s*<(div|form|h[1-6]|table|section|header|footer|main|article|nav|ul|ol|li|p|fieldset|legend|label|input|button|select|option|textarea|hr|br|img|span|style|script|link|meta|title|head|body|html)[\s>]/i.test(response.response);
            
            if (isBlockHtml) {
                html += `<div class="form-section">${DOMPurify.sanitize(response.response)}</div>`;
            } else {
                const formattedText = this.formatAIResponse(response.response);
                html += `
                    <div class="form-section">
                        <div class="ai-response">${formattedText}</div>
                    </div>
                `;
            }
        }
        
        // If no content, show a placeholder
        if (!response.response && !response.form_html) {
            html += `
                <div class="form-section">
                    <div class="ai-response">
                        <p>Continue with your tire search...</p>
                    </div>
                </div>
            `;
        }
        
        // Add the new content
        this.formWorkspace.insertAdjacentHTML('beforeend', html);
        
        // Update notepad
        if (response.notepad_content) {
            this.updateNotepad(response.notepad_content);
        }
        
        // Store response in history
        this.conversationHistory.push({
            type: 'assistant',
            content: response,
            timestamp: new Date()
        });
        
        // Scroll to the new form (which is at the bottom)
        this.scrollToNewForm();
    }

    showLoading() {
        this.loading.classList.add('active');
    }

    hideLoading() {
        this.loading.classList.remove('active');
    }

    formatAIResponse(text) {
        let formatted = this.escapeHtml(text);
        
        // Convert line breaks to <br> tags
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert ### headers to <h3>
        formatted = formatted.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        
        // Convert numbered lists (1. item)
        formatted = formatted.replace(/^(\d+)\. (.*?)$/gm, '<div style="margin:8px 0;"><strong>$1.</strong> $2</div>');
        
        // Convert bullet points (- item)
        formatted = formatted.replace(/^- (.*?)$/gm, '<div style="margin:8px 0;margin-left:15px;">• $1</div>');
        
        // Convert code blocks (`code`)
        formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Add paragraph breaks for double line breaks
        formatted = formatted.replace(/(<br>){2,}/g, '</p><p>');
        
        // Wrap in paragraph tags
        formatted = `<p>${formatted}</p>`;
        
        return DOMPurify.sanitize(formatted);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        // Smooth scroll to bottom of form workspace
        this.formWorkspace.scrollTo({
            top: this.formWorkspace.scrollHeight,
            behavior: 'smooth'
        });
    }

    scrollToNewForm() {
        // Smooth scroll to the newly added form (which is at the bottom)
        this.formWorkspace.scrollTo({
            top: this.formWorkspace.scrollHeight,
            behavior: 'smooth'
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ProfessionalTireFormsApp();
}); 