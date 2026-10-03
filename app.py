import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

from db import init_db, add_subject, get_subjects, add_topic, get_topics, add_session, get_sessions
from planner import add_scores, build_schedule

st.set_page_config(page_title="AI Study Planner", page_icon="🎓", layout="wide")
init_db()

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.card {padding: 18px; border-radius: 16px; background: rgba(127,127,127,0.08); border: 1px solid rgba(127,127,127,0.15);}
.big {font-size: 2rem; font-weight: 800;}
.small {opacity: .7; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

subjects = get_subjects()
topics = get_topics()
sessions = get_sessions()

with st.sidebar:
    st.title("🎓 AI Study Planner")
    page = st.radio("Navigate", ["Dashboard", "Subjects & Topics", "Planner", "Analytics", "Study Session"])
    st.divider()
    daily_hours = st.number_input("Daily study hours", min_value=0.5, max_value=12.0, value=3.0, step=0.5)

if page == "Dashboard":
    st.title("Good morning 👋")
    scored = add_scores(topics)
    total_est = sum(t["estimated_minutes"] for t in scored) or 1
    total_done = sum(t["completed_minutes"] for t in scored)
    progress = total_done / total_est * 100
    today_sessions = [s for s in sessions if s["session_date"] == date.today().isoformat()]
    today_minutes = sum(s["minutes"] for s in today_sessions)
    exams = [pd.to_datetime(t["exam_date"]).date() for t in topics]
    next_exam = min([d for d in exams if d >= date.today()], default=None)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Today's study", f"{today_minutes // 60}h {today_minutes % 60}m")
    c2.metric("Overall progress", f"{progress:.0f}%")
    c3.metric("Topics", len(topics))
    c4.metric("Next exam", next_exam.strftime("%d %b") if next_exam else "—")

    st.subheader("🔥 Today's recommended plan")
    schedule = build_schedule(topics, int(daily_hours * 60))
    if schedule:
        for i, item in enumerate(schedule, 1):
            st.markdown(f"**{i}. {item['subject']} — {item['topic']}**  ·  {item['minutes']} min  ")
            st.caption(f"Priority {item['priority']}/100 · {item['reason']}")
    else:
        st.success("You're caught up! Add more topics or enjoy your free time.")

    if scored:
        df = pd.DataFrame(scored).sort_values("priority", ascending=True)
        fig = px.bar(df, x="priority", y="name", orientation="h", title="Topic priority")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start by adding subjects and topics from the sidebar.")

elif page == "Subjects & Topics":
    st.title("📚 Subjects & Topics")
    left, right = st.columns(2)
    with left:
        st.subheader("Add subject")
        with st.form("subject_form"):
            name = st.text_input("Subject name")
            color = st.color_picker("Accent color", "#4F46E5")
            if st.form_submit_button("Add subject"):
                if name.strip():
                    add_subject(name, color)
                    st.success("Subject added")
                    st.rerun()

    with right:
        st.subheader("Add topic")
        subject_list = get_subjects()
        if not subject_list:
            st.info("Add a subject first.")
        else:
            mapping = {s["name"]: s["id"] for s in subject_list}
            with st.form("topic_form"):
                subject_name = st.selectbox("Subject", list(mapping))
                topic_name = st.text_input("Topic")
                exam_date = st.date_input("Exam date", min_value=date.today())
                difficulty = st.slider("Difficulty", 1, 5, 3)
                confidence = st.slider("Confidence", 0, 100, 50)
                importance = st.slider("Importance", 1, 5, 3)
                estimated = st.number_input("Estimated study minutes", 15, 600, 60, step=15)
                if st.form_submit_button("Add topic"):
                    if topic_name.strip():
                        add_topic(mapping[subject_name], topic_name, exam_date, difficulty, confidence, importance, int(estimated))
                        st.success("Topic added")
                        st.rerun()

    st.subheader("All topics")
    if topics:
        rows = []
        for t in topics:
            rows.append({
                "Subject": t["subject_name"], "Topic": t["name"], "Exam": t["exam_date"],
                "Difficulty": t["difficulty"], "Confidence": f"{t['confidence']}%",
                "Progress": f"{min(100, t['completed_minutes']/max(t['estimated_minutes'],1)*100):.0f}%",
                "Status": t["status"]
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No topics yet.")

elif page == "Planner":
    st.title("🧠 Adaptive Planner")
    col1, col2 = st.columns(2)
    with col1:
        plan_date = st.date_input("Plan date", date.today())
    with col2:
        minutes = st.number_input("Available minutes", 30, 720, int(daily_hours * 60), step=15)
    if st.button("Generate adaptive plan", type="primary"):
        schedule = build_schedule(topics, int(minutes), plan_date)
        if schedule:
            st.session_state["schedule"] = schedule
        else:
            st.warning("No pending topics fit the selected time.")
    schedule = st.session_state.get("schedule", [])
    if schedule:
        for i, item in enumerate(schedule, 1):
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.markdown(f"### {i}. {item['subject']} — {item['topic']}")
                c1.caption(item["reason"])
                c2.metric("Minutes", item["minutes"])
                c3.metric("Priority", item["priority"])

elif page == "Analytics":
    st.title("📈 Analytics")
    if not sessions:
        st.info("Record a study session to unlock analytics.")
    else:
        sdf = pd.DataFrame([dict(s) for s in sessions])
        sdf["session_date"] = pd.to_datetime(sdf["session_date"])
        daily = sdf.groupby("session_date", as_index=False)["minutes"].sum()
        fig = px.line(daily, x="session_date", y="minutes", markers=True, title="Study minutes over time")
        st.plotly_chart(fig, use_container_width=True)
        subject_minutes = sdf.groupby("subject_name", as_index=False)["minutes"].sum().sort_values("minutes", ascending=False)
        fig2 = px.bar(subject_minutes, x="subject_name", y="minutes", title="Study time by subject")
        st.plotly_chart(fig2, use_container_width=True)

elif page == "Study Session":
    st.title("⏱️ Record Study Session")
    if not topics:
        st.info("Add topics first.")
    else:
        mapping = {f"{t['subject_name']} — {t['name']}": t["id"] for t in topics}
        selected = st.selectbox("Topic", list(mapping))
        minutes = st.slider("Minutes studied", 5, 180, 30, step=5)
        session_date = st.date_input("Date", date.today())
        if st.button("Save session", type="primary"):
            add_session(mapping[selected], session_date, minutes)
            st.success("Study session recorded ✅")
            st.rerun()
