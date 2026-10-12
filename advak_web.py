# -*- coding: utf-8 -*-
"""
advak_web.py — Servidor Web Completo para Advak 5.0
Recursos: HTTP, WebSocket, Sessões, Autenticação, Banco Auto, Middleware
"""

import threading, os, sys, json, mimetypes, webbrowser, time, traceback
import asyncio, hashlib, hmac, base64, secrets, sqlite3, re
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from collections import defaultdict

# Windows: SelectorEventLoop para run_coroutine_threadsafe
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ── Cores ────────────────────────────────────────────────────────────────────
RESET  = "\033[0m"; AZUL = "\033[94m"; VERDE = "\033[92m"
AMARELO= "\033[93m"; VERM = "\033[91m"; CINZA = "\033[90m"; NEG = "\033[1m"

def _safe_print(*args, **kwargs):
    try:
        if sys.is_finalizing(): return
        print(*args, **kwargs)
    except Exception: pass

def _log(method, path, status, ms=0, extra=""):
    try:
        if sys.is_finalizing(): return
        cor = VERDE if status < 400 else AMARELO if status < 500 else VERM
        ws  = " 🔌WS" if extra == "ws" else ""
        print(f"  {CINZA}│{RESET} {AZUL}{method:7}{RESET} {path:32} {cor}{status}{RESET} {CINZA}{ms}ms{ws}{RESET}", flush=True)
    except Exception: pass

# ── Sessões ───────────────────────────────────────────────────────────────────
class GerenciadorSessoes:
    def __init__(self):
        self._sessoes = {}
        self._segredo = secrets.token_hex(32)

    def criar(self, dados=None):
        sid = secrets.token_urlsafe(32)
        self._sessoes[sid] = {
            'dados': dados or {},
            'criado_em': time.time(),
            'expira_em': time.time() + 86400  # 24h
        }
        return sid

    def obter(self, sid):
        s = self._sessoes.get(sid)
        if s and s['expira_em'] > time.time():
            return s['dados']
        if s: del self._sessoes[sid]
        return None

    def salvar(self, sid, dados):
        if sid in self._sessoes:
            self._sessoes[sid]['dados'] = dados

    def destruir(self, sid):
        self._sessoes.pop(sid, None)

    def limpar_expiradas(self):
        agora = time.time()
        expiradas = [k for k, v in self._sessoes.items() if v['expira_em'] < agora]
        for k in expiradas: del self._sessoes[k]

    def cookie_header(self, sid):
        return f"sessao_id={sid}; HttpOnly; SameSite=Lax; Path=/"

