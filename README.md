# AI Study Planner

A 2nd-year B.Tech-friendly adaptive study planner built with Python + Streamlit + SQLite + Plotly.

## Features
- Subject and topic management
- Exam dates, difficulty, confidence and importance
- Adaptive priority scoring
- Automatic daily study plan
- Progress tracking
- Study-session logging
- Analytics dashboard
- Local SQLite database

## Run
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The database is created automatically as `study_planner.db`.

## Viva idea
The planner's priority engine combines exam urgency, difficulty, low confidence, importance and remaining work into a weighted score. The scheduler then greedily allocates available daily minutes to the highest-priority incomplete topics.
