from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid
import random
import string

class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        DOCTOR = 'DOCTOR', 'Doctor'
        LAB_ATTENDANT = 'LAB_ATTENDANT', 'Lab Attendant'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True, help_text="Patient's date of birth")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Patient's contact number")
    address = models.TextField(blank=True, help_text="Patient's address")
    emergency_contact = models.CharField(max_length=100, blank=True, help_text="Emergency contact name")
    emergency_phone = models.CharField(max_length=20, blank=True, help_text="Emergency contact number")
    blood_type = models.CharField(max_length=5, blank=True, help_text="Patient's blood type")
    allergies = models.TextField(blank=True, help_text="Known allergies")
    medical_conditions = models.TextField(blank=True, help_text="Existing medical conditions")
    current_medications = models.TextField(blank=True, help_text="Current medications")
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    insurance_provider = models.CharField(max_length=100, blank=True, null=True)
    insurance_number = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Patient Profile for {self.user.username}"

    class Meta:
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patient Profiles"


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=100, blank=True, help_text="Doctor's specialty")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Doctor's contact number")
    address = models.TextField(blank=True, help_text="Doctor's office address")
    license_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    specialization = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField(default=0)
    education = models.TextField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    hospital_affiliation = models.CharField(max_length=200, blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Doctor Profile for {self.user.username}"

    class Meta:
        verbose_name = "Doctor Profile"
        verbose_name_plural = "Doctor Profiles"


class LabAttendantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lab_attendant_profile')
    lab_name = models.CharField(max_length=100, blank=True, help_text="Name of the lab")
    phone_number = models.CharField(max_length=20, blank=True, help_text="Lab's contact number")
    address = models.TextField(blank=True, help_text="Lab's address")

    def __str__(self):
        return f"Lab Attendant Profile for {self.user.username}"


def generate_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class DoctorRegistrationCode(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=8, unique=True, default=generate_code)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {'USED' if self.is_used else 'UNUSED'}"

class LabAttendantRegistrationCode(models.Model):
    email = models.EmailField(unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Registration code for lab attendants")
    is_used = models.BooleanField(default=False, help_text="Whether this code has been used for registration")
    notes = models.TextField(blank=True, help_text="Optional notes about this code")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_registration_codes', limit_choices_to={'role': 'ADMIN'})

    def __str__(self):
        return f"{self.email} - {'USED' if self.is_used else 'UNUSED'}"

    def use_code(self):
        self.is_used = True
        self.save()

    class Meta:
        verbose_name = "Lab Attendant Registration Code"
        verbose_name_plural = "Lab Attendant Registration Codes"