# ── Autenticação ──────────────────────────────────────────────────────────────
class Autenticacao:
    def __init__(self, sessoes):
        self._sessoes  = sessoes
        self._usuarios = {}  # login → {senha_hash, nome, nivel, dados}
    
    def gerar_csrf(self, sid):
        """Gera token CSRF vinculado à sessão."""
        import hashlib, hmac
        return hmac.new(sid.encode(), b'csrf', hashlib.sha256).hexdigest()[:32]
    
    def verificar_csrf(self, sid, token):
        """Verifica token CSRF da requisição."""
        return secrets.compare_digest(self.gerar_csrf(sid), token or '')

    def _hash(self, senha):
        """Hash seguro de senha — bcrypt se disponível, SHA-256 como fallback."""
        try:
            import bcrypt
            if isinstance(senha, str): senha = senha.encode()
            return bcrypt.hashpw(senha, bcrypt.gensalt()).decode()
        except ImportError:
            import hashlib, hmac, os
            salt = os.urandom(32).hex()
            h    = hmac.new(salt.encode(), senha.encode(), hashlib.sha256).hexdigest()
            return f"sha256${salt}${h}"

    def _verificar_hash(self, senha, hash_armazenado):
        """Verifica senha contra hash armazenado."""
        try:
            import bcrypt
            if hash_armazenado.startswith('$2'):
                return bcrypt.checkpw(senha.encode(), hash_armazenado.encode())
        except ImportError:
            pass
        # Fallback SHA256 com salt
        if '$' in hash_armazenado:
            partes = hash_armazenado.split('$')
            if len(partes) == 3 and partes[0] in ('sha256', ''):
                _, salt, stored = partes
                import hashlib, hmac
                h = hmac.new(salt.encode(), senha.encode(), hashlib.sha256).hexdigest()
                return hmac.compare_digest(h, stored)
        # Legado: SHA256 simples
        import hashlib
        return hashlib.sha256(senha.encode()).hexdigest() == hash_armazenado

    def cadastrar(self, login, senha, nome="", nivel="usuario", dados=None):
        self._usuarios[login] = {
            'senha_hash': self._hash(senha),
            'nome': nome or login,
            'nivel': nivel,
            'dados': dados or {}
        }
        return True

    def autenticar(self, login, senha):
        u = self._usuarios.get(login)
        if u and self._verificar_hash(senha, u['senha_hash']):
            return {
                'login': login, 'nome': u['nome'],
                'nivel': u['nivel'], 'dados': u['dados']
            }
        return None

    def fazer_login(self, login, senha):
        usuario = self.autenticar(login, senha)
        if usuario:
            sid = self._sessoes.criar(usuario)
            return sid, usuario
        return None, None

    def usuario_atual(self, sid):
        if not sid: return None
        return self._sessoes.obter(sid)

    def fazer_logout(self, sid):
        self._sessoes.destruir(sid)

