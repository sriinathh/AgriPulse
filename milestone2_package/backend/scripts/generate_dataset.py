"""Generate a SYNTHETIC but physically-grounded irrigation dataset for development of Weeks 1-4.

NOT real measurements. Every row is produced by a simulator:
  weather generator (monthly climate, wet/dry Markov chain, diurnal cycle)
  -> FAO-56 style crop water use (Hargreaves ET0 x stage-dependent Kc)
  -> single-layer soil water balance (rain, irrigation, ET, drainage)
  -> simulated farmer irrigating by a noisy threshold rule.
Monthly climate numbers below are APPROXIMATE regional averages, not station data.

Outputs (default data/synthetic/):
  irrigation_dataset.csv  ONE file, one row per field-day at 06:00: sensor soil moisture + crop info + weather
                          columns + targets (irrigate_today, irrigation_mm). This is the training set.
With --raw also: fields.csv, sensor_readings.csv (hourly, with nulls/spikes/outages), irrigation_events.csv.
Weather: the weather columns exist ONLY so a model can learn from them. In the running system the same
values come from the live weather API; no generated weather is ever stored in the weather_data table.
"""
import argparse
import math
import os
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

IST = timedelta(hours=5, minutes=30)

# month-indexed (Jan..Dec) approximate climate: Tmax, Tmin (C), rainfall (mm/month), mean RH (%)
SITES = {
    "Hyderabad": dict(state="Telangana", lat=17.385, lon=78.487,
                      tmax=[29, 32, 35, 38, 39, 34, 31, 30, 31, 31, 29, 28], tmin=[15, 18, 21, 25, 27, 24, 23, 23, 23, 21, 17, 14],
                      rain=[5, 8, 15, 25, 30, 100, 150, 140, 160, 100, 25, 5], rh=[55, 45, 40, 40, 45, 65, 75, 78, 75, 65, 58, 56]),
    "Bengaluru": dict(state="Karnataka", lat=12.972, lon=77.594,
                      tmax=[28, 31, 33, 34, 33, 30, 28, 28, 29, 28, 27, 27], tmin=[15, 17, 19, 21, 21, 20, 19, 19, 19, 19, 17, 15],
                      rain=[3, 5, 10, 45, 110, 80, 110, 130, 190, 160, 60, 15], rh=[60, 52, 48, 55, 62, 70, 75, 76, 76, 74, 68, 63]),
    "Pune": dict(state="Maharashtra", lat=18.520, lon=73.857,
                 tmax=[30, 32, 36, 38, 37, 32, 28, 28, 29, 32, 31, 29], tmin=[11, 12, 16, 20, 23, 23, 22, 22, 21, 18, 14, 11],
                 rain=[2, 1, 5, 15, 35, 120, 190, 130, 110, 80, 20, 3], rh=[50, 42, 36, 38, 48, 72, 82, 82, 78, 62, 52, 50]),
    "Ludhiana": dict(state="Punjab", lat=30.901, lon=75.857,
                     tmax=[18, 22, 28, 36, 40, 39, 35, 34, 34, 32, 26, 20], tmin=[6, 9, 14, 20, 25, 28, 27, 26, 24, 18, 11, 7],
                     rain=[25, 30, 25, 15, 20, 80, 220, 200, 120, 15, 5, 10], rh=[78, 70, 58, 42, 40, 55, 78, 82, 72, 62, 66, 76]),
}

# volumetric %: field capacity, wilting point
SOILS = {"Red Sandy Loam": (24, 11), "Black Clay": (38, 22), "Loam": (30, 14), "Alluvial Sandy Loam": (26, 10)}

# FAO-56-style: Kc ini/mid/end, stage lengths (ini, dev, mid, late) days, depletion fraction p
CROPS = {
    "Rice": dict(kc=(1.05, 1.20, 0.90), days=(20, 30, 40, 30), p=0.20, perc=4.0, methods=["Flood"]),
    "Maize": dict(kc=(0.30, 1.20, 0.60), days=(20, 35, 40, 25), p=0.55, perc=0.0, methods=["Sprinkler", "Flood"]),
    "Cotton": dict(kc=(0.35, 1.15, 0.70), days=(30, 50, 40, 0), p=0.65, perc=0.0, methods=["Drip", "Sprinkler"]),
    "Wheat": dict(kc=(0.30, 1.15, 0.40), days=(20, 30, 40, 30), p=0.55, perc=0.0, methods=["Sprinkler", "Flood"]),
}
METHOD = {"Drip": (0.90, 3.0), "Sprinkler": (0.75, 6.0), "Flood": (0.60, 15.0)}  # efficiency, mm/h

KHARIF = [("Hyderabad", "Rice"), ("Hyderabad", "Cotton"), ("Hyderabad", "Maize"), ("Bengaluru", "Rice"),
          ("Bengaluru", "Maize"), ("Pune", "Cotton"), ("Pune", "Maize"), ("Ludhiana", "Rice")]
