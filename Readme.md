# CareCore

**Care facility management platform built with Django.**

CareCore is a centralized management system for residential care facilities, bringing resident care, staff management, medications, incidents, appointments, compliance, and facility operations into one application.

---

## Features

### Resident Management

* Resident profiles
* Resident contacts
* Admission and status tracking
* Care-level information
* Mobility, nutrition, communication, and cognitive support information
* Resident 360 view

### Care Management

* Care plans
* Assessments
* Cognitive and behavioural support
* Care tasks
* Task assignment and status tracking
* Care task priorities and due dates

### Medication Management

* Medication records
* Dosage and frequency tracking
* Medication administration records
* Administration history
* Administration status tracking:

  * Administered
  * Missed
  * Refused
  * Withheld

### Incident Management

* Incident reporting
* Incident categories
* Severity levels
* Investigation notes
* Corrective actions
* Incident resolution tracking

### Appointments

* Resident appointments
* Appointment types
* Staff assignment
* Providers and locations
* Appointment status
* Notes

### Staff Management

* Staff profiles
* Employee IDs
* Facility and ward assignments
* Resident-staff assignments
* Staff workspace

### Facility Management

* Facilities
* Wards
* Rooms
* Room capacity and occupancy
* Facility management structure

### Compliance

* Compliance dashboard
* Permission-controlled access
* Audit-oriented data structure
* Role-based access control

---

## Roles

CareCore currently supports the following user roles:

* **Administrator**
* **Manager**
* **Registered Nurse (RN)**
* **Enrolled Nurse (EN)**
* **Personal Care Worker**

Access is controlled using Django authentication and model permissions.

---

## Architecture

CareCore is structured as a modular Django application.

```text
CareCore
│
├── accounts
│   └── Authentication, users, roles, audit logs
│
├── residents
│   └── Residents and contacts
│
├── staff
│   └── Staff and resident assignments
│
├── care
│   └── Care plans, assessments, support and tasks
│
├── medications
│   └── Medications and administration
│
├── incidents
│   └── Incident reporting and resolution
│
├── appointments
│   └── Resident appointments
│
├── facility
│   └── Facilities, wards and rooms
│
└── compliance
    └── Compliance management
```

---

## Technology Stack

* **Python**
* **Django**
* **SQLite** for development
* **HTML**
* **CSS**
* **JavaScript**
* **Django Templates**
* **Chart.js**

---

## Project Structure

```text
care-core/
│
├── accounts/
├── appointments/
├── care/
├── compliance/
├── facility/
├── incidents/
├── medications/
├── residents/
├── staff/
│
├── templates/
├── static/
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/axitpatel1310/care-core.git
cd care-core
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Demo Data

CareCore includes a demo-data management command for development and testing.

```bash
python manage.py seed_demo
```

The command creates sample:

* Users
* Facility
* Ward
* Rooms
* Staff
* Residents
* Contacts
* Staff assignments
* Care plans
* Assessments
* Care tasks
* Medications
* Medication administrations
* Incidents
* Appointments

Demo credentials are intended **only for local development** and must not be used in production.

---

## Permissions

CareCore uses Django's permission system to control access to resources.

Examples include:

```text
resident.view_resident
resident.add_resident
resident.change_resident
resident.delete_resident

care.view_careplan
care.add_careplan
care.change_careplan

medications.view_medication
medications.add_medication
medications.change_medication

incidents.view_incident
incidents.add_incident
incidents.change_incident

appointments.view_appointment
appointments.add_appointment
appointments.change_appointment
```

Views are protected using authentication and permission decorators where appropriate.

---

## Development

Run Django's system checks:

```bash
python manage.py check
```

View migration status:

```bash
python manage.py showmigrations
```

Create migrations after model changes:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Current Status

CareCore's core application functionality is implemented, including:

* Authentication
* Role-based permissions
* Resident management
* Resident 360
* Staff management
* Facility management
* Care management
* Medication management
* Medication administration
* Incident management
* Appointment management
* Compliance dashboard
* Demo data generation

The current phase is **end-to-end testing, security validation, and production hardening**.

---

## Security

CareCore handles sensitive care-related information and should be treated as a security-sensitive application.

Before production deployment:

* Disable development settings
* Use environment variables for secrets
* Configure a production database
* Configure HTTPS
* Review all permissions
* Configure secure cookies
* Configure CSRF protection
* Configure allowed hosts
* Remove demo credentials
* Configure proper logging and monitoring
* Perform a complete security review

---

## License

This project currently does not specify an open-source license.
