from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    """A single pet care activity with duration, priority, recurrence, and completion state."""
    name: str
    duration_minutes: int
    priority: int           # 1 = low, 5 = critical
    category: str           # "walk", "feeding", "medication", "grooming", "enrichment"
    completed: bool = False
    frequency: str = "once" # "once", "daily", "weekly"
    due_date: date = field(default_factory=date.today)
    start_time: Optional[str] = None  # "HH:MM", assigned by Scheduler.generate_plan()

    def __post_init__(self) -> None:
        """Validate priority and duration at construction time."""
        if not (1 <= self.priority <= 5):
            raise ValueError(f"priority must be 1-5, got {self.priority}")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")
        if self.frequency not in ("once", "daily", "weekly"):
            raise ValueError(f"frequency must be once/daily/weekly, got {self.frequency}")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> "Task":
        """Return a new Task for the next recurrence (daily → +1 day, weekly → +7 days)."""
        if self.frequency == "once":
            raise ValueError(f"Task '{self.name}' is not recurring.")
        delta = timedelta(days=1 if self.frequency == "daily" else 7)
        return Task(
            name=self.name,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            due_date=self.due_date + delta,
        )

    def __repr__(self) -> str:
        """Return a readable string representation of the task."""
        status = "✓" if self.completed else "○"
        time_str = f" @ {self.start_time}" if self.start_time else ""
        return f"[{status}] {self.name}{time_str} ({self.duration_minutes}min, priority={self.priority})"


@dataclass
class Pet:
    """A pet with its own list of care tasks."""
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, name: str) -> None:
        """Remove a task by name; does nothing if not found."""
        self.tasks = [t for t in self.tasks if t.name != name]

    def __str__(self) -> str:
        """Return a readable string representation of the pet."""
        return f"{self.name} ({self.species})"


@dataclass
class Owner:
    """A pet owner with a daily time budget and one or more pets."""
    name: str
    available_minutes_per_day: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def all_tasks(self) -> List[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def __str__(self) -> str:
        """Return a readable string representation of the owner."""
        return f"{self.name} ({self.available_minutes_per_day} min/day, {len(self.pets)} pet(s))"


class Scheduler:
    """Generates a daily care plan for all of an owner's pets within a time budget."""

    _DAY_START = 8 * 60  # 08:00 in minutes from midnight

    def __init__(self, owner: Owner) -> None:
        """Initialise the scheduler with an owner (and their pets + tasks)."""
        self.owner = owner
        self._plan: Optional[List[Task]] = None
        self._excluded: Optional[List[Task]] = None

    # ------------------------------------------------------------------
    # Core plan generation
    # ------------------------------------------------------------------

    def generate_plan(self) -> List[Task]:
        """
        Fit tasks within the owner's daily time budget (greedy, highest priority first).
        Assigns sequential HH:MM start times beginning at 08:00.
        """
        all_tasks = sorted(self.owner.all_tasks(), key=lambda t: t.priority, reverse=True)
        budget = self.owner.available_minutes_per_day
        plan, excluded = [], []
        cursor = self._DAY_START  # minutes from midnight

        for task in all_tasks:
            if task.duration_minutes <= budget:
                task.start_time = f"{cursor // 60:02d}:{cursor % 60:02d}"
                cursor += task.duration_minutes
                budget -= task.duration_minutes
                plan.append(task)
            else:
                excluded.append(task)

        self._plan = plan
        self._excluded = excluded
        return plan

    def explain_plan(self) -> str:
        """Return a plain-English explanation of the generated plan."""
        if self._plan is None:
            return "No plan generated yet. Call generate_plan() first."

        lines = [
            f"Daily plan for {self.owner.name}'s pet(s) "
            f"({self.owner.available_minutes_per_day} min available):",
            "",
        ]

        if self._plan:
            lines.append("Scheduled:")
            for task in self._plan:
                lines.append(f"  • {task.start_time}  {task.name} — {task.duration_minutes} min "
                             f"(priority {task.priority}, {task.category})")
        else:
            lines.append("  No tasks fit within the available time.")

        if self._excluded:
            lines.append("")
            lines.append("Skipped (not enough time remaining):")
            for task in self._excluded:
                lines.append(f"  • {task.name} — {task.duration_minutes} min "
                             f"(priority {task.priority})")

        total = sum(t.duration_minutes for t in self._plan)
        lines.append(f"\nTotal scheduled time: {total} min")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_by_time(self) -> List[Task]:
        """Return the current plan sorted chronologically by start_time (HH:MM)."""
        if self._plan is None:
            return []
        return sorted(self._plan, key=lambda t: t.start_time or "")

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """
        Filter all owner tasks by pet name and/or completion status.
        Pass None to skip that filter.
        """
        results = []
        for pet in self.owner.pets:
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results

    # ------------------------------------------------------------------
    # Recurring tasks
    # ------------------------------------------------------------------

    def mark_task_complete(self, task_name: str) -> Optional[Task]:
        """
        Mark a task complete by name. If it is recurring, add the next
        occurrence to the same pet and return it. Returns None otherwise.
        """
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.name == task_name and not task.completed:
                    task.mark_complete()
                    if task.frequency != "once":
                        next_task = task.next_occurrence()
                        pet.add_task(next_task)
                        return next_task
                    return None
        return None

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> List[str]:
        """
        Detect overlapping tasks in the current plan.
        Returns a list of human-readable warning strings (empty = no conflicts).
        A conflict occurs when a task's start time falls within another task's window.
        """
        if not self._plan:
            return []

        warnings = []
        # Convert each task to (start_minutes, end_minutes, name)
        windows = []
        for t in self._plan:
            if t.start_time is None:
                continue
            h, m = map(int, t.start_time.split(":"))
            start = h * 60 + m
            windows.append((start, start + t.duration_minutes, t.name))

        for i in range(len(windows)):
            for j in range(i + 1, len(windows)):
                s1, e1, n1 = windows[i]
                s2, e2, n2 = windows[j]
                if s2 < e1 and s1 < e2:  # overlap check
                    warnings.append(
                        f"⚠️  Conflict: '{n1}' ({_fmt(s1)}–{_fmt(e1)}) "
                        f"overlaps '{n2}' ({_fmt(s2)}–{_fmt(e2)})"
                    )
        return warnings


def _fmt(minutes: int) -> str:
    """Convert minutes-from-midnight to HH:MM string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
