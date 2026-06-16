# This page set all pages up
# It doesn't do anything else beside that
# Import
from PIL import Image
import streamlit as st

# Load our custom module from utils.py
from utils import load_data, load_geojson, load_svg, svg_to_img

# ---------------------------------------------------
# Set global config
# ---------------------------------------------------
st.set_page_config(
    page_title="Solar France",
    layout="wide",
    page_icon=Image.open("static/Solar_Energy_simple.png")
)


try:
    # Define pages
    page_dashboard = st.Page(
        "pages/Dashboard.py",
        title="Dashboard",
        url_path="dashboard",
        icon=None,
        default=True
    )

    page_predictions = st.Page(
        "pages/Predictions.py",
        title="Predictions",
        icon=None
    )


    # Create navigation and run
    pg = st.navigation([page_dashboard, page_predictions])
    pg.run()

except Exception as e:
    st.error(f"Navigation error: {e}")