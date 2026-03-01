# ============================================================
# simulation/environment.py — Ambiente Gymnasium com física realista
# ============================================================

import numpy as np
import gymnasium as gym
from gymnasium import spaces
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import SOLAR, WIND, ELECTROLYZER, TANK, MARKET, SIMULATION, REWARD
from simulation.solar import irradiance_to_power
from simulation.wind import wind_speed_to_power
from data.price import get_spot_price


def electrolyzer_efficiency(load_fraction: float, degradation: float = 0.0) -> float:
    """
    Curva de eficiência real do eletrolisador PEM.
    Retorna kWh por kg de H2.
    
    - Operação ótima entre 30-70% da carga
    - Eficiência piora progressivamente fora desse range
    - Degradação acumulada por partidas aumenta o consumo
    """
    base = ELECTROLYZER["efficiency_base_kwh_per_kg"]
    
    if load_fraction <= 0:
        return base
    
    # Curva em U: penaliza extremos
    if load_fraction < 0.30:
        # Abaixo de 30% — baixa eficiência por corrente fraca
        penalty = (0.30 - load_fraction) * 25.0
    elif load_fraction > 0.75:
        # Acima de 75% — calor excessivo reduz eficiência
        penalty = (load_fraction - 0.75) * 18.0
    else:
        # Zona ótima: pequena melhoria
        penalty = -2.0 * (1.0 - abs(load_fraction - 0.525) / 0.225)
    
    # Degradação acumulada (cada partida piora 0.05%)
    degradation_penalty = degradation * base * 100
    
    return max(base + penalty + degradation_penalty, base * 0.7)


