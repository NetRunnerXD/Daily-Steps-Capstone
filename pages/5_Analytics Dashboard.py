import streamlit as st
import pandas as pd
from backend import *

if not st.session_state.get("logged_in"):
    st.warning("Please log in from the Home page first.")
    st.stop()

render_sidebar()

st.title("📊 Insights & Analytics")
st.markdown("Track your progress, focus time, and productivity trends over time.")

if MONGO_AVAILABLE:
    history_cursor = history_col.find({"username": st.session_state.username}).sort("logged_at", 1)
    history_data = list(history_cursor)
    
    if not history_data:
        st.info("No data yet! Complete a day using the 'Checkout' button to see your insights.")
    else:
        df = pd.DataFrame(history_data)
        df['logged_at'] = pd.to_datetime(df['logged_at'], utc=True, errors='coerce')
        df = df.dropna(subset=['logged_at'])
        
        df['display_date'] = df['logged_at'].dt.strftime('%b %d')
        df['day_of_week'] = df['logged_at'].dt.day_name()
        
        time_filter = st.radio("⏳ Time Range:", ["Last 7 Days", "Last 30 Days", "All Time"], horizontal=True)
        if time_filter == "Last 7 Days":
            df = df.tail(7)
        elif time_filter == "Last 30 Days":
            df = df.tail(30)

        if df.empty:
            st.warning("No data found for this specific time range.")
        else:
            st.markdown("### 🏆 Performance Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                with st.container(border=True):
                    st.metric("Total Focus Mins", f"{df['focus_minutes'].sum()}m")
            with col2:
                with st.container(border=True):
                    st.metric("Daily Avg Focus", f"{int(df['focus_minutes'].mean())}m")
            with col3:
                with st.container(border=True):
                    st.metric("Tasks Completed", df['tasks_completed'].sum())
            with col4:
                with st.container(border=True):
                    avg_completion = int((df['tasks_completed'].sum() / df['total_tasks'].sum()) * 100) if df['total_tasks'].sum() > 0 else 0
                    st.metric("Avg Completion Rate", f"{avg_completion}%")
            
            st.divider()
            
            c_chart1, c_chart2 = st.columns(2)
            
            with c_chart1:
                st.subheader("⏱️ Focus Time Trend")
                focus_chart_data = df.set_index('display_date')['focus_minutes']
                st.area_chart(focus_chart_data, color="#8B5CF6") 
                
            with c_chart2:
                st.subheader("📋 Task Completion vs Assigned")
                task_chart_data = df[['display_date', 'tasks_completed', 'total_tasks']].set_index('display_date')
                task_chart_data = task_chart_data.rename(columns={'tasks_completed': 'Completed', 'total_tasks': 'Assigned'})
                st.line_chart(task_chart_data, color=["#10B981", "#EF4444"]) 

            st.divider()
            
            st.subheader("🧠 Deep Insights")
            
            best_day = df.groupby('day_of_week')['focus_minutes'].mean().idxmax()
            highest_focus = df['focus_minutes'].max()
            best_date = df.loc[df['focus_minutes'].idxmax()]['display_date']
            
            i1, i2 = st.columns(2)
            with i1:
                st.info(f"📅 **Best Focus Day:** You average the most focus time on **{best_day}s**.")
            with i2:
                st.success(f"🔥 **Record Focus:** Your highest focus time was **{highest_focus}m** on {best_date}.")
else:
    st.error("Cannot load analytics: MongoDB is not connected.")