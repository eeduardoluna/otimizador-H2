# ============================================================
# api/routes_dashboard.py
# ============================================================

from fastapi import APIRouter
import numpy as np
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.weather import fetch_forecast_sync
from data.price import get_spot_price, get_price_forecast
from simulation.solar import irradiance_to_power
from simulation.wind import wind_speed_to_power
from data.database import get_recent_operations, get_cumulative_profit
from config import TANK, MARKET

router = APIRouter()


@router.get("/current")
def get_current_state():
    """Estado atual do sistema — usado para atualização em tempo real."""
    forecast = fetch_forecast_sync(hours=1)
    weather = forecast[0] if forecast else {"irradiance_wm2": 400, "wind_speed_ms": 6, "temperature_c": 30}

    from datetime import datetime
    hour = datetime.now().hour
    price = get_spot_price(hour)

    solar_kw = irradiance_to_power(weather["irradiance_wm2"], weather["temperature_c"])
    wind_kw = wind_speed_to_power(weather["wind_speed_ms"])

    ops = get_recent_operations(limit=1)
    tank_level = ops[0]["tank_level"] if ops else TANK["initial_level"]

    return {
        "hour": hour,
        "solar_kw": solar_kw,
        "wind_kw": wind_kw,
        "total_gen_kw": round(solar_kw + wind_kw, 2),
        "price_mwh": price,
        "tank_level": round(tank_level * 100, 1),
        "cumulative_profit": get_cumulative_profit(),
        "curtailment_risk": price < MARKET["curtailment_threshold"],
        "weather": weather
    }


@router.get("/forecast")
def get_forecast():
    """Previsão das próximas 6 horas para exibição nos gráficos."""
    from datetime import datetime
    current_hour = datetime.now().hour
    weather_data = fetch_forecast_sync(hours=6)

    result = []
    for i, w in enumerate(weather_data):
        hour = (current_hour + i + 1) % 24
        solar = irradiance_to_power(w["irradiance_wm2"], w["temperature_c"])
        wind = wind_speed_to_power(w["wind_speed_ms"])
        price = get_spot_price(hour, noise_std=20 + i * 8)
        result.append({
            "hour": hour,
            "solar_kw": solar,
            "wind_kw": wind,
            "total_gen_kw": round(solar + wind, 2),
            "price_mwh": price,
            "timestamp": w["timestamp"]
        })

    return {"forecast": result}