from django.urls import path
from . import views

urlpatterns = [
    # Student endpoints
    path('create/', views.reservation_create_view, name='reservation_create'),
    path('my/', views.my_reservations_view, name='my_reservations'),
    path('<int:pk>/', views.reservation_detail_view, name='reservation_detail'),
    path('<int:pk>/edit/', views.reservation_update_view, name='reservation_update'),
    path('<int:pk>/cancel/', views.reservation_cancel_view, name='reservation_cancel'),

    # Custodian endpoints
    path('queue/', views.custodian_queue_view, name='custodian_queue'),
    path('<int:pk>/approve/', views.custodian_approve_view, name='custodian_approve'),
    path('<int:pk>/reject/', views.custodian_reject_view, name='custodian_reject'),
    path('<int:pk>/issue/', views.custodian_issue_view, name='custodian_issue'),
    path('<int:pk>/return/', views.custodian_return_view, name='custodian_return'),
]
