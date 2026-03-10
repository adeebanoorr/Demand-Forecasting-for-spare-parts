# KPCL Spare Parts Demand Forecasting — Project Documentation

<div align="center">

![Kirloskar Logo](src/webapp/public/logo.png)

**AI-Powered Weekly Demand Forecasting for ACR SPARES**  
Kirloskar Pneumatic Co. Ltd. | Production-Ready Deployment on Railway

[![Live App](https://img.shields.io/badge/Live_App-Railway-brightgreen?style=for-the-badge)](https://web-production-4bd43.up.railway.app/)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal?style=for-the-badge)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge)](https://react.dev)

</div>

---

## 📌 Overview

This project delivers a **production-ready AI forecasting system** for KPCL's spare parts demand planning. It combines classical time series models (AR, MA, SARIMA, Prophet) with ML-based approaches (XGBoost, Random Forest) to forecast weekly spare part quantities for **8 priority items** from the ACR SPARES model range.

The system surfaces forecasts through a modern web dashboard, a live Dash analytics panel, and a REST API — all deployed as a single service on Railway.

---

## 📊 Dataset

| Property | Details |
|---|---|
| **Source** | `KPC___Despatch_Details_260924.xlsx` — KPCL internal despatch records |
| **Model Filter** | ACR SPARES only |
| **Item Selection** | 8 highest-priority items by order volume |
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

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KPCL Forecasting Platform                 │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │ React Frontend│   │ FastAPI      │   │ Dash Analytics │  │
│  │ Vite + Recharts│  │ Backend API  │   │ Plotly + DBC   │  │
│  │ localhost:5173│   │ localhost:8000│  │ localhost:8050 │  │
│  └──────┬───────┘   └──────┬───────┘   └───────┬────────┘  │
│         │                  │                   │            │
│         └──────────────────┴───────────────────┘            │
│                    Vite Proxy (local dev)                    │
│                                                             │
│  ══════════════════[ Production: Railway ]═════════════════ │
│  Single FastAPI service serves:                             │
│  /api/*         → FastAPI endpoints                         │
│  /analytics/    → Dash (WSGIMiddleware)                     │
│  /*             → React dist (StaticFiles)                  │
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
├── src/
│   ├── api/
│   │   └── main.py              ← FastAPI backend (all /api/* endpoints)
│   ├── data/
│   │   └── data_preparation.py  ← Data cleaning & weekly aggregation
│   ├── modeling/
│   │   ├── compare_models_rmse.py
│   │   ├── train_forecast_all_models.py
│   │   └── validate_all_models.py
│   ├── visualization/
│   │   └── dashboard.py         ← Dash analytics dashboard
│   └── webapp/
│       ├── src/App.jsx           ← React frontend (all tabs)
│       ├── dist/                 ← Pre-built production assets (committed)
│       └── vite.config.js        ← Dev server + proxy config
│
├── data/
│   ├── raw/                     ← Source XLSX/CSV files
│   └── processed/
│       ├── all_forecast/        ← 8× *_final_forecast.csv
│       ├── all_validation/      ← Validation vs actual CSVs
│       ├── classic_ml_*/        ← ML model outputs
│       └── data_preparation/    ← train_dataset.csv, test_dataset.csv
│
├── models/                      ← Trained .pkl model files
├── reports/figures/             ← Static chart exports
│
├── start.ps1                    ← Local development launcher
├── run_pipeline.ps1             ← Full ML pipeline runner
├── requirements.txt
├── nixpacks.toml                ← Railway build config
└── runtime.txt                  ← Python 3.11.9 pin (Render)
```

---

## ⚙️ API Reference

Base URL (local): `http://localhost:8000/api`  
Base URL (production): `https://web-production-4bd43.up.railway.app/api`

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

## 🚀 Local Development

### Prerequisites
- Python 3.11+, Node.js 18+
- Virtual environment activated with `requirements.txt` installed

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

The Vite dev server proxies `/analytics/` → `:8050` and `/api` → `:8000`, so the app works seamlessly from a single origin.

### Run the Full ML Pipeline
```powershell
.\run_pipeline.ps1
```

Steps:
1. Data preparation & weekly aggregation
2. Classic ML model comparison
3. Time series model comparison
4. Auto-SARIMA training
5. Final forecast generation for all 8 items
6. Validation against hold-out set

---

## ☁️ Production Deployment (Railway)

### Architecture
A single Railway service runs the FastAPI app which:
- Mounts the Dash WSGI app at `/analytics`
- Serves the pre-built React `dist/` as static files at `/`
- Exposes all `/api/*` endpoints

### Deploy
```bash
git push origin main   # Railway auto-deploys on push
```

### Update Frontend (after UI changes)
```powershell
cd src\webapp
npm run build
cd ..\..
git add -f src/webapp/dist
git commit -m "Production build: <description>"
git push origin main
```

### Environment Variables (Railway Dashboard)
| Key | Value |
|---|---|
| `PORT` | Set automatically by Railway |
| `RAILWAY_ENVIRONMENT` | Set automatically — used to switch Dash routing mode |

### URLs
| Resource | URL |
|---|---|
| Main App | https://web-production-4bd43.up.railway.app/ |
| Analytics | https://web-production-4bd43.up.railway.app/analytics/ |
| API Docs | https://web-production-4bd43.up.railway.app/docs |

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.111.0 | REST API framework |
| `uvicorn` | 0.30.1 | ASGI server |
| `gunicorn` | 22.0.0 | Production WSGI runner |
| `pandas` | 2.2.2 | Data processing |
| `numpy` | 1.26.4 | Numerical computation |
| `statsmodels` | 0.14.2 | AR, MA, ARIMA, SARIMA, MSTL |
| `prophet` | 1.1.5 | Facebook Prophet model |
| `plotly` | 5.22.0 | Dash chart rendering |
| `dash` | 2.17.0 | Analytics dashboard |
| `dash-bootstrap-components` | 1.6.0 | Dashboard styling |
| `joblib` | 1.4.2 | Model serialization |
| React + Vite | 18 / 5 | Frontend framework |
| Recharts | Latest | Interactive time series charts |

---

## 🧪 Key Design Decisions

1. **Monolithic Deployment** — Dash + FastAPI + React served from one Railway service to minimize cost and complexity.
2. **Pre-built `dist/` in Git** — Bypasses cloud build limitations; ensures Railway always serves exactly what was tested locally.
3. **Environment-aware Dash routing** — `routes_pathname_prefix` switches between `'/'` (Railway/WSGIMiddleware) and `'/analytics/'` (local standalone) using `RAILWAY_ENVIRONMENT`.
4. **Vite proxy for local dev** — Routes `/analytics/` and `/api` through the Vite dev server so the app runs on a single origin without CORS issues.
5. **Zero-filled weekly series** — Missing weeks are filled with 0 before MSTL decomposition to ensure a complete regular time series for all items (including sparse ones).

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
