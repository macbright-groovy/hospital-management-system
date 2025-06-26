from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from users.models import User

class Medication(models.Model):
    """Model for managing available medications."""
    name = models.CharField(max_length=255, unique=True)
    generic_name = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    dosage_forms = models.CharField(max_length=100, help_text='Available forms (e.g., tablet, capsule, liquid)')
    strength = models.CharField(max_length=100, help_text='Available strengths (e.g., 500mg, 10mg/ml)')
    is_active = models.BooleanField(default=True)
    requires_prescription = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.generic_name})" if self.generic_name else self.name

    class Meta:
        ordering = ['name']

class Prescription(models.Model):
    """Model for managing prescriptions."""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]

    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='prescriptions_as_patient', limit_choices_to={'role': 'PATIENT'}
    )
    doctor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='prescriptions_as_doctor', limit_choices_to={'role': 'DOCTOR'}
    )
    medication = models.CharField(max_length=255, help_text='Medication name', default='Unknown')
    dosage = models.CharField(max_length=100, help_text='Dosage information (e.g., 1 tablet, 2 teaspoons)')
    frequency = models.CharField(max_length=100, default='Once daily', help_text='Frequency (e.g., twice daily, every 8 hours)')
    duration = models.IntegerField(default=7, help_text='Duration in days')
    instructions = models.TextField(help_text='Instructions for the patient')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    date_prescribed = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True, default=timezone.now, help_text='When the patient should start taking the medication')
    end_date = models.DateField(null=True, blank=True, help_text='When the prescription expires')
    refills_remaining = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(12)],
        help_text='Number of refills remaining (0-12)'
    )
    notes = models.TextField(blank=True, help_text='Additional notes (optional)')
    is_urgent = models.BooleanField(default=False)
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Priority level from 1 (lowest) to 5 (highest)'
    )

    def __str__(self):
        return f"{self.medication} for {self.patient.get_full_name()} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if self.start_date and not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=self.duration)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_prescribed', 'priority']
        permissions = [
            ('can_prescribe_medication', 'Can prescribe medication'),
            ('can_request_refill', 'Can request prescription refill'),
            ('can_approve_refill', 'Can approve prescription refill'),
        ]

class PrescriptionRefill(models.Model):
    """Model for tracking prescription refills."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='refills')
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='refill_requests', limit_choices_to={'role': 'PATIENT'}
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_refills', limit_choices_to={'role': 'DOCTOR'}
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    request_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_urgent = models.BooleanField(default=False)

    def __str__(self):
        return f"Refill request for {self.prescription} ({self.get_status_display()})"

    class Meta:
        ordering = ['-request_date']
        permissions = [
            ('can_request_refill', 'Can request prescription refill'),
            ('can_approve_refill', 'Can approve prescription refill'),
        ]
