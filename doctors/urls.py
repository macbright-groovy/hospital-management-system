from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='dashboard'),
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/medical-records/create/', views.medical_record_create, name='medical_record_create_for_patient'),
    path('medical-records/create/', views.medical_record_create, name='medical_record_create'),
    path('medical-records/', views.medical_record_list, name='medical_record_list'),
    path('medical-records/<int:record_id>/update/', views.medical_record_update, name='medical_record_update'),
    path('prescriptions/create/', views.prescription_create, name='prescription_create'),
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/<int:prescription_id>/update/', views.prescription_update, name='prescription_update'),
    path('lab-results/', views.lab_results, name='lab_results'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/update-status/', views.appointment_update_status, name='appointment_update_status'),
    path('appointments/<int:pk>/approve/', views.appointment_approve, name='appointment_approve'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    path('schedule/', views.manage_schedule, name='manage_schedule'),
    path('api/<int:doctor_id>/available-slots/', views.available_slots, name='available_slots'),
    path('specialties/', views.specialty_list, name='specialty_list'),
    path('specialties/create/', views.specialty_create, name='specialty_create'),
    path('specialties/<int:pk>/delete/', views.specialty_delete, name='specialty_delete'),
    path('profile/update/', views.profile_update, name='profile_update'),
] 