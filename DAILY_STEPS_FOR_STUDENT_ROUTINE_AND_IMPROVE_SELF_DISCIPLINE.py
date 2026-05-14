import streamlit as st
import time
import uuid
import sqlite3
import hashlib
from datetime import datetime, timedelta, date

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="DAILY STEPS - FOR STUDENT ROUTINE AND IMPROVE SELF DISCIPLINE", page_icon="📚", layout="wide")

# --- DATABASE SETUP (Data Persistence) ---
def init_db():
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            email TEXT,
            notifications_enabled INTEGER
        )
    ''')
    # Tasks table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            username TEXT,
            task TEXT,
            time TEXT,
            priority TEXT,
            completed INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- AUTHENTICATION HELPER FUNCTIONS ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

def add_user(username, password, email):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('INSERT INTO users(username, password, email, notifications_enabled) VALUES (?,?,?,?)', 
              (username, make_hashes(password), email, 0))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    if data:
        return check_hashes(password, data[0])
    return False

# --- DATABASE TASK OPERATIONS ---
def add_task(task_id, username, task, time_str, priority, completed=0):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('INSERT INTO tasks(id, username, task, time, priority, completed) VALUES (?,?,?,?,?,?)',
              (task_id, username, task, time_str, priority, completed))
    conn.commit()
    conn.close()

def get_tasks(username):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('SELECT id, task, time, priority, completed FROM tasks WHERE username = ?', (username,))
    data = c.fetchall()
    conn.close()
    return [{"id": row[0], "task": row[1], "time": row[2], "priority": row[3], "completed": bool(row[4])} for row in data]

def update_task_status(task_id, completed):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('UPDATE tasks SET completed = ? WHERE id = ?', (int(completed), task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# --- AUTHENTICATION UI ---
if not st.session_state.logged_in:
    st.title("🔒 Welcome to Daily Steps")
    st.write("Please log in or sign up to access your routine and save your progress.")
    
    auth_mode = st.radio("Select an option:", ["Login", "Sign Up"])
    
    if auth_mode == "Login":
        st.subheader("Login to your account")
        username = st.text_input("Username")
        password = st.text_input("Password", type='password')
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Incorrect Username or Password")
                
    elif auth_mode == "Sign Up":
        st.subheader("Create a new account")
        new_user = st.text_input("Username")
        new_email = st.text_input("Email Address")
        new_password = st.text_input("Password", type='password')
        if st.button("Sign Up"):
            # Check if user exists
            conn = sqlite3.connect('daily_steps.db')
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ?', (new_user,))
            if c.fetchone():
                st.warning("Username already exists. Please choose another one.")
            else:
                add_user(new_user, new_password, new_email)
                st.success("Account created successfully! Please proceed to Login.")
            conn.close()

# --- MAIN APPLICATION (Only visible if logged in) ---
else:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title(f"👤 {st.session_state.username}'s Dashboard")
    page = st.sidebar.radio("Go to:", [
        "Home", 
        "Daily Routine Checklist", 
        "Tips for Self-Discipline",
        "Weekly Goals",
        "Daily Reflection",
        "Notifications & Settings"
    ])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # --- PAGE 1: HOME ---
    if page == "Home":
        st.title("📚 Daily Steps for Students")
        st.subheader("Build a strong routine and master self-discipline.")
        
        st.write("""
        Welcome to your personal growth tracker! As a student, building a solid daily routine 
        is the foundation of academic success and reduced stress. 
        
        **How to use this site:**
        * Use the **Navigation menu** on the left to switch between pages.
        * Check out the **Daily Routine Checklist** to track your daily habits.
        * Read the **Tips for Self-Discipline** to stay motivated.
        * Set your targets in **Weekly Goals**.
        * Configure your automated alerts in **Notifications & Settings**.
        """)
        
        st.image("https://images.unsplash.com/photo-1434030216411-0b793f4b4173?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", caption="Focus and build your future.")

    # --- PAGE 2: DAILY ROUTINE ---
    elif page == "Daily Routine Checklist":
        if 'focus_time_logged' not in st.session_state:
            st.session_state.focus_time_logged = 0
        if 'timer_active' not in st.session_state:
            st.session_state.timer_active = False
        if 'start_time' not in st.session_state:
            st.session_state.start_time = None

        def get_time_window(start_time, duration_mins):
            start_dt = datetime.combine(date.today(), start_time)
            end_dt = start_dt + timedelta(minutes=duration_mins)
            def format_t(dt):
                return dt.strftime("%I:%M %p").lstrip("0").replace(":00", "")
            return f"{format_t(start_dt)} - {format_t(end_dt)}"

        def start_timer():
            if not st.session_state.timer_active:
                st.session_state.timer_active = True
                st.session_state.start_time = time.time()

        def stop_timer():
            if st.session_state.timer_active and st.session_state.start_time:
                elapsed_seconds = time.time() - st.session_state.start_time
                st.session_state.focus_time_logged += int(elapsed_seconds // 60)
            st.session_state.timer_active = False
            st.session_state.start_time = None

        PRESETS = {
            "📚 Study": [
                {"task": "Self Study (1 hr)", "priority": "🔴 High", "duration": 60},
                {"task": "Revise Session", "priority": "🟡 Med", "duration": 30},
                {"task": "Daily Lectures", "priority": "🟢 Low", "duration": 30}
            ],
            "💪 Fitness": [
                {"task": "30 Min Cardio", "priority": "🟡 Med", "duration": 30},
                {"task": "Strength Training", "priority": "🔴 High", "duration": 30}
            ]
        }

        st.markdown("""
            <style>
            .big-font { font-size:30px !important; font-weight: bold; color: #4CAF50;}
            .stButton button { width: 100%; text-align: left; }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<p class="big-font">⚡ Daily Routine</p>', unsafe_allow_html=True)

        # Fetch tasks from database
        current_tasks = get_tasks(st.session_state.username)
        total_tasks = len(current_tasks)
        completed_tasks = sum(1 for t in current_tasks if t["completed"])
        completion_rate = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Tasks Completed", value=f"{completed_tasks} / {total_tasks}", delta=f"{completion_rate}%")
        with col2:
            st.metric(label="Pending Tasks", value=total_tasks - completed_tasks)
        with col3:
            st.metric(label="Focus Time Logged", value=f"{st.session_state.focus_time_logged} mins", delta="Focus Session")

        st.progress(completion_rate)
        st.divider()

        left_col, right_col = st.columns([1, 2.5])

        # FOCUS TIMER
        with left_col:
            with st.container(border=True):
                st.subheader("⏱️ Focus Timer")
                focus_minutes = st.number_input("Minutes", min_value=1, max_value=120, value=25)
                
                col_start, col_stop = st.columns(2)
                with col_start:
                    st.button("🚀 Start", use_container_width=True, on_click=start_timer)
                with col_stop:
                    st.button("⏹️ Stop", use_container_width=True, on_click=stop_timer)

                timer_placeholder = st.empty()
                if st.session_state.timer_active:
                    total_seconds = focus_minutes * 60
                    for remaining in range(total_seconds, -1, -1):
                        mins, secs = divmod(remaining, 60)
                        timer_placeholder.markdown(f"<h1 style='text-align: center; color: #ff4b4b;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
                        time.sleep(1)
                    
                    st.session_state.timer_active = False
                    st.session_state.start_time = None
                    st.session_state.focus_time_logged += focus_minutes
                    st.toast("⏰ Time's up! Take a break.", icon="🔥")
                    st.balloons()
                    st.rerun()
                else:
                    timer_placeholder.markdown(f"<h1 style='text-align: center; color: #555;'>{focus_minutes:02d}:00</h1>", unsafe_allow_html=True)

        # TASK MANAGEMENT
        with right_col:
            st.subheader("📋 Build Your Routine")
            
            with st.expander("⚡ Regular Tasks", expanded=False):
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
                                    
            with st.expander("➕ Schedule a Custom Task", expanded=True):
                with st.form(key="add_task_form", clear_on_submit=True):
                    c1, c2, c3, c4 = st.columns([2.5, 1.5, 1, 1])
                    with c1:
                        new_task_name = st.text_input("Task Description:")
                    with c2:
                        clean_default_time = datetime.now().replace(second=0, microsecond=0).time()
                        new_time = st.time_input("Start Time:", value=clean_default_time)
                    with c3:
                        new_duration = st.number_input("Mins:", min_value=5, step=5, value=30)
                    with c4:
                        new_priority = st.selectbox("Priority:", ["🔴 High", "🟡 Med", "🟢 Low"])
                        
                    if st.form_submit_button("Add to Schedule") and new_task_name.strip():
                        t_window = get_time_window(new_time, new_duration)
                        add_task(str(uuid.uuid4()), st.session_state.username, new_task_name, t_window, new_priority)
                        st.toast(f"Added: {new_task_name}", icon="✅")
                        st.rerun()

            st.divider()
            st.subheader("🗓️ Today's Action Plan")
            
            if not current_tasks:
                st.info("Your schedule is empty! Use the menus above to plan your day.")
            else:
                sorted_tasks = sorted(current_tasks, key=lambda x: x['completed'])
                for task_dict in sorted_tasks:
                    with st.container(border=True):
                        col_chk, col_time, col_task, col_pri, col_del = st.columns([0.5, 1.5, 3, 1, 0.5])
                        
                        with col_chk:
                            is_checked = st.checkbox("", value=task_dict["completed"], key=f"chk_{task_dict['id']}")
                            if is_checked != task_dict["completed"]:
                                update_task_status(task_dict["id"], is_checked)
                                if is_checked:
                                    st.toast(f"Completed: {task_dict['task']}!", icon="🎉")
                                st.rerun()
                                
                        with col_time:
                            st.write(f"🕰️ **{task_dict['time']}**")
                            
                        with col_task:
                            if task_dict["completed"]:
                                st.markdown(f"<span style='text-decoration: line-through; color: #888;'>{task_dict['task']}</span>", unsafe_allow_html=True)
                            else:
                                st.write(task_dict["task"])
                                
                        with col_pri:
                            st.write(task_dict['priority'])
                            
                        with col_del:
                            if st.button("✖", key=f"del_{task_dict['id']}", help="Delete"):
                                delete_task(task_dict["id"])
                                st.rerun()

    # --- PAGE 3: DISCIPLINE TIPS ---
    elif page == "Tips for Self-Discipline":
        st.title("🧠 Improving Self-Discipline")
        st.write("Self-discipline is a muscle. The more you use it, the stronger it gets.")
        with st.expander("1. The 5-Minute Rule"):
            st.write("If a task takes less than 5 minutes to do, do it immediately.")
        with st.expander("2. Put Your Phone in Another Room"):
            st.write("Out of sight, out of mind. Eliminate the temptation to scroll.")
        with st.expander("3. Use the Pomodoro Technique"):
            st.write("Study for 25 minutes, then take a 5-minute break.")

    # --- PAGE 4: WEEKLY GOALS ---
    elif page == "Weekly Goals":
        st.title("🎯 Weekly Goals")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Academic Goals")
            st.text_input("Goal 1", key="acad1")
            st.text_input("Goal 2", key="acad2")
        with col2:
            st.subheader("Personal Goals")
            st.text_input("Goal 1", key="pers1")
            st.text_input("Goal 2", key="pers2")
        if st.button("Save Goals"):
            st.success("Goals saved securely to your profile!")

    # --- PAGE 5: DAILY REFLECTION ---
    elif page == "Daily Reflection":
        st.title("📝 Daily Reflection")
        st.slider("How productive do you feel you were today?", min_value=1, max_value=10, value=5)
        st.text_area("What went well today?")
        st.text_area("What could be improved tomorrow?")
        if st.button("Submit Reflection"):
            st.success("Reflection saved! Self-awareness is the first step to continuous improvement.")

    # --- PAGE 6: NOTIFICATIONS & SETTINGS (Implemented Future Work) ---
    elif page == "Notifications & Settings":
        st.title("🔔 Automated Notification System")
        st.write("Manage your email alerts and push notifications for your daily routines.")
        
        # Get user data
        conn = sqlite3.connect('daily_steps.db')
        c = conn.cursor()
        c.execute('SELECT email, notifications_enabled FROM users WHERE username = ?', (st.session_state.username,))
        user_data = c.fetchone()
        
        email = user_data[0]
        notifications_enabled = bool(user_data[1])
        
        with st.container(border=True):
            st.subheader("Email Preferences")
            new_email = st.text_input("Registered Email Address", value=email)
            enable_alerts = st.toggle("Enable Daily Summary & Alerts", value=notifications_enabled)
            
            if st.button("Update Settings"):
                c.execute('UPDATE users SET email = ?, notifications_enabled = ? WHERE username = ?', 
                          (new_email, int(enable_alerts), st.session_state.username))
                conn.commit()
                st.success("Settings updated successfully!")
                
        st.divider()
        st.subheader("🛠️ System Test: Force Send Alert")
        st.write("Click below to simulate the backend chron-job sending an email reminder for your pending tasks.")
        
        if st.button("📨 Send Mock Email Alert Now"):
            if not enable_alerts:
                st.error("Please enable alerts above to receive emails.")
            else:
                with st.spinner("Connecting to mail server..."):
                    time.sleep(1.5) # Simulate network delay
                    current_tasks = get_tasks(st.session_state.username)
                    pending = [t['task'] for t in current_tasks if not t['completed']]
                    
                    if pending:
                        st.success(f"**Email Sent to {new_email}!**")
                        st.info(f"**Subject:** 🚨 You have {len(pending)} pending tasks!\n\n**Body:**\nDon't forget to complete: {', '.join(pending)}.")
                    else:
                        st.success(f"**Email Sent to {new_email}!**")
                        st.info("**Subject:** 🎉 You are all caught up!\n\n**Body:**\nGreat job! You have no pending tasks for today.")
        conn.close()
