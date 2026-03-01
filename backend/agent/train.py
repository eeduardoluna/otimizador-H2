# ============================================================
# agent/train.py — Treino do agente SAC com Stable-Baselines3
# SAC (Soft Actor-Critic) é superior ao PPO para ações contínuas
# porque maximiza entropia — naturalmente evita políticas binárias
# ============================================================

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.monitor import Monitor

from simulation.environment import H2OptimizerEnv
from config import SIMULATION

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "sac_h2optimizer")
BEST_MODEL_PATH = os.path.join(MODEL_DIR, "best_model")
LOG_PATH = os.path.join(MODEL_DIR, "logs")


def train(total_timesteps: int = None):
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(LOG_PATH, exist_ok=True)

    if total_timesteps is None:
        total_timesteps = SIMULATION["training_episodes"] * SIMULATION["episode_length"]

    print(f"[train] Iniciando treino SAC com {total_timesteps:,} timesteps")
    print(f"[train] SAC maximiza entropia — ações contínuas e suaves por design")

    # SAC não suporta ambientes vetorizados — usa ambiente único
    env = Monitor(H2OptimizerEnv())
    eval_env = Monitor(H2OptimizerEnv())

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=BEST_MODEL_PATH,
        log_path=LOG_PATH,
        eval_freq=5000,
        n_eval_episodes=10,
        deterministic=True,
        verbose=1
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=MODEL_DIR,
        name_prefix="sac_checkpoint"
    )

    model = SAC(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        buffer_size=100_000,
        learning_starts=1000,
        batch_size=256,
        tau=0.005,
        gamma=0.99,
        ent_coef="auto",     # Ajuste automático de entropia — chave para ações suaves
        target_entropy="auto",
        verbose=1,
        tensorboard_log=LOG_PATH,
        seed=SIMULATION["seed"],
        policy_kwargs=dict(net_arch=[256, 256])
    )

    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback],
        progress_bar=True
    )

    model.save(MODEL_PATH)
    print(f"[train] Modelo salvo em: {MODEL_PATH}")
    print(f"[train] Melhor modelo salvo em: {BEST_MODEL_PATH}")

    return model


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=None)
    args = parser.parse_args()
    model = train(total_timesteps=args.timesteps)
    print("[train] Treino concluído!")