from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('history/', views.medical_history_list, name='medical_history_list'),
    path('history/<int:pk>/', views.medical_history_detail, name='medical_history_detail'),
    path('history/add/', views.medical_history_create, name='medical_history_create'),
    path('doctors/', views.doctor_list, name='doctor_list'),
] 