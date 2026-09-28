# Socio Sarthi CRM — Project Status & User Guide

## Part 1: Project Status — What's Been Built

### Summary

This is a Django + PostgreSQL rebuild of the original Node/React prototype CRM. It manages leads for an education-consulting business with three tiers of access: a single **Super Admin** (Divyanshu) who owns the whole system, one **Client Manager** per client business, and multiple **Telecallers** under each client.

The core data-isolation rule the whole system is built around:

- **Divyanshu (Super Admin)** sees every client, every user, every lead, in full detail.
- **A Client Manager** sees everything for their own client only — every telecaller's leads in full detail — and nothing from any other client.
- **A Telecaller** sees their own leads in full detail, and only aggregate *counts* (not details) of other telecallers' leads under the same client.

### Tech Stack

- **Backend + Frontend**: Django 5.2 (LTS), server-rendered templates — no separate API/React split.
- **Database**: PostgreSQL 17, accessed via Django's built-in ORM.
- **Frontend interactivity**: Bootstrap 5 (styling), HTMX (live search/filter, dashboard auto-refresh, follow-up tabs — no full page reloads), Alpine.js (the call-timer stopwatch).
- **Auth**: Django's built-in session-based login (email + password, not username).
- **Tests**: pytest-django + factory_boy — 21 tests covering phone-number normalization, lead-ID generation, cross-role/cross-client data-visibility rules, commission calculation, and audit-log immutability. All passing.

### What's implemented

| Area | Status |
|---|---|
| Client management (add/deactivate) | ✅ Super Admin only |
| Staff management (add/disable/reset password) | ✅ Super Admin manages Client Managers; Client Managers manage their own Telecallers |
| Lead creation, search, filtering by status/temperature/date | ✅ |
| Lead detail page: status/temperature updates, reassignment, call log, follow-ups, admission, timeline | ✅ |
| Follow-up queue (Overdue / Due Today / Upcoming) | ✅ |
| Admissions & commission calculation | ✅ (commission auto-calculated only when an admission is Confirmed) |
| Role-specific dashboards with live KPI cards | ✅ |
| Immutable audit log of every significant action | ✅ |
| Bulk CSV lead import | ✅ Super Admin only, with duplicate/invalid-row reporting |
| WhatsApp integration | 🔜 Placeholder page + webhook endpoint only — real message handling is future work, as originally scoped |

### Known limitations (by design, for now)

- CSV import caps at 5,000 rows per file (a hard limit, configurable in settings).
- WhatsApp integration is a stub — the page and webhook route exist so the architecture won't need to change later, but it doesn't yet create leads from messages.
- No email/SMS notifications yet for follow-up reminders.
- Deactivating a client or staff member is a **soft delete** (marks inactive, keeps all history) — there is no hard-delete button, intentionally, so historical leads/admissions/commission records are never destroyed.

---

## Test Login Credentials (local development only)

These accounts were created while building and testing this project on `http://127.0.0.1:8000/`. Use them now to log in and explore each role yourself. **Before this goes anywhere beyond your own machine, change every one of these passwords** (via *Change Password* once logged in, or *Staff → Reset Password* as an admin) — these are throwaway test values, not production credentials.

| Role | Name | Email (login ID) | Password | Client |
|---|---|---|---|---|
| Super Admin | Divyanshu | `divyanshu@sociosarthi.com` | `Divyanshu#2026` | — (sees all) |
| Client Manager | Ajay | `ajay.manager@nursingcollege.example` | `NurseMgr#2026` | Nursing College |
| Telecaller | Priya | `priya@nursingcollege.example` | `PriyaTC#2026` | Nursing College |

**What you'll see immediately after logging in as each one:**

- **Divyanshu** → Super Admin Dashboard: cross-client totals, a "Leads by Client" table (Nursing College, IT College), the full audit log, and nav links to *Clients*, *Staff*, *Campaigns*, *Import CSV*, *WhatsApp*, and *Audit Log* that no one else can see.
- **Ajay** → Nursing College's dashboard: that client's KPI totals only, a leaderboard of leads per telecaller (currently just Priya), admissions/commission summary, and follow-up queue. His nav has *Staff*, *Campaigns*, and *Audit Log*, but no *Clients*, *Import CSV*, or *WhatsApp* — and if he tries to visit `/clients/` directly, he gets a 403 Forbidden, not the page.
- **Priya** → "My Dashboard": her own lead KPIs (2 leads currently — Rahul Sharma and Sneha Patil), a "Team Totals" box showing only counts for herself (no other telecallers exist yet under Nursing College), and her own follow-up queue. Her nav is the shortest — just *Dashboard*, *Leads*, *Follow-ups*, *Admissions* — no staff/client/audit management at all.

