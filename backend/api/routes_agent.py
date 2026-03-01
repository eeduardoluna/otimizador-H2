# ============================================================
# api/routes_agent.py
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from simulation.environment import H2OptimizerEnv
from data.database import save_operation, clear_operations
from config import TANK, SIMULATION

router = APIRouter()

# Estado global do episódio em andamento
_env_state = {"env": None, "obs": None, "active": False}


class StepRequest(BaseModel):
    tank_level: float = TANK["initial_level"]


@router.post("/start")
def start_episode():
    """Inicia um novo episódio de simulação."""
    env = H2OptimizerEnv()
    obs, _ = env.reset(seed=42)
    _env_state["env"] = env
    _env_state["obs"] = obs
    _env_state["active"] = True
    clear_operations()
    return {"message": "Episódio iniciado", "episode_length": SIMULATION["episode_length"]}


@router.post("/step")
def step_episode():
    """Executa um passo da simulação com a decisão do agente RL."""
    if not _env_state["active"] or _env_state["env"] is None:
        raise HTTPException(status_code=400, detail="Nenhum episódio ativo. Use /start primeiro.")

    try:
        from agent.predict import predict_action
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Modelo não treinado. Execute train.py primeiro.")

    env = _env_state["env"]
    obs = _env_state["obs"]

    decision = predict_action(obs)
    new_obs, reward, terminated, truncated, info = env.step([decision["action"]])

    _env_state["obs"] = new_obs
    if terminated or truncated:
        _env_state["active"] = False

    last = env.episode_log[-1] if env.episode_log else {}
    save_operation(last, reasoning=decision["reasoning"])

    return {
        "step": env.step_count,
        "decision": decision,
        "state": last,
        "reward": round(reward, 4),
        "done": terminated or truncated,
        "total_profit": round(env.total_profit, 2)
    }


@router.post("/run_full")
def run_full_episode():
    """Roda um episódio completo de 24h e retorna o log completo."""
    try:
        from agent.predict import predict_action
        use_rl = True
    except FileNotFoundError:
        use_rl = False

    env = H2OptimizerEnv()
    obs, _ = env.reset(seed=42)
    clear_operations()

    done = False
    while not done:
        if use_rl:
            from agent.predict import predict_action
            decision = predict_action(obs)
            action_value = decision["action"]
            reasoning = decision["reasoning"]
        else:
            from scripts.generate_baseline import baseline_action
            from data.price import get_spot_price
            hour = (env.current_hour + env.step_count) % 24
            price = get_spot_price(hour)
            action_value = baseline_action(obs, price, env.tank_level)
            reasoning = "Regra simples (modelo não disponível)"

        obs, reward, terminated, truncated, info = env.step([action_value])
        done = terminated or truncated

        if env.episode_log:
            save_operation(env.episode_log[-1], reasoning=reasoning)

    return {
        "agent": "RL (PPO)" if use_rl else "Baseline",
        "total_profit": round(env.total_profit, 2),
        "log": env.episode_log,
        "summary": {
            "total_h2_kg": round(sum(s["h2_produced_kg"] for s in env.episode_log), 2),
            "total_energy_mwh": round(sum(s["energy_to_grid_kw"] for s in env.episode_log) / 1000, 3),
            "n_steps": len(env.episode_log)
        }
    }


@router.get("/status")
def agent_status():
    """Verifica se o modelo está disponível."""
    try:
        from agent.predict import load_model
        load_model()
        return {"model_loaded": True, "episode_active": _env_state["active"]}
    except FileNotFoundError:
        return {"model_loaded": False, "episode_active": False,
                "message": "Execute python backend/agent/train.py para treinar o modelo"}   