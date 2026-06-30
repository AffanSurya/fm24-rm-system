import streamlit as st

st.set_page_config(
    page_title="FM24 AI Scout",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ FM24 AI Recommendation Engine")
st.markdown("""
Welcome to the Football Manager 24 Machine Learning Scouting Dashboard.

### Features
- **Squad Matrix**: Analyze your current squad depth and retention signals.
- **Transfer Optimizer**: Find the Pareto-optimal candidates for any role using Multi-Objective Optimization.
- **Data Ingestion**: Upload raw FM exports to process them through the pipeline.
- **Tactical Config**: Tweak the underlying mathematical weights for specific player roles.

👈 **Select a module from the sidebar to begin.**
""")
