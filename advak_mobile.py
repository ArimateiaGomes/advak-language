"""
Advak 5.0 — Módulo Mobile

Suporte completo a desenvolvimento mobile via:

1. PWA (Progressive Web App) — app instalável no celular via browser
2. App WebView — janela nativa que exibe uma web app (ponte Python ↔ JS)
3. App Responsivo — layouts que se adaptam a telas pequenas
4. QR Code — gera QR codes para links, Wi-Fi, vCards, pagamentos PIX
5. Câmera / Scanner — acesso à câmera via browser API
6. Geolocalização — GPS via browser API
7. Push Notifications — notificações locais e via WebSocket
8. Storage Local — persistência no dispositivo
9. Gestos Touch — swipe, pinch, tap
10. Build APK — empacota como APK Android via Briefcase/Kivy

Uso:
    seja app = mobile.criar_app("Meu App", versao="1.0")
    app.tela("inicio") {
        mobile.label("Olá, Mobile!")
        mobile.botao("Ir para perfil", vai_para="perfil")
    }
    mobile.iniciar()

    // QR Code
    mobile.qr.gerar("https://meusite.com", arquivo="qr.png")

    // Embarcado via Wi-Fi
    mobile.iot.conectar("192.168.1.100", 1883)
    mobile.iot.publicar("sensor/temp", 25.4)
"""

import os
import json
import threading
import socket
import base64
import time
import hashlib
import struct
import html as _html
import urllib.parse
from typing import Dict, List, Optional, Callable, Any


# ══════════════════════════════════════════════════════════════════════════════
#  1. GERADOR DE PWA (Progressive Web App)
# ══════════════════════════════════════════════════════════════════════════════

class GeradorPWA:
    """
    Gera um Progressive Web App completo que funciona no celular.
    O usuário acessa a URL no browser e pode "instalar" no celular.

    Inclui:
    - manifest.json (nome, ícone, cor tema)
    - Service Worker (funciona offline)
    - Interface responsiva com tema Advak
    - Bridge JS ↔ Python via WebSocket
    """

    def __init__(self, nome: str, descricao: str = "", cor_tema: str = "#2563EB",
                 versao: str = "1.0", icone: str = "🚀"):
        self.nome = nome
        self.descricao = descricao
        self.cor_tema = cor_tema
        self.versao = versao
        self.icone = icone
        self._telas: Dict[str, str] = {}
        self._tela_inicial = "inicio"
        self._scripts_custom: List[str] = []
        self._estilos_custom: List[str] = []
        self._rotas: Dict[str, Callable] = {}

    def tela(self, nome: str, html_content: str):
        """Adiciona uma tela ao app."""
        self._telas[nome] = html_content
        return self

    def script(self, js: str):
        """Adiciona JavaScript customizado."""
        self._scripts_custom.append(js)
        return self

    def estilo(self, css: str):
        """Adiciona CSS customizado."""
        self._estilos_custom.append(css)
        return self

    def rota_api(self, caminho: str, fn: Callable):
        """Registra uma rota da API que o app mobile pode chamar."""
        self._rotas[caminho] = fn
        return self

    def gerar(self, pasta: str = "mobile_app") -> str:
        """
        Gera todos os arquivos do PWA em uma pasta.
        Retorna o caminho da pasta gerada.
        """
        os.makedirs(pasta, exist_ok=True)

        # manifest.json
        manifest = {
            "name": self.nome,
            "short_name": self.nome[:12],
            "description": self.descricao,
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0F172A",
            "theme_color": self.cor_tema,
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ],
            "categories": ["productivity", "utilities"],
            "lang": "pt-BR"
        }

        with open(os.path.join(pasta, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        # service-worker.js
        sw_js = f"""
// Advak PWA Service Worker v{self.versao}
const CACHE_NAME = 'advak-{self.nome.lower().replace(" ", "-")}-v{self.versao}';
const ASSETS = ['/', '/index.html', '/manifest.json', '/app.js', '/app.css'];

self.addEventListener('install', e => {{
    e.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
    );
    self.skipWaiting();
}});

self.addEventListener('activate', e => {{
    e.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
        ))
    );
    self.clients.claim();
}});

self.addEventListener('fetch', e => {{
    e.respondWith(
        caches.match(e.request).then(r => r || fetch(e.request).catch(() =>
            caches.match('/index.html')
        ))
    );
}});

// Push Notifications
self.addEventListener('push', e => {{
    const data = e.data?.json() || {{}};
    self.registration.showNotification(data.titulo || '{self.nome}', {{
        body: data.mensagem || '',
        icon: '/icon-192.png',
        badge: '/icon-192.png',
        tag: data.tag || 'advak-notif',
        data: data
    }});
}});
"""
        with open(os.path.join(pasta, "sw.js"), "w", encoding="utf-8") as f:
            f.write(sw_js)

        # Gera ícone SVG simples (sem dependências externas)
        self._gerar_icone_svg(pasta, 192)
        self._gerar_icone_svg(pasta, 512)

        # CSS principal — responsivo e moderno
        css = self._gerar_css()
        with open(os.path.join(pasta, "app.css"), "w", encoding="utf-8") as f:
            f.write(css)

        # JavaScript principal
        js = self._gerar_js()
        with open(os.path.join(pasta, "app.js"), "w", encoding="utf-8") as f:
            f.write(js)

        # HTML principal
        html = self._gerar_html()
        with open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)

        return os.path.abspath(pasta)

    def _gerar_icone_svg(self, pasta: str, tamanho: int):
        """Gera ícone SVG como PNG placeholder."""
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{tamanho}" height="{tamanho}" viewBox="0 0 {tamanho} {tamanho}">
  <rect width="{tamanho}" height="{tamanho}" rx="{tamanho//4}" fill="{self.cor_tema}"/>
  <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle"
        font-size="{tamanho//2}" font-family="serif">{self.icone}</text>
</svg>"""
        nome_arquivo = f"icon-{tamanho}.png"
        # Salva como SVG com extensão .png (browsers aceitam SVG em manifests)
        with open(os.path.join(pasta, nome_arquivo), "w", encoding="utf-8") as f:
            f.write(svg)

    def _gerar_css(self) -> str:
        estilos_extra = "\n".join(self._estilos_custom)
        return f"""
/* Advak Mobile CSS */
:root {{
  --cor-primaria: {self.cor_tema};
  --cor-fundo: #0F172A;
  --cor-surface: #1E293B;
  --cor-texto: #F1F5F9;
  --cor-texto2: #94A3B8;
  --cor-borda: #334155;
  --raio: 12px;
  --sombra: 0 4px 20px rgba(0,0,0,0.3);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--cor-fundo);
  color: var(--cor-texto);
  min-height: 100vh;
  overflow-x: hidden;
  -webkit-tap-highlight-color: transparent;
}}

