import streamlit as st
import time
import uuid
import hashlib
from datetime import datetime, timedelta, date
import pymongo

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="DAILY STEPS - FOR STUDENT ROUTINE", page_icon="📚", layout="wide")

# ==========================================
# 1. DATABASE SETUP (100% Cloud MongoDB)
# ==========================================
MONGO_URI = st.secrets["MONGO_URI"] 

# Use Streamlit's cache so it only connects to the database once
@st.cache_resource
def init_mongo_connection():
    return pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)

try:
    mongo_client = init_mongo_connection()
    mongo_client.server_info() # Trigger exception if cannot connect
    mongo_db = mongo_client["daily_steps_db"]
    
    # All Collections
    users_col = mongo_db["users"]
    tasks_col = mongo_db["tasks"]
    focus_col = mongo_db["focus_logs"]
    goals_col = mongo_db["weekly_goals"]
    reflections_col = mongo_db["reflections"]
    MONGO_AVAILABLE = True
except pymongo.errors.ServerSelectionTimeoutError:
    MONGO_AVAILABLE = False
    st.sidebar.error("⚠️ CRITICAL: Could not connect to MongoDB Atlas. Check your internet or secrets.toml.")


# ==========================================
# 2. HELPER FUNCTIONS (Now Fully MongoDB)
# ==========================================

# --- Authentication Helpers ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

def add_user(username, password, email):
    if not MONGO_AVAILABLE: return
    users_col.insert_one({
        "username": username, 
        "password": make_hashes(password), 
        "email": email, 
        "notifications_enabled": False
    })

def login_user(username, password):
    if not MONGO_AVAILABLE: return False
    user = users_col.find_one({"username": username})
    if user: return check_hashes(password, user["password"])
    return False

# --- Task Operations ---
def add_task(task_id, username, task, time_str, priority, completed=False):
    if not MONGO_AVAILABLE: return
    tasks_col.insert_one({
        "id": task_id, "username": username, "task": task, 
        "time": time_str, "priority": priority, "completed": bool(completed)
    })

def get_tasks(username):
    if not MONGO_AVAILABLE: return []
    data = tasks_col.find({"username": username})
    return [{"id": row["id"], "task": row["task"], "time": row["time"], "priority": row["priority"], "completed": row.get("completed", False)} for row in data]

def update_task_status(task_id, completed):
    if not MONGO_AVAILABLE: return
    tasks_col.update_one({"id": task_id}, {"$set": {"completed": bool(completed)}})

def delete_task(task_id):
    if not MONGO_AVAILABLE: return
    tasks_col.delete_one({"id": task_id})

# --- Other Operations ---
def log_focus_time_mongo(username, minutes):
    if not MONGO_AVAILABLE: 
        st.session_state.focus_time_logged = st.session_state.get('focus_time_logged', 0) + minutes
        return
    today = str(date.today())
    focus_col.update_one({"username": username, "date": today}, {"$inc": {"minutes_logged": minutes}}, upsert=True)

def get_today_focus_mongo(username):
    if not MONGO_AVAILABLE: return st.session_state.get('focus_time_logged', 0)
    doc = focus_col.find_one({"username": username, "date": str(date.today())})
    return doc["minutes_logged"] if doc else 0

def save_weekly_goals_mongo(username, goals_data):
    if not MONGO_AVAILABLE: return
    goals_col.update_one({"username": username}, {"$set": goals_data}, upsert=True)

def save_reflection_mongo(username, reflection_data):
    if not MONGO_AVAILABLE: return
    reflection_data["date"] = str(date.today())
    reflections_col.update_one({"username": username, "date": str(date.today())}, {"$set": reflection_data}, upsert=True)


# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""


# ==========================================
# 4. AUTHENTICATION UI
# ==========================================
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
            if MONGO_AVAILABLE:
                existing_user = users_col.find_one({"username": new_user})
                if existing_user:
                    st.warning("Username already exists. Please choose another one.")
                else:
                    add_user(new_user, new_password, new_email)
                    st.success("Account created successfully! Please proceed to Login.")
            else:
                st.error("Cannot sign up: MongoDB is disconnected.")


