# ============================================================
# config.py — Parâmetros físicos e econômicos do sistema
# ============================================================

SOLAR = {
    "capacity_kw": 500,
    "panel_efficiency": 0.20,
    "temp_coefficient": -0.004,
    "reference_temp": 25,
    "panel_area_m2": 2500,
    "efficiency": 0.20,
    "inverter_efficiency": 0.97,
}

WIND = {
    "capacity_kw": 300,
    "cut_in_speed": 3.0,
    "rated_speed": 12.0,
    "cut_out_speed": 25.0,
    "rotor_diameter": 40,
}

ELECTROLYZER = {
    # Potência
    "max_power_kw": 400,
    "min_power_kw": 20,          # mínimo para ligar (5% da capacidade)

    # Eficiência base a 50% de carga (kWh por kg H2)
    # Curva real: piora abaixo de 20% e acima de 85% da carga
    "efficiency_base_kwh_per_kg": 52.0,

    # Custos operacionais
    "startup_cost": 5.0,              # R$ por partida
    "operating_cost_per_hour": 8.0,   # R$ por hora rodando
    "ramp_rate_per_step": 0.35,       # máximo de variação de carga por hora (35%)

    # Degradação por partidas excessivas
    "degradation_per_start": 0.0005,  # perda de eficiência por partida (0.05%)
}

TANK = {
    "capacity_kg": 1000,
    "initial_level": 0.30,
    "max_level": 0.95,
    "min_level": 0.05,
    "storage_cost_per_kg_hour": 0.08,
}

MARKET = {
    "h2_price_per_kg": 18.0,
    "energy_price_max": 600,
    "energy_price_min": 80,
    "curtailment_threshold": 150,
    # Bônus de preço H2 quando tanque está baixo (comprador urgente)
    "h2_price_bonus_empty_tank": 5.0,
    # Desconto quando tanque está cheio (vendedor desesperado)
    "h2_price_discount_full_tank": 3.0,
}

SIMULATION = {
    "episode_length": 24,
    "timestep_hours": 1,
    "forecast_horizon": 6,
    "location": "Fortaleza, CE",
    "training_episodes": 5000,
    "seed": 42,
}

REWARD = {
    "profit_weight": 1.0,
    "waste_penalty": 0.4,
    "tank_overflow_penalty": 10.0,
    "tank_empty_penalty": 10.0,
    "ramp_violation_penalty": 2.0,
}
LOCATION = {
    "city": "Fortaleza",
    "state": "CE",
    "latitude": -3.7172,
    "longitude": -38.5433,
    "timezone": "America/Fortaleza",
}
DATABASE = {
    "path": "data/h2_optimizer.db",
}
API = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": True,
    "reload": True,
}