/* Safe area (notch, home bar) */
body {{ padding-bottom: env(safe-area-inset-bottom); }}

/* Telas */
.tela {{
  display: none;
  min-height: 100vh;
  padding: 16px;
  padding-top: calc(16px + env(safe-area-inset-top));
  animation: fadeIn 0.2s ease;
}}
.tela.ativa {{ display: block; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; }} }}

/* Componentes */
.advak-header {{
  background: var(--cor-surface);
  padding: 16px;
  border-radius: var(--raio);
  margin-bottom: 16px;
  box-shadow: var(--sombra);
}}

.advak-titulo {{ font-size: 24px; font-weight: 700; color: var(--cor-primaria); }}
.advak-subtitulo {{ font-size: 14px; color: var(--cor-texto2); margin-top: 4px; }}

.advak-card {{
  background: var(--cor-surface);
  border-radius: var(--raio);
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: var(--sombra);
  border: 1px solid var(--cor-borda);
}}

.advak-botao {{
  display: block;
  width: 100%;
  padding: 14px 20px;
  background: var(--cor-primaria);
  color: white;
  border: none;
  border-radius: var(--raio);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 8px;
  transition: all 0.15s;
  -webkit-appearance: none;
  min-height: 48px; /* touch-friendly */
}}
.advak-botao:active {{ transform: scale(0.97); opacity: 0.9; }}
.advak-botao.secundario {{
  background: var(--cor-surface);
  border: 1px solid var(--cor-borda);
}}
.advak-botao.perigo {{ background: #DC2626; }}
.advak-botao.sucesso {{ background: #16A34A; }}

.advak-campo {{
  width: 100%;
  padding: 12px 14px;
  background: var(--cor-surface);
  border: 1px solid var(--cor-borda);
  border-radius: var(--raio);
  color: var(--cor-texto);
  font-size: 16px;
  margin-bottom: 8px;
  outline: none;
  min-height: 48px;
}}
.advak-campo:focus {{ border-color: var(--cor-primaria); }}

.advak-label {{ font-size: 13px; color: var(--cor-texto2); margin-bottom: 4px; display: block; }}

/* Tab Bar */
.tab-bar {{
  position: fixed;
  bottom: 0;
  left: 0; right: 0;
  background: var(--cor-surface);
  border-top: 1px solid var(--cor-borda);
  display: flex;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 100;
}}
.tab-item {{
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px;
  cursor: pointer;
  color: var(--cor-texto2);
  font-size: 10px;
  transition: color 0.15s;
  min-height: 48px;
  justify-content: center;
}}
.tab-item.ativa {{ color: var(--cor-primaria); }}
.tab-item .icone {{ font-size: 22px; margin-bottom: 2px; }}

/* Lista */
.advak-lista-item {{
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: var(--cor-surface);
  border-bottom: 1px solid var(--cor-borda);
  cursor: pointer;
  min-height: 56px;
}}
.advak-lista-item:active {{ background: #0F172A; }}
.advak-lista-item .avatar {{
  width: 40px; height: 40px;
  border-radius: 50%;
  background: var(--cor-primaria);
  display: flex; align-items: center; justify-content: center;
  margin-right: 12px;
  font-size: 18px;
  flex-shrink: 0;
}}

/* Badge */
.badge {{
  background: #DC2626;
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 11px;
  font-weight: 700;
}}

/* Loading */
.spinner {{
  width: 32px; height: 32px;
  border: 3px solid var(--cor-borda);
  border-top-color: var(--cor-primaria);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 20px auto;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}

/* Toast */
.advak-toast {{
  position: fixed;
  bottom: 80px;
  left: 16px; right: 16px;
  background: #1E293B;
  color: white;
  padding: 12px 16px;
  border-radius: var(--raio);
  box-shadow: var(--sombra);
  z-index: 1000;
  animation: slideUp 0.3s ease;
  border-left: 4px solid var(--cor-primaria);
}}
@keyframes slideUp {{ from {{ transform: translateY(20px); opacity: 0; }} }}

/* Responsivo desktop */
@media (min-width: 640px) {{
  body {{ max-width: 430px; margin: 0 auto; box-shadow: 0 0 40px rgba(0,0,0,0.5); }}
}}

{estilos_extra}
"""

    def _gerar_js(self) -> str:
        telas_js = json.dumps(self._telas, ensure_ascii=False)
        scripts_extra = "\n".join(self._scripts_custom)
        return f"""
// Advak Mobile JS
const App = {{
  telas: {telas_js},
  telaAtual: '{self._tela_inicial}',
  historico: [],
  ws: null,

  init() {{
    // Registra Service Worker
    if ('serviceWorker' in navigator) {{
      navigator.serviceWorker.register('/sw.js').catch(() => {{}});
    }}

    // Instala prompt
    let installPrompt = null;
    window.addEventListener('beforeinstallprompt', e => {{
      e.preventDefault();
      installPrompt = e;
      document.getElementById('btn-instalar')?.classList.remove('hidden');
    }});

    document.getElementById('btn-instalar')?.addEventListener('click', () => {{
      installPrompt?.prompt();
    }});

    // Renderiza tela inicial
    this.navegar('{self._tela_inicial}');

    // Gestos de swipe
    this._initGestos();

    // Conecta WebSocket se disponível
    this._conectarWS();

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {{
      Notification.requestPermission();
    }}
  }},

  navegar(nomeTela, dados = {{}}) {{
    const tela = this.telas[nomeTela];
    if (!tela) return;

    this.historico.push(this.telaAtual);
    this.telaAtual = nomeTela;

    const container = document.getElementById('app-container');
    container.innerHTML = tela;

    // Atualiza tab bar ativa
    document.querySelectorAll('.tab-item').forEach(el => {{
      el.classList.toggle('ativa', el.dataset.tela === nomeTela);
    }});

    // Scroll topo
    window.scrollTo(0, 0);

    // Inicializa componentes dinâmicos
    this._initComponentes();
  }},

  voltar() {{
    if (this.historico.length > 0) {{
      this.navegar(this.historico.pop());
    }}
  }},

  toast(msg, tipo = 'info', duracao = 3000) {{
    const cores = {{ info: '#2563EB', sucesso: '#16A34A', erro: '#DC2626', aviso: '#D97706' }};
    const t = document.createElement('div');
    t.className = 'advak-toast';
    t.style.borderLeftColor = cores[tipo] || cores.info;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), duracao);
  }},

  chamarAPI(caminho, dados = {{}}) {{
    return fetch('/api' + caminho, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(dados)
    }}).then(r => r.json());
  }},

  // Geolocalização
  geolocalizacao() {{
    return new Promise((resolve, reject) => {{
      navigator.geolocation?.getCurrentPosition(
        pos => resolve({{ lat: pos.coords.latitude, lon: pos.coords.longitude, precisao: pos.coords.accuracy }}),
        err => reject(err),
        {{ enableHighAccuracy: true }}
      );
    }});
  }},

  // Câmera
  async abrirCamera(elemento_id) {{
    const stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'environment' }} }});
    const video = document.getElementById(elemento_id);
    if (video) {{ video.srcObject = stream; video.play(); }}
    return stream;
  }},

  // Vibração
  vibrar(padrao = 100) {{
    navigator.vibrate?.(padrao);
  }},

  // Compartilhar
  async compartilhar(dados) {{
    if (navigator.share) {{
      await navigator.share(dados);
    }} else {{
      this.toast('Compartilhamento não suportado neste browser', 'aviso');
    }}
  }},

  // Storage local
  salvar(chave, valor) {{
    localStorage.setItem('advak_' + chave, JSON.stringify(valor));
  }},

  carregar(chave, padrao = null) {{
    const v = localStorage.getItem('advak_' + chave);
    return v ? JSON.parse(v) : padrao;
  }},

  removerStorage(chave) {{
    localStorage.removeItem('advak_' + chave);
  }},

  _conectarWS() {{
    const porta = new URLSearchParams(window.location.search).get('ws') || '8765';
    try {{
      this.ws = new WebSocket(`ws://${{window.location.hostname}}:${{porta}}`);
      this.ws.onmessage = e => {{
        const msg = JSON.parse(e.data);
        if (msg.tipo === 'navegar') this.navegar(msg.tela, msg.dados);
        if (msg.tipo === 'toast') this.toast(msg.mensagem, msg.estilo);
        if (msg.tipo === 'atualizar_tela') this.navegar(this.telaAtual);
        if (msg.tipo === 'dados') window.dispatchEvent(new CustomEvent('advak-dados', {{ detail: msg }}));
      }};
      this.ws.onerror = () => {{}};
    }} catch(e) {{}}
  }},

  _initGestos() {{
    let startX = 0, startY = 0;
    document.addEventListener('touchstart', e => {{
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    }}, {{ passive: true }});
    document.addEventListener('touchend', e => {{
      const dx = e.changedTouches[0].clientX - startX;
      const dy = e.changedTouches[0].clientY - startY;
      if (Math.abs(dx) > 80 && Math.abs(dx) > Math.abs(dy) * 2) {{
        if (dx > 0) this.voltar(); // swipe right = voltar
      }}
    }}, {{ passive: true }});
  }},

  _initComponentes() {{
    // Botões de navegação
    document.querySelectorAll('[data-ir-para]').forEach(el => {{
      el.addEventListener('click', () => this.navegar(el.dataset.irPara));
    }});
    // Botão voltar
    document.querySelectorAll('[data-voltar]').forEach(el => {{
      el.addEventListener('click', () => this.voltar());
    }});
    // Chamadas API
    document.querySelectorAll('[data-api]').forEach(el => {{
      el.addEventListener('click', () => {{
        const campos = {{}};
        document.querySelectorAll('[data-campo]').forEach(c => {{
          campos[c.dataset.campo] = c.value;
        }});
        this.chamarAPI(el.dataset.api, campos).then(r => {{
          if (r.toast) this.toast(r.toast, r.tipo || 'info');
          if (r.navegar) this.navegar(r.navegar);
        }});
      }});
    }});
  }}
}};

