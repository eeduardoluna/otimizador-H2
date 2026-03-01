# ============================================================
# simulation/solar.py — Conversão de irradiação → potência solar
# ============================================================

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import SOLAR


def irradiance_to_power(irradiance_wm2: float, temperature_c: float) -> float:
    """
    Converte irradiação solar (W/m²) e temperatura ambiente (°C)
    em potência gerada pelo parque solar (kW).

    Modelo simplificado baseado em:
    P = irradiance * area * efficiency * (1 + temp_coeff * (T - 25)) * inverter_eff

    Args:
        irradiance_wm2: Irradiação solar em W/m²
        temperature_c: Temperatura ambiente em °C

    Returns:
        Potência gerada em kW (limitada pela capacidade instalada)
    """
    if irradiance_wm2 <= 0:
        return 0.0

    # Temperatura da célula fotovoltaica (aprox. +25°C acima da ambiente)
    cell_temp = temperature_c + 25.0

    # Fator de correção por temperatura
    temp_factor = 1.0 + SOLAR["temp_coefficient"] * (cell_temp - 25.0)
    temp_factor = max(temp_factor, 0.5)  # Limite inferior de segurança

    # Potência gerada (W)
    power_w = (
        irradiance_wm2
        * SOLAR["panel_area_m2"]
        * SOLAR["efficiency"]
        * temp_factor
        * SOLAR["inverter_efficiency"]
    )

    # Converte para kW e limita pela capacidade instalada
    power_kw = min(power_w / 1000.0, SOLAR["capacity_kw"])

    return round(max(power_kw, 0.0), 2)


def get_capacity() -> float:
    """Retorna a capacidade máxima instalada do parque solar em kW."""
    return SOLAR["capacity_kw"]


if __name__ == "__main__":
    # Teste rápido
    test_cases = [
        (0, 30),
        (200, 28),
        (600, 32),
        (1000, 35),
        (1200, 40),
    ]
    print("Irradiação (W/m²) | Temp (°C) | Potência (kW)")
    print("-" * 48)
    for irr, temp in test_cases:
        p = irradiance_to_power(irr, temp)
        print(f"{irr:>17} | {temp:>9} | {p:>13}")