// Blood Donor Management page JavaScript

let map;
let marker;
let selectedLat = null;
let selectedLng = null;
let userLocation = null;

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    const formElement = document.getElementById('donorForm');

    if (!mapElement || !formElement) {
        return;
    }

    initMap();
    loadDonors();

    document.getElementById('getCurrentLocation').addEventListener('click', getCurrentLocation);
    document.getElementById('dropPin').addEventListener('click', enableDropPin);
    formElement.addEventListener('submit', handleDonorSubmission);
    document.getElementById('resetForm').addEventListener('click', resetForm);
    document.getElementById('refreshDonors').addEventListener('click', loadDonors);
    
    // Emergency mode event listeners
    document.getElementById('emergencyMode').addEventListener('click', activateEmergencyMode);
    document.getElementById('exitEmergency').addEventListener('click', exitEmergencyMode);
    document.getElementById('findEmergencyResources').addEventListener('click', findEmergencyResources);

    // Filters - with debugging
    document.getElementById('filterBloodGroup').addEventListener('change', function() {
        console.log('🩸 Blood group changed to:', this.value);
        loadDonors();
    });
    document.getElementById('filterCity').addEventListener('input', debounce(loadDonors, 500));
    document.getElementById('filterPincode').addEventListener('input', debounce(loadDonors, 500));
    
    // Clear filters button
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters);
    }
});

// Initialize map
function initMap() {
    const defaultLat = 20.5937;
    const defaultLng = 78.9629;

    map = L.map('map').setView([defaultLat, defaultLng], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    map.on('click', function (e) {
        setMarkerPosition(e.latlng.lat, e.latlng.lng);
        showLocationStatus('✓ Location selected on map', 'success');
    });
}

function setMarkerPosition(lat, lng) {
    selectedLat = lat;
    selectedLng = lng;

    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lng;

    if (marker) {
        map.removeLayer(marker);
    }

    marker = L.marker([lat, lng], { draggable: true }).addTo(map);

    marker.on('dragend', function (e) {
        const position = e.target.getLatLng();
        selectedLat = position.lat;
        selectedLng = position.lng;
        document.getElementById('latitude').value = position.lat;
        document.getElementById('longitude').value = position.lng;
        showLocationStatus('✓ Marker position updated', 'success');
    });

    marker.bindPopup(
        `<div style="text-align: center; padding: 0.5rem;">
            <strong style="color: #e63946;">Selected Location</strong><br>
            <small>Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}</small><br>
            <small style="color: #6b7280;">Drag to adjust position</small>
        </div>`
    );

    map.setView([lat, lng], 15);
}

function getCurrentLocation() {
    const button = document.getElementById('getCurrentLocation');

    button.disabled = true;

    if (!navigator.geolocation) {
        showLocationStatus('❌ Geolocation is not supported by this browser.', 'error');
        button.disabled = false;
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function (position) {
            setMarkerPosition(position.coords.latitude, position.coords.longitude);
            showLocationStatus('✅ Location detected successfully!', 'success');
            button.disabled = false;
        },
        function (error) {
            let errorMessage = '❌ Unable to get your location. ';
            switch (error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage += 'Please allow location access in your browser settings.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage += 'Location information unavailable.';
                    break;
                case error.TIMEOUT:
                    errorMessage += 'Location request timed out. Please try again.';
                    break;
                default:
                    errorMessage += 'An unknown error occurred.';
                    break;
            }
            showLocationStatus(errorMessage, 'error');
            button.disabled = false;
        },
        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 300000
        }
    );
}
function enableDropPin() {
    showLocationStatus('📍 Click anywhere on the map to drop a pin', 'info');
    map.getContainer().style.cursor = 'crosshair';
    
    map.once('click', function(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        setMarkerPosition(lat, lng);
        showLocationStatus('✅ Pin dropped! You can drag it to adjust the position', 'success');
        map.getContainer().style.cursor = '';
    });
}

