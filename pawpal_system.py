from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskCategory(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    CLEANING = "cleaning"
    BEHAVIOR_RECORD = "behavior_record"
    HEALTH_CHECK = "health_check"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    PENDING = "pending"
    DONE = "done"
    OVERDUE = "overdue"
    MISSED = "missed"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    id:int
    name: str
    email: str
    preferences: list = field(default_factory=list)
    pets: list = field(default_factory=list)
    availability_slots: list = field(default_factory=list)
    daily_plans: list = field(default_factory=list)

    def create_profile(self):
        pass

    def edit_profile(self):
        pass

    def add_pet(self, pet):
        pass

    def update_preferences(self, preferences):
        pass


@dataclass
class Pet:
    id: int
    name: str
    species: str
    breed: str
    age: int
    gender: str
    health_notes: str
    care_tasks: list = field(default_factory=list)

    def create_profile(self):
        pass

    def edit_profile(self):
        pass


@dataclass
class CareTask:
    id: int
    title: str
    category: TaskCategory
    duration_minutes: int
    priority: Priority
    preferred_time_window: str
    status: TaskStatus
    reminders: list = field(default_factory=list)

    def update_duration(self, minutes):
        pass

    def update_priority(self, priority):
        pass

    def mark_done(self):
        pass

    def mark_pending(self):
        pass


@dataclass
class AvailabilitySlot:
    id: int
    start_time: datetime
    end_time: datetime
    available: bool
    note: str

    def update_availability(self, start_time, end_time, available):
        pass


@dataclass
class ScheduledTask:
    id: int
    care_task: CareTask
    scheduled_start: datetime
    scheduled_end: datetime
    reason: str

    def display_summary(self):
        pass


@dataclass
class DailyPlan:
    id: int
    plan_date: date
    scheduled_tasks: list = field(default_factory=list)
    explanation: str = ""

    def get_tasks(self):
        pass

    def show_plan(self):
        pass

    def show_explanation(self):
        pass


@dataclass
class Reminder:
    id: int
    reminder_time: datetime
    message: str
    sent: bool = False

    def send(self):
        pass

    def reschedule(self, new_time):
        pass


# ---------------------------------------------------------------------------
# Service classes
# ---------------------------------------------------------------------------

class TaskService:
    def add_task(self, pet, task):
        pass

    def edit_task(self, task_id, updated_task):
        pass

    def delete_task(self, task_id):
        pass

    def get_tasks_by_pet(self, pet):
        pass


class CarePlanService:
    def generate_plan(self, owner, pets, tasks, availability):
        pass

    def detect_conflict(self, task, scheduled_tasks):
        pass

    def sort_by_priority(self, tasks):
        pass

    def fit_tasks_into_availability(self, tasks, availability):
        pass

    def explain_plan(self, plan):
        pass


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class SchedulingTest:
    def test_high_priority_task_scheduled_first(self):
        pass

    def test_task_fits_within_availability(self):
        pass

    def test_conflict_detection(self):
        pass

    def test_unavailable_time_rejected(self):
        pass

    def test_plan_explanation_generated(self):
        pass
