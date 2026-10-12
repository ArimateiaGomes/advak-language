"""
Advak 3.0 — Servidor HTTP Nativo
Permite criar servidores web diretamente em código .dk

Sintaxe no código .dk:
  servidor.rota("/", "GET", fn)
  servidor.rota("/api/usuarios", "GET", fn)
  servidor.rota("/api/usuarios", "POST", fn)
  servidor.iniciar(porta=8080)
  servidor.parar()

  // Retorno nas rotas:
  retornar servidor.json({dados: [...]})
  retornar servidor.html("<h1>Olá</h1>")
  retornar servidor.texto("OK")
  retornar servidor.redirecionar("/outra-pagina")
  retornar servidor.arquivo("index.html")
"""

import json
import os
import sys
import threading
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from functools import partial


class AdvakRequest:
    """Objeto de requisição disponível nas rotas."""
    def __init__(self, method, path, query, headers, body, params=None):
        self.metodo   = method
        self.caminho  = path
        self.query    = query      # dict de query params
        self.headers  = headers    # dict de cabeçalhos
        self.corpo    = body       # str ou dict (se JSON)
        self.params   = params or {}  # parâmetros de rota (/user/:id)

    def __repr__(self):
        return f"<Requisição {self.metodo} {self.caminho}>"


class AdvakResponse:
    """Objeto de resposta para as rotas."""
    def __init__(self, body='', status=200, content_type='text/plain', headers=None):
        self.body         = body
        self.status       = status
        self.content_type = content_type
        self.headers      = headers or {}

    def __repr__(self):
        return f"<Resposta {self.status}>"


