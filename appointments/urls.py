from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('book/', views.appointment_book, name='appointment_book'),
    path('<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    path('doctor/schedule/', views.doctor_schedule, name='doctor_schedule'),
] 