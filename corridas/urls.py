from django.urls import path

from . import views


urlpatterns = [
    # Rotas HTML da aplicação
    path('', views.corrida_list, name='corrida_list'),
    path('<int:corrida_id>/', views.corrida_detail, name='corrida_detail'),

    # Rotas da API JSON
    path('api/', views.corrida_api_list, name='corrida_api_list'),
    path('post/', views.corrida_post, name='corrida_post'),
    path('api/<int:corrida_id>/', views.corrida_detail_api, name='corrida_detail_api'),
    path('<int:corrida_id>/delete/', views.corrida_delete, name='corrida_delete'),

    # Rotas para comentários
    path('comentarios/<int:corrida_id>/', views.comentario_corrida_list, name='comentario_corrida_list'),
    path('comentarios/<int:corrida_id>/post/', views.comentario_corrida_post, name='comentario_corrida_post'),
]