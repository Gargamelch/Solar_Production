import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import scipy.stats as stats
import streamlit as st
import requests
from scipy.stats import gaussian_kde

#   Load our custom module from utils.py
from utils import load_data, load_geojson

#   Page config
st.set_page_config(page_title="☀️ Solar Production", layout="wide", page_icon="☀️")
st.title("☀️ Solar Energy Production — France")
st.caption("Data sources: RTE (electricity) · Meteo-France (weather) · 2012–2026")

#   Palette
PALETTE = ["#345fff", "#e142d5", "#ff4b9b", "#ffc352", "#f9f871",
           "#9bde7e", "#4bbc8e", "#039590", "#1c6e7d", "#2f4858",
           "#ff6b6b", "#ffa07a", "#20b2aa", "#87ceeb"]

#   Load data
solar_prod_df = load_data()
geojson = load_geojson()



#   Loading dataframes used
solar_prod_df = solar_prod_df.loc[solar_prod_df['Year'] < 2026, :]


#   Sidebar filters
with st.sidebar:
    st.header("Filters")
    years = sorted(solar_prod_df["Year"].unique())

    selected_range = st.slider(
        "Select period",
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(int(min(years)), int(max(years))),
        key="year_range_slider"
    )

    year_min, year_max = selected_range

    if 'region' in solar_prod_df.columns:
        all_regions = sorted(solar_prod_df["region"].unique())
        region_selection = ["All"] + all_regions # Add the possibility to select everything
        
        selected_region_name = st.selectbox(
            "Select Region",
            options=region_selection,
            index=0,
            key="region_selectbox"
        )
        
        if selected_region_name == "All":
            selected_regions = all_regions 
        else:
            selected_regions = [selected_region_name]

    else:
        selected_regions = None
        st.warning("No 'region' column found.")

    # Apply Combined Filters
    df_filtered = solar_prod_df[
        (solar_prod_df["Year"] >= year_min) & 
        (solar_prod_df["Year"] <= year_max)
    ]

    # Apply region filter only if regions were selected and exist
    if selected_regions is not None and len(selected_regions) > 0:
        df_filtered = df_filtered[df_filtered["region"].isin(selected_regions)]
    elif selected_regions is not None and len(selected_regions) == 0:
        # If user deselects everything, show empty or warning
        st.info("No regions selected. Showing no data.")
        df_filtered = pd.DataFrame(columns=solar_prod_df.columns) # Empty DataFrame 

    monthly_df = (df_filtered
                .groupby(pd.Grouper(key="date", freq="ME"))["TWh"]
                .sum()
                .reset_index()
                )
    yearly_df = (df_filtered
                .groupby(pd.Grouper(key="date", freq="YE"))["TWh"]
                .sum().reset_index()
                )

    solar_prod_df_geo = df_filtered.groupby('region')[['TWh']].sum().reset_index()

    region_prod = (df_filtered
        .groupby("region", as_index=False)
        .agg(total_solar_TWh=("TWh", "sum"))
        .sort_values("total_solar_TWh", ascending=True)
)


#   KPI metrics
st.header('📊 Overview')
col1, col2, col3, col4 = st.columns(4)

#   Count days per year to detect partial years
days_per_year = df_filtered.groupby('Year')['date'].count()     # Count the number of days for every year
full_years = days_per_year[days_per_year >= 365].index.tolist() # List the full years in the dataset so growth is correct

if len(full_years) >= 2:    # If there's a least 2 more full years selected we can calculate growth                                             
    first_year_avg = df_filtered[df_filtered['Year'] == min(full_years)]['TWh'].mean()
    last_year_avg  = df_filtered[df_filtered['Year'] == max(full_years)]['TWh'].mean()
    growth = ((last_year_avg - first_year_avg) / first_year_avg * 100)
    growth_label = f'📊 Growth ({min(full_years)} → {max(full_years)})'
else:                       # If less than 2 full years are selected, show 0
    growth = 0
    growth_label = '📊 Growth (n/a)'

with col1:
    with st.container(border=True):
        st.metric(label='📅 Year Range',
                        value=f'{year_min} - {year_max}',
        )

with col2:
    with st.container(border=True):
        st.metric(
            label='⚡ Total Production (TWh)',
            value=f"{df_filtered['TWh'].sum():.2f}",
            delta='',
            delta_color='off'
        )

with col3:
    with st.container(border=True):
        st.metric(label='📈 Daily Average',
            value=f'{df_filtered['TWh'].mean() * 1_000_000:.2f}',
            delta='',
            delta_color='off'
        )

with col4:
    with st.container(border=True):
        delta_color = 'normal' if len(full_years) >= 2 else 'off'
        st.metric(label=f'📊 {year_min} → {year_max}',
            value=f'{growth:+.1f}%',
            delta_color=delta_color,
        )

with st.expander("🔍 Raw data"):
    st.dataframe(df_filtered, use_container_width=True)

st.divider()

#   Yearly production
st.header('📅 Yearly Production')
col1, col2 = st.columns(2)

yearly_df["Year"] = yearly_df["date"].dt.year

