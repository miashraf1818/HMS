# 🏥 Hospital Management System (HMS)

A comprehensive Hospital Management System built with Django (Backend) and Next.js (Frontend) for managing patient appointments, doctor schedules, and healthcare workflows.

## 🌟 Features

### Core Functionality
- **Patient Management**: Registration, login, profile management
- **Doctor Management**: Registration, login, appointment management
- **Appointment System**: Book, view, approve, cancel appointments
- **Email Notifications**: Welcome emails, appointment confirmations with calendar invites
- **Google OAuth**: One-click sign-in for patients
- **Calendar Integration**: Automatic .ics file generation for easy calendar import
- **Role-Based Access**: Separate dashboards for patients and doctors
- **Admin Monitoring**: All emails copied to admin for oversight

### Technical Features
- RESTful API architecture
- JWT authentication
- PostgreSQL database
- Responsive UI design
- Email notifications with SMTP
- iCalendar (.ics) attachments
- Session management
- Protected routes

## 🛠️ Tech Stack

### Backend
- Django 6.0
- Django REST Framework
- PostgreSQL
- Google OAuth 2.0
- Python 3.13

### Frontend
- Next.js 14
- React
- TypeScript
- Tailwind CSS
- Axios

## 📋 Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL
- Gmail account (for SMTP)
- Google Cloud Console project (for OAuth)

## 🚀 Installation

### Backend Setup

```bash
cd hms-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create PostgreSQL database
createdb hms_db
createuser hms_user

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

### Frontend Setup

```bash
cd hms-frontend
npm install
npm run dev
```

## ⚙️ Configuration

### Backend (.env)
```bash
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=hms_db
DB_USER=hms_user
DB_PASSWORD=your-password

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id
```

## 📱 Usage

1. **Access the application**: http://localhost:3000
2. **Register** as a patient or doctor
3. **Login** using credentials or Google OAuth (patients only)
4. **Book appointments** (patients)
5. **Manage appointments** (doctors)
6. **Receive email notifications** with calendar invites

## 🧪 API Endpoints

### Authentication
- `POST /api/accounts/login/` - Login
- `POST /api/accounts/logout/` - Logout
- `POST /api/accounts/patient/register/` - Patient registration
- `POST /api/accounts/doctor/register/` - Doctor registration
- `GET /api/accounts/me/` - Get current user

### Appointments
- `POST /api/appointments/book/` - Book appointment
- `GET /api/appointments/patient/` - Get patient appointments
- `GET /api/appointments/doctor/` - Get doctor appointments
- `PATCH /api/appointments/{id}/status/` - Update appointment status
- `GET /api/appointments/availability/{doctor_id}/?date={date}` - Check availability

## 📧 Email Features

- **Welcome Emails**: Sent on registration
- **Appointment Confirmations**: Sent when booking
- **Calendar Invites**: .ics files attached to emails
- **Status Updates**: Sent when appointments are approved/completed
- **Admin Copies**: All emails copied to admin

## 🔒 Security

- Password hashing with Django's built-in system
- JWT token authentication
- CSRF protection
- Session management
- Environment variable configuration
- Role-based access control

## 👥 User Roles

### Patient
- Register and login
- Browse doctors
- Book appointments
- View appointment history
- Cancel appointments
- Google OAuth login

### Doctor
- Register and login
- View appointment requests
- Approve/reject appointments
- Mark appointments as completed
- Set availability

## 🎯 Project Structure

```
hms-project/
├── hms-backend/          # Django backend
│   ├── accounts/         # User authentication
│   ├── appointments/     # Appointment management
│   ├── config/          # Settings
│   └── manage.py
├── hms-frontend/        # Next.js frontend
│   ├── src/
│   │   ├── app/        # Pages
│   │   ├── components/ # React components
│   │   └── context/    # Auth context
│   └── package.json
└── README.md
```

## 📊 Database Schema

### Users
- Custom user model with role (PATIENT/DOCTOR)
- Patient profiles with medical info
- Doctor profiles with specialty, license, fees

### Appointments
- Patient-Doctor relationship
- Date, time, status tracking
- Calendar event IDs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

This project is for educational purposes.

## 👨‍💻 Developer

**Mohammed Ikram**  
Internship Project - Hospital Management System

## 🙏 Acknowledgments

- Django REST Framework
- Next.js Team
- Google OAuth Documentation
- iCalendar RFC5545

---

**Status**: ✅ Production Ready | **Version**: 1.0.0 | **Last Updated**: December 2025
