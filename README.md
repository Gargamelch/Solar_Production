---
title: "Streamlit"
emoji: ⚡
colorFrom: yellow
colorTo: green
sdk: docker
sdk_version: 0.79.0
app_file: app.py
pinned: false
license: gpl-3.0
short_description: Solar Energy Production built with scikit-learn and streamlit
---
# ☀️ Solar France — Solar Energy Production Dashboard

An interactive dashboard for analyzing and predicting solar energy production across French regions, built with Streamlit and deployed on Hugging Face Spaces.

[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Solar__Production-yellow)](https://huggingface.co/spaces/Gargamelch/Solar_Production)
[![GitHub](https://img.shields.io/badge/GitHub-Solar__Production-181717?style=flat&logo=github)](https://github.com/Gargamelch/Solar_Production)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Data Sources](#data-sources)
- [Dataset Description](#dataset-description)
- [Installation](#installation)
- [Usage](#usage)
- [Docker](#docker)
- [Machine Learning](#machine-learning)

---

## 🔍 Overview

This project combines meteorological data from **Météo-France** with electricity production data from **RTE** (Réseau de Transport d'Électricité) to analyze and predict solar energy production across the 12 metropolitan French regions from 2020 to 2026.

The app includes two main pages:
- **Dashboard** — historical production analysis with interactive charts and regional map
- **Predictions** — next-day solar production forecast per m² of solar panel

---

## ✨ Features

- 📊 Interactive production trends (yearly, monthly, seasonal)
- 🗺️ Regional choropleth map with ranking
- 🤖 Next-day solar production prediction (J+1)
- ⚡ Per-m² production estimation based on panel surface input
- 🔍 Filter by year range and region
- 📦 Dockerized and deployed on Hugging Face Spaces

---

## 📁 Project Structure

```
📁 Solar_Production
├── 🐳 Dockerfile
├── 📄 requirements.txt
├── 🗒️ app.py                          ← Navigation entry point
├── 🗒️ utils.py                        ← Data loading & caching
├── 📁 pages
│   ├── 🗒️ 0_Dashboard.py              ← Production analysis dashboard
│   └── 🗒️ 1_Predictions.py            ← ML prediction page
└── 📁 data
    ├── 📁 coordinates
    │   ├── 📄 departements-20180101.shp
    │   └── 📄 ...
    ├── 📁 Meteo-France
    │   ├── 📄 QUOT_SIM2_2010-2019.csv
    │   └── 📄 QUOT_SIM2_previous-2020-202605.csv
    ├── 📁 RTE
    │   ├── 📁 Regions
    │   │   ├── 📄 eCO2mix_RTE_*_2013.xls
    │   │   └── 📄 ...
    │   ├── 📄 rte_regions_2013.csv
    │   └── 📄 ...
    └── 📁 solar_installations
        └── 📄 statistiques_sdes_2026_t1_*.xlsx
```

---

## 🗃️ Data Sources

| Source | Description | Format | Coverage |
|--------|-------------|--------|----------|
| ⚡ [RTE eCO2mix](https://www.rte-france.com/eco2mix) | Solar electricity production by region | `.xls` (tab-separated) | 2013–2026 |
| 🌤️ [Météo-France SIM2](https://www.meteofrance.fr) | Daily meteorological data on a 8km grid | `.csv` | 2010–2026 |
| ☀️ [SDES](https://www.statistiques.developpement-durable.gouv.fr) | Quarterly installed solar capacity by region | `.xlsx` | 2005–2026 |
| 🗺️ [OpenStreetMap / data.gouv.fr](https://www.data.gouv.fr) | French département boundaries (shapefile) | `.shp` | - |

---

## 📊 Dataset Description

The final merged dataset `solar_prod_predictions.csv` contains daily data per region:

| Column | Description | Unit | Precision | Source |
|--------|-------------|------|-----------|--------|
| `date` | Measurement date | YYYYMMDD | - | 🌤️ Meteo-France |
| `region` | French administrative region | - | - | 🔮 Engineered |
| `snowfall` | Solid precipitation (daily cumul 06UTC-06UTC) | mm | 1/10 | 🌤️ Meteo-France |
| `rainfall` | Liquid precipitation (daily cumul 06UTC-06UTC) | mm | 1/10 | 🌤️ Meteo-France |
| `daily_avg_temp` | Average daily temperature (00UTC-00UTC) | °C | 1/10 | 🌤️ Meteo-France |
| `daily_avg_wind_speed` | Average daily wind speed (00UTC-00UTC) | m/s | 1/10 | 🌤️ Meteo-France |
| `daily_avg_specific_humidity` | Specific humidity (00UTC-00UTC) | g/kg | - | 🌤️ Meteo-France |
| `atmospheric_radiation` | Atmospheric radiation (daily cumul 00UTC-00UTC) | J/cm² | - | 🌤️ Meteo-France |
| `visible_radiation` | Visible radiation (daily cumul 00UTC-00UTC) | J/cm² | - | 🌤️ Meteo-France |
| `daily_avg_relative_humidity` | Relative humidity (00UTC-00UTC) | % | - | 🌤️ Meteo-France |
| `total_evapotranspiration` | Total evapotranspiration (daily cumul 06UTC-06UTC) | mm | 1/10 | 🌤️ Meteo-France |
| `potential_evapotranspiration` | Potential evapotranspiration - Penman-Monteith FAO-56 | mm | 1/10 | 🌤️ Meteo-France |
| `effective_rainfall` | Effective rainfall (daily cumul 06UTC-06UTC) | mm | 1/10 | 🌤️ Meteo-France |
| `daily_avg_soil_moisture_index` | Soil moisture index (06UTC-06UTC) | % | - | 🌤️ Meteo-France |
| `soil_drought_index_10d` | 10-day integrated soil drought index | - | - | 🌤️ Meteo-France |
| `drainage` | Drainage (daily cumul 06UTC-06UTC) | mm | 1/10 | 🌤️ Meteo-France |
| `runoff` | Runoff (daily cumul 06UTC-06UTC) | mm | 1/10 | 🌤️ Meteo-France |
| `daily_avg_snow_water` | Snow water equivalent - daily average (06UTC-06UTC) | mm | 1/10 | 🌤️ Meteo-France |
| `snow_water_equivalent_6h` | Snow water equivalent at 06UTC | mm | 1/10 | 🌤️ Meteo-France |
| `daily_avg_snow_depth` | Snow depth - daily average (06UTC-06UTC) | m | - | 🌤️ Meteo-France |
| `snow_depth_6h` | Snow depth at 06UTC | m | - | 🌤️ Meteo-France |
| `max_snow_depth` | Maximum hourly snow depth during the day | m | - | 🌤️ Meteo-France |
| `daily_avg_snow_cover_fraction` | Snow cover fraction - daily average (06UTC-06UTC) | % | - | 🌤️ Meteo-France |
| `snowmelt_runoff` | Runoff at the base of the snowpack (daily cumul 06UTC-06UTC) | mm | - | 🌤️ Meteo-France |
| `root_liquid_water` | Liquid water content in root layer at 06UTC | m³/m³ | - | 🌤️ Meteo-France |
| `root_frozen_water` | Frozen water content in root layer at 06UTC | m³/m³ | - | 🌤️ Meteo-France |
| `min_temp` | Minimum temperature over 24h (18UTC-18UTC) | °C | 1/10 | 🌤️ Meteo-France |
| `max_temp` | Maximum temperature over 24h (06UTC-06UTC) | °C | 1/10 | 🌤️ Meteo-France |
| `solar` | Solar power production | MW | - | ⚡ RTE |
| `TWh` | Solar power production | TWh | - | ⚡ RTE |
| `installation_number` | Number of connected solar installations | - | - | ☀️ SDES |
| `capacity_power` | Installed solar capacity | MW | - | ☀️ SDES |
| `target` | Next day visible radiation (J+1) | J/cm² | - | 🔮 Engineered |
| `radiation_J1` | Visible radiation 1 day ago | J/cm² | - | 🔮 Engineered |
| `radiation_J2` | Visible radiation 2 days ago | J/cm² | - | 🔮 Engineered |
| `radiation_J3` | Visible radiation 3 days ago | J/cm² | - | 🔮 Engineered |
| `day_of_year` | Day of year (1–366) | - | - | 🔮 Engineered |
| `day_sin` | Sine encoding of day of year | - | - | 🔮 Engineered |
| `day_cos` | Cosine encoding of day of year | - | - | 🔮 Engineered |

---

## 🚀 Installation

### Prerequisites

- Python 3.13+
- pip

### Local setup

```bash
# Clone the repository
git clone https://github.com/Gargamelch/Solar_Production.git
cd Solar_Production

# Create and activate a virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---

## 🐳 Docker

```bash
# Build the image
docker build -t solar-app .

# Run locally
docker run -p 8501:8501 solar-app
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

The production image is deployed on **Hugging Face Spaces** at port `7860`.

---

## 🤖 Machine Learning

The prediction model estimates **next-day solar production per m²** using a supervised regression approach.

### Features used

| Category | Features |
|----------|----------|
| Radiation | `visible_radiation`, `atmospheric_radiation`, `radiation_J1`, `radiation_J2`, `radiation_J3` |
| Weather | `daily_avg_temp`, `rainfall`, `daily_avg_wind_speed`, `daily_avg_relative_humidity` |
| Seasonality | `day_sin`, `day_cos`, `Month` |
| Capacity | `puissance`, `nombre` |

### Pipeline

```
Raw features → StandardScaler → Linear Regression → Predicted J+1 production
```

### Train / Test split

| Set | Period |
|-----|--------|
| Train | 2020 → 2023 |
| Test | 2024 → 2025 |

> ⚠️ Data is sorted chronologically before splitting — no random shuffling is applied to avoid data leakage from future to past.

### Evaluation metrics

- **R²** — coefficient of determination
- **MAE** — mean absolute error
- **RMSE** — root mean squared error

---

## 📝 Notes

- Corsica (`2A`, `2B`) is excluded from the analysis as it is not covered by RTE's regional data
- Installed capacity data is quarterly and forward-filled to daily frequency
- Météo-France grid points (Lambert II étendu projection) are spatially joined to French regions using OpenStreetMap shapefiles
- Production values are in TWh; per-m² estimates assume **20% panel efficiency**

