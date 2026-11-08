# AgriPulse AI – AI-Powered Smart Irrigation System for Predictive Water Management and Crop Optimization

[![React 19](https://img.shields.io/badge/React-19.0-61dafb?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.13-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169e1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-Hypertables-fdb515?style=for-the-badge&logo=timescale&logoColor=black)](https://www.timescale.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.0-38bdf8?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **Precision Agriculture & Closed-Loop Irrigation Intelligence**  
> An end-to-end intelligent agricultural framework combining real-time IoT soil moisture telemetry, hyper-local OpenWeather integration, FAO-56 Penman–Monteith agronomic evapotranspiration equations, Random Forest regression models, and an intuitive, farmer-friendly operations dashboard.

---

## 📖 Abstract of the Invention

In this invention, an AI-powered smart irrigation and predictive water management system for precision agriculture is provided to model, monitor, and optimize crop water requirements using integrated Internet of Things (IoT) telemetry and agronomic machine learning algorithms. The system utilizes in-situ multi-depth soil moisture sensors, ambient microclimate stations, and LoRaWAN IoT telemetry nodes to capture spatial-temporal soil matric potential, ambient temperature, relative humidity, and rainfall variations across defined agricultural zones. Real-time and historical telemetry streams ingested into a dedicated time-series database are subjected to automated preprocessing operations, including outlier rejection, missing-value imputation, feature normalization, and evapotranspiration rate computation via the FAO-56 Penman–Monteith model. A predictive machine learning engine couples crop-specific growth-stage water depletion models with Random Forest and ensemble regressors to forecast root-zone moisture depletion and determine precise irrigation volumes and pump actuation durations. The framework further incorporates an automated decision-support and scheduling interface configured to generate dynamic irrigation schedules, enforce colour-coded field health classifications (optimal, warning, and critical), and trigger proactive drought-risk, sensor anomaly, and extreme weather notifications. Deployment across a cloud or hybrid edge computing architecture ensures authenticated multi-tenant access, secure sensor data ingestion, and closed-loop actuator management. The invention thereby minimizes agricultural water consumption, prevents over- and under-irrigation, and maximizes crop yield and environmental sustainability across diverse agro-climatic environments.

---

## 👥 Lead Developer & Inventor Profile

| Attribute | Details |
| :--- | :--- |
| **Lead Developer** | **Srinath** |
| **Email** | [psrinath821@gmail.com](mailto:psrinath821@gmail.com) |
| **Role** | **Member 1 – Farmer Dashboard & Irrigation Schedule Engineer** |
| **System Profile** | [View Profile & Telemetry Dashboard](http://localhost:5173/profile) |

---

## 🏛️ System Architecture

```
                       [ Agricultural Field Nodes ]
      (Multi-depth capacitive probes, temperature, humidity, rain gauge)
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │      Ingestion Gateway (REST JSON / LoRaWAN)     │
          │         Bearer Token Ingestion Protection        │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │        Data Quality & Preprocessing Engine       │
          │  - Outlier detection & physical range clipping   │
          │  - Temporal consistency & monotonic check        │
          │  - Auditable anomaly logging (DataQualityEvents) │
          └────────────────────────┬─────────────────────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
          ┌──────────────────────┐    ┌──────────────────────┐
          │  PostgreSQL 16 Core  │    │ TimescaleDB Hypertab │
          │  - Farmers & Fields  │    │  - sensor_readings   │
          │  - Crops & Sensors   │    │  - weather_data      │
          │  - Schedules & Users │    │  - 7-day chunking    │
          └──────────┬───────────┘    └──────────┬───────────┘
                     │                           │
                     └─────────────┬─────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │      FastAPI High-Performance Backend (8000)     │
          │  - FAO-56 Penman-Monteith Evapotranspiration ET0 │
          │  - Crop root-zone depletion & pump duration calc │
          │  - Argon2 password hashing & Bearer JWT auth     │
          └────────────────────────┬─────────────────────────┘
                                   │
                                   ▼
          ┌──────────────────────────────────────────────────┐
          │      React 19 + TypeScript + Vite UI (5173)      │
          │  - Farmer Dashboard with real-time agronomic KPIs│
          │  - Field Monitoring (🟢 Green / 🟡 Yellow / 🔴 Red) │
          │  - Today's Irrigation Schedule & Actuation Logs  │
          │  - Profile Management, IoT Token & Telemetry Pref│
          └──────────────────────────────────────────────────┘
```

---

## ✨ Key Features (Member 1 Implementation)

### 1. Farmer Operations Dashboard (`/dashboard`)
- **Personalized Operator Welcome**: Greets the authenticated farmer dynamically (`Welcome back, Srinath`) with system status and date badge.
- **Top 4 Agronomic KPIs**:
  - **Total Fields**: Land parcels actively under management.
  - **Needs Irrigation**: Real-time counter of fields operating below safe moisture thresholds.
  - **Average Soil Moisture**: Aggregate moisture benchmarked against the 35%–55% optimal zone.
  - **Water Dispensed**: Total liters delivered with conservation savings (~28% saved vs traditional flood irrigation).
- **Today's Irrigation Schedule Widget**: Embedded interactive widget with instant 1-click **Complete** and **Skip** actuation controls.
- **Real-Time Weather Widget**: Ambient temperature (°C), relative humidity (%), rainfall (mm), and reference evapotranspiration ($ET_0$).
- **Proactive Alerts Banner**: Real-time surfacing of drought risks, soil moisture depletion, and sensor anomaly events.

### 2. Field Health Monitoring Interface (`/fields`)
- **Dual-Mode Visual Switcher**: Toggle effortlessly between **Monitoring Cards View** and the comprehensive **Parcels Table**.
- **Colour-Coded Field Health Indicators**:
  - 🟢 **Green (Optimal Zone)**: Soil moisture within crop-specific optimal thresholds (e.g., Rice 45%–65%, Maize 25%–42%).
  - 🟡 **Yellow (Needs Attention)**: Moisture approaching depletion threshold or excessive moisture requiring drainage inspection.
  - 🔴 **Red (Urgent Action Required)**: Critically dry root zone requiring immediate irrigation.
- **Telemetry Progress Gauges**: Visual bar depicting live soil moisture % against minimum/maximum crop requirements.
- **Instant FAO-56 Action Triggers**: 1-click trigger to compute crop water requirements and dispatch actuation schedules.

### 3. Irrigation Schedule & Actuation Management (`/schedules`)
- **Schedule KPIs**: Scheduled Today, Pending Pump Runs, Completed Cycles, and Total Water to Dispense (L).
- **Execution State Engine**: Support for `pending`, `completed`, and `skipped` schedule states with instant UI updates.
- **AI Auto-Scheduler**: Runs the FAO-56 crop model for any selected parcel to determine precise water volumes and pump minutes.
- **Manual Schedule Creation**: Modal form for farmer-initiated irrigation events.

### 4. Interactive Profile & Farm Scope Management (`/profile`)
- **Profile Edit Mode**: Interactive toggle to edit full name, email, phone number, farm name, location, and crop portfolio.
- **IoT Device Ingestion Token**: Displays your gateway ingestion Bearer token with 1-click **Copy** and **Roll Secret** actions.
- **Telemetry Alert Toggles**: Configurable switches for Low Soil Moisture Alarms, Weather Alerts, and Daily Briefings.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite | Ultra-fast reactive client with zero runtime overhead |
| **Styling** | Tailwind CSS 4, Lucide Icons | Dark emerald glassmorphic agricultural design language |
| **Backend API** | FastAPI, Uvicorn, Python 3.10+ | Asynchronous RESTful service with auto-generated OpenAPI docs |
| **Authentication**| Argon2-cffi, JWT (Bearer) | Modern cryptographically secure credential hashing & tokens |
| **Primary Database**| PostgreSQL 16 / TimescaleDB | Hypertable chunking on time-series telemetry data |
| **Dev Database**| SQLite (`irrigation.db`) | Zero-configuration local database fallback |
| **Machine Learning**| scikit-learn, FAO-56 Model | Crop water balance, evapotranspiration, and yield optimization |
| **Weather** | OpenWeather API | Automated reverse geocoding & live weather telemetry synchronization |

---

## 📁 Repository Directory Structure

```
smart-irrigation/
├── backend/
│   ├── app/
│   │   ├── config.py                 # Configuration via pydantic-settings
│   │   ├── errors.py                 # JSON error envelopes & unhandled exception handling
│   │   ├── main.py                   # FastAPI application factory & router registration
│   │   ├── database/
│   │   │   ├── base.py               # SQLAlchemy DeclarativeBase
│   │   │   ├── session.py            # Engine connection pooling (PostgreSQL & SQLite)
│   │   │   ├── init_db.py            # Database initialization routine
│   │   │   └── timescale.py          # TimescaleDB hypertable setup
│   │   ├── models/
│   │   │   ├── farmer.py             # Farmer model
│   │   │   ├── field.py              # Field model with irrigation relationship
│   │   │   ├── crop.py               # Crop model & growth stages
│   │   │   ├── sensor.py             # Sensor registry model
│   │   │   ├── sensor_reading.py     # Time-series telemetry readings
│   │   │   ├── weather_data.py       # Time-series weather readings
│   │   │   ├── irrigation_schedule.py# IrrigationSchedule model
│   │   │   ├── user.py               # User authentication model
│   │   │   └── data_quality_event.py # Audit log model
│   │   ├── routers/
│   │   │   ├── auth.py               # Register, login, me, and profile update endpoints
│   │   │   ├── farmer_dashboard.py   # Aggregated farmer dashboard metrics
│   │   │   ├── irrigation_schedules.py # Schedule CRUD, status patch, and FAO-56 generation
│   │   │   ├── fields.py             # Parcel management & weather sync
│   │   │   ├── sensors.py            # Sensor registration & telemetry ingestion
│   │   │   ├── weather.py            # Live weather fetch & reverse geocoding
│   │   │   └── recommendations.py    # AI crop & water recommendation endpoints
│   │   ├── schemas/                  # Pydantic request / response validation schemas
│   │   └── services/                 # FAO-56 logic, data cleaning, demo seed routines
│   ├── requirements.txt              # Backend dependencies
│   └── .env.example                  # Environment variable configuration template
├── frontend/
│   ├── src/
│   │   ├── components/layout/        # Navbar, Sidebar (with profile card & schedule nav)
│   │   ├── context/
│   │   │   └── AuthContext.tsx       # Auth provider, JWT storage, profile updater
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx     # Enhanced Farmer Operations Dashboard
│   │   │   ├── FieldsPage.tsx        # Colour-coded Field Monitoring (Green/Yellow/Red)
│   │   │   ├── IrrigationSchedulePage.tsx # Dedicated Irrigation Schedule Management
│   │   │   ├── ProfilePage.tsx       # Farmer Profile, IoT Gateway Token, Preferences
│   │   │   ├── RecommendationsPage.tsx # AI Crop Advisory & Soil Health
│   │   │   ├── WeatherPage.tsx       # Weather Data & Forecast Analytics
│   │   │   └── AuthPage.tsx          # Clean glassmorphic Login & Sign-up
│   │   ├── services/
│   │   │   └── api.ts                # Axios client with JWT interceptor & API methods
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript contracts matching backend models
│   │   ├── App.tsx                   # Route registrations
│   │   └── index.css                 # Global Tailwind CSS styling
│   ├── package.json                  # Frontend dependencies
│   └── vite.config.ts                # Vite bundler configuration
├── docs/
│   ├── MILESTONE3_MEMBER1_IMPLEMENTATION.md # Comprehensive Member 1 implementation report
│   ├── MILESTONE3_MEMBER1_API_INTEGRATION.md # Full API integration specification
│   └── MILESTONE3_MEMBER1_TEST_REPORT.md    # Test execution & verification results
├── docker-compose.yml                # PostgreSQL / TimescaleDB container setup
└── README.md                         # Complete project documentation
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python:** 3.10, 3.11, or 3.13
- **Node.js:** v18.0.0 or higher
- **Package Manager:** npm or pnpm
- **Docker & Docker Compose** (optional, for PostgreSQL / TimescaleDB)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/psrinath821/smart-irrigation.git
cd smart-irrigation
```

---

### Step 2: Backend Setup & Execution

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the environment:
   ```bash
   cp .env.example .env
   ```
   *(SQLite fallback is pre-configured by default in `.env` for zero-setup execution. To use PostgreSQL / TimescaleDB, set `DATABASE_URL=postgresql://postgres:postgres@localhost:5434/irrigation` and run `docker compose up -d`)*.

5. Start the FastAPI backend server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   The backend will be live at `http://127.0.0.1:8000`.  
   Interactive Swagger documentation is available at `http://127.0.0.1:8000/docs`.

---

### Step 3: Frontend Setup & Execution

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

## 📡 Key REST API Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/auth/register` | Register a new farmer account | No |
| `POST` | `/auth/login` | Authenticate and obtain JWT access token | No |
| `GET` | `/auth/me` | Fetch authenticated user profile & phone | Yes (Bearer) |
| `PUT` | `/auth/me` | Update full name, email, or phone number | Yes (Bearer) |
| `GET` | `/farmers/me/dashboard` | Aggregated dashboard KPIs for current farmer | Yes (Bearer) |
| `GET` | `/irrigation/schedules` | List schedules (filters: `field_id`, `status`) | No |
| `POST` | `/irrigation/schedules` | Create a manual irrigation schedule | No |
| `POST` | `/irrigation/schedules/generate/{field_id}` | Compute FAO-56 recommendation and schedule pump run | No |
| `PATCH` | `/irrigation/schedules/{id}/status` | Update schedule status (`pending`, `completed`, `skipped`) | No |
| `GET` | `/fields` | List agricultural fields and crop assignments | No |
| `GET` | `/sensor/readings` | Fetch historical sensor readings | No |
| `GET` | `/weather/{field_id}/live` | Synchronize live weather for field coordinates | No |
| `GET` | `/data-quality/events` | Audit log of sensor anomalies and warnings | No |

---

## 🧪 Testing & Verification

### Running Frontend Tests & Production Build
```bash
cd frontend
npm run build
```
*Output: `✓ built in 5.88s` with zero TypeScript errors.*

### Running Backend Unit & Integration Tests
```bash
cd backend
pytest tests/
```

---

## 📄 License
This project is open-source and distributed under the [MIT License](LICENSE).

---

## 💡 Acknowledgements & References
- **FAO-56 Irrigation and Drainage Paper**: Crop evapotranspiration guidelines for computing crop water requirements.
- **TimescaleDB**: High-performance time-series data storage and analytical queries.
- **OpenWeather API**: Microclimate and precipitation forecast data.
