// Blood Bank Management page JavaScript

let map;
let marker;
let selectedLat = null;
let selectedLng = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function () {
    const mapElement = document.getElementById('map');
    const formElement = document.getElementById('bloodBankForm');

    // Only run on the blood bank page
    if (!mapElement || !formElement) {
        return;
    }

    initMap();
    loadDashboardStats();
    loadBloodBanks();

    // Event listeners
    formElement.addEventListener('submit', handleSubmit);
    document.getElementById('resetForm').addEventListener('click', resetForm);
    document.getElementById('getCurrentLocation').addEventListener('click', getCurrentLocation);
    document.getElementById('dropPin').addEventListener('click', enableDropPin);
    document.getElementById('refreshBanks').addEventListener('click', loadBloodBanks);
    document.getElementById('filterCity').addEventListener('input', debounce(loadBloodBanks, 400));
    document.getElementById('filterPincode').addEventListener('input', debounce(loadBloodBanks, 400));
});

// Load dashboard statistics from database
async function loadDashboardStats() {
    try {
        const response = await fetch('/blood-bank/dashboard/stats');
        const result = await response.json();
        
        if (response.ok && result.success) {
            const stats = result.stats;
            const statsContainer = document.getElementById('dashboardStats');
            
            if (stats.total_banks === 0) {
                // Hide dashboard if no data
                statsContainer.style.display = 'none';
                return;
            }
            
            statsContainer.innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${stats.total_banks}</div>
                    <div class="stat-label">Total Blood Banks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.total_units.toLocaleString()}</div>
                    <div class="stat-label">Total Blood Units</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.critical_types}</div>
                    <div class="stat-label">Critical Stock Types</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.active_banks}</div>
                    <div class="stat-label">Active Blood Banks</div>
                </div>
            `;
        } else {
            // Hide dashboard on error
            document.getElementById('dashboardStats').style.display = 'none';
        }
    } catch (error) {
        console.error('Failed to load dashboard stats:', error);
        // Hide dashboard on error
        document.getElementById('dashboardStats').style.display = 'none';
    }
}

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
            <strong style="color: #e63946;">Blood Bank Location</strong><br>
            <small>Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}</small><br>
            <small style="color: #6b7280;">Drag to adjust position</small>
        </div>`
    );

    map.setView([lat, lng], 15);
}

function getCurrentLocation() {
    const btn = document.getElementById('getCurrentLocation');
    const text = btn.querySelector('span');

    if (!navigator.geolocation) {
        showLocationStatus('✗ Geolocation not supported by this browser', 'error');
        return;
    }

    btn.disabled = true;

    navigator.geolocation.getCurrentPosition(
        function (position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            setMarkerPosition(lat, lng);
            showLocationStatus('✓ Current location detected successfully!', 'success');

            btn.disabled = false;
        },
        function (error) {
            let errorMessage = 'Unable to get location: ';
            switch (error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage += 'Location access denied by user';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage += 'Location information unavailable';
                    break;
                case error.TIMEOUT:
                    errorMessage += 'Location request timed out';
                    break;
                default:
                    errorMessage += 'Unknown location error';
                    break;
            }

            showLocationStatus('✗ ' + errorMessage, 'error');
            btn.disabled = false;
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000
        }
    );
}

// Enable drop pin mode
function enableDropPin() {
    showLocationStatus('📍 Click anywhere on the map to drop a pin', 'info');
    map.getContainer().style.cursor = 'crosshair';
    
    // Add click handler for dropping pin
    map.once('click', function(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        setMarkerPosition(lat, lng);
        showLocationStatus('✅ Pin dropped! You can drag it to adjust the position', 'success');
        map.getContainer().style.cursor = '';
    });
}

