
# Match Video Finder — Próximos Jogos & Agenda (multi) v1.2.6

- Agenda multi com data **DD/MM/AAAA**
- Exportação para **TXT** (UI e CLI)

## Instalar
```powershell
python -m pip install -U pip wheel setuptools
python -m pip install -r requirements.txt
```

## Rodar UI
```powershell
python app.py
```

### Configurar atletas
Edite `config/athletes.json`:
```json
[
  {"name": "Atleta A", "team_id": 306038, "team_label": "Cartagena FS"},
  {"name": "Atleta B", "team_id": 306038, "team_label": "Cartagena FS"}
]
```

## CLI de teste
```powershell
python scripts\agenda_multi.py
```
