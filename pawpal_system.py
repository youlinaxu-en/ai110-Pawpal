from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
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


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


class TaskStatus(Enum):
    PENDING = "pending"
    DONE = "done"
    OVERDUE = "overdue"
    MISSED = "missed"


_PRIORITY_ORDER = {
    Priority.CRITICAL: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
}

# Secondary tie-break when two tasks share priority and time: health-critical
# categories should still surface before routine ones.
_CATEGORY_URGENCY = {
    TaskCategory.MEDICATION: 0,
    TaskCategory.HEALTH_CHECK: 1,
    TaskCategory.FEEDING: 2,
    TaskCategory.WALK: 3,
    TaskCategory.CLEANING: 4,
    TaskCategory.GROOMING: 5,
    TaskCategory.ENRICHMENT: 6,
    TaskCategory.BEHAVIOR_RECORD: 7,
}


class SchedulingConflictError(Exception):
    """Raised when a task would overlap another active task for the same pet."""


# ---------------------------------------------------------------------------
# Core classes
# ---------------------------------------------------------------------------

@dataclass
class Task:
    id: int
    description: str
    category: TaskCategory
    scheduled_time: datetime
    priority: Priority
    frequency: Frequency = Frequency.ONCE
    duration_minutes: int = 15
    status: TaskStatus = TaskStatus.PENDING
    pet: "Pet | None" = None

    def mark_done(self) -> None:
        already_done = self.status == TaskStatus.DONE
        self.status = TaskStatus.DONE
        if not already_done:
            self._spawn_next_occurrence()

    def mark_pending(self) -> None:
        self.status = TaskStatus.PENDING

    def _spawn_next_occurrence(self) -> "Task | None":
        """For DAILY/WEEKLY tasks, create the next occurrence as a new Task once this one is done."""
        next_time = self.next_occurrence()
        if next_time is None or self.pet is None or self.pet.owner is None:
            return None
        next_task = Task(
            id=self.pet.owner.next_task_id(),
            description=self.description,
            category=self.category,
            scheduled_time=next_time,
            priority=self.priority,
            frequency=self.frequency,
            duration_minutes=self.duration_minutes,
        )
        try:
            self.pet.add_task(next_task)
        except SchedulingConflictError:
            return None  # something already occupies the next slot; skip auto-rollover
        return next_task

    def is_overdue(self, now: datetime) -> bool:
        return self.status != TaskStatus.DONE and now > self.scheduled_time

    def refresh_status(self, now: datetime) -> TaskStatus:
        if self.is_overdue(now):
            self.status = TaskStatus.OVERDUE
        return self.status

    def reschedule(self, new_time: datetime) -> None:
        if self.pet is not None:
            conflicts = self.pet.find_conflicts(self, at=new_time)
            if conflicts:
                other = conflicts[0]
                raise SchedulingConflictError(
                    f"Rescheduling '{self.description}' to {new_time:%I:%M %p} would "
                    f"conflict with '{other.description}' at {other.scheduled_time:%I:%M %p}"
                )
        old_date = self.scheduled_time.date()
        self.scheduled_time = new_time
        if self.status != TaskStatus.DONE:
            self.status = TaskStatus.PENDING
        if self.pet is not None and self.pet.owner is not None:
            self.pet.owner._reindex_task(self, old_date)

    def next_occurrence(self) -> "datetime | None":
        if self.frequency == Frequency.DAILY:
            return self.scheduled_time + timedelta(days=1)
        if self.frequency == Frequency.WEEKLY:
            return self.scheduled_time + timedelta(weeks=1)
        return None

    def occurs_on(self, day: date) -> bool:
        """Whether this task (materialized on demand, not as a stored copy) falls on `day`.

        A completed recurring task only occurs on its own day: its next occurrence
        is a separate Task (see `_spawn_next_occurrence`), so this one shouldn't
        keep showing up on later days too.
        """
        start = self.scheduled_time.date()
        if self.frequency == Frequency.ONCE or self.status == TaskStatus.DONE:
            return day == start
        if day < start:
            return False
        if self.frequency == Frequency.DAILY:
            return True
        if self.frequency == Frequency.WEEKLY:
            return (day - start).days % 7 == 0
        return False


