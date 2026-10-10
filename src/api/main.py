from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import time
import os
from src.db import (
    init_db, get_niches, get_anomalies, get_keywords,
    search_niches, search_anomalies, search_keywords,
    get_niches_with_url, get_anomalies_with_url,
)

app = FastAPI(title="Minerador de Nichos API", version="2.0")

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.getenv("API_TOKEN", "dev-token-12345")
security = HTTPBearer(auto_error=False)

rate_limit_store = {}

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 30


async def rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
    ]
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limit_store[client_ip].append(now)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    await rate_limit(request)
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minerador de Nichos - YouTube</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #fff; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%); padding: 20px 30px; display: flex; align-items: center; justify-content: space-between; }
        .header h1 { font-size: 24px; font-weight: 700; }
        .header .status { display: flex; align-items: center; gap: 8px; font-size: 14px; }
        .status-dot { width: 8px; height: 8px; background: #00ff00; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .search-bar { display: flex; gap: 10px; margin-bottom: 20px; }
        .search-input { flex: 1; padding: 12px 16px; border-radius: 8px; border: 1px solid #333; background: #1a1a1a; color: #fff; font-size: 14px; outline: none; }
        .search-input:focus { border-color: #ff0000; }
        .search-input::placeholder { color: #666; }
        .channel-link { color: #ff0000; text-decoration: none; }
        .channel-link:hover { text-decoration: underline; }
        .tabs { display: flex; gap: 4px; margin-bottom: 20px; border-bottom: 1px solid #333; }
        .tab { padding: 12px 24px; cursor: pointer; border: none; background: transparent; color: #aaa; font-size: 14px; font-weight: 500; border-bottom: 2px solid transparent; transition: all 0.2s; }
        .tab:hover { color: #fff; }
        .tab.active { color: #ff0000; border-bottom-color: #ff0000; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .card { background: #1a1a1a; border-radius: 12px; padding: 20px; margin-bottom: 16px; border: 1px solid #333; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .card-title { font-size: 18px; font-weight: 600; }
        .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .btn-primary { background: #ff0000; color: #fff; }
        .btn-primary:hover { background: #cc0000; }
        .btn-secondary { background: #333; color: #fff; }
        .btn-secondary:hover { background: #444; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
        .stat-card { background: #1a1a1a; border-radius: 12px; padding: 20px; border: 1px solid #333; text-align: center; }
        .stat-value { font-size: 32px; font-weight: 700; color: #ff0000; }
        .stat-label { font-size: 12px; color: #aaa; margin-top: 4px; text-transform: uppercase; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #333; }
        th { color: #aaa; font-weight: 500; font-size: 12px; text-transform: uppercase; }
        td { font-size: 14px; }
        tr:hover { background: #252525; }
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .badge-low { background: #00ff0022; color: #00ff00; }
        .badge-medium { background: #ffaa0022; color: #ffaa00; }
        .badge-high { background: #ff000022; color: #ff0000; }
        .score { font-weight: 700; color: #ff0000; }
        .loading { text-align: center; padding: 40px; color: #aaa; }
        .error { background: #ff000022; color: #ff0000; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
        .empty { text-align: center; padding: 40px; color: #666; }
        .refresh-time { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Minerador de Nichos</h1>
        <div class="status">
            <div class="status-dot"></div>
            <span>API Online</span>
        </div>
    </div>

    <div class="container">
        <div class="search-bar">
            <input type="text" class="search-input" id="search-input" placeholder="Buscar por termo, nicho ou canal..." onkeyup="handleSearch(event)">
            <button class="btn btn-primary" onclick="performSearch()">Buscar</button>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="stat-niches">-</div>
                <div class="stat-label">Nichos</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-anomalies">-</div>
                <div class="stat-label">Anomalias</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-keywords">-</div>
                <div class="stat-label">Keywords</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('niches')">Nichos</button>
            <button class="tab" onclick="switchTab('anomalies')">Anomalias</button>
            <button class="tab" onclick="switchTab('keywords')">Keywords</button>
        </div>

        <div id="tab-niches" class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Nichos Identificados</div>
                    <div>
                        <button class="btn btn-secondary" onclick="exportCSV('niches')">Exportar CSV</button>
                        <button class="btn btn-primary" onclick="loadNiches()">Atualizar</button>
                    </div>
                </div>
                <div id="niches-content"><div class="loading">Carregando...</div></div>
            </div>
        </div>

        <div id="tab-anomalies" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Anomalias Detectadas</div>
                    <div>
                        <button class="btn btn-secondary" onclick="exportCSV('anomalies')">Exportar CSV</button>
                        <button class="btn btn-primary" onclick="loadAnomalies()">Atualizar</button>
                    </div>
                </div>
                <div id="anomalies-content"><div class="loading">Carregando...</div></div>
            </div>
        </div>

        <div id="tab-keywords" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Palavras-chave Extraídas</div>
                    <div>
                        <button class="btn btn-secondary" onclick="exportCSV('keywords')">Exportar CSV</button>
                        <button class="btn btn-primary" onclick="loadKeywords()">Atualizar</button>
                    </div>
                </div>
                <div id="keywords-content"><div class="loading">Carregando...</div></div>
            </div>
        </div>
    </div>

    <script>
        const API_TOKEN = 'dev-token-12345';
        const API_URL = window.location.origin;
        let currentTab = 'niches';

        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
            currentTab = tab;
            loadCurrentTab();
        }

        function loadCurrentTab() {
            if (currentTab === 'niches') loadNiches();
            if (currentTab === 'anomalies') loadAnomalies();
            if (currentTab === 'keywords') loadKeywords();
        }

        async function fetchAPI(endpoint) {
            const q = document.getElementById('search-input').value.trim();
            const separator = endpoint.includes('?') ? '&' : '?';
            const url = q ? `${API_URL}/${endpoint}${separator}q=${encodeURIComponent(q)}` : `${API_URL}/${endpoint}`;
            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${API_TOKEN}` }
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        }

        function handleSearch(event) {
            if (event.key === 'Enter') performSearch();
        }

        function performSearch() {
            loadCurrentTab();
        }

        async function loadNiches() {
            const el = document.getElementById('niches-content');
            el.innerHTML = '<div class="loading">Carregando...</div>';
            try {
                const data = await fetchAPI('niches');
                document.getElementById('stat-niches').textContent = data.length;
                if (!data.length) { el.innerHTML = '<div class="empty">Nenhum nicho encontrado</div>'; return; }
                let html = '<table><thead><tr><th>Nicho</th><th>Score</th><th>Views</th><th>Crescimento</th><th>Concorrência</th><th>Canal</th></tr></thead><tbody>';
                data.forEach(n => {
                    html += `<tr>
                        <td>${n.niche}</td>
                        <td class="score">${n.anomaly_score}</td>
                        <td>${Number(n.avg_views).toLocaleString()}</td>
                        <td>${Number(n.growth_rate).toLocaleString()}/dia</td>
                        <td><span class="badge badge-${n.competition_level}">${n.competition_level}</span></td>
                        <td><a href="${n.channel_url || '#'}" target="_blank" class="channel-link">${n.channel}</a></td>
                    </tr>`;
                });
                html += '</tbody></table>';
                el.innerHTML = html;
            } catch (e) {
                el.innerHTML = `<div class="error">Erro: ${e.message}</div>`;
            }
        }

        async function loadAnomalies() {
            const el = document.getElementById('anomalies-content');
            el.innerHTML = '<div class="loading">Carregando...</div>';
            try {
                const data = await fetchAPI('anomalies');
                document.getElementById('stat-anomalies').textContent = data.length;
                if (!data.length) { el.innerHTML = '<div class="empty">Nenhuma anomalia encontrada</div>'; return; }
                let html = '<table><thead><tr><th>Vídeo</th><th>Canal</th><th>Views</th><th>Score</th><th>Viral</th><th>Crescimento</th><th>Concorrência</th></tr></thead><tbody>';
                data.forEach(a => {
                    html += `<tr>
                        <td>${a.title}</td>
                        <td><a href="${a.channel_url}" target="_blank" class="channel-link">${a.channel_title}</a></td>
                        <td>${Number(a.views).toLocaleString()}</td>
                        <td class="score">${a.anomaly_score}</td>
                        <td>${a.is_viral ? 'SIM' : 'nao'}</td>
                        <td>${a.is_fast_growth ? 'SIM' : 'nao'}</td>
                        <td>${a.is_low_competition ? 'SIM' : 'nao'}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                el.innerHTML = html;
            } catch (e) {
                el.innerHTML = `<div class="error">Erro: ${e.message}</div>`;
            }
        }

        async function loadKeywords() {
            const el = document.getElementById('keywords-content');
            el.innerHTML = '<div class="loading">Carregando...</div>';
            try {
                const data = await fetchAPI('keywords');
                document.getElementById('stat-keywords').textContent = data.length;
                if (!data.length) { el.innerHTML = '<div class="empty">Nenhuma keyword encontrada</div>'; return; }
                let html = '<table><thead><tr><th>Keyword</th><th>Frequência</th><th>Peso</th></tr></thead><tbody>';
                data.forEach(k => {
                    html += `<tr>
                        <td>${k.keyword}</td>
                        <td>${k.frequency}</td>
                        <td>${(k.weight * 100).toFixed(1)}%</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                el.innerHTML = html;
            } catch (e) {
                el.innerHTML = `<div class="error">Erro: ${e.message}</div>`;
            }
        }

        function exportCSV(type) {
            const endpoint = type === 'niches' ? 'niches' : type === 'anomalies' ? 'anomalies' : 'keywords';
            fetchAPI(endpoint).then(data => {
                if (!data.length) return;
                const headers = Object.keys(data[0]);
                const csv = [headers.join(','), ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))].join('\\n');
                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${type}.csv`;
                a.click();
            });
        }

        loadNiches();
    </script>
</body>
</html>
    """


@app.get("/niches")
async def niches(q: str = Query(default=""), token: str = Depends(verify_token)):
    if q:
        return JSONResponse(content=search_niches(q))
    return JSONResponse(content=get_niches_with_url())


@app.get("/anomalies")
async def anomalies(q: str = Query(default=""), token: str = Depends(verify_token)):
    if q:
        return JSONResponse(content=search_anomalies(q))
    return JSONResponse(content=get_anomalies_with_url())


@app.get("/keywords")
async def keywords(q: str = Query(default=""), token: str = Depends(verify_token)):
    if q:
        return JSONResponse(content=search_keywords(q))
    return JSONResponse(content=get_keywords())
