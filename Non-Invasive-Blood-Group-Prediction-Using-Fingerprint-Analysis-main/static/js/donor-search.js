// Donor Search functionality
function initDonorSearch() {
    const donorForm = document.getElementById('donor-search-form');
    if (donorForm) {
        donorForm.addEventListener('submit', handleDonorSearch);
    }
}

let currentPage = 1;
let totalPages = 1;
let currentSearchParams = {};

async function handleDonorSearch(e) {
    e.preventDefault();
    
    const bloodGroup = document.getElementById('blood-group-search').value;
    const pincode = document.getElementById('pincode-search').value;
    
    currentSearchParams = { bloodGroup, pincode };
    currentPage = 1;
    
    performSearch();
}

async function performSearch() {
    const { bloodGroup, pincode } = currentSearchParams;
    
    try {
        const params = new URLSearchParams({
            blood_group: bloodGroup,
            pincode: pincode
        });
        
        const response = await fetch(`/blood_donor/donors/search?${params}`);
        
        const result = await response.json();
        
        if (result.success) {
            displaySearchResults(result.donors, result.blood_banks);
        } else {
            throw new Error(result.error || 'Search failed');
        }
        
    } catch (error) {
        showMessage('Search failed: ' + error.message, 'error');
    }
}

// Display search results with pagination
function displaySearchResults(donors, bloodBanks) {
    const resultsDiv = document.getElementById('search-results');
    const donorsList = document.getElementById('donors-list');
    
    // Paginate donors - 10 per page
    const itemsPerPage = 10;
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedDonors = donors.slice(startIndex, endIndex);
    totalPages = Math.ceil(donors.length / itemsPerPage);
    
    let html = '';
    
    // Show summary header
    html += `
        <div class="search-summary">
            <h3><i class="fas fa-search"></i> Search Results</h3>
            <div class="search-stats">
                <span class="stat-badge"><i class="fas fa-users"></i> ${donors.length} Donors</span>
                <span class="stat-badge"><i class="fas fa-hospital"></i> ${bloodBanks ? bloodBanks.length : 0} Blood Banks</span>
            </div>
        </div>
    `;
    
    // Show blood banks if any
    if (bloodBanks && bloodBanks.length > 0) {
        html += '<div class="blood-banks-section"><h4><i class="fas fa-hospital"></i> Blood Banks</h4>';
        bloodBanks.forEach(bank => {
            html += `
                <div class="donor-card bank-card">
                    <div class="card-header">
                        <h4><i class="fas fa-hospital"></i> ${bank.name}</h4>
                        <span class="badge blood-badge">Blood Bank</span>
                    </div>
                    <div class="card-body">
                        <p><i class="fas fa-phone"></i> <strong>Phone:</strong> ${bank.phone}</p>
                        <p><i class="fas fa-envelope"></i> <strong>Email:</strong> ${bank.email || 'N/A'}</p>
                        <p><i class="fas fa-map-marker-alt"></i> <strong>Address:</strong> ${bank.address}, ${bank.city}, ${bank.pincode}</p>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    // Show donors
    if (donors.length === 0) {
        html += '<div class="no-results"><i class="fas fa-info-circle"></i> No donors found in this area. Try expanding your search or contact emergency services.</div>';
    } else {
        html += '<div class="donors-section"><h4><i class="fas fa-hand-holding-heart"></i> Blood Donors (Page ' + currentPage + ' of ' + totalPages + ')</h4>';
        paginatedDonors.forEach((donor, idx) => {
            html += `
                <div class="donor-card" style="animation-delay: ${idx * 0.1}s">
                    <div class="card-header">
                        <h4><i class="fas fa-user"></i> ${donor.name}</h4>
                        <span class="badge donor-badge">${donor.blood_group}</span>
                    </div>
                    <div class="card-body">
                        <p><i class="fas fa-phone"></i> <strong>Phone:</strong> <a href="tel:${donor.phone}">${donor.phone}</a></p>
                        ${donor.email ? `<p><i class="fas fa-envelope"></i> <strong>Email:</strong> <a href="mailto:${donor.email}">${donor.email}</a></p>` : ''}
                        <p><i class="fas fa-map-marker-alt"></i> <strong>Location:</strong> ${donor.address}, ${donor.city}, ${donor.pincode}</p>
                        <p><i class="fas fa-clock"></i> <strong>Last Updated:</strong> ${donor.last_updated ? new Date(donor.last_updated).toLocaleDateString() : 'Unknown'}</p>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        // Add pagination controls
        if (totalPages > 1) {
            html += '<div class="pagination">';
            if (currentPage > 1) {
                html += '<button class="page-btn" onclick="goToPage(' + (currentPage - 1) + ')"><i class="fas fa-chevron-left"></i> Previous</button>';
            }
            for (let i = 1; i <= totalPages; i++) {
                if (i === currentPage) {
                    html += '<button class="page-btn active">' + i + '</button>';
                } else {
                    html += '<button class="page-btn" onclick="goToPage(' + i + ')">' + i + '</button>';
                }
            }
            if (currentPage < totalPages) {
                html += '<button class="page-btn" onclick="goToPage(' + (currentPage + 1) + ')">Next <i class="fas fa-chevron-right"></i></button>';
            }
            html += '</div>';
        }
    }
    
    donorsList.innerHTML = html;
    resultsDiv.style.display = 'block';
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function goToPage(page) {
    currentPage = page;
    performSearch();
}