// Dashboard JavaScript functionality

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initFileUpload();
    initDonorSearch();
});

// File Upload Functionality
function initFileUpload() {
    const fileInput = document.getElementById('fingerprint-files');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelection);
    }
}

function handleFileSelection(e) {
    const files = Array.from(e.target.files);
    const fileList = document.getElementById('file-list');
    const uploadedFiles = document.getElementById('uploaded-files');
    const predictBtn = document.getElementById('predict-btn');
    
    if (files.length > 0) {
        if (files.length > 10) {
            showMessage('Maximum 10 files allowed', 'error');
            return;
        }
        
        fileList.innerHTML = '';
        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <i class="fas fa-file-image"></i>
                <span>${file.name}</span>
            `;
            fileList.appendChild(fileItem);
        });
        
        uploadedFiles.style.display = 'block';
        predictBtn.style.display = 'inline-block';
    }
}

// Predict Blood Group
async function predictBloodGroup() {
    const fileInput = document.getElementById('fingerprint-files');
    const files = fileInput.files;
    
    if (files.length === 0) {
        showMessage('Please select fingerprint images first', 'error');
        return;
    }
    
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('fingerprints', files[i]);
    }
    
    showLoading(true);
    
    try {
        // Upload files
        const uploadResponse = await fetch('/predict/upload-fingerprints', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });
        
        const uploadResult = await uploadResponse.json();
        
        if (!uploadResult.success) {
            throw new Error(uploadResult.error);
        }
        
        // Add a small delay to ensure session is saved
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Predict blood group
        const predictResponse = await fetch('/predict/predict-blood-group', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({})
        });
        
        if (!predictResponse.ok) {
            const errorText = await predictResponse.text();
            throw new Error(`Server error: ${predictResponse.status} - ${errorText}`);
        }
        
        const predictResult = await predictResponse.json();
        
        if (predictResult.success) {
            showResults(predictResult);
        } else {
            // Check if it's a quality check failure
            if (predictResult.error_type === 'quality_check_failed') {
                showQualityErrorModal(predictResult.error);
            } else {
                throw new Error(predictResult.error);
            }
            return;
        }
        
    } catch (error) {
        console.error('Prediction error:', error);
        showMessage('Prediction failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function showQualityErrorModal(errorMessage) {
    // Create modal overlay
    const modal = document.createElement('div');
    modal.className = 'quality-error-modal';
    modal.innerHTML = `
        <div class="quality-error-content">
            <div class="quality-error-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h2>Image Quality Issue</h2>
            <div class="quality-error-message">${errorMessage.replace(/\n/g, '<br>')}</div>
            <div class="quality-tips">
                <h3>💡 Tips for Better Images:</h3>
                <ul>
                    <li><i class="fas fa-check"></i> Use good lighting (natural light works best)</li>
                    <li><i class="fas fa-check"></i> Keep the camera steady to avoid blur</li>
                    <li><i class="fas fa-check"></i> Ensure fingerprints are clearly visible with high contrast</li>
                    <li><i class="fas fa-check"></i> Use a scanner or high-quality camera for best results</li>
                    <li><i class="fas fa-check"></i> Avoid shadows and overexposure</li>
                </ul>
            </div>
            <button class="quality-error-btn" onclick="closeQualityModal()">
                <i class="fas fa-upload"></i> Upload New Images
            </button>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Add click outside to close
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeQualityModal();
        }
    });
}

function closeQualityModal() {
    const modal = document.querySelector('.quality-error-modal');
    if (modal) {
        modal.remove();
    }
}

function showResults(data) {
    const resultsSection = document.getElementById('results-section');
    const bloodGroupResult = document.getElementById('blood-group-result');
    const confidenceScore = document.getElementById('confidence-score');
    const detailedResults = document.getElementById('detailed-results');
    
    bloodGroupResult.textContent = data.blood_group;
    confidenceScore.textContent = `${data.confidence.toFixed(1)}% Confidence`;
    
    // Show detailed results
    detailedResults.innerHTML = `
        <div style="background: rgba(15, 23, 42, 0.5); padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h3>Prediction Details</h3>
            <p><strong>Number of fingerprints analyzed:</strong> ${data.num_fingerprints}</p>
            <p><strong>Confidence Score:</strong> ${data.confidence.toFixed(1)}%</p>
            ${data.confidence > 80 ? 
                '<p style="color: var(--success-green);"><i class="fas fa-check-circle"></i> High confidence prediction</p>' :
                data.confidence > 60 ?
                '<p style="color: var(--warning-orange);"><i class="fas fa-exclamation-triangle"></i> Moderate confidence - consider uploading more fingerprints</p>' :
                '<p style="color: var(--primary-red);"><i class="fas fa-times-circle"></i> Low confidence - please upload clearer fingerprint images</p>'
            }
        </div>
    `;
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Navigation functions
function scrollToSearch() {
    const element = document.getElementById('search-section');
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

function scrollToUpload() {
    const element = document.getElementById('upload-section');
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}