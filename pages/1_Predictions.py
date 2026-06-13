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

# --- Title config----------------------------------
st.set_page_config(page_title='🤖 Solar production prediction', layout='wide', page_icon='🤖')

# --- Data loading----------------------------------
solar_prod_df = load_data()
geojson = load_geojson()

# --- Variable name for easier code readability----------------------------------
SOL_PROD = 'production_solaire/m2(en Kwh)'
SOL_PROD_PRED  = 'production_solaire/m2(en Kwh) J+1 predit'


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



    # Getting previous day prediction to check with todays result
    previous_date = pd.Timestamp(selected_date) - pd.Timedelta(days=1) # Date selected - 1 day
    df_previous = solar_prod_df.loc[
        (solar_prod_df['date'] == previous_date) &
        (solar_prod_df['region'].isin(selected_regions))
    ]

    has_data = not df_filtered.empty
    predicted_val = df_previous[SOL_PROD_PRED].mean() if not df_previous.empty and SOL_PROD_PRED in df_previous.columns else None
    actual_val = df_filtered[SOL_PROD].mean() if has_data and SOL_PROD in df_filtered.columns else None

    # Check for data availability and avoid display errors
    is_future = selected_date > solar_prod_df['date'].max().date()
    has_actual = actual_val is not None
    has_prediction = predicted_val is not None



# --- Page config----------------------------------
st.title(f'☀️ Solar Energy Production — France ({selected_date})')

if is_future:
    st.info('🔮 Future date selected — showing prediction only, no actual data available.')


# If the date selected is withing our dataframe, we show the real data
# Otherwise we hide this part ad show only the predictions
if selected_date <= solar_prod_df['date'].max().date():
    # --- KPI's----------------------------------
    st.header('Weather conditions')
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        with st.container(border=True):
            st.metric(
                label='Average temperature',
                value=f'{df_filtered['daily_avg_temp'].mean():.1f} °C',
                delta='',
                delta_color='off'
            )

    with col2:
        with st.container(border=True):
            st.metric(label='Average rainfall',
                value=f'{df_filtered['rainfall'].mean():.2f} mm',
            )

    with col3:
        with st.container(border=True):
            st.metric(label=f'Average wind speed',
                value=f'{df_filtered['daily_avg_wind_speed'].mean():.2f} m/s',
            )

    with col4:
        with st.container(border=True):
            st.metric(label=f'Visible radiation',
                value=f'{df_filtered['visible_radiation'].mean():.2f} J/cm²',
            )

    with col5:
        with st.container(border=True):
            st.metric(label=f'Estimated electric production',
                value=f'{df_filtered[SOL_PROD].mean():.2f} KWh/m²',
            )

if selected_date <= solar_prod_df['date'].max().date():
    st.divider()

# --- Predictions----------------------------------

if has_prediction:

    st.header('Predictions')
    col1, col2 = st.columns([2,5])

    with col1:
        with st.container(border=True):
            if predicted_val is not None:
                delta_str = f'{((predicted_val - actual_val) / actual_val) * 100:+,.1f} %' if actual_val else None
                st.metric(
                    label='Predicted production',
                    value=f'{predicted_val:.3f} KWh/m²',
                    delta=delta_str,
                    delta_color='normal',
                )
            else:
                st.warning('No prediction available for this date.')
        
                
    with col2:        
        # --- Informations----------------------------------
        st.markdown("""
        > **ℹ️ Note on Production Estimation**  
        > The *estimated electric production* shown here is a **theoretical calculation**, not real-time output from a specific power plant.  
        > It represents the energy generated per **m² of solar panel** assuming a fixed efficiency of **20%**.  
        > Actual production at any site may vary based on panel orientation, shading, temperature and equipment age.
        """, unsafe_allow_html=False)

   
   
# --- Gauge----------------------------------
GLOBAL_MAX = solar_prod_df[SOL_PROD].max() * solar_panels_surface # Set gauge max value so it remains consistant

if not is_future and has_actual and has_prediction: # Date available, has data, next day has prediction
    fig_pred = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=predicted_val * solar_panels_surface,
        delta=dict(reference=actual_val * solar_panels_surface,
                    valueformat='.2f',
                    suffix=' KWh/m²'),
        number=dict(suffix=' KWh/m²', valueformat='.2f'),
        title=dict(text='Predicted production'),
        gauge=dict(
            axis=dict(range=[0, GLOBAL_MAX]),
            bar=dict(color='#E67E22', thickness=0.9),
            steps=[dict(range=[0, GLOBAL_MAX], color='lightgray')],
            threshold=dict(line=dict(color='green', width=3),
                            thickness=0.75,
                            value=actual_val * solar_panels_surface)
        )
    ))
    fig_pred.update_layout(height=280, margin=dict(l=20, r=20, t=80, b=20))
    st.plotly_chart(fig_pred, use_container_width=True)

elif has_prediction: # Date unavailable but date has prediction because of previous day
    fig_pred = go.Figure(go.Indicator(
        mode='gauge+number',
        value=predicted_val * solar_panels_surface,
        number=dict(suffix=' KWh/m²', valueformat='.2f'),
        title=dict(text='Predicted production'),
        gauge=dict(
            axis=dict(range=[0, GLOBAL_MAX]),
            bar=dict(color='#E67E22', thickness=0.9),
            steps=[dict(range=[0, GLOBAL_MAX], color='lightgray')],
        )
    ))
    fig_pred.update_layout(height=280, margin=dict(l=20, r=20, t=80, b=20))
    st.plotly_chart(fig_pred, use_container_width=True)

else:
    # Date warning or error message
      if not has_data:
        st.warning('No data available for the selected date and region.')