from django import forms
from .models import PatientMedicalHistory

class PatientMedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = PatientMedicalHistory
        fields = ['diagnosis', 'treatment', 'diagnosis_date', 'age', 'height', 'blood_group', 'allergies', 'recurrent_illnesses']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'treatment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'diagnosis_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Height in cm', 'step': '0.01'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A+, O-'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'List any allergies'}),
            'recurrent_illnesses': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'List any recurrent illnesses'}),
        } 