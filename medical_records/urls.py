from django.urls import path
from . import views

app_name = 'medical_records'

urlpatterns = [
    path('', views.record_list, name='record_list'),
    path('create/', views.record_create, name='record_create'),
    path('<int:pk>/', views.record_detail, name='record_detail'),
    path('<int:pk>/update/', views.record_update, name='record_update'),
] 