import streamlit as st
import sqlite3
import uuid
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
            /* 1. Nuke the sidebar and header */
            [data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stHeader"] { 
                display: none !important; 
            }
            
            /* 2. Attach Background Image */
            .stApp {
                background-image: url("https://images.unsplash.com/photo-1653324101493-254c64719ba9?q=100&w=3840&auto=format&fit=crop");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }
            
            /* 3. Glass UI*/
            .block-container {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%) !important;
                backdrop-filter: blur(5px) saturate(180%) !important;
                -webkit-backdrop-filter: blur(5px) saturate(180%) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-top: 1px solid rgba(255, 255, 255, 0.2) !important; /* Premium light edge reflection */
                border-radius: 24px !important;
                box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4) !important;
                
                /* Sculpted Proportions */
                max-width: 420px !important; /* Slimmed down from 550px for a sleek phone-like aspect ratio */
                margin-top: 12vh !important;
                padding: 40px !important;
            }
            
            /* 4. Strip default form borders */
            [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
            }
            
            /* 5. Premium Input Fields (Rounded and darkened) */
            input {
                background-color: rgba(0, 0, 0, 0.2) !important;
                color: #ffffff !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
                border-radius: 12px !important;
                padding: 12px 16px !important;
                transition: all 0.3s ease !important;
            }
            input:focus {
                border-color: rgba(255, 255, 255, 0.4) !important;
                background-color: rgba(0, 0, 0, 0.4) !important;
                box-shadow: 0 0 10px rgba(255, 255, 255, 0.1) !important;
            }
            
            /* 6. Standard Buttons */
            .stButton > button {
                width: 100% !important;
                background: rgba(255, 255, 255, 0.05) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                color: white !important;
                border-radius: 12px !important;
                padding: 10px !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }
            .stButton > button:hover {
                background: rgba(255, 255, 255, 0.15) !important;
                transform: translateY(-2px) !important;
            }
            
            /* 7. Primary Action Button (Login/Signup) */
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #4F46E5, #7C3AED) !important; /* Deep indigo to purple */
                border: none !important;
                box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
            }
            .stButton > button[kind="primary"]:hover {
                box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6) !important;
                transform: translateY(-2px) !important;
            }
            
            /* 8. Crisp Typography */
            label, p, h1, h2, h3, span, .stTabs [data-baseweb="tab"] {
                color: #ffffff !important;
                text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.4) !important;
            }
            /* MOBILE RESPONSIVENESS PATCH */
            @media (max-width: 768px) {
                /* Fix the zoomed-in background glitch on phones */
                .stApp {
                    background-attachment: scroll !important; 
                    background-position: center top !important;
                }
                
                /* Shrink the glass card layout to fit small screens perfectly */
                .block-container {
                    max-width: 92% !important; /* Take up most of the phone screen width */
                    margin-top: 6vh !important; /* Push it slightly higher up */
                    padding: 24px !important; /* Reduce padding so input boxes have room to breathe */
                    border-radius: 18px !important;
                }
                
                /* Ensure tabs don't overflow */
                .stTabs [data-baseweb="tab-list"] {
                    gap: 0px;
                }
                .stTabs [data-baseweb="tab"] {
                    font-size: 14px !important;
                }
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='text-align: center;'>Welcome to Daily Steps</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Build your routine, master self-discipline, and track your progress.</p>", unsafe_allow_html=True)
    st.write("") 
    
    
    tab_login, tab_signup = st.tabs(["🔑 Login", "📄 Sign Up"])
            
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
                    
    # 🟢 FIXED: Un-indented to align completely with 'with tab_login:'
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