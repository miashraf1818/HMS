from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Create appointment
    path('book/', views.CreateAppointmentView.as_view(), name='book_appointment'),

    # List appointments
    path('patient/', views.PatientAppointmentsView.as_view(), name='patient_appointments'),
    path('doctor/', views.DoctorAppointmentsView.as_view(), name='doctor_appointments'),

    # Appointment details
    path('<uuid:id>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),

    # Update status (doctor)
    path('<uuid:id>/status/', views.UpdateAppointmentStatusView.as_view(), name='update_status'),

    # Cancel appointment (patient)
    path('<uuid:id>/cancel/', views.CancelAppointmentView.as_view(), name='cancel_appointment'),

    # Check availability
    path('availability/<int:doctor_id>/', views.DoctorAvailabilityView.as_view(), name='doctor_availability'),
]