# ==========================================
# 5. MAIN APPLICATION (Logged In)
# ==========================================
else:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title(f"👤 {st.session_state.username}'s Dashboard")
    page = st.sidebar.radio("Go to:", [
        "Home", "Daily Routine Checklist", "Tips for Self-Discipline",
        "Weekly Goals", "Daily Reflection", "Notifications & Settings"
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
        
        # Non-blocking Timer State
        if 'timer_active' not in st.session_state: st.session_state.timer_active = False
        if 'end_time' not in st.session_state: st.session_state.end_time = None
        if 'timer_minutes' not in st.session_state: st.session_state.timer_minutes = 0

        today_focus_time = get_today_focus_mongo(st.session_state.username)

        def get_time_window(start_time, duration_mins):
            start_dt = datetime.combine(date.today(), start_time)
            end_dt = start_dt + timedelta(minutes=duration_mins)
            return f"{start_dt.strftime('%I:%M %p').lstrip('0').replace(':00', '')} - {end_dt.strftime('%I:%M %p').lstrip('0').replace(':00', '')}"

        def start_timer(mins):
            st.session_state.timer_active = True
            st.session_state.timer_minutes = mins
            st.session_state.end_time = datetime.now() + timedelta(minutes=mins)

        def stop_timer():
            if st.session_state.timer_active and st.session_state.end_time:
                elapsed = st.session_state.timer_minutes - (st.session_state.end_time - datetime.now()).total_seconds() / 60
                if elapsed > 1:
                    log_focus_time_mongo(st.session_state.username, int(elapsed))
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
                if not st.session_state.timer_active:
                    focus_minutes = st.number_input("Minutes", min_value=1, max_value=120, value=25)
                    if st.button("🚀 Start Timer", use_container_width=True):
                        start_timer(focus_minutes)
                        st.rerun()
                else:
                    remaining = st.session_state.end_time - datetime.now()
                    if remaining.total_seconds() <= 0:
                        log_focus_time_mongo(st.session_state.username, st.session_state.timer_minutes)
                        st.session_state.timer_active = False
                        st.success("⏰ Time's up! Great focus session.")
                        st.balloons()
                        if st.button("Reset Timer", use_container_width=True):
                            st.rerun()
                    else:
                        mins, secs = divmod(int(remaining.total_seconds()), 60)
                        st.markdown(f"<h1 style='text-align: center; color: #ff4b4b;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
                        st.info("Timer is running in the background.")
                        c1, c2 = st.columns(2)
                        with c1: 
                            if st.button("🔄 Refresh", use_container_width=True): st.rerun()
                        with c2: 
                            if st.button("⏹️ Stop", use_container_width=True):
                                stop_timer()
                                st.rerun()

        with right_col:
            st.subheader("📋 Build Your Routine")
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
                    if not pending_tasks:
                        st.success("You are all caught up for today! 🎉")
                    else:
                        for task_dict in pending_tasks:
                            with st.container(border=True):
                                col_chk, col_time, col_task, col_pri, col_del = st.columns([0.5, 1.5, 3, 1, 0.5])
                                with col_chk:
                                    is_checked = st.checkbox("", value=task_dict["completed"], key=f"chk_p_{task_dict['id']}")
                                    if is_checked:
                                        update_task_status(task_dict["id"], True)
                                        st.toast(f"Completed: {task_dict['task']}!", icon="🎉")
                                        st.rerun()
                                with col_time: st.write(f"🕰️ **{task_dict['time']}**")
                                with col_task: st.write(task_dict["task"])
                                with col_pri: st.write(task_dict['priority'])
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
        
        existing_goals = {}
        if MONGO_AVAILABLE:
            existing_goals = goals_col.find_one({"username": st.session_state.username}) or {}
            
        acad = existing_goals.get("academic", ["", ""]) + ["", ""]
        pers = existing_goals.get("personal", ["", ""]) + ["", ""]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Academic Goals")
            acad1 = st.text_input("Goal 1", value=acad[0], key="acad1")
            acad2 = st.text_input("Goal 2", value=acad[1], key="acad2")
        with col2:
            st.subheader("Personal Goals")
            pers1 = st.text_input("Goal 1", value=pers[0], key="pers1")
            pers2 = st.text_input("Goal 2", value=pers[1], key="pers2")
            
        if st.button("Save Goals"):
            if MONGO_AVAILABLE:
                save_weekly_goals_mongo(st.session_state.username, {
                    "academic": [acad1, acad2], "personal": [pers1, pers2], "updated_at": datetime.now()
                })
                st.success("Goals saved securely to MongoDB profile!")
            else:
                st.error("Cannot save: MongoDB is not connected.")

    # --- PAGE 5: DAILY REFLECTION ---
    elif page == "Daily Reflection":
        st.title("📝 Daily Reflection")
        
        existing_ref = {}
        if MONGO_AVAILABLE:
            existing_ref = reflections_col.find_one({"username": st.session_state.username, "date": str(date.today())}) or {}

        score = st.slider("How productive do you feel you were today?", 1, 10, existing_ref.get("score", 5))
        went_well = st.text_area("What went well today?", existing_ref.get("went_well", ""))
        improve = st.text_area("What could be improved tomorrow?", existing_ref.get("improve", ""))
        
        if st.button("Submit Reflection"):
            if MONGO_AVAILABLE:
                save_reflection_mongo(st.session_state.username, {
                    "score": score, "went_well": went_well, "improve": improve, "submitted_at": datetime.now()
                })
                st.success("Reflection saved! Self-awareness is the first step to continuous improvement.")
            else:
                st.error("Cannot save: MongoDB is not connected.")

    # --- PAGE 6: NOTIFICATIONS & SETTINGS ---
    elif page == "Notifications & Settings":
        st.title("🔔 Automated Notification System")
        st.write("Manage your email alerts and push notifications for your daily routines.")
        
        # Get user data from MongoDB
        user_data = None
        if MONGO_AVAILABLE:
            user_data = users_col.find_one({"username": st.session_state.username})
            
        email = user_data.get("email", "") if user_data else ""
        notifications_enabled = user_data.get("notifications_enabled", False) if user_data else False
        
        with st.container(border=True):
            st.subheader("Email Preferences")
            new_email = st.text_input("Registered Email Address", value=email)
            enable_alerts = st.toggle("Enable Daily Summary & Alerts", value=notifications_enabled)
            
            if st.button("Update Settings"):
                if MONGO_AVAILABLE:
                    users_col.update_one(
                        {"username": st.session_state.username}, 
                        {"$set": {"email": new_email, "notifications_enabled": enable_alerts}}
                    )
                    st.success("Settings updated successfully!")
                else:
                    st.error("Cannot update settings: MongoDB is not connected.")
                
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