function showLocationStatus(message, type) {
    const statusDiv = document.getElementById('locationStatus');
    statusDiv.textContent = message;
    statusDiv.className = `location-status ${type}`;
    statusDiv.style.display = 'inline-flex';

    if (type === 'success') {
        setTimeout(() => (statusDiv.style.display = 'none'), 3000);
    } else if (type === 'error') {
        setTimeout(() => (statusDiv.style.display = 'none'), 8000);
    }
}

function showAlert(message, type) {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = `alert ${type}`;
    alert.style.display = 'block';

    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

async function handleDonorSubmission(e) {
    e.preventDefault();

    clearFormErrors();
    const name = document.getElementById('name').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const bloodGroup = document.getElementById('blood_group').value;
    const address = document.getElementById('address').value.trim();
    const city = document.getElementById('city').value.trim();
    const pincode = document.getElementById('pincode').value.trim();

    let hasErrors = false;

    if (!name || name.length < 2) {
        showFieldError('name', 'Name must be at least 2 characters long');
        hasErrors = true;
    }

    const phoneRegex = /[\+]?[0-9\s\-\(\)]{10,15}/;
    if (!phone || !phoneRegex.test(phone)) {
        showFieldError('phone', 'Please enter a valid phone number');
        hasErrors = true;
    }

    if (!bloodGroup) {
        showFieldError('blood_group', 'Please select a blood group');
        hasErrors = true;
    }

    if (!address || address.length < 10) {
        showFieldError('address', 'Address must be at least 10 characters long');
        hasErrors = true;
    }

    if (!city || city.length < 2) {
        showFieldError('city', 'Please enter a valid city name');
        hasErrors = true;
    }

    const pincodeRegex = /^[0-9]{5,6}$/;
    if (!pincode || !pincodeRegex.test(pincode)) {
        showFieldError('pincode', 'Please enter a valid 5-6 digit postal code');
        hasErrors = true;
    }

    if (hasErrors) {
        showAlert('⚠️ Please fix the errors highlighted in the form.', 'error');
        return;
    }

    const submitButton = document.querySelector('button[type="submit"]');
    submitButton.disabled = true;

    const formData = {
        name: name,
        phone: phone,
        email: document.getElementById('email').value.trim(),
        blood_group: bloodGroup,
        address: address,
        city: city,
        pincode: pincode,
        latitude: selectedLat,
        longitude: selectedLng
    };

    try {
        const response = await fetch('/blood_donor/add_donor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        console.log('Response status:', response.status);
        const result = await response.json();
        console.log('Response data:', result);

        if (response.ok && result.success) {
            showAlert('✅ Blood donor added successfully! Thank you for helping save lives.', 'success');
            resetForm();
            loadDonors();
        } else {
            showAlert('❌ ' + (result.error || 'Failed to add donor. Please try again.'), 'error');
        }
    } catch (error) {
        console.error('Network error:', error);
        showAlert('❌ Network error. Please check your connection and try again.', 'error');
    } finally {
        // Ensure button is always re-enabled and text reset
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = '<i class="fas fa-plus"></i> Add Donor';
        }
        console.log('Submission completed');
    }
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    field.classList.add('error');

    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }

    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.display = 'block';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);

    field.addEventListener(
        'input',
        function () {
            field.classList.remove('error');
            const errEl = field.parentNode.querySelector('.field-error');
            if (errEl) errEl.style.display = 'none';
        },
        { once: true }
    );
}

function clearFormErrors() {
    document.querySelectorAll('.form-input.error').forEach(field => {
        field.classList.remove('error');
    });
    document.querySelectorAll('.field-error').forEach(error => {
        error.style.display = 'none';
    });
}

function resetForm() {
    document.getElementById('donorForm').reset();
    document.getElementById('latitude').value = '';
    document.getElementById('longitude').value = '';
    selectedLat = null;
    selectedLng = null;

    clearFormErrors();

    if (marker) {
        map.removeLayer(marker);
        marker = null;
    }

    map.setView([20.5937, 78.9629], 5);
    showLocationStatus('📝 Form reset successfully', 'success');
}

