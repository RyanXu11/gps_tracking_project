// chart.js - Speed Chart JavaScript

let speedChart = null;

function renderSpeedChart() {
    // Get track data (you'll need to pass this from backend)
    const trackId = window.trackId; // Will be set from template
    
    // Fetch speed data
    fetch(`/api/track/${trackId}/speeds`)
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('speedChart').getContext('2d');
            
            // Destroy existing chart if exists
            if (speedChart) {
                speedChart.destroy();
            }
            
            // Create new chart
            speedChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.timestamps,
                    datasets: [{
                        label: 'Speed (km/h)',
                        data: data.speeds,
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        borderWidth: 1,
                        pointRadius: 1,
                        pointHoverRadius: 4,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            display: false // Hide x-axis labels since we show start/end time
                        },
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Speed (km/h)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Speed: ${context.parsed.y.toFixed(1)} km/h`;
                                }
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });
            
            // Update data point count
            document.getElementById('dataPointCount').textContent = data.speeds.length;
        })
        .catch(error => {
            console.error('Error loading speed data:', error);
            document.getElementById('dataPointCount').textContent = 'Error loading data';
        });
}

// Initialize chart when page loads
document.addEventListener('DOMContentLoaded', renderSpeedChart);