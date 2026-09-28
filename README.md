# Socio Sarthi CRM (Django)

A Django + PostgreSQL rebuild of the socio-sarthi-crm prototype. See
`C:\Users\91825\.claude\plans\lets-just-plan-the-cosmic-moonbeam.md` for the
full architecture plan.

## Stack

- Django 5.2 (LTS) + PostgreSQL, Django ORM only
- Server-rendered templates (Bootstrap 5) + HTMX for dynamic bits, Alpine.js for pure client-side state
- Django session auth
- pytest-django + factory_boy for tests

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # then fill in real values
```

Create the database (adjust credentials to match your `.env`):

```sql
CREATE DATABASE socio_sarthi_crm;
```

Then:

```bash
python manage.py migrate
python manage.py createsuperuser   # creates the first Super Admin
python manage.py runserver
```

## Apps

| App | Purpose |
|---|---|
| `core` | Shared base models, role permission helpers, view mixins, nav context processor |
| `accounts` | Custom `User` model (role + client), staff CRUD, auth |
| `clients` | `Client` model, Super-Admin client management |
| `campaigns` | `Campaign` model |
| `leads` | `Lead`, `FollowUp`, lead list/detail/status/reassign/follow-up queue |
| `calls` | `Call` log |
| `admissions` | `Admission` + commission calculation |
| `dashboard` | Role-aware dashboards + KPI aggregation |
| `audit` | Immutable `AuditLog` |
| `csv_import` | Super-Admin bulk lead import |
| `whatsapp` | Reserved stub for future WhatsApp integration |

## Tests

```bash
pytest
```

Pure-logic tests (`apps/leads/tests/test_utils.py`) run without a database.
Everything else needs the Postgres test database (created automatically by
pytest-django when you run `pytest`, using the same DB user as `DATABASE_URL`).