async function loadDonors() {
    const donorsList = document.getElementById('donorsList');
    
    try {
        const bloodGroup = document.getElementById('filterBloodGroup').value;
        const city = document.getElementById('filterCity').value.trim();
        const pincode = document.getElementById('filterPincode').value.trim();

        console.log('🔍 Loading donors with filters:', {
            bloodGroup: bloodGroup || 'none',
            city: city || 'none',
            pincode: pincode || 'none'
        });

        const params = new URLSearchParams();
        // Remove pagination limit to show all donors
        params.append('per_page', '1000');
        if (bloodGroup) params.append('blood_group', bloodGroup);
        if (city) params.append('city', city);
        if (pincode) params.append('pincode', pincode);

        const url = `/blood_donor/donors/list?${params.toString()}`;
        console.log('📡 Fetching:', url);

        const response = await fetch(url);
        const result = await response.json();

        console.log('📦 Response:', {
            ok: response.ok,
            total: result.total,
            donorsCount: result.donors ? result.donors.length : 0
        });

        if (response.ok) {
            displayDonors(result.donors || []);
        } else {
            donorsList.innerHTML = `
                <div style="text-align: center; color: #ef4444; padding: 2rem;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                    <p>Error: ${result.error || 'Failed to load donors'}</p>
                </div>
            `;
            showAlert(result.error || 'Failed to load donors', 'error');
        }
    } catch (error) {
        console.error('❌ Error loading donors:', error);
        donorsList.innerHTML = `
            <div style="text-align: center; color: #ef4444; padding: 2rem;">
                <i class="fas fa-wifi" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>Network error while loading donors.</p>
                <button class="btn btn-secondary" onclick="loadDonors()">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            </div>
        `;
        showAlert('Network error while loading donors.', 'error');
    }
}