#   Linear trend
with col1:
    x_num = np.arange(len(yearly_df))
    slope, intercept, r, *_ = stats.linregress(x_num, yearly_df["TWh"])
    trend_y = slope * x_num + intercept

    fig_yearly = go.Figure()
    fig_yearly.add_trace(go.Bar(
        x=yearly_df["Year"], y=yearly_df["TWh"],
        marker=dict(color=yearly_df["TWh"], colorscale="Blues", showscale=False),
        name="Production", hovertemplate="%{x}: %{y:.2f} TWh<extra></extra>"
    ))
    fig_yearly.add_trace(go.Scatter(
        x=yearly_df["Year"], y=trend_y,
        mode="lines", line=dict(color="blue", dash="dash", width=2),
        name=f"Trend (R²={r**2:.2f})"
    ))
    fig_yearly.update_layout(
        title="Solar Energy Production per Year",
        xaxis_title="Year", 
        yaxis_title="Production (TWh)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified", 
        template="plotly_dark"
    )
    st.plotly_chart(fig_yearly, use_container_width=True)

with col2:

    fig_seasonal = px.line(
        monthly_df, 
        x="date",
        y="TWh", 
        markers=True,
        title="Solar energy production seasonality",
        template="plotly_dark"
    )

    # Update Title styling to match fontweight="bold"
    fig_seasonal.update_layout(
        title_font=dict(weight="bold", size=18),
        xaxis_title="date", 
        yaxis_title="Production (TWh)"
    )


    st.plotly_chart(fig_seasonal, use_container_width=True)

st.divider()


#   Seasonality
st.header("🌸 Seasonality — Monthly Production per Year")

monthly_df["Year"]  = monthly_df["date"].dt.year
monthly_df["Month"] = monthly_df["date"].dt.month

fig_seasonal = px.line(
    monthly_df, x="Month", y="TWh", color="Year",
    color_discrete_sequence=PALETTE,
    labels={"TWh": "Production (TWh)", "Month": "Month"},
    title="Monthly Solar Production per Year",
    template="plotly_dark"
)
fig_seasonal.update_xaxes(
    tickvals=list(range(1, 13)),
    ticktext=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
)

st.plotly_chart(fig_seasonal, use_container_width=True)

st.divider()

# Convert th MWh for a better representation
solar_prod_mwh_df = df_filtered.copy()
solar_prod_mwh_df['MWh'] = solar_prod_mwh_df['TWh'].mul(1_000_000)
solar_prod_mwh_df.drop(columns='TWh', inplace=True)

# Histogram
fig_wh = px.histogram(
    solar_prod_mwh_df,
    x="MWh",
    nbins=50,
    histnorm="density"
)

# KDE
kde = gaussian_kde(solar_prod_mwh_df["MWh"])
x_grid = np.linspace(solar_prod_mwh_df["MWh"].min(), solar_prod_mwh_df["MWh"].max(), 500)

fig_wh.add_trace(
    go.Scatter(
        x=x_grid,
        y=kde(x_grid),
        mode="lines",
        name="KDE"
    )
)

fig_wh.update_layout(
    title="Distribution of daily solar production",
    xaxis_title="Production (MWh)",
    yaxis_title="Density"
)

fig_wh.show()
st.plotly_chart(fig_wh, use_container_width=True)



st.divider()

#   Year-over-year comparison
st.header("📊 Year-over-Year Comparison")

col1, col2 = st.columns(2)

with col1:
    # Heatmap: year vs month
    pivot = monthly_df.pivot(index="Year", columns="Month", values="TWh").fillna(0)
    pivot.columns = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    fig_heat = px.imshow(
        pivot, color_continuous_scale="Blues",
        labels=dict(color="TWh"),
        title="Production Heatmap (Year x Month)",
        template="plotly_dark",
        height=500 
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with col2:
    # Cumulative production per year
    df_filtered_sorted = df_filtered.sort_values("date")
    df_filtered_sorted["Cumulative"] = df_filtered_sorted.groupby("Year")["TWh"].cumsum()
    fig_cum = px.line(
        df_filtered_sorted, x="Month", y="Cumulative", color="Year",
        color_discrete_sequence=PALETTE,
        labels={"Cumulative": "Cumulative TWh", "Month": "Month"},
        title="Cumulative Production per Year",
        template="plotly_dark",
        height=500 
    )
    fig_cum.update_xaxes(
        tickvals=list(range(1, 13)),
        ticktext=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    )
    st.plotly_chart(fig_cum, use_container_width=True)


st.divider()
#   Geographical production
st.header("🗺️ Solar production by Region")
col1, col2 = st.columns(2)
HEIGHT = 600

with col1:
    fig_map = px.choropleth(
        solar_prod_df_geo,
        geojson=geojson,
        locations='region',
        featureidkey='properties.nom',
        color='TWh',
        hover_name='region',
        hover_data={'TWh': ':.2f'},
        color_continuous_scale='Blues',
    )
    fig_map.update_geos(fitbounds='locations', visible=False, projection_type='mercator')
    fig_map.update_layout(
        height=HEIGHT,
        width=900,
        margin={'r': 0, 't': 30, 'l': 0, 'b': 0}
    )
    fig_map.update_geos(fitbounds='locations', visible=False)
    fig_map.show()
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    fig_bar = px.bar(
        region_prod,
        y="region",
        x="total_solar_TWh",
        color="total_solar_TWh",
        color_continuous_scale="Blues",
        title="",                               # To avoid 'untitle' title
        template="plotly_dark",
        orientation='h'
    )

    # Update Layout for better polish
    fig_bar.update_layout(
        title_font=dict(weight="bold", size=18),
        xaxis_title="Total Production (TWh)",
        yaxis_title="Region",
        height=HEIGHT,
        margin=dict(l=200, r=20, t=50, b=20),   # Extra left margin for long region names
        coloraxis_showscale=True,               # Show the color scale legend (optional)
    )
    st.plotly_chart(fig_bar, use_container_width=True)