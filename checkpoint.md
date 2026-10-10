# Checkpoint - Minerador de Nichos

## Status: Funcional (coleta real testada)

## Estrutura

```
src/
  api/main.py          # FastAPI: auth (Bearer) + rate limit + /rank + /anomalies + /niches
  collectors/
    youtube.py         # YouTube Data API (trending videos)
    anomaly.py         # Detecção de anomalias (viral, crescimento, competição)
    google_trends.py   # Google Trends (placeholder/unofficial)
    ahrefs.py          # Ahrefs v3 (difficulty + search volume)
  processing/score.py  # Scoring: (volume × cpc) / difficulty
scripts/collect.py     # Pipeline: anomalias -> data/niches.csv + data/anomalies.csv
ui/app.py              # Streamlit: 3 abas (Keywords, Anomalias, Nichos)
data/
  niches.csv           # 20 nichos coletados
  anomalies.csv        # 50 anomalias detectadas
  keywords.json        # 10 palavras-chave extraídas
  keywords.csv         # Legado (exemplo)
.github/workflows/ci.yml # lint + pytest + docker build
Dockerfile
.streamlit/config.toml # showEmailPrompt = false
```

## Validado

- 7 testes pytest passando
- flake8 limpo (max-line-length=120)
- API: 401 sem token / 200 com `Bearer dev-token-12345`
- UI Streamlit responde 200 na porta 8501
- Coleta real: 20 nichos, 50 anomalias, 10 keywords

## Como rodar

```powershell
.\venv\Scripts\python -m uvicorn src.api.main:app --port 8000
.\venv\Scripts\python -m streamlit run ui/app.py --server.port 8501
```

## Pendencias

1. Implementar parser real do Google Trends (API não oficial)
2. Agendar coleta (cron / Airflow)
3. Deploy em nuvem (Azure / Railway / Render)
4. Substituir CSV por SQLite/PostgreSQL

## Proximos passos sugeridos

- Agendamento automático da coleta
- Cache/DB (SQLite) em vez de CSV estático
- Upload para produção via GitHub Actions
- Dashboard com gráficos de tendência
