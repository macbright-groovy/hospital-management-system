from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from .models import LabTest, LabResult, LabTestRequest
from .forms import LabTestForm, LabResultForm, LabResultUpdateForm, LabResultFilterForm, LabTestRequestForm, LabTestRequestProcessForm
from users.models import User

@login_required
def lab_test_list(request):
    """View available lab tests."""
    tests = LabTest.objects.filter(is_active=True)
    context = {
        'tests': tests,
        'can_manage_tests': request.user.has_perm('lab.change_labtest'),
    }
    return render(request, 'lab/test_list.html', context)

@login_required
@permission_required('lab.change_labtest')
def lab_test_create(request):
    """Create a new lab test (admin/lab manager only)."""
    if request.method == 'POST':
        form = LabTestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lab test created successfully.')
            return redirect('lab:test_list')
    else:
        form = LabTestForm()
    
    return render(request, 'lab/test_form.html', {'form': form, 'action': 'Create'})

@login_required
@permission_required('lab.change_labtest')
def lab_test_update(request, pk):
    """Update an existing lab test (admin/lab manager only)."""
    test = get_object_or_404(LabTest, pk=pk)
    if request.method == 'POST':
        form = LabTestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, 'Lab test updated successfully.')
            return redirect('lab:test_list')
    else:
        form = LabTestForm(instance=test)
    
    return render(request, 'lab/test_form.html', {'form': form, 'action': 'Update'})

# Lab Test Request Views
@login_required
def lab_test_request_list(request):
    """List lab test requests based on user role."""
    if request.user.role == 'PATIENT':
        requests = LabTestRequest.objects.filter(patient=request.user)
    elif request.user.role == 'LAB_ATTENDANT':
        requests = LabTestRequest.objects.filter(status='PENDING')
    else:
        requests = LabTestRequest.objects.none()
    
    # Pagination
    paginator = Paginator(requests.order_by('-created_at'), 10)
    page = request.GET.get('page')
    requests = paginator.get_page(page)
    
    context = {
        'requests': requests,
        'can_request_tests': request.user.role == 'PATIENT',
        'can_process_requests': request.user.role == 'LAB_ATTENDANT',
    }
    return render(request, 'lab/request_list.html', context)

@login_required
def lab_test_request_create(request):
    """Create a new lab test request (patients only)."""
    if request.user.role != 'PATIENT':
        messages.error(request, 'Only patients can request lab tests.')
        return redirect('lab:request_list')
    
    if request.method == 'POST':
        form = LabTestRequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.patient = request.user
            request_obj.save()
            messages.success(request, 'Lab test request submitted successfully.')
            return redirect('lab:request_list')
    else:
        form = LabTestRequestForm()
    
    return render(request, 'lab/request_form.html', {'form': form, 'action': 'Request'})

@login_required
def lab_test_request_detail(request, pk):
    """View detailed information about a lab test request."""
    request_obj = get_object_or_404(LabTestRequest, pk=pk)
    
    # Check if user has permission to view this request
    if not (request.user == request_obj.patient or request.user.role == 'LAB_ATTENDANT'):
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('lab:request_list')
    
    context = {
        'request_obj': request_obj,
        'can_process': request.user.role == 'LAB_ATTENDANT' and request_obj.status == 'PENDING',
    }
    return render(request, 'lab/request_detail.html', context)

@login_required
def lab_test_request_process(request, pk):
    """Process a lab test request (lab attendants only)."""
    if request.user.role != 'LAB_ATTENDANT':
        messages.error(request, 'Only lab attendants can process requests.')
        return redirect('lab:request_list')
    
    request_obj = get_object_or_404(LabTestRequest, pk=pk)
    
    if request_obj.status != 'PENDING':
        messages.error(request, 'This request has already been processed.')
        return redirect('lab:request_detail', pk=pk)
    
    if request.method == 'POST':
        form = LabTestRequestProcessForm(request.POST, request.FILES, instance=request_obj)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.processed_by = request.user
            request_obj.processed_at = timezone.now()
            request_obj.save()
            
            # If approved, create a completed lab result with the provided results
            if request_obj.status == 'APPROVED':
                test_result = form.cleaned_data.get('test_result')
                result_notes = form.cleaned_data.get('result_notes')
                result_file = form.cleaned_data.get('result_file')
                
                lab_result = LabResult.objects.create(
                    patient=request_obj.patient,
                    test=request_obj.test,
                    test_request=request_obj,
                    lab_attendant=request.user,
                    status='COMPLETED',
                    result=test_result,
                    notes=result_notes,
                    file=result_file,
                    date_ordered=timezone.now(),
                    date_completed=timezone.now(),
                    is_urgent=False,
                    priority=1
                )
                
                # Update the request status to completed
                request_obj.status = 'COMPLETED'
                request_obj.save()
                
                messages.success(request, 'Lab test request approved and results uploaded successfully.')
            else:
                messages.success(request, f'Lab test request {request_obj.status.lower()}.')
            
            return redirect('lab:request_list')
    else:
        form = LabTestRequestProcessForm(instance=request_obj)
    
    return render(request, 'lab/request_process_form.html', {'form': form, 'request_obj': request_obj})

