from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import DoctorSchedule, DoctorSpecialty, Doctor, TimeOff
from appointments.models import Appointment
from .forms import DoctorScheduleForm, DoctorSpecialtyForm, DoctorProfileForm, MedicalRecordForm, PrescriptionForm, TimeOffForm
from users.models import User
from patients.models import Patient
from medical_records.models import MedicalRecord
from lab.models import LabResult
from prescriptions.models import Prescription
from django.http import JsonResponse
from datetime import datetime, timedelta
import sys
from appointments.forms import AppointmentUpdateForm

def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

@login_required
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
        today = timezone.now().date()
        
        # Get today's appointments
        today_appointments = Appointment.objects.filter(
            doctor=request.user,
            date=today,
            status__iexact='approved'
        ).order_by('time')
        
        # Get upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            doctor=request.user,
            date__gt=today,
            status__iexact='approved'
        ).order_by('date', 'time')[:5]
        
        # Get recent patients through appointments
        recent_appointments = Appointment.objects.filter(
            doctor=request.user
        ).order_by('-date', '-time')[:5]
        recent_patients = [appointment.patient for appointment in recent_appointments]
        
        context = {
            'doctor': doctor,
            'today_appointments': today_appointments,
            'upcoming_appointments': upcoming_appointments,
            'recent_patients': recent_patients,
        }
        return render(request, 'doctors/dashboard.html', context)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor profile not found. Please contact the administrator.')
        return redirect('home')

@login_required
@user_passes_test(is_doctor)
def schedule_list(request):
    doctor = Doctor.objects.get(user=request.user)
    schedules = DoctorSchedule.objects.filter(doctor=doctor).order_by('-date', 'start_time')
    return render(request, 'doctors/schedule_list.html', {'schedules': schedules})

@login_required
@user_passes_test(is_doctor)
def schedule_create(request):
    doctor = Doctor.objects.get(user=request.user)
    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor
            schedule.save()
            messages.success(request, 'Schedule created successfully.')
            return redirect('doctors:schedule_list')
    else:
        form = DoctorScheduleForm()
    return render(request, 'doctors/schedule_form.html', {'form': form, 'action': 'Create'})

@login_required
@user_passes_test(is_doctor)
def schedule_update(request, pk):
    doctor = Doctor.objects.get(user=request.user)
    schedule = get_object_or_404(DoctorSchedule, pk=pk, doctor=doctor)
    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule updated successfully.')
            return redirect('doctors:schedule_list')
    else:
        form = DoctorScheduleForm(instance=schedule)
    return render(request, 'doctors/schedule_form.html', {'form': form, 'action': 'Update'})

@login_required
@user_passes_test(is_doctor)
def schedule_delete(request, pk):
    doctor = Doctor.objects.get(user=request.user)
    schedule = get_object_or_404(DoctorSchedule, pk=pk, doctor=doctor)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted successfully.')
        return redirect('doctors:schedule_list')
    return render(request, 'doctors/schedule_confirm_delete.html', {'schedule': schedule})

@login_required
@user_passes_test(is_doctor)
def specialty_list(request):
    doctor = Doctor.objects.get(user=request.user)
    specialties = DoctorSpecialty.objects.filter(doctor=doctor)
    return render(request, 'doctors/specialty_list.html', {'specialties': specialties})

@login_required
@user_passes_test(is_doctor)
def specialty_create(request):
    doctor = Doctor.objects.get(user=request.user)
    if request.method == 'POST':
        form = DoctorSpecialtyForm(request.POST)
        if form.is_valid():
            specialty = form.save(commit=False)
            specialty.doctor = doctor
            specialty.save()
            messages.success(request, 'Specialty added successfully.')
            return redirect('doctors:specialty_list')
    else:
        form = DoctorSpecialtyForm()
    return render(request, 'doctors/specialty_form.html', {'form': form, 'action': 'Add'})

@login_required
@user_passes_test(is_doctor)
def specialty_delete(request, pk):
    doctor = Doctor.objects.get(user=request.user)
    specialty = get_object_or_404(DoctorSpecialty, pk=pk, doctor=doctor)
    if request.method == 'POST':
        specialty.delete()
        messages.success(request, 'Specialty removed successfully.')
        return redirect('doctors:specialty_list')
    return render(request, 'doctors/specialty_confirm_delete.html', {'specialty': specialty})

@login_required
@user_passes_test(is_doctor)
def profile_update(request):
    doctor = Doctor.objects.get(user=request.user)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('doctors:dashboard')
    else:
        form = DoctorProfileForm(instance=doctor)
    return render(request, 'doctors/profile_update.html', {'form': form})

@login_required
@user_passes_test(is_doctor)
def patient_list(request):
    from doctors.models import DoctorPatient
    patient_ids = DoctorPatient.objects.filter(doctor=request.user).values_list('patient_id', flat=True)
    patients = User.objects.filter(role='PATIENT', id__in=patient_ids)
    return render(request, 'doctors/patient_list.html', {'patients': patients})