function displayDonors(donors) {
    const donorsList = document.getElementById('donorsList');

    if (!donors.length) {
        donorsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <i class="fas fa-users"></i>
                </div>
                <h3>No Donors Found</h3>
                <p>No blood donors match your current filters. Try adjusting the search criteria or add new donors to the system.</p>
                <button class="btn btn-primary" onclick="document.getElementById('donorForm').scrollIntoView({behavior: 'smooth'})">
                    <i class="fas fa-plus"></i> Add First Donor
                </button>
            </div>
        `;
        return;
    }

    donorsList.innerHTML = donors
        .map(
            (donor, index) => `
        <div class="donor-card-enhanced" style="animation-delay: ${index * 0.05}s">
            <div class="donor-card-header">
                <div class="donor-avatar">
                    <i class="fas fa-user-circle"></i>
                </div>
                <div class="donor-title">
                    <h3>${donor.name}</h3>
                    <span class="donor-location">
                        <i class="fas fa-map-marker-alt"></i> ${donor.city}, ${donor.pincode}
                    </span>
                </div>
                <div class="blood-badge-large">
                    <div class="blood-badge-icon"><i class="fas fa-tint"></i></div>
                    <div class="blood-badge-text">${donor.blood_group}</div>
                </div>
            </div>
            
            <div class="donor-card-body">
                <div class="donor-info-grid">
                    <div class="info-box phone-box">
                        <div class="info-icon">
                            <i class="fas fa-phone-alt"></i>
                        </div>
                        <div class="info-content">
                            <span class="info-label">Phone</span>
                            <a href="tel:${donor.phone}" class="info-value">${donor.phone}</a>
                        </div>
                    </div>
                    
                    <div class="info-box email-box">
                        <div class="info-icon">
                            <i class="fas fa-envelope"></i>
                        </div>
                        <div class="info-content">
                            <span class="info-label">Email</span>
                            ${
                                donor.email
                                    ? `<a href="mailto:${donor.email}" class="info-value">${donor.email}</a>`
                                    : '<span class="info-value not-provided">Not provided</span>'
                            }
                        </div>
                    </div>
                    
                    <div class="info-box address-box">
                        <div class="info-icon">
                            <i class="fas fa-home"></i>
                        </div>
                        <div class="info-content">
                            <span class="info-label">Address</span>
                            <span class="info-value">${donor.address}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="donor-card-footer">
                ${(donor.latitude && donor.longitude) ? 
                    `<button class="action-btn directions-btn" data-lat="${donor.latitude}" data-lng="${donor.longitude}" data-name="${donor.name}">
                        <i class="fas fa-route"></i>
                        <span>Get Directions</span>
                    </button>` : ''
                }
                <button class="action-btn copy-btn" data-copy="${donor.name}|${donor.phone}|${donor.blood_group}">
                    <i class="fas fa-copy"></i>
                    <span>Copy Info</span>
                </button>
            </div>
        </div>`
        )
        .join('');

    donorsList.querySelectorAll('button[data-lat]').forEach(btn => {
        btn.addEventListener('click', () => {
            const lat = parseFloat(btn.getAttribute('data-lat'));
            const lng = parseFloat(btn.getAttribute('data-lng'));
            const name = btn.getAttribute('data-name');
            if (!lat || !lng) return;
            showOnMap(lat, lng, name);
        });
    });

    donorsList.querySelectorAll('button[data-copy]').forEach(btn => {
        btn.addEventListener('click', () => {
            const [name, phone, bloodGroup] = btn.getAttribute('data-copy').split('|');
            copyDonorInfo(name, phone, bloodGroup);
        });
    });
    
    // Update results count
    updateResultsCount(donors.length);
}

function updateResultsCount(count) {
    const resultsCountElement = document.getElementById('resultsCount');
    const filterResultsCount = document.getElementById('filterResultsCount');
    
    if (resultsCountElement && filterResultsCount) {
        resultsCountElement.textContent = count;
        filterResultsCount.style.display = 'block';
    }
}

function clearFilters() {
    document.getElementById('filterBloodGroup').value = '';
    document.getElementById('filterCity').value = '';
    document.getElementById('filterPincode').value = '';
    loadDonors();
    showAlert('Filters cleared', 'success');
}

function showOnMap(lat, lng, donorName) {
    if (!lat || !lng) {
        showAlert('No location stored for this donor.', 'error');
        return;
    }
    
    // Create Google Maps URL with directions
    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(donorName)}`;
    
    // Confirm before redirecting
    if (confirm(`Open Google Maps for directions to ${donorName}?`)) {
        window.open(googleMapsUrl, '_blank');
    }
    
    showAlert(`Redirecting to Google Maps for ${donorName}`, 'success');
}

async function copyDonorInfo(name, phone, bloodGroup) {
    const donorInfo = `Blood Donor Information:\nName: ${name}\nPhone: ${phone}\nBlood Group: ${bloodGroup}`;

    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(donorInfo);
        } else {
            const textArea = document.createElement('textarea');
            textArea.value = donorInfo;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        }
        showAlert('Donor information copied to clipboard!', 'success');
    } catch (err) {
        console.error(err);
        showAlert('Failed to copy donor information.', 'error');
    }
}

// Emergency Mode Functions
function activateEmergencyMode() {
    const emergencySection = document.getElementById('emergencySection');
    emergencySection.style.display = 'block';
    emergencySection.scrollIntoView({ behavior: 'smooth' });
    
    showAlert('🚨 Emergency Mode Activated! Getting your location...', 'info');
    
    // Get user's location for emergency search
    getUserLocationForEmergency();
}

