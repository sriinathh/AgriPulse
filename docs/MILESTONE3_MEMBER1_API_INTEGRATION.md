# Milestone 3 – Member 1 API Integration Specification
## Project: AgriPulse AI – Precision Smart Irrigation System
### Module: Backend API & Data Pipeline Integration
**Author:** Member 1 – Farmer Dashboard & Irrigation Schedule Engineer  
**Date:** November 2026  

---

## 1. Overview

This document specifies the backend REST API endpoints implemented and integrated by **Member 1** to power the Farmer Dashboard, Field Monitoring, and Today's Irrigation Schedule interfaces.

All endpoints support JSON payloads, CORS compliance, and Bearer token JWT authentication.

---

## 2. Integrated Endpoints

### 2.1 Farmer Dashboard Overview
- **Endpoint**: `GET /farmers/me/dashboard`
- **Authentication**: Required (`Bearer <token>`)
- **Description**: Returns aggregated agronomic indicators for the authenticated farmer.
- **Response Schema (`FarmerDashboardResponse`)**:
```json
{
  "farmer_name": "Srinath",
  "farmer_email": "psrinath821@gmail.com",
  "total_fields": 3,
  "fields_needing_irrigation": 1,
  "average_soil_moisture": 42.5,
  "total_water_used_liters": 14500.0,
  "weather_summary": {
    "temperature": 28.4,
    "humidity": 64.0,
    "rainfall": 0.0,
    "timestamp": "2026-11-08T12:00:00Z"
  }
}
```

---

### 2.2 List Irrigation Schedules
- **Endpoint**: `GET /irrigation/schedules`
- **Query Parameters**:
  - `field_id` (optional, string): Filter by specific field ID.
  - `status` (optional, enum: `pending`, `completed`, `skipped`): Filter by execution state.
  - `limit` (optional, integer, default: 50): Number of records.
- **Response Schema (`List[IrrigationScheduleOut]`)**:
```json
[
  {
    "schedule_id": "SCH_DEMO_01",
    "field_id": "F001",
    "recommended_date": "2026-11-08T00:00:00",
    "recommended_time": "06:30",
    "duration_minutes": 45.0,
    "water_quantity_liters": 1500.0,
    "priority": "high",
    "reason": "Depletion below 45% FAO-56 threshold for Rice",
    "status": "pending",
    "created_at": "2026-11-08T10:00:00Z",
    "updated_at": "2026-11-08T10:00:00Z"
  }
]
```

---

### 2.3 Create Manual Irrigation Schedule
- **Endpoint**: `POST /irrigation/schedules`
- **Status Code**: `201 Created`
- **Request Body (`IrrigationScheduleCreate`)**:
```json
{
  "field_id": "F001",
  "recommended_date": "2026-11-08",
  "recommended_time": "07:00",
  "duration_minutes": 30.0,
  "water_quantity_liters": 1200.0,
  "priority": "normal",
  "reason": "Scheduled root zone replenishment"
}
```
- **Response**: Full `IrrigationScheduleOut` object with auto-generated `schedule_id`.

---

### 2.4 Auto-Generate FAO-56 Irrigation Schedule
- **Endpoint**: `POST /irrigation/schedules/generate/{field_id}`
- **Status Code**: `201 Created`
- **Description**: Invokes the FAO-56 Penman-Monteith recommendation service (`recommend_irrigation()`), calculates required water volume in liters, estimates pump actuation duration, and persists a `pending` schedule.
- **Response**: `IrrigationScheduleOut` object.

---

### 2.5 Update Schedule Actuation Status
- **Endpoint**: `PATCH /irrigation/schedules/{schedule_id}/status`
- **Request Body (`IrrigationScheduleStatusUpdate`)**:
```json
{
  "status": "completed"
}
```
- **Response**: Updated `IrrigationScheduleOut` object with new status and updated timestamp.

---

### 2.6 Farm Alerts & Telemetry Anomalies
- **Endpoint**: `GET /data-quality/events?limit=10`
- **Description**: Fetches real-time sensor anomalies, drought risks, and low soil moisture threshold crossings to populate the dashboard notification ribbon.

---

## 3. Resilience & Error Handling

1. **Authentication Graceful Degradation**:
   - If a user opens the dashboard without a valid JWT or when the session is expired (HTTP 401), the frontend falls back automatically to the public summary (`/dashboard/summary`) without crashing or showing blank pages.
2. **Nullable Telemetry Fields**:
   - Sensor reading schemas support optional `None`/`null` values for historical and simulated data points.
3. **Optimistic UI Updates**:
   - Status actions (`Complete` / `Skip`) update the local React state immediately and synchronize with the backend in the background.

