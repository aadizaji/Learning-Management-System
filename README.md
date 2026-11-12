# 🎓 Sematec LMS
### Bilingual Learning Management System

**Sematec LMS** is a full-stack Learning Management System developed with **Python and Django** for managing the educational and administrative operations of IT training institutes.
The platform integrates student and instructor management, courses, registrations, academic scheduling, attendance, examinations, certificates, surveys, and reporting into a centralized, responsive web application.
It supports **English and Persian**, **Gregorian and Jalali calendars**, role-based access control, automated class scheduling, and CSV/PDF/PNG exports.


## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, Django 6.1.1 |
| Frontend | HTML5, CSS3, JavaScript |
| UI Framework | Bootstrap 5, Bootstrap Icons |
| Database | SQLite, Django ORM |
| Authentication | Django Authentication, Groups & Permissions |
| Internationalization | Django i18n, gettext |
| Certificate Generation | Pillow, arabic-reshaper, python-bidi |
| Reporting | Python CSV |
| Fonts | Plus Jakarta Sans, Vazirmatn |
| Additional Tools | Git, GitHub, Virtual Environments |

The application follows Django's **Model–Template–View (MTV)** architecture, separating database models, business logic, templates, and frontend interactions.

---

## ✨ Main Features

### 1. Dashboard

A centralized dashboard displaying essential educational information, including students, instructors, courses, registrations, upcoming classes, examinations, and quick-access shortcuts.

The interface uses a clean, minimal design without unnecessary analytical charts.

### 2. Student & Instructor Management

- Create, view, update, and delete records.
- Card-based lists with profile photographs.
- Detailed read-only profile pages.
- Search, filtering, and pagination.
- Student contact, educational, and professional information.
- Instructor qualifications and assigned courses.
- CSV export.

### 3. Course & Category Management

- Course creation and management.
- Categories, descriptions, posters, and syllabus topics.
- Tuition fees with thousand separators.
- Course capacity and availability.
- In-person, remote, and hybrid delivery methods.
- Weekly schedules and classroom assignments.
- Animated circular capacity indicators.

Course syllabus topics can be dynamically added or removed through JavaScript.

### 4. Registration Management

The `Register` model connects students to courses and stores registration-related information.

Features include registration management, instructor assignment, capacity validation, duplicate registration checks, and registration statuses:

- Active
- Completed
- Dropped

### 5. Academic Calendar & Scheduling

The system generates class sessions automatically from course dates and weekly schedules.

Each schedule includes an instructor, weekday, start/end time, and classroom.

Sessions support **Scheduled, Completed, and Cancelled** statuses.

The interactive calendar supports Gregorian and Jalali dates, navigation, filtering, and class details.

### 6. Attendance Management

Attendance records are connected to actual class sessions and registered students.

- Present, Absent, and Unmarked statuses.
- Attendance recording and editing.
- Session-based attendance management.
- CSV reports for individual sessions and courses.
- Instructor-specific access restrictions.

### 7. Examination Management

The examination module supports:

- Online/offline examination definitions.
- Examination dates and passing scores.
- Final, written, and practical grades.
- Automatic pass/fail evaluation.
- Green and red result indicators.
- CSV grade reports.

Written and practical scores are optional. The module records results but does not host online exams.

### 8. Certificate Management

Certificates are linked to student registrations.

Features include:

- English and Persian certificates.
- Unique serial numbers.
- Live preview without saving.
- Certificate creation, editing, and deletion.
- PDF and PNG exports.
- Persian text rendering support.

**Pillow** handles certificate rendering, while `arabic-reshaper` and `python-bidi` provide alternative Persian text processing where needed.

### 9. Survey & Evaluation

A configurable survey system for evaluating courses and instructors.

It supports separate questions for students and instructors, rating-based responses, question management, and evaluation summaries.

Responses are connected to the relevant course and student registration or instructor.

### 10. Authentication & Access Control

The application uses Django's built-in authentication system.

Two operational roles are supported:

| Manager | Instructor |
|---|---|
| Manage educational records | View assigned courses |
| Create and edit courses | View related students |
| Manage registrations | Manage own class attendance |
| Manage examinations | Record grades for own classes |
| Issue certificates | Cannot issue certificates |
| Manage user accounts | Cannot delete students or courses |

