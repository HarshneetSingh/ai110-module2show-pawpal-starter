import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("Your smart daily pet care planner.")

# ---------------------------------------------------------------------------
# Sidebar — Owner & Pet setup
# ---------------------------------------------------------------------------
st.sidebar.header("Owner & Pet Setup")
owner_name = st.sidebar.text_input("Your name", value="Harshneet")
available_minutes = st.sidebar.number_input(
    "Minutes available today", min_value=10, max_value=480, value=90, step=5
)

st.sidebar.divider()
st.sidebar.subheader("Add a Pet")
pet_name_input = st.sidebar.text_input("Pet name", value="Buddy")
pet_species = st.sidebar.selectbox("Species", ["Dog", "Cat", "Rabbit", "Bird", "Other"])

if st.sidebar.button("Add Pet"):
    if "pets" not in st.session_state:
        st.session_state.pets = []
    names = [p["name"] for p in st.session_state.pets]
    if pet_name_input and pet_name_input not in names:
        st.session_state.pets.append({"name": pet_name_input, "species": pet_species})
        st.sidebar.success(f"Added {pet_name_input}!")
    elif pet_name_input in names:
        st.sidebar.warning("A pet with that name already exists.")

# ---------------------------------------------------------------------------
# Initialise session state
# ---------------------------------------------------------------------------
if "pets" not in st.session_state:
    st.session_state.pets = []
if "task_rows" not in st.session_state:
    st.session_state.task_rows = []

# ---------------------------------------------------------------------------
# Main area — tabs
# ---------------------------------------------------------------------------
tab_tasks, tab_plan, tab_filter = st.tabs(["📋 Tasks", "📅 Daily Plan", "🔍 Filter & History"])

# ===== TAB 1: Add Tasks =====
with tab_tasks:
    st.subheader("Add a Care Task")

    if not st.session_state.pets:
        st.info("Add at least one pet in the sidebar first.")
    else:
        pet_names = [p["name"] for p in st.session_state.pets]
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        with col1:
            task_title = st.text_input("Task name", value="Morning Walk")
        with col2:
            task_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            task_priority = st.selectbox("Priority (1=low, 5=critical)", [1, 2, 3, 4, 5], index=2)
        with col4:
            task_category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
        with col5:
            task_pet = st.selectbox("For pet", pet_names)

        freq_col, _ = st.columns([1, 3])
        with freq_col:
            task_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

        if st.button("Add Task ➕"):
            st.session_state.task_rows.append({
                "pet": task_pet,
                "name": task_title,
                "duration_minutes": int(task_duration),
                "priority": int(task_priority),
                "category": task_category,
                "frequency": task_frequency,
            })
            st.success(f"Task '{task_title}' added for {task_pet}.")

    if st.session_state.task_rows:
        st.divider()
        st.subheader("Current Task List")
        st.table(st.session_state.task_rows)

        if st.button("Clear all tasks 🗑️"):
            st.session_state.task_rows = []
            st.rerun()

# ===== TAB 2: Daily Plan =====
with tab_plan:
    st.subheader("Generate Today's Plan")

    if st.button("Generate Schedule 🚀"):
        if not st.session_state.pets or not st.session_state.task_rows:
            st.warning("Add at least one pet and one task first.")
        else:
            # Build domain objects
            owner = Owner(name=owner_name, available_minutes_per_day=int(available_minutes))
            pet_map: dict = {}
            for p in st.session_state.pets:
                pet_obj = Pet(name=p["name"], species=p["species"])
                pet_map[p["name"]] = pet_obj
                owner.add_pet(pet_obj)

            for row in st.session_state.task_rows:
                try:
                    t = Task(
                        name=row["name"],
                        duration_minutes=row["duration_minutes"],
                        priority=row["priority"],
                        category=row["category"],
                        frequency=row["frequency"],
                    )
                    pet_map[row["pet"]].add_task(t)
                except ValueError as e:
                    st.error(f"Task error: {e}")
                    st.stop()

            scheduler = Scheduler(owner)
            plan = scheduler.generate_plan()

            # Conflict check — show warnings prominently
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                for warning in conflicts:
                    st.warning(warning)
            else:
                st.success("No scheduling conflicts detected.")

            # Scheduled tasks table
            if plan:
                st.subheader(f"📅 {owner_name}'s Plan ({sum(t.duration_minutes for t in plan)} min)")
                plan_data = [
                    {
                        "Time": t.start_time,
                        "Task": t.name,
                        "Duration": f"{t.duration_minutes} min",
                        "Priority": t.priority,
                        "Category": t.category,
                        "Recurring": t.frequency,
                    }
                    for t in scheduler.sort_by_time()
                ]
                st.table(plan_data)
            else:
                st.error("No tasks fit within the available time budget.")

            # Explanation
            with st.expander("🧠 Why was this plan chosen?"):
                st.text(scheduler.explain_plan())

# ===== TAB 3: Filter & History =====
with tab_filter:
    st.subheader("Filter Tasks")

    if not st.session_state.pets or not st.session_state.task_rows:
        st.info("Add pets and tasks first, then generate a plan to filter results.")
    else:
        pet_names_all = ["All"] + [p["name"] for p in st.session_state.pets]
        selected_pet = st.selectbox("Filter by pet", pet_names_all)
        selected_status = st.radio("Filter by status", ["All", "Incomplete", "Completed"], horizontal=True)

        # Rebuild owner/pets/tasks for filtering
        owner = Owner(name=owner_name, available_minutes_per_day=int(available_minutes))
        pet_map = {}
        for p in st.session_state.pets:
            pet_obj = Pet(name=p["name"], species=p["species"])
            pet_map[p["name"]] = pet_obj
            owner.add_pet(pet_obj)
        for row in st.session_state.task_rows:
            try:
                t = Task(
                    name=row["name"],
                    duration_minutes=row["duration_minutes"],
                    priority=row["priority"],
                    category=row["category"],
                    frequency=row["frequency"],
                )
                pet_map[row["pet"]].add_task(t)
            except ValueError:
                pass

        scheduler = Scheduler(owner)
        filter_pet = None if selected_pet == "All" else selected_pet
        filter_done = None if selected_status == "All" else (selected_status == "Completed")
        results = scheduler.filter_tasks(pet_name=filter_pet, completed=filter_done)

        if results:
            st.table([{
                "Task": t.name,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
                "Category": t.category,
                "Status": "✓ Done" if t.completed else "○ Pending",
            } for t in results])
        else:
            st.info("No tasks match the selected filters.")