class H2OptimizerEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self, use_real_weather: bool = False):
        super().__init__()
        self.use_real_weather = use_real_weather
        self.forecast_horizon = SIMULATION["forecast_horizon"]
        self.episode_length = SIMULATION["episode_length"]
        self.timestep_hours = SIMULATION["timestep_hours"]

        self.action_space = spaces.Box(
            low=np.array([0.0], dtype=np.float32),
            high=np.array([1.0], dtype=np.float32),
            dtype=np.float32
        )

        # Estado: 5 variáveis atuais + 3 previsões x 6h + carga atual do eletrolisador
        obs_size = 6 + self.forecast_horizon * 3
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(obs_size,), dtype=np.float32
        )

        self.max_solar = SOLAR["capacity_kw"]
        self.max_wind = WIND["capacity_kw"]
        self.max_price = MARKET["energy_price_max"]
        self.tank_capacity = TANK["capacity_kg"]
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0
        self.current_hour = 0 if seed is not None else np.random.randint(0, 24)
        self.tank_level = TANK["initial_level"]
        self.electrolyzer_on = False
        self.current_load = 0.0          # carga atual do eletrolisador (0-1)
        self.total_profit = 0.0
        self.total_starts = 0
        self.degradation = 0.0
        self.episode_log = []
        self._generate_weather_episode()
        return self._get_observation(), {}

    def _generate_weather_episode(self):
        total_steps = self.episode_length + self.forecast_horizon
        hours = [(self.current_hour + i) % 24 for i in range(total_steps)]
        self.irradiance_profile = []
        self.wind_profile = []
        self.temp_profile = []
        for h in hours:
            if 6 <= h <= 18:
                peak = 900 * np.sin(np.pi * (h - 6) / 12)
                irr = max(0, peak + np.random.normal(0, 70))
            else:
                irr = 0.0
            base_wind = 5.5 + 3.5 * np.sin(np.pi * (h - 14) / 12)
            wind = max(0, base_wind + np.random.normal(0, 1.2))
            temp = 28.0 + 4.0 * np.sin(np.pi * (h - 6) / 12) + np.random.normal(0, 0.8)
            self.irradiance_profile.append(irr)
            self.wind_profile.append(wind)
            self.temp_profile.append(temp)

    def _get_current_generation(self, step_offset=0):
        idx = self.step_count + step_offset
        solar_kw = irradiance_to_power(self.irradiance_profile[idx], self.temp_profile[idx])
        wind_kw = wind_speed_to_power(self.wind_profile[idx])
        return solar_kw, wind_kw

    def _get_h2_price(self):
        """Preço dinâmico do H2 baseado no nível do tanque."""
        base = MARKET["h2_price_per_kg"]
        if self.tank_level < 0.15:
            return base + MARKET["h2_price_bonus_empty_tank"]
        elif self.tank_level > 0.80:
            return base - MARKET["h2_price_discount_full_tank"]
        return base

    def _get_observation(self):
        solar_kw, wind_kw = self._get_current_generation()
        hour = (self.current_hour + self.step_count) % 24
        price = get_spot_price(hour)
        solar_forecast, wind_forecast, price_forecast = [], [], []
        for i in range(1, self.forecast_horizon + 1):
            s, w = self._get_current_generation(step_offset=i)
            h = (hour + i) % 24
            p = get_spot_price(h, noise_std=20 + i * 8)
            solar_forecast.append(s / self.max_solar)
            wind_forecast.append(w / self.max_wind)
            price_forecast.append(p / self.max_price)
        obs = np.array([
            solar_kw / self.max_solar,
            wind_kw / self.max_wind,
            price / self.max_price,
            self.tank_level,
            hour / 23.0,
            self.current_load,           # carga atual do eletrolisador
            *solar_forecast,
            *wind_forecast,
            *price_forecast
        ], dtype=np.float32)
        return obs

    def step(self, action):
        action = float(np.clip(action[0], 0.0, 1.0))
        hour = (self.current_hour + self.step_count) % 24
        solar_kw, wind_kw = self._get_current_generation()
        total_gen_kw = solar_kw + wind_kw
        price_mwh = get_spot_price(hour)

        # ── Restrição de rampa ──────────────────────────────────────────────
        # Eletrolisador não pode mudar mais de 35% de carga por hora
        max_ramp = ELECTROLYZER["ramp_rate_per_step"]
        target_load = action
        actual_load = float(np.clip(
            target_load,
            self.current_load - max_ramp,
            self.current_load + max_ramp
        ))
        ramp_violation = abs(target_load - actual_load)

        # ── Potência e produção de H2 ───────────────────────────────────────
        energy_to_electrolysis_kw = min(
            total_gen_kw * actual_load,
            ELECTROLYZER["max_power_kw"]
        )
        energy_to_grid_kw = total_gen_kw - energy_to_electrolysis_kw

        if energy_to_electrolysis_kw < ELECTROLYZER["min_power_kw"]:
            energy_to_electrolysis_kw = 0.0
            energy_to_grid_kw = total_gen_kw
            electrolyzer_running = False
            actual_load = 0.0
        else:
            electrolyzer_running = True

        # Carga normalizada para curva de eficiência
        load_fraction = energy_to_electrolysis_kw / ELECTROLYZER["max_power_kw"]
        eff_kwh_per_kg = electrolyzer_efficiency(load_fraction, self.degradation)

        h2_produced_kg = (
            energy_to_electrolysis_kw * self.timestep_hours / eff_kwh_per_kg
            if electrolyzer_running else 0.0
        )

        # ── Tanque ──────────────────────────────────────────────────────────
        new_tank = self.tank_level + h2_produced_kg / self.tank_capacity

        # ── Receitas ────────────────────────────────────────────────────────
        energy_sold_mwh = energy_to_grid_kw * self.timestep_hours / 1000.0
        revenue_energy = energy_sold_mwh * price_mwh
        h2_price = self._get_h2_price()
        revenue_h2 = h2_produced_kg * h2_price

        # ── Custos ──────────────────────────────────────────────────────────
        is_new_start = electrolyzer_running and not self.electrolyzer_on
        startup_cost = ELECTROLYZER["startup_cost"] if is_new_start else 0.0
        operating_cost = ELECTROLYZER["operating_cost_per_hour"] if electrolyzer_running else 0.0
        storage_cost = self.tank_level * self.tank_capacity * TANK["storage_cost_per_kg_hour"]
        total_cost = startup_cost + operating_cost + storage_cost
        profit = revenue_energy + revenue_h2 - total_cost

        # ── Penalidades ─────────────────────────────────────────────────────
        penalty = 0.0

        # Overflow do tanque
        if new_tank > TANK["max_level"]:
            penalty += REWARD["tank_overflow_penalty"] * (new_tank - TANK["max_level"]) * 100
            new_tank = TANK["max_level"]

        # Tanque vazio
        if new_tank < TANK["min_level"]:
            penalty += REWARD["tank_empty_penalty"] * (TANK["min_level"] - new_tank) * 100
            new_tank = max(new_tank, 0.0)

        # Desperdício: geração alta, preço baixo, tanque não cheio
        if total_gen_kw > 100 and price_mwh < 200 and actual_load < 0.2 and self.tank_level < 0.85:
            penalty += REWARD["waste_penalty"] * total_gen_kw * 0.015

        # Violação de rampa
        penalty += REWARD["ramp_violation_penalty"] * ramp_violation

        reward = REWARD["profit_weight"] * profit - penalty

        # ── Atualiza estado ─────────────────────────────────────────────────
        if is_new_start:
            self.total_starts += 1
            self.degradation += ELECTROLYZER["degradation_per_start"]

        self.tank_level = float(np.clip(new_tank, 0.0, 1.0))
        self.electrolyzer_on = electrolyzer_running
        self.current_load = actual_load
        self.total_profit += profit
        self.step_count += 1

        self.episode_log.append({
            "hour": hour,
            "solar_kw": round(solar_kw, 2),
            "wind_kw": round(wind_kw, 2),
            "total_gen_kw": round(total_gen_kw, 2),
            "action": round(action, 3),
            "actual_load": round(actual_load, 3),
            "energy_to_electrolysis_kw": round(energy_to_electrolysis_kw, 2),
            "energy_to_grid_kw": round(energy_to_grid_kw, 2),
            "h2_produced_kg": round(h2_produced_kg, 3),
            "efficiency_kwh_per_kg": round(eff_kwh_per_kg, 2),
            "tank_level": round(self.tank_level, 3),
            "price_mwh": round(price_mwh, 2),
            "h2_price": round(h2_price, 2),
            "revenue_energy": round(revenue_energy, 2),
            "revenue_h2": round(revenue_h2, 2),
            "total_cost": round(total_cost, 2),
            "profit": round(profit, 2),
            "reward": round(reward, 4),
            "electrolyzer_on": electrolyzer_running,
            "load_fraction": round(load_fraction, 3),
        })

        terminated = self.step_count >= self.episode_length
        obs = self._get_observation() if not terminated else np.zeros(
            self.observation_space.shape, dtype=np.float32)
        return obs, reward, terminated, False, {"total_profit": self.total_profit}

    def render(self, mode="human"):
        if self.episode_log:
            last = self.episode_log[-1]
            print(
                f"H:{last['hour']:02d}h | Gen:{last['total_gen_kw']:>6.1f}kW | "
                f"Ação:{last['action']:.2f}→{last['actual_load']:.2f} | "
                f"H2:{last['h2_produced_kg']:>5.2f}kg | "
                f"Ef:{last['efficiency_kwh_per_kg']:.1f}kWh/kg | "
                f"Tanque:{last['tank_level']*100:>5.1f}% | "
                f"Preço:R${last['price_mwh']:>6.0f} | Lucro:R${last['profit']:>7.2f}"
            )