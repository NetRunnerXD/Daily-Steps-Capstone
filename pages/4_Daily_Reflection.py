import streamlit as st
from datetime import datetime, date
from backend import *

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the Home page first.")
    st.stop()

render_sidebar()

st.title("📝 Daily Reflection & Journal")

tab_write, tab_history = st.tabs(["✍️ Write Today's Entry", "📖 Past Journals"])

with tab_write:
    existing_ref = reflections_col.find_one({"username": st.session_state.username, "date": str(date.today())}) or {} if MONGO_AVAILABLE else {}

    st.write("Take a few minutes to evaluate your day and clear your mind.")
    
    score = st.slider("Productivity Score (1-10)", 1, 10, existing_ref.get("score", 5))
    
    c1, c2 = st.columns(2)
    with c1:
        went_well = st.text_area("What went well today?", existing_ref.get("went_well", ""), height=100)
    with c2:
        improve = st.text_area("What could be improved tomorrow?", existing_ref.get("improve", ""), height=100)
    
    st.divider()
    
    st.subheader("📓 Dear Diary...")
    diary_entry = st.text_area(
        "Write whatever is on your mind.", 
        existing_ref.get("diary_entry", ""), 
        height=200, 
        placeholder="Today I felt really good about..."
    )
    
    if st.button("Submit Reflection & Journal", type="primary"):
        if MONGO_AVAILABLE:
            save_reflection_mongo(st.session_state.username, {
                "score": score, 
                "went_well": went_well, 
                "improve": improve, 
                "diary_entry": diary_entry,
                "submitted_at": datetime.now()
            })
            st.success("Entry saved! Self-awareness is the first step to continuous improvement.")
            st.balloons()
        else:
            st.error("Cannot save: MongoDB is not connected.")

with tab_history:
    st.subheader("Your Past Journals")
    if MONGO_AVAILABLE:
        past_refs = list(reflections_col.find({"username": st.session_state.username}).sort("date", -1).limit(10))
        
        if not past_refs:
            st.info("No past journals found. Your journey starts today!")
        else:
            for ref in past_refs:
                with st.expander(f"📅 {ref['date']} - Productivity: {ref.get('score', 'N/A')}/10"):
                    st.write("**What went well:**")
                    st.write(f"> {ref.get('went_well', 'Nothing entered.')}")
                    st.write("**What to improve:**")
                    st.write(f"> {ref.get('improve', 'Nothing entered.')}")
                    
                    diary_text = ref.get('diary_entry', '').strip()
                    if diary_text:
                        st.divider()
                        st.write("**📓 Dear Diary:**")
                        st.write(f"> *{diary_text}*")
    else:
        st.warning("MongoDB not connected. History unavailable.")