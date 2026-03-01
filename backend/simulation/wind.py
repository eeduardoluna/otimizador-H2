# ============================================================
# simulation/wind.py — Conversão de velocidade do vento → potência eólica
# ============================================================

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import WIND


def wind_speed_to_power(wind_speed_ms: float) -> float:
    """
    Converte velocidade do vento (m/s) em potência gerada pela turbina (kW).

    Modelo de curva de potência simplificado:
    - Abaixo de cut_in: sem geração
    - Entre cut_in e rated: crescimento cúbico (P ∝ v³)
    - Entre rated e cut_out: potência nominal
    - Acima de cut_out: desligamento por segurança

    Args:
        wind_speed_ms: Velocidade do vento em m/s

    Returns:
        Potência gerada em kW
    """
    v = wind_speed_ms
    cut_in = WIND["cut_in_speed"]
    rated = WIND["rated_speed"]
    cut_out = WIND["cut_out_speed"]
    capacity = WIND["capacity_kw"]

    if v < cut_in or v >= cut_out:
        return 0.0

    if v >= rated:
        return float(capacity)

    # Região cúbica: interpolação entre cut_in e rated
    power_fraction = (v**3 - cut_in**3) / (rated**3 - cut_in**3)
    power_kw = power_fraction * capacity

    return round(max(power_kw, 0.0), 2)


def get_capacity() -> float:
    """Retorna a capacidade máxima instalada da turbina eólica em kW."""
    return WIND["capacity_kw"]


if __name__ == "__main__":
    # Teste rápido
    test_speeds = [0, 2, 3, 5, 8, 12, 15, 20, 25, 30]
    print("Velocidade (m/s) | Potência (kW)")
    print("-" * 34)
    for v in test_speeds:
        p = wind_speed_to_power(v)
        print(f"{v:>16} | {p:>12}")