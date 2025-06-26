from django import forms
from django.utils import timezone
from .models import LabTest, LabResult, LabTestRequest
from users.models import User

class LabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = ['name', 'description', 'price', 'turnaround_time', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'turnaround_time': forms.NumberInput(attrs={'min': '1'}),
        }

class LabTestRequestForm(forms.ModelForm):
    test_name = forms.CharField(
        max_length=100,
        label='Test Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter the name of the test you need...',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = LabTestRequest
        fields = ['requested_date', 'requested_time', 'reason']
        widgets = {
            'requested_date': forms.DateInput(attrs={'type': 'date'}),
            'requested_time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please provide the reason for this test request...'}),
        }

    def clean_requested_date(self):
        requested_date = self.cleaned_data.get('requested_date')
        if requested_date and requested_date < timezone.now().date():
            raise forms.ValidationError('Requested date cannot be in the past.')
        return requested_date

    def clean(self):
        cleaned_data = super().clean()
        requested_date = cleaned_data.get('requested_date')
        requested_time = cleaned_data.get('requested_time')
        
        if requested_date and requested_time:
            requested_datetime = timezone.make_aware(
                timezone.datetime.combine(requested_date, requested_time)
            )
            if requested_datetime < timezone.now():
                raise forms.ValidationError('Requested date and time cannot be in the past.')
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Create or get the LabTest object based on the test name
        test_name = self.cleaned_data.get('test_name')
        test, created = LabTest.objects.get_or_create(
            name=test_name,
            defaults={
                'description': f'Lab test: {test_name}',
                'price': 50.00,  # Default price
                'turnaround_time': 24,  # Default 24 hours
                'is_active': True
            }
        )
        instance.test = test
        if commit:
            instance.save()
        return instance

class LabTestRequestProcessForm(forms.ModelForm):
    # Fields for test results when approving
    test_result = forms.CharField(
        required=False,
        label='Test Result',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Enter the test results here...',
            'class': 'form-control'
        })
    )
    
    result_notes = forms.CharField(
        required=False,
        label='Result Notes',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Additional notes about the results...',
            'class': 'form-control'
        })
    )
    
    result_file = forms.FileField(
        required=False,
        label='Result File',
        help_text='Upload a file (PDF, image, etc.) with the test results'
    )
    
    class Meta:
        model = LabTestRequest
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add any notes or instructions for the patient...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        test_result = cleaned_data.get('test_result')
        
        if status == 'REJECTED' and not cleaned_data.get('notes'):
            raise forms.ValidationError('Notes are required when rejecting a request.')
        
        if status == 'APPROVED' and not test_result:
            raise forms.ValidationError('Test result is required when approving a request.')
        
        return cleaned_data

class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = ['result', 'notes', 'file']
        widgets = {
            'result': forms.Textarea(attrs={'rows': 5}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class LabResultUpdateForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = ['status', 'result', 'notes', 'file']
        widgets = {
            'result': forms.Textarea(attrs={'rows': 5}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        result = cleaned_data.get('result')

        if status == 'COMPLETED' and not result:
            raise forms.ValidationError('Result is required when marking test as completed.')

        return cleaned_data

class LabResultFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Statuses')] + LabResult.STATUS_CHOICES
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    is_urgent = forms.BooleanField(required=False)
    test = forms.ModelChoiceField(queryset=LabTest.objects.filter(is_active=True), required=False) 