from django.core.management.base import BaseCommand
from appointments.models import Appointment
from appointments.google_calendar import GoogleCalendarService


class Command(BaseCommand):
    help = 'Sync all appointments to Google Calendar'

    def handle(self, *args, **options):
        appointments = Appointment.objects.filter(
            status__in=['PENDING', 'CONFIRMED'],
            google_calendar_event_id__isnull=True
        )

        synced_count = 0

        for appointment in appointments:
            if appointment.doctor.user.is_google_user:
                calendar_service = GoogleCalendarService(appointment.doctor.user)
                event_id = calendar_service.create_appointment_event(appointment)

                if event_id:
                    appointment.google_calendar_event_id = event_id
                    appointment.save()
                    synced_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Synced appointment {appointment.id}')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'\nTotal appointments synced: {synced_count}')
        )