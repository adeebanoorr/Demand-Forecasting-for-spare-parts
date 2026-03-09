# KPCL Spare Parts Demand Forecasting

AI-driven forecasting enterprise dashboard for Kirloskar Pneumatic Company Limited (KPCL), specifically designed to predict demand for high-priority spare parts in the ACR SPARES model.

## 🌟 Overview

This project provides a full-stack solution for predicting spare part consumption. It leverages multiple machine learning and time-series models to identify the most accurate "Champion Model" for each specific item code, helping optimize inventory and supply chain decisions.

### Key Features
- **Multi-Model Engine**: Automatically compares Statistical (AR, MA, SARIMA), Time-Series (Prophet), and Machine Learning (XGBoost, Random Forest) models.
- **Enterprise Dashboard**: A modern React/Vite frontend featuring interactive charts (Recharts), trend analysis, and performance metrics.
- **Automated Pipeline**: End-to-end scripts for data cleaning, feature engineering, model training, and validation.
- **Production Ready**: Fully configured for deployment on **Railway** using Nixpacks (no Docker required).

---

## 🏗️ Project Architecture

```
├── data/
│   ├── raw/            <- Original Excel records (not tracked in Git).
│   └── processed/      <- Cleaned CSVs, aggregated series, and results.
├── models/             <- Serialized (.pkl) trained model files.
├── reports/            <- Generated figures, MSTL analysis, and CSV reports.
├── src/
│   ├── api/            <- FastAPI backend serving the prediction engine.
│   ├── webapp/         <- React + Vite frontend dashboard.
│   ├── data/           <- Data preparation and cleaning scripts.
│   ├── modeling/       <- Model training and comparison logic.
│   └── visualization/  <- Time-series decomposition (MSTL) analysis.
├── app.py              <- Entry point for the production server.
├── nixpacks.toml       <- Railway deployment configuration.
└── Procfile            <- Process file for production (Gunicorn/Uvicorn).
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+

### Local Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/adeebanoorr/Demand-Forecasting-for-KPCL-spare-parts.git
    cd Demand-Forecasting-for-KPCL-spare-parts
    ```

2.  **Setup Backend**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Frontend**:
    ```bash
    cd src/webapp
    npm install
    npm run build
    cd ../..
    ```

4.  **Run the Application**:
    ```bash
    python app.py
    ```
    Access the dashboard at `http://localhost:8000`.

---

## 📉 Execution Flow (Pipeline)

Follow this sequence to execute the full ML pipeline:

1.  **Data Preparation**:
    ```bash
    python src/data/data_preparation.py
    ```
2.  **Comparative Analysis**:
    ```bash
    python src/modeling/compare_models_rmse.py
    ```
3.  **Training & Forecasting**:
    ```bash
    python src/modeling/train_forecast_all_models.py
    ```
4.  **Validation**:
    ```bash
    python src/forecast_validation/validate_all_models.py
    ```

---

## ☁️ Deployment (Railway)

The project is configured to deploy directly from GitHub to Railway using **Nixpacks**.

1.  **Connect Repo**: Create a new project on Railway and select this repository.
2.  **Build Phase**: Railway will automatically build the React frontend and install Python dependencies.
3.  **Variables**: Add any required environment variables in the Railway dashboard "Variables" tab.
4.  **Enjoy**: Your dashboard will be live on a `railway.app` URL.

---

## 📊 Dataset Highlights

- **Source**: KPCL Despatch Records (up to Sept 2024).
- **Scope**: ACR SPARES model, filtered to 8 highest-demand items.
- **Volume**: ~6k records aggregated into 156-week time series.
- **Features**: Lag features (1-12w), Rolling statistics, and Temporal features (Seasonality).

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