@login_required
@user_passes_test(is_doctor)
def patient_detail(request, patient_id):
    from doctors.models import DoctorPatient
    patient = get_object_or_404(User, id=patient_id, role='PATIENT')
    if not DoctorPatient.objects.filter(doctor=request.user, patient=patient).exists():
        messages.error(request, 'You do not have access to this patient.')
        return redirect('doctors:patient_list')
    doctor = Doctor.objects.get(user=request.user)
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-date')
    lab_results = LabResult.objects.filter(patient=patient).order_by('-date_ordered')
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-start_date')
    appointments = Appointment.objects.filter(patient=patient, doctor=doctor).order_by('-date', '-time')
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'lab_results': lab_results,
        'prescriptions': prescriptions,
        'appointments': appointments,
    }
    return render(request, 'doctors/patient_detail.html', context)

@login_required
@user_passes_test(is_doctor)
def medical_record_create(request):
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            record = form.save(commit=False)
            record.doctor = request.user
            record.save()
            messages.success(request, 'Medical record created successfully.')
            return redirect('doctors:medical_record_list')
    else:
        form = MedicalRecordForm(user=request.user)
    return render(request, 'doctors/medical_record_form.html', {
        'form': form,
        'patient': None,
        'action': 'Create'
    })

@login_required
@user_passes_test(is_doctor)
def medical_record_update(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id, doctor=request.user)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medical record updated successfully.')
            return redirect('doctors:patient_detail', patient_id=record.patient.id)
    else:
        form = MedicalRecordForm(instance=record)
    return render(request, 'doctors/medical_record_form.html', {
        'form': form,
        'patient': record.patient,
        'action': 'Update'
    })

@login_required
@user_passes_test(is_doctor)
def prescription_create(request):
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, user=request.user)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = request.user
            prescription.save()
            messages.success(request, 'Prescription created successfully.')
            return redirect('doctors:prescription_list')
    else:
        form = PrescriptionForm(user=request.user)
    return render(request, 'doctors/prescription_form.html', {
        'form': form,
        'patient': None,
        'action': 'Create'
    })

@login_required
@user_passes_test(is_doctor)
def appointment_list(request):
    appointments = Appointment.objects.filter(doctor=request.user).order_by('-date', '-time')
    return render(request, 'doctors/appointment_list.html', {'appointments': appointments})

@login_required
@user_passes_test(is_doctor)
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, doctor=request.user)
    
    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, instance=appointment, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Appointment status has been updated to {appointment.get_status_display()}.")
            return redirect('doctors:appointment_list')
    else:
        form = AppointmentUpdateForm(instance=appointment, user=request.user)
        
    context = {
        'appointment': appointment,
        'form': form,
    }
    return render(request, 'doctors/appointment_detail.html', context)

@login_required
@user_passes_test(is_doctor)
def appointment_approve(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, doctor=request.user)
    if appointment.status.lower() == 'pending':
        appointment.status = 'approved'
        appointment.save()
        from doctors.models import DoctorPatient
        DoctorPatient.objects.get_or_create(doctor=request.user, patient=appointment.patient)
        messages.success(request, 'Appointment approved successfully.')
    else:
        messages.error(request, 'Only pending appointments can be approved.')
    return redirect('doctors:appointment_detail', pk=pk)

@login_required
@user_passes_test(is_doctor)
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, doctor=request.user)
    if appointment.status.lower() == 'pending':
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'Only pending appointments can be cancelled.')
    return redirect('doctors:appointment_detail', pk=pk)

@login_required
@user_passes_test(is_doctor)
def appointment_update_status(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, doctor=request.user)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Appointment.STATUS_CHOICES):
            appointment.status = new_status
            appointment.save()
            messages.success(request, f'Appointment status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status provided.')
    return redirect('doctors:appointment_detail', appointment_id=appointment.pk)

@login_required
@user_passes_test(is_doctor)
def medical_record_list(request):
    from doctors.models import DoctorPatient
    patient_ids = DoctorPatient.objects.filter(doctor=request.user).values_list('patient_id', flat=True)
    medical_records = MedicalRecord.objects.filter(doctor=request.user, patient__in=patient_ids).order_by('-date')
    return render(request, 'doctors/medical_record_list.html', {'medical_records': medical_records})

@login_required
@user_passes_test(is_doctor)
def prescription_list(request):
    from doctors.models import DoctorPatient
    patient_ids = DoctorPatient.objects.filter(doctor=request.user).values_list('patient_id', flat=True)
    prescriptions = Prescription.objects.filter(doctor=request.user, patient__in=patient_ids).order_by('-start_date')
    return render(request, 'doctors/prescription_list.html', {'prescriptions': prescriptions})

@login_required
@user_passes_test(is_doctor)
def lab_results(request):
    from doctors.models import DoctorPatient
    patient_ids = DoctorPatient.objects.filter(doctor=request.user).values_list('patient_id', flat=True)
    lab_results = LabResult.objects.filter(patient_id__in=patient_ids).order_by('-date_ordered')
    return render(request, 'doctors/lab_results.html', {'lab_results': lab_results})

