import streamlit as st
from backend import *

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the Home page first.")
    st.stop()

render_sidebar()

st.title("🧠 Improving Self-Discipline")
st.write("Self-discipline is a muscle. The more you use it, the stronger it gets.")

with st.expander("1. The 5-Minute Rule"):
    st.write("If a task takes less than 5 minutes to do, do it immediately.")

with st.expander("2. Put Your Phone in Another Room"):
    st.write("Out of sight, out of mind. Eliminate the temptation to scroll.")

with st.expander("3. Use the Pomodoro Technique"):
    st.write("Study for 25 minutes, then take a 5-minute break.")