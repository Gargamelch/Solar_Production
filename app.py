# This page set all pages up
# It doesn't do anything else beside that
# Import
import streamlit as st

# Set global config
st.set_page_config(page_title="Solar France", layout="wide")


try:
    # Define pages
    page_dashboard = st.Page(
        "pages/0_Dashboard.py",
        title="Dashboard",
        url_path="dashboard",
        icon="📊",
        default=True
    )

    page_predictions = st.Page(
        "pages/1_Predictions.py",
        title="Predictions",
        icon="🔮"
    )

    # Create navigation and run
    pg = st.navigation([page_dashboard, page_predictions])
    pg.run()

except Exception as e:
    st.error(f"Navigation error: {e}")