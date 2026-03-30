import pytest
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# --- Helpers ---

def make_task(**kwargs):
    defaults = dict(name="Walk", duration_minutes=20, priority=3, category="walk")
    defaults.update(kwargs)
    return Task(**defaults)


def make_scheduler(available_minutes=120):
    owner = Owner(name="Test Owner", available_minutes_per_day=available_minutes)
    pet = Pet(name="Rex", species="Dog")
    owner.add_pet(pet)
    return owner, pet, Scheduler(owner)


# ==========================================================================
# Task tests
# ==========================================================================

def test_mark_complete_changes_status():
    """mark_complete() should flip completed from False to True."""
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_task_invalid_priority_raises():
    """Task with priority outside 1-5 should raise ValueError."""
    with pytest.raises(ValueError):
        make_task(priority=0)
    with pytest.raises(ValueError):
        make_task(priority=6)


def test_task_invalid_duration_raises():
    """Task with non-positive duration should raise ValueError."""
    with pytest.raises(ValueError):
        make_task(duration_minutes=0)


def test_task_invalid_frequency_raises():
    """Task with unrecognised frequency should raise ValueError."""
    with pytest.raises(ValueError):
        make_task(frequency="monthly")


# ==========================================================================
# Recurrence tests
# ==========================================================================

def test_next_occurrence_daily_advances_one_day():
    """next_occurrence() on a daily task should have due_date = today + 1."""
    task = make_task(frequency="daily")
    next_task = task.next_occurrence()
    assert next_task.due_date == task.due_date + timedelta(days=1)
    assert next_task.completed is False


def test_next_occurrence_weekly_advances_seven_days():
    """next_occurrence() on a weekly task should have due_date = today + 7."""
    task = make_task(frequency="weekly")
    next_task = task.next_occurrence()
    assert next_task.due_date == task.due_date + timedelta(days=7)


def test_next_occurrence_raises_for_once():
    """Calling next_occurrence() on a one-off task should raise ValueError."""
    task = make_task(frequency="once")
    with pytest.raises(ValueError):
        task.next_occurrence()


def test_mark_task_complete_creates_recurrence():
    """Completing a daily task via Scheduler should add the next occurrence to the pet."""
    owner, pet, scheduler = make_scheduler()
    pet.add_task(make_task(name="Feed", frequency="daily"))
    initial_count = len(pet.tasks)
    scheduler.mark_task_complete("Feed")
    assert len(pet.tasks) == initial_count + 1
    assert pet.tasks[-1].due_date == date.today() + timedelta(days=1)


def test_mark_task_complete_once_does_not_recur():
    """Completing a one-off task should NOT add a new task."""
    owner, pet, scheduler = make_scheduler()
    pet.add_task(make_task(name="Grooming", frequency="once"))
    initial_count = len(pet.tasks)
    scheduler.mark_task_complete("Grooming")
    assert len(pet.tasks) == initial_count


# ==========================================================================
# Pet tests
# ==========================================================================

def test_add_task_increases_count():
    """Adding a task to a pet should increase its task list length."""
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.tasks) == 0
    pet.add_task(make_task(name="Walk"))
    assert len(pet.tasks) == 1


def test_remove_task_decreases_count():
    """Removing a task by name should reduce the pet's task list."""
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(make_task(name="Walk"))
    pet.add_task(make_task(name="Feed"))
    pet.remove_task("Walk")
    assert len(pet.tasks) == 1
    assert pet.tasks[0].name == "Feed"


# ==========================================================================
# Scheduler — generate_plan tests
# ==========================================================================

def test_generate_plan_respects_time_budget():
    """Total scheduled time must not exceed the owner's daily budget."""
    owner, pet, scheduler = make_scheduler(available_minutes=30)
    pet.add_task(make_task(name="Long Walk", duration_minutes=25, priority=5))
    pet.add_task(make_task(name="Feed",      duration_minutes=10, priority=5))
    plan = scheduler.generate_plan()
    assert sum(t.duration_minutes for t in plan) <= 30