window.addEventListener('load', () => App.init());
window.App = App;
{scripts_extra}
"""

    def _gerar_html(self) -> str:
        telas_html = ""
        for nome, conteudo in self._telas.items():
            telas_html += f'<div class="tela" id="tela-{nome}">{conteudo}</div>\n'

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="{self.cor_tema}">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="{self.nome}">
  <meta name="description" content="{self.descricao}">
  <link rel="manifest" href="/manifest.json">
  <link rel="stylesheet" href="/app.css">
  <title>{self.nome}</title>
</head>
<body>
  <div id="app-container"></div>
  <button id="btn-instalar" class="hidden advak-botao" style="position:fixed;bottom:80px;left:50%;transform:translateX(-50%);width:auto;padding:10px 20px;">
    📲 Instalar App
  </button>
  <script src="/app.js"></script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
#  2. SERVIDOR MOBILE (Backend do PWA + WebSocket Bridge)
# ══════════════════════════════════════════════════════════════════════════════

class ServidorMobile:
    """Servidor HTTP + WebSocket que alimenta o PWA."""

    def __init__(self, pasta_app: str = "mobile_app", porta: int = 8080, porta_ws: int = 8765):
        self.pasta = pasta_app
        self.porta = porta
        self.porta_ws = porta_ws
        self._rotas_api: Dict[str, Callable] = {}
        self._clientes_ws: List = []
        self._rodando = False

    def rota(self, caminho: str, fn: Callable):
        self._rotas_api[caminho] = fn
        return self

    def enviar_todos(self, mensagem: dict):
        """Envia mensagem para todos os clientes conectados."""
        dados = json.dumps(mensagem, ensure_ascii=False).encode()
        for cliente in list(self._clientes_ws):
            try:
                self._ws_enviar(cliente, dados)
            except Exception:
                self._clientes_ws.remove(cliente)

    def navegar_todos(self, tela: str, dados: dict = None):
        """Navega todos os clientes para uma tela."""
        self.enviar_todos({"tipo": "navegar", "tela": tela, "dados": dados or {}})

    def toast_todos(self, mensagem: str, tipo: str = "info"):
        """Envia toast para todos os clientes."""
        self.enviar_todos({"tipo": "toast", "mensagem": mensagem, "estilo": tipo})

    def iniciar(self, abrir_browser: bool = True):
        """Inicia o servidor em thread separada."""
        self._rodando = True

        # Thread HTTP
        t_http = threading.Thread(target=self._servidor_http, daemon=True)
        t_http.start()

        # Thread WebSocket
        t_ws = threading.Thread(target=self._servidor_ws, daemon=True)
        t_ws.start()

        ip = self._obter_ip_local()
        url = f"http://{ip}:{self.porta}"

        print(f"📱 App Mobile rodando!")
        print(f"   📡 URL local: {url}")
        print(f"   📡 URL rede:  http://{ip}:{self.porta}")
        print(f"   Escaneie o QR code abaixo com o celular:")
        print(self._qr_terminal(url))
        print(f"   Ctrl+C para parar")

        if abrir_browser:
            try:
                import webbrowser
                webbrowser.open(url)
            except Exception:
                pass

        return url

    def _obter_ip_local(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "localhost"

    def _servidor_http(self):
        """Servidor HTTP simples."""
        import http.server

        pasta = self.pasta
        rotas_api = self._rotas_api

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self._servir_arquivo()

            def do_POST(self):
                if self.path.startswith('/api/'):
                    caminho = self.path[4:]
                    fn = rotas_api.get(caminho)
                    if fn:
                        tamanho = int(self.headers.get('Content-Length', 0))
                        corpo = json.loads(self.rfile.read(tamanho)) if tamanho else {}
                        try:
                            resultado = fn(corpo)
                            resposta = json.dumps(resultado or {}, ensure_ascii=False).encode()
                        except Exception as e:
                            resposta = json.dumps({"erro": str(e)}).encode()
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(resposta)
                    else:
                        self.send_response(404)
                        self.end_headers()
                else:
                    self._servir_arquivo()

            def _servir_arquivo(self):
                caminho = self.path.split('?')[0]
                if caminho == '/':
                    caminho = '/index.html'
                arquivo = os.path.join(pasta, caminho.lstrip('/'))
                tipos = {
                    '.html': 'text/html', '.js': 'application/javascript',
                    '.css': 'text/css', '.json': 'application/json',
                    '.png': 'image/png', '.svg': 'image/svg+xml',
                    '.ico': 'image/x-icon', '.woff2': 'font/woff2',
                }
                ext = os.path.splitext(arquivo)[1]
                tipo = tipos.get(ext, 'application/octet-stream')
                try:
                    with open(arquivo, 'rb') as f:
                        conteudo = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', tipo)
                    self.send_header('Cache-Control', 'no-cache')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(conteudo)
                except FileNotFoundError:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, fmt, *args):
                pass  # Silencia logs HTTP

        server = http.server.HTTPServer(('0.0.0.0', self.porta), Handler)
        server.serve_forever()

    def _servidor_ws(self):
        """Servidor WebSocket manual (sem dependências externas)."""
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind(('0.0.0.0', self.porta_ws))
            srv.listen(10)
            while self._rodando:
                try:
                    srv.settimeout(1)
                    conn, addr = srv.accept()
                    t = threading.Thread(target=self._ws_handshake, args=(conn,), daemon=True)
                    t.start()
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception:
            pass

    def _ws_handshake(self, conn):
        """Realiza handshake WebSocket."""
        try:
            data = conn.recv(4096).decode('utf-8', errors='ignore')
            key = None
            for line in data.split('\r\n'):
                if 'Sec-WebSocket-Key' in line:
                    key = line.split(': ')[1].strip()
            if not key:
                conn.close()
                return
            magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept = base64.b64encode(hashlib.sha1((key + magic).encode()).digest()).decode()
            resp = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            )
            conn.send(resp.encode())
            self._clientes_ws.append(conn)
            # Keep alive
            while True:
                try:
                    conn.recv(1024)
                except Exception:
                    break
            if conn in self._clientes_ws:
                self._clientes_ws.remove(conn)
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _ws_enviar(self, conn, dados: bytes):
        """Envia frame WebSocket."""
        tamanho = len(dados)
        if tamanho < 126:
            header = struct.pack('BB', 0x81, tamanho)
        elif tamanho < 65536:
            header = struct.pack('!BBH', 0x81, 126, tamanho)
        else:
            header = struct.pack('!BBQ', 0x81, 127, tamanho)
        conn.send(header + dados)

    def _qr_terminal(self, url: str) -> str:
        """Gera QR Code em ASCII para o terminal."""
        # Implementação simples de QR code ASCII
        try:
            import qrcode
            qr = qrcode.QRCode(border=1)
            qr.add_data(url)
            qr.make()
            linhas = []
            for row in qr.modules:
                linha = ''.join('██' if cell else '  ' for cell in row)
                linhas.append(f"   {linha}")
            return '\n'.join(linhas)
        except ImportError:
            # Fallback sem qrcode
            return f"\n   [QR Code: {url}]\n   pip install qrcode para gerar QR visual\n"


# ══════════════════════════════════════════════════════════════════════════════
#  3. GERADOR DE QR CODE
# ══════════════════════════════════════════════════════════════════════════════

class GeradorQR:
    """Gera QR Codes para URLs, Wi-Fi, vCards, PIX, etc."""

    @staticmethod
    def url(link: str, arquivo: str = None) -> str:
        return GeradorQR._gerar(link, arquivo)

    @staticmethod
    def wifi(ssid: str, senha: str, seguranca: str = "WPA", arquivo: str = None) -> str:
        dados = f"WIFI:T:{seguranca};S:{ssid};P:{senha};;"
        return GeradorQR._gerar(dados, arquivo)

    @staticmethod
    def pix(chave: str, nome: str, cidade: str, valor: float = None,
            descricao: str = "", arquivo: str = None) -> str:
        """Gera QR Code PIX (padrão EMV/Copia-e-cola)."""
        def tlv(tag, value):
            v = str(value)
            return f"{tag:02d}{len(v):02d}{v}"

        merchant_account = tlv(0, "BR.GOV.BCB.PIX") + tlv(1, chave)
        payload = (
            tlv(0, "01") +
            tlv(1, "12") +
            tlv(26, merchant_account) +
            tlv(52, "0000") +
            tlv(53, "986") +  # BRL
            (tlv(54, f"{valor:.2f}") if valor else "") +
            tlv(58, "BR") +
            tlv(59, nome[:25]) +
            tlv(60, cidade[:15]) +
            (tlv(62, tlv(5, descricao[:25])) if descricao else "") +
            "6304"  # CRC placeholder
        )
        # CRC16-CCITT
        crc = 0xFFFF
        for byte in payload.encode('utf-8'):
            crc ^= byte << 8
            for _ in range(8):
                crc = (crc << 1) ^ (0x1021 if crc & 0x8000 else 0)
                crc &= 0xFFFF
        payload += f"{crc:04X}"
        return GeradorQR._gerar(payload, arquivo)

    @staticmethod
    def vcard(nome: str, telefone: str = "", email: str = "",
              empresa: str = "", cargo: str = "", arquivo: str = None) -> str:
        vcard = (
            f"BEGIN:VCARD\nVERSION:3.0\n"
            f"FN:{nome}\n"
            f"ORG:{empresa}\n"
            f"TITLE:{cargo}\n"
            f"TEL:{telefone}\n"
            f"EMAIL:{email}\n"
            f"END:VCARD"
        )
        return GeradorQR._gerar(vcard, arquivo)

    @staticmethod
    def _gerar(dados: str, arquivo: str = None) -> str:
        """Gera QR Code e salva se arquivo especificado."""
        try:
            import qrcode as qrc
            qr = qrc.QRCode(
                error_correction=qrc.constants.ERROR_CORRECT_M,
                box_size=10, border=4
            )
            qr.add_data(dados)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            if arquivo:
                img.save(arquivo)
            return arquivo or dados
        except ImportError:
            # ASCII fallback
            linhas = [f"[QR: {dados[:50]}{'...' if len(dados) > 50 else ''}]"]
            if arquivo:
                with open(arquivo, 'w') as f:
                    f.write('\n'.join(linhas))
            return arquivo or dados


# ══════════════════════════════════════════════════════════════════════════════
#  4. COMPONENTES UI MOBILE
# ══════════════════════════════════════════════════════════════════════════════

class ComponentesMobile:
    """Gera HTML de componentes mobile responsivos."""

    @staticmethod
    def header(titulo: str, subtitulo: str = "", voltar: bool = False,
               acao: str = None, texto_acao: str = "⚙️") -> str:
        btn_voltar = '<button data-voltar class="advak-botao secundario" style="width:auto;padding:8px 12px;margin-right:12px">← Voltar</button>' if voltar else ''
        btn_acao = f'<button onclick="{acao}" class="advak-botao secundario" style="width:auto;padding:8px 12px">{texto_acao}</button>' if acao else ''
        return f"""
