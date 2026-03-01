# ============================================================
# main.py — FastAPI app principal
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.dirname(__file__))

from api.routes_dashboard import router as dashboard_router
from api.routes_agent import router as agent_router
from api.routes_history import router as history_router
from config import API

app = FastAPI(
    title="H2 Verde Optimizer API",
    description="Sistema de otimização de produção de hidrogênio verde via RL",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(agent_router, prefix="/api/agent", tags=["Agente RL"])
app.include_router(history_router, prefix="/api/history", tags=["Histórico"])


@app.get("/")
def root():
    return {"status": "ok", "message": "H2 Verde Optimizer API rodando"}


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API["host"],
        port=API["port"],
        reload=API["reload"]
    )