class AdvakHTTPServer:
    """
    Servidor HTTP nativo da linguagem Advak.
    Exposto como objeto global 'servidor' nos programas .dk
    """

    def __init__(self):
        self._rotas      = []   # [(method, pattern, handler, param_names)]
        self._middlewares= []   # [fn]
        self._servidor   = None
        self._thread     = None
        self._porta      = 8080
        self._host       = 'localhost'
        self._dir_static = 'public'
        self._templates  = {}
        self._running    = False
        self._not_found_handler  = None
        self._error_handler      = None

    # ── Registro de rotas ────────────────────────────────────────────────────

    def rota(self, caminho, metodo, handler):
        """
        servidor.rota("/", "GET", fn)
        servidor.rota("/api/users/:id", "GET", fn)
        """
        metodo = metodo.upper()
        pattern, param_names = self._parse_pattern(caminho)
        self._rotas.append((metodo, pattern, caminho, handler, param_names))
        return self

    def get(self, caminho, handler):
        return self.rota(caminho, 'GET', handler)

    def post(self, caminho, handler):
        return self.rota(caminho, 'POST', handler)

    def put(self, caminho, handler):
        return self.rota(caminho, 'PUT', handler)

    def delete(self, caminho, handler):
        return self.rota(caminho, 'DELETE', handler)

    def middleware(self, fn):
        """Adiciona middleware executado antes de cada rota."""
        self._middlewares.append(fn)
        return self

    def nao_encontrado(self, handler):
        """Handler para 404."""
        self._not_found_handler = handler
        return self

    def erro(self, handler):
        """Handler para erros 500."""
        self._error_handler = handler
        return self

    # ── Respostas ────────────────────────────────────────────────────────────

    def json(self, dados, status=200):
        """retornar servidor.json({nome: 'Ana'})"""
        body = json.dumps(dados, ensure_ascii=False, default=str)
        return AdvakResponse(body, status, 'application/json; charset=utf-8')

    def html(self, conteudo, status=200):
        """retornar servidor.html('<h1>Olá</h1>')"""
        return AdvakResponse(conteudo, status, 'text/html; charset=utf-8')

    def texto(self, conteudo, status=200):
        """retornar servidor.texto('OK')"""
        return AdvakResponse(str(conteudo), status, 'text/plain; charset=utf-8')

    def redirecionar(self, url, status=302):
        """retornar servidor.redirecionar('/login')"""
        return AdvakResponse('', status, 'text/plain',
                             headers={'Location': url})

    def arquivo(self, caminho):
        """retornar servidor.arquivo('index.html')"""
        paths = [
            caminho,
            os.path.join(self._dir_static, caminho),
        ]
        for p in paths:
            if os.path.exists(p):
                with open(p, 'rb') as f:
                    content = f.read()
                mime, _ = mimetypes.guess_type(p)
                return AdvakResponse(content.decode('utf-8', errors='replace'),
                                     200, mime or 'application/octet-stream')
        return AdvakResponse(f'Arquivo não encontrado: {caminho}', 404, 'text/plain')

    def renderizar(self, template_nome, variaveis=None):
        """
        Renderiza um template HTML simples com {{variavel}}.
        retornar servidor.renderizar("index.html", {titulo: "Página"})
        """
        paths = [
            template_nome,
            os.path.join('templates', template_nome),
            os.path.join(self._dir_static, template_nome),
        ]
        content = None
        for p in paths:
            if os.path.exists(p):
                with open(p, encoding='utf-8') as f:
                    content = f.read()
                break

        if content is None:
            return AdvakResponse(f'Template não encontrado: {template_nome}', 404, 'text/plain')

        # Substitui {{variavel}} pelo valor
        if variaveis:
            import re
            def replacer(m):
                key = m.group(1).strip()
                val = variaveis.get(key, m.group(0))
                return str(val)
            content = re.sub(r'\{\{([^}]+)\}\}', replacer, content)

        return AdvakResponse(content, 200, 'text/html; charset=utf-8')

    # ── Iniciar / Parar ──────────────────────────────────────────────────────

    def iniciar(self, porta=8080, host='localhost', dir_static='public', bloqueante=True):
        self._porta      = porta
        self._host       = host
        self._dir_static = dir_static
        self._running    = True

        handler = partial(AdvakRequestHandler, self)
        self._servidor = HTTPServer((host, porta), handler)

        print(f'\n🌐 Advak HTTP Server rodando em http://{host}:{porta}')
        print(f'   Arquivos estáticos: ./{dir_static}/')
        print(f'   Rotas registradas: {len(self._rotas)}')
        for m, _, caminho, _, _ in self._rotas:
            print(f'   {m.ljust(6)} {caminho}')
        print('   Pressione Ctrl+C para parar\n')

        if bloqueante:
            try:
                self._servidor.serve_forever()
            except KeyboardInterrupt:
                self.parar()
        else:
            self._thread = threading.Thread(target=self._servidor.serve_forever, daemon=True)
            self._thread.start()
            return f'✅ Servidor iniciado em http://{host}:{porta}'

    def parar(self):
        if self._servidor:
            self._servidor.shutdown()
            self._running = False
            print('\n⏹  Servidor parado.')

    # ── Roteamento interno ───────────────────────────────────────────────────

    def _parse_pattern(self, caminho):
        """Converte /user/:id em regex e extrai nomes dos params."""
        import re
        param_names = re.findall(r':(\w+)', caminho)
        pattern = re.sub(r':(\w+)', r'([^/]+)', caminho)
        pattern = f'^{pattern}$'
        return pattern, param_names

    def _match_route(self, method, path):
        """Encontra handler para método + caminho."""
        import re
        for rmethod, pattern, _, handler, param_names in self._rotas:
            if rmethod != method and rmethod != 'ANY':
                continue
            m = re.match(pattern, path)
            if m:
                params = dict(zip(param_names, m.groups()))
                return handler, params
        return None, {}

    def _dispatch(self, method, path, query, headers, body):
        """Despacha requisição para o handler correto."""
        import asyncio

        # Arquivos estáticos
        static_path = os.path.join(self._dir_static, path.lstrip('/'))
        if method == 'GET' and os.path.isfile(static_path):
            with open(static_path, 'rb') as f:
                content = f.read()
            mime, _ = mimetypes.guess_type(static_path)
            return AdvakResponse(content.decode('utf-8', errors='replace'),
                                 200, mime or 'text/plain')

        handler, params = self._match_route(method, path)

        if handler is None:
            if self._not_found_handler:
                req = AdvakRequest(method, path, query, headers, body, {})
                try:
                    return self._call_handler(self._not_found_handler, req)
                except:
                    pass
            return AdvakResponse(
                json.dumps({'erro': f'Rota não encontrada: {method} {path}'},
                           ensure_ascii=False),
                404, 'application/json; charset=utf-8'
            )

        # Parse body JSON se necessário
        parsed_body = body
        if headers.get('content-type', '').startswith('application/json') and body:
            try:
                parsed_body = json.loads(body)
            except:
                pass

        req = AdvakRequest(method, path, query, headers, parsed_body, params)

        # Executa middlewares
        for mw in self._middlewares:
            result = self._call_handler(mw, req)
            if isinstance(result, AdvakResponse):
                return result  # middleware interrompeu

        # Executa handler da rota
        try:
            result = self._call_handler(handler, req)
            if isinstance(result, AdvakResponse):
                return result
            if isinstance(result, dict):
                return self.json(result)
            if isinstance(result, str):
                if result.strip().startswith('<'):
                    return self.html(result)
                return self.texto(result)
            if result is None:
                return self.json({'ok': True})
            return self.texto(str(result))
        except Exception as e:
            if self._error_handler:
                req.erro = str(e)
                try:
                    return self._call_handler(self._error_handler, req)
                except:
                    pass
            return AdvakResponse(
                json.dumps({'erro': str(e)}, ensure_ascii=False),
                500, 'application/json; charset=utf-8'
            )

    def _call_handler(self, handler, req):
        """Chama um handler (função Python ou AdvakFunction)."""
        import asyncio
        if callable(handler):
            result = handler(req)
            if asyncio.iscoroutine(result):
                loop = asyncio.new_event_loop()
                result = loop.run_until_complete(result)
                loop.close()
            return result
        # AdvakFunction — chama via wrapper
        if hasattr(handler, 'params') and hasattr(handler, 'body'):
            from advak_interpreter import AdvakInterpreter, Scope
            # Execução síncrona de AdvakFunction
            loop = asyncio.new_event_loop()
            interp = AdvakInterpreter.__new__(AdvakInterpreter)
            interp.ast = []
            interp.global_scope = handler.closure
            interp.ai_api_key = None
            interp.db = None
            result = loop.run_until_complete(interp._call_fn(handler, [req], handler.closure))
            loop.close()
            return result
        return None


