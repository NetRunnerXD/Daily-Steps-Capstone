import streamlit as st
import time
from datetime import datetime
from backend import *

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the Home page first.")
    st.stop()

render_sidebar()

st.title("🎯 Weekly Goals")
st.markdown("Set your macro targets for the week. Cross them off as you go to fill your progress bars!")

existing_goals = {}
if MONGO_AVAILABLE:
    existing_goals = goals_col.find_one({"username": st.session_state.username}) or {}

def format_goals(goal_list):
    if not goal_list:
        return [{"text": "", "done": False}]
    
    formatted = []
    for g in goal_list:
        if isinstance(g, str):   
            formatted.append({"text": g, "done": False})
        elif isinstance(g, dict): 
            formatted.append(g)
        else:                     
            formatted.append({"text": str(g) if g else "", "done": False})
            
    return formatted

if 'acad_goals' in st.session_state and len(st.session_state.acad_goals) > 0 and isinstance(st.session_state.acad_goals[0], str):
    del st.session_state['acad_goals']
if 'pers_goals' in st.session_state and len(st.session_state.pers_goals) > 0 and isinstance(st.session_state.pers_goals[0], str):
    del st.session_state['pers_goals']

if 'acad_goals' not in st.session_state:
    st.session_state.acad_goals = format_goals(existing_goals.get("academic", []))
if 'pers_goals' not in st.session_state:
    st.session_state.pers_goals = format_goals(existing_goals.get("personal", []))

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("📚 Academic Goals")
        
        total_acad = len(st.session_state.acad_goals)
        done_acad = sum(1 for g in st.session_state.acad_goals if g["done"])
        acad_prog = done_acad / total_acad if total_acad > 0 else 0.0
        st.progress(acad_prog, text=f"Progress: {done_acad} / {total_acad} Completed")
        st.write("") 
        
        for i in range(len(st.session_state.acad_goals)):
            c1, c2, c3 = st.columns([0.15, 0.7, 0.15])
            
            st.session_state.acad_goals[i]["done"] = c1.checkbox("", value=st.session_state.acad_goals[i].get("done", False), key=f"ac_chk_{i}")
            
            is_done = st.session_state.acad_goals[i]["done"]
            st.session_state.acad_goals[i]["text"] = c2.text_input(
                f"Goal {i+1}", 
                value=st.session_state.acad_goals[i].get("text", ""), 
                key=f"ac_txt_{i}", 
                label_visibility="collapsed",
                disabled=is_done
            )
            
            if c3.button("✖", key=f"ac_del_{i}", help="Delete Goal"):
                st.session_state.acad_goals.pop(i)
                st.rerun()
        
        if st.button("➕ Add Academic Goal", use_container_width=True):
            st.session_state.acad_goals.append({"text": "", "done": False})
            st.rerun()

with col2:
    with st.container(border=True):
        st.subheader("🌱 Personal Goals")
        
        total_pers = len(st.session_state.pers_goals)
        done_pers = sum(1 for g in st.session_state.pers_goals if g["done"])
        pers_prog = done_pers / total_pers if total_pers > 0 else 0.0
        st.progress(pers_prog, text=f"Progress: {done_pers} / {total_pers} Completed")
        st.write("") 
        
        for i in range(len(st.session_state.pers_goals)):
            c1, c2, c3 = st.columns([0.15, 0.7, 0.15])
            
            st.session_state.pers_goals[i]["done"] = c1.checkbox("", value=st.session_state.pers_goals[i].get("done", False), key=f"pe_chk_{i}")
            
            is_done = st.session_state.pers_goals[i]["done"]
            st.session_state.pers_goals[i]["text"] = c2.text_input(
                f"Goal {i+1}", 
                value=st.session_state.pers_goals[i].get("text", ""), 
                key=f"pe_txt_{i}", 
                label_visibility="collapsed",
                disabled=is_done
            )
            
            if c3.button("✖", key=f"pe_del_{i}", help="Delete Goal"):
                st.session_state.pers_goals.pop(i)
                st.rerun()
        
        if st.button("➕ Add Personal Goal", use_container_width=True):
            st.session_state.pers_goals.append({"text": "", "done": False})
            st.rerun()
    
st.write("")
if st.button("💾 Save Weekly Goals", type="primary", use_container_width=True):
    if MONGO_AVAILABLE:
        clean_acad = [g for g in st.session_state.acad_goals if g["text"].strip()]
        clean_pers = [g for g in st.session_state.pers_goals if g["text"].strip()]
        
        save_weekly_goals_mongo(st.session_state.username, {
            "academic": clean_acad, 
            "personal": clean_pers, 
            "updated_at": datetime.now()
        })
        
        st.session_state.acad_goals = clean_acad if clean_acad else [{"text": "", "done": False}]
        st.session_state.pers_goals = clean_pers if clean_pers else [{"text": "", "done": False}]
        
        st.success("Weekly Goals locked in! Go crush them.")
        st.balloons()
        time.sleep(1)
        st.rerun()
    else:
        st.error("Cannot save: MongoDB is not connected.")