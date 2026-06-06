import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import scipy.stats as stats
import streamlit as st

### Files paths ################################################################
solar_prod = "data/solar_prod.csv"
rte = "data/rte.csv"

### Page config ################################################################
st.set_page_config(page_title="☀️ Solar Production", layout="wide", page_icon="☀️")

st.title("☀️ Solar Energy Production — France")
st.caption("Data sources: RTE (electricity) · Meteo-France (weather) · 2012–2026")

### Palette ####################################################################
PALETTE = ["#345fff", "#e142d5", "#ff4b9b", "#ffc352", "#f9f871",
           "#9bde7e", "#4bbc8e", "#039590", "#1c6e7d", "#2f4858",
           "#ff6b6b", "#ffa07a", "#20b2aa", "#87ceeb"]

### Load data ##################################################################
@st.cache_data
def load_data():
    df = pd.read_csv(solar_prod, parse_dates=["date"])
    df["Year"]  = df["date"].dt.year
    df["Month"] = df["date"].dt.month
    df["Month_name"] = df["date"].dt.strftime("%b") # Month_name with the abbreviated month
    return df

df = load_data()

### Sidebar filters ############################################################
with st.sidebar:
    st.header("🔧 Filters")
    years = sorted(df["Year"].unique())
    select_all = st.checkbox("Select all years", value=True)
    if select_all:
        selected_years = years
    else:
        selected_years = st.multiselect("Years", years, default=[years[-1]])
    if not selected_years:
        selected_years = years
    st.divider()
    st.caption("☀️ Solar Production EDA")

df_filtered = df[df["Year"].isin(selected_years)]


### KPI metrics ###############################################################
st.header("📊 Overview")
col1, col2, col3, col4 = st.columns(4)

# Count days per year to detect partial years
days_per_year = df_filtered.groupby('Year')['date'].count()     # Count the number of days for every year
full_years = days_per_year[days_per_year >= 365].index.tolist() # List the full years in the dataset so growth is correct

if len(full_years) >= 2:    # If there's a least 2 more full years selected we can calculate growth                                             
    first_year_avg = df_filtered[df_filtered['Year'] == min(full_years)]['TWh'].mean()
    last_year_avg  = df_filtered[df_filtered['Year'] == max(full_years)]['TWh'].mean()
    growth = ((last_year_avg - first_year_avg) / first_year_avg * 100)
    growth_label = f"📊 Growth ({min(full_years)} → {max(full_years)})"
else:                       # If less than 2 full years are selected, show 0
    growth = 0
    growth_label = "📊 Growth (n/a)"

with col1:
    with st.container(border=True):
        st.caption("📅 Date range")
        st.write(f"{df_filtered['date'].min().date()} → {df_filtered['date'].max().date()}")

with col2:
    with st.container(border=True):
        st.caption("⚡ Total (TWh)")
        st.write(f"{df_filtered['TWh'].sum():.2f}")

with col3:
    with st.container(border=True):
        st.caption("📈 Daily avg (TWh)")
        st.write(f"{df_filtered['TWh'].mean():.4f}")

with col4:
    with st.container(border=True):
        st.caption(f"📊 Growth ({min(selected_years)} → {max(selected_years)})")
        st.write(f"{growth:+.1f}%")

with st.expander("🔍 Raw data"):
    st.dataframe(df_filtered, use_container_width=True)

st.divider()

### Yearly production ##########################################################
st.header("📅 Yearly Production")

yearly_df = (df_filtered
             .groupby(pd.Grouper(key="date", freq="YE"))["TWh"]
             .sum().reset_index())
yearly_df["Year"] = yearly_df["date"].dt.year

# Linear trend
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
    mode="lines", line=dict(color="red", dash="dash", width=2),
    name=f"Trend (R²={r**2:.2f})"
))
fig_yearly.update_layout(
    title="Solar Energy Production per Year",
    xaxis_title="Year", yaxis_title="Production (TWh)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    hovermode="x unified", template="plotly_dark"
)
st.plotly_chart(fig_yearly, use_container_width=True)

st.divider()

### Seasonality ################################################################
st.header("🌸 Seasonality — Monthly Production per Year")

month_year_df = (df_filtered
                 .groupby(pd.Grouper(key="date", freq="ME"))["TWh"]
                 .sum().reset_index())
month_year_df["Year"]  = month_year_df["date"].dt.year
month_year_df["Month"] = month_year_df["date"].dt.month

fig_seasonal = px.line(
    month_year_df, x="Month", y="TWh", color="Year",
    color_discrete_sequence=PALETTE,
    labels={"TWh": "Production (TWh)", "Month": "Month"},
    title="Monthly Solar Production per Year",
    template="plotly_dark"
)
fig_seasonal.update_xaxes(
    tickvals=list(range(1, 13)),
    ticktext=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
)
# Mark partial years (only 1 month of data)
partial = month_year_df.groupby("Year").filter(lambda x: len(x) == 1)
if not partial.empty:
    fig_seasonal.add_trace(go.Scatter(
        x=partial["Month"], y=partial["TWh"],
        mode="markers", marker=dict(color="red", size=10, symbol="circle-dot"),
        name="Partial year"
    ))
st.plotly_chart(fig_seasonal, use_container_width=True)

st.divider()

### Monthly boxplot ############################################################
st.header("📦 Production Distribution by Month")

month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
fig_box = px.box(
    df_filtered, x="Month_name", y="TWh",
    category_orders={"Month_name": month_order},
    color="Month_name", color_discrete_sequence=PALETTE,
    labels={"TWh": "Production (TWh)", "Month_name": "Month"},
    title="Daily Solar Production Distribution by Month",
    template="plotly_dark",
    height=500
)
fig_box.update_layout(showlegend=False)
st.plotly_chart(fig_box, use_container_width=True)

st.divider()

### Year-over-year comparison ##################################################
st.header("📊 Year-over-Year Comparison")

col1, col2 = st.columns(2)

with col1:
    # Heatmap: year vs month
    pivot = month_year_df.pivot(index="Year", columns="Month", values="TWh").fillna(0)
    pivot.columns = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    fig_heat = px.imshow(
        pivot, color_continuous_scale="YlOrRd",
        labels=dict(color="TWh"),
        title="Production Heatmap (Year × Month)",
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