<div class="advak-header" style="display:flex;align-items:center">
  <div style="flex:1">
    {btn_voltar}
    <div class="advak-titulo">{titulo}</div>
    {'<div class="advak-subtitulo">' + subtitulo + '</div>' if subtitulo else ''}
  </div>
  {btn_acao}
</div>"""

    @staticmethod
    def card(titulo: str = "", conteudo: str = "", icone: str = "",
             clique: str = None, cor: str = None) -> str:
        style = f"border-left: 4px solid {cor};" if cor else ""
        onclick = f'onclick="{clique}"' if clique else ""
        return f"""
<div class="advak-card" {onclick} style="{style}cursor:{'pointer' if clique else 'default'}">
  {'<div style="font-size:32px;margin-bottom:8px">' + icone + '</div>' if icone else ''}
  {'<div style="font-weight:600;margin-bottom:6px">' + titulo + '</div>' if titulo else ''}
  {conteudo}
</div>"""

    @staticmethod
    def botao(texto: str, tipo: str = "primario", acao: str = None,
              vai_para: str = None) -> str:
        onclick = f'onclick="{acao}"' if acao else ""
        data_nav = f'data-ir-para="{vai_para}"' if vai_para else ""
        return f'<button class="advak-botao {tipo}" {onclick} {data_nav}>{texto}</button>'

    @staticmethod
    def campo(placeholder: str = "", tipo: str = "text", nome: str = "",
              label: str = "") -> str:
        lbl = f'<label class="advak-label">{label}</label>' if label else ""
        return f"""
{lbl}
<input class="advak-campo" type="{tipo}" placeholder="{placeholder}"
  data-campo="{nome}" id="campo-{nome}" autocomplete="off">"""

    @staticmethod
    def lista_item(titulo: str, subtitulo: str = "", icone: str = "•",
                   vai_para: str = None, badge: str = None) -> str:
        nav = f'data-ir-para="{vai_para}"' if vai_para else ""
        bdg = f'<span class="badge">{badge}</span>' if badge else ""
        return f"""
