# AgriPulse AI — Crop Recommendation Dataset Documentation Report

## 1. Dataset Identification & Purpose
- **Filename:** `Crop_recommendationV2 (1).csv`
- **Storage Location:** `data/raw/Crop_recommendationV2 (1).csv` (original untouched)
- **Primary Objective:** Provides agronomic baseline soil, climate, and cultivation parameters across 22 major crop species for future multi-class agricultural recommendation models.
- **Milestone 1 Scope Boundary:** This dataset is **strictly static** and is preserved in `data/raw/`. It is **NOT** injected into live IoT sensor time-series tables (`sensor_readings`) and no machine learning models are trained during Milestone 1.

## 2. Dataset Dimensions & Basic Metrics
- **Total Observations (Rows):** 2,200
- **Total Features (Columns):** 23 (22 predictors + 1 target class)
- **Missing Values:** 0 (0% missing across all attributes)
- **Duplicate Records:** 0 (0 duplicate rows)

## 3. Data Dictionary
| Column Name | Data Type | Physical / Agronomic Meaning | Unit / Scale | Range [Min, Max] |
|---|---|---|---|---|
| `N` | `int64` | N | Ratio in soil (kg/ha) | [0.00, 140.00] |
| `P` | `int64` | P | Ratio in soil (kg/ha) | [5.00, 145.00] |
| `K` | `int64` | K | Ratio in soil (kg/ha) | [5.00, 205.00] |
| `temperature` | `float64` | Temperature | Ambient temperature (°C) | [8.83, 43.68] |
| `humidity` | `float64` | Humidity | Relative air humidity (%) | [14.26, 99.98] |
| `ph` | `float64` | Ph | Soil acidity / alkalinity (0-14 pH scale) | [3.50, 9.94] |
| `rainfall` | `float64` | Rainfall | Annual / seasonal precipitation (mm) | [20.21, 298.56] |
| `label` | `str` | Label | Target crop classification name | 22 distinct classes (balanced) |
| `soil_moisture` | `float64` | Soil Moisture | Volumetric soil moisture content (%) | [10.02, 30.00] |
| `soil_type` | `int64` | Soil Type | Soil classification category code (1-3) | [1.00, 3.00] |
| `sunlight_exposure` | `float64` | Sunlight Exposure | Daily sunshine duration (hours/day) | [5.00, 11.99] |
| `wind_speed` | `float64` | Wind Speed | Average ambient wind velocity (km/h) | [0.00, 19.99] |
| `co2_concentration` | `float64` | Co2 Concentration | Atmospheric CO2 concentration (ppm) | [350.00, 449.98] |
| `organic_matter` | `float64` | Organic Matter | Soil organic matter percentage (%) | [1.00, 10.00] |
| `irrigation_frequency` | `int64` | Irrigation Frequency | Scheduled irrigation events per cycle (1-6) | [1.00, 6.00] |
| `crop_density` | `float64` | Crop Density | Plant population density (plants/m²) | [5.00, 19.99] |
| `pest_pressure` | `float64` | Pest Pressure | Standardized pest incidence index (0-100) | [0.04, 99.98] |
| `fertilizer_usage` | `float64` | Fertilizer Usage | Applied synthetic / organic fertilizer (kg/ha) | [50.21, 199.98] |
| `growth_stage` | `int64` | Growth Stage | Phenological growth stage (1=seedling, 2=vegetative, 3=maturity) | [1.00, 3.00] |
| `urban_area_proximity` | `float64` | Urban Area Proximity | Distance to major urban / market centers (km) | [0.02, 49.99] |
| `water_source_type` | `int64` | Water Source Type | Water sourcing code (1=canal/surface, 2=borewell/ground, 3=rainfed) | [1.00, 3.00] |
| `frost_risk` | `float64` | Frost Risk | Computed frost risk vulnerability index (0-100) | [0.05, 99.96] |
| `water_usage_efficiency` | `float64` | Water Usage Efficiency | Crop water productivity metric (kg/m³) | [1.00, 5.00] |

## 4. Class Distribution (`label`)
The target variable is perfectly balanced with exactly 100 observations per crop:

| Crop Label | Observation Count | Percentage of Dataset |
|---|---|---|
| `rice` | 100 | 4.5% |
| `maize` | 100 | 4.5% |
| `chickpea` | 100 | 4.5% |
| `kidneybeans` | 100 | 4.5% |
| `pigeonpeas` | 100 | 4.5% |
| `mothbeans` | 100 | 4.5% |
| `mungbean` | 100 | 4.5% |
| `blackgram` | 100 | 4.5% |
| `lentil` | 100 | 4.5% |
| `pomegranate` | 100 | 4.5% |
| `banana` | 100 | 4.5% |
| `mango` | 100 | 4.5% |
| `grapes` | 100 | 4.5% |
| `watermelon` | 100 | 4.5% |
| `muskmelon` | 100 | 4.5% |
| `apple` | 100 | 4.5% |
| `orange` | 100 | 4.5% |
| `papaya` | 100 | 4.5% |
| `coconut` | 100 | 4.5% |
| `cotton` | 100 | 4.5% |
| `jute` | 100 | 4.5% |
| `coffee` | 100 | 4.5% |

