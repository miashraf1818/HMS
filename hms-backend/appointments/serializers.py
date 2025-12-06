from rest_framework import serializers
from .models import Appointment
from accounts.models import DoctorProfile, PatientProfile
from accounts.serializers import UserSerializer


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    doctor_specialty = serializers.CharField(source='doctor.get_specialty_display', read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'patient', 'appointment_date', 'appointment_time',
            'reason', 'status', 'google_calendar_event_id',
            'doctor_name', 'doctor_specialty', 'patient_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'google_calendar_event_id', 'created_at', 'updated_at']


class CreateAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'reason']

    def validate(self, attrs):
        doctor = attrs.get('doctor')
        appointment_date = attrs.get('appointment_date')
        appointment_time = attrs.get('appointment_time')

        # Check if doctor is available
        if not doctor.is_available:
            raise serializers.ValidationError("This doctor is currently not available")

        # Check if slot is already booked
        existing = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['PENDING', 'CONFIRMED']
        ).exists()

        if existing:
            raise serializers.ValidationError("This time slot is already booked")

        return attrs

    def create(self, validated_data):
        # Get patient from request user
        request = self.context.get('request')
        patient = request.user.patient_profile

        appointment = Appointment.objects.create(
            patient=patient,
            **validated_data
        )

        return appointment


class UpdateAppointmentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['status']

    def validate_status(self, value):
        if value not in ['CONFIRMED', 'COMPLETED', 'CANCELLED']:
            raise serializers.ValidationError("Invalid status")
        return value
