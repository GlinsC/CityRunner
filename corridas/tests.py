import json
from datetime import datetime, timedelta, timezone

import jwt
from django.test import TestCase
from django.urls import reverse

from .models import Corrida, rankingPaceCorrida, usuario
from .views import JWT_SECRET, JWT_TTL_HOURS


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
        self.user = usuario.objects.create(nome='Teste', email='teste@example.com', senha='1234')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer ' + jwt.encode({
            'user_id': self.user.id,
            'email': self.user.email,
            'exp': int((datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS)).timestamp()),
        }, JWT_SECRET, algorithm='HS256')

    def test_lista_de_corridas_exibe_html(self):
        response = self.client.get(reverse("corrida_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Corridas em destaque")

    def test_lista_de_corridas_redireciona_para_login_sem_sessao(self):
        unauthenticated_client = self.client_class()
        response = unauthenticated_client.get(reverse("corrida_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_detalhe_da_corrida_exibe_html(self):
        response = self.client.get(reverse("corrida_detail", args=[self.corrida.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.corrida.nome)

    def test_api_de_corridas_retorna_json(self):
        response = self.client.get(reverse("corrida_api_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["nome"], self.corrida.nome)

    def test_criar_corrida_exige_autenticacao(self):
        unauthenticated_client = self.client_class()
        response = unauthenticated_client.post(
            reverse("corrida_post"),
            data=json.dumps({
                "nome": "Nova corrida",
                "local_inicio": "Centro",
                "local_fim": "Parque",
                "distancia": 8.0,
                "descricao": "Corrida protegida",
                "origem_latitude": 0,
                "origem_longitude": 0,
                "destino_latitude": 1,
                "destino_longitude": 1,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

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

    def test_login_page_exibe_formulario(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entrar')

    def test_detalhe_da_corrida_exibe_ranking_de_pace(self):
        usuario_obj = usuario.objects.create(nome='Ana', email='ana@example.com', senha='1234')
        rankingPaceCorrida.objects.create(corrida=self.corrida, usuario=usuario_obj, pace=4.8)

        response = self.client.get(reverse('corrida_detail', args=[self.corrida.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ranking de pace')
        self.assertContains(response, 'Ana')

    def test_ranking_pace_salva_e_ordena_pelo_melhor_pace(self):
        usuario1 = usuario.objects.create(nome='Ana', email='ana@example.com', senha='1234')
        usuario2 = usuario.objects.create(nome='Bruno', email='bruno@example.com', senha='1234')
        expires_at = datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS)
        token = jwt.encode({
            'user_id': usuario1.id,
            'email': usuario1.email,
            'exp': int(expires_at.timestamp()),
        }, JWT_SECRET, algorithm='HS256')
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'

        response = self.client.post(
            reverse('ranking_pace_post'),
            data=json.dumps({
                'corrida_id': self.corrida.id,
                'usuario_id': usuario1.id,
                'pace': 5.2,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(rankingPaceCorrida.objects.filter(corrida=self.corrida, usuario=usuario1).exists())

        ranking_pace_post = self.client.post(
            reverse('ranking_pace_post'),
            data=json.dumps({
                'corrida_id': self.corrida.id,
                'usuario_id': usuario2.id,
                'pace': 4.8,
            }),
            content_type='application/json',
        )

        self.assertEqual(ranking_pace_post.status_code, 201)

        response = self.client.get(reverse('ranking_pace'))
        self.assertEqual(response.status_code, 200)
        ranking = response.json()
        self.assertEqual(ranking[0]['usuario_id'], usuario2.id)
        self.assertEqual(ranking[0]['pace'], 4.8)
        self.assertEqual(ranking[1]['usuario_id'], usuario1.id)
        self.assertEqual(ranking[1]['pace'], 5.2)
