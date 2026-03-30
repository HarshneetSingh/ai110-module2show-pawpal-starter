from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    # --- Setup owner ---
    owner = Owner(name="Harshneet", available_minutes_per_day=90)

    # --- Setup pets ---
    dog = Pet(name="Buddy", species="Dog")
    cat = Pet(name="Luna", species="Cat")

    # --- Add tasks to dog ---
    dog.add_task(Task("Morning Walk",    duration_minutes=30, priority=5, category="walk"))
    dog.add_task(Task("Evening Walk",    duration_minutes=30, priority=4, category="walk"))
    dog.add_task(Task("Flea Medication", duration_minutes=5,  priority=5, category="medication"))

    # --- Add tasks to cat ---
    cat.add_task(Task("Feeding",         duration_minutes=10, priority=5, category="feeding"))
    cat.add_task(Task("Litter Cleaning", duration_minutes=10, priority=4, category="grooming"))
    cat.add_task(Task("Playtime",        duration_minutes=20, priority=2, category="enrichment"))

    # --- Register pets with owner ---
    owner.add_pet(dog)
    owner.add_pet(cat)

    # --- Generate and display plan ---
    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    print("=" * 50)
    print(scheduler.explain_plan())
    print("=" * 50)


if __name__ == "__main__":
    main()
