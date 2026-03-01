# ============================================================
# data/weather.py — Integração com Open-Meteo API
# ============================================================

import httpx
from datetime import datetime, timezone
from typing import Optional
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import LOCATION, SIMULATION

BASE_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_forecast(hours: Optional[int] = None) -> list[dict]:
    """
    Busca previsão horária da Open-Meteo para a localização configurada.

    Retorna lista de dicts com:
        - timestamp: datetime UTC
        - irradiance_wm2: irradiação solar (W/m²)
        - wind_speed_ms: velocidade do vento a 10m (m/s)
        - temperature_c: temperatura ambiente (°C)

    Args:
        hours: Número de horas a retornar (padrão: forecast_horizon do config)
    """
    if hours is None:
        hours = SIMULATION["forecast_horizon"]

    params = {
        "latitude": LOCATION["latitude"],
        "longitude": LOCATION["longitude"],
        "hourly": [
            "shortwave_radiation",       # Irradiação solar (W/m²)
            "windspeed_10m",             # Vento a 10m (m/s)
            "temperature_2m"             # Temperatura (°C)
        ],
        "timezone": LOCATION["timezone"],
        "forecast_days": 2,
        "timeformat": "iso8601"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    hourly = data["hourly"]
    now = datetime.now(timezone.utc)

    results = []
    for i, ts_str in enumerate(hourly["time"]):
        ts = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
        if ts < now:
            continue
        results.append({
            "timestamp": ts.isoformat(),
            "irradiance_wm2": max(hourly["shortwave_radiation"][i] or 0.0, 0.0),
            "wind_speed_ms": hourly["windspeed_10m"][i] or 0.0,
            "temperature_c": hourly["temperature_2m"][i] or 28.0
        })
        if len(results) >= hours:
            break

    # Fallback: se não houver dados suficientes, preenche com valores típicos do Ceará
    while len(results) < hours:
        results.append({
            "timestamp": now.isoformat(),
            "irradiance_wm2": 400.0,
            "wind_speed_ms": 6.0,
            "temperature_c": 30.0
        })

    return results


def fetch_forecast_sync(hours: Optional[int] = None) -> list[dict]:
    """
    Versão síncrona do fetch_forecast para uso em scripts e treino do agente.
    """
    import httpx
    if hours is None:
        hours = SIMULATION["forecast_horizon"]

    params = {
        "latitude": LOCATION["latitude"],
        "longitude": LOCATION["longitude"],
        "hourly": [
            "shortwave_radiation",
            "windspeed_10m",
            "temperature_2m"
        ],
        "timezone": LOCATION["timezone"],
        "forecast_days": 2,
        "timeformat": "iso8601"
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        hourly = data["hourly"]
        now = datetime.now(timezone.utc)

        results = []
        for i, ts_str in enumerate(hourly["time"]):
            ts = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
            if ts < now:
                continue
            results.append({
                "timestamp": ts.isoformat(),
                "irradiance_wm2": max(hourly["shortwave_radiation"][i] or 0.0, 0.0),
                "wind_speed_ms": hourly["windspeed_10m"][i] or 0.0,
                "temperature_c": hourly["temperature_2m"][i] or 28.0
            })
            if len(results) >= hours:
                break
    except Exception as e:
        print(f"[weather] Erro ao buscar dados: {e}. Usando fallback.")
        results = []

    # Fallback com valores típicos do Ceará
    while len(results) < hours:
        results.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "irradiance_wm2": 400.0,
            "wind_speed_ms": 6.0,
            "temperature_c": 30.0
        })

    return results


if __name__ == "__main__":
    data = fetch_forecast_sync(hours=6)
    print(f"Previsão para {LOCATION['name']} — próximas {len(data)}h:")
    print("-" * 60)
    for h in data:
        print(
            f"{h['timestamp']} | "
            f"Solar: {h['irradiance_wm2']:>6.1f} W/m² | "
            f"Vento: {h['wind_speed_ms']:>4.1f} m/s | "
            f"Temp: {h['temperature_c']:>4.1f}°C"
        )