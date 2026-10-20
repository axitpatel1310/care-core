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

* Medication records with **scheduled dose times** (suggested automatically from the frequency, e.g. "Twice daily" → 08:00, 20:00) and PRN (as-required) medicines
* **Medication round** page: every dose due today grouped by round, showing given / refused / missed / withheld / due now / overdue, with one-click recording against the scheduled dose
* **7-day MAR chart** per resident (printable), including PRN doses given
* "Dose overdue" alerts when a scheduled dose is more than an hour late with nothing recorded
* A reason is required when a dose is refused, missed or withheld; a scheduled dose cannot be recorded twice
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
* Room capacity, with occupancy **calculated from residents** (residents in hospital or on leave keep their bed); a resident cannot be placed in a full room
* Rooms already over capacity raise an alert and are badged; `python manage.py occupancy_report` lists them along with any residents missing a facility
* Facility management structure

### Clinical Observations & NEWS2 Early Warning

* Vital signs: respiration rate, SpO₂ (scale 1 and 2), supplemental oxygen, blood pressure, pulse, ACVPU consciousness, temperature, blood glucose and pain score
* Automatic **NEWS2** (National Early Warning Score 2, Royal College of Physicians, 2017) calculation with per-parameter breakdown
* Clinical risk band (low, low–medium, medium, high) and the matching clinical response and monitoring frequency
* Live score preview while the form is being filled in
* Amendments require a reason; who amended and why is shown on the record, and the original values stay in the audit trail
* Automatic escalation: medium/high scores create an urgent care task assigned to the resident's nurse or primary carer
* Per-resident observation chart with NEWS2 and vital-sign trend graphs

### Clinical Safety Insights

* **Alert Centre**: a rule-based engine that raises critical / warning / information alerts for deteriorating residents, overdue repeat observations, unresolved serious incidents, overdue or urgent care tasks, missed/refused doses, medication courses ending, overdue care plan and assessment reviews, unconfirmed appointments and governance deadlines. Alerts are filtered by the user's permissions and shown as a badge on the notification bell
* **Resident Risk Register**: an explainable 0–100 composite risk score per resident (see *Risk scoring* below), with every contributing factor shown
* **Shift Handover Report**: printable per-resident summary of the last 8/12/24 hours, filterable by ward
* **Analytics & Reports**: quality indicators (falls per 1,000 occupied bed days, medication adherence, on-time task completion, mean incident resolution time, NEWS2 escalations) with charts and CSV exports (exports are audited and protected against spreadsheet formula injection)

### Compliance & Governance

* Compliance dashboard with a 5×5 risk heat map
* **Risk register**: severity rated automatically from likelihood × impact (low 1–4, medium 5–9, high 10–14, extreme 15–25)
* **Policies & documents** with versioning, file upload and review-date tracking
* **Audits** with individual controls and a computed compliance score (passed = 1, partial = ½, failed = 0)
* **Corrective actions** raised directly from failed audit controls or incidents, with completion/verification timestamps and overdue tracking

### Security & Audit Trail

