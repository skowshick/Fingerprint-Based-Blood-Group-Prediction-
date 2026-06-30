/**
 * Enhanced Form Interactions and Validation
 * This file provides comprehensive form enhancement features including
 * real-time validation, smooth transitions, and user feedback
 */

// Initialize form enhancements when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFormEnhancements();
});

/**
 * Initialize all form enhancement features
 */
function initializeFormEnhancements() {
    // Add floating labels effect
    initializeFloatingLabels();
    
    // Add real-time validation
    initializeRealTimeValidation();
    
    // Add form submission enhancements
    initializeFormSubmission();
    
    // Add interactive elements
    initializeInteractiveElements();
    
    // Add accessibility improvements
    initializeAccessibility();
}

/**
 * Initialize floating labels for better UX
 */
function initializeFloatingLabels() {
    const floatingContainers = document.querySelectorAll('.form-floating');
    
    floatingContainers.forEach(container => {
        const input = container.querySelector('.form-input, .form-select, .form-textarea');
        const label = container.querySelector('.form-label');
        
        if (input && label) {
            // Check initial state
            checkFloatingLabel(input, label);
            
            // Add event listeners
            input.addEventListener('focus', () => floatLabel(label));
            input.addEventListener('blur', () => checkFloatingLabel(input, label));
            input.addEventListener('input', () => checkFloatingLabel(input, label));
        }
    });
}

function floatLabel(label) {
    label.classList.add('floated');
}

function checkFloatingLabel(input, label) {
    if (input.value.trim() === '') {
        label.classList.remove('floated');
    } else {
        label.classList.add('floated');
    }
}

/**
 * Real-time form validation
 */
function initializeRealTimeValidation() {
    const formInputs = document.querySelectorAll('.form-input, .form-select, .form-textarea');
    
    formInputs.forEach(input => {
        // Add validation on blur and input
        input.addEventListener('blur', () => validateField(input));
        input.addEventListener('input', () => clearFieldError(input));
        
        // Add ARIA attributes for accessibility
        input.setAttribute('aria-describedby', input.id + '-error');
    });
}

/**
 * Validate individual field
 */
function validateField(input) {
    const formGroup = input.closest('.form-group');
    const errorElement = formGroup.querySelector('.form-error') || createErrorElement(formGroup, input.id);
    
    let isValid = true;
    let errorMessage = '';
    
    // Required field validation
    if (input.hasAttribute('required') && !input.value.trim()) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    if (input.type === 'email' && input.value.trim()) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(input.value.trim())) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Phone validation
    if (input.type === 'tel' && input.value.trim()) {
        const phoneRegex = /^[+]?[\d\s\-\(\)]{10,}$/;
        if (!phoneRegex.test(input.value.trim())) {
            isValid = false;
            errorMessage = 'Please enter a valid phone number';
        }
    }
    
    // Password validation
    if (input.type === 'password' && input.value.trim()) {
        if (input.value.length < 6) {
            isValid = false;
            errorMessage = 'Password must be at least 6 characters long';
        }
    }
    
    // Number validation
    if (input.type === 'number' && input.value.trim()) {
        const min = input.getAttribute('min');
        const max = input.getAttribute('max');
        const value = parseFloat(input.value);
        
        if (isNaN(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid number';
        } else if (min !== null && value < parseFloat(min)) {
            isValid = false;
            errorMessage = `Value must be at least ${min}`;
        } else if (max !== null && value > parseFloat(max)) {
            isValid = false;
            errorMessage = `Value must be no more than ${max}`;
        }
    }
    
    // Update field state
    if (isValid) {
        setFieldValid(formGroup, input);
    } else {
        setFieldError(formGroup, input, errorMessage, errorElement);
    }
    
    return isValid;
}

/**
 * Set field as valid
 */
function setFieldValid(formGroup, input) {
    formGroup.classList.remove('error');
    formGroup.classList.add('success');
    input.setAttribute('aria-invalid', 'false');
    
    const errorElement = formGroup.querySelector('.form-error');
    if (errorElement) {
        errorElement.style.display = 'none';
        errorElement.textContent = '';
    }
}

