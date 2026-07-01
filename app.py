from datetime import date, datetime, time

import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task, TaskCategory

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

# Streamlit reruns this entire script top-to-bottom on every interaction
# (button click, text edit, etc.). A plain `owner = Owner(...)` here would
# recreate an empty Owner on every rerun. st.session_state is a dict-like
# "vault" that persists across reruns for the same browser session, so we
# only build the Owner the first time and reuse the same instance after that.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(id=1, name=owner_name, email="")
if "next_pet_id" not in st.session_state:
    st.session_state.next_pet_id = 1

owner = st.session_state.owner
owner.name = owner_name  # keep the stored Owner in sync with the widget

st.divider()

st.markdown("### Add a Pet")
pet_col1, pet_col2 = st.columns(2)
with pet_col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with pet_col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    # Owner.add_pet() is the Phase 2 method that owns this data: it appends
    # the new Pet onto owner.pets, which is the same list object living in
    # st.session_state.owner. The mutation happens in place, so nothing else
    # needs to "save" it back into the vault.
    new_pet = Pet(id=st.session_state.next_pet_id, name=pet_name, species=species)
    owner.add_pet(new_pet)
    st.session_state.next_pet_id += 1

if owner.pets:
    st.write("Current pets:")
    st.table([{"name": p.name, "species": p.species} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.divider()

st.markdown("### Schedule a Task")

if not owner.pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    pet_names = [p.name for p in owner.pets]
    selected_pet_name = st.selectbox("Pet", pet_names)
    selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        category = st.selectbox("Category", [c.value for c in TaskCategory])
    with col3:
        priority = st.selectbox("Priority", [p.value for p in Priority], index=2)

    col4, col5 = st.columns(2)
    with col4:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col5:
        task_time = st.time_input("Scheduled time", value=time(8, 0))

    if st.button("Add task"):
        # Pet.add_task() is the Phase 2 method that owns this data: it
        # appends the Task onto the selected pet's task list AND sets
        # task.pet back to that pet, so the task stays traceable to its pet.
        # The id comes from owner.next_task_id() (not a separate counter) so it
        # can't collide with ids the scheduler auto-generates for recurring rollovers.
        new_task = Task(
            id=owner.next_task_id(),
            description=task_title,
            category=TaskCategory(category),
            scheduled_time=datetime.combine(date.today(), task_time),
            priority=Priority(priority),
            duration_minutes=int(duration),
        )
        selected_pet.add_task(new_task)

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("Current tasks:")
        st.table(
            [
                {
                    "pet": t.pet.name if t.pet else "",
                    "title": t.description,
                    "time": t.scheduled_time.strftime("%I:%M %p"),
                    "priority": t.priority.value,
                    "status": t.status.value,
                }
                for t in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generates today's plan across all pets, sorted by priority.")

if st.button("Generate schedule"):
    # Scheduler.get_tasks_for_day() is the Phase 2 method that owns this:
    # it reads owner.get_all_tasks(), filters to today, and sorts by priority.
    scheduler = Scheduler()
    todays_tasks = scheduler.get_tasks_for_day(owner, date.today())

    if not todays_tasks:
        st.info("No tasks scheduled for today.")
    else:
        st.write("### Today's Schedule")
        for task in todays_tasks:
            pet_label = task.pet.name if task.pet else "Unknown pet"
            time_str = task.scheduled_time.strftime("%I:%M %p")
            st.write(f"**{time_str}** — {pet_label}: {task.description} _({task.priority.value})_")
