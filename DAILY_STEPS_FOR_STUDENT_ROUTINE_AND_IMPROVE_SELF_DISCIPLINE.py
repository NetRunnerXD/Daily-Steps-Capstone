import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="DAILY STEPS - FOR STUDENT ROUTINE AND IMPROVE SELF DISCIPLINE", page_icon="📚")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
# Added "Weekly Goals" and "Daily Reflection" to the radio list
page = st.sidebar.radio("Go to:", [
    "Home", 
    "Daily Routine Checklist", 
    "Tips for Self-Discipline",
    "Weekly Goals",
    "Daily Reflection"
])

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
    st.title("⏰ Your Daily Routine")
    st.write("Check off your steps as you complete them today!")
    
    st.subheader("Morning Setup")
    st.checkbox("06:00 AM - Wake up immediately (No hitting snooze!)")
    st.checkbox("06:15 AM - Drink a glass of water & stretch")
    st.checkbox("06:30 AM - Review today's goals and classes")
    
    st.subheader("Academic Focus")
    st.checkbox("09:00 AM - Attend classes / Deep study session 1")
    st.checkbox("01:00 PM - Healthy lunch & brain break")
    st.checkbox("03:00 PM - Deep study session 2 (Review notes)")
    
    st.subheader("Evening Wind Down")
    st.checkbox("06:00 PM - Exercise or walk outside")
    st.checkbox("08:00 PM - Pack bag for tomorrow & organize desk")
    st.checkbox("10:00 PM - Read a book (No screens) & Sleep")
    
    st.success("Consistency is key! Try to check off as many as you can each day.")

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