import streamlit as st
import sqlite3
from backend import *

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="DAILY STEPS", page_icon="📚", layout="wide")

if not MONGO_AVAILABLE:
    st.sidebar.warning("⚠️ Could not connect to MongoDB. Goals, Reflections, and Focus Time will not be saved permanently.")

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""

# --- AUTHENTICATION UI ---
if not st.session_state.logged_in:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            [data-testid="collapsedControl"] { display: none; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center;'>🔒 Welcome to Daily Steps</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Build your routine, master self-discipline, and track your progress.</p>", unsafe_allow_html=True)
    st.write("") 
    
    col_spacer1, col_auth, col_spacer2 = st.columns([1, 1.5, 1])
    with col_auth:
        with st.container(border=True):
            tab_login, tab_signup = st.tabs(["🔑 Login", "📝 Sign Up"])
            
            with tab_login:
                st.subheader("Welcome Back")
                login_username = st.text_input("Username", key="login_user")
                login_password = st.text_input("Password", type='password', key="login_pass")
                
                if st.button("Login", use_container_width=True, type="primary"):
                    if login_user(login_username, login_password):
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.rerun()
                    else:
                        st.error("Incorrect Username or Password")
                        
            with tab_signup:
                st.subheader("Create an Account")
                new_user = st.text_input("Choose a Username", key="reg_user")
                new_email = st.text_input("Email Address", key="reg_email")
                new_password = st.text_input("Choose a Password", type='password', key="reg_pass")
                
                if st.button("Sign Up", use_container_width=True):
                    if not new_user or not new_password:
                        st.warning("Please fill out all fields.")
                    else:
                        conn = sqlite3.connect('daily_steps.db')
                        c = conn.cursor()
                        c.execute('SELECT * FROM users WHERE username = ?', (new_user,))
                        if c.fetchone():
                            st.error("Username already exists.")
                        else:
                            add_user(new_user, new_password, new_email)
                            st.success("Account created successfully! Switch to the Login tab.")
                            st.balloons()
                        conn.close()

# --- MAIN APPLICATION (Logged In) ---
else:
    # --- RENDER SIDEBAR & LOGOUT ---
    render_sidebar()

    # --- HOME PAGE ---
    st.title("📚 Daily Steps for Students")
    st.subheader("Build a strong routine and master self-discipline.")
    st.write("""
    Welcome to your personal growth tracker! As a student, building a solid daily routine 
    is the foundation of academic success and reduced stress. 
    """)
    st.image("https://images.unsplash.com/photo-1434030216411-0b793f4b4173?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", caption="Focus and build your future.")