from django.urls import path
from . import views

urlpatterns = [
    path('', views.equipment_list_view, name='equipment_list'),
    path('add/', views.equipment_create_view, name='equipment_create'),
    path('<int:pk>/', views.equipment_detail_view, name='equipment_detail'),
    path('<int:pk>/edit/', views.equipment_update_view, name='equipment_update'),
    path('<int:pk>/delete/', views.equipment_delete_view, name='equipment_delete'),
]