RABI = [("Hyderabad", "Maize"), ("Hyderabad", "Wheat"), ("Bengaluru", "Maize"), ("Pune", "Wheat"),
        ("Ludhiana", "Wheat"), ("Ludhiana", "Maize")]
NAMES = ["Harini", "Ravi", "Lakshmi", "Suresh", "Anitha", "Manjunath", "Kavitha", "Gurpreet", "Savitri", "Venkatesh",
         "Padma", "Balwinder"]
D_MM = 500.0  # effective root-zone depth represented by the sensor (mm)


def es(t):  # saturation vapour pressure, kPa
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def ra_mm(lat, doy):
    phi, dr = math.radians(lat), 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    dec = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(dec))))
    ra = 24 * 60 / math.pi * 0.082 * dr * (ws * math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.sin(ws))
    return 0.408 * ra


def monthly(arr, d: date):  # linear interpolation between mid-month values
    x = d.month - 1 + (d.day - 15) / 30.0
    i0 = int(math.floor(x)) % 12
    i1 = (i0 + 1) % 12
    f = x - math.floor(x)
    return arr[i0] * (1 - f) + arr[i1] * f


def weather(site, start: date, days, rng):
    s = SITES[site]
    n = days * 24
    T, RH, R = np.zeros(n), np.zeros(n), np.zeros(n)
    et0_day, tmean_day, rain_day = np.zeros(days), np.zeros(days), np.zeros(days)
    anom, wet = 0.0, rng.random() < 0.3
    for d in range(days):
        day = start + timedelta(days=d)
        mrain = monthly(s["rain"], day)
        wet_days = max(0.5, mrain / 9.0)
        p_wet = min(0.8, wet_days / 30.0)
        p_ww = min(0.9, p_wet + 0.35 * (1 - p_wet))
        p_dw = p_wet * (1 - p_ww) / (1 - p_wet)
        wet = rng.random() < (p_ww if wet else p_dw)
        rain = float(min(150, rng.gamma(0.7, (mrain / wet_days) / 0.7))) if wet else 0.0
        anom = 0.7 * anom + rng.normal(0, 1.5)
        tmax = monthly(s["tmax"], day) + anom - (min(6, 3 + 0.03 * rain) if wet else 0)
        tmin = monthly(s["tmin"], day) + 0.5 * anom + (0.5 if wet else 0)
        rh_mean = float(np.clip(monthly(s["rh"], day) + (15 if wet else 0) + rng.normal(0, 5), 20, 98))
        tmean = (tmax + tmin) / 2
        hrs = np.arange(1, 25) % 24  # clock hour at the end of each hourly block
        T[d * 24:(d + 1) * 24] = tmin + (tmax - tmin) * 0.5 * (1 + np.cos(2 * np.pi * (hrs - 15) / 24))
        RH[d * 24:(d + 1) * 24] = np.clip(100 * (rh_mean / 100 * es(tmean)) / es(T[d * 24:(d + 1) * 24]), 15, 100)
        if rain > 0:  # concentrate in 1-6 hours, afternoon-biased
            k = int(rng.integers(1, 7))
            start_h = int(np.clip(rng.normal(15, 4), 0, 23 - k + 1)) if k < 24 else 0
            R[d * 24 + start_h:d * 24 + start_h + k] += rain * rng.dirichlet(np.ones(k))
        et0_day[d] = max(0.0, 0.0023 * (tmean + 17.8) * math.sqrt(max(tmax - tmin, 0.1)) * ra_mm(s["lat"], day.timetuple().tm_yday))
        tmean_day[d], rain_day[d] = tmean, rain
    w = np.maximum(0, np.sin(np.pi * (np.arange(24) - 6) / 12)); w /= w.sum()  # blocks 6..17 carry ET
    ET0 = np.concatenate([et0_day[d] * w for d in range(days)])
    return T, RH, np.round(R, 2), ET0, et0_day


def kc_at(crop, das):
    c = CROPS[crop]
    k_ini, k_mid, k_end = c["kc"]
    d_ini, d_dev, d_mid, d_late = c["days"]
    if das < d_ini:
        return k_ini
    if das < d_ini + d_dev:
        return k_ini + (k_mid - k_ini) * (das - d_ini) / d_dev
    if das < d_ini + d_dev + d_mid:
        return k_mid
    if d_late == 0:
        return k_mid
    return max(k_end, k_mid + (k_end - k_mid) * (das - d_ini - d_dev - d_mid) / d_late)


def stage_at(crop, das):
    d_ini, d_dev, d_mid, _ = CROPS[crop]["days"]
    return "Sowing" if das < d_ini else "Vegetative" if das < d_ini + d_dev else "Flowering" if das < d_ini + d_dev + d_mid else "Harvest"


