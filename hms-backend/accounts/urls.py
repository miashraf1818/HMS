from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Traditional Registration
    path('doctor/register/', views.DoctorRegisterView.as_view(), name='doctor_register'),
    path('patient/register/', views.PatientRegisterView.as_view(), name='patient_register'),

    # Google OAuth - Doctor
    path('doctor/auth/google/', views.DoctorGoogleAuthView.as_view(), name='doctor_google_auth'),
    path('doctor/auth/google/complete/', views.DoctorGoogleRegisterView.as_view(), name='doctor_google_register'),

    # Google OAuth - Patient
    path('patient/auth/google/', views.PatientGoogleAuthView.as_view(), name='patient_google_auth'),
    path('patient/auth/google/complete/', views.PatientGoogleRegisterView.as_view(), name='patient_google_register'),

    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.CurrentUserView.as_view(), name='current_user'),

    # Browse Doctors
    path('doctors/', views.DoctorListView.as_view(), name='doctor_list'),
]
