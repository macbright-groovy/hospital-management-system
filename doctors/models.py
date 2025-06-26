from django.db import models
from django.utils import timezone
from users.models import User
import datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} ({self.get_specialization_display()})"

class DoctorSchedule(models.Model):
    """
    Represents a doctor's recurring weekly work schedule.
    e.g., Dr. Smith works Mondays from 9:00 to 17:00.
    """
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, _('Monday')
        TUESDAY = 1, _('Tuesday')
        WEDNESDAY = 2, _('Wednesday')
        THURSDAY = 3, _('Thursday')
        FRIDAY = 4, _('Friday')
        SATURDAY = 5, _('Saturday')
        SUNDAY = 6, _('Sunday')

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day_of_week')
        ordering = ['doctor', 'day_of_week', 'start_time']

    def __str__(self):
        availability = "Available" if self.is_available else "Unavailable"
        return f"{self.doctor.user.get_full_name()}: {self.get_day_of_week_display()} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}) - {availability}"

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_('Start time must be before end time.'))

class TimeOff(models.Model):
    """
    Represents a specific block of time a doctor is unavailable.
    e.g., Dr. Smith is on vacation from 2024-07-20 to 2024-07-28.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='time_offs')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    reason = models.CharField(max_length=255, blank=True, null=True, help_text="e.g., Vacation, Conference")

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return f"Time Off for {self.doctor.user.get_full_name()}: {self.start_datetime.strftime('%Y-%m-%d %H:%M')} to {self.end_datetime.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        if self.start_datetime and self.end_datetime and self.start_datetime >= self.end_datetime:
            raise ValidationError(_('Start datetime must be before end datetime.'))

class DoctorSpecialty(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    specialty = models.CharField(max_length=100, default='General Medicine')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Doctor Specialties"

    def __str__(self):
        return f"{self.doctor} - {self.specialty}"

class DoctorPatient(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'DOCTOR'}, related_name='doctor_patients')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'PATIENT'}, related_name='patient_doctors')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'patient')