@login_required
@user_passes_test(is_doctor)
def prescription_update(request, prescription_id):
    prescription = get_object_or_404(Prescription, id=prescription_id, doctor=request.user)
    if request.method == 'POST':
        form = PrescriptionForm(request.POST, instance=prescription, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prescription updated successfully.')
            return redirect('doctors:prescription_list')
    else:
        form = PrescriptionForm(instance=prescription, user=request.user)
    return render(request, 'doctors/prescription_form.html', {
        'form': form,
        'patient': prescription.patient if hasattr(prescription, 'patient') else None,
        'action': 'Update'
    })

@login_required
def manage_schedule(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    
    # Existing weekly schedule
    schedules = DoctorSchedule.objects.filter(doctor=doctor).order_by('day_of_week')
    
    # Existing time off
    time_offs = TimeOff.objects.filter(doctor=doctor, end_datetime__gte=timezone.now()).order_by('start_datetime')

    # Forms for adding new entries
    schedule_form = DoctorScheduleForm(prefix='schedule')
    timeoff_form = TimeOffForm(prefix='timeoff')

    if request.method == 'POST':
        if 'submit_schedule' in request.POST:
            form = DoctorScheduleForm(request.POST, prefix='schedule')
            if form.is_valid():
                schedule, created = DoctorSchedule.objects.update_or_create(
                    doctor=doctor,
                    day_of_week=form.cleaned_data['day_of_week'],
                    defaults={
                        'start_time': form.cleaned_data['start_time'],
                        'end_time': form.cleaned_data['end_time'],
                        'is_available': form.cleaned_data['is_available'],
                    }
                )
                messages.success(request, 'Your weekly schedule has been updated.')
            return redirect('doctors:manage_schedule')

        elif 'submit_timeoff' in request.POST:
            form = TimeOffForm(request.POST, prefix='timeoff')
            if form.is_valid():
                time_off = form.save(commit=False)
                time_off.doctor = doctor
                time_off.save()
                messages.success(request, 'Your time off has been added.')
            return redirect('doctors:manage_schedule')

    context = {
        'schedules': schedules,
        'time_offs': time_offs,
        'schedule_form': schedule_form,
        'timeoff_form': timeoff_form,
    }
    return render(request, 'doctors/manage_schedule.html', context)

@login_required
def available_slots(request, doctor_id):
    """
    API endpoint: /api/doctors/<doctor_id>/available-slots/?date=YYYY-MM-DD
    Accepts a User ID (doctor_id), finds the Doctor profile, and returns available slots.
    """
    from users.models import User
    date_str = request.GET.get('date')
    print(f"[DEBUG] doctor_id={doctor_id}, date_str={date_str}", file=sys.stderr)
    if not date_str:
        print("[DEBUG] Missing date parameter", file=sys.stderr)
        return JsonResponse({'error': 'Missing date parameter.'}, status=400)
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print("[DEBUG] Invalid date format", file=sys.stderr)
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    user = get_object_or_404(User, pk=doctor_id, role='DOCTOR')
    print(f"[DEBUG] Found user: {user}", file=sys.stderr)
    doctor = get_object_or_404(Doctor, user=user)
    print(f"[DEBUG] Found doctor profile: {doctor}", file=sys.stderr)
    day_of_week = date_obj.weekday()  # Monday=0, Sunday=6
    print(f"[DEBUG] day_of_week={day_of_week}", file=sys.stderr)

    # Get the doctor's schedule for that day
    try:
        schedule = DoctorSchedule.objects.get(doctor=doctor, day_of_week=day_of_week, is_available=True)
        print(f"[DEBUG] Found schedule: {schedule}", file=sys.stderr)
    except DoctorSchedule.DoesNotExist:
        print("[DEBUG] No schedule found for this day", file=sys.stderr)
        return JsonResponse({'slots': []})  # Doctor not available on this day

    # Check for time off
    if TimeOff.objects.filter(doctor=doctor, start_datetime__lte=datetime.combine(date_obj, schedule.end_time), end_datetime__gte=datetime.combine(date_obj, schedule.start_time)).exists():
        print("[DEBUG] Doctor is on time off for this day", file=sys.stderr)
        return JsonResponse({'slots': []})  # Doctor is on time off for this day

    # Get already booked appointments for this doctor on this date
    booked_times = set(
        Appointment.objects.filter(doctor=user, date=date_obj)
        .values_list('time', flat=True)
    )
    print(f"[DEBUG] Booked times: {booked_times}", file=sys.stderr)

    # Generate all possible slots (e.g., every 30 minutes)
    slots = []
    slot_length = timedelta(minutes=30)
    current_time = datetime.combine(date_obj, schedule.start_time)
    end_time = datetime.combine(date_obj, schedule.end_time)
    while current_time + slot_length <= end_time:
        slot_str = current_time.strftime('%H:%M')
        if slot_str not in booked_times:
            slots.append(slot_str)
        current_time += slot_length
    print(f"[DEBUG] Returning slots: {slots}", file=sys.stderr)
    return JsonResponse({'slots': slots})
