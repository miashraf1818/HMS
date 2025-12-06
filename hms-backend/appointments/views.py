from .google_calendar import GoogleCalendarService
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    CreateAppointmentSerializer,
    UpdateAppointmentStatusSerializer
)
from accounts.models import DoctorProfile, PatientProfile
from django.core.mail import send_mail
from django.conf import settings
import os


# Create Appointment (Patient Only)
class CreateAppointmentView(generics.CreateAPIView):
    serializer_class = CreateAppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Check if user is a patient
        if request.user.role != 'PATIENT':
            return Response(
                {'error': 'Only patients can book appointments'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()

        # Send confirmation email
        self.send_booking_confirmation(appointment)

        # Create Google Calendar event for doctor
        if appointment.doctor.user.is_google_user:
            calendar_service = GoogleCalendarService(appointment.doctor.user)
            event_id = calendar_service.create_appointment_event(appointment)
            if event_id:
                appointment.google_calendar_event_id = event_id
                appointment.save()

        return Response({
            'message': 'Appointment booked successfully',
            'appointment': AppointmentSerializer(appointment).data
        }, status=status.HTTP_201_CREATED)

    def send_booking_confirmation(self, appointment):
        from django.core.mail import EmailMessage
        from icalendar import Calendar, Event as iEvent
        from datetime import datetime, timedelta
        import pytz
        
        # Create iCalendar event
        cal = Calendar()
        cal.add('prodid', '-//HMS Hospital//Appointment//EN')
        cal.add('version', '2.0')
        
        event = iEvent()
        event.add('summary', f'Appointment: Dr. {appointment.doctor.user.get_full_name()}')
        event.add('description', f'''
Medical Appointment

Patient: {appointment.patient.user.get_full_name()}
Doctor: Dr. {appointment.doctor.user.get_full_name()}
Specialty: {appointment.doctor.get_specialty_display()}
Reason: {appointment.reason}
Fee: ₹{appointment.doctor.consultation_fee}

Please arrive 10 minutes early.
        '''.strip())
        
        # Combine date and time
        tz = pytz.timezone('Asia/Kolkata')
        start_dt = datetime.combine(appointment.appointment_date, appointment.appointment_time)
        start_dt = tz.localize(start_dt)
        end_dt = start_dt + timedelta(minutes=30)  # 30-minute appointments
        
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        event.add('dtstamp', datetime.now(tz))
        event.add('location', 'HMS Hospital')
        event.add('status', 'CONFIRMED')
        
        # Add attendees
        event.add('organizer', f'mailto:{appointment.doctor.user.email}')
        event.add('attendee', f'mailto:{appointment.patient.user.email}')
        
        # Add reminders
        from icalendar import Alarm
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', 'Appointment Reminder')
        alarm.add('trigger', timedelta(hours=-24))  # 24 hours before
        event.add_component(alarm)
        
        cal.add_component(event)
        
        # Generate .ics file content
        ics_content = cal.to_ical()
        
        # Email to patient
        patient_subject = 'Appointment Confirmation - HMS Hospital'
        patient_message = f"""
Dear {appointment.patient.user.get_full_name()},

Your appointment has been successfully booked!

Details:
Doctor: Dr. {appointment.doctor.user.get_full_name()}
Specialty: {appointment.doctor.get_specialty_display()}
Date: {appointment.appointment_date}
Time: {appointment.appointment_time}
Consultation Fee: ₹{appointment.doctor.consultation_fee}
Status: {appointment.get_status_display()}

📅 CALENDAR INVITE ATTACHED
Click the attached .ics file to add this appointment to your calendar (works with Google Calendar, Outlook, Apple Calendar).

Please arrive 10 minutes early.

Best regards,
HMS Hospital Team
        """.strip()
        
        # Get admin email for BCC
        admin_email = os.getenv('ADMIN_EMAIL', '')
        patient_recipients = [appointment.patient.user.email]
        if admin_email:
            patient_recipients.append(admin_email)
        
        # Send email with calendar attachment
        patient_email = EmailMessage(
            patient_subject,
            patient_message,
            settings.DEFAULT_FROM_EMAIL,
            patient_recipients,
        )
        patient_email.attach('appointment.ics', ics_content, 'text/calendar')
        patient_email.send(fail_silently=True)

        # Email to doctor
        doctor_subject = 'New Appointment Booking - HMS Hospital'
        doctor_message = f"""
Dear Dr. {appointment.doctor.user.get_full_name()},

You have a new appointment booking!

Details:
Patient: {appointment.patient.user.get_full_name()}
Date: {appointment.appointment_date}
Time: {appointment.appointment_time}
Reason: {appointment.reason}

📅 CALENDAR INVITE ATTACHED
Click the attached .ics file to add this appointment to your calendar.

Please log in to your dashboard to confirm.

Best regards,
HMS Hospital Team
        """.strip()

        doctor_email = EmailMessage(
            doctor_subject,
            doctor_message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.doctor.user.email],
        )
        doctor_email.attach('appointment.ics', ics_content, 'text/calendar')
        doctor_email.send(fail_silently=True)


# List Patient's Appointments
class PatientAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'PATIENT':
            return Appointment.objects.none()
        return Appointment.objects.filter(patient=self.request.user.patient_profile)


# List Doctor's Appointments
class DoctorAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'DOCTOR':
            return Appointment.objects.none()
        return Appointment.objects.filter(doctor=self.request.user.doctor_profile)


# Get Single Appointment Details
class AppointmentDetailView(generics.RetrieveAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return Appointment.objects.filter(patient=user.patient_profile)
        elif user.role == 'DOCTOR':
            return Appointment.objects.filter(doctor=user.doctor_profile)
        return Appointment.objects.none()


# Update Appointment Status (Doctor Only)
class UpdateAppointmentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, id):
        # Check if user is a doctor
        if request.user.role != 'DOCTOR':
            return Response(
                {'error': 'Only doctors can update appointment status'},
                status=status.HTTP_403_FORBIDDEN
            )

        appointment = get_object_or_404(
            Appointment,
            id=id,
            doctor=request.user.doctor_profile
        )

        serializer = UpdateAppointmentStatusSerializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Send status update email
        self.send_status_update_email(appointment)

        # Update Google Calendar event
        if appointment.doctor.user.is_google_user:
            calendar_service = GoogleCalendarService(appointment.doctor.user)
            calendar_service.update_appointment_event(appointment)

        return Response({
            'message': 'Appointment status updated',
            'appointment': AppointmentSerializer(appointment).data
        })

    def send_status_update_email(self, appointment):
        subject = f'Appointment Status Update - HMS Hospital'
        message = f"""
        Dear {appointment.patient.user.get_full_name()},

        Your appointment status has been updated!

        Details:
        Doctor: Dr. {appointment.doctor.user.get_full_name()}
        Date: {appointment.appointment_date}
        Time: {appointment.appointment_time}
        New Status: {appointment.get_status_display()}

        Best regards,
        HMS Hospital Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.patient.user.email],
            fail_silently=True,
        )


# Cancel Appointment (Patient Only)
class CancelAppointmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        if request.user.role != 'PATIENT':
            return Response(
                {'error': 'Only patients can cancel their appointments'},
                status=status.HTTP_403_FORBIDDEN
            )

        appointment = get_object_or_404(
            Appointment,
            id=id,
            patient=request.user.patient_profile
        )

        if appointment.status == 'CANCELLED':
            return Response(
                {'error': 'Appointment is already cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = 'CANCELLED'
        appointment.save()

        # Send cancellation email
        self.send_cancellation_email(appointment)

        # Delete Google Calendar event
        if appointment.doctor.user.is_google_user:
            calendar_service = GoogleCalendarService(appointment.doctor.user)
            calendar_service.delete_appointment_event(appointment)

        return Response({
            'message': 'Appointment cancelled successfully',
            'appointment': AppointmentSerializer(appointment).data
        })

    def send_cancellation_email(self, appointment):
        # Email to patient
        patient_subject = 'Appointment Cancellation - HMS Hospital'
        patient_message = f"""
        Dear {appointment.patient.user.get_full_name()},

        Your appointment has been cancelled.

        Details:
        Doctor: Dr. {appointment.doctor.user.get_full_name()}
        Date: {appointment.appointment_date}
        Time: {appointment.appointment_time}

        You can book a new appointment anytime.

        Best regards,
        HMS Hospital Team
        """

        send_mail(
            patient_subject,
            patient_message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.patient.user.email],
            fail_silently=True,
        )

        # Email to doctor
        doctor_subject = 'Appointment Cancelled - HMS Hospital'
        doctor_message = f"""
        Dear Dr. {appointment.doctor.user.get_full_name()},

        An appointment has been cancelled.

        Details:
        Patient: {appointment.patient.user.get_full_name()}
        Date: {appointment.appointment_date}
        Time: {appointment.appointment_time}

        Best regards,
        HMS Hospital Team
        """

        send_mail(
            doctor_subject,
            doctor_message,
            settings.DEFAULT_FROM_EMAIL,
            [appointment.doctor.user.email],
            fail_silently=True,
        )


# Get Available Time Slots for a Doctor
class DoctorAvailabilityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, doctor_id):
        """
        Get available time slots for a doctor on a specific date
        Query params: ?date=YYYY-MM-DD
        """
        from datetime import datetime, time, timedelta

        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        doctor = get_object_or_404(DoctorProfile, id=doctor_id)

        # Define working hours (9 AM to 5 PM, 30-minute slots)
        working_hours = []
        start_time = time(9, 0)
        end_time = time(17, 0)
        current_time = datetime.combine(appointment_date, start_time)
        end_datetime = datetime.combine(appointment_date, end_time)

        while current_time < end_datetime:
            working_hours.append(current_time.time())
            current_time += timedelta(minutes=30)

        # Get booked slots
        booked_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status__in=['PENDING', 'CONFIRMED']
        ).values_list('appointment_time', flat=True)

        # Available slots
        available_slots = [
            slot.strftime('%H:%M') for slot in working_hours
            if slot not in booked_appointments
        ]

        return Response({
            'doctor': doctor.user.get_full_name(),
            'date': date_str,
            'available_slots': available_slots
        })