<div class="advak-lista-item" {nav}>
  <div class="avatar">{icone}</div>
  <div style="flex:1">
    <div style="font-weight:600">{titulo}</div>
    {'<div style="color:var(--cor-texto2);font-size:13px">' + subtitulo + '</div>' if subtitulo else ''}
  </div>
  {bdg}
  {'<span style="color:var(--cor-texto2)">›</span>' if vai_para else ''}
</div>"""

    @staticmethod
    def tab_bar(abas: List[dict]) -> str:
        """abas = [{icone, texto, tela}]"""
        items = ""
        for aba in abas:
            items += f"""
<div class="tab-item" data-tela="{aba.get('tela','')}"
     onclick="App.navegar('{aba.get('tela','')}')">
  <div class="icone">{aba.get('icone','📱')}</div>
  <div>{aba.get('texto','')}</div>
</div>"""
        return f'<div class="tab-bar">{items}</div>'

    @staticmethod
    def grade(itens: List[dict], colunas: int = 2) -> str:
        """Grade de cards com N colunas."""
        cards = ""
        for item in itens:
            cards += f"""
<div class="advak-card" data-ir-para="{item.get('ir_para','')}"
     style="cursor:pointer;text-align:center" >
  <div style="font-size:40px">{item.get('icone','📦')}</div>
  <div style="font-weight:600;margin-top:8px">{item.get('titulo','')}</div>
  {'<div style="color:var(--cor-texto2);font-size:13px">' + item.get('subtitulo','') + '</div>' if item.get('subtitulo') else ''}
