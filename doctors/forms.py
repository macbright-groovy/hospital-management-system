from django import forms
from .models import Doctor, DoctorSpecialty, DoctorSchedule, TimeOff
from users.models import User
from medical_records.models import MedicalRecord
from prescriptions.models import Prescription
from django.utils import timezone

class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'is_available']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TimeOffForm(forms.ModelForm):
    class Meta:
        model = TimeOff
        fields = ['start_datetime', 'end_datetime', 'reason']
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Vacation, Conference'}),
        }

class DoctorSpecialtyForm(forms.ModelForm):
    class Meta:
        model = DoctorSpecialty
        fields = ['specialty']
        widgets = {
            'specialty': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DoctorProfileForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Doctor
        fields = ['specialization', 'license_number', 'years_of_experience']
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        doctor = super().save(commit=False)
        if commit:
            doctor.user.first_name = self.cleaned_data['first_name']
            doctor.user.last_name = self.cleaned_data['last_name']
            doctor.user.email = self.cleaned_data['email']
            doctor.user.save()
            doctor.save()
        return doctor

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['patient', 'record_type', 'description', 'date', 'file']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'record_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter detailed description of the medical record'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.role == 'DOCTOR':
            self.fields['patient'].queryset = User.objects.filter(role='PATIENT')
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient', 'medication', 'dosage', 'frequency', 'duration', 'instructions']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'medication': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.role == 'DOCTOR':
            self.fields['patient'].queryset = User.objects.filter(role='PATIENT')
        # Removed: if not self.instance.pk: self.fields['date'].initial = timezone.now().date() 