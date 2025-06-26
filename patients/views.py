from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PatientMedicalHistory
from users.models import User, PatientProfile
from .forms import PatientMedicalHistoryForm
from django.contrib import messages
from django.db import transaction
from users.forms import UserProfileUpdateForm
from doctors.models import Doctor, DoctorSpecialty
from medical_records.models import MedicalRecord
from lab.models import LabResult, LabTestRequest

# Create your views here.

@login_required
def medical_history_list(request):
    histories = PatientMedicalHistory.objects.filter(patient=request.user)
    medical_records = MedicalRecord.objects.filter(patient=request.user)
    return render(request, 'patients/medical_history_list.html', {
        'histories': histories,
        'medical_records': medical_records,
        'user': request.user
    })

@login_required
def medical_history_detail(request, pk):
    history = get_object_or_404(PatientMedicalHistory, pk=pk, patient=request.user)
    return render(request, 'patients/medical_history_detail.html', {'history': history})

@login_required
def medical_history_create(request):
    if request.method == 'POST':
        form = PatientMedicalHistoryForm(request.POST)
        if form.is_valid():
            history = form.save(commit=False)
            history.patient = request.user
            history.save()
            return redirect('medical_history_list')
    else:
        form = PatientMedicalHistoryForm()
    return render(request, 'patients/medical_history_form.html', {'form': form})

@login_required
def dashboard(request):
    if request.user.role != User.Role.PATIENT:
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('login')
    
    # Get medical records
    medical_records = MedicalRecord.objects.filter(patient=request.user).order_by('-date')
    
    # Get lab test results
    lab_results = LabResult.objects.filter(patient=request.user, status='COMPLETED').order_by('-date_completed')
    
    # Get recent lab test requests
    lab_requests = LabTestRequest.objects.filter(patient=request.user).order_by('-created_at')[:5]
    
    return render(request, 'patients/dashboard.html', {
        'user': request.user,
        'medical_records': medical_records,
        'lab_results': lab_results,
        'lab_requests': lab_requests,
    })

@login_required
def profile(request):
    if request.user.role != User.Role.PATIENT:
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('login')
    
    # Get or create patient profile
    patient_profile, created = PatientProfile.objects.get_or_create(user=request.user)
        
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update user information
                    user = form.save()
                    
                    # Update patient profile
                    date_of_birth = form.cleaned_data.get('date_of_birth')
                    if date_of_birth:
                        patient_profile.date_of_birth = date_of_birth
                        patient_profile.save()
                    
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('patients:profile')
            except Exception as e:
                messages.error(request, f'An error occurred while updating profile: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileUpdateForm(instance=request.user)
        if patient_profile.date_of_birth:
            form.initial['date_of_birth'] = patient_profile.date_of_birth
    
    return render(request, 'patients/profile.html', {
        'form': form,
        'user': request.user,
        'patient_profile': patient_profile
    })

@login_required
def doctor_list(request):
    if request.user.role != User.Role.PATIENT:
        messages.error(request, 'Access denied. This page is for patients only.')
        return redirect('login')
    doctors = Doctor.objects.all().select_related('user').prefetch_related('doctorspecialty_set')
    return render(request, 'patients/doctor_list.html', {'doctors': doctors})