class AdvakRequestHandler(BaseHTTPRequestHandler):
    """Handler HTTP interno do Advak."""

    def __init__(self, advak_server, *args, **kwargs):
        self._advak = advak_server
        super().__init__(*args, **kwargs)

    def log_message(self, fmt, *args):
        # Log colorido
        status = args[1] if len(args) > 1 else ''
        color = '\033[32m' if str(status).startswith('2') else \
                '\033[33m' if str(status).startswith('3') else \
                '\033[31m'
        reset = '\033[0m'
        print(f"  {color}{self.command:<7}{reset} {self.path:<40} {color}{status}{reset}")

    def _handle(self):
        parsed  = urlparse(self.path)
        path    = parsed.path
        query   = {k: v[0] if len(v)==1 else v
                   for k, v in parse_qs(parsed.query).items()}
        headers = dict(self.headers)

        # Lê body
        body = ''
        length = int(self.headers.get('Content-Length', 0))
        if length > 0:
            body = self.rfile.read(length).decode('utf-8', errors='replace')

        resp = self._advak._dispatch(self.command, path, query, headers, body)

        # Envia resposta
        self.send_response(resp.status)
        self.send_header('Content-Type', resp.content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        for k, v in resp.headers.items():
            self.send_header(k, v)

        body_bytes = resp.body.encode('utf-8') if isinstance(resp.body, str) else resp.body
        self.send_header('Content-Length', len(body_bytes))
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_GET(self):    self._handle()
    def do_POST(self):   self._handle()
    def do_PUT(self):    self._handle()
    def do_DELETE(self): self._handle()
    def do_PATCH(self):  self._handle()
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        self.end_headers()