function searchAddress() {
    const address = document.getElementById('bankAddress').value || document.getElementById('address')?.value || '';
    const city = document.getElementById('bankCity').value || document.getElementById('city')?.value || '';
    const pincode = document.getElementById('bankPincode').value || document.getElementById('pincode')?.value || '';

    if (!address && !city) {
        showAlert('Please enter an address or city to search', 'error');
        return;
    }

    const searchQuery = `${address} ${city} ${pincode}`.trim();

    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&limit=1`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lng = parseFloat(data[0].lon);
                setMarkerPosition(lat, lng);
                showLocationStatus('✓ Address found and location set', 'success');
            } else {
                showLocationStatus('✗ Address not found', 'error');
            }
        })
        .catch(error => {
            console.error('Geocoding error:', error);
            showLocationStatus('✗ Error searching for address', 'error');
        });
}

function showLocationStatus(message, type) {
    const statusDiv = document.getElementById('locationStatus');
    if (!statusDiv) return;

    statusDiv.textContent = message;
    statusDiv.className = `location-status ${type}`;
    statusDiv.style.display = 'block';

    if (type === 'success') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
}

function showAlert(message, type) {
    const alertDiv = document.getElementById('alert');
    if (!alertDiv) return;

    alertDiv.textContent = message;
    alertDiv.className = `alert ${type}`;
    alertDiv.style.display = 'block';

    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 5000);
}

function handleSubmit(e) {
    e.preventDefault();
    e.stopPropagation();

    // Location is now optional - users can submit without selecting location
    // if (!selectedLat || !selectedLng) {
    //     showAlert('Please select a location on the map', 'error');
    //     return;
    // }

    const submitBtn = document.querySelector('#bloodBankForm button[type="submit"]');
    console.log('Submit button found:', submitBtn);
    
    if (submitBtn) {
        submitBtn.disabled = true;
        console.log('Button disabled, current innerHTML:', submitBtn.innerHTML);
    }

    const formData = {
        name: document.getElementById('name').value,
        phone: document.getElementById('phone').value,
        email: document.getElementById('email').value,
        address: document.getElementById('address').value,
        city: document.getElementById('city').value,
        pincode: document.getElementById('pincode').value,
        latitude: selectedLat,
        longitude: selectedLng,
        units_A_pos: document.getElementById('units_A_pos')?.value || 0,
        units_A_neg: document.getElementById('units_A_neg')?.value || 0,
        units_B_pos: document.getElementById('units_B_pos')?.value || 0,
        units_B_neg: document.getElementById('units_B_neg')?.value || 0,
        units_AB_pos: document.getElementById('units_AB_pos')?.value || 0,
        units_AB_neg: document.getElementById('units_AB_neg')?.value || 0,
        units_O_pos: document.getElementById('units_O_pos')?.value || 0,
        units_O_neg: document.getElementById('units_O_neg')?.value || 0
    };

    console.log('Submitting form data:', formData);

    fetch('/blood-bank/add_blood_bank', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            if (data.success) {
                showAlert('Blood bank added successfully!', 'success');
                resetForm();
                loadBloodBanks();
                loadDashboardStats(); // Refresh dashboard stats
            } else {
                showAlert(data.error || 'Failed to add blood bank', 'error');
            }
            console.log('About to reset button in then block');
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Failed to add blood bank', 'error');
        })
        .finally(() => {
            console.log('In finally block, resetting button');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-plus"></i> Add Blood Bank';
                console.log('Button reset complete, innerHTML now:', submitBtn.innerHTML);
            }
            console.log('Blood bank form submission completed');
        });
}

function resetForm() {
    const form = document.getElementById('bloodBankForm');
    if (form) form.reset();

    document.getElementById('latitude').value = '';
    document.getElementById('longitude').value = '';

    if (marker) {
        map.removeLayer(marker);
        marker = null;
    }

    selectedLat = null;
    selectedLng = null;

    showLocationStatus('Form reset', 'success');
}

function loadBloodBanks() {
    const cityInput = document.getElementById('filterCity');
    const pincodeInput = document.getElementById('filterPincode');

    const city = cityInput ? cityInput.value : '';
    const pincode = pincodeInput ? pincodeInput.value : '';

    let url = '/blood-bank/blood_banks/list?';
    if (city) url += `city=${encodeURIComponent(city)}&`;
    if (pincode) url += `pincode=${encodeURIComponent(pincode)}&`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayBloodBanks(data.blood_banks || []);
        })
        .catch(error => {
            console.error('Error loading blood banks:', error);
            showAlert('Failed to load blood banks', 'error');
        });
}

function displayBloodBanks(bloodBanks) {
    const container = document.getElementById('bloodBanksList');
    if (!container) return;

    if (bloodBanks.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: #94a3b8; padding: 2rem;">
                <i class="fas fa-search" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>No blood banks found matching your criteria.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = bloodBanks.map(bank => {
        const bloodUnits = bank.available_blood_groups || {};
        const bloodUnitsHtml = Object.entries(bloodUnits).map(([type, count]) => `
            <div class="blood-unit">
                <span class="blood-unit-type">${type}</span>
                <span class="blood-unit-count">${count} units</span>
            </div>
        `).join('');

        return `
            <div class="blood-bank-card">
                <div class="bank-header">
                    <h3 class="bank-name">${bank.name}</h3>
                    <div class="bank-actions">
                        ${(bank.latitude && bank.longitude) ? 
                            `<button class="btn btn-secondary" data-bank-id="${bank.id}" data-action="show" data-lat="${bank.latitude}" data-lng="${bank.longitude}">
                                <i class="fas fa-directions"></i> Get Directions
                            </button>` : ''
                        }
                        <button class="btn btn-secondary" data-bank-id="${bank.id}" data-action="edit">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn btn-danger" data-bank-id="${bank.id}" data-action="delete">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
                
                <div class="bank-info">
                    <div class="bank-info-item">
                        <i class="fas fa-phone"></i> ${bank.phone}
                    </div>
                    <div class="bank-info-item">
                        <i class="fas fa-envelope"></i> ${bank.email || 'Not provided'}
                    </div>
                    <div class="bank-info-item">
                        <i class="fas fa-map-marker-alt"></i> ${bank.city}, ${bank.pincode}
                    </div>
                </div>
                
                <div class="bank-info-item" style="margin-top: 0.5rem;">
                    <i class="fas fa-home"></i> ${bank.address}
                </div>
                
                ${bloodUnitsHtml ? `
                    <div class="blood-units">
                        ${bloodUnitsHtml}
                    </div>
                ` : '<p style="color: #94a3b8; margin-top: 1rem;">No blood units information</p>'}
            </div>
        `;
    }).join('');

    // Attach event listeners for edit/delete
    container.querySelectorAll('button[data-action]').forEach(btn => {
        const id = btn.getAttribute('data-bank-id');
        const action = btn.getAttribute('data-action');
        if (action === 'delete') {
            btn.addEventListener('click', () => deleteBloodBank(id));
        } else if (action === 'edit') {
            btn.addEventListener('click', () => editBloodBank(id));
        } else if (action === 'show') {
            const lat = parseFloat(btn.getAttribute('data-lat'));
            const lng = parseFloat(btn.getAttribute('data-lng'));
            const name = btn.closest('.blood-bank-card')?.querySelector('.bank-name')?.textContent || 'Blood Bank';
            btn.addEventListener('click', () => showOnMap(lat, lng, name));
        }
    });
}

function editBloodBank() {
    showAlert('Edit functionality coming soon!', 'info');
}

function deleteBloodBank(bankId) {
    if (!confirm('Are you sure you want to deactivate this blood bank?')) {
        return;
    }

    fetch(`/blood-bank/blood_banks/${bankId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Blood bank deactivated successfully', 'success');
                loadBloodBanks();
            } else {
                showAlert(data.error || 'Failed to deactivate blood bank', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Failed to deactivate blood bank', 'error');
        });
}

function showOnMap(lat, lng, name) {
    if (!lat || !lng) {
        showAlert('No location stored for this blood bank.', 'error');
        return;
    }
    
    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(name)}`;
    
    // Confirm before redirecting
    if (confirm(`Open Google Maps for directions to ${name}?`)) {
        window.open(googleMapsUrl, '_blank');
    }
    
    showAlert(`Redirecting to Google Maps for ${name}`, 'success');
}

// Simple debounce helper
function debounce(fn, delay) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}

