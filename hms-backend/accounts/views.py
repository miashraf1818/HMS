# Add these imports at the top
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
import jwt
from datetime import datetime, timedelta
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from .serializers import (
    DoctorRegistrationSerializer,
    PatientRegistrationSerializer,
    LoginSerializer,
    UserSerializer
)
from .models import CustomUser, DoctorProfile, PatientProfile


# Doctor Registration View
class DoctorRegisterView(generics.CreateAPIView):
    serializer_class = DoctorRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Auto login after registration
        login(request, user)

        return Response({
            'message': 'Doctor registered successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


# Patient Registration View
class PatientRegisterView(generics.CreateAPIView):
    serializer_class = PatientRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Auto login after registration
        login(request, user)

        return Response({
            'message': 'Patient registered successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


# Login View
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        login(request, user)

        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)


# Logout View
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


# Current User View
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# Doctor List (for patients to browse)
class DoctorListView(generics.ListAPIView):
    queryset = DoctorProfile.objects.filter(is_available=True)
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        doctors = self.get_queryset()
        data = []

        for doctor in doctors:
            data.append({
                'id': str(doctor.id),  # Changed from doctor.user.id to doctor.id
                'user_id': str(doctor.user.id),
                'name': doctor.user.get_full_name(),
                'specialty': doctor.get_specialty_display(),
                'consultation_fee': str(doctor.consultation_fee),
                'bio': doctor.bio,
                'profile_picture': doctor.profile_picture.url if doctor.profile_picture else None
            })

        return Response(data)


# Google OAuth - Doctor
class DoctorGoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Expects: { "token": "google_id_token" }
        """
        token = request.data.get('token')

        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify Google token
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            google_id = idinfo['sub']
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            # Check if user exists
            user = CustomUser.objects.filter(google_id=google_id).first()

            if user:
                # User exists, login
                login(request, user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            else:
                # New user - need to complete profile
                return Response({
                    'message': 'Please complete your doctor profile',
                    'google_data': {
                        'google_id': google_id,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name
                    }
                }, status=status.HTTP_206_PARTIAL_CONTENT)

        except ValueError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class DoctorGoogleRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Complete doctor registration after Google OAuth
        Expects: {
            "google_id": "...",
            "email": "...",
            "first_name": "...",
            "last_name": "...",
            "phone": "...",
            "specialty": "...",
            "license_number": "...",
            "consultation_fee": "...",
            "bio": "...",
            "google_token": {...},  # Optional - for calendar access
            "google_refresh_token": "..."  # Optional - for calendar access
        }
        """
        google_id = request.data.get('google_id')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        phone = request.data.get('phone')
        specialty = request.data.get('specialty')
        license_number = request.data.get('license_number')
        consultation_fee = request.data.get('consultation_fee')
        bio = request.data.get('bio', '')

        # Create username from email
        username = email.split('@')[0]

        # Check if username exists, append number if needed
        base_username = username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user
        user = CustomUser.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='DOCTOR',
            google_id=google_id,
            is_google_user=True
        )
        user.set_unusable_password()  # No password for OAuth users

        # ✅ Store Google tokens for calendar access (CORRECTED PLACEMENT)
        google_token = request.data.get('google_token')  # Full token object from frontend
        google_refresh_token = request.data.get('google_refresh_token')

        if google_token:
            user.google_token = google_token
        if google_refresh_token:
            user.google_refresh_token = google_refresh_token

        user.save()  # ✅ Save user with tokens

        # Create doctor profile
        DoctorProfile.objects.create(
            user=user,
            specialty=specialty,
            license_number=license_number,
            consultation_fee=consultation_fee,
            bio=bio
        )

        # Auto login
        login(request, user)

        # Send welcome email
        send_welcome_email(user, 'DOCTOR')

        return Response({
            'message': 'Doctor registered successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


# Google OAuth - Patient
class PatientGoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')

        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            google_id = idinfo['sub']
            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            # Check if user exists by google_id OR email
            user = CustomUser.objects.filter(google_id=google_id).first()
            
            if not user:
                # Check by email (user might have registered manually)
                user = CustomUser.objects.filter(email=email, role='PATIENT').first()
                
                if user:
                    # Update user with google_id for future logins
                    user.google_id = google_id
                    user.is_google_user = True
                    user.save()

            if user:
                # User exists - log them in
                login(request, user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            else:
                # New user - show registration form
                return Response({
                    'message': 'Please complete your patient profile',
                    'google_data': {
                        'google_id': google_id,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name
                    }
                }, status=status.HTTP_206_PARTIAL_CONTENT)

        except ValueError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class PatientGoogleRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Complete patient registration after Google OAuth
        """
        google_id = request.data.get('google_id')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        phone = request.data.get('phone')
        date_of_birth = request.data.get('date_of_birth')
        blood_group = request.data.get('blood_group')
        emergency_contact = request.data.get('emergency_contact')

        username = email.split('@')[0]
        base_username = username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = CustomUser.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='PATIENT',
            google_id=google_id,
            is_google_user=True
        )
        user.set_unusable_password()

        # ✅ Store Google tokens for calendar access (ADDED FOR PATIENT TOO)
        google_token = request.data.get('google_token')
        google_refresh_token = request.data.get('google_refresh_token')

        if google_token:
            user.google_token = google_token
        if google_refresh_token:
            user.google_refresh_token = google_refresh_token

        user.save()  # ✅ Save user with tokens

        PatientProfile.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            blood_group=blood_group,
            emergency_contact=emergency_contact
        )

        login(request, user)
        send_welcome_email(user, 'PATIENT')

        return Response({
            'message': 'Patient registered successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


# Helper function for sending emails
def send_welcome_email(user, role):
    from django.core.mail import send_mail
    import os

    subject = f'Welcome to HMS Hospital - {role.title()} Registration'
    message = f"""
    Dear {user.get_full_name()},

    Welcome to HMS Hospital Management System!

    Your {role.lower()} account has been successfully created.

    Email: {user.email}
    Role: {role.title()}

    You can now access your dashboard and manage your appointments.

    Best regards,
    HMS Hospital Team
    """

    # Get admin email from environment variable
    admin_email = os.getenv('ADMIN_EMAIL', '')
    recipient_list = [user.email]
    
    # Add admin email to BCC if configured
    if admin_email:
        recipient_list.append(admin_email)

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,  # Sends to both user and admin
        fail_silently=True,
    )

