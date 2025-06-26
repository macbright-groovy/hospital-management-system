from django.db import models
from users.models import User

# Create your models here.

class PatientMedicalHistory(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_histories', limit_choices_to={'role': 'PATIENT'})
    diagnosis = models.TextField(help_text='Diagnosis details')
    treatment = models.TextField(help_text='Treatment prescribed')
    diagnosis_date = models.DateField(help_text='Date of diagnosis')
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Height in cm')
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True, help_text='List any allergies')
    recurrent_illnesses = models.TextField(blank=True, help_text='List any recurrent illnesses')

    def __str__(self):
        return f"Medical History for {self.patient.username} on {self.diagnosis_date}"

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=100)
    emergency_phone = models.CharField(max_length=20)
    blood_type = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
