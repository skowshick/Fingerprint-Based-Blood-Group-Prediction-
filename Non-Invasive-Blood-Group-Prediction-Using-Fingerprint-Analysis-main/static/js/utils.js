// Common utility functions used across all pages

// Show success/error messages
function showMessage(text, type = 'info') {
    const message = document.getElementById('message');
    if (message) {
        message.textContent = text;
        message.className = `message ${type} show`;
        message.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            message.style.display = 'none';
            message.classList.remove('show');
        }, 5000);
    }
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Validate blood group format
function validateBloodGroup(bloodGroup) {
    const validGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
    return validGroups.includes(bloodGroup);
}

// Validate phone number
function validatePhone(phone) {
    const phoneRegex = /^[+]?[\d\s\-\(\)]{10,15}$/;
    return phoneRegex.test(phone);
}

// Validate email
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Handle form submission without loading state
async function handleFormSubmission(formElement, url, data, successCallback) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success || result.donors || result.blood_group) {
            if (successCallback) {
                successCallback(result);
            }
            return result;
        } else {
            throw new Error(result.error || 'Operation failed');
        }
        
    } catch (error) {
        showMessage(error.message, 'error');
        throw error;
    }
}

// Copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showMessage('Copied to clipboard!', 'success');
    } catch (err) {
        console.error('Failed to copy: ', err);
        showMessage('Failed to copy to clipboard', 'error');
    }
}

// Smooth scroll to element
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Toggle element visibility
function toggleElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const isHidden = element.style.display === 'none' || element.style.display === '';
        element.style.display = isHidden ? 'block' : 'none';
    }
}

// Show/hide loading overlay
function showLoading(show) {
    let loader = document.getElementById('loading-overlay');
    
    if (show) {
        if (!loader) {
            // Create loading overlay if it doesn't exist
            loader = document.createElement('div');
            loader.id = 'loading-overlay';
            loader.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            `;
            
            const spinner = document.createElement('div');
            spinner.innerHTML = `
                <div style="text-align: center; color: white;">
                    <div class="spinner" style="
                        border: 5px solid rgba(255, 255, 255, 0.3);
                        border-top: 5px solid white;
                        border-radius: 50%;
                        width: 60px;
                        height: 60px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 20px;
                    "></div>
                    <p style="font-size: 1.2rem; font-weight: 600;">Processing fingerprints...</p>
                    <p style="font-size: 0.9rem; opacity: 0.8;">This may take a few moments</p>
                </div>
            `;
            
            loader.appendChild(spinner);
            document.body.appendChild(loader);
            
            // Add spinner animation if not already present
            if (!document.getElementById('spinner-style')) {
                const style = document.createElement('style');
                style.id = 'spinner-style';
                style.textContent = `
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                `;
                document.head.appendChild(style);
            }
        } else {
            loader.style.display = 'flex';
        }
    } else {
        if (loader) {
            loader.style.display = 'none';
        }
    }
}