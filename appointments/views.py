from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Appointment
from .forms import AppointmentBookingForm, AppointmentUpdateForm, AppointmentFilterForm
from users.models import User

def is_patient(user):
    return user.is_authenticated and user.role == 'PATIENT'

def is_doctor(user):
    return user.is_authenticated and user.role == 'DOCTOR'

@login_required
def appointment_list(request):
    user = request.user
    filter_form = AppointmentFilterForm(request.GET)
    appointments = Appointment.objects.none()

    if user.role == 'PATIENT':
        appointments = Appointment.objects.filter(patient=user)
    elif user.role == 'DOCTOR':
        appointments = Appointment.objects.filter(doctor=user)
    else:
        messages.error(request, "You don't have permission to view appointments.")
        return redirect('home')

    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        status = filter_form.cleaned_data.get('status')

        if date_from:
            appointments = appointments.filter(date__gte=date_from)
        if date_to:
            appointments = appointments.filter(date__lte=date_to)
        if status:
            appointments = appointments.filter(status=status)

    # Order appointments by date and time
    appointments = appointments.order_by('date', 'time')

    context = {
        'appointments': appointments,
        'filter_form': filter_form,
        'user_role': user.role,
    }
    return render(request, 'appointments/appointment_list.html', context)

@login_required
@user_passes_test(is_patient)
def appointment_book(request):
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST, patient=request.user)
        if form.is_valid():
            appointment = form.save()
            print('Appointment saved:', appointment)
            messages.success(request, 'Appointment booked successfully. Waiting for doctor confirmation.')
            return redirect('appointments:appointment_list')
        else:
            print('Form errors:', form.errors, form.non_field_errors())
    else:
        form = AppointmentBookingForm(patient=request.user)

    context = {
        'form': form,
        'action': 'Book',
    }
    return render(request, 'appointments/appointment_form.html', context)

@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    user = request.user

    # Check if user has permission to view this appointment
    if user.role == 'PATIENT' and appointment.patient != user:
        messages.error(request, "You don't have permission to view this appointment.")
        return redirect('appointments:appointment_list')
    elif user.role == 'DOCTOR' and appointment.doctor != user:
        messages.error(request, "You don't have permission to view this appointment.")
        return redirect('appointments:appointment_list')

    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, instance=appointment, user=user)
        if form.is_valid():
            appointment = form.save()
            status_display = dict(Appointment.STATUS_CHOICES)[appointment.status]
            messages.success(request, f'Appointment {status_display.lower()}.')
            return redirect('appointments:appointment_list')
    else:
        form = AppointmentUpdateForm(instance=appointment, user=user)

    context = {
        'appointment': appointment,
        'form': form,
        'user_role': user.role,
    }
    return render(request, 'appointments/appointment_detail.html', context)

@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    user = request.user

    # Check if user has permission to cancel this appointment
    if user.role == 'PATIENT' and appointment.patient != user:
        messages.error(request, "You don't have permission to cancel this appointment.")
        return redirect('appointments:appointment_list')
    elif user.role == 'DOCTOR' and appointment.doctor != user:
        messages.error(request, "You don't have permission to cancel this appointment.")
        return redirect('appointments:appointment_list')

    if appointment.status in ['CANCELLED', 'COMPLETED']:
        messages.error(request, "This appointment cannot be cancelled.")
        return redirect('appointments:appointment_list')

    if request.method == 'POST':
        appointment.status = 'CANCELLED'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
        return redirect('appointments:appointment_list')

    context = {
        'appointment': appointment,
        'user_role': user.role,
    }
    return render(request, 'appointments/appointment_confirm_cancel.html', context)

@login_required
@user_passes_test(is_doctor)
def doctor_schedule(request):
    doctor = request.user
    today = timezone.now().date()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        date__gte=today,
        status__in=['CONFIRMED', 'PENDING']
    ).order_by('date', 'time')

    # Get today's appointments
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        date=today,
        status__in=['CONFIRMED', 'PENDING']
    ).order_by('time')

    context = {
        'upcoming_appointments': upcoming_appointments,
        'today_appointments': today_appointments,
        'today': today,
    }
    return render(request, 'appointments/doctor_schedule.html', context)