def simulate_field(f, T, RH, R, ET0, days, rng):
    fc, wp = SOILS[f["soil_type"]]
    crop = CROPS[f["crop_type"]]
    eff, rate = METHOD[f["irrigation_type"]]
    aggr = f["aggressiveness"]
    n = days * 24
    theta, sim = np.zeros(n), fc * (1.0 if f["crop_type"] == "Rice" else 0.9)
    irr_net = np.zeros(n)
    events, last_irr_day = [], -9
    for i in range(n):
        d, hb = divmod(i, 24)
        if hb == 6 and d >= 1:  # farmer decision at 06:00 on the state after block 5
            trig = fc - min(0.9, crop["p"] * aggr) * (fc - wp)
            fcst = R[i:i + 24].sum() + rng.normal(0, 0.3 * R[i:i + 24].sum() + 0.5)  # imperfect forecast
            if sim <= trig and fcst < 8 and d - last_irr_day >= 2 and rng.random() > 0.04:
                net = max(3.0, (fc - sim) / 100 * D_MM * rng.uniform(0.85, 1.15))
                gross = net / eff
                dur_h = max(0.5, gross / rate)
                span = max(1, math.ceil(dur_h))
                irr_net[i:i + span] += net / span if i + span <= n else 0
                start = f["_t0"] + timedelta(hours=i)
                events.append(dict(field_id=f["field_id"], start_time=start, duration_min=int(round(dur_h * 60)),
                                   volume_mm=round(gross, 2), net_mm=round(net, 2),
                                   volume_litres=int(round(gross * f["area_hectares"] * 10000)), method=f["irrigation_type"],
                                   day=d, is_simulated=True))
                last_irr_day = d
        das = d
        etc = ET0[i] * kc_at(f["crop_type"], das)
        crit = fc - crop["p"] * (fc - wp)
        ks = 1.0 if sim >= crit else max(0.0, (sim - wp) / max(crit - wp, 1e-6))
        rain_eff = R[i] * (0.9 if R[i] > 10 else 1.0)
        sim += (rain_eff + irr_net[i] - etc * ks - crop["perc"] / 24) / D_MM * 100
        if sim > fc:
            sim -= 0.25 * (sim - fc)
        sim = float(min(fc + 8, max(wp * 0.8, sim)))
        theta[i] = sim
    return theta, events


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/synthetic")
    ap.add_argument("--fields", type=int, default=24)
    ap.add_argument("--days", type=int, default=120)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--raw", action="store_true", help="also write hourly sensor_readings.csv / fields.csv / irrigation_events.csv (for testing ingestion)")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    os.makedirs(a.out, exist_ok=True)

    combos = [(c, "Kharif") for c in KHARIF] + [(c, "Rabi") for c in RABI]
    n_farmers = math.ceil(a.fields / 3)
    fields = []
    for k in range(a.fields):
        (site, crop), season = combos[k % len(combos)]
        s = SITES[site]
        sow = date(2025, 6, 15) + timedelta(days=int(rng.integers(0, 21))) if season == "Kharif" \
            else date(2025, 11, 5) + timedelta(days=int(rng.integers(0, 21)))
        fields.append(dict(
            field_id=f"F{k + 1:03d}", sensor_id=f"SM{k + 1:03d}", farmer_id=f"FR{k % n_farmers + 1:03d}",
            farmer_name=NAMES[(k % n_farmers) % len(NAMES)], name=f"{crop} plot {k + 1}",
            location_name=f"{site}, {s['state']}", site=site, latitude=round(s["lat"] + rng.uniform(-0.05, 0.05), 4),
            longitude=round(s["lon"] + rng.uniform(-0.05, 0.05), 4), crop_type=crop,
            area_hectares=round(float(rng.uniform(0.5, 4.0)), 2), soil_type=list(SOILS)[int(rng.integers(0, len(SOILS)))],
            irrigation_type=str(rng.choice(CROPS[crop]["methods"])), season=season, sowing_date=sow.isoformat(),
            aggressiveness=float(rng.uniform(0.85, 1.15)), sensor_bias=float(rng.normal(0, 1.0))))

    sensor_rows, weather_rows, event_rows, ml_rows = [], [], [], []
    n = a.days * 24
    for f in fields:
        sow = date.fromisoformat(f["sowing_date"])
        f["_t0"] = datetime(sow.year, sow.month, sow.day)  # local (IST) start
        T, RH, R, ET0, et0_day = weather(f["site"], sow, a.days, rng)
        theta, events = simulate_field(f, T, RH, R, ET0, a.days, rng)
        ts_utc = [f["_t0"] + timedelta(hours=i + 1) - IST for i in range(n)]  # reading/weather stamped at block end
        iso = [t.isoformat() for t in ts_utc]

        # --- sensor stream with realistic faults (these are what the Week-1 cleaning layer must catch)
        meas = np.clip(theta + f["sensor_bias"] + rng.normal(0, 0.7, n), 0, 100).round(2).astype(object)
        valid_for_ml = np.array(meas, dtype=float)
        keep = np.ones(n, bool)
        for _ in range(2):  # 2 outages of 6-48 h (rows missing entirely)
            s0, ln = int(rng.integers(0, n - 48)), int(rng.integers(6, 49))
            keep[s0:s0 + ln] = False
        bad = rng.random(n)
        meas[bad < 0.015] = None                               # null reading
        spike = (bad >= 0.015) & (bad < 0.018)
        meas[spike] = rng.choice([250, -999, 101.5, 180], spike.sum())  # impossible values
        valid_for_ml[(bad < 0.018) | ~keep] = np.nan
        for i in np.flatnonzero(keep):
            sensor_rows.append((f["sensor_id"], f["field_id"], iso[i], meas[i], True))

        # --- weather with API-downtime gaps
        wkeep = np.ones(n, bool)
        for _ in range(int(n / 24 / 6)):
            s0 = int(rng.integers(0, n - 6))
            wkeep[s0:s0 + int(rng.integers(3, 7))] = False
        for i in np.flatnonzero(wkeep):
            weather_rows.append((f["field_id"], iso[i], round(float(T[i]), 1), round(float(RH[i]), 1), round(float(R[i]), 2), "synthetic"))

        # --- irrigation events
        for e in events:
            e["start_time"] = (e["start_time"] - IST).isoformat()
            event_rows.append(e)

        # --- ML daily table (decision at 06:00 local)
        ev_by_day = {}
        for e in events:
            ev_by_day.setdefault(e["day"], []).append(e["volume_mm"])
        last = None
        for d in range(3, a.days):
            i6 = d * 24 + 5  # block 5 end == 06:00 reading
            prev24 = R[i6 - 23:i6 + 1].sum()
            sm = valid_for_ml[i6]
            sm_prev = valid_for_ml[i6 - 24]
            vols = ev_by_day.get(d, [])
            irr7 = sum(sum(ev_by_day.get(k, [])) for k in range(max(0, d - 7), d))
            days_since = next((d - k for k in range(d - 1, -1, -1) if k in ev_by_day), 99)
            fut = R[i6 + 1:i6 + 25].sum() if i6 + 25 <= n else R[i6 + 1:].sum()
            ml_rows.append(dict(
                field_id=f["field_id"], date=(f["_t0"] + timedelta(days=d)).date().isoformat(), crop_type=f["crop_type"],
                soil_type=f["soil_type"], irrigation_type=f["irrigation_type"], days_after_sowing=d,
                growth_stage=stage_at(f["crop_type"], d),
                soil_moisture_0600=None if np.isnan(sm) else round(sm, 2),
                soil_moisture_change_24h=None if np.isnan(sm) or np.isnan(sm_prev) else round(sm - sm_prev, 2),
                temperature_0600=round(float(T[i6]), 1), humidity_0600=round(float(RH[i6]), 1),
                rain_prev24h_mm=round(float(prev24), 2),
                rain_forecast_next24h_mm=round(float(max(0, fut + rng.normal(0, 0.3 * fut + 0.5))), 2),
                irrigation_prev7d_mm=round(irr7, 2), days_since_irrigation=days_since,
                irrigate_today=int(bool(vols)), irrigation_mm=round(sum(vols), 2)))

    pd.DataFrame(ml_rows).to_csv(f"{a.out}/irrigation_dataset.csv", index=False)
    written = ["irrigation_dataset"]
    if a.raw:
        pd.DataFrame([{k: v for k, v in f.items() if not k.startswith("_") and k not in ("aggressiveness", "sensor_bias")} for f in fields]) \
            .to_csv(f"{a.out}/fields.csv", index=False)
        pd.DataFrame(sensor_rows, columns=["sensor_id", "field_id", "timestamp", "soil_moisture", "is_simulated"]) \
            .to_csv(f"{a.out}/sensor_readings.csv", index=False)
        ev = pd.DataFrame(event_rows).drop(columns=["day"])
        ev.insert(0, "event_id", range(1, len(ev) + 1))
        ev.to_csv(f"{a.out}/irrigation_events.csv", index=False)
        written += ["fields", "sensor_readings", "irrigation_events"]
        # NOTE: no weather file is written. Weather comes ONLY from the live API at runtime.
    print(f"*** SYNTHETIC DATA written to {a.out}/ (seed={a.seed}) ***")
    for name in written:
        print(f"  {name}.csv: {len(pd.read_csv(f'{a.out}/{name}.csv'))} rows")


if __name__ == "__main__":
    main()
