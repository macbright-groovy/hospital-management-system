from django.db import models
from users.models import User

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_patient', limit_choices_to={'role': 'PATIENT'})
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_doctor', limit_choices_to={'role': 'DOCTOR'})
    date = models.DateField(help_text='Appointment date')
    time = models.TimeField(help_text='Appointment time')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, help_text='Additional notes (optional)')
    doctor_message = models.TextField(blank=True, null=True, help_text='Optional message from the doctor when declining/cancelling.')

    def __str__(self):
        return f"Appointment: {self.patient.username} with {self.doctor.username} on {self.date} at {self.time}"