function exitEmergencyMode() {
    const emergencySection = document.getElementById('emergencySection');
    emergencySection.style.display = 'none';
    
    // Clear emergency results
    document.getElementById('emergencyDonors').innerHTML = '<p style="color: #94a3b8;">Click "Find Emergency Resources" to search</p>';
    document.getElementById('emergencyBloodBanks').innerHTML = '<p style="color: #94a3b8;">Click "Find Emergency Resources" to search</p>';
    document.getElementById('emergencyBloodGroup').value = '';
    
    showAlert('Emergency Mode Deactivated', 'info');
}

function getUserLocationForEmergency() {
    if (!navigator.geolocation) {
        showAlert('❌ Geolocation is not supported. Please enter location manually.', 'error');
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function (position) {
            userLocation = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };
            
            // Try to get pincode from coordinates (reverse geocoding)
            reverseGeocode(userLocation.lat, userLocation.lng);
            
            showAlert('✅ Location detected! Select blood group and search for emergency resources.', 'success');
        },
        function (error) {
            console.error('Geolocation error:', error);
            showAlert('❌ Unable to get location. You can still search by manually entering details.', 'error');
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        }
    );
}

async function reverseGeocode(lat, lng) {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
        const data = await response.json();
        
        if (data && data.address) {
            const pincode = data.address.postcode;
            if (pincode) {
                userLocation.pincode = pincode;
                showLocationStatus(`📍 Detected location: ${data.display_name}`, 'success');
            }
        }
    } catch (error) {
        console.error('Reverse geocoding failed:', error);
    }
}

async function findEmergencyResources() {
    const bloodGroup = document.getElementById('emergencyBloodGroup').value;
    
    if (!bloodGroup) {
        showAlert('⚠️ Please select the required blood group first.', 'error');
        return;
    }
    
    if (!userLocation || !userLocation.pincode) {
        const manualPincode = prompt('Please enter the pincode/area code to search for emergency resources:');
        if (!manualPincode) {
            return;
        }
        userLocation = { pincode: manualPincode };
    }
    
    showAlert('🔍 Searching for emergency resources...', 'info');
    
    try {
        // Search for nearby donors
        const donorsResponse = await fetch(`/blood_donor/donors/list?blood_group=${bloodGroup}&pincode=${userLocation.pincode}&emergency=true`);
        const donorsResult = await donorsResponse.json();
        
        // Search for nearby blood banks using emergency endpoint
        const emergencyData = {
            blood_group: bloodGroup,
            pincode: userLocation.pincode,
            patient_name: 'Emergency Patient',
            contact_phone: 'Emergency Contact',
            urgency_level: 'Critical'
        };
        
        const banksResponse = await fetch('/emergency/create-request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(emergencyData)
        });
        
        const banksResult = await banksResponse.json();
        
        // Display results
        displayEmergencyDonors(donorsResult.donors || []);
        displayEmergencyBloodBanks(banksResult.nearby_banks || []);
        
        if ((donorsResult.donors && donorsResult.donors.length > 0) || 
            (banksResult.nearby_banks && banksResult.nearby_banks.length > 0)) {
            showAlert('✅ Emergency resources found! Contact details are displayed below.', 'success');
        } else {
            showAlert('⚠️ No immediate resources found. Try expanding search or contact emergency services (108).', 'error');
        }
        
    } catch (error) {
        console.error('Emergency search error:', error);
        showAlert('❌ Failed to search for emergency resources. Please try again or contact emergency services directly.', 'error');
    }
}

