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

    const statusLabel = document.createElement('div');
    statusLabel.className = 'map-loading';
    statusLabel.innerHTML = '<p>Carregando a rota...</p>';
    mapContainer.appendChild(statusLabel);

    let watchId = null;
    let completed = false;
    let userMarker = null;
    let routeLine = null;
    let routeCoordinates = [];
    let isTracking = false;

    const updateStatus = (message) => {
        if (statusLabel) {
            statusLabel.innerHTML = `<p>${message}</p>`;
        }
    };

    const finishRun = () => {
        if (completed) {
            return;
        }
        completed = true;
        isTracking = false;
        if (watchId !== null && navigator.geolocation) {
            navigator.geolocation.clearWatch(watchId);
        }
        updateStatus('Parabéns! Você concluiu a corrida.');
        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('cityrunner:run-finished'));
        }
    };

    const drawRoute = (coordinates) => {
        if (routeLine) {
            map.removeLayer(routeLine);
        }

        if (coordinates.length) {
            routeCoordinates = coordinates;
            routeLine = L.polyline(coordinates, { color: '#2b7fff', weight: 6, opacity: 0.9 }).addTo(map);
            map.fitBounds(routeLine.getBounds());
        }
    };

    const toMeters = (from, to) => {
        const dx = from.lat - to.lat;
        const dy = from.lng - to.lng;
        return Math.hypot(dx, dy) * 111000;
    };

    const loadRoute = async () => {
        updateStatus('Carregando rota...');

        const startPoint = [routeData.origin.lng, routeData.origin.lat];
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
                drawRoute(routeCoords);
                updateStatus('Rota carregada. Clique em iniciar corrida para acompanhar sua posição.');
            } else {
                updateStatus('Não foi possível carregar a rota.');
            }
        } catch (error) {
            updateStatus('Não foi possível carregar a rota.');
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

        updateStatus('Rota iniciada. Siga até o destino.');

        navigator.geolocation.getCurrentPosition((position) => {
            const initialPosition = {
                lat: position.coords.latitude,
                lng: position.coords.longitude
            };

            if (userMarker) {
                map.removeLayer(userMarker);
            }

            userMarker = L.marker([initialPosition.lat, initialPosition.lng]).addTo(map).bindPopup('Você');
            map.setView([initialPosition.lat, initialPosition.lng], 16);
        });

        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const userPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };

                if (userMarker) {
                    map.removeLayer(userMarker);
                }

                userMarker = L.marker([userPosition.lat, userPosition.lng]).addTo(map).bindPopup('Você');
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
