# Windows Development Setup for AgriPulse AI

This guide walks you through getting the **AgriPulse AI** project up and running on a Windows machine.

## 1️⃣ Prerequisites

| Tool | Minimum version | How to install |
|------|-----------------|----------------|
| **Python** | 3.11 | Download from https://www.python.org/downloads/windows/ and add it to `PATH` during installation. |
| **PowerShell** | 5.1 (built‑in) | No action needed. |
| **Node.js** | 20.x (includes npm) | Download from https://nodejs.org/en/download/. |
| **Docker Desktop** (optional, for PostgreSQL/TimescaleDB) | 4.x | https://www.docker.com/products/docker-desktop/ |

> **Important:** Do **not** install packages globally. All dependencies are installed inside the project‑specific virtual environment.

## 2️⃣ Clone the repository (already done)
```powershell
cd C:\Users\Arpitha Medharametla\Documents
# The repository is already present at smart-irrigation
``` 

## 3️⃣ Create / activate the Python virtual environment
```powershell
# Create if it does not exist (the repo already contains .venv)
# Ensure execution policy allows the activation script
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate the venv
& "C:\Users\Arpitha Medharametla\Documents\smart-irrigation\.venv\Scripts\Activate.ps1"
```
You should see the prompt prefixed with `(.venv)`.  All subsequent `python`/`pip` commands will use this environment.

## 4️⃣ Install Python dependencies
```powershell
pip install -r backend/requirements.txt
```
If you see any version conflicts, keep the versions specified in the `requirements.txt`.  Do **not** upgrade them unless a test fails because of a missing package.

## 5️⃣ Configure environment variables
1. Copy the example file:
```powershell
copy backend/.env.example backend/.env
```
2. Open `backend/.env` in an editor and fill in placeholders.  Example entries:
```
# Application
APP_ENV=development
APP_VERSION=0.1.0

# Database – SQLite fallback (works out‑of‑the‑box)
DATABASE_URL=sqlite:///./test.db

# PostgreSQL (optional – uncomment if Docker is running)
# DATABASE_URL=postgresql://postgres:postgres@localhost:5433/irrigation

# Weather (mock mode by default)
WEATHER_MOCK=true
# If you have a real API key, set the following and flip WEATHER_MOCK to false
# OPENWEATHER_API_KEY=YOUR_KEY_HERE
```
> **Never** commit real secrets.  The `.env` file is ignored by `.gitignore`.

## 6️⃣ Install frontend dependencies
```powershell
cd frontend
npm install
```
The `package.json` already defines the scripts:
- `npm run dev` – start Vite dev server.
- `npm run build` – production build.
- `npm run lint` – run `oxlint`.

## 7️⃣ Run the backend API
```powershell
# From the repository root
uvicorn backend.app.main:app --reload
```
The server starts on `http://127.0.0.1:8000`.  Swagger UI is available at `http://127.0.0.1:8000/docs`.

## 8️⃣ Run the frontend (development)
```powershell
cd frontend
npm run dev
```
The Vite dev server defaults to `http://127.0.0.1:5173`.  It proxies API calls to the backend (`VITE_API_BASE_URL` is set in `frontend/.env` – create it if missing).  Example:
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 9️⃣ Run the test suite
```powershell
# Backend tests – run inside the venv
python -m pytest backend -q
```
All backend tests should pass (`132 passed, 4 warnings`).  Frontend tests are not defined in this repository.

## 🔟 Optional: Start PostgreSQL via Docker
```powershell
docker-compose up -d db
```
If you enable the PostgreSQL URL in `.env`, the ready health check (`/health/ready`) will report `"ok"` when the DB is reachable.

---
### Troubleshooting
- **`Access is denied` when running the Python executable** – make sure you are invoking the venv's `python.exe` with the full path as shown above, or run the commands from an activated PowerShell session (`(.venv)` prefix).
- **Missing environment variables** – the application will start, but endpoints that depend on them (e.g., real weather) will fall back to mock mode.
- **Docker not installed** – the application will continue using the SQLite fallback; persistence is limited to the local file.

Happy coding!