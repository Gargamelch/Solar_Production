import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
import scipy.stats as stats
import streamlit as st
from scipy.stats import gaussian_kde

# Load our custom module from utils.py
from utils import load_data, load_geojson



# --- Data loading----------------------------------
solar_prod_df = load_data()
geojson = load_geojson()
# Filtering to < 2026 (for complete years graphs)
solar_prod_full_year_df = solar_prod_df.loc[solar_prod_df['Year'] < 2026, :]



# --- Sidebar filters----------------------------------  
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



# --- Title and page config----------------------------------
st.set_page_config(page_title='☀️ Solar Production', layout='wide', page_icon='☀️')

year_range = str(year_min) if year_min == year_max else f'{year_min} - {year_max}'
st.title(f'☀️ Solar Energy Production — France ({year_range})')
st.caption(f'Data sources: RTE (electricity) · Meteo-France (weather) · {year_range}')



# --- Tab settings----------------------------------
tab1, tab2 = st.tabs([
    'Production Analysis',
    'Regional Distribution',
])



# --- First tab ----------------------------------
with tab1:
    # KPI metrics
    st.header('📊 Solar production overview')
    col1, col2, col3, col4 = st.columns(4)

    # Count days per year to detect partial years
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
            st.metric(
                label='⚡ Total Production (TWh)',
                value=f'{df_filtered['TWh'].sum():.2f}',
                delta='',
                delta_color='off'
            )

    with col2:
        with st.container(border=True):
            st.metric(label='📈 Daily Average (MWh)',
                value=f'{df_filtered['TWh'].mean() * 1_000_000:.2f}',
                delta='',
                delta_color='off'
            )

    with col3:
        with st.container(border=True):
            delta_color = 'normal' if len(full_years) >= 2 else 'off'
            st.metric(label=f'📊 Evolution (MWh) {year_min} → {year_max}',
                value=f'{growth:+.1f}%',
                delta_color=delta_color,
            )

    with col4:
        with st.container(border=True):
            delta_color = 'normal' if len(full_years) >= 2 else 'off'
            st.metric(label=f'📊 Evolution {year_min} → {year_max}',
                value=f'{growth:+.1f}%',
                delta_color=delta_color,
            )

    with st.expander('🔍 Raw data'):
        st.dataframe(df_filtered, width='content')

    st.divider()

    # Yearly production
    st.header('📅 Yearly Production')
    col1, col2 = st.columns(2)

    yearly_df['Year'] = yearly_df['date'].dt.year

    # Linear trend
    with col1:
        x_num = np.arange(len(yearly_df))
        slope, intercept, r, *_ = stats.linregress(x_num, yearly_df['TWh'])
        trend_y = slope * x_num + intercept

        fig_yearly = go.Figure()
        fig_yearly.add_trace(go.Bar(
            x=yearly_df['Year'], y=yearly_df['TWh'],
            marker=dict(color=yearly_df['TWh'], colorscale='YlOrBr', showscale=False),
            name='Production', hovertemplate='%{x}: %{y:.2f} TWh'
        ))
        fig_yearly.add_trace(go.Scatter(
            x=yearly_df['Year'], 
            y=trend_y,
            mode='lines', 
            line=dict(color='orange', dash='dash', width=2),
            name=f'Trend (R²={r**2:.2f})'
        ))
        fig_yearly.update_layout(
            title='Solar Energy Production per Year',
            xaxis_title='Year', 
            yaxis_title='Production (TWh)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            hovermode='x unified', 
            template='plotly_dark'
        )
        st.plotly_chart(fig_yearly, width='content')

    with col2:
        fig_seasonal = px.line(
            monthly_df, 
            x='date',
            y='TWh', 
            markers=True,
            title='Solar energy production seasonality',
            template='plotly_dark',
            color_discrete_sequence=['#FF9800'],
        )

        # Update Title styling to match fontweight='bold'
        fig_seasonal.update_layout(
            title_font=dict(weight='bold', size=18),
            xaxis_title='date', 
            yaxis_title='Production (TWh)'
        )


        st.plotly_chart(fig_seasonal, width='content')

    st.divider()


    # Seasonality
    st.header('🌸 Seasonality — Monthly Production per Year')

    monthly_df['Year']  = monthly_df['date'].dt.year
    monthly_df['Month'] = monthly_df['date'].dt.month

    fig_seasonal = px.line(
        monthly_df, x='Month', y='TWh', color='Year',
        labels={'TWh': 'Production (TWh)', 'Month': 'Month'},
        title='Monthly Solar Production per Year',
        template='plotly_dark',
        color_discrete_sequence=pc.sequential.Oranges,
    )
    fig_seasonal.update_xaxes(
        tickvals=list(range(1, 13)),
        ticktext=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    )

    st.plotly_chart(fig_seasonal, width='content')

    st.divider()

    # Convert th MWh for a better representation
    solar_prod_mwh_df = df_filtered.copy()
    solar_prod_mwh_df['MWh'] = solar_prod_mwh_df['TWh'].mul(1_000_000)
    solar_prod_mwh_df.drop(columns='TWh', inplace=True)

    # Histogram
    fig_wh = px.histogram(
        solar_prod_mwh_df,
        x='MWh',
        nbins=50,
        histnorm='density',
        color_discrete_sequence=['#FF9800']
    )

    # KDE
    kde = gaussian_kde(solar_prod_mwh_df['MWh'])
    x_grid = np.linspace(solar_prod_mwh_df['MWh'].min(), solar_prod_mwh_df['MWh'].max(), 500)

    fig_wh.add_trace(
        go.Scatter(
            x=x_grid,
            y=kde(x_grid),
            mode='lines',
            name='KDE',
            line=dict(color='#FF9800', width=2),
        )
    )

    fig_wh.update_layout(
        title='Distribution of daily solar production',
        xaxis_title='Production (MWh)',
        yaxis_title='Density'
    )

    st.plotly_chart(fig_wh, width='content')

    st.divider()

    # Year-over-year comparison
    st.header('📊 Year-over-Year Comparison')

    col1, col2 = st.columns(2)

    with col1:
        # Heatmap: year vs month
        pivot = monthly_df.pivot(index='Year', columns='Month', values='TWh').fillna(0)
        pivot.columns = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        fig_heat = px.imshow(
            pivot, color_continuous_scale='YlOrBr',
            labels=dict(color='TWh'),
            title='Production Heatmap (Year x Month)',
            template='plotly_dark',
            height=500 
        )
        st.plotly_chart(fig_heat, width='content')

    with col2:
        # Cumulative production per year
        df_filtered_sorted = df_filtered.sort_values('date')
        df_filtered_sorted['Cumulative'] = df_filtered_sorted.groupby('Year')['TWh'].cumsum()
        fig_cum = px.line(
            df_filtered_sorted, x='Month', y='Cumulative', color='Year',
            labels={'Cumulative': 'Cumulative TWh', 'Month': 'Month'},
            title='Cumulative Production per Year',
            template='plotly_dark',
            height=500,
            color_discrete_sequence=pc.sequential.Oranges,
        )
        fig_cum.update_xaxes(
            tickvals=list(range(1, 13)),
            ticktext=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        )
        st.plotly_chart(fig_cum, width='content')



