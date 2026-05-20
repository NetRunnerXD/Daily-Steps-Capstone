import sqlite3
import hashlib
from datetime import datetime, date
import pymongo
import streamlit as st

# ==========================================
# 1. DATABASE SETUP (Polyglot Persistence)
# ==========================================

# --- A. SQLite Setup (Relational Data: Users & Tasks) ---
def init_sqlite_db():
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, password TEXT, email TEXT, notifications_enabled INTEGER
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY, username TEXT, task TEXT, time TEXT, priority TEXT, completed INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_sqlite_db()

# --- B. MongoDB Setup (Document Data) ---
try:
    MONGO_URI = st.secrets["MONGO_URI"] 
    mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    mongo_client.server_info() 
    mongo_db = mongo_client["daily_steps_db"]
    focus_col = mongo_db["focus_logs"]
    goals_col = mongo_db["weekly_goals"]
    reflections_col = mongo_db["reflections"]
    history_col = mongo_db["daily_history"] 
    gamification_col = mongo_db["gamification"]
    MONGO_AVAILABLE = True
except (pymongo.errors.ServerSelectionTimeoutError, KeyError):
    MONGO_AVAILABLE = False
    focus_col = goals_col = reflections_col = history_col = gamification_col = None

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

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
    if data: return check_hashes(password, data[0])
    return False

def add_task(task_id, username, task, time_str, priority, completed=0):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?)', (task_id, username, task, time_str, priority, completed))
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

def edit_task_details(task_id, new_task, new_time_str, new_priority):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('UPDATE tasks SET task = ?, time = ?, priority = ? WHERE id = ?', 
              (new_task, new_time_str, new_priority, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

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

def get_gamification(username):
    if not MONGO_AVAILABLE: return {"xp": 0, "level": 1, "streak": 0}
    profile = gamification_col.find_one({"username": username})
    if not profile:
        profile = {"username": username, "xp": 0, "level": 1, "streak": 0, "last_checkout": None}
        gamification_col.insert_one(profile)
    return profile

def add_xp(username, xp_amount):
    if not MONGO_AVAILABLE: return False
    profile = get_gamification(username)
    new_xp = profile["xp"] + xp_amount
    new_level = (new_xp // 100) + 1 
    
    gamification_col.update_one(
        {"username": username},
        {"$set": {"xp": new_xp, "level": new_level}}
    )
    return new_level > profile["level"] 

def update_streak_on_checkout(username):
    if not MONGO_AVAILABLE: return
    profile = get_gamification(username)
    today_date = date.today()
    
    last_checkout_str = profile.get("last_checkout")
    
    if last_checkout_str:
        last_checkout_date = datetime.strptime(last_checkout_str, "%Y-%m-%d").date()
        delta = (today_date - last_checkout_date).days
        
        if delta == 1:
            new_streak = profile["streak"] + 1 
        elif delta == 0:
            new_streak = profile["streak"] 
        else:
            new_streak = 1 
    else:
        new_streak = 1 
        
    gamification_col.update_one(
        {"username": username},
        {"$set": {"streak": new_streak, "last_checkout": str(today_date)}}
    )

def get_rank_title(level):
    if level < 5: return "Novice Planner 🥉"
    elif level < 10: return "Focused Scholar 🥈"
    elif level < 25: return "Discipline Master 🥇"
    elif level < 50: return "Productivity Ninja 🥷"
    else: return "Grandmaster 👑"

@st.dialog("🌟 LEVEL UP!")
def level_up_popup(level, title):
    st.balloons()
    st.markdown(f"<h1 style='text-align: center; color: #FFD700;'>Congratulations!</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>You've reached Level {level}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; font-size: 20px;'>New Rank: <b>{title}</b></p>", unsafe_allow_html=True)
    st.write("---")
    st.write("Your dedication to your routine is paying off. Keep building those habits!")
    if st.button("Awesome! Let's keep going", use_container_width=True):
        st.rerun()

def update_user_password(username, new_password):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE username = ?', (make_hashes(new_password), username))
    conn.commit()
    conn.close()

def update_user_username(old_username, new_username):
    conn = sqlite3.connect('daily_steps.db')
    c = conn.cursor()
    
    c.execute('SELECT username FROM users WHERE username = ?', (new_username,))
    if c.fetchone():
        conn.close()
        return False 
    
    c.execute('UPDATE users SET username = ? WHERE username = ?', (new_username, old_username))
    c.execute('UPDATE tasks SET username = ? WHERE username = ?', (new_username, old_username))
    conn.commit()
    conn.close()

    if MONGO_AVAILABLE:
        collections = [focus_col, goals_col, reflections_col, history_col, gamification_col]
        for col in collections:
            col.update_many({"username": old_username}, {"$set": {"username": new_username}})
    
    return True

def render_sidebar():
    if st.session_state.get("logged_in"):
        user_stats = get_gamification(st.session_state.username)
        rank_title = get_rank_title(user_stats['level'])
        progress_to_next = (user_stats['xp'] % 100)

        st.sidebar.markdown("""
            <style>
                [data-testid="stSidebarNav"] {
                    order: 2 !important;
                }
                [data-testid="stVerticalBlock"] > div:has(div.nav-wrapper) {
                    order: 1 !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # 1. Profile and Level System Container
        with st.sidebar.container():
            st.markdown(f"## 👤 {st.session_state.username}")
            st.markdown(f"### {rank_title}")
            st.markdown(f"**Level {user_stats['level']}** | 🔥 **{user_stats['streak']} Day Streak**")
            st.progress(progress_to_next / 100.0, text=f"XP: {user_stats['xp']} / 500")
            st.write("")
            
        # 2. Logout Button (Stays at the very bottom)
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.switch_page("0_🏠_Home.py")