* Role-based access control: each role is mapped to a Django permission group automatically (groups are provisioned after `migrate` and kept in sync when a user's role changes)
* Sign-in with email address (case-insensitive)
* **Account approval:** self-registration only creates a request; an administrator approves it and assigns the role
* **Sign-in throttling:** repeated failed attempts lock sign-in for 15 minutes; attempts are stored in the database, so the limit holds across all server processes
* Password reset by email and password change
* Safe post-login redirects (no open redirect), and sign-out only via POST
* **Facility data segregation:** every resident and incident belongs to a facility, and staff only see residents (and their records, incidents, alerts and reports) for the facility they work in or manage; administrators see everything
* Uploaded policy documents are served only to users with permission, never from a public URL
* **Automatic audit trail** of every create/update/delete on clinical and governance records, with the acting user, IP address and a field-level before/after diff; sign-ins, sign-outs, failed sign-ins and data exports are also logged
* Filterable, paginated audit log for administrators
* Environment-based configuration with secure cookie/HSTS settings when `CARECORE_DEBUG` is off

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
├── compliance
│   └── Risk register, policies, audits, corrective actions
│
├── observations
│   └── Vital signs, NEWS2 scoring (news2.py) and escalation (services.py)
│
└── insights
    └── Alert engine (alerts.py), risk scoring (risk.py),
        quality indicators (analytics.py), handover and CSV exports
```

See [`docs/architecture.md`](docs/architecture.md) for the ER diagram, request flows, security model and known limitations.

### Design notes

* **Pure scoring logic.** `observations/news2.py` and the risk-band functions contain no database access, so the clinical rules are unit tested against the published NEWS2 boundary values.
* **Rule registry.** Each alert rule in `insights/alerts.py` is a small generator registered with the permission required to see it; adding a new alert is one decorated function.
* **Explainability.** The risk score is the sum of named factors (each capped), and the UI always shows the factors, not just the number.
* **Audit by signals.** `accounts/audit_trail.py` connects `pre_save`/`post_save`/`post_delete` handlers for every tracked model; `accounts.middleware.CurrentRequestMiddleware` exposes the acting user and IP to those handlers.

### Risk scoring

| Factor | Points |
| --- | --- |
| Latest NEWS2 in the last 72 h | high 30 · medium 20 · low–medium 12 · low but > 0: 4 |
| Falls in the last 90 days | 10 each, max 25 |
| Other high/critical incidents in the last 30 days | 10 each, max 15 |
| Doses missed/refused/withheld in the last 14 days | up to 20 (proportional) |
| Overdue care tasks | 3 each, max 10 |
| Care level | complex 10 · high 5 |
| No active care plan, or plan review overdue | 5 |
| Overdue assessment reviews | 5 each, max 10 |

Bands: **low** 0–29, **moderate** 30–59, **high** 60–100.

---

## Technology Stack

* **Python**
* **Django**
* **SQLite** for development
* **HTML**
* **CSS**
* **JavaScript**
* **Django Templates**
* **Chart.js 4.4.1** (vendored in `static/vendor`, so charts work offline)

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
├── observations/
├── insights/
├── docs/
│   └── architecture.md
│
├── manage.py
├── requirements.txt
└── Readme.md
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

### 4. Configure (optional)

Development works with no configuration. For any shared or production deployment set:

| Variable | Purpose |
| --- | --- |
| `CARECORE_DEBUG` | `false` in production (enables secure cookies, HSTS, SSL redirect) |
| `CARECORE_SECRET_KEY` | Required when debug is off |
| `CARECORE_ALLOWED_HOSTS` | Comma-separated host names |
| `CARECORE_CSRF_TRUSTED_ORIGINS` | Comma-separated origins, e.g. `https://care.example.org` |
| `CARECORE_TIME_ZONE` | e.g. `Europe/London` (default `UTC`) |
| `CARECORE_DB_PATH` | Location of the SQLite file (default `db.sqlite3` in the project) |
| `CARECORE_MEDIA_ROOT` | Where uploaded documents are stored |
| `CARECORE_EMAIL_BACKEND`, `CARECORE_EMAIL_HOST`, `CARECORE_EMAIL_PORT`, `CARECORE_EMAIL_USER`, `CARECORE_EMAIL_PASSWORD`, `CARECORE_FROM_EMAIL` | SMTP for password-reset emails. In development, emails are printed to the console |

### 5. Run migrations

```bash
python manage.py migrate
```

Role permission groups are created automatically. To re-apply them after changing `accounts/roles.py`, run `python manage.py setup_roles`.

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the development server

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
* Medication administrations (12 weeks of history)
* Incidents (a year of history for the analytics charts)
* Appointments
* Observations, including a deteriorating resident who triggers NEWS2 escalation
* Compliance documents, risks, an audit with controls and corrective actions

Demo accounts (password `CareCoreDemo123!`): `admin@carecore.demo`, `manager@carecore.demo`, `rn@carecore.demo`, `en@carecore.demo`, `careworker@carecore.demo`.

New accounts created through **Request access** must be approved by an administrator under *User Management* before they can sign in.

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

## Testing

```bash
python manage.py test
```

The suite (123 tests) covers NEWS2 boundary values for every parameter, risk bands and escalation, the composite risk score, alert rules and their permission filtering, quality-indicator calculations, CSV export safety, the risk matrix, audit compliance scoring, corrective-action lifecycle, role/permission group sync, email login, the audit trail, medication scheduling and the MAR, derived occupancy and room capacity, facility data segregation, login throttling, open-redirect protection, account approval, password reset, observation amendments, form submissions in every module, a check that risk scoring uses a constant number of queries, and a smoke test that renders every page as every role against the demo data.

Continuous integration (`.github/workflows/ci.yml`) runs the system checks, a migrations check, `check --deploy` with production settings, and the full test suite on every push.

---

## Docker

CareCore ships with a production-style image (gunicorn, static files via WhiteNoise, SQLite and uploads on a `/data` volume). Migrations run automatically on start.

```bash
CARECORE_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" docker compose up --build
docker compose exec web python manage.py createsuperuser   # or: seed_demo
```

Then open http://localhost:8000/. The compose file assumes no TLS proxy in front; behind HTTPS, drop `CARECORE_SSL_REDIRECT` / `CARECORE_SECURE_COOKIES` from it.

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
* Compliance & governance registers
* Clinical observations with NEWS2 early warning and escalation
* Alert centre, resident risk register, shift handover and analytics
* Medication dose scheduling, medication round and MAR chart
* Facility data segregation, account approval, sign-in throttling and password reset
* Docker image and CI pipeline
* Automatic audit trail
* Demo data generation
* Automated test suite

---

## Security

CareCore handles sensitive care-related information and should be treated as a security-sensitive application.

Before production deployment:

* Set `CARECORE_DEBUG=false` and a strong `CARECORE_SECRET_KEY`
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
