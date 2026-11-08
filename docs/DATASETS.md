# Datasets for the Smart Irrigation project

## 1. Why `irrigation_prediction.csv` (Kaggle-style, 10k rows) is not enough
Synthetic i.i.d. rows (uniform columns, ~0 correlation), only a Low/Medium/High label (no volume/timing), no timestamps/field IDs
(so no LSTM, no pipeline test), and `Rainfall_mm` is annual-scale vs the hourly mm our weather service stores.
Good only for a first Random Forest classifier prototype. Never quote its ~97 % accuracy as real-world performance.

## 2. Our generated dataset: ONE file
`python scripts/generate_dataset.py` -> `data/synthetic/irrigation_dataset.csv` (seeded; 24 fields x 120 days = 2,808 rows).
**Synthetic, not measured.** A simulator (weather generator -> Hargreaves ET0 x FAO-56-style Kc -> soil-water balance -> a simulated farmer
with a noisy threshold rule). Monthly climate values are approximate regional averages (Hyderabad, Bengaluru, Pune, Ludhiana).

One row = one field-day, decision time 06:00. Where each column comes from **at runtime**:

| Column(s) | Runtime source |
|---|---|
| `soil_moisture_0600`, `soil_moisture_change_24h` | our sensor readings table (simulated/real sensor) |
| `crop_type`, `growth_stage`, `days_after_sowing`, `soil_type`, `irrigation_type` | field configuration |
| `temperature_0600`, `humidity_0600` | **live OpenWeatherMap** (`GET /weather/{field_id}`) |
| `rain_prev24h_mm` | live weather observations we have stored over the last 24 h (needs periodic fetching: Week 3 task) |
| `rain_forecast_next24h_mm` | OpenWeatherMap **forecast** endpoint (not implemented in Week 1: Week 3 task) |
| `irrigation_prev7d_mm`, `days_since_irrigation` | irrigation log (table to be added in Week 3) |
| **targets** `irrigate_today` (0/1), `irrigation_mm` | what the model must predict |

**Weather in this file exists only so a model can learn from it.** Real deployments never read weather from a dataset: the live API supplies it.
Generated weather is never loaded into the `weather_data` table.

`--raw` additionally writes hourly `sensor_readings.csv` (with ~1.6 % nulls, ~0.3 % impossible values, outages), `fields.csv` and
`irrigation_events.csv`, for demonstrating Week 1 ingestion: `python scripts/load_dataset.py` runs each reading through the cleaning layer
(faults are rejected and counted) and registers the fields/sensors. It does not touch weather.

Baseline Random Forest with **field-grouped** CV: AUC 0.94, F1 0.58 (base rate 9 %); volume MAE 6.1 mm vs 15.8 mm for predicting the mean.
These numbers measure recovery of the simulator's behaviour, not real farms.
Simplifications: one soil layer, no salinity/pests; the farmer rule is a threshold so models can partly learn the rule; cotton rarely irrigates.

## 3. Real data you can download (verify licence/terms before use in your report)
Found via search on 11 Oct 2026; I have **not** downloaded or validated these files.

| Source | What it has | Fit |
|---|---|---|
| Mendeley Data — *Soil Moisture, Irrigation Actuator and Weather Dataset from a Multi-Sector Precision-Irrigation* (DOI 10.17632/c837v6p8ph.2) | One season, 5 sectors, soil moisture/pH/EC + **applied water volumes** + ERA5 weather, 10-min grid, 789 irrigation events, 24 h-ahead targets | **Best match** for ML (sensor + weather + actual irrigation). Italy, tomato/zucchini/blueberry: good for model development, not for Indian crop calibration |
| Mendeley Data — *Environmental Sensor Dataset for LSTM-Based Predictive Irrigation… ESP32* (DOI 10.17632/jtsyb593fy.1) | 960 readings, 30-min, soil moisture, temp, humidity, light, **pump status** | Small; good for an LSTM demo |
| Mendeley Data — Adetunji, hourly 2017–18 (DOI 10.17632/m6j79zjyd7.1) | Soil moisture, soil/air temp, humidity, dew point, rainfall (CHIRPS) | Hourly sensor + rainfall |
| IEEE DataPort — North Gujarat soil sensing (2,073 observations) and Anand District IoT soil-moisture dataset (Jun 2024–Jul 2025) | **Indian** soil moisture/pH/EC; the Anand set is a time series | Best Indian soil-moisture sources; no irrigation volumes |
| Topraq open-access precision-irrigation data (topraq.ai) | Soil moisture + on-site weather | Check format/licence on their page |
| IEEE DataPort — AgriField-Manipur | Daily temp/humidity/soil moisture/rain; **field-level values are synthetic** (documented) | Indian context, but synthetic like ours |

Weather history (free): **Open-Meteo archive API** (no key, free for non-commercial use, attribution required; ERA5-based) and **NASA POWER** (daily/hourly from 1981, free).
Use either to build the *historical* weather columns of a training set from real weather (live API calls alone cannot give history for training).

IEEE DataPort may require a free account. Cite each dataset's DOI/licence in the project report.
