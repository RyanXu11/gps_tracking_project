let map;
const polylines = []; // Stores all polylines with their trackId as key
const markers = [];   // Stores all markers with their trackId as key
const colors = ["#FF0000", "#0000FF", "#00AA00", "#FF9900", "#AA00FF"];
let colorIndex = 0;

function initMap() {
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 14,
        center: { lat: 45.4215, lng: -75.6972 }
    });

    // Set up event listeners for all track buttons
    document.querySelectorAll(".show-track").forEach(btn => {
        btn.addEventListener("click", function (event) {
            event.preventDefault();
            const trackId = this.getAttribute("data-track-id");
            toggleTrack(trackId, this);
        });
    });
}

function toggleTrack(trackId, button) {
    // Check if track is already displayed
    const isDisplayed = polylines.some(p => p.trackId === trackId);
    
    if (isDisplayed) {
        // Remove the track from map
        removeTrack(trackId);
        // Update button text and class
        button.textContent = "Show on Map";
        button.classList.remove('active');
    } else {
        // Load and display the track
        loadTrack(trackId);
        // Update button text and class
        button.textContent = "Hide from Map";
        button.classList.add('active');
    }
}

function loadTrack(trackId) {
    fetch(`/api/track_coords/${trackId}`)
        .then(response => response.json())
        .then(data => {
            const path = data.coords.map(pt => ({ lat: pt.lat, lng: pt.lon }));

            if (path.length === 0) {
                console.warn("No coordinates found.");
                return;
            }

            // Assign color
            const color = colors[colorIndex % colors.length];
            colorIndex++;

            // Create polyline
            const polyline = new google.maps.Polyline({
                path: path,
                map: map,
                strokeColor: color,
                strokeOpacity: 1.0,
                strokeWeight: 3,
            });
            polyline.trackId = trackId; // Store trackId with polyline
            polylines.push(polyline);

            // Add start/end markers
            const startMarker = new google.maps.Marker({
                position: path[0],
                map: map,
                label: "A",
                title: `Start of Track ${trackId}`,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 5,
                    fillColor: color,
                    fillOpacity: 1,
                    strokeColor: "#000",
                    strokeWeight: 1
                }
            });
            startMarker.trackId = trackId;

            const endMarker = new google.maps.Marker({
                position: path[path.length - 1],
                map: map,
                label: "B",
                title: `End of Track ${trackId}`,
                icon: {
                    path: google.maps.SymbolPath.BACKWARD_CLOSED_ARROW,
                    scale: 4,
                    fillColor: color,
                    fillOpacity: 1,
                    strokeColor: "#000",
                    strokeWeight: 1
                }
            });
            endMarker.trackId = trackId;

            markers.push(startMarker, endMarker);

            // Center map on the track if it's the first one being displayed
            if (polylines.length === 1) {
                map.setCenter(path[0]);
            }
        })
        .catch(error => {
            console.error("Error loading track coordinates:", error);
        });
}

function removeTrack(trackId) {
    // Remove polylines
    for (let i = polylines.length - 1; i >= 0; i--) {
        if (polylines[i].trackId === trackId) {
            polylines[i].setMap(null);
            polylines.splice(i, 1);
        }
    }
    
    // Remove markers
    for (let i = markers.length - 1; i >= 0; i--) {
        if (markers[i].trackId === trackId) {
            markers[i].setMap(null);
            markers.splice(i, 1);
        }
    }
}

// <!-- Google Maps API -->
<script async src="https://maps.googleapis.com/maps/api/js?key={{ config.GOOGLE_MAPS_API_KEY }}&callback=initMap"></script>