from django.urls import path

from . import views


urlpatterns = [
    #Rota para Corrida
    path('', views.corrida_list, name='corrida_list'), 
    path('post/', views.corrida_post, name='corrida_post'),
    path('<int:corrida_id>/', views.corrida_detail, name='corrida_detail'),


    #Rota para ComentarioCorrida
    path('comentarios/<int:corrida_id>/', views.comentario_corrida_list, name='comentario_corrida_list'),
    path('comentarios/<int:corrida_id>/post/', views.comentario_corrida_post, name='comentario_corrida_post'),
]