@dataclass
class Pet:
    id: int
    name: str
    species: str
    breed: str = ""
    age: int = 0
    gender: str = ""
    health_notes: str = ""
    tasks: list = field(default_factory=list)
    owner: "Owner | None" = None

    def add_task(self, task: Task) -> None:
        conflicts = self.find_conflicts(task)
        if conflicts:
            other = conflicts[0]
            raise SchedulingConflictError(
                f"Task '{task.description}' at {task.scheduled_time:%I:%M %p} conflicts "
                f"with '{other.description}' at {other.scheduled_time:%I:%M %p}"
            )
        task.pet = self
        self.tasks.append(task)
        if self.owner is not None:
            self.owner._register_task(task)

    def remove_task(self, task_id: int) -> None:
        removed = next((t for t in self.tasks if t.id == task_id), None)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        if removed is not None and self.owner is not None:
            self.owner._unregister_task(removed)

    def get_tasks(self) -> list:
        return list(self.tasks)

    def get_tasks_by_status(self, status: TaskStatus) -> list:
        return [t for t in self.tasks if t.status == status]

    def find_conflicts(self, task: Task, at: "datetime | None" = None) -> list:
        """Active tasks on this pet whose time window overlaps `task` (at an optional hypothetical time)."""
        start = at if at is not None else task.scheduled_time
        end = start + timedelta(minutes=task.duration_minutes)
        conflicts = []
        for existing in self.tasks:
            if existing.id == task.id or existing.status in (TaskStatus.DONE, TaskStatus.MISSED):
                continue
            existing_end = existing.scheduled_time + timedelta(minutes=existing.duration_minutes)
            if start < existing_end and existing.scheduled_time < end:
                conflicts.append(existing)
        return conflicts


@dataclass
class Owner:
    id: int
    name: str
    email: str
    pets: list = field(default_factory=list)

    # Derived caches (not identity fields): kept in sync by Pet/Task via
    # back-references so repeated lookups don't need to rescan every task.
    _task_index: dict = field(default_factory=dict, repr=False, compare=False)
    _tasks_by_date: dict = field(default_factory=dict, repr=False, compare=False)
    _recurring_tasks: list = field(default_factory=list, repr=False, compare=False)
    _pending_heap: list = field(default_factory=list, repr=False, compare=False)
    _overdue_cache: list = field(default_factory=list, repr=False, compare=False)

    def add_pet(self, pet: Pet) -> None:
        pet.owner = self
        self.pets.append(pet)
        for task in pet.tasks:
            self._register_task(task)

    def remove_pet(self, pet_id: int) -> None:
        pet = self.get_pet(pet_id)
        if pet is not None:
            for task in list(pet.tasks):
                self._unregister_task(task)
            pet.owner = None
        self.pets = [p for p in self.pets if p.id != pet_id]

    def get_pet(self, pet_id: int) -> "Pet | None":
        return next((p for p in self.pets if p.id == pet_id), None)

    def get_pet_by_name(self, name: str) -> "Pet | None":
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> list:
        return [task for pet in self.pets for task in pet.tasks]

    def get_task_by_id(self, task_id: int) -> "Task | None":
        return self._task_index.get(task_id)

    def next_task_id(self) -> int:
        """Smallest id guaranteed unused by any task currently registered on this owner."""
        return max(self._task_index.keys(), default=0) + 1

    def get_tasks_for_date(self, day: date) -> list:
        exact = list(self._tasks_by_date.get(day, []))
        recurring = [t for t in self._recurring_tasks if t.occurs_on(day)]
        return exact + recurring

    def pull_newly_overdue(self, now: datetime) -> list:
        """Pop every pending task whose time has passed, transitioning it to OVERDUE.

        Uses a lazily-cleaned min-heap keyed by scheduled_time so this only
        touches tasks that are actually due, not the whole task history.
        """
        due_now = []
        while self._pending_heap and self._pending_heap[0][0] <= now:
            due_now.append(heapq.heappop(self._pending_heap))

        newly_overdue = []
        for _, task_id, task in due_now:
            if self._task_index.get(task_id) is not task or task.status != TaskStatus.PENDING:
                continue  # stale entry: removed, completed, or superseded by a reschedule
            if task.is_overdue(now):
                task.refresh_status(now)
                self._overdue_cache.append(task)
                newly_overdue.append(task)
            else:
                heapq.heappush(self._pending_heap, (task.scheduled_time, task.id, task))
        return newly_overdue

    def get_cached_overdue(self) -> list:
        self._overdue_cache = [t for t in self._overdue_cache if t.status == TaskStatus.OVERDUE]
        return list(self._overdue_cache)

    def _register_task(self, task: Task) -> None:
        self._task_index[task.id] = task
        if task.frequency == Frequency.ONCE:
            self._tasks_by_date.setdefault(task.scheduled_time.date(), []).append(task)
        else:
            self._recurring_tasks.append(task)
        if task.status == TaskStatus.PENDING:
            heapq.heappush(self._pending_heap, (task.scheduled_time, task.id, task))

    def _unregister_task(self, task: Task) -> None:
        self._task_index.pop(task.id, None)
        if task.frequency == Frequency.ONCE:
            bucket = self._tasks_by_date.get(task.scheduled_time.date())
            if bucket is not None:
                self._tasks_by_date[task.scheduled_time.date()] = [t for t in bucket if t.id != task.id]
        else:
            self._recurring_tasks = [t for t in self._recurring_tasks if t.id != task.id]
        self._overdue_cache = [t for t in self._overdue_cache if t.id != task.id]
        # any stale entry left in _pending_heap is discarded lazily on pop

    def _reindex_task(self, task: Task, old_date: date) -> None:
        if task.frequency == Frequency.ONCE and old_date != task.scheduled_time.date():
            bucket = self._tasks_by_date.get(old_date)
            if bucket is not None:
                self._tasks_by_date[old_date] = [t for t in bucket if t.id != task.id]
            self._tasks_by_date.setdefault(task.scheduled_time.date(), []).append(task)
        if task.status == TaskStatus.PENDING:
            heapq.heappush(self._pending_heap, (task.scheduled_time, task.id, task))


