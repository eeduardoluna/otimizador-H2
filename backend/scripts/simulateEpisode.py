# ============================================================
# scripts/simulate_episode.py — Roda episódio e imprime decisões hora a hora
# ============================================================

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from simulation.environment import H2OptimizerEnv


def simulate(use_rl: bool = True, seed: int = 42, verbose: bool = True) -> dict:
    """
    Simula um episódio completo (24h) e exibe as decisões hora a hora.

    Args:
        use_rl: Se True usa o agente RL, se False usa regra simples
        seed: Seed para reprodutibilidade
        verbose: Se True imprime no terminal
    """
    env = H2OptimizerEnv()
    obs, _ = env.reset(seed=seed)

    if use_rl:
        try:
            from agent.predict import load_model, predict_action
            load_model()
            agent_label = "Agente RL (PPO)"
        except FileNotFoundError:
            print("[simulate] Modelo não encontrado. Usando regra simples.")
            use_rl = False
            agent_label = "Regra Simples (Baseline)"
    else:
        agent_label = "Regra Simples (Baseline)"

    if verbose:
        print(f"\n{'='*80}")
        print(f"  Simulação 24h — {agent_label}")
        print(f"  Localização: Fortaleza, CE")
        print(f"{'='*80}")
        print(f"{'Hora':>4} | {'Solar':>6} | {'Eólica':>6} | {'Total':>6} | "
              f"{'Ação':>4} | {'H2':>5} | {'Tanque':>6} | "
              f"{'Preço':>6} | {'Lucro':>8} | {'Acu.':>9}")
        print("-" * 80)

    done = False
    while not done:
        if use_rl:
            decision = predict_action(obs)
            action_value = decision["action"]
        else:
            from scripts.generate_baseline import baseline_action
            from data.price import get_spot_price
            hour = (env.current_hour + env.step_count) % 24
            price = get_spot_price(hour)
            action_value = baseline_action(obs, price, env.tank_level)

        obs, reward, terminated, truncated, info = env.step([action_value])
        done = terminated or truncated

        if verbose and env.episode_log:
            last = env.episode_log[-1]
            acum = sum(s["profit"] for s in env.episode_log)
            eletro_icon = "⚡" if last["electrolyzer_on"] else "  "
            print(
                f"{last['hour']:>02d}h  | "
                f"{last['solar_kw']:>5.0f}k | "
                f"{last['wind_kw']:>5.0f}k | "
                f"{last['total_gen_kw']:>5.0f}k | "
                f"{last['action']:>4.2f} | "
                f"{last['h2_produced_kg']:>4.1f}k | "
                f"{last['tank_level']*100:>5.1f}% | "
                f"R${last['price_mwh']:>5.0f} | "
                f"R${last['profit']:>7.2f} | "
                f"R${acum:>8.2f} {eletro_icon}"
            )

    if verbose:
        print("=" * 80)
        print(f"  LUCRO TOTAL DO EPISÓDIO: R$ {env.total_profit:.2f}")
        print(f"  H2 total produzido: {sum(s['h2_produced_kg'] for s in env.episode_log):.2f} kg")
        print(f"  Energia total vendida: {sum(s['energy_to_grid_kw'] for s in env.episode_log)/1000:.2f} MWh")
        print("=" * 80)

    return {
        "agent": agent_label,
        "total_profit": round(env.total_profit, 2),
        "log": env.episode_log
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true", help="Usa regra simples em vez do RL")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--compare", action="store_true", help="Compara RL vs baseline lado a lado")
    parser.add_argument("--save", type=str, default=None, help="Salva log em JSON")
    args = parser.parse_args()

    if args.compare:
        print("\n>>> AGENTE RL:")
        result_rl = simulate(use_rl=True, seed=args.seed)
        print("\n>>> REGRA SIMPLES:")
        result_bl = simulate(use_rl=False, seed=args.seed)
        diff = result_rl["total_profit"] - result_bl["total_profit"]
        print(f"\n💰 Diferença de lucro: R$ {diff:+.2f} ({diff/abs(result_bl['total_profit'])*100:+.1f}%)")
    else:
        result = simulate(use_rl=not args.baseline, seed=args.seed)
        if args.save:
            with open(args.save, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nLog salvo em: {args.save}")