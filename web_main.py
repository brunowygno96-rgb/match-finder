import os
import sys
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Garantir que o pacote "mvf" (dentro de src/) esteja no PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from mvf.runner_next import run_next
from mvf.multi import run_multi

app = FastAPI(
    title="Match Video Finder API",
    version="1.0.0",
    description=(
        "API em FastAPI para buscar próximos jogos de atletas/times usando o engine "
        "local do Match Video Finder (SofaScore)."
    ),
)

# CORS liberado geral (ajuste se quiser restringir em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Endpoint simples de health check."""
    return {"status": "ok"}


@app.get("/next")
def next_matches(
    team: Optional[str] = Query(
        None,
        description="Nome do time, ex: 'Benfica Futsal'. Opcional se passar team_id ou team_url.",
    ),
    team_id: Optional[int] = Query(
        None,
        description="ID do time no SofaScore. Opcional se passar team ou team_url.",
    ),
    team_url: Optional[str] = Query(
        None,
        description="URL completa do time no SofaScore. Opcional se passar team ou team_id.",
    ),
    next_: int = Query(
        3,
        alias="next",
        ge=1,
        le=20,
        description="Quantidade de próximos jogos a listar (1–20).",
    ),
    tz: str = Query(
        "America/Fortaleza",
        description="Timezone para datas locais (padrão: America/Fortaleza).",
    ),
    debug: bool = Query(
        False,
        description="Se verdadeiro, ativa logs extras internos (se suportado).",
    ),
):
    """Busca próximos jogos de um único time a partir do engine existente (run_next)."""
    result = run_next(
        team=team,
        limit=next_,
        tz=tz,
        team_id=team_id,
        team_url=team_url,
        debug=debug,
    )
    return result


@app.get("/multi")
def multi_matches(
    next_per_team: int = Query(
        2,
        ge=1,
        le=10,
        description="Quantidade de próximos jogos por atleta/time cadastrado em config/athletes.json.",
    ),
    tz: str = Query(
        "America/Fortaleza",
        description="Timezone para datas locais (padrão: America/Fortaleza).",
    ),
):
    """Agenda agregada usando o arquivo config/athletes.json e run_multi."""
    data = run_multi(next_per_team=next_per_team, tz=tz)
    return data
