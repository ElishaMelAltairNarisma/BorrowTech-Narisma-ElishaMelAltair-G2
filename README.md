# BorrowTech - University IT Laboratory Equipment Borrowing & Inventory Management System

[![Django](https://img.shields.io/badge/Django-6.1-0C4B33?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed-emerald?style=for-the-badge&logo=pytest&logoColor=white)]()

**BorrowTech** is a web-based laboratory equipment borrowing and inventory management platform designed for university IT departments. It replaces manual paper logbooks by enabling IT students to check live hardware availability and submit digital reservations, while giving lab custodians an automated dashboard to manage approvals, track returns, and maintain an accurate asset audit trail.

> **Project Phase:** IM2 Project Development 1 – Account Feature  
> **Repository:** `BorrowTech-Narisma-ElishaMelAltair-G2`  
> **Student:** Elisha Mel Altair Narisma  
> **Section:** G2  

---

## 🚀 Key Features Built in Phase 1: Account Feature

### 1. Account Registration
- **Dynamic Registration Form:** Accessible to students and lab personnel with custom university fields (Student/Staff ID, Department, Year Level, Contact Number, and Role).
- **Strict Input Validation:** Enforces required fields, email format verification, uniqueness check for both username and email, and password confirmation matching.
- **Secure Password Hashing:** Utilizes Django's PBKDF2/SHA256 password hashing. Plaintext passwords are never stored.
- **Feedback & Notifications:** Real-time feedback with colored dismissal alerts for both success and validation error states.

### 2. Login & Logout Authentication Flow
- **Flexible Credential Login:** Supports authenticating with either **Username OR Email Address**.
- **Error Handling:** Shows clear, security-conscious error alerts on invalid credentials without leaking internal state.
- **Session Management:** Secure login and logout flows that completely flush sessions and cookies upon sign-out.
- **Route Protection:** `@login_required` decorators ensure unauthenticated requests to protected pages are redirected to the login page with a safe `?next=` return URL.

### 3. Role-Based User Dashboards
The system features two distinct, role-based workflows tailored to university laboratory operations:
- **IT Student Dashboard (`/dashboard/student/`):**
  - Live hardware availability catalog (Arduino Kits, Raspberry Pi 4, Fluke Multimeters, Cisco Switches, Oscilloscopes).
  - Active digital reservation status tracker (Active Loan, Pending Approval, Returned).
  - Borrowing quota indicator and university IT lab policies.
- **Laboratory Custodian Console (`/dashboard/custodian/`):**
  - Real-time inventory overview (total equipment units, available units, active loans, overdue items).
  - Pending reservation approval queue with instantaneous Approve/Reject actions.
  - University asset audit trail logging handovers, condition inspections, and return verifications.
- **Strict URL Protection:** Enforced via custom `@student_required` and `@custodian_required` decorators. A student typing the custodian URL (or vice-versa) is immediately blocked, redirected to their authorized dashboard, and presented with an **Access Denied** alert.

### 4. User Profile Management (`/profile/`)
- Logged-in users can view their comprehensive profile data (Role, Student ID, Contact Number, Department, Year Level, Registration Date, and Last Login).
- Users can update their profile information and upload custom avatar photos (`/media/profile_photos/`).
- **Privacy & Security Boundary:** Users can **only view and edit their own profile** (`request.user`).
- Built-in secure password change feature (`/profile/change-password/`) maintaining authenticated session integrity.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend & Frontend** | **Full Stack Django 6.1** | Server-rendered Django templates with template inheritance |
| **Database** | **PostgreSQL / Supabase** | Production-ready PostgreSQL database with connection pooling |
| **Styling** | **Tailwind CSS & FontAwesome** | Responsive modern UI with university IT lab branding |
| **Authentication** | **Django Auth + Custom User** | Custom `accounts.User` model inheriting from `AbstractUser` |
| **Environment** | **Python Dotenv & dj-database-url** | 12-factor configuration via `.env` file |

---

## 📋 Repository Structure

```text
BorrowTech-Narisma-ElishaMelAltair-G2/
├── accounts/
│   ├── management/
│   │   └── commands/
│   │       └── seed_borrowtech.py     # Seeds test accounts for both roles
│   ├── migrations/
│   │   └── 0001_initial.py            # Initial Custom User migration
│   ├── admin.py                       # Django Admin configuration for User
│   ├── apps.py                        # App configuration
│   ├── decorators.py                  # Strict role authorization decorators
│   ├── forms.py                       # Registration, Login, Profile & Password forms
│   ├── models.py                      # Custom User model (roles, ID, contact, avatar)
│   ├── tests.py                       # Comprehensive 18-case test suite
│   ├── urls.py                        # Account routing paths
│   └── views.py                       # View logic for auth, dashboards, and profile
├── borrowtech_project/
│   ├── asgi.py
│   ├── settings.py                    # Project settings (PostgreSQL/Supabase ready)
│   ├── urls.py                        # Main URL dispatcher
│   └── wsgi.py
├── templates/
│   ├── base.html                      # Base layout with navbar, alerts, footer
│   └── accounts/
│       ├── change_password.html       # Change password form
│       ├── custodian_dashboard.html   # Role 2: Custodian Console
│       ├── home.html                  # Landing page
│       ├── login.html                 # Login page
│       ├── profile.html               # User profile view & update
│       ├── register.html              # Registration form
│       └── student_dashboard.html     # Role 1: Student Dashboard
├── .env.example                       # Sample environment file
├── .gitignore                         # Excludes venv, .env, media, __pycache__
├── manage.py                          # Django management script
├── README.md                          # Comprehensive project documentation
└── requirements.txt                   # Frozen dependencies
```

---

## ⚙️ Setup & Installation Guide

### Prerequisites
- Python 3.12+
- Git
- PostgreSQL or a free [Supabase](https://supabase.com/) project

### 1. Clone the Repository
```bash
git clone https://github.com/ElishaMelAltairNarisma/BorrowTech-Narisma-ElishaMelAltair-G2.git
cd BorrowTech-Narisma-ElishaMelAltair-G2
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and configure your secret key and **PostgreSQL / Supabase** connection string:

#### For Supabase (Recommended Cloud PostgreSQL):
1. Create a project at [supabase.com](https://supabase.com).
2. Go to **Project Settings** > **Database** > **Connection String** > **URI**.
3. Set `DATABASE_URL` in `.env`:
```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DATABASE_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require
```

#### For Local PostgreSQL:
```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/borrowtech_db
```

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Seed Demo Laboratory Accounts
Run the built-in seeding command to populate test accounts for both roles:
```bash
python manage.py seed_borrowtech
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🔑 Demo Account Credentials

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **IT Student** | `it_student` | `StudentPass2026!` | Explore hardware catalog, active loans, and student dashboard |
| **Lab Custodian** | `lab_custodian` | `CustodianPass2026!` | Manage pending requests, equipment inventory, and audit trail |
| **Superuser (Admin)** | `admin` | `AdminPass2026!` | Full administrative access to Django admin at `/admin/` |

---

## 🧪 Automated Unit Testing

A comprehensive test suite of **18 test cases** covering registration validation, authentication, role authorization, and profile management is included.

Run tests using:
```bash
python manage.py test
```

Expected output:
```text
Creating test database for alias 'default'...
..................
----------------------------------------------------------------------
Ran 18 tests in 0.85s

OK
```

---

## 📝 Git Commit Standards (Conventional Commits)
This repository strictly follows the **Conventional Commits** specification:
- `feat(accounts): implement custom user model with role-based system`
- `feat(accounts): implement user registration with validation and password hashing`
- `feat(accounts): implement authentication flow with login, logout, and redirection`
- `feat(accounts): build role-based dashboards with strict URL authorization for Student and Custodian`
- `feat(accounts): create user profile view and edit functionality with avatar upload`
- `feat(ui): design modern, responsive UI templates for university laboratory theme`
- `docs: add comprehensive README with setup instructions, Supabase/PostgreSQL guide, and project documentation`
- `test: add unit tests for registration, authentication, role authorization, and profile management`
- `chore: add demo seeding management command and database migrations`