# ── Banco de Dados Auto ───────────────────────────────────────────────────────
class BancoAuto:
    """Cria e gerencia banco SQLite automaticamente a partir de um esquema simples."""

    TIPOS = {
        'texto': 'TEXT', 'text': 'TEXT',
        'numero': 'REAL', 'inteiro': 'INTEGER', 'int': 'INTEGER',
        'booleano': 'INTEGER', 'bool': 'INTEGER',
        'data': 'TEXT', 'timestamp': 'TEXT',
        'json': 'TEXT', 'lista': 'TEXT',
    }

    def __init__(self, nome_banco="app.db"):
        self._arquivo = nome_banco
        self._conn = None
        self._lock = threading.Lock()

    def _conectar(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self._arquivo, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def criar_tabela(self, nome, campos, chave_primaria="id"):
        """
        campos = {
            'nome':    'texto',
            'email':   'texto',
            'nota':    'numero',
            'ativo':   'booleano',
            'dados':   'json',
        }
        """
        colunas = [f"{chave_primaria} INTEGER PRIMARY KEY AUTOINCREMENT"]
        for campo, tipo in campos.items():
            sql_tipo = self.TIPOS.get(tipo.lower(), 'TEXT')
            colunas.append(f"{campo} {sql_tipo}")
        colunas.append("criado_em TEXT DEFAULT (datetime('now'))")
        colunas.append("atualizado_em TEXT DEFAULT (datetime('now'))")

        sql = f"CREATE TABLE IF NOT EXISTS {nome} ({', '.join(colunas)})"
        with self._lock:
            conn = self._conectar()
            conn.execute(sql)
            conn.commit()
        _safe_print(f"  {VERDE}✅ Tabela '{nome}' pronta{RESET}")
        return self

    def _serializar(self, valor):
        if isinstance(valor, (dict, list)):
            return json.dumps(valor, ensure_ascii=False)
        if isinstance(valor, bool):
            return 1 if valor else 0
        return valor

    def _deserializar(self, row):
        d = dict(row)
        for k, v in d.items():
            if isinstance(v, str) and v and v[0] in ('{', '['):
                try: d[k] = json.loads(v)
                except: pass
        return d

    def inserir(self, tabela, dados):
        campos = list(dados.keys())
        valores = [self._serializar(v) for v in dados.values()]
        marcadores = ', '.join(['?'] * len(campos))
        sql = f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({marcadores})"
        with self._lock:
            conn = self._conectar()
            cur = conn.execute(sql, valores)
            conn.commit()
            return cur.lastrowid

    def buscar(self, tabela, onde=None, params=None, ordenar=None, limite=None):
        sql = f"SELECT * FROM {tabela}"
        if onde: sql += f" WHERE {onde}"
        if ordenar: sql += f" ORDER BY {ordenar}"
        if limite: sql += f" LIMIT {limite}"
        with self._lock:
            conn = self._conectar()
            rows = conn.execute(sql, params or []).fetchall()
        return [self._deserializar(r) for r in rows]

    def buscar_um(self, tabela, onde, params=None):
        resultados = self.buscar(tabela, onde, params, limite=1)
        return resultados[0] if resultados else None

    def atualizar(self, tabela, dados, onde, params=None):
        sets = ', '.join([f"{k}=?" for k in dados.keys()])
        sets += ", atualizado_em=datetime('now')"
        valores = [self._serializar(v) for v in dados.values()]
        if params: valores += params
        sql = f"UPDATE {tabela} SET {sets} WHERE {onde}"
        with self._lock:
            conn = self._conectar()
            cur = conn.execute(sql, valores)
            conn.commit()
            return cur.rowcount

    def excluir(self, tabela, onde, params=None):
        sql = f"DELETE FROM {tabela} WHERE {onde}"
        with self._lock:
            conn = self._conectar()
            cur = conn.execute(sql, params or [])
            conn.commit()
            return cur.rowcount

    def contar(self, tabela, onde=None, params=None):
        sql = f"SELECT COUNT(*) FROM {tabela}"
        if onde: sql += f" WHERE {onde}"
        with self._lock:
            conn = self._conectar()
            return conn.execute(sql, params or []).fetchone()[0]

    def sql_direto(self, sql, params=None):
        with self._lock:
            conn = self._conectar()
            rows = conn.execute(sql, params or []).fetchall()
            conn.commit()
        return [self._deserializar(r) for r in rows]

    def fechar(self):
        if self._conn:
            self._conn.close()
            self._conn = None

# ── WebSocket Manager ─────────────────────────────────────────────────────────
class GerenciadorWS:
    def __init__(self):
        self._clientes = {}  # client_id → ws_connection
        self._salas    = defaultdict(set)  # sala → {client_ids}
        self._handlers = {}  # evento → handler_fn
        self._lock     = threading.Lock()
        self._id_counter = 0

    def ao_mensagem(self, evento, handler):
        self._handlers[evento] = handler

    def _novo_id(self):
        with self._lock:
            self._id_counter += 1
            return f"ws_{self._id_counter}"

    def entrar_sala(self, cid, sala):
        with self._lock:
            self._salas[sala].add(cid)

    def sair_sala(self, cid, sala):
        with self._lock:
            self._salas[sala].discard(cid)

    def enviar(self, cid, dados):
        """Envia mensagem para um cliente específico."""
        msg = json.dumps(dados, ensure_ascii=False, default=str)
        with self._lock:
            conn = self._clientes.get(cid)
        if conn:
            try:
                conn['queue'].put_nowait(msg)
                return True
            except: pass
        return False

    def transmitir(self, dados, sala=None, exceto=None):
        """Envia para todos (ou todos de uma sala)."""
        msg = json.dumps(dados, ensure_ascii=False, default=str)
        with self._lock:
            if sala:
                alvos = list(self._salas.get(sala, set()))
            else:
                alvos = list(self._clientes.keys())

        for cid in alvos:
            if cid == exceto: continue
            with self._lock:
                conn = self._clientes.get(cid)
            if conn:
                try: conn['queue'].put_nowait(msg)
                except: pass

    def contar(self, sala=None):
        with self._lock:
            if sala: return len(self._salas.get(sala, set()))
            return len(self._clientes)

# ── Respostas HTTP ────────────────────────────────────────────────────────────
class Resposta:
    def __init__(self, corpo, status=200, tipo="text/html; charset=utf-8", cabecalhos=None):
        self.corpo     = corpo
        self.status    = status
        self.tipo      = tipo
        self.cabecalhos = cabecalhos or {}

class Requisicao:
    def __init__(self, metodo, caminho, consulta, corpo, cabecalhos, parametros=None, sessao=None, usuario=None):
        self.metodo     = metodo
        self.caminho    = caminho
        self.consulta   = consulta
        self.corpo      = corpo
        self.cabecalhos = cabecalhos
        self.parametros = parametros or {}
        self.sessao     = sessao or {}
        self.usuario    = usuario
        self.dados      = None
        self.eh_get     = metodo == "GET"
        self.eh_post    = metodo == "POST"
        self.eh_put     = metodo == "PUT"
        self.eh_delete  = metodo == "DELETE"
        # Parse JSON body
        if corpo:
            try: self.dados = json.loads(corpo)
            except: pass
        # Compat aliases
        self.method  = metodo
        self.path    = caminho
        self.query   = consulta
        self.params  = parametros
        self.json    = self.dados

# ── Funções de resposta ────────────────────────────────────────────────────────
def _html(conteudo, status=200, cabecalhos=None):
    return Resposta(str(conteudo), status, "text/html; charset=utf-8", cabecalhos)

def _json_resp(dados, status=200):
    corpo = json.dumps(dados, ensure_ascii=False, default=str)
    return Resposta(corpo, status, "application/json; charset=utf-8")

def _texto_resp(conteudo, status=200):
    return Resposta(str(conteudo), status, "text/plain; charset=utf-8")

def _redirecionar(url, status=302):
    return Resposta("", status, "text/plain", {"Location": url})

def _renderizar(template_path, contexto=None):
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        pastas = [os.path.join(os.getcwd(), "templates"), os.getcwd()]
        env = Environment(loader=FileSystemLoader(pastas),
                         autoescape=select_autoescape(['html']))
        tmpl = env.get_template(template_path)
        return _html(tmpl.render(**(contexto or {})))
    except Exception as e:
        return _html(f"<h2>Erro no template</h2><pre>{e}</pre>", 500)

# ── Servidor Principal ────────────────────────────────────────────────────────
class AdvakServer:
    def __init__(self):
        self._porta      = 8080
        self._host       = "0.0.0.0"
        self._rotas      = []
        self._middleware = []
        self._estaticos  = {}
        self._erro_404   = None
        self._erro_500   = None
        self._servidor   = None
        self._auto_browser = True
        # Serviços integrados
        self.sessoes   = GerenciadorSessoes()
        self.auth      = Autenticacao(self.sessoes)
        self.ws        = GerenciadorWS()
        self._banco    = None
        # Rate limiting
        self._rate_limit    = {}   # ip → [timestamps]
        self._rate_max      = 100  # req por janela
        self._rate_janela   = 60   # segundos
        self._rate_ativo    = False

    # ── Banco automático ──────────────────────────────────────────────────────
    def usar_banco(self, arquivo="app.db"):
        self._banco = BancoAuto(arquivo)
        _safe_print(f"  {VERDE}🗄️  Banco SQLite: {arquivo}{RESET}")
        return self._banco

    def criar_tabela(self, nome, campos):
        if not self._banco:
            self.usar_banco()
        return self._banco.criar_tabela(nome, campos)

    # ── Configuração ──────────────────────────────────────────────────────────
    def porta(self, p): self._porta = int(p); return self
    def host(self, h):  self._host  = h;      return self
    def auto_abrir(self, v=True): self._auto_browser = bool(v); return self

    # ── Rotas ─────────────────────────────────────────────────────────────────
    def rota(self, caminho, handler, metodo="GET"):
        self._rotas.append((metodo.upper(), caminho, handler))
        return self

    def obter(self, c, h):     return self.rota(c, h, "GET")
    def publicar(self, c, h):  return self.rota(c, h, "POST")
    def atualizar(self, c, h): return self.rota(c, h, "PUT")
    def deletar(self, c, h):   return self.rota(c, h, "DELETE")
    def qualquer(self, c, h):  return self.rota(c, h, "*")
    # EN aliases
    def get(self, c, h):    return self.obter(c, h)
    def post(self, c, h):   return self.publicar(c, h)
    def put(self, c, h):    return self.atualizar(c, h)
    def delete(self, c, h): return self.deletar(c, h)

    # ── Middleware ────────────────────────────────────────────────────────────
    def limitar(self, max_req=100, janela=60):
        """Ativa rate limiting: max_req requisições por janela (segundos)."""
        self._rate_max   = max_req
        self._rate_janela = janela
        self._rate_ativo  = True
        return self

    def _verificar_rate(self, ip):
        """Retorna True se IP está dentro do limite, False se excedeu."""
        if not self._rate_ativo: return True
        agora = time.time()
        janela_inicio = agora - self._rate_janela
        if ip not in self._rate_limit:
            self._rate_limit[ip] = []
        # Remove timestamps antigos
        self._rate_limit[ip] = [t for t in self._rate_limit[ip] if t > janela_inicio]
        if len(self._rate_limit[ip]) >= self._rate_max:
            return False
        self._rate_limit[ip].append(agora)
        return True

    def usar(self, fn):
        self._middleware.append(fn)
        return self

    # ── Arquivos estáticos ────────────────────────────────────────────────────
    def estatico(self, url, pasta):
        self._estaticos[url] = pasta
        return self
    def arquivos(self, url, pasta): return self.estatico(url, pasta)

    # ── WebSocket ─────────────────────────────────────────────────────────────
    def ao_conexao_ws(self, handler):
        self.ws._handler_conexao = handler
        return self

    def ao_mensagem_ws(self, evento, handler):
        self.ws.ao_mensagem(evento, handler)
        return self

    # ── Proteção de rota ──────────────────────────────────────────────────────
    def proteger(self, rota, handler, nivel=None):
        def _handler_protegido(req):
            if not req.usuario:
                return _redirecionar("/login")
            if nivel and req.usuario.get('nivel') != nivel:
                return _html("<h2>Acesso negado</h2>", 403)
            return handler(req)
        return self.obter(rota, _handler_protegido)

    # ── Roteamento ────────────────────────────────────────────────────────────
    def _match_rota(self, method, path):
        for m, pattern, handler in self._rotas:
            if m != method and m != "*": continue
            params, ok = self._match_pattern(pattern, path)
            if ok: return handler, params
        return None, {}

    def _match_pattern(self, pattern, path):
        p_parts = pattern.rstrip("/").split("/")
        r_parts = path.rstrip("/").split("/")
        if len(p_parts) != len(r_parts): return {}, False
        params = {}
        for pp, rp in zip(p_parts, r_parts):
            if pp.startswith(":"): params[pp[1:]] = rp
            elif pp != rp: return {}, False
        return params, True

    def _servir_estatico(self, path):
        for prefix, pasta in self._estaticos.items():
            if path.startswith(prefix):
                rel  = path[len(prefix):].lstrip("/")
                full = os.path.join(pasta, rel)
                if os.path.isfile(full):
                    mime, _ = mimetypes.guess_type(full)
                    with open(full, "rb") as f: data = f.read()
                    return Resposta(data.decode("utf-8", errors="replace"),
                        200, mime or "application/octet-stream")
        return None

    def _obter_sessao(self, headers):
        cookies = headers.get("Cookie", "")
        for c in cookies.split(";"):
            c = c.strip()
            if c.startswith("sessao_id="):
                sid = c[len("sessao_id="):]
                dados = self.sessoes.obter(sid)
                return sid, dados or {}
        return None, {}

    def _handle(self, req_raw):
        # Arquivos estáticos
        st = self._servir_estatico(req_raw.path)
        if st: return st, None

        # Sessão + usuário
        sid, sessao_dados = self._obter_sessao(req_raw.headers)
        usuario = sessao_dados if sessao_dados.get('login') else None

        # Montar Requisicao
        req = Requisicao(
            req_raw.method, req_raw.path,
            req_raw.query, req_raw.body,
            req_raw.headers,
            sessao=sessao_dados,
            usuario=usuario
        )

        # Middleware
        for mw in self._middleware:
            resultado = mw(req)
            if resultado is not None:
                return resultado, sid

        # Match de rota
        handler, params = self._match_rota(req.method, req.path)
        req.parametros = params; req.params = params

        if handler is None:
            handler, params = self._match_rota("*", req.path)
            req.parametros = params; req.params = params

        if handler is None:
            if self._erro_404:
                try: return self._erro_404(req), sid
                except: pass
            return Resposta(self._pag_404(req.path), 404), sid

        try:
            resultado = handler(req)
            if isinstance(resultado, Resposta): return resultado, sid
            if isinstance(resultado, (dict, list)): return _json_resp(resultado), sid
            return _html(str(resultado)), sid
        except Exception as e:
            tb = traceback.format_exc()
            # Log error for debugging
            try:
                if not sys.is_finalizing():
                    print(f"  [ERR] {req.caminho}: {e}", flush=True)
                    print(tb[-300:], flush=True)
            except: pass
            if self._erro_500:
                try: return self._erro_500(req, str(e)), sid
                except: pass
            return Resposta(self._pag_500(str(e), tb), 500), sid

    def _pag_404(self, path):
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>404</title><style>body{{font-family:'Segoe UI',sans-serif;
background:#0F172A;color:#F1F5F9;display:flex;align-items:center;
justify-content:center;height:100vh;margin:0}}
.b{{text-align:center;background:#1E293B;padding:40px;border-radius:12px;
border:1px solid #334155}}h1{{font-size:72px;margin:0;color:#3B82F6}}
a{{color:#3B82F6}}</style></head>
<body><div class="b"><h1>404</h1><h2>Não encontrado</h2>
<p><code>{path}</code></p><a href="/">← Início</a></div></body></html>"""

    def _pag_500(self, erro, tb):
        tb_h = tb.replace('<','&lt;').replace('>','&gt;')
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>500</title><style>body{{font-family:'Segoe UI',sans-serif;
background:#0F172A;color:#F1F5F9;padding:24px}}
.h{{background:#7F1D1D;padding:16px;border-radius:8px;margin-bottom:16px}}
pre{{background:#1E293B;padding:16px;border-radius:8px;font-size:12px;
color:#94A3B8;white-space:pre-wrap;overflow:auto}}</style></head>
<body><div class="h"><b>⚠️ 500 — Erro Interno</b></div>
<p style="color:#EF4444">{erro}</p><pre>{tb_h}</pre></body></html>"""

    # ── HTTP Server ───────────────────────────────────────────────────────────
    def iniciar(self, bloquear=True):
        servidor_ref = self

        class RawReq:
            def __init__(self, method, path, query, body, headers):
                self.method  = method; self.path    = path
                self.query   = query;  self.body    = body
                self.headers = headers

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args): pass

            def _build(self, method):
                parsed = urlparse(self.path)
                path   = unquote(parsed.path)
                query  = {k: vs[0] if len(vs)==1 else vs
                         for k, vs in parse_qs(parsed.query).items()}
                body = ""
                if "Content-Length" in self.headers:
                    body = self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8","replace")
                return RawReq(method, path, query, body, dict(self.headers))

            def _send(self, resp, extra_headers=None):
                try:
                    body = resp.corpo.encode("utf-8") if isinstance(resp.corpo, str) else resp.corpo
                    self.send_response(resp.status)
                    self.send_header("Content-Type", resp.tipo)
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    for k, v in resp.cabecalhos.items():
                        self.send_header(k, v)
                    if extra_headers:
                        for k, v in extra_headers.items():
                            self.send_header(k, v)
                    self.end_headers()
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError, OSError): pass

            def handle_req(self, method):
                if sys.is_finalizing(): return
                t0  = time.time()
                raw = self._build(method)
                # Rate limiting
                ip = self.client_address[0]
                if not servidor_ref._verificar_rate(ip):
                    try:
                        resp = Resposta('{"erro":"Muitas requisições. Tente novamente."}',
                            429, 'application/json')
                        self._send(resp)
                    except: pass
                    return
                try:
                    resp, sid = servidor_ref._handle(raw)
                    extra = {}
                    if sid:
                        extra["Set-Cookie"] = servidor_ref.sessoes.cookie_header(sid)
                    self._send(resp, extra)
                    _log(method, raw.path, resp.status, int((time.time()-t0)*1000))
                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    try:
                        if not sys.is_finalizing():
                            print(f"  [HTTP ERR] {method} {raw.path}: {e}", flush=True)
                            print(tb[-600:], flush=True)
                    except: pass
                    try:
                        err_resp = Resposta(servidor_ref._pag_500(str(e), tb), 500)
                        self._send(err_resp)
                    except:
                        try: self.send_error(500, str(e)[:200])
                        except: pass

            def do_GET(self):
                # WebSocket upgrade?
                if (self.headers.get("Upgrade","").lower() == "websocket"):
                    self._handle_ws()
                    return
                self.handle_req("GET")

            def do_POST(self):   self.handle_req("POST")
            def do_PUT(self):    self.handle_req("PUT")
            def do_DELETE(self): self.handle_req("DELETE")
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods",
                    "GET,POST,PUT,DELETE,OPTIONS")
                self.send_header("Access-Control-Allow-Headers",
                    "Content-Type,Authorization,X-Requested-With")
                self.end_headers()

            def _handle_ws(self):
                """Handshake WebSocket simplificado (RFC 6455)."""
                try:
                    import hashlib, base64
                    key = self.headers.get("Sec-WebSocket-Key","")
                    magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
                    accept = base64.b64encode(
                        hashlib.sha1((key+magic).encode()).digest()
                    ).decode()
                    self.send_response(101)
                    self.send_header("Upgrade", "websocket")
                    self.send_header("Connection", "Upgrade")
                    self.send_header("Sec-WebSocket-Accept", accept)
                    self.end_headers()

                    import queue as _q
                    cid = servidor_ref.ws._novo_id()
                    q   = _q.Queue()
                    with servidor_ref.ws._lock:
                        servidor_ref.ws._clientes[cid] = {
                            'queue': q, 'sock': self.connection}

                    _log("WS", self.path, 101, extra="ws")

                    def _writer():
                        while True:
                            try:
                                msg = q.get(timeout=30)
                                if msg is None: break
                                _ws_send_frame(self.connection, msg)
                            except: break

                    wt = threading.Thread(target=_writer, daemon=True)
                    wt.start()

                    # Notify connection handler
                    ws_ref = servidor_ref.ws
                    if hasattr(ws_ref, '_handler_conexao') and ws_ref._handler_conexao:
                        try: ws_ref._handler_conexao({'id': cid, 'caminho': self.path})
                        except: pass

                    # Read loop
                    while True:
                        dados = _ws_recv_frame(self.connection)
                        if dados is None: break
                        try:
                            msg = json.loads(dados)
                            evento = msg.get('evento', 'mensagem')
                            handler = ws_ref._handlers.get(evento)
                            if handler:
                                handler({'id': cid, 'dados': msg.get('dados'), 'sala': msg.get('sala')})
                        except: pass

                    q.put(None)
                    with servidor_ref.ws._lock:
                        servidor_ref.ws._clientes.pop(cid, None)
                    _log("WS", self.path, 0, extra="ws")

                except Exception: pass

        _safe_print()
        url = f"http://localhost:{self._porta}"
        _safe_print(f"  {NEG}{AZUL}╔══════════════════════════════════════════╗{RESET}")
        _safe_print(f"  {NEG}{AZUL}║   ⚡  ADVAK 5.0 — SERVIDOR WEB          ║{RESET}")
        _safe_print(f"  {NEG}{AZUL}╚══════════════════════════════════════════╝{RESET}")
        _safe_print(f"  {VERDE}▶  Endereço:  {NEG}{url}{RESET}")
        if self._banco:
            _safe_print(f"  {VERDE}🗄️  Banco:    {NEG}{self._banco._arquivo}{RESET}")
        _safe_print(f"  {CINZA}   Rotas:{RESET}")
        for m, p, _ in self._rotas:
            _safe_print(f"  {CINZA}│{RESET}  {AZUL}{m:7}{RESET}  {p}")
        _safe_print(f"  {CINZA}   Ctrl+C para encerrar{RESET}")
        _safe_print(f"  {CINZA}{'─'*44}{RESET}")

        class ServidorReutilizavel(HTTPServer):
            allow_reuse_address = True
            allow_reuse_port    = True

        self._servidor = ServidorReutilizavel((self._host, self._porta), Handler)

        if self._auto_browser:
            def _abrir():
                time.sleep(0.8)
                webbrowser.open(url)
            threading.Thread(target=_abrir, daemon=True).start()

        if bloquear:
            try:
                self._servidor.serve_forever()
            except (KeyboardInterrupt, SystemExit): pass
            except Exception: pass
            finally:
                try: self._servidor.shutdown()
                except: pass
                try: self._servidor.server_close()
                except: pass
                if self._banco: self._banco.fechar()

    def parar(self):
        if self._servidor:
            try: self._servidor.shutdown()
            except: pass
            try: self._servidor.server_close()
            except: pass
            self._servidor = None
        if self._banco: self._banco.fechar()
        try:
            if not sys.is_finalizing():
                _safe_print("  Servidor parado.", flush=True)
        except: pass

# ── WebSocket Frame Encoding/Decoding ─────────────────────────────────────────
def _ws_send_frame(sock, mensagem):
    """Encode and send a WebSocket text frame."""
    try:
        dados = mensagem.encode("utf-8")
        n = len(dados)
        if n <= 125:
            header = bytes([0x81, n])
        elif n <= 65535:
            header = bytes([0x81, 126]) + n.to_bytes(2, 'big')
        else:
            header = bytes([0x81, 127]) + n.to_bytes(8, 'big')
        sock.sendall(header + dados)
    except: pass

def _ws_recv_frame(sock):
    """Receive and decode a WebSocket frame."""
    try:
        b = sock.recv(2)
        if len(b) < 2: return None
        opcode = b[0] & 0x0F
        if opcode == 8: return None  # close
        masked = (b[1] & 0x80) != 0
        length = b[1] & 0x7F
        if length == 126:
            length = int.from_bytes(sock.recv(2), 'big')
        elif length == 127:
            length = int.from_bytes(sock.recv(8), 'big')
        mask = sock.recv(4) if masked else b'\x00\x00\x00\x00'
        dados = bytearray(sock.recv(length))
        if masked:
            for i in range(len(dados)):
                dados[i] ^= mask[i % 4]
        return dados.decode("utf-8", errors="replace")
    except: return None

# ── Instância global ──────────────────────────────────────────────────────────
_servidor_global = AdvakServer()
def _get_servidor(): return _servidor_global
