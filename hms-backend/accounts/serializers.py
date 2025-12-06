from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, DoctorProfile, PatientProfile


class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ['specialty', 'license_number', 'consultation_fee', 'bio', 'profile_picture', 'is_available']


class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['date_of_birth', 'blood_group', 'emergency_contact', 'medical_history', 'profile_picture']


class UserSerializer(serializers.ModelSerializer):
    doctor_profile = DoctorProfileSerializer(required=False)
    patient_profile = PatientProfileSerializer(required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone',
                  'is_google_user', 'doctor_profile', 'patient_profile']
        read_only_fields = ['id', 'is_google_user']


class DoctorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'},
                                      label='Confirm Password')

    specialty = serializers.ChoiceField(choices=DoctorProfile.SPECIALTY_CHOICES)
    license_number = serializers.CharField(max_length=100)
    consultation_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    bio = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name',
                  'phone', 'specialty', 'license_number', 'consultation_fee', 'bio']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        # Extract doctor profile data
        specialty = validated_data.pop('specialty')
        license_number = validated_data.pop('license_number')
        consultation_fee = validated_data.pop('consultation_fee')
        bio = validated_data.pop('bio', '')
        validated_data.pop('password2')

        # Create user
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            role='DOCTOR'
        )

        # Create doctor profile
        DoctorProfile.objects.create(
            user=user,
            specialty=specialty,
            license_number=license_number,
            consultation_fee=consultation_fee,
            bio=bio
        )

        return user


class PatientRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'},
                                      label='Confirm Password')

    date_of_birth = serializers.DateField()
    blood_group = serializers.ChoiceField(choices=PatientProfile.BLOOD_GROUP_CHOICES)
    emergency_contact = serializers.CharField(max_length=15)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name',
                  'phone', 'date_of_birth', 'blood_group', 'emergency_contact']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        # Extract patient profile data
        date_of_birth = validated_data.pop('date_of_birth')
        blood_group = validated_data.pop('blood_group')
        emergency_contact = validated_data.pop('emergency_contact')
        validated_data.pop('password2')

        # Create user
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            role='PATIENT'
        )

        # Create patient profile
        PatientProfile.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            blood_group=blood_group,
            emergency_contact=emergency_contact
        )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            # Try username first
            user = authenticate(username=username, password=password)
            
            # If authentication fails, try as email
            if not user:
                try:
                    user_obj = CustomUser.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except CustomUser.DoesNotExist:
                    pass
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "username" and "password"')