Note that `IT College` (the second client, code `ITC`) currently has no manager or telecallers created yet — if you want to see full cross-client isolation in action, ask to have a manager/telecaller added there too, then compare what Ajay can and can't see relative to that client.

**Troubleshooting "wrong credential" on login**: this almost always means the browser's autofill silently pre-filled a saved value into the Email field, and typing appended to it instead of replacing it (e.g. submitting `test@gmail.comdivyanshu@sociosarthi.com` instead of the real address). Before typing, click the field and press **Ctrl+A** then **Delete** to clear it fully, or just use an Incognito window, which has no saved autofill data.

---

## Part 2: User Guide

### How the system is organized

Three roles, three different experiences after login:

```
Divyanshu (Super Admin)
   └── manages: Clients, all Staff, sees everything
        │
        ├── Client A (e.g. "Nursing College")
        │     └── Client Manager (e.g. Ajay)
        │           └── manages: that client's Telecallers, sees all of that client's leads
        │                 ├── Telecaller 1 (e.g. Priya) — sees only her own leads in detail
        │                 └── Telecaller 2             — sees only his own leads in detail
        │
        └── Client B (e.g. "IT College")
              └── (completely separate — Client A's manager/telecallers cannot see any of this)
```

### Logging in

Go to the app's login page and sign in with your **email and password** (not a username). There's a single login form for everyone — what you see next depends on your role automatically.

If you don't have login details, ask:
- A new **Client Manager** account is created by Divyanshu (Super Admin).
- A new **Telecaller** account is created by your Client Manager.

---

### Guide for Divyanshu (Super Admin)

You have full visibility and a few controls nobody else has.

**Your dashboard** shows totals across every client, a breakdown of leads per client, and a live feed of recent activity across the whole system.

**Managing clients** (nav → *Clients*):
- **Add Client**: give it a name, a short code (e.g. `NURSE` — this becomes part of every lead ID for that client, like `SS-NURSE-2026-000001`), and the default commission paid per confirmed admission.
- **Deactivate**: turns the client off without deleting any of its data or history.

**Managing staff** (nav → *Staff*):
- From here you can add **Client Managers** for any client, or (less commonly) add a Telecaller directly.
- **Reset Password**: sets a new password for anyone and immediately logs them out of any other device they were signed into.
- **Disable**: blocks login without deleting their historical leads/calls/admissions.

**Bulk importing leads** (nav → *Import CSV*):
- Only you can do this. Pick the client the leads belong to, upload a `.csv` file (up to 5,000 rows).
- The importer is flexible about column headers (`Phone`, `Mobile`, `Mobile Number` all work the same).
- After import, you'll see how many leads were created, how many were skipped as duplicates (matched against existing phone/WhatsApp/alternate numbers for that client), and how many had invalid phone numbers. A full history is kept under *Import CSV → View full import history*.

**WhatsApp** (nav → *WhatsApp*): a placeholder inbox for now — this is reserved for a future integration, not yet functional for auto-creating leads.

**Audit Log** (nav → *Audit Log*): a permanent, uneditable record of every important action anyone in the system has taken — who created which client, who reset whose password, every lead status change, every CSV import. Nothing here can ever be edited or deleted, by anyone, including you.

---

### Guide for a Client Manager

You manage one client's operation end-to-end. You do **not** see anything belonging to other clients.

**Your dashboard** shows your client's total leads broken down by status, a leaderboard of leads per telecaller, your admissions/commission summary, and your follow-up queue.

