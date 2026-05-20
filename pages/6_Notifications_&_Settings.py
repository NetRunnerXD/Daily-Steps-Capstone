import streamlit as st
import time
import sqlite3
import pandas as pd
from backend import *

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the Home page first.")
    st.stop()

render_sidebar()

st.title("⚙️ Settings & Account Security")

with st.container(border=True):
    st.subheader("🔐 Account Security")
    col_u, col_p = st.columns(2)
    
    with col_u:
        st.write("**Change Username**")
        new_u = st.text_input("New Username", placeholder="Enter new username")
        if st.button("Update Username", use_container_width=True):
            if new_u.strip():
                success = update_user_username(st.session_state.username, new_u)
                if success:
                    st.session_state.username = new_u
                    st.success(f"Username changed to {new_u}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("This username is already taken.")
            else:
                st.warning("Username cannot be empty.")

    with col_p:
        st.write("**Change Password**")
        new_p = st.text_input("New Password", type="password", placeholder="Enter new password")
        confirm_p = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password", use_container_width=True, type="primary"):
            if new_p == confirm_p and len(new_p) >= 4:
                update_user_password(st.session_state.username, new_p)
                st.success("Password updated successfully!")
            elif len(new_p) < 4:
                st.error("Password must be at least 4 characters.")
            else:
                st.error("Passwords do not match.")

st.write("") 

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("🔔 Automated Alerts")
        conn = sqlite3.connect('daily_steps.db')
        c = conn.cursor()
        c.execute('SELECT email, notifications_enabled FROM users WHERE username = ?', (st.session_state.username,))
        user_data = c.fetchone()
        
        email = user_data[0] if user_data else ""
        notif_on = bool(user_data[1]) if user_data else False
        
        new_email = st.text_input("Registered Email", value=email)
        enable_alerts = st.toggle("Enable Daily Summary Emails", value=notif_on)
        
        if st.button("Update Alert Settings", use_container_width=True):
            c.execute('UPDATE users SET email = ?, notifications_enabled = ? WHERE username = ?', 
                      (new_email, int(enable_alerts), st.session_state.username))
            conn.commit()
            st.success("Alert settings updated!")
        conn.close()

with col2:
    with st.container(border=True):
        st.subheader("💾 Data Management")
        st.write("Export your historical data for your own records.")
        
        if st.button("📥 Download My Data (CSV)", use_container_width=True):
            if MONGO_AVAILABLE:
                export_data = list(history_col.find({"username": st.session_state.username}, {"_id": 0}))
                if export_data:
                    df_export = pd.DataFrame(export_data)
                    csv = df_export.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", data=csv, file_name=f"{st.session_state.username}_history.csv", mime='text/csv', use_container_width=True)
                else:
                    st.info("No data found to export.")
            else:
                st.error("MongoDB not connected.")