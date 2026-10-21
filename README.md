# 🏭 SCADA BI & KPI Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-00a393.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-lightgrey.svg)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine%20Learning-orange.svg)

An intelligent, dual-server Business Intelligence (BI) dashboard designed for industrial SCADA systems. This project processes raw PLC sensor data to calculate real-time Overall Equipment Effectiveness (OEE), applies dynamic management scoring formulas, and uses Machine Learning to detect production anomalies.

## ✨ Key Features

*   **Smart OEE Calculation:** Accurately calculates Availability, Performance, and Quality based on raw PLC 5-second interval data (counters, weights, and motor statuses).
*   **Dynamic Weighting System:** Managers can adjust the importance of Quality (KPI) vs. Volume (Achievement) using UI sliders. The system calculates a balanced, weighted shift score without penalizing high-performing shifts.
*   **Machine Learning Anomaly Detection:** Utilizes a `RandomForestClassifier` to identify suspicious or abnormal production patterns based on the day of the week, shift type, and actual production volume.
*   **Intelligent Data Caching:** Heavy raw data processing is done only for new records. Results are cached in a lightweight CSV, allowing the dashboard to apply dynamic user filters (like 7-day or 30-day lookbacks) in milliseconds.
*   **External API Synchronization:** Seamlessly fetches the latest telemetry data from external WebSCADA backends on demand.

## 🏗️ System Architecture

This project employs a robust separation of concerns using a dual-server architecture:

1.  **Frontend / UI Server (Flask - `app.py`):**
    *   Serves the `index.html` dashboard.
    *   Acts as a middleman, receiving user configurations (slider weights, time ranges) and forwarding them to the processing engine.
2.  **Data Processing Engine (FastAPI - `api_server.py` & `kpi_calculator.py`):**
    *   Handles the heavy lifting.
    *   `update_metrics_cache`: Parses raw dataset, detects bag releases, calculates OEE, and updates the local CSV cache.
    *   `calculate_final_scores`: A lightning-fast layer that reads the cache, applies UI weights, calculates penalties based on hardcoded thresholds, and injects ML anomaly predictions.

## 🧠 Machine Learning Module (`train_ml.py`)

The anomaly detection engine uses a Supervised Learning approach, cleverly trained on initially unlabeled data:
*   **Statistical Labeling:** Historical data is grouped by Day and Shift. Anomalies are tagged using the statistical threshold of `Mean - (1.5 * Standard Deviation)`.
*   **Random Forest Classifier:** An ensemble of 100 decision trees (`n_estimators=100`) evaluates the encoded features (`DayOfWeek`, `Shift_Encoded`, `Actual_Production`).
*   **Reproducibility:** Configured with `random_state=42` and `stratify=y` during the train/test split to ensure consistent, reliable accuracy metrics across deployments.

## 📂 Project Structure

```text
├── data/
│   ├── Cleaned_Dataset.csv      # Raw PLC data (simulated or synced)
│   └── metrics_cache.csv        # Auto-generated lightweight cache
├── models/
│   ├── anomaly_model.pkl        # Trained Random Forest model weights
│   └── shift_encoder.pkl        # Label encoder for shift types
├── app.py                       # Flask UI server
├── api_server.py                # FastAPI data processing server
├── kpi_calculator.py            # Core logic (Caching, OEE, Scoring)
├── train_ml.py                  # ML training and evaluation script
└── templates/
    └── index.html               # Main dashboard interface
```

## 🚀 API Endpoints

The FastAPI server exposes the following main endpoint for the dashboard:

*   **`POST /api/calculate-kpi`**
    *   **Payload:** `{ "target_production": int, "kpi_weight": int, "vol_weight": int, "time_range": string }`
    *   **Response:** JSON object containing an array of calculated shift results, including OEE, final scores, and the `Is_Anomaly` flag.

## 🛠️ Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/scada-bi-dashboard.git
   ```
2. Install the required dependencies:
   ```bash
   pip install pandas numpy scikit-learn fastapi uvicorn flask requests joblib
   ```
3. Train the Machine Learning model (generates `.pkl` files):
   ```bash
   python train_ml.py
   ```
4. Start the FastAPI backend server:
   ```bash
   uvicorn api_server:app --port 8000
   ```
5. Start the Flask UI server (in a separate terminal):
   ```bash
   python app.py
   ```
6. Open your browser and navigate to `http://localhost:5000`