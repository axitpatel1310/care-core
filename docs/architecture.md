# CareCore architecture

This document describes CareCore's data model, module boundaries and the main
design decisions. The diagrams are written in [Mermaid](https://mermaid.js.org/)
and render directly on GitHub.

## Entity–relationship diagram

```mermaid
erDiagram
    USER ||--o| STAFF_MEMBER : "has profile"
    USER ||--o{ AUDIT_LOG : performs
    USER ||--o{ FACILITY : manages

    FACILITY ||--o{ WARD : contains
    WARD ||--o{ ROOM : contains
    FACILITY ||--o{ STAFF_MEMBER : employs
    ROOM ||--o{ RESIDENT : "is occupied by"
    FACILITY ||--o{ RESIDENT : "is home to"
    FACILITY ||--o{ INCIDENT : "happens at"
    USER ||--o{ LOGIN_ATTEMPT : "signs in"

    RESIDENT ||--o{ RESIDENT_CONTACT : has
    RESIDENT ||--o{ RESIDENT_STAFF_ASSIGNMENT : "cared for by"
    STAFF_MEMBER ||--o{ RESIDENT_STAFF_ASSIGNMENT : "assigned to"

    RESIDENT ||--o{ CARE_PLAN : has
    RESIDENT ||--o{ ASSESSMENT : has
    RESIDENT ||--o| COGNITIVE_BEHAVIOURAL_SUPPORT : has
    RESIDENT ||--o{ CARE_TASK : has
    STAFF_MEMBER ||--o{ CARE_TASK : "assigned / completes"

    RESIDENT ||--o{ MEDICATION : "is prescribed"
    MEDICATION ||--o{ MEDICATION_DOSE_TIME : "scheduled at"
    MEDICATION ||--o{ MEDICATION_ADMINISTRATION : "recorded in"
    STAFF_MEMBER ||--o{ MEDICATION_ADMINISTRATION : administers

    RESIDENT ||--o{ OBSERVATION : has
    OBSERVATION }o--o| CARE_TASK : "escalates to"

    RESIDENT ||--o{ INCIDENT : "involved in"
    RESIDENT ||--o{ APPOINTMENT : attends

    AUDIT ||--o{ AUDIT_CONTROL : contains
    AUDIT_CONTROL ||--o{ CORRECTIVE_ACTION : raises
    INCIDENT ||--o{ CORRECTIVE_ACTION : raises
    STAFF_MEMBER ||--o{ RISK : owns
    USER ||--o{ COMPLIANCE_DOCUMENT : owns

    RESIDENT {
        string first_name
        string last_name
        date date_of_birth
        string status "active, hospital, leave, discharged, deceased"
        string care_level "standard, high, complex"
    }
    ROOM {
        string room_number
        int capacity
        int occupied "derived from residents"
    }
    MEDICATION {
        string name
        string dose
        string route
        bool as_required "PRN"
        date start_date
        date end_date
    }
    MEDICATION_DOSE_TIME {
        time time
    }
    MEDICATION_ADMINISTRATION {
        datetime administered_at
        datetime scheduled_for "null for PRN"
        string status "administered, refused, missed, withheld"
    }
    OBSERVATION {
        int respiratory_rate
        int spo2
        bool on_oxygen
        int systolic_bp
        int pulse
        string consciousness "ACVPU"
        decimal temperature
        int news2_score "calculated"
        string risk_level "calculated"
        datetime amended_at
        string amendment_reason
    }
    RISK {
        int likelihood "1-5"
        int impact "1-5"
        string severity "derived from L x I"
    }
    LOGIN_ATTEMPT {
        string email
        string ip_address
        bool successful
        datetime created_at
    }
    AUDIT_LOG {
        string action
        string module
        json changes "field: [old, new]"
        string ip_address
    }
```

## Modules

| App | Responsibility |
| --- | --- |
| `accounts` | Users, roles → permission groups, email login, sign-in throttling, approval of new accounts, password reset, audit trail, facility scoping |
| `facility` | Facilities, wards, rooms; derived occupancy |
| `residents` | Residents and contacts |
| `staff` | Staff profiles, resident assignments, personal workspace |
| `care` | Care plans, assessments, behavioural support, care tasks |
| `medications` | Prescriptions, dose schedules, medication round, MAR |
| `observations` | Vital signs, NEWS2 scoring, escalation, amendments |
| `incidents` | Incident reporting and investigation |
| `appointments` | Resident appointments |
| `compliance` | Risk register, policies, audits, corrective actions |
| `insights` | Alert engine, resident risk score, analytics, handover, CSV export |

## Key flows

### Deterioration → escalation

```mermaid
sequenceDiagram
    actor Carer
    participant View as observation_create
    participant Model as Observation.save()
    participant NEWS2 as news2.calculate_news2
    participant Service as escalate_if_required
    participant Alerts as alerts_for (bell)

    Carer->>View: submit vital signs
    View->>Model: save
    Model->>NEWS2: score parameters
    NEWS2-->>Model: total, risk band, red score
    View->>Service: medium/high risk?
    Service-->>View: urgent CareTask for assigned nurse
    Note over Alerts: Next page load: "Deterioration" and,<br/>if no repeat set within the interval,<br/>"repeat observations overdue"
```

### Medication round

1. Each `Medication` has zero or more `MedicationDoseTime`s (none for PRN).
2. `medications.schedule.scheduled_doses()` expands them into dated doses and
   matches each to the `MedicationAdministration` whose `scheduled_for` equals it.
3. An unmatched dose is *upcoming*, *due* (±60 minutes) or *overdue*.
4. The round page, the 7-day MAR grid and the "Dose overdue" alert all use the
   same function, so they always agree.

## Security model

* **Authentication:** email + password; 5 failed attempts per email since its
  last successful sign-in (or 20 per IP) within 15 minutes locks sign-in.
  Attempts are stored in the `LoginAttempt` table, so the limit is shared by
  every server process. New accounts are
  inactive until an administrator approves them and picks the role.
* **Authorisation:** each role maps to a Django permission group
  (`accounts/roles.py`); views check model permissions.
* **Data segregation:** every resident and incident stores its facility (taken
  from the room or resident automatically, chosen explicitly otherwise).
  `accounts/scoping.py` limits every resident-linked query to the facilities
  the user works in or manages; records without a facility are visible to
  administrators only. Lookups outside scope
  return 404 so record existence is not leaked; form dropdowns are filtered so
  submitting another facility's id fails validation.
* **Audit:** create/update/delete on clinical and governance models, sign-ins,
  sign-outs, failed sign-ins, approvals and exports are logged with user, IP and
  field-level changes. The audit log is read-only, including in Django admin.
* **Files:** uploaded policy documents are not publicly served; they are
  streamed by a view that checks the user's permission.
* **Transport/cookies:** with `CARECORE_DEBUG=false`, HTTPS redirect, HSTS and
  secure cookies are on (`manage.py check --deploy` runs in CI).

## Known limitations

* The resident risk score weights are design choices, not a validated clinical
  instrument.
* SQLite suits a single facility server. Multiple application servers would
  need a client–server database.
* Rooms that were already over capacity before the capacity check existed are
  not changed automatically (that needs a decision about who moves). They raise
  a "Room over capacity" alert, are badged on the facility page, and are listed
  by `python manage.py occupancy_report`, which also lists residents without a
  facility.