/**
 * Set field as invalid with error message
 */
function setFieldError(formGroup, input, message, errorElement) {
    formGroup.classList.remove('success');
    formGroup.classList.add('error');
    input.setAttribute('aria-invalid', 'true');
    
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

/**
 * Clear field error state
 */
function clearFieldError(input) {
    const formGroup = input.closest('.form-group');
    formGroup.classList.remove('error', 'success');
    input.setAttribute('aria-invalid', 'false');
    
    const errorElement = formGroup.querySelector('.form-error');
    if (errorElement) {
        errorElement.style.display = 'none';
        errorElement.textContent = '';
    }
}

/**
 * Create error element for field
 */
function createErrorElement(formGroup, inputId) {
    const errorElement = document.createElement('div');
    errorElement.className = 'form-error';
    errorElement.id = inputId + '-error';
    errorElement.setAttribute('role', 'alert');
    errorElement.setAttribute('aria-live', 'polite');
    formGroup.appendChild(errorElement);
    return errorElement;
}

/**
 * Enhanced form submission
 */
function initializeFormSubmission() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Validate all fields before submission
            const isFormValid = validateForm(form);
            
            if (!isFormValid) {
                e.preventDefault();
                showFormMessage('Please fix the errors above before submitting', 'error');
                
                // Focus on first error field
                const firstErrorField = form.querySelector('.form-group.error .form-input, .form-group.error .form-select, .form-group.error .form-textarea');
                if (firstErrorField) {
                    firstErrorField.focus();
                    firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return false;
            }
        });
    });
}

/**
 * Validate entire form
 */
function validateForm(form) {
    const inputs = form.querySelectorAll('.form-input, .form-select, .form-textarea');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Show form message
 */
function showFormMessage(message, type = 'info', duration = 5000) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.form-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageElement = document.createElement('div');
    messageElement.className = `alert ${type} form-message`;
    messageElement.style.display = 'block';
    messageElement.textContent = message;
    messageElement.setAttribute('role', 'alert');
    messageElement.setAttribute('aria-live', 'polite');
    
    // Insert at top of first form or body
    const form = document.querySelector('form') || document.body;
    form.insertBefore(messageElement, form.firstChild);
    
    // Auto remove after duration
    if (duration > 0) {
        setTimeout(() => {
            messageElement.style.opacity = '0';
            setTimeout(() => messageElement.remove(), 300);
        }, duration);
    }
    
    // Scroll to message
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Initialize interactive elements
 */
function initializeInteractiveElements() {
    // Blood type selector
    initializeBloodTypeSelector();
    
    // File upload
    initializeFileUpload();
    
    // Custom checkboxes and radios
    initializeCustomInputs();
    
    // Form step navigation
    initializeFormSteps();
}

/**
 * Blood type selector enhancement
 */
function initializeBloodTypeSelector() {
    const bloodTypeInputs = document.querySelectorAll('.blood-type-option input[type=\"radio\"]');
    
    bloodTypeInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Remove selection from siblings
            const container = this.closest('.blood-type-selector');
            container.querySelectorAll('.blood-type-option').forEach(option => {
                option.classList.remove('selected');
            });
            
            // Add selection to current
            this.closest('.blood-type-option').classList.add('selected');
            
            // Add success state to form group
            const formGroup = container.closest('.form-group');
            if (formGroup) {
                formGroup.classList.remove('error');
                formGroup.classList.add('success');
            }
        });
    });
}

/**
 * File upload enhancement
 */
function initializeFileUpload() {
    const fileUploadContainers = document.querySelectorAll('.file-upload-container');
    
    fileUploadContainers.forEach(container => {
        const input = container.querySelector('.file-upload-input');
        const label = container.querySelector('.file-upload-label');
        
        if (input && label) {
            // Drag and drop
            label.addEventListener('dragover', function(e) {
                e.preventDefault();
                this.classList.add('dragover');
            });
            
            label.addEventListener('dragleave', function() {
                this.classList.remove('dragover');
            });
            
            label.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    input.files = files;
                    handleFileSelection(input, files);
                }
            });
            
            // File selection
            input.addEventListener('change', function() {
                handleFileSelection(input, this.files);
            });
        }
    });
}