function displayEmergencyDonors(donors) {
    const container = document.getElementById('emergencyDonors');
    
    if (!donors.length) {
        container.innerHTML = `
            <div style="text-align: center; color: #94a3b8; padding: 2rem;">
                <i class="fas fa-users" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <p>No donors found in immediate area</p>
                <p style="font-size: 0.9rem;">Try expanding search radius or contact emergency services</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = donors.map(donor => `
        <div class="emergency-item">
            <div class="emergency-item-header">
                <div class="emergency-item-name">${donor.name}</div>
                <div class="emergency-item-blood">${donor.blood_group}</div>
            </div>
            <div class="emergency-item-details">
                <div><i class="fas fa-phone"></i> ${donor.phone}</div>
                <div><i class="fas fa-map-marker-alt"></i> ${donor.city}, ${donor.pincode}</div>
                ${donor.address ? `<div><i class="fas fa-home"></i> ${donor.address}</div>` : ''}
            </div>
            <div class="emergency-item-actions">
                <button class="btn btn-success" onclick="callDonor('${donor.phone}', '${donor.name}')">
                    <i class="fas fa-phone"></i> Call
                </button>
                ${donor.latitude && donor.longitude ? 
                    `<button class="btn btn-secondary" onclick="getDirections(${donor.latitude}, ${donor.longitude}, '${donor.name}')">
                        <i class="fas fa-directions"></i> Directions
                    </button>` : ''
                }
                <button class="btn btn-secondary" onclick="copyEmergencyDonorInfo('${donor.name}', '${donor.phone}', '${donor.blood_group}')">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>
        </div>
    `).join('');
}

function displayEmergencyBloodBanks(banks) {
    const container = document.getElementById('emergencyBloodBanks');
    
    if (!banks.length) {
        container.innerHTML = `
            <div style="text-align: center; color: #94a3b8; padding: 2rem;">
                <i class="fas fa-hospital" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <p>No blood banks found in immediate area</p>
                <p style="font-size: 0.9rem;">Contact emergency services or expand search</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = banks.map(bank => `
        <div class="emergency-item">
            <div class="emergency-item-header">
                <div class="emergency-item-name">${bank.name}</div>
                <div class="emergency-item-blood">${bank.available_units || 0} units</div>
            </div>
            <div class="emergency-item-details">
                <div><i class="fas fa-phone"></i> ${bank.phone}</div>
                <div><i class="fas fa-envelope"></i> ${bank.email || 'Not provided'}</div>
                <div><i class="fas fa-map-marker-alt"></i> ${bank.city}, ${bank.pincode}</div>
                <div><i class="fas fa-home"></i> ${bank.address}</div>
            </div>
            <div class="emergency-item-actions">
                <button class="btn btn-emergency" onclick="callBloodBank('${bank.phone}', '${bank.name}')">
                    <i class="fas fa-phone"></i> Call Bank
                </button>
                <button class="btn btn-secondary" onclick="getDirectionsToBank('${bank.address}', '${bank.name}')">
                    <i class="fas fa-directions"></i> Directions
                </button>
            </div>
        </div>
    `).join('');
}

function callDonor(phone, name) {
    if (confirm(`Call ${name} at ${phone}?`)) {
        window.open(`tel:${phone}`);
        showAlert(`Calling ${name}...`, 'info');
    }
}

function callBloodBank(phone, name) {
    if (confirm(`Call ${name} blood bank at ${phone}?`)) {
        window.open(`tel:${phone}`);
        showAlert(`Calling ${name} blood bank...`, 'info');
    }
}

function getDirections(lat, lng, name) {
    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(name)}`;
    
    if (confirm(`Open Google Maps for directions to ${name}?`)) {
        window.open(googleMapsUrl, '_blank');
        showAlert(`Opening directions to ${name}`, 'success');
    }
}

function getDirectionsToBank(address, name) {
    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(address + ', ' + name)}`;
    
    if (confirm(`Open Google Maps for directions to ${name}?`)) {
        window.open(googleMapsUrl, '_blank');
        showAlert(`Opening directions to ${name}`, 'success');
    }
}

function copyEmergencyDonorInfo(name, phone, bloodGroup) {
    const info = `EMERGENCY DONOR:\nName: ${name}\nPhone: ${phone}\nBlood Group: ${bloodGroup}\n\nTime: ${new Date().toLocaleString()}`;
    
    navigator.clipboard.writeText(info).then(() => {
        showAlert('Emergency contact info copied!', 'success');
    }).catch(() => {
        showAlert('Failed to copy information', 'error');
    });
}

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

