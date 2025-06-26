from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.crypto import get_random_string
from .models import User, PatientProfile, DoctorProfile, LabAttendantProfile, DoctorRegistrationCode, LabAttendantRegistrationCode

# Register the custom User model using the default UserAdmin (or a custom one if needed)
admin.site.register(User, BaseUserAdmin)

# Register the user profile models
admin.site.register(PatientProfile)
admin.site.register(DoctorProfile)
admin.site.register(LabAttendantProfile)

@admin.register(DoctorRegistrationCode)
class DoctorRegistrationCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'is_used', 'created_at', 'used_at')
    search_fields = ('email', 'code')
    list_filter = ('is_used', 'created_at')
    readonly_fields = ('is_used', 'used_at')
    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj:
            ro.append('code')
        return ro

@admin.register(LabAttendantRegistrationCode)
class LabAttendantRegistrationCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'is_used', 'created_by')
    search_fields = ('email', 'code', 'created_by__username')
    list_filter = ('is_used',)
    readonly_fields = ('is_used', 'code', 'created_by')

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj:
            ro.append('code')
        return ro

    def save_model(self, request, obj, form, change):
        if not change:
            # Generate a unique code
            while True:
                code = get_random_string(8).upper()
                if not LabAttendantRegistrationCode.objects.filter(code=code).exists():
                    obj.code = code
                    break
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