function handleFileSelection(input, files) {
    const container = input.closest('.file-upload-container');
    const fileList = container.querySelector('.file-list') || createFileList(container);
    
    // Clear existing files
    fileList.innerHTML = '';
    
    // Display selected files
    Array.from(files).forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <i class="fas fa-file"></i>
            <span class="file-name">${file.name}</span>
            <span class="file-size">(${formatFileSize(file.size)})</span>
            <button type="button" class="btn-remove-file" onclick="removeFile(this)">
                <i class="fas fa-times"></i>
            </button>
        `;
        fileList.appendChild(fileItem);
    });
    
    // Show uploaded files section
    const uploadedSection = container.querySelector('.uploaded-files');
    if (uploadedSection) {
        uploadedSection.style.display = 'block';
    }
    
    // Update form group state
    const formGroup = container.closest('.form-group');
    if (formGroup && files.length > 0) {
        formGroup.classList.remove('error');
        formGroup.classList.add('success');
    }
}

function createFileList(container) {
    let uploadedSection = container.querySelector('.uploaded-files');
    if (!uploadedSection) {
        uploadedSection = document.createElement('div');
        uploadedSection.className = 'uploaded-files';
        uploadedSection.innerHTML = '<h4>Uploaded Files:</h4><div class="file-list"></div>';
        container.appendChild(uploadedSection);
    }
    return uploadedSection.querySelector('.file-list');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function removeFile(button) {
    const fileItem = button.closest('.file-item');
    fileItem.remove();
    
    // Check if any files remain
    const container = button.closest('.file-upload-container');
    const fileList = container.querySelector('.file-list');
    if (fileList.children.length === 0) {
        const uploadedSection = container.querySelector('.uploaded-files');
        if (uploadedSection) {
            uploadedSection.style.display = 'none';
        }
        
        // Clear file input
        const input = container.querySelector('.file-upload-input');
        if (input) {
            input.value = '';
        }
        
        // Update form group state
        const formGroup = container.closest('.form-group');
        if (formGroup) {
            formGroup.classList.remove('success', 'error');
        }
    }
}

/**
 * Custom checkbox and radio inputs
 */
function initializeCustomInputs() {
    const customInputs = document.querySelectorAll('.form-checkbox, .form-radio');
    
    customInputs.forEach(input => {
        input.addEventListener('change', function() {
            const formGroup = this.closest('.form-group');
            if (formGroup) {
                formGroup.classList.remove('error');
                if (this.checked) {
                    formGroup.classList.add('success');
                } else {
                    formGroup.classList.remove('success');
                }
            }
        });
    });
}

/**
 * Form steps navigation
 */
function initializeFormSteps() {
    const progressSteps = document.querySelectorAll('.progress-step');
    const formSections = document.querySelectorAll('.form-step');
    
    if (progressSteps.length > 0 && formSections.length > 0) {
        // Initialize first step
        showFormStep(0);
        
        // Add navigation buttons
        addStepNavigationButtons();
    }
}

function showFormStep(stepIndex) {
    const progressSteps = document.querySelectorAll('.progress-step');
    const formSections = document.querySelectorAll('.form-step');
    const connectors = document.querySelectorAll('.progress-connector');
    
    // Update progress indicators
    progressSteps.forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index < stepIndex) {
            step.classList.add('completed');
        } else if (index === stepIndex) {
            step.classList.add('active');
        }
    });
    
    // Update connectors
    connectors.forEach((connector, index) => {
        connector.classList.toggle('completed', index < stepIndex);
    });
    
    // Show/hide form sections
    formSections.forEach((section, index) => {
        section.style.display = index === stepIndex ? 'block' : 'none';
    });
    
    // Store current step
    window.currentFormStep = stepIndex;
}

function addStepNavigationButtons() {
    const formSections = document.querySelectorAll('.form-step');
    
    formSections.forEach((section, index) => {
        const navContainer = document.createElement('div');
        navContainer.className = 'form-step-navigation';
        
        if (index > 0) {
            const prevButton = document.createElement('button');
            prevButton.type = 'button';
            prevButton.className = 'btn btn-secondary';
            prevButton.innerHTML = '<i class=\"fas fa-arrow-left\"></i> Previous';
            prevButton.addEventListener('click', () => showFormStep(index - 1));
            navContainer.appendChild(prevButton);
        }
        
        if (index < formSections.length - 1) {
            const nextButton = document.createElement('button');
            nextButton.type = 'button';
            nextButton.className = 'btn btn-primary';
            nextButton.innerHTML = 'Next <i class=\"fas fa-arrow-right\"></i>';
            nextButton.addEventListener('click', () => {
                if (validateCurrentFormStep()) {
                    showFormStep(index + 1);
                }
            });
            navContainer.appendChild(nextButton);
        }
        
        section.appendChild(navContainer);
    });
}

function validateCurrentFormStep() {
    const currentSection = document.querySelectorAll('.form-step')[window.currentFormStep];
    if (currentSection) {
        const inputs = currentSection.querySelectorAll('.form-input, .form-select, .form-textarea');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            showFormMessage('Please fix the errors in this section before continuing', 'error', 3000);
        }
        
        return isValid;
    }
    return true;
}

/**
 * Accessibility improvements
 */
function initializeAccessibility() {
    // Add ARIA labels to form elements
    const formInputs = document.querySelectorAll('.form-input, .form-select, .form-textarea');
    
    formInputs.forEach(input => {
        const label = input.closest('.form-group').querySelector('.form-label');
        if (label && !input.hasAttribute('aria-label')) {
            input.setAttribute('aria-label', label.textContent.replace(/[*]/g, '').trim());
        }
        
        // Add required indication
        if (input.hasAttribute('required')) {
            input.setAttribute('aria-required', 'true');
        }
    });
    
    // Improve button accessibility
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        if (!button.hasAttribute('aria-label') && !button.textContent.trim()) {
            const icon = button.querySelector('i[class*=\"fa-\"]');
            if (icon) {
                // Extract action from icon class
                const iconClass = Array.from(icon.classList).find(cls => cls.startsWith('fa-'));
                const action = iconClass ? iconClass.replace('fa-', '').replace(/-/g, ' ') : 'Action';
                button.setAttribute('aria-label', action.charAt(0).toUpperCase() + action.slice(1));
            }
        }
    });
    
    // Add keyboard navigation support
    addKeyboardSupport();
}

/**
 * Add keyboard navigation support
 */
function addKeyboardSupport() {
    // Escape key to close modals/overlays
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal, .overlay');
            modals.forEach(modal => {
                if (modal.style.display !== 'none') {
                    modal.style.display = 'none';
                }
            });
        }
    });
    
    // Enter key on buttons
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.classList.contains('btn')) {
            e.target.click();
        }
    });
}

/**
 * Utility function to reset all form states
 */
function resetFormStates(form) {
    if (!form) return;
    
    // Reset all field states
    const formGroups = form.querySelectorAll('.form-group');
    formGroups.forEach(group => {
        group.classList.remove('error', 'success');
    });
    
    // Clear all error messages
    const errorElements = form.querySelectorAll('.form-error');
    errorElements.forEach(error => {
        error.style.display = 'none';
        error.textContent = '';
    });
    
    // Clear any form messages
    const messages = document.querySelectorAll('.form-message');
    messages.forEach(msg => msg.remove());
}

/**
 * Utility function to populate form data
 */
function populateForm(form, data) {
    if (!form || !data) return;
    
    Object.keys(data).forEach(key => {
        const input = form.querySelector(`[name=\"${key}\"], #${key}`);
        if (input) {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = !!data[key];
                input.dispatchEvent(new Event('change'));
            } else if (input.type === 'file') {
                // File inputs cannot be programmatically set for security reasons
            } else {
                input.value = data[key] || '';
                input.dispatchEvent(new Event('input'));
            }
        }
    });
}

// Export functions for global use
window.FormEnhancements = {
    validateField,
    setFieldValid,
    setFieldError,
    clearFieldError,
    validateForm,
    showFormMessage,
    resetFormStates,
    populateForm,
    showFormStep
};