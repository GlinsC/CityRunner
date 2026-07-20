window.CITYRUNNER_MAP_INIT = function (routeData) {
    const mapContainer = document.getElementById('map');
    if (!mapContainer || !routeData) {
        return;
    }

    if (typeof google === 'undefined' || !google.maps) {
        mapContainer.innerHTML = '<div class="map-loading"><p>Adicione a chave da API do Google Maps para exibir o trajeto real.</p></div>';
        return;
    }

    const map = new google.maps.Map(mapContainer, {
        center: routeData.origin,
        zoom: 15,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false
    });

    const originMarker = new google.maps.Marker({ position: routeData.origin, map, title: 'Origem' });
    const destinationMarker = new google.maps.Marker({ position: routeData.destination, map, title: 'Destino' });

    const bounds = new google.maps.LatLngBounds();
    bounds.extend(routeData.origin);
    bounds.extend(routeData.destination);
    map.fitBounds(bounds);

    const statusLabel = document.createElement('div');
    statusLabel.className = 'map-loading';
    statusLabel.innerHTML = '<p>Pronto para começar. Clique em iniciar corrida.</p>';
    mapContainer.appendChild(statusLabel);

    let watchId = null;
    let routeProgress = [];
    let completed = false;
    let userMarker = null;
    let currentPolyline = null;

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
        if (watchId !== null && navigator.geolocation) {
            navigator.geolocation.clearWatch(watchId);
        }
        updateStatus('Parabéns! Você concluiu a corrida.');
        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('cityrunner:run-finished'));
        }
    };

    const drawProgressPath = (points) => {
        if (currentPolyline) {
            currentPolyline.setMap(null);
        }

        if (points.length > 1) {
            currentPolyline = new google.maps.Polyline({
                path: points,
                geodesic: true,
                strokeColor: '#ffffff',
                strokeOpacity: 0.95,
                strokeWeight: 4,
                map
            });
        }
    };

    const startRun = () => {
        if (!navigator.geolocation) {
            updateStatus('Seu navegador não suporta geolocalização.');
            return;
        }

        updateStatus('Rota iniciada. Siga até o destino.');

        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const userPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };

                routeProgress.push(userPosition);

                if (userMarker) {
                    userMarker.setMap(null);
                }

                userMarker = new google.maps.Marker({
                    position: userPosition,
                    map,
                    title: 'Você'
                });

                const distanceToDestination = google.maps.geometry.spherical.computeDistanceBetween(
                    new google.maps.LatLng(userPosition.lat, userPosition.lng),
                    new google.maps.LatLng(routeData.destination.lat, routeData.destination.lng)
                );

                if (distanceToDestination <= 50) {
                    finishRun();
                    return;
                }

                drawProgressPath(routeProgress.slice(-50));
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

    const startButton = document.getElementById('start-run-btn');
    if (startButton) {
        startButton.addEventListener('click', startRun, { once: true });
    }
};
