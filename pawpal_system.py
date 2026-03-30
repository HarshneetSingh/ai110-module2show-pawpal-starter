from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Pet:
    name: str
    species: str

    def __str__(self) -> str:
        return f"{self.name} ({self.species})"


@dataclass
class Owner:
    name: str
    available_minutes_per_day: int

    def __str__(self) -> str:
        return f"{self.name} ({self.available_minutes_per_day} min/day available)"


@dataclass
class Task:
    name: str
    duration_minutes: int
    priority: int          # 1 = low, 5 = critical
    category: str          # e.g. "walk", "feeding", "medication", "grooming", "enrichment"

    def __repr__(self) -> str:
        return f"Task({self.name!r}, {self.duration_minutes}min, priority={self.priority})"


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the task list."""
        pass

    def remove_task(self, name: str) -> None:
        """Remove a task by name. Does nothing if the task is not found."""
        pass

    def generate_plan(self) -> List[Task]:
        """
        Return the list of tasks that fit within the owner's available time,
        sorted by priority (highest first). Lower-priority tasks are dropped
        when the time budget is exhausted.
        """
        pass

    def explain_plan(self) -> str:
        """
        Return a plain-English string explaining which tasks were scheduled
        and why any tasks were excluded.
        """
        pass
