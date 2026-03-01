# ============================================================
# data/database.py — Conexão e modelos SQLite
# ============================================================

import sqlite3
import json
import os
from datetime import datetime
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import DATABASE

DB_PATH = DATABASE["path"]


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            hour INTEGER,
            solar_kw REAL,
            wind_kw REAL,
            total_gen_kw REAL,
            action REAL,
            energy_to_electrolysis_kw REAL,
            energy_to_grid_kw REAL,
            h2_produced_kg REAL,
            tank_level REAL,
            price_mwh REAL,
            revenue_energy REAL,
            revenue_h2 REAL,
            total_cost REAL,
            profit REAL,
            electrolyzer_on INTEGER,
            reasoning TEXT
        );

        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            agent_type TEXT,
            total_profit REAL,
            total_h2_kg REAL,
            total_energy_mwh REAL,
            n_steps INTEGER
        );
    """)
    conn.commit()
    conn.close()


def save_operation(data: dict, reasoning: str = ""):
    """Salva uma decisão de operação no banco."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO operations (
            timestamp, hour, solar_kw, wind_kw, total_gen_kw,
            action, energy_to_electrolysis_kw, energy_to_grid_kw,
            h2_produced_kg, tank_level, price_mwh,
            revenue_energy, revenue_h2, total_cost, profit,
            electrolyzer_on, reasoning
        ) VALUES (
            :timestamp, :hour, :solar_kw, :wind_kw, :total_gen_kw,
            :action, :energy_to_electrolysis_kw, :energy_to_grid_kw,
            :h2_produced_kg, :tank_level, :price_mwh,
            :revenue_energy, :revenue_h2, :total_cost, :profit,
            :electrolyzer_on, :reasoning
        )
    """, {**data, "timestamp": datetime.utcnow().isoformat(), "reasoning": reasoning})
    conn.commit()
    conn.close()


def get_recent_operations(limit: int = 24) -> list[dict]:
    """Retorna as N operações mais recentes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM operations ORDER BY id DESC LIMIT ?", (limit,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))


def get_cumulative_profit() -> float:
    """Retorna o lucro acumulado total."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(profit), 0) FROM operations")
    result = cursor.fetchone()[0]
    conn.close()
    return round(float(result), 2)


def clear_operations():
    """Limpa o histórico de operações (útil para nova simulação)."""
    conn = get_connection()
    conn.execute("DELETE FROM operations")
    conn.commit()
    conn.close()


# Inicializa o banco ao importar
init_db()