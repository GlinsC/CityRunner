window.CITYRUNNER_MAP_INIT = function (routeData) {
    const mapContainer = document.getElementById('map');
    if (!mapContainer || !routeData) {
        return;
    }

    if (mapContainer.dataset.initialized === 'true') {
        return;
    }
    mapContainer.dataset.initialized = 'true';

    if (typeof L === 'undefined') {
        mapContainer.innerHTML = '<div class="map-loading"><p>Não foi possível carregar o mapa.</p></div>';
        return;
    }

    mapContainer.innerHTML = '';

    const map = L.map(mapContainer, { zoomControl: true }).setView([routeData.origin.lat, routeData.origin.lng], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    L.marker([routeData.origin.lat, routeData.origin.lng]).addTo(map).bindPopup('Origem');
    L.marker([routeData.destination.lat, routeData.destination.lng]).addTo(map).bindPopup('Destino');

    const bounds = L.latLngBounds([routeData.origin, routeData.destination]);
    map.fitBounds(bounds);

    const createMarkerIcon = (emoji, color) => L.divIcon({
        html: `<div class="map-marker ${color}">${emoji}</div>`,
        className: 'map-marker-wrapper',
        iconSize: [42, 42],
        iconAnchor: [21, 42]
    });

    const startIcon = createMarkerIcon('🏁', 'start-icon');
    const finishIcon = createMarkerIcon('🎯', 'finish-icon');
    const userIcon = createMarkerIcon('🏃', 'user-icon');

    L.marker([routeData.origin.lat, routeData.origin.lng], { icon: startIcon }).addTo(map).bindPopup('Origem');
    L.marker([routeData.destination.lat, routeData.destination.lng], { icon: finishIcon }).addTo(map).bindPopup('Destino');

    const statusLabel = document.createElement('div');
    statusLabel.className = 'map-loading map-status';
    statusLabel.innerHTML = '<p>Carregando a rota...</p>';
    mapContainer.appendChild(statusLabel);

    let watchId = null;
    let completed = false;
    let userMarker = null;
    let routeLine = null;
    let routeCoordinates = [];
    let isTracking = false;
    let startTime = null;
    let elapsedSeconds = 0;
    let timerId = null;
    let distanceMeters = 0;
    let lastPosition = null;

    const updateStatus = (message) => {
        if (statusLabel) {
            statusLabel.innerHTML = `<p>${message}</p>`;
        }
    };

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const formatPace = (seconds, meters) => {
        if (!meters || meters <= 0) {
            return 'Pace indisponível';
        }
        const minutesPerKm = (seconds / 60) / (meters / 1000);
        const minutes = Math.floor(minutesPerKm);
        const secs = Math.round((minutesPerKm - minutes) * 60);
        return `${minutes}:${secs.toString().padStart(2, '0')} /km`;
    };

    const stopTimer = () => {
        if (timerId) {
            clearInterval(timerId);
            timerId = null;
        }
    };

    const startTimer = () => {
        startTime = Date.now();
        elapsedSeconds = 0;
        stopTimer();
        timerId = setInterval(() => {
            elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
            updateStatus(`Tempo: ${formatTime(elapsedSeconds)} • ${Math.round(distanceMeters / 1000 * 10) / 10} km`);
        }, 1000);
    };

    const finishRun = () => {
        if (completed) {
            return;
        }
        completed = true;
        isTracking = false;
        stopTimer();
        if (watchId !== null && navigator.geolocation) {
            navigator.geolocation.clearWatch(watchId);
        }
        const distanceKm = Math.round((distanceMeters / 1000) * 10) / 10;
        const pace = formatPace(elapsedSeconds, distanceMeters);
        updateStatus(`Parabéns! Você concluiu a corrida em ${formatTime(elapsedSeconds)}. Pace: ${pace}.`);
        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('cityrunner:run-finished'));
        }
    };

    const drawRoute = (coordinates, options = {}) => {
        if (routeLine) {
            map.removeLayer(routeLine);
        }

        if (coordinates.length) {
            routeCoordinates = coordinates;
            routeLine = L.polyline(coordinates, {
                color: '#ff7a1a',
                weight: 7,
                opacity: 0.95,
                lineCap: 'round',
                lineJoin: 'round',
                dashArray: '8 8',
                ...options
            }).addTo(map);
            map.fitBounds(routeLine.getBounds());
        }
    };

    const toMeters = (from, to) => {
        const dx = from.lat - to.lat;
        const dy = from.lng - to.lng;
        return Math.hypot(dx, dy) * 111000;
    };

    const loadRoute = async () => {
        const previewPath = [
            [routeData.origin.lat, routeData.origin.lng],
            [routeData.destination.lat, routeData.destination.lng]
        ];
        drawRoute(previewPath, {
            color: '#f59e0b',
            weight: 6,
            opacity: 0.7,
            dashArray: '6 6'
        });
        updateStatus('Carregando rota...');
    };

    const loadRealRouteFromUser = async (startPosition) => {
        if (routeLine) {
            map.removeLayer(routeLine);
        }

        const startPoint = [startPosition.lng, startPosition.lat];
        const endPoint = [routeData.destination.lng, routeData.destination.lat];

        try {
            const response = await fetch('https://api.openrouteservice.org/v2/directions/foot-walking/geojson', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json, application/geo+json',
                    'Content-Type': 'application/json',
                    'Authorization': window.OPENROUTESERVICE_API_KEY
                },
                body: JSON.stringify({
                    coordinates: [startPoint, endPoint],
                    instructions: false,
                    preference: 'recommended'
                })
            });

            const data = await response.json();
            const coordinates = data.features?.[0]?.geometry?.coordinates || [];
            if (coordinates.length) {
                const routeCoords = coordinates.map(([lng, lat]) => [lat, lng]);
                drawRoute(routeCoords, {
                    color: '#22c55e',
                    weight: 7,
                    opacity: 0.95,
                    dashArray: ''
                });
                updateStatus('Rota real iniciada. Siga o trajeto até o destino.');
            } else {
                updateStatus('Não foi possível encontrar uma rota real a partir da sua posição.');
            }
        } catch (error) {
            updateStatus('Não foi possível carregar a rota real.');
        }
    };

    const startRun = async () => {
        if (!navigator.geolocation) {
            updateStatus('Seu navegador não suporta geolocalização.');
            return;
        }

        if (isTracking) {
            return;
        }

        isTracking = true;

        if (!routeCoordinates.length) {
            await loadRoute();
        }

        updateStatus('Buscando sua posição e montando a rota real...');
        startTimer();
        distanceMeters = 0;
        lastPosition = null;

        navigator.geolocation.getCurrentPosition(async (position) => {
            const initialPosition = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };

            if (userMarker) {
                map.removeLayer(userMarker);
            }

            userMarker = L.marker([initialPosition.lat, initialPosition.lng], { icon: userIcon }).addTo(map).bindPopup('Você');
            map.flyTo([initialPosition.lat, initialPosition.lng], 17, { duration: 1.2 });

            await loadRealRouteFromUser(initialPosition);
            updateStatus('Rota iniciada. Siga até o destino.');
        });

        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const userPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };

                if (lastPosition) {
                    const segmentMeters = toMeters(lastPosition, userPosition);
                    distanceMeters += segmentMeters;
                }
                lastPosition = userPosition;

                if (userMarker) {
                    map.removeLayer(userMarker);
                }

                userMarker = L.marker([userPosition.lat, userPosition.lng], { icon: userIcon }).addTo(map).bindPopup('Você');
                map.panTo([userPosition.lat, userPosition.lng]);

                const distanceToDestination = toMeters(userPosition, routeData.destination);
                if (distanceToDestination <= 50) {
                    finishRun();
                    return;
                }

                updateStatus(`Você está a ${Math.round(distanceToDestination)} metros do fim da rota.`);
            },
            () => {
                updateStatus('Não foi possível acessar a sua localização.');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    };

    loadRoute();

    const startButton = document.getElementById('start-run-btn');
    if (startButton) {
        startButton.addEventListener('click', startRun);
    }
};