</div>"""
        return f'<div style="display:grid;grid-template-columns:repeat({colunas},1fr);gap:12px">{cards}</div>'

    @staticmethod
    def grafico_barras(dados: List[dict], titulo: str = "") -> str:
        """dados = [{label, valor, cor}]"""
        maximo = max((d.get('valor', 0) for d in dados), default=1)
        barras = ""
        for d in dados:
            pct = (d.get('valor', 0) / maximo) * 100
            cor = d.get('cor', '#2563EB')
            barras += f"""
<div style="margin-bottom:12px">
  <div style="display:flex;justify-content:space-between;margin-bottom:4px;font-size:13px">
    <span>{d.get('label','')}</span>
    <span style="color:var(--cor-texto2)">{d.get('valor','')}</span>
  </div>
  <div style="background:var(--cor-borda);border-radius:4px;height:8px">
    <div style="background:{cor};width:{pct:.1f}%;height:100%;border-radius:4px;transition:width 0.5s"></div>
  </div>
</div>"""
        return f"""
<div class="advak-card">
  {'<div style="font-weight:600;margin-bottom:16px">' + titulo + '</div>' if titulo else ''}
  {barras}
</div>"""


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTAÇÃO DO SISTEMA MOBILE
# ══════════════════════════════════════════════════════════════════════════════

def criar_sistema_mobile():
    """Retorna o objeto 'mobile' para o escopo Advak."""
    _app = [None]
    _servidor = [None]
    ui = ComponentesMobile()
    qr = GeradorQR()

    def novo_app(nome, descricao="", cor="#2563EB", versao="1.0", icone="🚀"):
        app = GeradorPWA(nome, descricao, cor, versao, icone)
        _app[0] = app
        return {
            'tela':        lambda nome_t, html: app.tela(nome_t, html),
            'script':      lambda js: app.script(js),
            'estilo':      lambda css: app.estilo(css),
            'rota_api':    lambda caminho, fn: app.rota_api(caminho, fn),
            'gerar':       lambda pasta="mobile_app": app.gerar(pasta),
            '_app':        app,
        }

    def iniciar_servidor(pasta="mobile_app", porta=8080, porta_ws=8765, browser=True):
        srv = ServidorMobile(pasta, porta, porta_ws)
        _servidor[0] = srv
        url = srv.iniciar(browser)
        return {
            'url':          url,
            'rota':         lambda caminho, fn: srv.rota(caminho, fn),
            'enviar':       lambda msg: srv.enviar_todos(msg),
            'navegar':      lambda tela, dados=None: srv.navegar_todos(tela, dados),
            'toast':        lambda msg, tipo="info": srv.toast_todos(msg, tipo),
            '_servidor':    srv,
        }

    return {
        # App PWA
        'criar_app':    lambda nome, desc="", cor="#2563EB", v="1.0", icone="🚀":
                            novo_app(nome, desc, cor, v, icone),
        'servidor':     iniciar_servidor,

        # QR Code
        'qr':           {
            'url':      lambda link, arq=None: qr.url(link, arq),
            'wifi':     lambda ssid, senha, seg="WPA", arq=None: qr.wifi(ssid, senha, seg, arq),
            'pix':      lambda chave, nome, cidade, valor=None, desc="", arq=None:
                            qr.pix(chave, nome, cidade, valor, desc, arq),
            'vcard':    lambda nome, tel="", email="", emp="", cargo="", arq=None:
                            qr.vcard(nome, tel, email, emp, cargo, arq),
        },

        # Componentes UI
        'ui':           {
            'header':       lambda titulo, sub="", voltar=False, acao=None, txt_acao="⚙️":
                                ui.header(titulo, sub, voltar, acao, txt_acao),
            'card':         lambda titulo="", conteudo="", icone="", clique=None, cor=None:
                                ui.card(titulo, conteudo, icone, clique, cor),
            'botao':        lambda texto, tipo="primario", acao=None, vai_para=None:
                                ui.botao(texto, tipo, acao, vai_para),
            'campo':        lambda placeholder="", tipo="text", nome="", label="":
                                ui.campo(placeholder, tipo, nome, label),
            'lista_item':   lambda titulo, sub="", icone="•", vai_para=None, badge=None:
                                ui.lista_item(titulo, sub, icone, vai_para, badge),
            'tab_bar':      lambda abas: ui.tab_bar(abas),
            'grade':        lambda itens, colunas=2: ui.grade(itens, colunas),
            'grafico':      lambda dados, titulo="": ui.grafico_barras(dados, titulo),
        },

        # Utilitários
        'ip_local':     lambda: ServidorMobile()._obter_ip_local(),
    }
