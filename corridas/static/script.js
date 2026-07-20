document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start-run-btn');

    if (!startButton) {
        return;
    }

    startButton.addEventListener('click', () => {
        if (window.CITYRUNNER_MAP_INIT) {
            window.CITYRUNNER_MAP_INIT(window.CITYRUNNER_ROUTE);
            return;
        }

        const mapContainer = document.getElementById('map');
        const routeData = window.CITYRUNNER_ROUTE;

        if (!mapContainer || !routeData) {
            return;
        }

        mapContainer.innerHTML = '<div class="map-loading"><p>Iniciando corrida e preparando o trajeto...</p></div>';

        if (typeof google !== 'undefined' && google.maps) {
            const map = new google.maps.Map(mapContainer, {
                center: {
                    lat: routeData.origin.lat || 0,
                    lng: routeData.origin.lng || 0
                },
                zoom: 14,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: false
            });

            const markerOrigin = new google.maps.Marker({ position: routeData.origin, map, title: 'Origem' });
            const markerDestination = new google.maps.Marker({ position: routeData.destination, map, title: 'Destino' });

            const bounds = new google.maps.LatLngBounds();
            bounds.extend(routeData.origin);
            bounds.extend(routeData.destination);
            map.fitBounds(bounds);

            new google.maps.Polyline({
                path: [routeData.origin, routeData.destination],
                geodesic: true,
                strokeColor: '#62f2c2',
                strokeOpacity: 0.9,
                strokeWeight: 5,
                map
            });

            const infoWindow = new google.maps.InfoWindow({ content: `<strong>${routeData.title}</strong>` });
            markerOrigin.addListener('click', () => infoWindow.open({ anchor: markerOrigin, map }));
            markerDestination.addListener('click', () => infoWindow.open({ anchor: markerDestination, map }));
            return;
        }

        mapContainer.innerHTML = '<div class="map-loading"><p>Adicione a chave da API do Google Maps para exibir o trajeto real.</p></div>';
    });
});
