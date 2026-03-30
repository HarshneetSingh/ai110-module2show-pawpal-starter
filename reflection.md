# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

**Three core user actions:**
1. **Add a pet and owner info** — the user enters their name, their pet's name/species, and how many minutes per day they have available for pet care. This gives the scheduler its time constraint.
2. **Add and edit care tasks** — the user creates tasks (walk, feeding, medication, grooming, enrichment) each with a duration in minutes and a priority level (1 = low, 5 = critical). Tasks can be added or removed before generating the plan.
3. **Generate today's daily plan** — the scheduler takes all tasks, fits as many as possible within the owner's available time budget starting from highest priority, and displays the selected tasks along with a plain-English explanation of why each was included or excluded.

**Classes and responsibilities:**

- `Pet` — holds the pet's name and species. Pure data object, no scheduling logic.
- `Owner` — holds the owner's name and their daily available time in minutes. Acts as the time constraint source.
- `Task` — holds task name, duration, priority (1–5), and category. Comparable by priority so the scheduler can sort them.
- `Scheduler` — owns the owner, pet, and task list. Responsible for `add_task()`, `remove_task()`, `generate_plan()` (greedy priority sort + time-fit), and `explain_plan()` (plain-English reasoning for each included/excluded task).

**b. Design changes**

After reviewing the skeleton, two bottlenecks were identified and fixed:

1. **Added `_plan` cache to `Scheduler`** — the original design had `generate_plan()` and `explain_plan()` as independent methods, but `explain_plan()` needs to know which tasks were selected. Without a stored result, it would either have to recompute the plan (wasteful) or produce an explanation with no data. The fix was adding `self._plan: Optional[List[Task]] = None` so `generate_plan()` stores its result and `explain_plan()` reads from it.

2. **Added `__post_init__` validation to `Task`** — a priority of 0 or -1 would silently sort to the bottom and a zero-duration task would always be included. These are system-boundary inputs (from the UI), so validating them at construction time catches errors early rather than producing a subtly wrong plan.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

The conflict detection checks for overlapping time *windows* (start + duration) rather than exact start-time matches only. This means a 30-minute task starting at 08:00 and a 10-minute task starting at 08:15 will correctly be flagged as conflicting even though their start times differ.

The tradeoff is that this approach assumes tasks run back-to-back with no buffer time between them. In reality, an owner might need 5 minutes to move between tasks (e.g., walk → feeding). A more accurate model would subtract a transition buffer from the available time. For a v1 pet care planner, ignoring transition time is a reasonable simplification — the plan still fits within the day and the owner can adjust manually.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
