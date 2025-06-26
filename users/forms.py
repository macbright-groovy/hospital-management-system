from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, PatientProfile, DoctorRegistrationCode, LabAttendantRegistrationCode
from django.utils import timezone
from django.utils.crypto import get_random_string
from healthcare.security import SecurityUtils, SecurityValidator

class UserRegistrationForm(UserCreationForm):
    license_number = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Your medical license number (required for doctors)"
    )
    registration_code = forms.CharField(
        required=False,
        max_length=32,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Enter the code provided by the admin (required for doctors and lab attendants)"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude 'Admin' role from the choices
        self.fields['role'].choices = [
            (role, label) for role, label in User.Role.choices if role != User.Role.ADMIN
        ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = SecurityUtils.sanitize_input(username, 30)
            if SecurityUtils.is_suspicious_input(username):
                raise forms.ValidationError("Username contains invalid characters.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = SecurityUtils.sanitize_input(email, 254).lower()
            if SecurityUtils.is_suspicious_input(email):
                raise forms.ValidationError("Email contains invalid characters.")
        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = SecurityUtils.sanitize_input(first_name, 50)
            if SecurityUtils.is_suspicious_input(first_name):
                raise forms.ValidationError("First name contains invalid characters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = SecurityUtils.sanitize_input(last_name, 50)
            if SecurityUtils.is_suspicious_input(last_name):
                raise forms.ValidationError("Last name contains invalid characters.")
        return last_name

    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        if license_number:
            license_number = SecurityUtils.sanitize_input(license_number, 50)
            if SecurityUtils.is_suspicious_input(license_number):
                raise forms.ValidationError("License number contains invalid characters.")
        return license_number

    def clean_registration_code(self):
        registration_code = self.cleaned_data.get('registration_code')
        if registration_code:
            registration_code = SecurityUtils.sanitize_input(registration_code, 32)
            if SecurityUtils.is_suspicious_input(registration_code):
                raise forms.ValidationError("Registration code contains invalid characters.")
        return registration_code

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        license_number = cleaned_data.get('license_number')
        registration_code = cleaned_data.get('registration_code')
        email = cleaned_data.get('email')

        if role == User.Role.DOCTOR:
            if not license_number:
                raise forms.ValidationError("License number is required for doctors.")
            if not registration_code:
                raise forms.ValidationError("Registration code is required for doctors.")
            # Validate doctor code
            try:
                code_obj = DoctorRegistrationCode.objects.get(email=email, code=registration_code, is_used=False)
            except DoctorRegistrationCode.DoesNotExist:
                raise forms.ValidationError("Invalid or already used registration code for this email.")
            self._doctor_code_obj = code_obj
        
        elif role == User.Role.LAB_ATTENDANT:
            if not registration_code:
                raise forms.ValidationError("Registration code is required for lab attendants.")
            # Validate lab attendant code
            try:
                code_obj = LabAttendantRegistrationCode.objects.get(code=registration_code, is_used=False)
                # Check if email matches the code's email
                if code_obj.email != email:
                    raise forms.ValidationError("This code does not match the provided email.")
            except LabAttendantRegistrationCode.DoesNotExist:
                raise forms.ValidationError("Invalid or already used registration code.")
            self._lab_attendant_code_obj = code_obj
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Mark code as used if doctor
        role = self.cleaned_data.get('role')
        if role == User.Role.DOCTOR and hasattr(self, '_doctor_code_obj'):
            code_obj = self._doctor_code_obj
            code_obj.is_used = True
            code_obj.used_at = timezone.now()
            code_obj.save()
        
        # Mark code as used if lab attendant
        elif role == User.Role.LAB_ATTENDANT and hasattr(self, '_lab_attendant_code_obj'):
            code_obj = self._lab_attendant_code_obj
            code_obj.use_code()
        
        if commit:
            user.save()
        return user

class UserProfileUpdateForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Your date of birth"
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = SecurityUtils.sanitize_input(first_name, 50)
            if SecurityUtils.is_suspicious_input(first_name):
                raise forms.ValidationError("First name contains invalid characters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = SecurityUtils.sanitize_input(last_name, 50)
            if SecurityUtils.is_suspicious_input(last_name):
                raise forms.ValidationError("Last name contains invalid characters.")
        return last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = SecurityUtils.sanitize_input(email, 254).lower()
            if SecurityUtils.is_suspicious_input(email):
                raise forms.ValidationError("Email contains invalid characters.")
        return email 