from django.urls import path

from . import views

urlpatterns = [
    path('posts/', views.posts, name='posts'),
    path('billets/creer/', views.ticket_create, name='ticket_create'),
    path('billets/<int:ticket_id>/modifier/', views.ticket_update, name='ticket_update'),
    path('billets/<int:ticket_id>/supprimer/', views.ticket_delete, name='ticket_delete'),
    path('billets/<int:ticket_id>/critique/', views.review_create, name='review_create'),
    path('critiques/creer/', views.review_create_full, name='review_create_full'),
    path('critiques/<int:review_id>/modifier/', views.review_update, name='review_update'),
    path('critiques/<int:review_id>/supprimer/', views.review_delete, name='review_delete'),
]
