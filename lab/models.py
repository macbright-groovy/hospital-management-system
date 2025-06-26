from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from users.models import User

class LabTest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    turnaround_time = models.IntegerField(help_text='Expected turnaround time in hours')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class LabTestRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='lab_test_requests', limit_choices_to={'role': 'PATIENT'}
    )
    test = models.ForeignKey(LabTest, on_delete=models.PROTECT)
    requested_date = models.DateField(help_text='Date when the patient wants the test')
    requested_time = models.TimeField(help_text='Time when the patient wants the test')
    reason = models.TextField(help_text='Reason for the test request')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, help_text='Additional notes from lab attendant')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='processed_lab_requests', limit_choices_to={'role': 'LAB_ATTENDANT'}
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.test.name} for {self.patient.username} on {self.requested_date} at {self.requested_time}"

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_request_lab_test', 'Can request lab test'),
            ('can_process_lab_request', 'Can process lab request'),
        ]

class LabResult(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='lab_results_as_patient', limit_choices_to={'role': 'PATIENT'}
    )
    doctor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='ordered_lab_tests', limit_choices_to={'role': 'DOCTOR'}
    )
    lab_attendant = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_results_as_attendant', limit_choices_to={'role': 'LAB_ATTENDANT'}
    )
    test = models.ForeignKey(LabTest, on_delete=models.PROTECT, null=True, blank=True)
    test_request = models.ForeignKey(LabTestRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_results')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    result = models.TextField(blank=True, help_text='Result of the lab test')
    notes = models.TextField(blank=True, help_text='Additional notes or observations')
    date_ordered = models.DateTimeField(default=timezone.now)
    date_completed = models.DateTimeField(null=True, blank=True)
    file = models.FileField(upload_to='lab_results/', blank=True, null=True, help_text="Optional file upload (e.g., PDF or image of the lab report)")
    is_urgent = models.BooleanField(default=False)
    priority = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Priority level from 1 (lowest) to 5 (highest)'
    )

    def __str__(self):
        return f"{self.test.name if self.test else 'Unknown Test'} for {self.patient.username} ({self.status})"

    class Meta:
        ordering = ['-date_ordered', 'priority']
        permissions = [
            ('can_order_lab_test', 'Can order lab test'),
            ('can_process_lab_test', 'Can process lab test'),
            ('can_view_lab_result', 'Can view lab result'),
        ]