@login_required
def lab_result_list(request):
    """List lab results based on user role."""
    filter_form = LabResultFilterForm(request.GET)
    results = LabResult.objects.all()

    # Apply role-based filtering
    if request.user.role == 'PATIENT':
        results = results.filter(patient=request.user)
    elif request.user.role == 'DOCTOR':
        results = results.filter(doctor=request.user)
    elif request.user.role == 'LAB_ATTENDANT':
        results = results.filter(status__in=['PENDING', 'IN_PROGRESS'])

    # Apply filters
    if filter_form.is_valid():
        if status := filter_form.cleaned_data.get('status'):
            results = results.filter(status=status)
        if date_from := filter_form.cleaned_data.get('date_from'):
            results = results.filter(date_ordered__date__gte=date_from)
        if date_to := filter_form.cleaned_data.get('date_to'):
            results = results.filter(date_ordered__date__lte=date_to)
        if filter_form.cleaned_data.get('is_urgent'):
            results = results.filter(is_urgent=True)
        if test := filter_form.cleaned_data.get('test'):
            results = results.filter(test=test)

    # Pagination
    paginator = Paginator(results.order_by('-date_ordered', 'priority'), 10)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    context = {
        'results': results,
        'filter_form': filter_form,
        'can_order_tests': request.user.has_perm('lab.can_order_lab_test'),
        'can_process_tests': request.user.has_perm('lab.can_process_lab_test'),
    }
    return render(request, 'lab/result_list.html', context)

@login_required
@permission_required('lab.can_order_lab_test')
def lab_result_create(request):
    """Create a new lab test order (doctors only)."""
    if request.method == 'POST':
        form = LabResultForm(request.POST, doctor=request.user)
        if form.is_valid():
            result = form.save(commit=False)
            result.doctor = request.user
            result.save()
            messages.success(request, 'Lab test ordered successfully.')
            return redirect('lab:result_list')
    else:
        form = LabResultForm(doctor=request.user)
    
    return render(request, 'lab/result_form.html', {'form': form, 'action': 'Order'})

@login_required
@permission_required('lab.can_process_lab_test')
def lab_result_update(request, pk):
    """Update lab test results (lab attendants only)."""
    result = get_object_or_404(LabResult, pk=pk)
    if request.method == 'POST':
        form = LabResultUpdateForm(request.POST, request.FILES, instance=result)
        if form.is_valid():
            result = form.save(commit=False)
            if result.status == 'COMPLETED' and not result.date_completed:
                result.date_completed = timezone.now()
            result.save()
            messages.success(request, 'Lab result updated successfully.')
            return redirect('lab:result_list')
    else:
        form = LabResultUpdateForm(instance=result)
    
    return render(request, 'lab/result_update_form.html', {'form': form, 'result': result})

@login_required
def lab_result_detail(request, pk):
    """View detailed information about a lab result."""
    result = get_object_or_404(LabResult, pk=pk)
    
    # Check if user has permission to view this result
    if not (request.user == result.patient or 
            request.user == result.doctor or 
            request.user.role == 'LAB_ATTENDANT' or
            request.user.has_perm('lab.can_view_lab_result')):
        messages.error(request, 'You do not have permission to view this result.')
        return redirect('lab:result_list')
    
    context = {
        'result': result,
        'can_update': request.user.has_perm('lab.can_process_lab_test'),
    }
    return render(request, 'lab/result_detail.html', context)

@login_required
def dashboard(request):
    return render(request, 'lab/dashboard.html')

@login_required
def lab_attendant_dashboard(request):
    pending_requests = LabTestRequest.objects.filter(status='PENDING')
    pending_results = LabResult.objects.filter(status='PENDING')
    context = {
        'pending_requests': pending_requests,
        'pending_results': pending_results,
    }
    return render(request, 'lab/lab_attendant_dashboard.html', context)

@login_required
def upload_lab_result(request, pk):
    lab_result = get_object_or_404(LabResult, pk=pk)
    if request.method == 'POST':
        form = LabResultForm(request.POST, request.FILES, instance=lab_result)
        if form.is_valid():
            result = form.save(commit=False)
            result.lab_attendant = request.user
            result.status = 'COMPLETED'
            result.date_completed = timezone.now()
            result.save()
            messages.success(request, 'Lab result uploaded successfully.')
            return redirect('lab:lab_attendant_dashboard')
    else:
        form = LabResultForm(instance=lab_result)
    return render(request, 'lab/upload_lab_result.html', {'form': form, 'lab_result': lab_result})

@login_required
def patient_lab_results(request):
    lab_results = LabResult.objects.filter(patient=request.user, status='COMPLETED')
    return render(request, 'lab/patient_lab_results.html', {'lab_results': lab_results})
