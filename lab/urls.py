from django.urls import path
from . import views

app_name = 'lab'

urlpatterns = [
    path('dashboard/', views.lab_attendant_dashboard, name='lab_attendant_dashboard'),
    path('upload/<int:pk>/', views.upload_lab_result, name='upload_lab_result'),
    path('my-results/', views.patient_lab_results, name='patient_lab_results'),
    # Lab Test URLs
    path('tests/', views.lab_test_list, name='test_list'),
    path('tests/create/', views.lab_test_create, name='test_create'),
    path('tests/<int:pk>/update/', views.lab_test_update, name='test_update'),
    
    # Lab Test Request URLs
    path('requests/', views.lab_test_request_list, name='request_list'),
    path('requests/create/', views.lab_test_request_create, name='request_create'),
    path('requests/<int:pk>/', views.lab_test_request_detail, name='request_detail'),
    path('requests/<int:pk>/process/', views.lab_test_request_process, name='request_process'),
    
    # Lab Result URLs
    path('results/', views.lab_result_list, name='result_list'),
    path('results/create/', views.lab_result_create, name='result_create'),
    path('results/<int:pk>/', views.lab_result_detail, name='result_detail'),
    path('results/<int:pk>/update/', views.lab_result_update, name='result_update'),
] 