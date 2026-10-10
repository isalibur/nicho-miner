from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import time
import os
from src.db import (
    init_db,
    get_keywords,
    search_niches,
    search_anomalies,
    search_keywords,
    get_niches_with_url,
    get_anomalies_with_url,
)
from src.collectors.youtube import search_videos
from src.collectors.anomaly import find_deep_niches

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
        .deep-toggle { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; cursor: pointer; }
        .deep-toggle input { accent-color: #ff0000; }
        .deep-toggle label { color: #aaa; font-size: 13px; cursor: pointer; }
        .deep-toggle.active { border-color: #ff0000; background: #ff000022; }
        .deep-toggle.active label { color: #ff0000; }
        .channel-link { color: #ff0000; text-decoration: none; }
        .channel-link:hover { text-decoration: underline; }
        .video-link { color: #4da6ff; text-decoration: none; }
        .video-link:hover { text-decoration: underline; }
        .source-badge { padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; margin-left: 8px; }
        .source-local { background: #00ff0022; color: #00ff00; }
        .source-youtube { background: #4da6ff22; color: #4da6ff; }
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
            <div class="deep-toggle" id="deep-toggle" onclick="toggleDeepSearch()">
                <input type="checkbox" id="deep-search-checkbox">
                <label for="deep-search-checkbox">Busca Profunda</label>
            </div>
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

        function toggleDeepSearch() {
            document.getElementById('deep-toggle').classList.toggle('active');
        }

        function isDeepSearch() {
            return document.getElementById('deep-search-checkbox').checked;
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

        async function fetchDeepSearch() {
            const q = document.getElementById('search-input').value.trim();
            const separator = '?';
            const url = q ? `${API_URL}/deep-search${separator}q=${encodeURIComponent(q)}` : `${API_URL}/deep-search`;
            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${API_TOKEN}` }
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        }

        function handleSearch(event) {
            if (event.key === 'Enter') performSearch();
        }

        async function performSearch() {
            const q = document.getElementById('search-input').value.trim();
            if (!q) { loadCurrentTab(); return; }

            if (isDeepSearch()) {
                const el = document.getElementById(currentTab + '-content');
                el.innerHTML = '<div class="loading">Busca profunda em andamento...</div>';
                try {
                    const deepData = await fetchDeepSearch();
                    const items = currentTab === 'niches' ? deepData.niches : currentTab === 'anomalies' ? deepData.anomalies : deepData.keywords;
                    if (items && items.length > 0) {
                        renderCurrentTab(items);
                    } else {
                        el.innerHTML = '<div class="empty">Nenhum resultado encontrado na busca profunda</div>';
                    }
                } catch (e) {
                    el.innerHTML = `<div class="error">Erro: ${e.message}</div>`;
                }
                return;
            }

            const localData = await fetchAPI(currentTab);
            if (localData.length > 0) {
                renderCurrentTab(localData);
                return;
            }

            const el = document.getElementById(currentTab + '-content');
            el.innerHTML = '<div class="loading">Buscando no YouTube...</div>';
            try {
                const ytData = await fetch(`${API_URL}/search-youtube?q=${encodeURIComponent(q)}`, {
                    headers: { 'Authorization': `Bearer ${API_TOKEN}` }
                }).then(r => r.json());

                if (!ytData.length) {
                    el.innerHTML = '<div class="empty">Nenhum resultado encontrado</div>';
                    return;
                }

                let html = '<table><thead><tr><th>Vídeo</th><th>Canal</th><th>Publicado</th></tr></thead><tbody>';
                ytData.forEach(v => {
                    html += `<tr>
                        <td><a href="${v.video_url}" target="_blank" class="video-link">${v.title}</a><span class="source-badge source-youtube">YouTube</span></td>
                        <td><a href="${v.channel_url}" target="_blank" class="channel-link">${v.channel_title}</a></td>
                        <td>${new Date(v.published_at).toLocaleDateString()}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                el.innerHTML = html;
            } catch (e) {
                el.innerHTML = `<div class="error">Erro: ${e.message}</div>`;
            }
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

        async function performSearch() {
            const q = document.getElementById('search-input').value.trim();
            if (!q) { loadCurrentTab(); return; }

            const localData = await fetchAPI(currentTab);
            if (localData.length > 0) {
                renderCurrentTab(localData);
                return;
            }

            const el = document.getElementById(currentTab + '-content');
            el.innerHTML = '<div class="loading">Buscando no YouTube...</div>';
            try {
                const ytData = await fetch(`${API_URL}/search-youtube?q=${encodeURIComponent(q)}`, {
                    headers: { 'Authorization': `Bearer ${API_TOKEN}` }
                }).then(r => r.json());

                if (!ytData.length) {
                    el.innerHTML = '<div class="empty">Nenhum resultado encontrado</div>';
                    return;
                }

                let html = '<table><thead><tr><th>Vídeo</th><th>Canal</th><th>Publicado</th></tr></thead><tbody>';
                ytData.forEach(v => {
                    html += `<tr>
                        <td><a href="${v.video_url}" target="_blank" class="video-link">${v.title}</a><span class="source-badge source-youtube">YouTube</span></td>
                        <td><a href="${v.channel_url}" target="_blank" class="channel-link">${v.channel_title}</a></td>
                        <td>${new Date(v.published_at).toLocaleDateString()}</td>
                    </tr>`;
                });
                html += '</tbody></table>';
                el.innerHTML = html;
            } catch (e) {
                el.innerHTML = `<div class="error">Erro: ${e.message}</div>`;
            }
        }

        function renderCurrentTab(data) {
            if (currentTab === 'niches') {
                document.getElementById('stat-niches').textContent = data.length;
                const el = document.getElementById('niches-content');
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
            } else if (currentTab === 'anomalies') {
                document.getElementById('stat-anomalies').textContent = data.length;
                const el = document.getElementById('anomalies-content');
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
            } else {
                document.getElementById('stat-keywords').textContent = data.length;
                const el = document.getElementById('keywords-content');
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


@app.get("/search-youtube")
async def search_youtube(q: str = Query(...), token: str = Depends(verify_token)):
    result = await search_videos(q)
    items = result.get("items", [])
    videos = []
    for item in items:
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")
        channel_id = snippet.get("channelId", "")
        videos.append(
            {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "channel_id": channel_id,
                "channel_title": snippet.get("channelTitle", ""),
                "channel_url": f"https://youtube.com/channel/{channel_id}",
                "video_url": f"https://youtube.com/watch?v={video_id}",
                "published_at": snippet.get("publishedAt", ""),
            }
        )
    return JSONResponse(content=videos)


@app.get("/deep-search")
async def deep_search(
    q: str = Query(default=""),
    max_results: int = Query(default=20, ge=1, le=100),
    token: str = Depends(verify_token),
):
    result = await find_deep_niches(query=q, max_results=max_results)
    channels = result.get("channels", [])
    for ch in channels:
        ch["channel_url"] = f"https://youtube.com/channel/{ch['channel_id']}"
    return JSONResponse(
        content={
            "niches": result["niches"],
            "anomalies": result["anomalies"],
            "keywords": result["keywords"],
            "channels": channels,
        }
    )