# --- Second tab ----------------------------------
with tab2:
    st.header('🗺️ Solar Production by Region')
    # Aggregate data by region for the selected years
    region_prod = (
        df_filtered
        .groupby('region', as_index=False)
        .agg(
            total_TWh=('TWh', 'sum'),
            avg_TWh=('TWh', 'mean')
        )
    )

    # Approximate regional coordinates for map display
    region_coords = {
        'Auvergne-Rhône-Alpes': (45.76, 4.84),
        'Bourgogne-Franche-Comté': (47.32, 5.04),
        'Bretagne': (48.11, -1.68),
        'Centre-Val de Loire': (47.90, 1.91),
        'Centre-Val-de-Loire': (47.90, 1.91),
        'Grand Est': (48.58, 7.75),
        'Grand-Est': (48.58, 7.75),
        'Hauts-de-France': (50.63, 3.06),
        'Île-de-France': (48.85, 2.35),
        'Ile-de-France': (48.85, 2.35),
        'Normandie': (49.18, -0.37),
        'Nouvelle-Aquitaine': (44.84, -0.58),
        'Occitanie': (43.60, 1.44),
        'Pays de la Loire': (47.22, -1.55),
        'Pays-de-la-Loire': (47.22, -1.55),
        "Provence-Alpes-Côte d'Azur": (43.30, 5.37),
        'PACA': (43.30, 5.37),
        'Corse': (42.15, 9.08)
    }

    region_prod['lat'] = region_prod['region'].map(lambda x: region_coords.get(x, (None, None))[0])
    region_prod['lon'] = region_prod['region'].map(lambda x: region_coords.get(x, (None, None))[1])

    # Keep only regions with coordinates
    region_prod = region_prod.dropna(subset=['lat', 'lon'])

    # Layout with map and ranking
    map_col, rank_col = st.columns([2, 1])
    HEIGHT_2=650

    with map_col:
        fig_map = px.scatter_geo(
            region_prod,
            lat='lat',
            lon='lon',
            size='total_TWh',
            color='total_TWh',
            hover_name='region',
            hover_data={
                'total_TWh': ':.2f',
                'avg_TWh': ':.4f',
                'lat': False,
                'lon': False
            },
            color_continuous_scale='YlOrRd',
            size_max=55,
            projection='natural earth',
            #title='Total Solar Production by Region',
            labels={
                'total_TWh': 'Total production (TWh)',
                'avg_TWh': 'Average daily production (TWh)'
            },
            template='plotly_dark'
        )

        fig_map.update_geos(
            visible=True,
            resolution=50,
            showcountries=True,
            countrycolor='white',
            showland=True,
            landcolor='rgb(35,35,35)',
            showocean=True,
            oceancolor='rgb(15,20,35)',
            lataxis_range=[41, 52],
            lonaxis_range=[-6, 10],
            center=dict(lat=46.5, lon=2)
        )

        fig_map.update_layout(
                height=HEIGHT_2,
                margin=dict(l=0, r=0, t=0, b=0),
                coloraxis_colorbar=dict(
                    title='TWh',
                    len=0.7,
                    y=0.5
            )
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