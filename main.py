from datetime import date, datetime

from pawpal_system import Owner, Pet, Task, TaskCategory, Priority, TaskStatus, Frequency, Scheduler


def at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(date.today(), datetime.min.time()).replace(hour=hour, minute=minute)


def print_task(task) -> None:
    time_str = task.scheduled_time.strftime("%I:%M %p")
    pet_name = task.pet.name if task.pet else "Unknown pet"
    print(f"{time_str} - {pet_name}: {task.description} [{task.priority.value}] ({task.status.value})")


def main():
    owner = Owner(1, "Youlina", "youlinaxu@gmail.com")

    dog = Pet(1, "Biscuit", "dog", "Golden Retriever", age=3)
    cat = Pet(2, "Mochi", "cat", "Tabby", age=2)
    owner.add_pet(dog)
    owner.add_pet(cat)

    # Added deliberately out of chronological order (noon, then 8am, then 7am, ...)
    # to prove sort_by_time actually sorts rather than echoing insertion order.
    cat.add_task(Task(4, "Litter box cleaning", TaskCategory.CLEANING, at(12, 0), Priority.LOW))
    dog.add_task(Task(1, "Morning walk", TaskCategory.WALK, at(8, 0), Priority.MEDIUM))
    dog.add_task(
        Task(2, "Give medication", TaskCategory.MEDICATION, at(7, 0), Priority.CRITICAL, frequency=Frequency.DAILY)
    )
    cat.add_task(Task(3, "Evening feeding", TaskCategory.FEEDING, at(18, 30), Priority.HIGH))
    dog.add_task(Task(5, "Enrichment play", TaskCategory.ENRICHMENT, at(9, 30), Priority.LOW))

    # Same time, different pets: add_task's hard conflict check only looks within one
    # pet's own tasks, so this succeeds even though the owner can't walk Biscuit and
    # groom Mochi at the exact same moment. This is what detect_conflicts is for.
    cat.add_task(Task(owner.next_task_id(), "Grooming session", TaskCategory.GROOMING, at(8, 0), Priority.MEDIUM))

    scheduler = Scheduler()

    print("=== Conflict Warnings ===")
    conflicts = scheduler.detect_conflicts(owner)
    if conflicts:
        for warning in conflicts:
            print(f"[!] {warning}")
    else:
        print("No conflicts detected.")

    print("\n=== Today's Schedule (by priority) ===")
    for task in scheduler.get_tasks_for_day(owner, date.today()):
        print_task(task)

    print("\n=== Sorted by Time ===")
    for task in scheduler.sort_by_time(owner.get_all_tasks()):
        print_task(task)

    scheduler.mark_task_done(owner, 2)  # Biscuit's medication is done for today; DAILY tasks auto-roll to tomorrow

    print("\n=== Filter: Pending Tasks Only ===")
    for task in scheduler.filter_tasks(owner, status=TaskStatus.PENDING):
        print_task(task)

    print("\n=== Filter: Biscuit's Tasks Only ===")
    for task in scheduler.filter_tasks(owner, pet_name="Biscuit"):
        print_task(task)

    print("\n=== Recurring Auto-Rollover: Biscuit's Medication Tasks ===")
    for task in scheduler.filter_tasks(owner, pet_id=dog.id):
        if task.category == TaskCategory.MEDICATION:
            due_str = task.scheduled_time.strftime("%m/%d %I:%M %p")
            print(f"  id={task.id} due={due_str} status={task.status.value}")


if __name__ == "__main__":
    main()
