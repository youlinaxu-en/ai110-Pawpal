# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
    Action added: Walks, Feeding, Meds, Enrichment, Grooming, Cleaning, Behavior Record, Health Check.

- Consider constraints (time available, priority, owner preferences)
    The system should detect conflicts with existing plans and reschedule flexible tasks when possible.
    If a task is not marked as Done before the due time, the system should keep it as Pending or mark it as Overdue and send a reminder to the owner.
    The system should consider each pet's species, breed, age, health conditions, medication schedule, and special care requirements.
    Each pet may have a profile page containing photos, descriptions, breed information, age, gender, sterilization status, personality, and public reactions from other users.
               
- Produce a daily plan and explain why it chose that plan
    Generate daily care plans based on owner availability, task priority, pet health needs, and owner preferences. This will help owner take control of their pets, especially when owner is not at home.

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```
=== Today's Schedule ===
07:00 AM - Biscuit: Give medication [critical]
06:30 PM - Mochi: Evening feeding [high]
08:00 AM - Biscuit: Morning walk [medium]
## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

### Sorting

- **`Scheduler.sort_by_time(tasks)`** — pure chronological sort (tie-broken by priority). Gives an agenda-style, time-ordered view of a task list.
- **`Scheduler.sort_by_priority(tasks)`** — priority first (CRITICAL → LOW), then time, then category urgency (medication/health checks outrank routine care at equal priority), then duration. This is what `Scheduler.get_tasks_for_day()` uses to build the daily plan.

### Filtering

- **`Scheduler.filter_tasks(owner, pet_id=None, pet_name=None, status=None)`** — filter an owner's tasks by pet (id or name), by completion status (`PENDING`/`DONE`/`OVERDUE`/`MISSED`), or any combination of both.
- **`Pet.get_tasks_by_status(status)`** — the same status filter scoped to a single pet.

### Conflict detection

Two intentionally separate layers:

- **`Pet.add_task(task)` / `Task.reschedule(new_time)`** (backed by `Pet.find_conflicts`) — a hard guard for one pet's own calendar. If a new or rescheduled task's time window overlaps another active task *for that same pet*, it raises `SchedulingConflictError` instead of silently double-booking.
- **`Scheduler.detect_conflicts(owner)`** — a lightweight, non-raising sweep across *all* of an owner's pets. Since one owner can't be in two places at once, this also catches two different pets' tasks landing at overlapping times, returning plain warning strings instead of an exception.

### Recurring tasks

- **`Task.occurs_on(day)`** — for a still-pending DAILY/WEEKLY task, reports whether it should appear on a given day without duplicating it into stored copies.
- **`Task.mark_done()`**, via **`Task._spawn_next_occurrence()`** — once a DAILY/WEEKLY task is completed, a new `Task` instance is automatically created for the next occurrence (`scheduled_time + timedelta(days=1)` or `+ timedelta(weeks=1)`). The completed task becomes a closed historical record and the new instance starts `PENDING`.
- **`Owner.next_task_id()`** — hands out a collision-free id for auto-spawned tasks (also used by the Streamlit UI for manually-added ones, so both paths share one id source).
- **`Owner.get_tasks_for_date(day)` / `Scheduler.get_tasks_for_day(owner, day)`** — combine both mechanisms: exact-date lookup for one-off tasks, plus `occurs_on` expansion for still-open recurring ones.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
