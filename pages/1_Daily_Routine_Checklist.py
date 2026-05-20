import streamlit as st
import time
import uuid
import sqlite3
from datetime import datetime, timedelta, date
from backend import *

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the Home page first.")
    st.stop()

render_sidebar()

if 'timer_active' not in st.session_state: st.session_state.timer_active = False
if 'end_time' not in st.session_state: st.session_state.end_time = None
if 'timer_minutes' not in st.session_state: st.session_state.timer_minutes = 0

today_focus_time = get_today_focus_mongo(st.session_state.username)

def get_time_window(start_time, duration_mins):
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = start_dt + timedelta(minutes=duration_mins)
    return f"{start_dt.strftime('%I:%M %p').lstrip('0').replace(':00', '')} - {end_dt.strftime('%I:%M %p').lstrip('0').replace(':00', '')}"

def start_timer_cb(mins):
    st.session_state.timer_active = True
    st.session_state.timer_minutes = mins
    st.session_state.end_time = datetime.now() + timedelta(minutes=mins)

def stop_timer_cb():
    if st.session_state.timer_active and st.session_state.end_time:
        remaining_sec = (st.session_state.end_time - datetime.now()).total_seconds()
        elapsed_sec = (st.session_state.timer_minutes * 60) - remaining_sec
        if elapsed_sec > 60: 
            log_focus_time_mongo(st.session_state.username, int(elapsed_sec // 60))
    st.session_state.timer_active = False
    st.session_state.end_time = None

@st.dialog("➕ Schedule Custom Task")
def custom_task_modal():
    new_task_name = st.text_input("Task Description:")
    col1, col2, col3 = st.columns([1.5, 1, 1])
    with col1: new_time = st.time_input("Start Time:", value=datetime.now().time().replace(second=0, microsecond=0))
    with col2: new_duration = st.number_input("Mins:", min_value=5, step=5, value=30)
    with col3: new_priority = st.selectbox("Priority:", ["🔴 High", "🟡 Med", "🟢 Low"])
        
    if st.button("Add to Schedule", use_container_width=True):
        if new_task_name.strip():
            t_window = get_time_window(new_time, new_duration)
            add_task(str(uuid.uuid4()), st.session_state.username, new_task_name, t_window, new_priority)
            st.toast(f"Added: {new_task_name}", icon="✅")
            st.rerun()
        else:
            st.error("Please enter a description.")

@st.dialog("✏️ Edit Task")
def edit_task_modal(task_id, current_name, current_priority, current_time_str):
    try:
        start_str = current_time_str.split(" - ")[0]
        parsed_time = datetime.strptime(start_str, "%I:%M %p").time()
    except (IndexError, ValueError):
        parsed_time = datetime.now().time().replace(second=0, microsecond=0)

    new_task_name = st.text_input("New Description:", value=current_name)
    col1, col2 = st.columns(2)
    with col1: new_time = st.time_input("New Start Time:", value=parsed_time)
    with col2: new_duration = st.number_input("Duration (Mins):", min_value=5, step=5, value=30)
    
    if st.button("Save Changes", use_container_width=True):
        if new_task_name.strip():
            t_window = get_time_window(new_time, new_duration)
            edit_task_details(task_id, new_task_name, t_window, current_priority)
            st.toast("Task updated!", icon="✏️")
            st.rerun()

PRESETS = {
    "📚 Study": [
        {"task": "Self Study (1 hr)", "priority": "🔴 High", "duration": 60},
        {"task": "Revise Session", "priority": "🟡 Med", "duration": 30},
        {"task": "Daily Lectures", "priority": "🟢 Low", "duration": 30},
        {"task": "Complete Practice Set", "priority": "🔴 High", "duration": 30}
    ],
    "💪 Fitness": [
        {"task": "30 Min Cardio", "priority": "🟡 Med", "duration": 30},
        {"task": "Strength Training", "priority": "🔴 High", "duration": 30},
        {"task": "15 Min Yoga/Stretch", "priority": "🟢 Low", "duration": 15},
        {"task": "Hit 10k Steps", "priority": "🟡 Med", "duration": 30}
    ],
    "🧠 Life": [
        {"task": "Meal Prep", "priority": "🟡 Med", "duration": 30},
        {"task": "Tidy Workspace", "priority": "🟢 Low", "duration": 30},
        {"task": "Read 10 Pages", "priority": "🟢 Low", "duration": 30},
        {"task": "Checking Inboxes", "priority": "🟡 Med", "duration": 30}
    ],
    "💻 Project": [
        {"task": "Code for 1 Hour", "priority": "🔴 High", "duration": 60},
        {"task": "Youtube Lectures", "priority": "🟡 Med", "duration": 30},
        {"task": "Brainstorming/ Leetcode", "priority": "🔴 High", "duration": 30},
        {"task": "Update GitHub", "priority": "🟢 Low", "duration": 30}
    ]
}

st.markdown("""
    <style>
    .big-font { font-size:30px !important; font-weight: bold; color: #4CAF50;}
    .stButton button { width: 100%; text-align: left; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">⚡ Daily Routine</p>', unsafe_allow_html=True)

current_tasks = get_tasks(st.session_state.username)
total_tasks = len(current_tasks)
completed_tasks = sum(1 for t in current_tasks if t["completed"])
completion_rate = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

col1, col2, col3 = st.columns(3)
with col1: st.metric("Tasks Completed", f"{completed_tasks} / {total_tasks}", f"{completion_rate}%")
with col2: st.metric("Pending Tasks", total_tasks - completed_tasks)
with col3: st.metric("Focus Time Logged", f"{today_focus_time} mins", "Today")

st.progress(completion_rate)
st.divider()

left_col, right_col = st.columns([1, 2.5])

with left_col:
    with st.container(border=True):
        st.subheader("⏱️ Focus Timer")
        focus_minutes = st.number_input("Minutes", min_value=1, max_value=120, value=25)
        
        col_start, col_stop = st.columns(2)
        with col_start: st.button("🚀 Start", use_container_width=True, on_click=start_timer_cb, args=(focus_minutes,))
        with col_stop: st.button("⏹️ Stop", use_container_width=True, on_click=stop_timer_cb)

        timer_placeholder = st.empty()
        
        if st.session_state.timer_active and st.session_state.end_time:
            remaining_sec = int((st.session_state.end_time - datetime.now()).total_seconds())
            
            if remaining_sec > 0:
                for rem in range(remaining_sec, -1, -1):
                    mins, secs = divmod(rem, 60)
                    timer_placeholder.markdown(f"<h1 style='text-align: center; color: #ff4b4b;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
                    time.sleep(1)
            
            st.session_state.timer_active = False
            log_focus_time_mongo(st.session_state.username, st.session_state.timer_minutes)
            st.session_state.end_time = None
            st.toast("⏰ Time's up! Take a break.", icon="🔥")
            st.balloons()
            st.rerun()
        else:
            timer_placeholder.markdown(f"<h1 style='text-align: center; color: #555;'>{focus_minutes:02d}:00</h1>", unsafe_allow_html=True)

with right_col:
    c_header, c_sort = st.columns([2, 1])
    with c_header:
        st.subheader("📋 Build Your Routine")
    with c_sort:
        sort_pref = st.selectbox("Sort By:", ["Time", "Priority"], label_visibility="collapsed")
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("➕ Custom Task", use_container_width=True):
            custom_task_modal()
    
    with st.expander("⚡ Add Regular Presets", expanded=False):
        tabs = st.tabs(list(PRESETS.keys()))
        for i, (category, items) in enumerate(PRESETS.items()):
            with tabs[i]:
                cols = st.columns(2) 
                for j, item in enumerate(items):
                    with cols[j % 2]:
                        if st.button(f"➕ {item['task']}", key=f"preset_{category}_{j}"):
                            clean_now = datetime.now().replace(second=0, microsecond=0).time()
                            t_window = get_time_window(clean_now, item["duration"])
                            add_task(str(uuid.uuid4()), st.session_state.username, item["task"], t_window, item["priority"])
                            st.toast(f"Added: {item['task']}", icon="✅")
                            st.rerun()

    st.divider()
    st.subheader("🗓️ Today's Action Plan")
    
    if not current_tasks:
        st.info("Your schedule is empty! Use the menus above to plan your day.")
    else:
        tab_pending, tab_completed = st.tabs(["⏳ Pending Tasks", "✅ Completed Tasks"])
        
        with tab_pending:
            pending_tasks = [t for t in current_tasks if not t['completed']]
            
            if "Priority" in sort_pref:
                w = {"🔴 High": 1, "🟡 Med": 2, "🟢 Low": 3}
                pending_tasks = sorted(pending_tasks, key=lambda x: w.get(x['priority'], 4))

            if not pending_tasks:
                st.success("You are all caught up for today! 🎉")
            else:
                for task_dict in pending_tasks:
                    with st.container(border=True):
                        col_chk, col_time, col_task, col_pri, col_edit, col_del = st.columns([0.5, 1.5, 2.5, 1, 0.5, 0.5])
                        with col_chk:
                            is_checked = st.checkbox("", value=task_dict["completed"], key=f"chk_p_{task_dict['id']}")
                            if is_checked:
                                update_task_status(task_dict["id"], True)
                                xp_reward = {"🔴 High": 20, "🟡 Med": 10, "🟢 Low": 5}.get(task_dict['priority'], 10)
                                leveled_up = add_xp(st.session_state.username, xp_reward) 
                                
                                if leveled_up:
                                    new_stats = get_gamification(st.session_state.username)
                                    new_title = get_rank_title(new_stats['level'])
                                    level_up_popup(new_stats['level'], new_title)
                                else:
                                    st.toast(f"Task Completed! (+{xp_reward} XP)", icon="🎮")
                                    time.sleep(0.5) 
                                    st.rerun()

                        with col_time: st.write(f"🕰️ **{task_dict['time']}**")
                        with col_task: st.write(task_dict["task"])
                        with col_pri: st.write(task_dict['priority'])
                        with col_edit:
                            if st.button("✏️", key=f"edit_p_{task_dict['id']}", help="Edit Task"):
                                edit_task_modal(task_dict["id"], task_dict["task"], task_dict["priority"], task_dict["time"])
                        with col_del:
                            if st.button("✖", key=f"del_p_{task_dict['id']}", help="Delete"):
                                delete_task(task_dict["id"])
                                st.rerun()

        with tab_completed:
            done_tasks = [t for t in current_tasks if t['completed']]
            if not done_tasks:
                st.info("No tasks completed yet. Let's get to work! 💪")
            else:
                for task_dict in done_tasks:
                    with st.container(border=True):
                        col_chk, col_time, col_task, col_pri, col_del = st.columns([0.5, 1.5, 3, 1, 0.5])
                        with col_chk:
                            is_checked = st.checkbox("", value=task_dict["completed"], key=f"chk_c_{task_dict['id']}")
                            if not is_checked:
                                update_task_status(task_dict["id"], False)
                                st.rerun()
                        with col_time: st.write(f"🕰️ **{task_dict['time']}**")
                        with col_task: st.markdown(f"<span style='text-decoration: line-through; color: #888;'>{task_dict['task']}</span>", unsafe_allow_html=True)
                        with col_pri: st.write(task_dict['priority'])
                        with col_del:
                            if st.button("✖", key=f"del_c_{task_dict['id']}", help="Delete"):
                                delete_task(task_dict["id"])
                                st.rerun()
            
        st.divider()
        st.markdown("### 🌙 End of Day Checkout")
        st.write("Done for the day? Log your final progress to history and clear your board for tomorrow.")
        
        if st.button("✅ Complete My Day & Checkout", use_container_width=True, type="primary"):
            if total_tasks > 0:
                if MONGO_AVAILABLE:
                    history_data = {
                        "completion_rate": completion_rate,
                        "tasks_completed": completed_tasks,
                        "total_tasks": total_tasks,
                        "focus_minutes": today_focus_time,
                        "logged_at": datetime.now()
                    }
                    history_col.update_one(
                        {"username": st.session_state.username, "date": str(date.today())},
                        {"$set": history_data},
                        upsert=True
                    )
                
                conn = sqlite3.connect('daily_steps.db')
                c = conn.cursor()
                c.execute('DELETE FROM tasks WHERE username = ?', (st.session_state.username,))
                conn.commit()
                conn.close()
                
                update_streak_on_checkout(st.session_state.username)
                
                @st.dialog("🌙 Day Completed!")
                def checkout_summary(rate, focus):
                    st.balloons()
                    final_stats = get_gamification(st.session_state.username)
                    streak = final_stats['streak']
                    
                    st.markdown(f"<h2 style='text-align: center; color: #4CAF50;'>Great work, {st.session_state.username}!</h2>", unsafe_allow_html=True)
                    
                    if streak in [3, 7, 14, 30, 100]:
                        st.success(f"🔥 INCREDIBLE! You hit a {streak}-Day Streak!")
                    else:
                        st.write(f"Current Streak: 🔥 **{streak} Days**")

                    st.write(f"📊 **Completion Rate:** {rate}%")
                    st.write(f"⏱️ **Focus Time:** {focus} minutes")
                    st.divider()
                    st.info("Your progress is logged. See you tomorrow!")
                    if st.button("Finish", use_container_width=True):
                        st.rerun()
                
                checkout_summary(completion_rate, today_focus_time)
                
            else:
                st.warning("You don't have any tasks on your board to check out!")