class Scheduler:
    """The "brain": retrieves, organizes, and manages tasks across pets."""

    def get_all_tasks(self, owner: Owner) -> list:
        return owner.get_all_tasks()

    def organize_by_pet(self, owner: Owner) -> dict:
        return {pet.id: pet.get_tasks() for pet in owner.pets}

    def detect_conflicts(self, owner: Owner) -> list:
        """Lightweight pairwise scan for any two active tasks (same pet or different pets)
        whose time windows overlap. Returns warning strings instead of raising, so a caller
        can log/display them without the schedule build breaking.
        """
        warnings = []
        active = [t for t in owner.get_all_tasks() if t.status not in (TaskStatus.DONE, TaskStatus.MISSED)]
        for i, task in enumerate(active):
            task_end = task.scheduled_time + timedelta(minutes=task.duration_minutes)
            for other in active[i + 1:]:
                other_end = other.scheduled_time + timedelta(minutes=other.duration_minutes)
                if task.scheduled_time < other_end and other.scheduled_time < task_end:
                    pet_a = task.pet.name if task.pet else "Unknown pet"
                    pet_b = other.pet.name if other.pet else "Unknown pet"
                    warnings.append(
                        f"Conflict: '{task.description}' ({pet_a}) at {task.scheduled_time:%I:%M %p} overlaps "
                        f"with '{other.description}' ({pet_b}) at {other.scheduled_time:%I:%M %p}"
                    )
        return warnings

    def filter_tasks(
        self,
        owner: Owner,
        pet_id: "int | None" = None,
        pet_name: "str | None" = None,
        status: "TaskStatus | None" = None,
    ) -> list:
        if pet_id is not None:
            pet = owner.get_pet(pet_id)
            tasks = pet.get_tasks() if pet is not None else []
        elif pet_name is not None:
            pet = owner.get_pet_by_name(pet_name)
            tasks = pet.get_tasks() if pet is not None else []
        else:
            tasks = owner.get_all_tasks()
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def sort_by_time(self, tasks: list) -> list:
        return sorted(tasks, key=lambda t: (t.scheduled_time, _PRIORITY_ORDER[t.priority]))

    def sort_by_priority(self, tasks: list) -> list:
        return sorted(
            tasks,
            key=lambda t: (
                _PRIORITY_ORDER[t.priority],
                t.scheduled_time,
                _CATEGORY_URGENCY.get(t.category, 99),
                t.duration_minutes,
            ),
        )

    def get_tasks_for_day(self, owner: Owner, day: date) -> list:
        return self.sort_by_priority(owner.get_tasks_for_date(day))

    def refresh_all_statuses(self, owner: Owner, now: datetime) -> None:
        owner.pull_newly_overdue(now)

    def get_overdue_tasks(self, owner: Owner, now: datetime) -> list:
        owner.pull_newly_overdue(now)
        return owner.get_cached_overdue()

    def mark_task_done(self, owner: Owner, task_id: int) -> "Task | None":
        task = owner.get_task_by_id(task_id)
        if task is not None:
            task.mark_done()
        return task


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class SchedulingTest:
    def test_high_priority_task_sorted_first(self):
        pass

    def test_overdue_task_detected(self):
        pass

    def test_tasks_grouped_by_pet(self):
        pass

    def test_mark_task_done_updates_status(self):
        pass

    def test_daily_plan_filters_by_date(self):
        pass
