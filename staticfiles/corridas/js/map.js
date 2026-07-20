window.CITYRUNNER_MAP_INIT = function (routeData) {
    const mapContainer = document.getElementById('map');
    if (!mapContainer || !routeData) {
        return;
    }

    mapContainer.innerHTML = '<div class="map-loading"><p>Iniciando corrida e preparando o trajeto...</p></div>';

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

    const path = [routeData.origin, routeData.destination];
    const polyline = new google.maps.Polyline({
        path,
        geodesic: true,
        strokeColor: '#62f2c2',
        strokeOpacity: 0.9,
        strokeWeight: 5,
        map
    });

    const bounds = new google.maps.LatLngBounds();
    bounds.extend(routeData.origin);
    bounds.extend(routeData.destination);
    map.fitBounds(bounds);

    let watchId = null;
    let routeProgress = [];
    let completed = false;
    const statusLabel = document.createElement('div');
    statusLabel.className = 'map-loading';
    statusLabel.innerHTML = '<p>Preparando corrida...</p>';
    mapContainer.appendChild(statusLabel);

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

    const checkProgress = (position) => {
        const userPosition = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
        };

        routeProgress.push(userPosition);

        const userMarker = new google.maps.Marker({
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

        updateStatus(`Você está a ${Math.round(distanceToDestination)} metros do fim da rota.`);

        if (routeProgress.length > 1) {
            const recentPath = routeProgress.slice(-2);
            const activePolyline = new google.maps.Polyline({
                path: recentPath,
                geodesic: true,
                strokeColor: '#ffffff',
                strokeOpacity: 0.9,
                strokeWeight: 4,
                map
            });
            activePolyline.setMap(map);
        }
    };

    if (navigator.geolocation) {
        updateStatus('Aguardando sua localização para começar...');
        watchId = navigator.geolocation.watchPosition(
            (position) => {
                checkProgress(position);
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
    } else {
        updateStatus('Seu navegador não suporta geolocalização.');
    }
};
