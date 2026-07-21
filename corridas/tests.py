from django.test import TestCase
from django.urls import reverse

from .models import Corrida


class CorridaViewsTest(TestCase):
    def setUp(self):
        self.corrida = Corrida.objects.create(
            nome="Corrida Teste",
            local_inicio="Centro",
            local_fim="Parque",
            distancia=5.5,
            descricao="Uma corrida de teste",
            origem_latitude=-23.5505,
            origem_longitude=-46.6333,
            destino_latitude=-23.5605,
            destino_longitude=-46.6400,
        )

    def test_lista_de_corridas_exibe_html(self):
        response = self.client.get(reverse("corrida_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Corridas em destaque")

    def test_detalhe_da_corrida_exibe_html(self):
        response = self.client.get(reverse("corrida_detail", args=[self.corrida.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.corrida.nome)

    def test_api_de_corridas_retorna_json(self):
        response = self.client.get(reverse("corrida_api_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["nome"], self.corrida.nome)

    def test_detalhe_da_corrida_referencia_asset_do_mapa(self):
        response = self.client.get(reverse("corrida_detail", args=[self.corrida.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/corridas/js/map.js")

    def test_template_nao_usa_chave_placeholder(self):
        response = self.client.get(reverse("corrida_detail", args=[self.corrida.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "SUA_CHAVE_AQUI")
        self.assertNotContains(response, "OPENROUTESERVICE_API_KEY")

    def test_template_carrega_leaflet_e_inicializacao(self):
        response = self.client.get(reverse("corrida_detail", args=[self.corrida.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "leaflet")
        self.assertContains(response, "CITYRUNNER_MAP_INIT")

    def test_rota_raiz_redireciona_para_corridas(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/corridas/')
