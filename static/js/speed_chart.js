// Speed Chart Analysis JavaScript
let speedChart = null;

// Get track ID from URL
function getTrackId() {
    const path = window.location.pathname;
    const match = path.match(/\/speed_chart\/(\d+)/);
    return match ? match[1] : null;
}

// Load page data when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // console.log("document.addEventListener before loadSpeedChart");  // for debug
    loadSpeedChart();
    // console.log("document.addEventListener after loadSpeedChart");   // for debug
    
    // Bind form submission
    const form = document.getElementById('speedAnalysisForm');
    // console.log("document.addEventListener const form");         // for debug
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
    }
});

// Load and display speed chart
function loadSpeedChart() {
    const loading = document.getElementById('chartLoading');
    const canvas = document.getElementById('speedChart');
    const trackId = getTrackId();
    console.log('Track ID:', trackId);   // for debug
    
    if (!trackId) {
        loading.innerHTML = '<div class="error">No track ID found</div>';
        return;
    }
    
    loading.style.display = 'block';
    canvas.style.display = 'none';
    
    const endpoint = [`/api/track/${trackId}/speeds`];
    
    tryLoadFromEndpoints(endpoint, 0, loading, canvas);
}

function tryLoadFromEndpoints(endpoints, index, loading, canvas) {
    if (index >= endpoints.length) {
        loading.innerHTML = `
            <div class="error">
                Could not find speed data API endpoint.<br>
                Tried: ${endpoints.join(', ')}<br>
                Please check your Flask routes.
            </div>
        `;
        return;
    }
    
    const endpoint = endpoints[index];
    console.log(`Trying endpoint: ${endpoint}`);
    
    fetch(endpoint)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Speed data received from:', endpoint, data);
            createSpeedChart(data);
            
            loading.style.display = 'none';
            canvas.style.display = 'block';
        })
        .catch(error => {
            console.log(`Endpoint ${endpoint} failed:`, error.message);
            // Try next endpoint
            tryLoadFromEndpoints(endpoints, index + 1, loading, canvas);
        });
}

// Create speed chart
function createSpeedChart(data) {
    const ctx = document.getElementById('speedChart').getContext('2d');
    
    if (speedChart) {
        speedChart.destroy();
    }
    
    speedChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps || [],
            datasets: [
                {
                    label: 'Original Speed',
                    data: data.raw_speeds || [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: 'Processed Speed',
                    data: data.processed_speeds || [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Speed (km/h)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Data Points'
                    }
                }
            },
            plugins: {
                // title: {
                //     display: true,
                //     text: `Speed Comparison - ${(data.raw_speeds || []).length} data points`
                // },
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}

// Update statistics display (only called after form submission)
function updateStatistics(data) {
    console.log('Full data received:', data); // ← debug
    const stats = data.statistics || {};
    
    // Find and update result cards
    const resultCards = document.querySelectorAll('.result-card h4');

    if (resultCards[0] && stats.avg_speed !== undefined) {           // The first: Average Speed
        resultCards[0].textContent = stats.avg_speed.toFixed(2);
    }
    if (resultCards[1] && stats.outliers_detected !== undefined) {   // The second：Outliers
        resultCards[1].textContent = stats.outliers_detected;
    }
    if (resultCards[2] && stats.total_distance !== undefined) {      // The third：Distance
        resultCards[2].textContent = stats.total_distance.toFixed(2);
    }
    if (resultCards[3] && stats.processed_max_speed !== undefined) { // The last：Max Speed
        resultCards[3].textContent = stats.processed_max_speed.toFixed(2);
    }

}

// Handle form submission
function handleFormSubmission(e) {
    e.preventDefault();
    const trackId = getTrackId();
    if (!trackId) {
        alert('No track ID found');
        return;
    }
    
    const formData = new FormData(e.target);
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    submitBtn.innerHTML = 'Processing...';
    submitBtn.disabled = true;
    
    fetch(`/speed_chart/${trackId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('=== DEBUGGING RESPONSE ===');
        console.log('Full response:', JSON.stringify(data, null, 2));
        console.log('data.success:', data.success);
        console.log('data.statistics:', data.statistics);
        console.log('data keys:', Object.keys(data));
        console.log('========================');
        if (data.success) {
            updateStatistics(data);
            loadSpeedChart();
            alert('Processing completed successfully!');
        } else {
            throw new Error(data.error || 'Processing failed');
        }
    })
    .catch(error => {
        alert('Error processing track: ' + error.message);
        console.error('Processing error:', error);
    })
    .finally(() => {
        console.log('fetch finally:');
        submitBtn.innerHTML = 'Apply New Processing';
        submitBtn.disabled = false;
    });
}

// Reset to defaults
function resetToDefaults() {
    document.getElementById('use_iqr').checked = true;
    document.getElementById('window_size').value = '2';
    document.getElementById('interpolation_method').value = 'linear';
}

// Go to dashboard
function goToDashboard(button) {
    const source = button?.dataset?.source || 'my';
    const target = source === 'public' ? '/dashboard_public' : '/dashboard';
    window.location.href = target;
}