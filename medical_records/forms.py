from django import forms
from .models import MedicalRecord
from users.models import User
from django.utils import timezone

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['patient', 'doctor', 'record_type', 'description', 'date', 'file']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'record_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Only allow doctors to select themselves, patients to select themselves
        if user:
            if user.role == 'DOCTOR':
                self.fields['doctor'].queryset = User.objects.filter(pk=user.pk)
            elif user.role == 'PATIENT':
                self.fields['patient'].queryset = User.objects.filter(pk=user.pk)
                self.fields['doctor'].queryset = User.objects.filter(role='DOCTOR')
            else:
                self.fields['doctor'].queryset = User.objects.filter(role='DOCTOR')
                self.fields['patient'].queryset = User.objects.filter(role='PATIENT')
        else:
            self.fields['doctor'].queryset = User.objects.filter(role='DOCTOR')
            self.fields['patient'].queryset = User.objects.filter(role='PATIENT')

class MedicalRecordFilterForm(forms.Form):
    record_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + MedicalRecord.RECORD_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('End date must be after start date.')
        return cleaned_data 