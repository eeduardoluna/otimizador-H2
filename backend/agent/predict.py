# ============================================================
# agent/predict.py — Carrega modelo treinado e toma decisões
# ============================================================

import os
import sys
import numpy as np
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from stable_baselines3 import SAC
from config import MARKET, ELECTROLYZER, TANK, SIMULATION

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
BEST_MODEL_PATH = os.path.join(MODEL_DIR, "best_model", "best_model.zip")
FINAL_MODEL_PATH = os.path.join(MODEL_DIR, "sac_h2optimizer.zip")

_model = None  # Cache do modelo em memória


def load_model():
    """Carrega o modelo treinado. Prioriza o melhor modelo salvo pelo EvalCallback."""
    global _model
    if _model is not None:
        return _model

    if os.path.exists(BEST_MODEL_PATH):
        path = BEST_MODEL_PATH
    elif os.path.exists(FINAL_MODEL_PATH):
        path = FINAL_MODEL_PATH
    else:
        raise FileNotFoundError(
            "Nenhum modelo treinado encontrado. "
            "Execute backend/agent/train.py primeiro."
        )

    _model = SAC.load(path)
    print(f"[predict] Modelo carregado de: {path}")
    return _model


def predict_action(observation: np.ndarray, deterministic: bool = True) -> dict:
    """
    Recebe um vetor de observação e retorna a ação da IA + explicação.

    Args:
        observation: Vetor numpy com o estado atual (23 valores normalizados)
        deterministic: Se True, usa política determinística (recomendado para produção)

    Returns:
        dict com:
            - action: float [0,1] — fração de energia para eletrólise
            - electrolysis_fraction: float — % da energia para H2
            - grid_fraction: float — % da energia para rede
            - reasoning: str — explicação em linguagem simples
    """
    model = load_model()
    action, _ = model.predict(observation, deterministic=deterministic)
    action_value = float(np.clip(action[0], 0.0, 1.0))

    reasoning = _generate_reasoning(observation, action_value)

    return {
        "action": round(action_value, 3),
        "electrolysis_fraction": round(action_value * 100, 1),
        "grid_fraction": round((1 - action_value) * 100, 1),
        "reasoning": reasoning
    }


def _generate_reasoning(obs: np.ndarray, action: float) -> str:
    """
    Gera explicação em linguagem simples para a decisão da IA.
    Usa os valores do vetor de observação para justificar.
    """
    solar_norm = obs[0]
    wind_norm = obs[1]
    price_norm = obs[2]
    tank_level = obs[3]
    hour_norm = obs[4]

    price_mwh = price_norm * MARKET["energy_price_max"]
    tank_pct = tank_level * 100
    hour = int(hour_norm * 23)

    # Previsões (próximas 6h)
    forecast_horizon = SIMULATION["forecast_horizon"]
    price_forecast = obs[5 + forecast_horizon * 2: 5 + forecast_horizon * 3]
    avg_future_price = float(np.mean(price_forecast)) * MARKET["energy_price_max"]

    reasons = []

    # Análise do preço atual vs futuro
    if price_mwh < MARKET["curtailment_threshold"]:
        reasons.append(
            f"preço atual baixo (R${price_mwh:.0f}/MWh — provável curtailment)"
        )
    elif price_mwh > 300:
        reasons.append(f"preço atual alto (R${price_mwh:.0f}/MWh)")

    if avg_future_price > price_mwh * 1.2:
        reasons.append(
            f"preço deve subir nas próximas horas (média prevista R${avg_future_price:.0f}/MWh)"
        )
    elif avg_future_price < price_mwh * 0.8:
        reasons.append(
            f"preço deve cair nas próximas horas (média prevista R${avg_future_price:.0f}/MWh)"
        )

    # Análise do tanque
    if tank_pct > 85:
        reasons.append(f"tanque quase cheio ({tank_pct:.0f}%)")
    elif tank_pct < 20:
        reasons.append(f"tanque baixo ({tank_pct:.0f}%) — oportunidade de produzir H₂")

    # Análise da geração
    total_gen_norm = solar_norm + wind_norm
    if total_gen_norm > 1.2:
        reasons.append("alta geração renovável disponível")
    elif total_gen_norm < 0.2:
        reasons.append("baixa geração disponível")

    # Decisão
    if action > 0.7:
        decision = f"IA direcionou {action*100:.0f}% para eletrólise"
    elif action > 0.3:
        decision = f"IA dividiu energia: {action*100:.0f}% eletrólise / {(1-action)*100:.0f}% rede"
    else:
        decision = f"IA direcionou {(1-action)*100:.0f}% para a rede elétrica"

    if reasons:
        return f"{decision} — {', '.join(reasons)}."
    else:
        return f"{decision}."


if __name__ == "__main__":
    # Teste com observação aleatória
    obs = np.random.uniform(0, 1, size=(23,)).astype(np.float32)
    print("Observação de teste:", obs)
    result = predict_action(obs)
    print("\nDecisão da IA:")
    for k, v in result.items():
        print(f"  {k}: {v}")