**Managing your staff** (nav → *Staff*):
- **Add Staff**: creates a new Telecaller under your client only (you can't create Client Managers or assign staff to other clients).
- **Reset Password** / **Disable**: same as above, scoped to your own telecallers only.

**Leads** (nav → *Leads*): you see every lead for your client, from every telecaller, in full detail — not just your own. You can:
- Search/filter by name, phone, lead ID, email, status, temperature, or time period (today/this week/this month).
- Open any lead to view/update its status, **reassign it to a different telecaller**, log calls, schedule follow-ups, and record admissions.

**Campaigns** (nav → *Campaigns*): add campaigns for your client; a campaign can optionally override the client's default commission rate.

**Admissions** (nav → *Admissions*): a full list of every admission recorded for your client, with status and commission.

**Follow-ups** (nav → *Follow-ups*): the queue of all upcoming/overdue follow-ups across your whole team, bucketed into Overdue / Due Today / Upcoming.

**Audit Log**: shows the history of actions taken by you and your telecallers.

---

### Guide for a Telecaller (the everyday user)

This is what most people using the CRM day-to-day will see.

**Your dashboard** shows:
- **My Leads** — your own totals by status (New, Follow Up, Counselling, Admissions, Lost, etc.)
- **Team Totals** — how many leads your teammates have, as numbers only. You cannot open or see details of another telecaller's individual leads — that's by design.
- **My Follow-up Queue** — your own Overdue / Due Today / Upcoming follow-ups.

**Adding a lead**: click **+ Add Lead** from your dashboard or the Leads page. Fill in name, phone (and optionally WhatsApp/alternate numbers, email), pick a temperature (Hot/Warm/Cold/Unqualified), and where the lead came from. It's automatically assigned to you and given a permanent lead ID like `SS-NURSE-2026-000002`.

**Working a lead** — open any of your leads to get a detail page with five tabs:
- **Overview**: change status/temperature; update as the lead progresses through the pipeline (New → Contact Attempted → Connected → Follow Up → Counselling → Visit Scheduled → Visited → Admission Pending/Confirmed, or a closed-out status like Not Interested/Wrong Number/Lost).
- **Calls**: log a call — pick an outcome, optionally use the **Start Call Timer** button to time the call automatically (or just type remarks and log it directly), then **Log Call**.
- **Follow-ups**: schedule your next follow-up (a call, WhatsApp message, visit, counselling session, etc.) for a specific date/time. Mark a follow-up complete once it's done — it'll then appear correctly bucketed on the Follow-up Queue page.
- **Admission**: once a lead is ready, record their admission details (admission number, amount, status). Commission is calculated automatically once the status is set to **Confirmed**.
- **Timeline**: a read-only, chronological record of everything that's happened on this lead — calls, follow-ups, admissions.

**Viewing your leads by time period**: on the Leads page, use the "All time / Today / This week / This month" filter alongside the search box and status/temperature filters — results update live as you type or change a filter, no page reload needed.

**Follow-up Queue** (nav → *Follow-ups*): your personal queue, split into three tabs — **Overdue**, **Due Today**, **Upcoming**. Mark any follow-up complete directly from here.

**Admissions** (nav → *Admissions*): a list of admissions tied to your own leads.

**Changing your password**: nav → *Change Password* (top right), any time.

---

### Quick reference: who can do what

| Action | Super Admin | Client Manager | Telecaller |
|---|:---:|:---:|:---:|
| See every client | ✅ | ❌ | ❌ |
| Add/deactivate clients | ✅ | ❌ | ❌ |
| Add Client Managers | ✅ | ❌ | ❌ |
| Add Telecallers | ✅ | ✅ (own client only) | ❌ |
| Reset anyone's password | ✅ | ✅ (own telecallers only) | ❌ |
| See all leads for a client | ✅ (all clients) | ✅ (own client) | ❌ |
| See own leads in detail | ✅ | ✅ | ✅ |
| See other telecallers' lead counts (not detail) | ✅ | ✅ | ✅ |
| Reassign a lead to another telecaller | ✅ | ✅ | ❌ |
| Add a lead | ✅ | ✅ | ✅ |
| Bulk import leads via CSV | ✅ | ❌ | ❌ |
| View audit log | ✅ (everything) | ✅ (own client) | ❌ |

---

### Getting started checklist for a brand-new client

1. Divyanshu logs in and adds the new client under *Clients*, with its code and commission rate.
2. Divyanshu adds that client's Manager under *Staff* (role: Client Manager).
3. The new Manager logs in with the credentials Divyanshu gave them, and immediately changes their password.
4. The Manager adds their Telecallers under *Staff*.
5. Each Telecaller logs in, changes their password, and starts adding/working leads.
