from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    # --- Setup ---
    owner = Owner(name="Harshneet", available_minutes_per_day=90)

    dog = Pet(name="Buddy", species="Dog")
    cat = Pet(name="Luna", species="Cat")

    dog.add_task(Task("Morning Walk",    30, priority=5, category="walk",       frequency="daily"))
    dog.add_task(Task("Evening Walk",    30, priority=4, category="walk",       frequency="daily"))
    dog.add_task(Task("Flea Medication",  5, priority=5, category="medication", frequency="weekly"))

    cat.add_task(Task("Feeding",         10, priority=5, category="feeding",    frequency="daily"))
    cat.add_task(Task("Litter Cleaning", 10, priority=4, category="grooming",   frequency="daily"))
    cat.add_task(Task("Playtime",        20, priority=2, category="enrichment", frequency="once"))

    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner)

    # --- Generate plan ---
    print("=" * 55)
    scheduler.generate_plan()
    print(scheduler.explain_plan())

    # --- Sort by time ---
    print("\n--- Sorted by start time ---")
    for task in scheduler.sort_by_time():
        print(f"  {task.start_time}  {task.name}")

    # --- Filter: incomplete tasks for Buddy ---
    print("\n--- Buddy's incomplete tasks ---")
    for task in scheduler.filter_tasks(pet_name="Buddy", completed=False):
        print(f"  {task}")

    # --- Recurring task: complete Morning Walk → auto-schedule tomorrow ---
    print("\n--- Completing 'Morning Walk' (daily recurring) ---")
    next_task = scheduler.mark_task_complete("Morning Walk")
    if next_task:
        print(f"  Next occurrence created: {next_task.name} due {next_task.due_date}")

    # --- Conflict detection: force two tasks to share a start time ---
    scheduler.generate_plan()
    plan = scheduler._plan
    if len(plan) >= 2:
        plan[1].start_time = plan[0].start_time  # force overlap
    conflicts = scheduler.detect_conflicts()
    print("\n--- Conflict detection (forced overlap for demo) ---")
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts detected.")

    print("=" * 55)


if __name__ == "__main__":
    main()
