from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_item, name='add_item'),
    path('organize/', views.organize, name='organize'),
    path('roulette/', views.roulette, name='roulette'),
    path('api/item/<int:item_id>/update/', views.update_item, name='update_item'),
    path('api/categories/', views.get_categories, name='get_categories'),
]