Access restrictions are enforced through Django Views and permissions, not only through the user interface.

### 11. Bilingual Interface

- English and Persian interfaces.
- LTR and RTL layouts.
- Gregorian and Jalali date selection.
- Django translation catalogs.
- Vazirmatn for Persian typography.
- Plus Jakarta Sans for English typography.
- Dark and light themes.

### 12. Reporting System

CSV reporting is available across major modules, including students, instructors, courses, registrations, attendance, examinations, certificates, and surveys.

Reports use UTF-8 BOM for improved Persian text compatibility.

---

## 🏗️ Architecture & Database Relationships

Sematec LMS is organized around interconnected Django models.

```text
CourseCategory
    └── Course
         ├── CourseTopic
         ├── CourseSchedule
         │      └── ClassSession
         │             └── Attendance
         ├── Register
         │      ├── Student
         │      ├── Attendance
         │      └── Certificate
         ├── Exam
         │      └── ExamGrade
         └── SurveyResponse
                └── SurveyAnswer
```

### How the Modules Work Together

1. A **Course** is created with instructors, dates, capacity, and weekly schedules.
2. The system automatically generates **ClassSession** records.
3. Students join courses through **Register**.
4. Attendance is recorded for registered students in scheduled sessions.
5. Examinations evaluate registered students and store grades.
6. Certificates can be issued for individual course registrations.
7. Surveys collect feedback associated with courses and participants.
8. Administrative information is available through dashboards and CSV reports.

Django ORM manages these relationships using foreign keys, many-to-many relationships, and database constraints.

---

## ✅ Validation & Data Integrity

The project uses Django Forms, model validation, and database constraints to protect educational records.

Key validation rules include:

- Required fields and valid input formats.
- Course capacity restrictions.
- Duplicate registration checks.
- Valid course and instructor relationships.
- Classroom scheduling conflict detection.
- Valid class start/end times.
- Examination score boundaries.
- Unique examination results per registration.
- Duplicate attendance prevention.
- Unique certificate serial numbers.
- Role-based access restrictions.

Selected multi-step operations use `transaction.atomic()` to help maintain database consistency.

JavaScript provides additional frontend validation and interaction, while critical validation remains on the server.

---

## 📁 Project Structure

```text
SEMATEC_LMS/
│
├── manage.py
├── requirements.txt
│
├── congif/
│   ├── settings.py
│   └── urls.py
│
├── accounts/
│   ├── views.py
│   ├── forms.py
│   └── tests.py
│
├── lms/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   ├── test_certificates.py
│   ├── migrations/
│   ├── services/
│   │   └── session_generator.py
│   ├── templates/
│   └── static/
│
├── templates/
├── locale/
└── media/
```

The `lms` application contains the main educational functionality, while `accounts` manages user authentication and account-related operations.

---

## 🚀 Installation & Setup

### Prerequisites

- Python
- pip
- Git
- A modern web browser

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the URL with your repository address.

### 2. Create a Virtual Environment

**Windows:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply Migrations

```bash
python manage.py migrate
```

### 5. Create a Superuser

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

Open:

`http://127.0.0.1:8000/`

---

## 🔒 Security & Deployment Notes

Sematec LMS is primarily developed for **local execution and academic demonstration**.

The project uses Django Authentication, CSRF protection, ORM-based database operations, and authorization checks.

Before production deployment:

- Set `DEBUG=False`.
- Configure a secure `SECRET_KEY`.
- Configure `ALLOWED_HOSTS`.
- Enable HTTPS.
- Review user permissions and file uploads.
- Protect sensitive educational records.
- Configure static and media files.
- Establish database backups.

SQLite is used for local development; PostgreSQL may be considered for larger deployments.

---


## 🎯 Project Purpose

Sematec LMS was developed to demonstrate real-world **full-stack development with Django**, including relational database modeling, CRUD operations, authentication, authorization, validation, automated scheduling, internationalization, frontend interactions, and reporting.

By connecting essential educational processes within one application, it provides a practical foundation for managing the operations of an IT training institute.

**Built with Python, Django, HTML, CSS, JavaScript, Bootstrap, and SQLite.**
