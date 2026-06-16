# This file is dedicated to define functions, paths and colors
import pandas as pd
import streamlit as st
import requests
import base64 # SVG manipulation
import re # SVG manipulation


# ---------------------------------------------------
# General settings
# ---------------------------------------------------

APP_VERSION = '1.0.7'

# Constants
GEOJSON_URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions-version-simplifiee.geojson"
DATA_PATH = "https://huggingface.co/buckets/Gargamelch/solar_production/resolve/solar_prod_predictions.csv?download=true"

# Color palette
SOLAR_COLORSCALE = [
    [0.0,  '#FFF3E0'],
    [0.25, '#FFAB40'],
    [0.5,  '#E67E22'],
    [0.75, '#BF360C'],
    [1.0,  '#7B1900'],
]

PRIMARY_COLOR = '#E67E22'
SECONDARY_COLOR = '#F1C40F'

# ---------------------------------------------------
# Cache Functions
# ---------------------------------------------------

# GeoJSON
@st.cache_data(ttl=604800) # Cache for 1 week
def load_geojson():
    """Fetch and cache the France GeoJSON."""
    try:
        response = requests.get(GEOJSON_URL, timeout=10)
        return response.json()
    except Exception as e:
        st.error(f"Failed to load GeoJSON: {e}")
        return None


# CSV
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
    df['date'] = pd.to_datetime(df['date'])
    
    return df


# SVG recolor
def load_svg(filename, color=PRIMARY_COLOR):
    """Load an SVG file and change its color"""
    with open(f'static/{filename}', 'r') as f:
        svg = f.read()
    
    svg = re.sub(r'fill="(?!none)[^"]*"', f'fill="{color}"', svg)
    svg = re.sub(r'stroke="(?!none)[^"]*"', f'stroke="{color}"', svg)
    svg = re.sub(r'fill:[^;}"]*', f'fill:{color}', svg)
    svg = re.sub(r'stroke:[^;}"]*', f'stroke:{color}', svg)
    
    return svg


# SVG to imgage tag
def svg_to_img(filename, color=PRIMARY_COLOR, width=30):
    """Converts an SVG file into an HTML <img> tag that can be embedded directly in a webpage"""
    svg = load_svg(filename, color)
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{width}"/>'