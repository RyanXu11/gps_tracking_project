let previewChart = null;

function showQuickPreview() {
    const previewDiv = document.getElementById('quickPreview');
    const loading = document.getElementById('previewLoading');
    const canvas = document.getElementById('previewChart');
    
    previewDiv.style.display = 'block';
    loading.style.display = 'block';
    canvas.style.display = 'none';
    
    // Scroll to preview
    previewDiv.scrollIntoView({ behavior: 'smooth' });
    
    // Destroy existing chart
    if (previewChart) {
        previewChart.destroy();
    }
    
    // Fetch speed data for preview
    makeAjaxRequest(`/api/track/{{ track_id }}/speeds`)
        .then(data => {
            loading.style.display = 'none';
            canvas.style.display = 'block';
            
            // Create simplified preview chart
            const ctx = canvas.getContext('2d');
            previewChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.timestamps.filter((_, i) => i % 5 === 0), // Sample every 5th point for preview
                    datasets: [{
                        label: 'Speed',
                        data: data.processed_speeds.filter((_, i) => i % 5 === 0),
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
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
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Speed Profile Preview'
                        },
                        legend: {
                            display: false
                        }
                    }
                }
            });
        })
        .catch(error => {
            loading.innerHTML = '<div class="error">Failed to load preview data</div>';
            console.error('Error loading preview:', error);
        });
}

function hideQuickPreview() {
    document.getElementById('quickPreview').style.display = 'none';
    if (previewChart) {
        previewChart.destroy();
        previewChart = null;
    }
}

// Auto-focus on main action
document.addEventListener('DOMContentLoaded', function() {
    // Add some celebration effect
    const header = document.querySelector('.success-header');
    header.style.animation = 'fadeInScale 0.6s ease-out';
    
    // Focus on dashboard button for keyboard users
    document.querySelector('.btn-primary').focus();
});
