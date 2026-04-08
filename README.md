# Freelance Job Platform (Django + PostgreSQL)

Full-stack coursework project for an open-source software development class.
This repository now includes:
- Web UI (Django templates) for end users
- REST API for integration and testing
- PostgreSQL persistence

## Core features

- Role-based users: `student`, `employer`, `admin`
- Auth flows: register, login, logout
- Job management: create, edit, delete, browse, filter
  - Multi-category job posting
  - Work mode: remote/onsite/hybrid
  - City/address for onsite jobs
  - Salary type: negotiable/range/fixed
  - Employment type and experience level
- Application flow: apply to job, view applications, update status
  - CV upload per application
  - Optional profile default CV
  - Portfolio URL + expected salary
- Role-aware dashboard (student/employer/admin)
- Django admin management panel
- Token-based API auth (DRF authtoken)

## Tech stack

- Django 6
- Django REST Framework 3
- PostgreSQL
- Psycopg 3

## Project setup

1. Create virtual environment and install packages:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure PostgreSQL environment variables (see `.env.example`):

```env
DB_NAME=freelance_platform
DB_USER=freelance_user
DB_PASSWORD=123
DB_HOST=localhost
DB_PORT=5432
```

3. Apply migrations:

```powershell
.\venv\Scripts\python manage.py migrate
```

4. Create admin account:

```powershell
.\venv\Scripts\python manage.py createsuperuser
```

5. Optional: seed demo data quickly:

```powershell
.\venv\Scripts\python manage.py seed_demo
```

Demo accounts created by seed command:
- `employer_demo / 123456Aa!`
- `student_demo / 123456Aa!`

6. Start server:

```powershell
.\venv\Scripts\python manage.py runserver
```

## Main web routes

- `/` Job marketplace home
- `/accounts/register/` Register
- `/accounts/login/` Login
- `/dashboard/` Dashboard by role
- `/admin-center/` Web admin center (for admin/staff)
- `/jobs/create/` Post a new job
- `/jobs/<id>/` Job details + apply
- `/applications/` Application management
- `/admin/` Django admin

## API routes

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `GET /api/auth/me/`
- `GET /api/jobs/`
- `GET /api/jobs/categories/`
- `POST /api/jobs/` (employer/admin)
- `GET /api/jobs/{id}/`
- `PUT/PATCH/DELETE /api/jobs/{id}/` (owner/admin)
- `POST /api/jobs/{id}/apply/` (student)
- `GET /api/applications/my/`
- `PATCH /api/applications/{id}/status/` (employer/admin)
