from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    """A single pet care activity with duration, priority, and completion state."""
    name: str
    duration_minutes: int
    priority: int          # 1 = low, 5 = critical
    category: str          # e.g. "walk", "feeding", "medication", "grooming", "enrichment"
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate priority and duration at construction time."""
        if not (1 <= self.priority <= 5):
            raise ValueError(f"priority must be 1-5, got {self.priority}")
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def __repr__(self) -> str:
        """Return a readable string representation of the task."""
        status = "✓" if self.completed else "○"
        return f"[{status}] {self.name} ({self.duration_minutes}min, priority={self.priority})"


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

    def __init__(self, owner: Owner) -> None:
        """Initialise the scheduler with an owner (and their pets + tasks)."""
        self.owner = owner
        self._plan: Optional[List[Task]] = None
        self._excluded: Optional[List[Task]] = None

    def generate_plan(self) -> List[Task]:
        """
        Return the tasks that fit within the owner's daily time budget,
        sorted by priority (highest first). Excess tasks are dropped.
        """
        all_tasks = sorted(self.owner.all_tasks(), key=lambda t: t.priority, reverse=True)
        budget = self.owner.available_minutes_per_day
        plan, excluded = [], []
        for task in all_tasks:
            if task.duration_minutes <= budget:
                plan.append(task)
                budget -= task.duration_minutes
            else:
                excluded.append(task)
        self._plan = plan
        self._excluded = excluded
        return plan

    def explain_plan(self) -> str:
        """
        Return a plain-English explanation of the generated plan.
        Must call generate_plan() first.
        """
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
                lines.append(f"  • {task.name} — {task.duration_minutes} min "
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
