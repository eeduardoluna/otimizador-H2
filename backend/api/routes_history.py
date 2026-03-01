# ============================================================
# api/routes_history.py
# ============================================================

from fastapi import APIRouter
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_recent_operations, get_cumulative_profit

router = APIRouter()


@router.get("/operations")
def get_operations(limit: int = 24):
    """Retorna histórico de operações para os gráficos."""
    ops = get_recent_operations(limit=limit)
    return {"operations": ops, "count": len(ops)}


@router.get("/profit")
def get_profit_summary():
    """Retorna resumo de lucro acumulado."""
    ops = get_recent_operations(limit=24)
    cumulative = []
    acum = 0
    for op in ops:
        acum += op.get("profit", 0)
        cumulative.append({
            "hour": op.get("hour"),
            "profit": op.get("profit"),
            "cumulative_profit": round(acum, 2)
        })
    return {
        "total_profit": get_cumulative_profit(),
        "cumulative_series": cumulative
    }


@router.get("/comparison")
def get_comparison():
    """
    Retorna dados para o gráfico comparativo RL vs Baseline.
    Roda ambos os agentes com o mesmo seed e retorna os logs.
    """
    from simulation.environment import H2OptimizerEnv
    from data.price import get_spot_price
    from scripts.generate_baseline import baseline_action

    results = {}

    # Baseline
    env_bl = H2OptimizerEnv()
    obs, _ = env_bl.reset(seed=42)
    done = False
    while not done:
        hour = (env_bl.current_hour + env_bl.step_count) % 24
        price = get_spot_price(hour)
        action = baseline_action(obs, price, env_bl.tank_level)
        obs, _, terminated, truncated, _ = env_bl.step([action])
        done = terminated or truncated

    baseline_cumulative = []
    acum = 0
    for step in env_bl.episode_log:
        acum += step["profit"]
        baseline_cumulative.append({"hour": step["hour"], "cumulative_profit": round(acum, 2)})

    results["baseline"] = {
        "total_profit": round(env_bl.total_profit, 2),
        "cumulative_series": baseline_cumulative
    }

    # RL
    try:
        from agent.predict import predict_action
        env_rl = H2OptimizerEnv()
        obs, _ = env_rl.reset(seed=42)
        done = False
        while not done:
            decision = predict_action(obs)
            obs, _, terminated, truncated, _ = env_rl.step([decision["action"]])
            done = terminated or truncated

        rl_cumulative = []
        acum = 0
        for step in env_rl.episode_log:
            acum += step["profit"]
            rl_cumulative.append({"hour": step["hour"], "cumulative_profit": round(acum, 2)})

        results["rl_agent"] = {
            "total_profit": round(env_rl.total_profit, 2),
            "cumulative_series": rl_cumulative
        }
        improvement = (env_rl.total_profit - env_bl.total_profit) / abs(env_bl.total_profit) * 100
        results["improvement_pct"] = round(improvement, 2)
    except FileNotFoundError:
        results["rl_agent"] = None
        results["message"] = "Modelo RL não disponível"

    return results