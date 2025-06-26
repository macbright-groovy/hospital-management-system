from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Medication, Prescription, PrescriptionRefill
from .forms import (
    MedicationForm, PrescriptionForm, PrescriptionUpdateForm,
    PrescriptionRefillForm, PrescriptionRefillUpdateForm, PrescriptionFilterForm
)
from users.models import User

@login_required
def medication_list(request):
    """View available medications."""
    medications = Medication.objects.filter(is_active=True)
    context = {
        'medications': medications,
        'can_manage_medications': request.user.has_perm('prescriptions.change_medication'),
    }
    return render(request, 'prescriptions/medication_list.html', context)

@login_required
@permission_required('prescriptions.change_medication')
def medication_create(request):
    """Create a new medication (admin/pharmacist only)."""
    if request.method == 'POST':
        form = MedicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medication created successfully.')
            return redirect('prescriptions:medication_list')
    else:
        form = MedicationForm()
    
    return render(request, 'prescriptions/medication_form.html', {'form': form, 'action': 'Create'})

@login_required
@permission_required('prescriptions.change_medication')
def medication_update(request, pk):
    """Update an existing medication (admin/pharmacist only)."""
    medication = get_object_or_404(Medication, pk=pk)
    if request.method == 'POST':
        form = MedicationForm(request.POST, instance=medication)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medication updated successfully.')
            return redirect('prescriptions:medication_list')
    else:
        form = MedicationForm(instance=medication)
    
    return render(request, 'prescriptions/medication_form.html', {'form': form, 'action': 'Update'})

@login_required
def prescription_list(request):
    """List prescriptions based on user role."""
    filter_form = PrescriptionFilterForm(request.GET)
    prescriptions = Prescription.objects.all()

    # Apply role-based filtering
    if request.user.role == 'PATIENT':
        prescriptions = prescriptions.filter(patient=request.user)
    elif request.user.role == 'DOCTOR':
        prescriptions = prescriptions.filter(doctor=request.user)

    # Apply filters
    if filter_form.is_valid():
        if status := filter_form.cleaned_data.get('status'):
            prescriptions = prescriptions.filter(status=status)
        if date_from := filter_form.cleaned_data.get('date_from'):
            prescriptions = prescriptions.filter(date_prescribed__date__gte=date_from)
        if date_to := filter_form.cleaned_data.get('date_to'):
            prescriptions = prescriptions.filter(date_prescribed__date__lte=date_to)
        if filter_form.cleaned_data.get('is_urgent'):
            prescriptions = prescriptions.filter(is_urgent=True)
        if medication := filter_form.cleaned_data.get('medication'):
            prescriptions = prescriptions.filter(medication=medication)
        if filter_form.cleaned_data.get('has_refills'):
            prescriptions = prescriptions.filter(refills_remaining__gt=0)

    # Pagination
    paginator = Paginator(prescriptions.order_by('-date_prescribed', 'priority'), 10)
    page = request.GET.get('page')
    prescriptions = paginator.get_page(page)

    context = {
        'prescriptions': prescriptions,
        'filter_form': filter_form,
        'can_prescribe': request.user.has_perm('prescriptions.can_prescribe_medication'),
        'can_request_refill': request.user.has_perm('prescriptions.can_request_refill'),
    }
    return render(request, 'prescriptions/prescription_list.html', context)

@login_required
@permission_required('prescriptions.can_prescribe_medication')
def prescription_create(request):
    """Create a new prescription (doctors only)."""
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, doctor=request.user)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = request.user
            prescription.save()
            messages.success(request, 'Prescription created successfully.')
            return redirect('prescriptions:prescription_list')
    else:
        form = PrescriptionForm(doctor=request.user)
    
    return render(request, 'prescriptions/prescription_form.html', {'form': form, 'action': 'Create'})

@login_required
def prescription_detail(request, pk):
    """View detailed information about a prescription."""
    prescription = get_object_or_404(Prescription, pk=pk)
    
    # Check if user has permission to view this prescription
    if not (request.user == prescription.patient or 
            request.user == prescription.doctor or
            request.user.has_perm('prescriptions.can_prescribe_medication')):
        messages.error(request, 'You do not have permission to view this prescription.')
        return redirect('prescriptions:prescription_list')
    
    # Get refill requests for this prescription
    refills = prescription.refills.all().order_by('-request_date')
    
    context = {
        'prescription': prescription,
        'refills': refills,
        'can_update': request.user.has_perm('prescriptions.can_prescribe_medication'),
        'can_request_refill': (
            request.user == prescription.patient and
            prescription.status == 'ACTIVE' and
            request.user.has_perm('prescriptions.can_request_refill')
        ),
        'can_approve_refill': request.user.has_perm('prescriptions.can_approve_refill'),
    }
    return render(request, 'prescriptions/prescription_detail.html', context)

@login_required
@permission_required('prescriptions.can_prescribe_medication')
def prescription_update(request, pk):
    """Update prescription status (doctors only)."""
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.method == 'POST':
        form = PrescriptionUpdateForm(request.POST, instance=prescription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prescription updated successfully.')
            return redirect('prescriptions:prescription_detail', pk=prescription.pk)
    else:
        form = PrescriptionUpdateForm(instance=prescription)
    
    return render(request, 'prescriptions/prescription_update_form.html', {'form': form, 'prescription': prescription})

@login_required
@permission_required('prescriptions.can_request_refill')
def prescription_refill_request(request, pk):
    """Request a prescription refill (patients only)."""
    prescription = get_object_or_404(Prescription, pk=pk)
    
    # Check if patient can request refill
    if request.user != prescription.patient:
        messages.error(request, 'You can only request refills for your own prescriptions.')
        return redirect('prescriptions:prescription_list')
    
    if prescription.status != 'ACTIVE':
        messages.error(request, 'Cannot request refill for inactive prescription.')
        return redirect('prescriptions:prescription_detail', pk=prescription.pk)
    
    if request.method == 'POST':
        form = PrescriptionRefillForm(request.POST, prescription=prescription)
        if form.is_valid():
            refill = form.save(commit=False)
            refill.prescription = prescription
            refill.requested_by = request.user
            refill.save()
            messages.success(request, 'Refill request submitted successfully.')
            return redirect('prescriptions:prescription_detail', pk=prescription.pk)
    else:
        form = PrescriptionRefillForm(prescription=prescription)
    
    return render(request, 'prescriptions/refill_request_form.html', {'form': form, 'prescription': prescription})

@login_required
@permission_required('prescriptions.can_approve_refill')
def prescription_refill_update(request, pk):
    """Update refill request status (doctors only)."""
    refill = get_object_or_404(PrescriptionRefill, pk=pk)
    if request.method == 'POST':
        form = PrescriptionRefillUpdateForm(request.POST, instance=refill)
        if form.is_valid():
            refill = form.save(commit=False)
            if refill.status == 'APPROVED':
                refill.approved_by = request.user
                refill.approval_date = timezone.now()
                # Update prescription refills remaining
                prescription = refill.prescription
                if prescription.refills_remaining > 0:
                    prescription.refills_remaining -= 1
                    prescription.save()
            elif refill.status == 'COMPLETED':
                refill.completion_date = timezone.now()
            refill.save()
            messages.success(request, 'Refill request updated successfully.')
            return redirect('prescriptions:prescription_detail', pk=refill.prescription.pk)
    else:
        form = PrescriptionRefillUpdateForm(instance=refill)
    
    return render(request, 'prescriptions/refill_update_form.html', {'form': form, 'refill': refill}) 