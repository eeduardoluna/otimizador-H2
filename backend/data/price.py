# ============================================================
# data/price.py — Simulação de preço spot de energia (R$/MWh)
# ============================================================

import numpy as np
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import MARKET, SIMULATION


def get_spot_price(hour_of_day: int, noise_std: float = 30.0, seed: int = None) -> float:
    """
    Simula preço spot de energia para uma hora do dia.

    O perfil segue padrão realista do mercado brasileiro (PLD):
    - Madrugada (0-5h): preço baixo
    - Manhã (6-9h): subida gradual
    - Meio do dia (10-15h): queda por excesso solar (curtailment)
    - Tarde (16-19h): pico de demanda
    - Noite (20-23h): queda gradual

    Args:
        hour_of_day: Hora do dia (0-23)
        noise_std: Desvio padrão do ruído aleatório (R$/MWh)
        seed: Seed para reprodutibilidade

    Returns:
        Preço spot em R$/MWh
    """
    if seed is not None:
        np.random.seed(seed)

    # Perfil base (R$/MWh) por hora
    base_profile = [
        180, 170, 165, 160, 165, 175,  # 0-5h (madrugada)
        210, 250, 280, 260, 200, 180,  # 6-11h (manhã → queda solar)
        160, 150, 155, 180, 240, 320,  # 12-17h (curtailment → pico tarde)
        350, 340, 300, 260, 220, 195   # 18-23h (pico noite → queda)
    ]

    base = base_profile[hour_of_day % 24]
    noise = np.random.normal(0, noise_std)
    price = base + noise

    # Limita ao intervalo configurado
    price = np.clip(price, MARKET["energy_price_min"], MARKET["energy_price_max"])

    return round(float(price), 2)


def get_price_forecast(current_hour: int, horizon: int = None) -> list[float]:
    """
    Retorna previsão de preço spot para as próximas `horizon` horas.
    Inclui ruído crescente para simular incerteza da previsão.

    Args:
        current_hour: Hora atual do dia (0-23)
        horizon: Número de horas à frente (padrão: forecast_horizon do config)

    Returns:
        Lista de preços previstos (R$/MWh)
    """
    if horizon is None:
        horizon = SIMULATION["forecast_horizon"]

    prices = []
    for i in range(1, horizon + 1):
        hour = (current_hour + i) % 24
        # Ruído cresce com o horizonte (previsões mais distantes são menos certas)
        noise_std = 20.0 + i * 8.0
        price = get_spot_price(hour, noise_std=noise_std)
        prices.append(price)

    return prices


def is_curtailment_likely(price: float) -> bool:
    """Retorna True se o preço indica provável curtailment."""
    return price <= MARKET["curtailment_threshold"]


if __name__ == "__main__":
    print("Perfil de preço spot simulado — 24 horas:")
    print("-" * 40)
    for h in range(24):
        price = get_spot_price(h, noise_std=0)  # Sem ruído para visualizar perfil base
        curtailment = " ← curtailment" if is_curtailment_likely(price) else ""
        bar = "█" * int(price / 20)
        print(f"{h:02d}h | R${price:>6.0f}/MWh | {bar}{curtailment}")