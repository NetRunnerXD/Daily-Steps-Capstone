import streamlit as st
import time
import uuid
from datetime import datetime, timedelta, date

import streamlit as st
import time
import uuid
import sqlite3
import hashlib
from datetime import datetime, timedelta, date

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="DAILY STEPS - FOR STUDENT ROUTINE", page_icon="📚", layout="centered")

# --- DATABASE SETUP ---
# Connect to SQLite database (this creates a file named 'data.db' in your folder)
conn = sqlite3.connect('data.db', check_same_thread=False)
c = conn.cursor()

# Create a table for users if it doesn't exist already
def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT PRIMARY KEY, password TEXT)')

# Add a new user to the database
def add_userdata(username, password):
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn.commit()

# Check if a user exists and the password matches
def login_user(username, password):
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, password))
    data = c.fetchall()
    return data

# Security: Hash passwords so they aren't saved as plain text
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# Initialize the database table
create_usertable()

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# --- LOGIN PAGE FUNCTION ---
# --- LOGIN & REGISTER PAGE ---
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.write("") 
        st.markdown("<h2 style='text-align: center; color: #4CAF50;'>Welcome to Daily Steps</h2>", unsafe_allow_html=True)
        
        # Create tabs for Login and Sign Up
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        # --- LOGIN TAB ---
        with tab1:
            with st.form(key="login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit_button = st.form_submit_button("Sign In", use_container_width=True)
                
                if submit_button:
                    # Hash the entered password to check against the database
                    hashed_pswd = make_hashes(password)
                    result = login_user(username, hashed_pswd)
                    
                    if result:
                        st.session_state.logged_in = True
                        st.session_state.current_user = username
                        st.success(f"Welcome back, {username}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                        
        # --- REGISTRATION TAB ---
        with tab2:
            with st.form(key="register_form"):
                new_username = st.text_input("Choose a Username")
                new_password = st.text_input("Choose a Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                register_button = st.form_submit_button("Create Account", use_container_width=True)
                
                if register_button:
                    if new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif len(new_username) < 3:
                        st.warning("Username must be at least 3 characters long.")
                    else:
                        # Check if username already exists
                        c.execute('SELECT * FROM userstable WHERE username =?', (new_username,))
                        if c.fetchone():
                            st.warning("Username already taken. Please choose another one.")
                        else:
                            # Hash the password and save to DB
                            add_userdata(new_username, make_hashes(new_password))
                            st.success("Account created successfully! You can now log in.")
                            st.balloons()

# --- MAIN APP FUNCTION ---
def show_main_app():
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", [
        "Home", 
        "Daily Routine Checklist", 
        "Tips for Self-Discipline",
        "Weekly Goals",
        "Daily Reflection"
    ])
    
    st.sidebar.divider()
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.logged_in = False
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
        * Review your progress in **Daily Reflection**.
        """)
        
        st.image("https://images.unsplash.com/photo-1434030216411-0b793f4b4173?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", caption="Focus and build your future.")

    # --- PAGE 2: DAILY ROUTINE ---
    elif page == "Daily Routine Checklist":
        # Note: Removed duplicate set_page_config from here as it can only be called once
        
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []
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
                time_str = dt.strftime("%I:%M %p").lstrip("0")
                return time_str.replace(":00", "")
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

        total_tasks = len(st.session_state.tasks)
        completed_tasks = sum(1 for t in st.session_state.tasks if t["completed"])
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

        with right_col:
            st.subheader("📋 Build Your Routine")
            
            with st.expander("⚡ Regular Tasks", expanded=True):
                tabs = st.tabs(list(PRESETS.keys()))
                
                for i, (category, items) in enumerate(PRESETS.items()):
                    with tabs[i]:
                        cols = st.columns(2) 
                        for j, item in enumerate(items):
                            with cols[j % 2]:
                                if st.button(f"➕ {item['task']}", key=f"preset_{category}_{j}"):
                                    clean_now = datetime.now().replace(second=0, microsecond=0).time()
                                    st.session_state.tasks.append({
                                        "id": str(uuid.uuid4()), 
                                        "task": item["task"], 
                                        "time": get_time_window(clean_now, item["duration"]),
                                        "priority": item["priority"],
                                        "completed": False
                                    })
                                    st.toast(f"Added: {item['task']}", icon="✅")
                                    st.rerun()
                                    
            with st.expander("➕ Schedule a Custom Task", expanded=False):
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
                        st.session_state.tasks.append({
                            "id": str(uuid.uuid4()), 
                            "task": new_task_name, 
                            "time": get_time_window(new_time, new_duration),
                            "priority": new_priority,
                            "completed": False
                        })
                        st.toast(f"Added: {new_task_name}", icon="✅")
                        st.rerun()

            st.divider()
            
            st.subheader("🗓️ Today's Action Plan")
            
            if not st.session_state.tasks:
                st.info("Your schedule is empty! Use the menus above to plan your day.")
            else:
                sorted_tasks = sorted(st.session_state.tasks, key=lambda x: x['completed'])
                
                for task_dict in sorted_tasks:
                    with st.container(border=True):
                        col_chk, col_time, col_task, col_pri, col_del = st.columns([0.5, 1.5, 3, 1, 0.5])
                        
                        with col_chk:
                            is_checked = st.checkbox("", value=task_dict["completed"], key=f"chk_{task_dict['id']}")
                            if is_checked != task_dict["completed"]:
                                for t in st.session_state.tasks:
                                    if t["id"] == task_dict["id"]:
                                        t["completed"] = is_checked
                                        if is_checked:
                                            st.toast(f"Completed: {t['task']}!", icon="🎉")
                                        break
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
                                st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_dict["id"]]
                                st.rerun()

    # --- PAGE 3: DISCIPLINE TIPS ---
    elif page == "Tips for Self-Discipline":
        st.title("🧠 Improving Self-Discipline")
        
        st.write("Self-discipline is a muscle. The more you use it, the stronger it gets. Here are some beginner-friendly tips:")
        
        with st.expander("1. The 5-Minute Rule"):
            st.write("If a task takes less than 5 minutes to do, do it immediately. If it takes longer and you are procrastinating, commit to doing it for just 5 minutes. Usually, starting is the hardest part!")
            
        with st.expander("2. Put Your Phone in Another Room"):
            st.write("Out of sight, out of mind. When studying, put your phone in a drawer or another room to eliminate the temptation to scroll.")
            
        with st.expander("3. Use the Pomodoro Technique"):
            st.write("Study for 25 minutes, then take a 5-minute break. This keeps your brain fresh and makes large study sessions feel much more manageable.")
            
        with st.expander("4. Forgive Yourself"):
            st.write("If you mess up your routine one day, don't quit. Acknowledge the slip-up, and just try again the next day. Perfection is impossible; progress is the goal.")

    # --- PAGE 4: WEEKLY GOALS ---
    elif page == "Weekly Goals":
        st.title("🎯 Weekly Goals")
        st.write("Set your main objectives for the week so you know exactly what you're working towards.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Academic Goals")
            st.text_input("Goal 1 (e.g., Finish Math Assignment)")
            st.text_input("Goal 2 (e.g., Read 2 chapters of History)")
            st.text_input("Goal 3 (e.g., Organize study notes)")
            
        with col2:
            st.subheader("Personal Goals")
            st.text_input("Goal 1 (e.g., Exercise 3 times)")
            st.text_input("Goal 2 (e.g., Sleep 8 hours every night)")
            st.text_input("Goal 3 (e.g., Call family/friends)")
            
        st.write("---")
        if st.button("Save Goals"):
            st.balloons()
            st.success("Goals saved for the week! Keep pushing, you've got this!")

    # --- PAGE 5: DAILY REFLECTION ---
    elif page == "Daily Reflection":
        st.title("📝 Daily Reflection")
        st.write("Take a few minutes at the end of the day to review your progress.")
        
        st.slider("How productive do you feel you were today?", min_value=1, max_value=10, value=5)
        
        st.text_area("What went well today?", placeholder="E.g., I successfully completed my morning routine and focused well during deep study.")
        st.text_area("What could be improved tomorrow?", placeholder="E.g., I spent too much time on my phone during my lunch break.")
        
        if st.button("Submit Reflection"):
            st.success("Reflection submitted! Self-awareness is the first step to continuous improvement.")


# --- APP ROUTING LOGIC ---
if not st.session_state.logged_in:
    show_login_page()
else:
    show_main_app()