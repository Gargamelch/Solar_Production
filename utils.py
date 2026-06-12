# This file is dedicated to load and cache data between pages

import pandas as pd
import streamlit as st
import requests

# Constants
GEOJSON_URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-version-simplifiee.geojson"
DATA_PATH = "solar_prod_predictions.csv"

#   Cache Functions
@st.cache_data(ttl=604800) # Cache for 1 week
def load_geojson():
    """Fetch and cache the France GeoJSON."""
    try:
        response = requests.get(GEOJSON_URL, timeout=10)
        return response.json()
    except Exception as e:
        st.error(f"Failed to load GeoJSON: {e}")
        return None

@st.cache_data(ttl=604800) # Cache data for 1 week
def load_data():
    """Load solar production prediction data."""
    try:
        df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    except Exception as e: 
        st.error(f"Data file not found")
        return None
        
    # Feature Engineering
    df["Year"] = df["date"].dt.year
    df["Month"] = df["date"].dt.month
    df["Month_name"] = df["date"].dt.strftime("%b")
    
    return df