## 5. Statistical Summary of Numerical Features

| Feature | Min | 25% | Median | 75% | Max | Mean | Std Dev |
|---|---|---|---|---|---|---|---|
| `N` | 0.00 | 21.00 | 37.00 | 84.25 | 140.00 | 50.55 | 36.92 |
| `P` | 5.00 | 28.00 | 51.00 | 68.00 | 145.00 | 53.36 | 32.99 |
| `K` | 5.00 | 20.00 | 32.00 | 49.00 | 205.00 | 48.15 | 50.65 |
| `temperature` | 8.83 | 22.77 | 25.60 | 28.56 | 43.68 | 25.62 | 5.06 |
| `humidity` | 14.26 | 60.26 | 80.47 | 89.95 | 99.98 | 71.48 | 22.26 |
| `ph` | 3.50 | 5.97 | 6.43 | 6.92 | 9.94 | 6.47 | 0.77 |
| `rainfall` | 20.21 | 64.55 | 94.87 | 124.27 | 298.56 | 103.46 | 54.96 |
| `soil_moisture` | 10.02 | 15.18 | 20.09 | 25.26 | 30.00 | 20.15 | 5.79 |
| `soil_type` | 1.00 | 1.00 | 2.00 | 3.00 | 3.00 | 1.99 | 0.81 |
| `sunlight_exposure` | 5.00 | 6.90 | 8.61 | 10.22 | 11.99 | 8.57 | 2.00 |
| `wind_speed` | 0.00 | 5.28 | 10.26 | 15.06 | 19.99 | 10.17 | 5.74 |
| `co2_concentration` | 350.00 | 375.25 | 399.69 | 424.12 | 449.98 | 399.65 | 28.45 |
| `organic_matter` | 1.00 | 3.20 | 5.42 | 7.69 | 10.00 | 5.47 | 2.61 |
| `irrigation_frequency` | 1.00 | 2.00 | 4.00 | 5.00 | 6.00 | 3.52 | 1.70 |
| `crop_density` | 5.00 | 8.59 | 12.30 | 15.98 | 19.99 | 12.34 | 4.30 |
| `pest_pressure` | 0.04 | 24.38 | 49.98 | 74.68 | 99.98 | 49.85 | 28.89 |
| `fertilizer_usage` | 50.21 | 88.03 | 126.44 | 163.85 | 199.98 | 125.85 | 43.56 |
| `growth_stage` | 1.00 | 1.00 | 2.00 | 3.00 | 3.00 | 2.00 | 0.82 |
| `urban_area_proximity` | 0.02 | 12.21 | 24.92 | 37.32 | 49.99 | 24.80 | 14.52 |
| `water_source_type` | 1.00 | 1.00 | 2.00 | 3.00 | 3.00 | 2.00 | 0.81 |
| `frost_risk` | 0.05 | 26.10 | 50.17 | 75.26 | 99.96 | 50.30 | 28.58 |
| `water_usage_efficiency` | 1.00 | 2.05 | 2.97 | 3.97 | 5.00 | 2.99 | 1.14 |

## 6. Agronomic Validation & Outlier Assessment
- **Phosphorus (P) and Potassium (K):** Naive statistical IQR flags values > 128 for P and > 92.5 for K as outliers. However, grouping by crop demonstrates that Apple (mean P=134.2, mean K=199.9) and Grapes (mean P=132.5, mean K=200.1) have biological requirements that are significantly higher than cereals. These are valid agronomic signatures, not corrupted data.
- **Rainfall:** Heavy precipitation (>200 mm) corresponds to rice and tropical crops, reflecting monsoon-dependent paddy cultivation.
- **Nitrogen (N):** Exactly 27 entries have N=0, which corresponds to biological nitrogen-fixing legumes (e.g. chickpea, kidneybeans, mothbeans) where synthetic nitrogen input is minimized.

## 7. Future Milestone Roadmap (Milestones 2 & 3)
1. **Model Exploration:** Benchmark multi-class classification algorithms: Random Forest Classifier, XGBoost, and LightGBM.
2. **Feature Preprocessing:** Scale continuous variables using `RobustScaler` to retain distinct high-nutrient crop signatures.
3. **Encoding:** Map categorical integer features (`soil_type`, `water_source_type`, `growth_stage`) to verified ontological categories.
4. **Inference API:** Expose an isolated endpoint `POST /recommend/crop` in Milestone 2 that accepts field soil test results and predicts the top 3 recommended crops with confidence scores.
5. **Isolation Principle:** Keep the recommendation engine strictly decoupled from real-time IoT telemetry pipelines to prevent cross-contamination.