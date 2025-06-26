from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import MedicalRecord
from .forms import MedicalRecordForm, MedicalRecordFilterForm
from users.models import User
from django.utils import timezone

def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

def is_patient(user):
    return user.is_authenticated and user.role == 'PATIENT'

@login_required
def record_list(request):
    user = request.user
    filter_form = MedicalRecordFilterForm(request.GET)
    records = MedicalRecord.objects.none()

    if user.role == 'PATIENT':
        records = MedicalRecord.objects.filter(patient=user)
    elif user.role == 'DOCTOR':
        records = MedicalRecord.objects.filter(doctor=user)
    else:
        records = MedicalRecord.objects.all()

    if filter_form.is_valid():
        record_type = filter_form.cleaned_data.get('record_type')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        if record_type:
            records = records.filter(record_type=record_type)
        if date_from:
            records = records.filter(date__gte=date_from)
        if date_to:
            records = records.filter(date__lte=date_to)

    records = records.order_by('-date')
    context = {
        'records': records,
        'filter_form': filter_form,
        'user_role': user.role,
    }
    return render(request, 'medical_records/record_list.html', context)

@login_required
def record_detail(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)
    user = request.user
    if user.role == 'PATIENT' and record.patient != user:
        messages.error(request, "You don't have permission to view this record.")
        return redirect('medical_records:record_list')
    if user.role == 'DOCTOR' and record.doctor != user:
        messages.error(request, "You don't have permission to view this record.")
        return redirect('medical_records:record_list')
    return render(request, 'medical_records/record_detail.html', {'record': record, 'user_role': user.role})

@login_required
@user_passes_test(is_doctor)
def record_create(request):
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medical record created successfully.')
            return redirect('medical_records:record_list')
    else:
        form = MedicalRecordForm(user=request.user)
    return render(request, 'medical_records/record_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(is_doctor)
def record_update(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES, instance=record, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medical record updated successfully.')
            return redirect('medical_records:record_detail', pk=record.pk)
    else:
        form = MedicalRecordForm(instance=record, user=request.user)
    return render(request, 'medical_records/record_form.html', {'form': form, 'action': 'Update', 'record': record})