def test_generate_plan_orders_by_priority():
    """Higher-priority tasks should be scheduled before lower-priority ones."""
    owner, pet, scheduler = make_scheduler()
    pet.add_task(make_task(name="Low",  duration_minutes=10, priority=1))
    pet.add_task(make_task(name="High", duration_minutes=10, priority=5))
    plan = scheduler.generate_plan()
    assert plan[0].name == "High"


def test_generate_plan_assigns_start_times():
    """Every scheduled task should have a start_time set after generate_plan()."""
    owner, pet, scheduler = make_scheduler()
    pet.add_task(make_task(name="Walk", duration_minutes=20, priority=3))
    plan = scheduler.generate_plan()
    assert all(t.start_time is not None for t in plan)


def test_generate_plan_empty_tasks():
    """A pet with no tasks should produce an empty plan."""
    owner, pet, scheduler = make_scheduler()
    assert scheduler.generate_plan() == []


# ==========================================================================
# Scheduler — sort_by_time tests
# ==========================================================================

def test_sort_by_time_is_chronological():
    """sort_by_time() should return tasks ordered from earliest to latest."""
    owner, pet, scheduler = make_scheduler()
    pet.add_task(make_task(name="C", duration_minutes=10, priority=1))
    pet.add_task(make_task(name="B", duration_minutes=10, priority=3))
    pet.add_task(make_task(name="A", duration_minutes=10, priority=5))
    scheduler.generate_plan()
    sorted_tasks = scheduler.sort_by_time()
    times = [t.start_time for t in sorted_tasks]
    assert times == sorted(times)


# ==========================================================================
# Scheduler — filter_tasks tests
# ==========================================================================

def test_filter_by_pet_name():
    """filter_tasks(pet_name=) should only return tasks belonging to that pet."""
    owner = Owner(name="Owner", available_minutes_per_day=120)
    dog = Pet(name="Buddy", species="Dog")
    cat = Pet(name="Luna",  species="Cat")
    dog.add_task(make_task(name="Walk"))
    cat.add_task(make_task(name="Feed"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    scheduler = Scheduler(owner)
    result = scheduler.filter_tasks(pet_name="Buddy")
    assert all(t.name == "Walk" for t in result)
    assert len(result) == 1


def test_filter_by_completion_status():
    """filter_tasks(completed=True) should only return completed tasks."""
    owner, pet, scheduler = make_scheduler()
    t1 = make_task(name="Walk")
    t2 = make_task(name="Feed")
    t2.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    done = scheduler.filter_tasks(completed=True)
    assert len(done) == 1
    assert done[0].name == "Feed"


# ==========================================================================
# Scheduler — conflict detection tests
# ==========================================================================

def test_no_conflicts_in_normal_plan():
    """A freshly generated sequential plan should have zero conflicts."""
    owner, pet, scheduler = make_scheduler()
    pet.add_task(make_task(name="Walk", duration_minutes=20, priority=5))
    pet.add_task(make_task(name="Feed", duration_minutes=10, priority=4))
    scheduler.generate_plan()
    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_flags_overlap():
    """Manually overlapping two start_times should produce a conflict warning."""
    owner, pet, scheduler = make_scheduler()
    pet.add_task(make_task(name="Walk", duration_minutes=30, priority=5))
    pet.add_task(make_task(name="Feed", duration_minutes=10, priority=4))
    scheduler.generate_plan()
    # Force overlap
    scheduler._plan[1].start_time = scheduler._plan[0].start_time
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "Conflict" in conflicts[0]


def test_explain_plan_before_generate_returns_message():
    """explain_plan() without generate_plan() should return a helpful message."""
    _, _, scheduler = make_scheduler()
    assert "No plan generated yet" in scheduler.explain_plan()
