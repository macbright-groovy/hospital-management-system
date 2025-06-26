from django.db import models
from users.models import User

class MedicalRecord(models.Model):
    RECORD_TYPE_CHOICES = [
        ('CONSULTATION', 'Consultation'),
        ('LAB_RESULT', 'Lab Result'),
        ('PRESCRIPTION', 'Prescription'),
        ('OTHER', 'Other'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_records_as_patient', limit_choices_to={'role': 'PATIENT'})
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_records_as_doctor', limit_choices_to={'role': 'DOCTOR'})
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    description = models.TextField(help_text='Description of the record')
    date = models.DateField(help_text='Date of the record')
    file = models.FileField(upload_to='medical_records/', blank=True, null=True, help_text='Optional file upload (e.g., lab result, report)')

    def __str__(self):
        return f"Medical Record for {self.patient.username} ({self.record_type}) on {self.date}"
