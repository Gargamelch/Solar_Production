import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
import scipy.stats as stats
import streamlit as st
from scipy.stats import gaussian_kde

# Load our custom module from utils.py
from utils import (load_data, load_geojson, load_svg, svg_to_img, 
                    SOLAR_COLORSCALE, PRIMARY_COLOR, SECONDARY_COLOR, 
                    DATA_PATH, APP_VERSION)


# Custom CSS to have a clean and well placed logo branding
st.markdown("""
    <style>
        [data-testid="stSidebarNav"]::before {
            content: "";
            display: block;
            background-image: url("app/static/Solar_Energy_clean.png");
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            height: 150px;
            margin: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# Data loading
# ---------------------------------------------------
solar_prod_df = load_data()
geojson = load_geojson()
# Filtering to < 2026 (for complete years graphs)
solar_prod_full_year_df = solar_prod_df.loc[solar_prod_df['Year'] < 2026, :]


# ---------------------------------------------------
# Sidebar filters 
# ---------------------------------------------------
with st.sidebar:
    st.header('Filters')
    years = sorted(solar_prod_full_year_df['Year'].unique())

    selected_range = st.slider(
        'Select period',
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(int(min(years)), int(max(years))),
        key='year_range_slider'
    )

    year_min, year_max = selected_range

    if 'region' in solar_prod_full_year_df.columns:
        all_regions = sorted(solar_prod_full_year_df['region'].unique())
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

    # Apply Combined Filters
    df_filtered = solar_prod_full_year_df[
        (solar_prod_full_year_df['Year'] >= year_min) & 
        (solar_prod_full_year_df['Year'] <= year_max)
    ]

    # Apply region filter only if regions were selected and exist
    if selected_regions is not None and len(selected_regions) > 0:
        df_filtered = df_filtered[df_filtered['region'].isin(selected_regions)]
    elif selected_regions is not None and len(selected_regions) == 0:
    # If user deselects everything, show empty or warning
        st.info('No regions selected. Showing no data.')
        df_filtered = pd.DataFrame(columns=solar_prod_df.columns) # Empty DataFrame 

    monthly_df = (df_filtered
                .groupby(pd.Grouper(key='date', freq='ME'))['TWh']
                .sum()
                .reset_index()
                )
    yearly_df = (df_filtered
                .groupby(pd.Grouper(key='date', freq='YE'))['TWh']
                .sum().reset_index()
                )

    solar_prod_df_geo = df_filtered.groupby('region')[['TWh']].sum().reset_index()

    region_prod = (df_filtered
        .groupby('region', as_index=False)
        .agg(total_solar_TWh=('TWh', 'sum'))
        .sort_values('total_solar_TWh', ascending=True)
)
    # Sources
    st.markdown('<div style="font-size:0.65rem;color:#3C4460;text-align:center">RTE · Météo-France · SDES</div>', unsafe_allow_html=True)

    # Badges - CSS
    st.markdown(f"""
        <style>
            .version-badge {{
                position: fixed;
                bottom: 20px;
                display: flex;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
            }}
        </style>
        <div class="version-badge">
            <div style="
                background: #0A0E1A;
                color: white;
                padding: 2px 10px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 700;
                letter-spacing: 1px;
            ">{APP_VERSION}</div>
            <a href="https://www.gnu.org/licenses/gpl-3.0.html" target="_blank" style="
                background: #0A0E1A;
                color: white;
                padding: 2px 10px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 700;
                text-decoration: none;
            ">GPL-3.0</a>
            <a href="https://github.com/Gargamelch/Solar_Production" target="_blank" style="
                background: #0A0E1A;
                color: white;
                padding: 2px 10px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 700;
                text-decoration: none;
            ">{svg_to_img('github.svg', color='white', width=14)} GitHub</a>
            <span style="color: gray; font-size: 0.75rem;"
    """, unsafe_allow_html=True)
    

year_range = str(year_min) if year_min == year_max else f'{year_min} - {year_max}'
st.title(f'Solar Energy Dashboard · France ({year_range})')


# ---------------------------------------------------
# Tab settings 
# ---------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    'Overview',
    'Regions',
    'Production',
    'Solar Radiations',
    'Installations',
    'Data',
])

# ---------------------------------------------------
# First tab 
# ---------------------------------------------------
with tab1:
    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)

    # Average daily production across all regions
    daily_agg = (df_filtered.groupby('date')
            .agg(
                total_TWh=('TWh', 'sum'),
                total_capacity=('capacity_power', 'sum'))
            .reset_index()
    )

    # Calculating KPI
    total_production = daily_agg['total_TWh'].sum()
    daily_avg        = daily_agg['total_TWh'].mean() * 1_000_000
    avg_capacity     = daily_agg['total_capacity'].mean()

    # Count days per year to detect partial years
    days_per_year = df_filtered.groupby('Year')['date'].count()     # Count the number of days for every year
    full_years = days_per_year[days_per_year >= 365].index.tolist() # List the full years in the dataset so growth is correct

    if len(full_years) >= 2:    # If there's a least 2 full years selected we can calculate growth                                             
        first_year_avg = daily_agg[daily_agg['date'].dt.year == min(full_years)]['total_TWh'].mean()
        last_year_avg  = daily_agg[daily_agg['date'].dt.year == max(full_years)]['total_TWh'].mean()
        growth = ((last_year_avg - first_year_avg) / first_year_avg * 100)
        growth_label = f'📊 Growth ({min(full_years)} → {max(full_years)})'
    else:                       # If less than 2 full years are selected, show 0
        growth = 0
        growth_label = ' Growth (n/a)'

    # Total Production
    with col1:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('pred.svg')} **Total Production (TWh)**", unsafe_allow_html=True)
            st.metric(
                label='Total Production (TWh)',
                value=f'{total_production:.2f}',
                label_visibility='hidden',
            )

    # Daily Average
    with col2:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('prod.svg')} **Daily Average (MWh)**", unsafe_allow_html=True)
            st.metric(
                label='Daily Average (MWh)',
                value=f'{daily_avg:.2f}',
                label_visibility='hidden',
            )

    # Evolution
    with col3:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('charts.svg')} **Evolution (MWh) {year_min} → {year_max}**", unsafe_allow_html=True)
            delta_color = 'normal' if len(full_years) >= 2 else 'off'
            st.metric(
                label=f'Evolution (MWh)',
                value=f'{growth:+.1f}%',
                delta_color=delta_color,
                label_visibility='hidden',
            )

    # Power Capacity    
    with col4:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('panel.svg')} **Average Power Capacity**", unsafe_allow_html=True)
            st.metric(
                label='Average Power Capacity',
                value=f'{avg_capacity:.2f}',
                label_visibility='hidden',
            )


    st.divider()

    # Yearly production
    col1, col2 = st.columns(2)

    yearly_df['Year'] = yearly_df['date'].dt.year

    # Linear trend
    HEIGHT_GRAPHS = 450
    with col1:
        st.markdown(f"**Solar Energy Production Per Year**", unsafe_allow_html=True)

        fig_yearly = go.Figure()
        fig_yearly.add_trace(go.Bar(
            x=yearly_df['Year'], 
            y=yearly_df['TWh'],
            marker=dict(color=yearly_df['TWh'], 
            colorscale=SOLAR_COLORSCALE, 
            showscale=False),
            name='Production', 
            hovertemplate='%{x}: %{y:.2f} TWh'
        ))

        fig_yearly.update_layout(
            title=dict(text=None), # Remove individual titles
            xaxis_title='Year', 
            yaxis_title='Production (TWh)',
            template='plotly_dark',
            height=HEIGHT_GRAPHS,
            margin=dict(t=30, b=20, l=20, r=20),
            showlegend=False,
        )
        st.plotly_chart(fig_yearly, width='content')

    with col2:
        st.markdown(f"**Solar Energy Production Trend**", unsafe_allow_html=True)
        fig_seasonal = px.line(
            monthly_df, 
            x='date',
            y='TWh', 
            markers=True,
            template='plotly_dark',
            color_discrete_sequence=[PRIMARY_COLOR],
        )
        
        fig_seasonal.update_layout(
            title=dict(text=None), # Remove individual titles
            xaxis_title='Date', 
            yaxis_title='Production (TWh)',
            height=HEIGHT_GRAPHS,
            margin=dict(t=30, b=20, l=20, r=20),
        )
        
        # y = 0 axis doesn't show up. Drawing it so both charts look aligned together
        fig_seasonal.add_hline(
            y=0,
            line=dict(color='rgba(255,255,255,0.01)', width=1),
        )


        st.plotly_chart(fig_seasonal, width='content')


# ---------------------------------------------------
# Second tab
# ---------------------------------------------------
with tab2:

    st.markdown(f'**Geographical Electrical Production**', unsafe_allow_html=True)
    # Layout with map and ranking
    map_col, rank_col = st.columns([2, 1])
    HEIGHT_2=650

    with map_col:
        # production by region
        region_prod = (
            df_filtered
            .groupby("region", as_index=False)
            .agg(total_TWh=("TWh", "sum"))
        )

        fig_map = px.choropleth_mapbox(
            region_prod,
            geojson=geojson,
            locations="region",
            featureidkey="properties.nom",
            color="total_TWh",
            mapbox_style="carto-darkmatter",
            center={"lat": 46.6, "lon": 2.4},
            zoom=4.7,
            opacity=1,
            color_continuous_scale=SOLAR_COLORSCALE,
            labels={"total_TWh": "Production (TWh)"}
        )

        region_coords = {
        "Auvergne-Rhône-Alpes": (45.76, 4.84),
        "Bourgogne-Franche-Comté": (47.32, 5.04),
        "Bretagne": (48.20, -2.93),
        "Centre-Val de Loire": (47.75, 1.68),
        "Corse": (42.15, 9.10),
        "Grand Est": (48.70, 6.20),
        "Hauts-de-France": (50.50, 2.80),
        "Île-de-France": (48.85, 2.35),
        "Normandie": (49.10, 0.20),
        "Nouvelle-Aquitaine": (45.20, 0.20),
        "Occitanie": (43.80, 2.20),
        "Pays de la Loire": (47.50, -0.80),
        "Provence-Alpes-Côte d'Azur": (43.95, 6.00),
        }
        
        region_prod["lat"] = region_prod["region"].map(
                    lambda x: region_coords.get(x, (None, None))[0]
        )
        region_prod["lon"] = region_prod["region"].map(
                    lambda x: region_coords.get(x, (None, None))[1]
        )

        region_prod["label"] = (
            region_prod["region"]
            + "<br>"
            + region_prod["total_TWh"].round(1).astype(str)
            + " TWh"
        )

        fig_map.add_trace(
            go.Scattermapbox(
                lat=region_prod["lat"],
                lon=region_prod["lon"],
                mode="text",
                text=region_prod["label"],
                textfont=dict(
                    size=11,
                    color="black"
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig_map.update_layout(
            height=HEIGHT_2,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            coloraxis_colorbar=dict(
                title="TWh",
                x=1.02
                ),
            )

        st.plotly_chart(fig_map, width='stretch')

    with rank_col:
        ranking = (region_prod
                .sort_values("total_TWh", ascending=False)[["region", "total_TWh"]]
                .reset_index(drop=True)
        )
        ranking.index += 1 # Starting index as 1 for display

        st.dataframe(
            ranking,
            width='content',
            height=35 * len(ranking) + 38,  # 35px per row + 38px for header
            column_config={
                "total_TWh": st.column_config.ProgressColumn(
                    label="Total (TWh)",
                    format="%.2f TWh",
                    min_value=0,
                    max_value=float(ranking["total_TWh"].max()),
                    )
                }
        )   

# ---------------------------------------------------
# Third tab
# ---------------------------------------------------
with tab3:
    HEIGHT_3 = 400
    # Convert to MWh for better representation
    solar_prod_mwh_df = df_filtered.copy()
    solar_prod_mwh_df['MWh'] = solar_prod_mwh_df['TWh'].mul(1_000_000)
    solar_prod_mwh_df['Year'] = solar_prod_mwh_df['date'].dt.year
    solar_prod_mwh_df.drop(columns='TWh', inplace=True)

    # Calculate Daily Capacity Factor (%)
    # Percentage of real production over theorical maximum production
    solar_prod_mwh_df['daily_capacity_factor_pct'] = solar_prod_mwh_df.apply(
        lambda row: (row['MWh'] / (row['capacity_power'] * 24)) * 100 if row['capacity_power'] > 0 else 0,
        axis=1)

    # Aggregate to date level so we can properly compute values
    daily_prod = (
        solar_prod_mwh_df
        .groupby('date')['MWh']
        .sum()
        .reset_index()
        )

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('avg.svg')} **Daily Mean**", unsafe_allow_html=True)
            st.metric(label='Mean', 
                      value=f'{daily_prod["MWh"].mean():,.0f} MWh',
                      label_visibility='hidden',
                      )
            
    with col2:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('median.svg')} **Daily Median**", unsafe_allow_html=True)
            st.metric(label='Median', 
                      value=f'{daily_prod["MWh"].median():,.0f} MWh',
                      label_visibility='hidden',
                      )
    with col3:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('max.svg')} **Daily Max**", unsafe_allow_html=True)
            st.metric(label='Max', 
                      value=f'{daily_prod["MWh"].max():,.0f} MWh',
                      label_visibility='hidden',
                      )
    with col4:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('perc.svg')} **Daily Average Capacity Factor**", unsafe_allow_html=True)
            st.metric(label='Avg', 
                      value=f'{solar_prod_mwh_df['daily_capacity_factor_pct'].mean():,.2f} %',
                      label_visibility='hidden',
                      )


    st.divider()

    col1, col2 = st.columns(2)


    monthly_cf = (
        solar_prod_mwh_df
        .groupby(pd.Grouper(key='date', freq='ME'))['daily_capacity_factor_pct']
        .mean()
        .reset_index()
    )

    with col1:
        st.markdown(f"**Electrical Production Distributions Per Day**", unsafe_allow_html=True)
        # Histogram
        fig_wh = px.histogram(
            daily_prod,
            x='MWh',
            nbins=50,
            color_discrete_sequence=[PRIMARY_COLOR],
            opacity=0.8,
        )

        fig_wh.update_layout(
            title=dict(text=None),
            xaxis_title='Production (MWh)',
            yaxis_title='Number of days',
            template='plotly_dark',
            height=HEIGHT_3,
            margin=dict(t=30, b=20, l=20, r=20),
            showlegend=False,
            bargap=0.05,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        )
        st.plotly_chart(fig_wh, width='content')

    with col2:
        st.markdown(f"**Production Per Capacity**", unsafe_allow_html=True)

        # Calculate capacity factor
        fig_cf = go.Figure()

        fig_cf.add_trace(go.Scatter(
            x=monthly_cf['date'],
            y=monthly_cf['daily_capacity_factor_pct'],
            mode='lines+markers',
            line=dict(color=PRIMARY_COLOR, width=2.5),
        ))

        fig_cf.add_hline(
            y=15, 
            line_dash="dash", 
            line_color=SECONDARY_COLOR, 
            line_width=2,
            annotation_text="Excellent",
            annotation_font_color=SECONDARY_COLOR,
            annotation_position="bottom right"
)


        fig_cf.update_layout(
            title=dict(text=None),
            xaxis_title=None,
            yaxis_title='Average Capacity Factor (%)',
            template='plotly_dark',
            height=HEIGHT_3,
            margin=dict(t=30, b=20, l=20, r=20),
            showlegend=False,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )

        st.plotly_chart(fig_cf, width='content', key='fig_cf')

    info_icon = svg_to_img('info.svg', color=PRIMARY_COLOR, width=20)
    st.markdown(f"""
        <div style="
            background-color: rgba(15, 21, 37, 1);
            border-left: 3px solid {PRIMARY_COLOR};
            border-radius: 0 8px 8px 0;
            padding: 15px 20px;
            margin: 0px 0;
        ">
            <p style="margin: 0; font-size: 1rem; line-height: 1.6;">
                {info_icon} <strong>Capacity Factor:</strong>
                <span style="color: #aaa;">The ratio (%) of actual energy produced to the theoretical maximum if the pannel ran at full capacity 24/7.</span>
            </p>
        </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------
# Fourth tab
# ---------------------------------------------------
with tab4:
    monthly_vr_df = df_filtered.groupby(pd.Grouper(key='date', freq='ME'))[['TWh', 'visible_radiation']].mean().reset_index()
    monthly_agg_vr_df = df_filtered.groupby('Month')[['TWh', 'visible_radiation']].mean().reset_index()
    correlation = df_filtered['TWh'].corr(df_filtered['visible_radiation'])


    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('sun.svg')} **Correlation · Solar Production vs Visible Radiation**", unsafe_allow_html=True)
            st.metric(
                label='Correlation · Solar Production vs Visible Radiation',
                value=f'{correlation:.2f}',
                label_visibility='hidden',
            )

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Visible Radiation vs Solar Production Trend**", unsafe_allow_html=True)
        fig_dual = go.Figure()

        fig_dual.add_trace(go.Scatter(
            x=monthly_vr_df['date'], 
            y=monthly_vr_df['TWh'],
            mode='lines+markers', 
            name='Solar Production',
            line=dict(color=PRIMARY_COLOR, width=2.5),
            yaxis='y1',
        ))

        fig_dual.add_trace(go.Scatter(
            x=monthly_vr_df['date'], 
            y=monthly_vr_df['visible_radiation'],
            mode='lines+markers', 
            name='Visible Radiation',
            line=dict(color=SECONDARY_COLOR, width=2.5),
            yaxis='y2'
        ))

        fig_dual.update_layout(
            title=dict(text=None),
            xaxis_title=None,
            yaxis=dict(title='Production (TWh)', 
                       color=PRIMARY_COLOR),
            yaxis2=dict(title='Visible Radiation (J/cm²)', 
                        color=SECONDARY_COLOR,
                        overlaying='y', 
                        side='right',
                        showgrid=False,), # Can't manage to  have a clean look, removing y2 grid
            template='plotly_dark',
            height=HEIGHT_GRAPHS,
            margin=dict(t=30, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5,
            ),
        )

        st.plotly_chart(fig_dual, width='content')

    with col2:
        st.markdown(f"**Visible Radiation vs Solar Production Per Month**", unsafe_allow_html=True)
        fig_dual_month = go.Figure()

        fig_dual_month.add_trace(go.Scatter(
            x=monthly_agg_vr_df['Month'], 
            y=monthly_agg_vr_df['TWh'],
            mode='lines+markers', 
            name='Solar Production',
            line=dict(color=PRIMARY_COLOR, width=2.5),
            yaxis='y1'
        ))

        fig_dual_month.add_trace(go.Scatter(
            x=monthly_agg_vr_df['Month'], 
            y=monthly_agg_vr_df['visible_radiation'],
            mode='lines+markers', 
            name='Visible Radiation',
            line=dict(color=SECONDARY_COLOR, width=2.5),
            yaxis='y2'
        ))

        fig_dual_month.update_layout(
            title=dict(text=None),
            xaxis=dict(
                tickvals=list(range(1, 13)),
                ticktext=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
            ),
            yaxis=dict(title='Production (TWh)', color=PRIMARY_COLOR),
            yaxis2=dict(title='Visible Radiation (J/cm²)', 
                        color=SECONDARY_COLOR,
                        overlaying='y', 
                        side='right',
                        showgrid=False,), # Can't manage to  have a clean look, removing y2 grid
            template='plotly_dark',
            height=HEIGHT_GRAPHS,
            margin=dict(t=30, b=20, l=20, r=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.2,
                xanchor='center',
                x=0.5,
        ))
        
        st.plotly_chart(fig_dual_month, width='content', key='fig_dual_month')


