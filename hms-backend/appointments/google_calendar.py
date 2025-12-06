from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.conf import settings
from datetime import datetime, timedelta


class GoogleCalendarService:
    """
    Service for Google Calendar API integration
    """

    def __init__(self, user):
        self.user = user
        self.service = None

        if user.google_token:
            self._init_service()

    def _init_service(self):
        """Initialize Google Calendar service with user's token"""
        try:
            creds = Credentials(
                token=self.user.google_token.get('access_token'),
                refresh_token=self.user.google_refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET
            )

            self.service = build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"Error initializing Google Calendar service: {e}")
            self.service = None

    def create_appointment_event(self, appointment):
        """
        Create a calendar event for an appointment
        """
        if not self.service:
            return None

        try:
            # Combine date and time
            start_datetime = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time
            )
            end_datetime = start_datetime + timedelta(minutes=30)  # 30-minute appointments

            # Event details
            event = {
                'summary': f'Appointment with {appointment.patient.user.get_full_name()}',
                'description': f'Reason: {appointment.reason}\nPatient Phone: {appointment.patient.user.phone}',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'attendees': [
                    {'email': appointment.patient.user.email},
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60},  # 1 hour before
                    ],
                },
            }

            # Create event
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'  # Send notifications to attendees
            ).execute()

            return created_event.get('id')

        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None

    def update_appointment_event(self, appointment):
        """
        Update an existing calendar event
        """
        if not self.service or not appointment.google_calendar_event_id:
            return False

        try:
            # Combine date and time
            start_datetime = datetime.combine(
                appointment.appointment_date,
                appointment.appointment_time
            )
            end_datetime = start_datetime + timedelta(minutes=30)

            # Get existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=appointment.google_calendar_event_id
            ).execute()

            # Update event details
            event[
                'summary'] = f'Appointment with {appointment.patient.user.get_full_name()} - {appointment.get_status_display()}'
            event['start'] = {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Asia/Kolkata',
            }
            event['end'] = {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Kolkata',
            }

            # Update event
            self.service.events().update(
                calendarId='primary',
                eventId=appointment.google_calendar_event_id,
                body=event,
                sendUpdates='all'
            ).execute()

            return True

        except Exception as e:
            print(f"Error updating calendar event: {e}")
            return False

    def delete_appointment_event(self, appointment):
        """
        Delete a calendar event
        """
        if not self.service or not appointment.google_calendar_event_id:
            return False

        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=appointment.google_calendar_event_id,
                sendUpdates='all'
            ).execute()

            return True

        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            return False