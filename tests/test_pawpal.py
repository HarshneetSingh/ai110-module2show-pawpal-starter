import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


# --- Fixtures ---

def make_task(**kwargs):
    defaults = dict(name="Walk", duration_minutes=20, priority=3, category="walk")
    defaults.update(kwargs)
    return Task(**defaults)


def make_scheduler(available_minutes=60):
    owner = Owner(name="Test Owner", available_minutes_per_day=available_minutes)
    pet = Pet(name="Rex", species="Dog")
    owner.add_pet(pet)
    return owner, pet, Scheduler(owner)


# --- Task tests ---

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


# --- Pet tests ---

def test_add_task_increases_count():
    """Adding a task to a pet should increase its task list length by 1."""
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.tasks) == 0
    pet.add_task(make_task(name="Walk"))
    assert len(pet.tasks) == 1
    pet.add_task(make_task(name="Feed"))
    assert len(pet.tasks) == 2


def test_remove_task_decreases_count():
    """Removing a task by name should reduce the pet's task list."""
    pet = Pet(name="Buddy", species="Dog")
    pet.add_task(make_task(name="Walk"))
    pet.add_task(make_task(name="Feed"))
    pet.remove_task("Walk")
    assert len(pet.tasks) == 1
    assert pet.tasks[0].name == "Feed"


# --- Scheduler tests ---

def test_generate_plan_respects_time_budget():
    """Tasks exceeding the budget should not appear in the plan."""
    owner, pet, scheduler = make_scheduler(available_minutes=30)
    pet.add_task(make_task(name="Long Walk", duration_minutes=25, priority=5))
    pet.add_task(make_task(name="Feed",      duration_minutes=10, priority=5))
    plan = scheduler.generate_plan()
    total = sum(t.duration_minutes for t in plan)
    assert total <= 30


def test_generate_plan_orders_by_priority():
    """Higher-priority tasks should appear first in the plan."""
    owner, pet, scheduler = make_scheduler(available_minutes=60)
    pet.add_task(make_task(name="Low",  duration_minutes=10, priority=1))
    pet.add_task(make_task(name="High", duration_minutes=10, priority=5))
    plan = scheduler.generate_plan()
    assert plan[0].name == "High"


def test_explain_plan_before_generate_returns_message():
    """explain_plan() without generate_plan() should return a helpful message."""
    _, _, scheduler = make_scheduler()
    msg = scheduler.explain_plan()
    assert "No plan generated yet" in msg
