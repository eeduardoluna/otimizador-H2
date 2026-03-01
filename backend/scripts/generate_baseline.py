# ============================================================
# scripts/generate_baseline.py — Simula regra condicional simples
# para comparação com o agente RL
# ============================================================

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from simulation.environment import H2OptimizerEnv
from data.price import is_curtailment_likely
from config import MARKET, TANK


def baseline_action(obs, price_mwh: float, tank_level: float) -> float:
    """
    Regra condicional simples (o 'operador burro'):
    - Se preço baixo (curtailment) E tanque não cheio → eletrolisa tudo
    - Se preço alto → vende tudo para a rede
    - Caso intermediário → divide 50/50
    """
    tank_pct = tank_level

    if is_curtailment_likely(price_mwh) and tank_pct < TANK["max_level"]:
        return 1.0  # Produz H2
    elif price_mwh > 300:
        return 0.0  # Vende para a rede
    else:
        return 0.5  # Divide


def run_baseline_episode(seed: int = 42) -> dict:
    """Roda um episódio completo com a regra simples e retorna o log."""
    env = H2OptimizerEnv()
    obs, _ = env.reset(seed=seed)

    done = False
    while not done:
        step_idx = env.step_count
        hour = (env.current_hour + step_idx) % 24

        from data.price import get_spot_price
        price = get_spot_price(hour)
        action_value = baseline_action(obs, price, env.tank_level)

        obs, reward, terminated, truncated, info = env.step([action_value])
        done = terminated or truncated

    return {
        "total_profit": round(env.total_profit, 2),
        "log": env.episode_log
    }


def run_comparison(n_episodes: int = 100, seed_start: int = 0) -> dict:
    """
    Compara o agente RL com a regra simples em N episódios.
    Retorna estatísticas de lucro para ambos.
    """
    try:
        from agent.predict import load_model, predict_action
        model_available = True
        load_model()
        print("[baseline] Modelo RL carregado com sucesso.")
    except FileNotFoundError:
        model_available = False
        print("[baseline] Modelo RL não encontrado. Rodando apenas baseline.")

    baseline_profits = []
    rl_profits = []

    for ep in range(n_episodes):
        seed = seed_start + ep

        # Baseline
        result = run_baseline_episode(seed=seed)
        baseline_profits.append(result["total_profit"])

        # RL (se disponível)
        if model_available:
            env = H2OptimizerEnv()
            obs, _ = env.reset(seed=seed)
            done = False
            while not done:
                decision = predict_action(obs)
                obs, _, terminated, truncated, _ = env.step([decision["action"]])
                done = terminated or truncated
            rl_profits.append(round(env.total_profit, 2))

        if (ep + 1) % 10 == 0:
            print(f"[baseline] Episódio {ep+1}/{n_episodes} concluído")

    import numpy as np
    stats = {
        "n_episodes": n_episodes,
        "baseline": {
            "mean_profit": round(float(np.mean(baseline_profits)), 2),
            "std_profit": round(float(np.std(baseline_profits)), 2),
            "min_profit": round(float(np.min(baseline_profits)), 2),
            "max_profit": round(float(np.max(baseline_profits)), 2),
        }
    }

    if model_available and rl_profits:
        improvement = (np.mean(rl_profits) - np.mean(baseline_profits)) / abs(np.mean(baseline_profits)) * 100
        stats["rl_agent"] = {
            "mean_profit": round(float(np.mean(rl_profits)), 2),
            "std_profit": round(float(np.std(rl_profits)), 2),
            "min_profit": round(float(np.min(rl_profits)), 2),
            "max_profit": round(float(np.max(rl_profits)), 2),
        }
        stats["improvement_pct"] = round(float(improvement), 2)
        print(f"\n[baseline] RL vs Baseline: {improvement:+.1f}% de lucro médio")

    return stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--output", type=str, default="baseline_comparison.json")
    args = parser.parse_args()

    print(f"[baseline] Rodando {args.episodes} episódios de comparação...")
    stats = run_comparison(n_episodes=args.episodes)

    print("\n=== RESULTADOS ===")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    output_path = os.path.join(os.path.dirname(__file__), args.output)
    with open(output_path, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\n[baseline] Resultados salvos em: {output_path}")