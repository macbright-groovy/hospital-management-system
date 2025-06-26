from django.contrib import admin
from .models import Doctor, DoctorSpecialty, DoctorSchedule, TimeOff

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'license_number', 'years_of_experience')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')
    list_filter = ('specialization',)

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('doctor', 'day_of_week', 'is_available')
    search_fields = ('doctor__user__username',)
    list_editable = ('start_time', 'end_time', 'is_available')
    ordering = ('doctor', 'day_of_week')

@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_datetime', 'end_datetime', 'reason')
    list_filter = ('doctor',)
    search_fields = ('doctor__user__username', 'reason')

admin.site.register(DoctorSpecialty)
