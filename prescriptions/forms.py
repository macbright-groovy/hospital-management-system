from django import forms
from django.utils import timezone
from .models import Medication, Prescription, PrescriptionRefill
from users.models import User

class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ['name', 'generic_name', 'description', 'dosage_forms', 'strength', 'is_active', 'requires_prescription']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'dosage_forms': forms.TextInput(attrs={'placeholder': 'e.g., tablet, capsule, liquid'}),
            'strength': forms.TextInput(attrs={'placeholder': 'e.g., 500mg, 10mg/ml'}),
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient', 'medication', 'dosage', 'frequency', 'duration', 'instructions', 
                 'start_date', 'refills_remaining', 'notes', 'is_urgent', 'priority']
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'priority': forms.NumberInput(attrs={'min': '1', 'max': '5'}),
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        if doctor:
            self.fields['patient'].queryset = User.objects.filter(
                role='PATIENT',
                doctor_patients__doctor=doctor
            ).distinct()

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < timezone.now().date():
            raise forms.ValidationError('Start date cannot be in the past.')
        return start_date

class PrescriptionUpdateForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PrescriptionRefillForm(forms.ModelForm):
    class Meta:
        model = PrescriptionRefill
        fields = ['notes', 'is_urgent']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        prescription = kwargs.pop('prescription', None)
        super().__init__(*args, **kwargs)
        if prescription and prescription.refills_remaining <= 0:
            self.fields['notes'].widget.attrs['placeholder'] = 'Please explain why you need a refill despite having no refills remaining.'

class PrescriptionRefillUpdateForm(forms.ModelForm):
    class Meta:
        model = PrescriptionRefill
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        notes = cleaned_data.get('notes')

        if status == 'REJECTED' and not notes:
            raise forms.ValidationError('Please provide a reason for rejecting the refill request.')

        return cleaned_data

class PrescriptionFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Statuses')] + Prescription.STATUS_CHOICES
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    is_urgent = forms.BooleanField(required=False)
    medication = forms.ModelChoiceField(queryset=Medication.objects.filter(is_active=True), required=False)
    has_refills = forms.BooleanField(required=False, label='Has Refills Remaining') 