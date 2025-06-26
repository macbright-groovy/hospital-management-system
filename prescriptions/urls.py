from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    # Medication URLs
    path('medications/', views.medication_list, name='medication_list'),
    path('medications/create/', views.medication_create, name='medication_create'),
    path('medications/<int:pk>/update/', views.medication_update, name='medication_update'),
    
    # Prescription URLs
    path('', views.prescription_list, name='prescription_list'),
    path('create/', views.prescription_create, name='prescription_create'),
    path('<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('<int:pk>/update/', views.prescription_update, name='prescription_update'),
    
    # Refill URLs
    path('<int:pk>/refill/', views.prescription_refill_request, name='refill_request'),
    path('refills/<int:pk>/update/', views.prescription_refill_update, name='refill_update'),
] 