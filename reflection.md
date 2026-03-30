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

The scheduler considers two constraints: the owner's daily time budget (minutes available) and each task's priority (1–5). Time is the hard constraint — no plan can exceed the budget. Priority is the soft ordering rule — when the budget can't fit everything, higher-priority tasks are always scheduled first.

I decided these two mattered most because they directly answer the pet owner's real problem: "I only have X minutes today — what's most important for my pet?" Category and frequency are metadata that inform the plan display and recurrence logic, but they don't affect which tasks get scheduled.

**b. Tradeoffs**

The conflict detection checks for overlapping time *windows* (start + duration) rather than exact start-time matches only. This means a 30-minute task starting at 08:00 and a 10-minute task starting at 08:15 will correctly be flagged as conflicting even though their start times differ.

The tradeoff is that this approach assumes tasks run back-to-back with no buffer time between them. In reality, an owner might need 5 minutes to move between tasks (e.g., walk → feeding). A more accurate model would subtract a transition buffer from the available time. For a v1 pet care planner, ignoring transition time is a reasonable simplification — the plan still fits within the day and the owner can adjust manually.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code (Anthropic) across every phase of this project. In Phase 1 I used it to generate the Mermaid UML diagram from a description of four classes. In Phase 2 it scaffolded the class skeletons and flagged two bottlenecks in the design (missing `_plan` cache and lack of `Task` validation). In Phases 4–5 it implemented the sorting, filtering, recurrence, and conflict detection algorithms and wrote the full 21-test suite.

The most effective prompts were concrete and scoped — e.g. "The divisor in update_score is wrong; it should use attempt_limit not difficulty rank. Fix it." Vague prompts like "improve the scheduler" produced over-engineered suggestions that I had to trim down.

**b. Judgment and verification**

In the first pass on `update_score` the AI introduced `DIFFICULTY_LEVEL = {"Easy": 1, "Normal": 2, "Hard": 3}` as the divisor, producing a 50-point deduction per wrong guess on Normal instead of the correct 16. I caught this by playing the game manually: after one wrong guess on Normal, winning gave 50 points instead of 84. I reported the discrepancy, explained the correct formula (`int(100 / attempt_limit)`), and the AI corrected it. The lesson: always verify numeric logic against a concrete expected value, not just syntactic correctness.

I also rejected the AI's first conflict detection implementation which compared only exact `start_time` strings. That would miss a case where task A starts at 08:00 (30 min) and task B starts at 08:15 — they overlap but have different start times. I replaced the equality check with a proper window-overlap check (`s2 < e1 and s1 < e2`).

---

## 4. Testing and Verification

**a. What you tested**

The 21-test suite covers: Task validation (priority/duration/frequency bounds), `mark_complete()` status change, recurrence (daily +1 day, weekly +7 days, one-off raises), Pet add/remove task count, Scheduler time-budget enforcement, priority ordering, start-time assignment, empty task list, `sort_by_time()` chronological order, `filter_tasks()` by pet and status, and conflict detection (clean plan → no conflicts; forced overlap → warning flagged).

These tests matter because the scheduler's correctness is invisible to the user — a wrong deduction or a missed conflict would look like a working app but silently produce bad plans. Automated tests are the only reliable way to catch regressions during refactoring.

**b. Confidence**

★★★★☆ — all 21 tests pass and cover both happy paths and key edge cases. I'd add tests for: two pets with tasks at the same time, an owner with zero available minutes, and the Streamlit UI layer (e.g. verifying the warning banner appears when conflicts exist) with more time.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the "CLI-first" workflow — building and verifying all logic in `main.py` before touching `app.py` meant that by the time the UI was wired up, there were zero logic bugs to debug through the Streamlit interface. The clean separation between `pawpal_system.py` (logic) and `app.py` (display) also made the Streamlit code straightforward to write.

**b. What you would improve**

I would add a `transition_buffer_minutes` field to `Owner` so the conflict detector accounts for travel time between tasks (e.g. walk ends at 08:30, next task can't start until 08:35). Right now back-to-back tasks never conflict, which is technically correct but unrealistic. I'd also persist the schedule to a JSON file so the owner's task history survives a page refresh.

**c. Key takeaway**

The most important thing I learned is that AI is a fast first-draft tool, not a final answer. Every significant piece of logic — the score divisor, the conflict detection algorithm, the `_plan` cache — needed human review to catch a subtle error or design gap. The AI wrote confident, syntactically correct code that was logically wrong in at least two places. The only way to trust it is to test against concrete expected values and reason about the edge cases yourself. Being the "lead architect" means you set the requirements, you verify the output, and you decide what to keep.
