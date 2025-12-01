import os
import sys
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Garantir que o pacote "mvf" (dentro de src/) esteja no PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from mvf.runner_next import run_next
from mvf.multi import run_multi

app = FastAPI(
    title="Match Finder API",
    version="1.0.0",
    description="API para buscar próximos jogos (SofaScore) usando o Match Finder.",
)

# CORS liberado geral (se quiser, depois restringe)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------- INTERFACE WEB SIMPLES -----------

@app.get("/", response_class=HTMLResponse)
def home():
    """Página inicial com formulários para /next e /multi."""
    return """
    <!doctype html>
    <html lang="pt-BR">
    <head>
      <meta charset="utf-8">
      <title>Match Finder</title>
      <style>
        body {
          background:#0b0b10;
          color:#f5f5f5;
          font-family:system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          padding:24px;
        }
        h1 { margin-bottom: 4px; }
        h2 { margin-top: 32px; }
        label { display:block; margin-top:8px; font-size:14px; }
        input, select {
          width:100%;
          padding:6px 8px;
          margin-top:4px;
          border-radius:4px;
          border:1px solid #333;
          background:#181824;
          color:#f5f5f5;
        }
        button {
          margin-top:12px;
          padding:8px 14px;
          border-radius:4px;
          border:none;
          background:#6366f1;
          color:white;
          cursor:pointer;
        }
        button:hover { background:#4f46e5; }
        .card {
          background:#111321;
          padding:16px;
          border-radius:8px;
          max-width:480px;
          margin-bottom:24px;
        }
        pre {
          background:#05060d;
          padding:12px;
          border-radius:6px;
          overflow:auto;
        }
        .cols {
          display:flex;
          flex-wrap:wrap;
          gap:24px;
        }
        @media (max-width: 768px) {
          .card { max-width: 100%; }
        }
      </style>
    </head>
    <body>
      <h1>Match Finder</h1>
      <p>Backend rodando no Render. Use os formulários abaixo para buscar jogos.</p>
      <p><small>Dica: a interface técnica da API está em <code>/docs</code>.</small></p>

      <div class="cols">
        <div class="card">
          <h2>Buscar próximos jogos de um time (/next)</h2>
          <form id="nextForm">
            <label>
              Time (nome)
              <input type="text" id="team" placeholder="Ex: SC Farense">
            </label>
            <label>
              ID do time (SofaScore)
              <input type="number" id="team_id" placeholder="Opcional se usar nome ou URL">
            </label>
            <label>
              URL do time (SofaScore)
              <input type="text" id="team_url" placeholder="https://www.sofascore.com/team/...">
            </label>
            <label>
              Quantidade de próximos jogos
              <input type="number" id="next" value="3" min="1" max="20">
            </label>
            <label>
              Timezone
              <input type="text" id="tz" value="America/Fortaleza">
            </label>
            <button type="submit">Buscar /next</button>
          </form>
          <h3>Resultado</h3>
          <pre id="nextResult">{}</pre>
        </div>

        <div class="card">
          <h2>Agenda multi atletas (/multi)</h2>
          <form id="multiForm">
            <label>
              Próximos jogos por atleta
              <input type="number" id="next_per_team" value="2" min="1" max="10">
            </label>
            <label>
              Timezone
              <input type="text" id="tz_multi" value="America/Fortaleza">
            </label>
            <button type="submit">Buscar /multi</button>
          </form>
          <h3>Resultado</h3>
          <pre id="multiResult">{}</pre>
        </div>
      </div>

      <script>
     const baseUrl = "";

     async function callApi(url, outputElementId) {
       const out = document.getElementById(outputElementId);
       out.textContent = "Carregando...";

       try {
         const res = await fetch(url);
         const text = await res.text();   // lê texto bruto

         if (!res.ok) {
           // Mostra o erro HTTP em vez de tentar fazer JSON.parse
           out.textContent = `Erro HTTP ${res.status}: ${text}`;
           return;
         }

         let data;
         try {
           data = JSON.parse(text);
         } catch (e) {
           out.textContent =
             "Erro ao ler JSON de resposta: " +
             e +
             "\n\nTexto bruto recebido:\n" +
             text;
           return;
         }

         out.textContent = JSON.stringify(data, null, 2);
       } catch (err) {
         out.textContent = "Erro ao chamar API: " + err;
       }
     }

     document.getElementById("nextForm").addEventListener("submit", async (e) => {
       e.preventDefault();
       const team = document.getElementById("team").value.trim();
       const team_id = document.getElementById("team_id").value.trim();
       const team_url = document.getElementById("team_url").value.trim();
       const nextVal = document.getElementById("next").value.trim() || "3";
       const tz = document.getElementById("tz").value.trim() || "America/Fortaleza";

       const params = new URLSearchParams();
       if (team) params.append("team", team);
       if (team_id) params.append("team_id", team_id);
       if (team_url) params.append("team_url", team_url);
       params.append("next", nextVal);
       params.append("tz", tz);

       const url = baseUrl + "/next?" + params.toString();
       callApi(url, "nextResult");
     });

     document.getElementById("multiForm").addEventListener("submit", async (e) => {
       e.preventDefault();
       const nextPerTeam =
         document.getElementById("next_per_team").value.trim() || "2";
       const tzMulti =
         document.getElementById("tz_multi").value.trim() || "America/Fortaleza";

       const params = new URLSearchParams();
       params.append("next_per_team", nextPerTeam);
       params.append("tz", tzMulti);

       const url = baseUrl + "/multi?" + params.toString();
       callApi(url, "multiResult");
     });
</script>

    </body>
    </html>
    """


# ----------- ENDPOINTS DA API -----------

@app.get("/health")
def health():
    """Endpoint simples de health check."""
    return {"status": "ok"}


@app.get("/next")
def next_matches(
    team: Optional[str] = Query(
        None,
        description="Nome do time, ex: 'SC Farense'. Opcional se passar team_id ou team_url.",
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
