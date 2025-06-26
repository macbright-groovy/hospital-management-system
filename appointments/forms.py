from django import forms
from .models import Appointment
from users.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from doctors.models import Doctor, DoctorSchedule, TimeOff

class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'notes']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any specific concerns or notes for the doctor'}),
        }

    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)
        if self.patient:
            self.instance.patient = self.patient
        # Use User model for queryset, only doctors
        self.fields['doctor'].queryset = User.objects.filter(role='DOCTOR')
        # Set minimum date to today
        self.fields['date'].widget.attrs['min'] = timezone.now().date().isoformat()
        # Set maximum date to 3 months from now
        max_date = timezone.now().date() + timedelta(days=90)
        self.fields['date'].widget.attrs['max'] = max_date.isoformat()

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        doctor_user = cleaned_data.get('doctor')

        if not (date and time and doctor_user):
            return cleaned_data

        # --- VALIDATION LOGIC ---

        # 1. Check if appointment is in the past
        appointment_datetime = timezone.make_aware(datetime.combine(date, time))
        if appointment_datetime < timezone.now():
            raise forms.ValidationError("You cannot book appointments in the past.")

        try:
            doctor = doctor_user.doctor
        except Doctor.DoesNotExist:
            raise forms.ValidationError("The selected user does not have a valid doctor profile.")

        # 2. Check for doctor's time off
        if TimeOff.objects.filter(
            doctor=doctor,
            start_datetime__lte=appointment_datetime,
            end_datetime__gte=appointment_datetime
        ).exists():
            raise forms.ValidationError(
                "The doctor has scheduled time off and is not available at the selected date and time."
            )

        # 3. Check against the doctor's weekly schedule for unavailability
        day_of_week = date.weekday()  # Monday is 0, Sunday is 6
        unavailable_slots = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            start_time__lte=time,
            end_time__gte=time
        )

        if unavailable_slots.exists():
            # Find the specific slot for a more informative error message
            slot = unavailable_slots.first()
            raise forms.ValidationError(
                f"The doctor is unavailable from {slot.start_time.strftime('%I:%M %p')} to "
                f"{slot.end_time.strftime('%I:%M %p')} on this day."
            )

        # 4. Check for existing appointments (double-booking)
        if Appointment.objects.filter(
            doctor=doctor_user,
            date=date,
            time=time,
            status__in=['CONFIRMED', 'PENDING']
        ).exists():
            raise forms.ValidationError("The doctor already has an appointment at this time. Please select another slot.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert Doctor instance to User instance for the doctor field
        if isinstance(instance.doctor, Doctor):
            instance.doctor = instance.doctor.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class AppointmentUpdateForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Customize status choices based on user role
        if self.user and self.user.role == 'DOCTOR':
            self.fields['status'].choices = [
                ('CONFIRMED', 'Confirm'),
                ('CANCELLED', 'Cancel'),
                ('COMPLETED', 'Mark as Completed'),
            ]
        elif self.user and self.user.role == 'PATIENT':
            self.fields['status'].choices = [
                ('CANCELLED', 'Cancel Appointment'),
            ]

class AppointmentFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Appointment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("End date must be after start date.")

        return cleaned_data 