# ---------------------------------------------------
# Fifth tab
# ---------------------------------------------------
with tab5:
    # Aggregations
    first_date = df_filtered['date'].min()
    latest_date = df_filtered['date'].max()

    # Aggregate to date level so we can properly compute values
    total_max_installations = (
        df_filtered[df_filtered['date'] == latest_date]
        ['installation_number']
        .sum()
        )
    total_max_capacity = (
        df_filtered[df_filtered['date'] == latest_date]
        ['capacity_power']
        .sum()
        )
    total_min_installations = (
        df_filtered[df_filtered['date'] == first_date]
        ['installation_number']
        .sum()
        )
    total_min_capacity = (
        df_filtered[df_filtered['date'] == first_date]
        ['capacity_power']
        .sum()
        )
    installation_growth = (total_max_installations - total_min_installations) * 100 / total_min_installations
    capacity_growth = (total_max_capacity - total_min_capacity) * 100 / total_min_capacity      

    
    df_filtered['Year']  = df_filtered['date'].dt.year
    df_filtered['Month'] = df_filtered['date'].dt.month

    yearly_deploy_df = (df_filtered
        .groupby('Year')[['installation_number', 'capacity_power']]
        .mean()
        .reset_index()
    )
    monthly_deploy_df = (df_filtered
        .groupby('Month')[['installation_number', 'capacity_power']]
        .mean()
        .reset_index()
    )
    growth_label = f'{min(full_years)} → {max(full_years)}'

    # --- KPIs ----------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('panel.svg')} **Total Installations**", unsafe_allow_html=True)
            st.metric(label='Total Installations', 
                      value=f'{total_max_installations:,.0f}',
                      label_visibility='hidden',
                      )

    with col2:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('growth.svg')} **Installation Growth {growth_label}**", unsafe_allow_html=True)
            st.metric(
                label='Installation Growth',
                value=f'{installation_growth:+.1f}%',
                delta_color='normal' if len(full_years) >= 2 else 'off',
                label_visibility='hidden',
            )

    with col3:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('prod.svg')} **Capacity Power (MW)**", unsafe_allow_html=True)
            st.metric(label='Avg Capacity Power', 
                      value=f'{total_max_capacity:,.0f}',
                      label_visibility='hidden',
                      )

    with col4:
        with st.container(border=True):
            st.markdown(f"{svg_to_img('growth.svg')} **Capacity Growth (MW) {growth_label}**", unsafe_allow_html=True)
            st.metric(
                label='Capacity Growth',
                value=f'{capacity_growth:+.1f}%',
                delta_color='normal' if len(full_years) >= 2 else 'off',
                label_visibility='hidden',
            )

    st.divider()

    # Graphs
    col1, col2 = st.columns(2)

    daily_install = (
        df_filtered
        .groupby('date')['installation_number']
        .sum()
        .reset_index()
    )
    daily_cap = (
        df_filtered
        .groupby('date')['capacity_power']
        .sum()
        .reset_index()
    )

    with col1:
        quarterly_install_df = (daily_install
            .groupby(pd.Grouper(key='date', freq='QE'))['installation_number']
            .max()
            .reset_index()
        )
        
        fig_install = go.Figure()
        fig_install.add_trace(go.Scatter(
            x=quarterly_install_df['date'],
            y=quarterly_install_df['installation_number'],
            mode='lines+markers',
            name='Installations',
            line=dict(color=PRIMARY_COLOR, width=2.5),
        ))
        fig_install.update_layout(
            title=dict(text=None),
            xaxis_title='Date',
            yaxis_title='Number of Installations',
            template='plotly_dark',
            height=HEIGHT_GRAPHS,
            margin=dict(t=30, b=60, l=20, r=20),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.markdown(f'**Installation Number Over Time**', unsafe_allow_html=True)
        st.plotly_chart(fig_install, width='content', key='fig_install')

    with col2:

        quaterly_cap_df = (daily_cap
            .groupby(pd.Grouper(key='date', freq='QE'))['capacity_power']
            .max()
            .reset_index()
        )
        fig_cap = go.Figure()
        fig_cap.add_trace(go.Scatter(
            x=quaterly_cap_df['date'],
            y=quaterly_cap_df['capacity_power'],
            mode='lines+markers',
            name='Capacity Power',
            line=dict(color=SECONDARY_COLOR, width=2.5),
        ))
        fig_cap.update_layout(
            title=dict(text=None),
            xaxis_title='Date',
            yaxis_title='Capacity Power (MW)',
            template='plotly_dark',
            height=HEIGHT_GRAPHS,
            margin=dict(t=30, b=60, l=20, r=20),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.markdown(f'**Capacity Power Over Time**', unsafe_allow_html=True)
        st.plotly_chart(fig_cap, width='content', key='fig_cap')


# ---------------------------------------------------
# Sixth tab
# ---------------------------------------------------
with tab6:
    st.markdown(f"{svg_to_img('glass.svg')} **Data Preview**", unsafe_allow_html=True)
    st.dataframe(df_filtered.head(10), width='content')
    
    st.markdown(f"{svg_to_img('download.svg')} [Download full dataset]({DATA_PATH})", unsafe_allow_html=True)

    st.markdown(f"{svg_to_img('DB.svg')} **Sources**", unsafe_allow_html=True)
    st.markdown("""
    | Source | Description | Link |
    |--------|-------------|------|
    | RTE France | Solar energy production by region | [rte-france.com](https://www.rte-france.com/donnees-publications/eco2mix-donnees-temps-reel/telecharger-indicateurs) |
    | Météo-France | Weather data (temperature, rainfall, wind) | [data.gouv.fr](https://www.data.gouv.fr/datasets/donnees-changement-climatique-sim-quotidienne) |
    | SDES | Open French government data portal | [statistiques.developpement-durable.gouv.fr](https://www.statistiques.developpement-durable.gouv.fr/tableau-de-bord-solaire-photovoltaique-premier-trimestre-2026) |
    """)