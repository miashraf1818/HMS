from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, DoctorProfile, PatientProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_google_user', 'created_at']
    list_filter = ['role', 'is_google_user', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone', 'google_id', 'is_google_user')}),
    )


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'license_number', 'consultation_fee', 'is_available']
    list_filter = ['specialty', 'is_available']
    search_fields = ['user__username', 'user__email', 'license_number']


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'blood_group', 'emergency_contact']
    list_filter = ['blood_group']
    search_fields = ['user__username', 'user__email']
