import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
import scipy.stats as stats
import streamlit as st
from datetime import datetime, timedelta

# Load our custom module from utils.py
from utils import load_data, load_geojson



# --- Data loading----------------------------------
solar_prod_df = load_data()
geojson = load_geojson()



# --- Sidebar filters----------------------------------
default_date = pd.Timestamp("2026-01-01").date()  # Setting up the default date to be selected in our menu
with st.sidebar:
    st.header("Filters")

    selected_date = st.date_input(
        "Select a day",
        value=default_date,
        min_value=solar_prod_df["date"].min().date(),
        # Adding only 1 days doesn't do the trick to select the next day: we need to add 2
        max_value=(solar_prod_df["date"].max() + pd.Timedelta(days=2)).date()
    )

    if 'region' in solar_prod_df.columns:
        all_regions = sorted(solar_prod_df['region'].unique())
        region_selection = ['All'] + all_regions # Add the possibility to select everything
        
        selected_region_name = st.selectbox(
            'Select region',
            options=region_selection,
            index=0,
            key='region_selectbox'
        )
        
        if selected_region_name == 'All':
            selected_regions = all_regions 
        else:
            selected_regions = [selected_region_name]

    else:
        selected_regions = None
        st.warning('No "region" column found.')

    
    solar_panels_surface = st.slider(
        "Select a surface (m²)",
        min_value=10,
        max_value=10_000,
        value=100,
        step=10,
    )


    # Apply Combined Filters
    df_filtered = solar_prod_df.loc[solar_prod_df['date'] == pd.Timestamp(selected_date)]

    # Apply region filter only if regions were selected and exist
    if selected_regions is not None and len(selected_regions) > 0:
        df_filtered = df_filtered[df_filtered['region'].isin(selected_regions)]
    elif selected_regions is not None and len(selected_regions) == 0:
    # If user deselects everything, show empty or warning
        st.info('No regions selected. Showing no data.')
        df_filtered = pd.DataFrame(columns=solar_prod_df.columns) # Empty DataFrame 

    # Getting a dataframe to select the day before to check to prediction for the day
    previous_day_selected = selected_date - timedelta(days=1)
    df_filtered_day_before = solar_prod_df.loc[solar_prod_df['date'] == pd.Timestamp(previous_day_selected)]

    # Apply region filter only if regions were selected and exist
    if selected_regions is not None and len(selected_regions) > 0:
        df_filtered_day_before = df_filtered_day_before[df_filtered_day_before['region'].isin(selected_regions)]
    elif selected_regions is not None and len(selected_regions) == 0:
    # If user deselects everything, show empty or warning
        st.info('No regions selected. Showing no data.')
        df_filtered_day_before = pd.DataFrame(columns=solar_prod_df.columns) # Empty DataFrame 

# --- Variables definition----------------------------------
# We want to convert J/cm² into kWh/m²
# 1 m² = 10_000 cm²
# 1 J/cm² = 10_000 J/m²

# We want to convert J into kWh
# 1 kWh = 3.6 × 10^6 J
# 1 J = 1 / (3.6 × 10^6) kWh
# 1 J = 1 / 3.6e6 kWh

# 1 J/cm² = 10,000 J/m²
# 1 J/cm² = 10,000 * (1 / 3.6e6) kWh/m²
joules_to_kwh = 10_000 * (1 / (3.6 * 10**6)) # # ~0.00278
panel_efficiency = 0.2


production_kwh = df_filtered['visible_radiation'].mean() * joules_to_kwh * solar_panels_surface * panel_efficiency
predicted_production_kwh = df_filtered_day_before['visible_radiation J+1 predit'].mean() * joules_to_kwh * solar_panels_surface * panel_efficiency


# --- Title and page config----------------------------------
st.set_page_config(page_title='🤖 Solar production prediction', layout='wide', page_icon='🤖')
st.title(f'☀️ Solar Energy Production — France ({selected_date})')


# --- KPI's----------------------------------
st.header('Overview')
col1, col2, col3, col4, col5 = st.columns(5)

# If the date selected is withing our dataframe, we show the real data
# Otherwise we hide this part ad show only the predictions
if selected_date <= solar_prod_df['date'].max().date():
    with col1:
        with st.container(border=True):
            st.metric(
                label='Average temperature (°C)',
                value=f'{df_filtered['daily_avg_temp'].mean():.1f}',
                delta='',
                delta_color='off'
            )

    with col2:
        with st.container(border=True):
            st.metric(label='Average rainfall (mm)',
                value=f'{df_filtered['rainfall'].mean():.2f}',
            )

    with col3:
        with st.container(border=True):
            st.metric(label=f'Average wind speed (m/s)',
                value=f'{df_filtered['daily_avg_wind_speed'].mean():.2f}',
            )

    with col4:
        with st.container(border=True):
            st.metric(label=f'Visible radiation (J/cm²)',
                value=f'{df_filtered['visible_radiation'].mean():.2f}',
            )

    with col5:
        with st.container(border=True):
            st.metric(label=f'Estimated electric production (KWh)',
                value=f'{production_kwh:.2f}',
            )


st.divider()



# --- Predictions----------------------------------
st.header('Predictions')
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.metric(label=f'Predicted visible radiation (J/cm²)',
        value=f'{df_filtered_day_before['visible_radiation J+1 predit'].mean():.2f}',
        )

with col2:
    with st.container(border=True):
        st.metric(label=f'Predicted electric production (KWh)',
        value=f'{predicted_production_kwh:.2f}',
    )
        
with col3:
    with st.container(border=True):
        st.metric(label=f'Delta (%)',
        value=f'{((df_filtered_day_before['visible_radiation J+1 predit'].mean()
                - df_filtered['visible_radiation'].mean())
                / df_filtered['visible_radiation'].mean()) * 100 :+,.2f} %',
    )
        

# --- Informations----------------------------------
st.markdown("""
> **ℹ️ Note on Production Estimation**  
> The *estimated electric production* shown here is a **theoretical calculation**, not real-time output from a specific power plant.  
> It represents the energy generated per **m² of solar panel** assuming a fixed efficiency of **20%**.  
> Actual production at any site may vary based on panel orientation, shading, temperature and equipment age.
""", unsafe_allow_html=False)