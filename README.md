# KPCL Spare Parts Demand Forecasting — Project Documentation

<div align="center">

![KPCL Logo](frontend/public/logo.png)

**AI-Powered Weekly Demand Forecasting for ACR SPARES**  
Kirloskar Pneumatic Co. Ltd.

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal?style=for-the-badge)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge)](https://react.dev)

</div>

---

## 📌 Overview

This project delivers a **production-ready AI forecasting system** for KPCL's spare parts demand planning. It combines classical time series models (AR, MA, SARIMA, Prophet) with ML-based approaches (XGBoost, Random Forest) to forecast weekly spare part quantities for **8 priority items** from the ACR SPARES model range.

The system surfaces forecasts through a modern React web dashboard, a live Dash analytics panel, and a REST API — all running locally as an integrated system.

---

## 📊 Dataset

| Property | Details |
|---|---|
| **Source** | `KPC___Despatch_Details_260924.xlsx` — KPCL internal despatch records |
| **Model Filter** | ACR SPARES only |
| **Item Selection** | 8 items selected by KPCL based on operational priority |
| **Training Columns** | `OA_DATE`, `ITEM_CODE`, `QTY`, `MODEL`, `ITEM_DESCRIPTION` |
| **Training Period** | June 2021 → December 2023 (4,769 rows → weekly aggregate) |
| **Test Period** | January 2024 → September 2024 (12 hold-out weeks per item) |
| **Granularity** | Weekly aggregated QTY per item |

### 8 Tracked Items

| Item Code | Description | Rows | Champion Model |
|---|---|---|---|
| `082.03.110.50.` | Piston KC/KCX | 1,055 | AR |
| `082.04.030.50.` | Bearing Bush Big End Con Rod KC/KCX | 1,052 | AR |
| `082.08.000.50.` | Shaft Seal Assembly KC/KCX | 973 | Prophet |
| `336.40.401.50.` | Cylinder Liner KC/KCX | 932 | AR |
| `993.00.311.00.` | Gasket Suct Strainer & Side Cover KC/KCX | 337 | AR |
| `085.00.003.50.` | Kirloskar Advantage Oil, 20 Ltr Drum | 243 | MA |
| `084.19.001.50.` | Gasket Set KC4 | 150 | MA |
| `351.03.301.50.` | Liner Cylinder AC70 | 27 | MA |

---


### Local Development

```
┌─────────────────────────────────────────────────────────────┐
│                    Local Dev Environment                     │
│                                                             │
│  ┌────────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │ React Frontend │   │ FastAPI      │   │ Dash Analytics │  │
│  │ localhost:5173 │   │ localhost:8000│   │ localhost:8050 │  │
│  └──────┬─────────┘   └──────┬───────┘   └───────┬────────┘  │
│         │                    │                   │            │
│         └────────────────────┴───────────────────┘            │
│                    Vite Proxy (local dev)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Forecasting Pipeline

### Feature Engineering (ML Models)

| Feature | Description |
|---|---|
| **Lag Features** | QTY at lag 1, 2, 3, 4, 8, 12 weeks |
| **Rolling Mean** | 4-week and 12-week rolling average |
| **Rolling Std** | 4-week rolling standard deviation |
| **Temporal** | Week-of-year, Month, Quarter |

### Model Competition

Every item is evaluated across three model families:

```
┌─────────────────────────────────────────────────────┐
│  ML Models         Time Series        Auto           │
│  ─────────         ────────────       ────           │
│  XGBoost           AR                 Auto-SARIMA    │
│  Random Forest     MA                                │
│  Ridge Regression  ARMA                              │
│                    ARIMA                             │
│                    SARIMA                            │
│                    Prophet                           │
└─────────────────────────────────────────────────────┘
         ↓
  All models scored on 12 hold-out weeks (RMSE)
         ↓
  Lowest RMSE → "Champion Model" for that item
```

### MSTL Decomposition (Analysis Tab)

Weekly demand data is decomposed using **MSTL (Multiple Seasonal-Trend decomposition using Loess)** into:
- **Trend** — long-term movement
- **Seasonal** — regular cyclic patterns (52-week period)
- **Residual** — unexplained noise

---

## 🗂️ Project Structure

```
kpcl_selected_item_forecasting/
│
├── backend/                  ← All Python logic & API
│   ├── api/
│   │   └── main.py           ← FastAPI backend (all /api/* endpoints)
│   ├── data/
│   │   └── data_preparation.py ← Data cleaning & weekly aggregation
│   ├── modeling/
│   │   ├── compare_models_rmse.py
│   │   ├── train_forecast_all_models.py
│   │   └── train_forecast_autosarima.py
│   ├── visualization/
│   │   └── dashboard.py      ← Dash analytics dashboard
│   └── forecast_validation/  ← Logic for scoring & error metrics
│
├── frontend/                 ← React web application
│   ├── src/App.jsx           ← Main interface logic
│   ├── dist/                 ← Production build (for distribution)
│   └── vite.config.js        ← Dev server + proxy config
│
├── data/
│   ├── raw/                  ← Source records (XLSX/CSV)
│   └── processed/            ← Model-ready datasets & results
│
├── models/                   ← Saved champion model files (.skl/.pkl)
├── reports/figures/          ← Static visualization exports
│
├── app.py                    ← Integrated entry point (FastAPI + Dash)
├── start.ps1                 ← Local dev: Start all 3 servers
├── run_pipeline.ps1          ← Full 10-step ML automation
└── requirements.txt          ← Python dependencies
```

---

## ⚙️ API Reference

Base URL (local): `http://localhost:8000`

| Endpoint | Method | Description |
|---|---|---|
| `/api/items` | GET | List all 8 tracked item codes |
| `/api/global_metrics` | GET | Portfolio-level KPIs (total revenue, QTY, tax, avg order) |
| `/api/metrics/{item}` | GET | Per-item RMSE metrics for all model families |
| `/api/comparison/{item}` | GET | Champion model summary |
| `/api/forecast_comparison/{item}` | GET | ML vs TS vs Champion forecast data |
| `/api/validation/{item}` | GET | Champion model vs actuals (12-week hold-out) |
| `/api/aggregate_forecast` | GET | Portfolio-wide demand aggregate |
| `/api/mstl/{item}` | GET | MSTL decomposition (Trend, Seasonal, Residual) |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive Swagger UI |
| `/analytics/` | GET | Dash analytics dashboard |

---

## 🖥️ Web Application Tabs

### 🏠 Home
Displays the **Kirloskar Analytics Dash Dashboard** in an embedded panel — Regional & Revenue Analytics, transporter analysis, year-wise sales trends.

### 📊 Analysis
Interactive **MSTL Decomposition** for each item — 4 stacked Recharts panels (Observed, Trend, Seasonal, Residual). Select any of the 8 items from the dropdown.

### 📈 Forecasting
**Comparative forecast view** — ML model vs Time Series vs Champion model plotted on a single interactive chart with confidence intervals. Select item → Generate Forecast.

### ℹ️ About
Documentation panel covering dataset overview, training/test split, feature engineering, champion model table, and the full forecasting pipeline methodology.

---

## 🏁 Getting Started (Step-by-Step)

Follow these steps to set up the project on your local machine.

### 1. Prerequisites
Ensure you have the following installed:
*   **Python 3.11+**: [Download here](https://www.python.org/downloads/)
*   **Node.js 18+**: [Download here](https://nodejs.org/)
*   **Git**: [Download here](https://git-scm.com/)

### 2. Clone the Repository
```bash
git clone https://github.com/adeebanoorr/Demand-Forecasting-for-spare-parts.git
cd Demand-Forecasting-for-spare-parts
```

### 3. Backend Environment Setup
Create a virtual environment to isolate project dependencies:
```powershell
# Create environment
python -m venv myenv

# Activate environment
.\myenv\Scripts\activate

# Install required Python libraries
pip install -r requirements.txt
```

### 4. Frontend Environment Setup
Navigate to the frontend folder and install web dependencies:
```powershell
cd frontend
npm install
cd ..
```

### 5. Initialize the ML Models
Run the full automation pipeline to generate pre-trained models and processed data (takes ~10–15 minutes):
```powershell
.\run_pipeline.ps1
```

### 6. Launch the Application
Once the pipeline is complete, start the integrated local server environment:
```powershell
.\start.ps1
```
The application will be available at **`http://localhost:5173`**.

---

## 🚀 Local Development Reference

### Start All Servers
```powershell
.\start.ps1
```

This launches three servers in separate windows:

| Server | URL | Description |
|---|---|---|
| Dash Dashboard | http://localhost:8050 | Analytics dashboard |
| FastAPI Backend | http://localhost:8000 | REST API + Swagger UI at `/docs` |
| React Frontend | http://localhost:5173 | Main web app (Vite + proxy) |

The Vite dev server proxies `/analytics/` → `:8050` and `/api` → `:8000`, so the app works seamlessly from a single origin during development.

### Run the Full ML Pipeline
```powershell
.\run_pipeline.ps1
```

Steps:
1. **Data Preparation**: Cleans raw XLSX and aggregates to weekly CSV.
2. **MSTL Analysis**: Performs seasonal-trend decomposition.
3. **ML Comparison**: Scores XGBoost, Random Forest, etc. (RMSE).
4. **ML Training**: Trains the champion Classical ML model.
5. **TS Comparison**: Scores AR, MA, Prophet, ARIMA (RMSE).
6. **Auto-SARIMA**: Exhaustive seasonal parameter search.
7. **ML Validation**: Generates hold-out sets for ML models.
8. **SARIMA Validation**: Generates hold-out sets for Auto-SARIMA.
9. **Final Forecast**: Produces 12-week output for the dashboard.
10. **Global Summary**: Unified ranking for the home tab.

---


## 📦 Core Technology Stack

### Backend (Python)
*   **FastAPI**: High-performance REST API framework.
*   **Statsmodels**: Classical time series models (AR, MA, ARIMA, SARIMA, MSTL).
*   **Prophet**: Meta's forecasting library for strong seasonality patterns.
*   **Scikit-Learn / XGBoost**: ML-based forecasting (Random Forest, Gradient Boosting).
*   **Pandas / NumPy**: Data manipulation and numerical processing.
*   **Dash / Plotly**: Integrated analytics dashboard for revenue reporting.
*   **Gunicorn + Uvicorn**: ASGI/WSGI server components.

### Frontend (JavaScript/React)
*   **React + Vite**: Modern, fast frontend framework and build tool.
*   **Recharts**: Interactive charting for dynamic forecast and MSTL plots.
*   **Tailwind CSS**: Utility-first CSS framework for the enterprise dashboard UI.
*   **Lucide React**: Consistent icon library.


## 📄 License

MIT License — see [LICENSE](LICENSE)
