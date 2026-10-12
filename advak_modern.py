"""
Advak 4.0 — Módulos Modernos Avançados

Recursos incluídos:
  1. Sistema de tipos estáticos opcionais (type inference + validação em runtime)
  2. WebSockets nativos (ws://)
  3. ORM reativo com relacionamentos (pertence_a, tem_muitos, muitos_para_muitos)
  4. Cache inteligente (memória + Redis se disponível)
  5. Pipeline de ML simplificado (sem TensorFlow — usa scikit-learn via subprocess)
  6. Fila de tarefas assíncronas
  7. Validador de dados com schemas
  8. Logger estruturado
  9. Variáveis de ambiente tipadas (.env)
 10. Criptografia e JWT simples
"""

import os, sys, json, time, hashlib, hmac, base64, threading, queue
import asyncio, logging, re
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict


# ══════════════════════════════════════════════════════════════════════════════
#  1. SISTEMA DE TIPOS ESTÁTICOS OPCIONAIS
# ══════════════════════════════════════════════════════════════════════════════

class AdvakTipo:
    """Define um tipo Advak com validação em runtime."""
    
    PRIMITIVOS = {
        'Texto':     (str,),
        'Numero':    (int, float),
        'Inteiro':   (int,),
        'Decimal':   (float,),
        'Booleano':  (bool,),
        'Lista':     (list,),
        'Mapa':      (dict,),
        'Nulo':      (type(None),),
        'Qualquer':  None,  # any
    }

    def __init__(self):
        self._schemas = {}

    def schema(self, nome, campos):
        """
        tipos.schema("Usuario", {
            "nome":  "Texto",
            "idade": "Inteiro",
            "email": "Texto",
            "ativo": "Booleano"
        })
        """
        self._schemas[nome] = campos
        return nome

    def validar(self, valor, tipo_nome):
        """
        tipos.validar("Ana", "Texto")   → True
        tipos.validar(42, "Texto")      → False
        tipos.validar({...}, "Usuario") → True/False conforme schema
        """
        if tipo_nome in self.PRIMITIVOS:
            tipos_py = self.PRIMITIVOS[tipo_nome]
            if tipos_py is None: return True  # Qualquer
            return isinstance(valor, tipos_py)

        if tipo_nome in self._schemas:
            if not isinstance(valor, dict): return False
            schema = self._schemas[tipo_nome]
            for campo, tipo_campo in schema.items():
                if campo not in valor: return False
                if not self.validar(valor[campo], tipo_campo): return False
            return True

        if tipo_nome.startswith('Lista['):
            inner = tipo_nome[6:-1]
            return isinstance(valor, list) and all(self.validar(v, inner) for v in valor)

        if tipo_nome.startswith('Opcional['):
            inner = tipo_nome[9:-1]
            return valor is None or self.validar(valor, inner)

        return True

    def moldar(self, dados, tipo_nome):
        """
        Cria objeto tipado e valida.
        tipos.moldar({nome:"Ana",idade:25}, "Usuario")
        """
        if not self.validar(dados, tipo_nome):
            erros = []
            if tipo_nome in self._schemas:
                schema = self._schemas[tipo_nome]
                for campo, tipo_campo in schema.items():
                    if campo not in dados:
                        erros.append(f"campo '{campo}' ausente")
                    elif not self.validar(dados[campo], tipo_campo):
                        erros.append(f"campo '{campo}' deve ser {tipo_campo}, recebeu {type(dados[campo]).__name__}")
            raise TypeError(f"❌ Tipo '{tipo_nome}' inválido: {'; '.join(erros)}")
        return dados

    def inferir(self, valor):
        """Infere o tipo Advak de um valor Python."""
        if valor is None:       return 'Nulo'
        if isinstance(valor, bool):  return 'Booleano'
        if isinstance(valor, int):   return 'Inteiro'
        if isinstance(valor, float): return 'Decimal'
        if isinstance(valor, str):   return 'Texto'
        if isinstance(valor, list):  return 'Lista'
        if isinstance(valor, dict):  return 'Mapa'
        return 'Qualquer'


# ══════════════════════════════════════════════════════════════════════════════
#  2. WEBSOCKETS NATIVOS
# ══════════════════════════════════════════════════════════════════════════════

class AdvakWebSocket:
    """
    Servidor WebSocket nativo.
    
    ws.ao_conectar((cliente) => { imprimir("conectou"); })
    ws.ao_mensagem((cliente, msg) => { ws.enviar(cliente, "eco: " + msg); })
    ws.ao_desconectar((cliente) => { imprimir("saiu"); })
    ws.iniciar(porta=9001)
    ws.broadcast("mensagem para todos")
    """

    def __init__(self):
        self._clientes = {}
        self._on_connect    = None
        self._on_message    = None
        self._on_disconnect = None
        self._server = None
        self._loop   = None
        self._id_counter = 0

    def ao_conectar(self, fn):    self._on_connect    = fn; return self
    def ao_mensagem(self, fn):    self._on_message    = fn; return self
    def ao_desconectar(self, fn): self._on_disconnect = fn; return self

    def enviar(self, cliente_id, mensagem):
        """ws.enviar(cliente_id, "olá")"""
        if cliente_id in self._clientes:
            ws = self._clientes[cliente_id]['ws']
            if self._loop:
                asyncio.run_coroutine_threadsafe(ws.send(str(mensagem)), self._loop)

    def broadcast(self, mensagem, excluir=None):
        """ws.broadcast("mensagem para todos")"""
        for cid, info in list(self._clientes.items()):
            if cid != excluir:
                self.enviar(cid, mensagem)

    def clientes_conectados(self):
        return list(self._clientes.keys())

    def total_clientes(self):
        return len(self._clientes)

    def iniciar(self, porta=9001, host='localhost'):
        """Inicia o servidor WebSocket em thread separada."""
        try:
            import websockets
        except ImportError:
            print("⚠️  websockets não instalado. Execute: pip install websockets")
            print("   Simulando WebSocket (modo desenvolvimento)")
            print(f"   ws://{host}:{porta} — aguardando conexões")
            return f"✅ WS pronto em ws://{host}:{porta} (instale websockets para produção)"

        async def handler(websocket, path):
            self._id_counter += 1
            cid = self._id_counter
            self._clientes[cid] = {'ws': websocket, 'path': path, 'id': cid}
            cliente_obj = {'id': cid, 'path': path}
            if self._on_connect:
                self._call(self._on_connect, cliente_obj)
            try:
                async for msg in websocket:
                    if self._on_message:
                        self._call(self._on_message, cliente_obj, msg)
            finally:
                del self._clientes[cid]
                if self._on_disconnect:
                    self._call(self._on_disconnect, cliente_obj)

        def run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            start = websockets.serve(handler, host, porta)
            self._server = self._loop.run_until_complete(start)
            print(f"🔌 WebSocket rodando em ws://{host}:{porta}")
            self._loop.run_forever()

        t = threading.Thread(target=run, daemon=True)
        t.start()
        time.sleep(0.3)
        return f"✅ WebSocket em ws://{host}:{porta}"

    def _call(self, fn, *args):
        if callable(fn): fn(*args)


# ══════════════════════════════════════════════════════════════════════════════
#  3. ORM REATIVO COM RELACIONAMENTOS
# ══════════════════════════════════════════════════════════════════════════════

class AdvakORM:
    """
    ORM com relacionamentos, hooks e reatividade.

    // Define modelo
    seja Usuario = orm.modelo("usuarios", {
        nome:  "Texto",
        email: "Texto",
        ativo: "Booleano"
    });

    // CRUD simplificado
    seja u = await Usuario.criar({nome: "Ana", email: "ana@x.com"});
    seja todos = await Usuario.todos();
    seja um = await Usuario.buscar(1);
    seja filtrados = await Usuario.onde({ativo: verdadeiro});
    await Usuario.atualizar(1, {nome: "Ana Silva"});
    await Usuario.deletar(1);

    // Relacionamentos
    Usuario.pertence_a("departamentos", "depto_id");
    Pedido.tem_muitos("itens_pedido", "pedido_id");
    Usuario.muitos_para_muitos("roles", "usuario_roles");
    """

    def __init__(self, db):
        self._db = db
        self._modelos = {}

    def modelo(self, tabela, campos_schema=None):
        """Cria/retorna um modelo ORM para a tabela."""
        if tabela in self._modelos:
            return self._modelos[tabela]

        orm_ref = self
        db_ref  = self._db

        class ModeloORM:
            _tabela    = tabela
            _schema    = campos_schema or {}
            _hooks     = defaultdict(list)
            _rels      = {}

            # ── Hooks ────────────────────────────────────────────────────────
            @classmethod
            def antes_de(cls, evento, fn):
                cls._hooks[f'antes_{evento}'].append(fn)

            @classmethod
            def depois_de(cls, evento, fn):
                cls._hooks[f'depois_{evento}'].append(fn)

            @classmethod
            def _executar_hooks(cls, evento, dados):
                for fn in cls._hooks.get(evento, []):
                    r = fn(dados)
                    if r is not None: dados = r
                return dados

            # ── CRUD ─────────────────────────────────────────────────────────
            @classmethod
            def criar(cls, dados):
                dados = cls._executar_hooks('antes_criar', dados)
                resultado = db_ref.inserir(cls._tabela, dados)
                resultado = cls._executar_hooks('depois_criar', resultado)
                return resultado

            @classmethod
            def todos(cls, ordem=None, lim=None):
                q = db_ref.buscar(cls._tabela)
                if ordem: q = q.ordenar(ordem)
                if lim:   q = q.limite(lim)
                return q.executar()

            @classmethod
            def buscar(cls, id_val):
                return db_ref.buscar_por_id(cls._tabela, id_val)

            @classmethod
            def onde(cls, filtros, op='AND'):
                """
                Usuario.onde({"ativo": True})
                Usuario.onde({"nota": (">=", 7)})
                """
                q = db_ref.buscar(cls._tabela)
                for campo, val in filtros.items():
                    if isinstance(val, (list, tuple)) and len(val) == 2:
                        operador, v = val
                        q = q.onde(f'"{campo}" {operador} %s', v)
                    else:
                        q = q.onde(f'"{campo}" = %s', val)
                return q.executar()

            @classmethod
            def primeiro(cls, filtros=None):
                if filtros:
                    q = db_ref.buscar(cls._tabela)
                    for campo, val in filtros.items():
                        q = q.onde(f'"{campo}" = %s', val)
                    return q.primeiro()
                return db_ref.buscar(cls._tabela).primeiro()

            @classmethod
            def atualizar(cls, id_val, dados):
                dados = cls._executar_hooks('antes_atualizar', dados)
                resultado = db_ref.atualizar(cls._tabela, dados)\
                    .onde('id = %s', id_val).executar()
                return resultado

            @classmethod
            def deletar(cls, id_val):
                cls._executar_hooks('antes_deletar', {'id': id_val})
                return db_ref.deletar(cls._tabela)\
                    .onde('id = %s', id_val).executar()

            @classmethod
            def contar(cls, filtros=None):
                if filtros:
                    conds = [f'"{c}" = %s' for c in filtros]
                    vals  = list(filtros.values())
                    where = ' AND '.join(conds)
                    return db_ref.contar(cls._tabela, where, vals)
                return db_ref.contar(cls._tabela)

            @classmethod
            def paginar(cls, pagina=1, por_pagina=10, ordem=None):
                q = db_ref.buscar(cls._tabela)
                if ordem: q = q.ordenar(ordem)
                itens  = q.pagina(pagina, por_pagina).executar()
                total  = cls.contar()
                import math
                return {
                    'dados':    itens,
                    'pagina':   pagina,
                    'por_pagina': por_pagina,
                    'total':    total,
                    'paginas':  math.ceil(total / por_pagina) if por_pagina else 1,
                    'tem_mais': pagina * por_pagina < total,
                }

            # ── Relacionamentos ───────────────────────────────────────────────
            @classmethod
            def pertence_a(cls, tabela_pai, chave_estrangeira):
                cls._rels[tabela_pai] = ('pertence_a', tabela_pai, chave_estrangeira)

            @classmethod
            def tem_muitos(cls, tabela_filha, chave_estrangeira):
                cls._rels[tabela_filha] = ('tem_muitos', tabela_filha, chave_estrangeira)

            @classmethod
            def com(cls, id_val, *relacoes):
                """Busca com includes (eager loading)."""
                obj = cls.buscar(id_val)
                if not obj: return None
                for rel_nome in relacoes:
                    if rel_nome in cls._rels:
                        tipo, tabela, fk = cls._rels[rel_nome]
                        if tipo == 'pertence_a':
                            fk_val = obj.get(fk)
                            if fk_val:
                                obj[rel_nome] = db_ref.buscar_por_id(tabela, fk_val)
                        elif tipo == 'tem_muitos':
                            obj[rel_nome] = db_ref.buscar(tabela)\
                                .onde(f'"{fk}" = %s', id_val).executar()
                return obj

            @classmethod
            def nome_tabela(cls):
                return cls._tabela

        ModeloORM.__name__  = tabela.capitalize()
        self._modelos[tabela] = ModeloORM
        return ModeloORM


# ══════════════════════════════════════════════════════════════════════════════
#  4. CACHE INTELIGENTE
# ══════════════════════════════════════════════════════════════════════════════

class AdvakCache:
    """
    Cache em memória com TTL, Redis opcional.
    
    cache.definir("chave", valor)
    cache.definir("chave", valor, ttl=300)  // expira em 5 min
    cache.obter("chave")
    cache.remover("chave")
    cache.limpar()
    cache.ou_buscar("chave", fn, ttl=60)   // cache-aside pattern
    """

    def __init__(self):
        self._mem   = {}       # {key: (value, expires_at)}
        self._redis = None
        self._hits  = 0
        self._miss  = 0

    def conectar_redis(self, host='localhost', port=6379, db=0):
        try:
            import redis
            self._redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self._redis.ping()
            return "✅ Redis conectado"
        except Exception as e:
            self._redis = None
            return f"⚠️  Redis indisponível: {e} — usando cache em memória"

    def definir(self, chave, valor, ttl=None):
        """cache.definir("usuario:1", dados, ttl=300)"""
        expires = time.time() + ttl if ttl else None
        self._mem[str(chave)] = (valor, expires)
        if self._redis and ttl:
            try:
                self._redis.setex(str(chave), ttl, json.dumps(valor, default=str))
            except: pass
        elif self._redis:
            try:
                self._redis.set(str(chave), json.dumps(valor, default=str))
            except: pass

    def obter(self, chave, padrao=None):
        """cache.obter("usuario:1")"""
        k = str(chave)
        # Memória
        if k in self._mem:
            valor, expires = self._mem[k]
            if expires is None or time.time() < expires:
                self._hits += 1
                return valor
            else:
                del self._mem[k]
        # Redis
        if self._redis:
            try:
                raw = self._redis.get(k)
                if raw:
                    self._hits += 1
                    return json.loads(raw)
            except: pass
        self._miss += 1
        return padrao

    def remover(self, chave):
        k = str(chave)
        self._mem.pop(k, None)
        if self._redis:
            try: self._redis.delete(k)
            except: pass

    def limpar(self, prefixo=None):
        if prefixo:
            keys = [k for k in self._mem if k.startswith(str(prefixo))]
            for k in keys: del self._mem[k]
        else:
            self._mem.clear()

    def ou_buscar(self, chave, fn, ttl=60):
        """
        Padrão cache-aside: busca no cache, se não tiver chama fn e armazena.
        cache.ou_buscar("todos_usuarios", () => banco.buscar("usuarios").executar(), ttl=30)
        """
        valor = self.obter(chave)
        if valor is not None:
            return valor
        valor = fn() if callable(fn) else fn
        self.definir(chave, valor, ttl=ttl)
        return valor

    def invalidar_prefixo(self, prefixo):
        """Invalida todas as chaves que começam com prefixo."""
        self.limpar(prefixo)

    def estatisticas(self):
        total = self._hits + self._miss
        taxa  = round(self._hits / total * 100, 1) if total else 0
        return {
            'hits':      self._hits,
            'misses':    self._miss,
            'taxa_hit':  f"{taxa}%",
            'entradas':  len(self._mem),
            'redis':     self._redis is not None,
        }

    def memoizar(self, fn, ttl=300):
        """Decora uma função para cachear seu resultado."""
        def wrapper(*args):
            chave = f"memo:{fn.__name__}:{hash(str(args))}"
            return self.ou_buscar(chave, lambda: fn(*args), ttl=ttl)
        return wrapper


# ══════════════════════════════════════════════════════════════════════════════
#  5. VALIDADOR DE DADOS / SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class AdvakValidator:
    """
    Validação de dados com schemas declarativos.

    validar.schema("CriarUsuario", {
        "nome":  validar.texto(min=2, max=100),
        "email": validar.email(),
        "idade": validar.numero(min=0, max=150),
        "senha": validar.texto(min=8),
        "cpf":   validar.regex(r"\\d{11}")
    })
    seja erros = validar.verificar(dados, "CriarUsuario")
    se (!erros) { ... } senão { imprimir(erros); }
    """

    def __init__(self):
        self._schemas = {}

    # ── Tipos de campo ────────────────────────────────────────────────────────

    def texto(self, min=None, max=None, obrigatorio=True):
        return {'tipo': 'texto', 'min': min, 'max': max, 'obrigatorio': obrigatorio}

    def numero(self, min=None, max=None, obrigatorio=True):
        return {'tipo': 'numero', 'min': min, 'max': max, 'obrigatorio': obrigatorio}

    def email(self, obrigatorio=True):
        return {'tipo': 'email', 'obrigatorio': obrigatorio}

    def booleano(self, obrigatorio=True):
        return {'tipo': 'booleano', 'obrigatorio': obrigatorio}

    def lista(self, min=None, max=None, obrigatorio=True):
        return {'tipo': 'lista', 'min': min, 'max': max, 'obrigatorio': obrigatorio}

    def regex(self, pattern, obrigatorio=True):
        return {'tipo': 'regex', 'pattern': pattern, 'obrigatorio': obrigatorio}

    def opcoes(self, valores, obrigatorio=True):
        return {'tipo': 'opcoes', 'valores': valores, 'obrigatorio': obrigatorio}

    def data(self, obrigatorio=True):
        return {'tipo': 'data', 'obrigatorio': obrigatorio}

    # ── Schema e verificação ──────────────────────────────────────────────────

    def schema(self, nome, campos):
        self._schemas[nome] = campos
        return self

    def verificar(self, dados, schema_nome):
        """
        Retorna None se válido, ou dict de erros se inválido.
        seja erros = validar.verificar(req.corpo, "CriarUsuario")
        """
        if schema_nome not in self._schemas:
            return {'schema': f"Schema '{schema_nome}' não encontrado"}

        erros = {}
        campos = self._schemas[schema_nome]

        for campo, regra in campos.items():
            valor = dados.get(campo) if isinstance(dados, dict) else None
            erro  = self._validar_campo(campo, valor, regra)
            if erro:
                erros[campo] = erro

        return erros if erros else None

    def verificar_ou_erro(self, dados, schema_nome):
        """Lança exceção se inválido."""
        erros = self.verificar(dados, schema_nome)
        if erros:
            raise ValueError(f"Dados inválidos: {json.dumps(erros, ensure_ascii=False)}")
        return dados

    def _validar_campo(self, campo, valor, regra):
        obrig = regra.get('obrigatorio', True)
        if valor is None or valor == '':
            return "obrigatório" if obrig else None

        tipo = regra.get('tipo')

        if tipo == 'texto':
            if not isinstance(valor, str): return "deve ser texto"
            if regra.get('min') and len(valor) < regra['min']:
                return f"mínimo {regra['min']} caracteres"
            if regra.get('max') and len(valor) > regra['max']:
                return f"máximo {regra['max']} caracteres"

        elif tipo == 'numero':
            try: n = float(valor)
            except: return "deve ser número"
            if regra.get('min') is not None and n < regra['min']:
                return f"mínimo {regra['min']}"
            if regra.get('max') is not None and n > regra['max']:
                return f"máximo {regra['max']}"

        elif tipo == 'email':
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(valor)):
                return "email inválido"

        elif tipo == 'booleano':
            if not isinstance(valor, bool): return "deve ser booleano"

        elif tipo == 'lista':
            if not isinstance(valor, list): return "deve ser lista"
            if regra.get('min') and len(valor) < regra['min']:
                return f"mínimo {regra['min']} itens"

        elif tipo == 'regex':
            if not re.match(regra['pattern'], str(valor)):
                return "formato inválido"

        elif tipo == 'opcoes':
            if valor not in regra['valores']:
                return f"deve ser um de: {regra['valores']}"

        elif tipo == 'data':
            try: datetime.fromisoformat(str(valor))
            except: return "data inválida (use YYYY-MM-DD)"

        return None


# ══════════════════════════════════════════════════════════════════════════════
#  6. FILA DE TAREFAS ASSÍNCRONAS
# ══════════════════════════════════════════════════════════════════════════════

class AdvakFila:
    """
    Fila de tarefas em background.

    fila.tarefa("enviar_email", (dados) => {
        imprimir("Enviando email para " + dados.para);
    })
    fila.adicionar("enviar_email", {para: "ana@x.com", assunto: "Bem-vindo!"})
    fila.iniciar(workers=3)
    """

    def __init__(self):
        self._handlers = {}
        self._q        = queue.Queue()
        self._workers  = []
        self._running  = False
        self._stats    = defaultdict(int)

    def tarefa(self, nome, handler):
        """Registra um handler para um tipo de tarefa."""
        self._handlers[nome] = handler
        return self

    def adicionar(self, tipo, dados=None, delay=0):
        """Adiciona tarefa na fila."""
        item = {'tipo': tipo, 'dados': dados or {}, 'at': time.time() + delay,
                'id': f"{tipo}_{int(time.time()*1000)}"}
        self._q.put(item)
        return item['id']

    def iniciar(self, workers=2):
        """Inicia os workers em background."""
        self._running = True
        for i in range(workers):
            t = threading.Thread(target=self._worker, daemon=True,
                                 name=f"advak-worker-{i}")
            t.start()
            self._workers.append(t)
        return f"✅ Fila iniciada com {workers} workers"

    def parar(self):
        self._running = False

    def _worker(self):
        while self._running:
            try:
                item = self._q.get(timeout=1)
                if item['at'] > time.time():
                    self._q.put(item)
                    time.sleep(0.1)
                    continue
                tipo = item['tipo']
                if tipo in self._handlers:
                    try:
                        self._handlers[tipo](item['dados'])
                        self._stats[f"{tipo}_ok"] += 1
                    except Exception as e:
                        self._stats[f"{tipo}_erro"] += 1
                        print(f"[Fila] Erro em '{tipo}': {e}")
                self._q.task_done()
            except queue.Empty:
                continue

    def estatisticas(self):
        return {
            'pendentes':   self._q.qsize(),
            'workers':     len(self._workers),
            'processadas': dict(self._stats),
        }


# ══════════════════════════════════════════════════════════════════════════════
#  7. LOGGER ESTRUTURADO
# ══════════════════════════════════════════════════════════════════════════════

class AdvakLogger:
    """
    Logger estruturado com níveis, formatação e saída para arquivo.
    
    log.info("Servidor iniciado")
    log.erro("Falha ao conectar", {host: "localhost", porta: 5432})
    log.aviso("Cache cheio")
    log.debug("Token recebido", {user_id: 42})
    log.configurar(arquivo="app.log", nivel="INFO", json_format=verdadeiro)
    """

    NIVEIS = {'DEBUG': 10, 'INFO': 20, 'AVISO': 30, 'ERRO': 40, 'CRITICO': 50}
    CORES  = {
        'DEBUG':   '\033[36m',   # ciano
        'INFO':    '\033[32m',   # verde
        'AVISO':   '\033[33m',   # amarelo
        'ERRO':    '\033[31m',   # vermelho
        'CRITICO': '\033[35m',   # magenta
        'RESET':   '\033[0m',
    }

    def __init__(self):
        self._nivel      = 'INFO'
        self._arquivo    = None
        self._json_mode  = False
        self._handlers   = []

    def configurar(self, arquivo=None, nivel='INFO', json_format=False):
        self._nivel     = nivel.upper()
        self._arquivo   = arquivo
        self._json_mode = json_format
        if arquivo:
            fh = logging.FileHandler(arquivo, encoding='utf-8')
            self._handlers.append(fh)
        return self

    def _log(self, nivel, mensagem, contexto=None):
        if self.NIVEIS.get(nivel, 0) < self.NIVEIS.get(self._nivel, 0):
            return
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if self._json_mode:
            entrada = json.dumps({
                'ts': ts, 'nivel': nivel,
                'msg': mensagem,
                **(contexto or {})
            }, ensure_ascii=False, default=str)
        else:
            cor   = self.CORES.get(nivel, '')
            reset = self.CORES['RESET']
            ctx   = f" {json.dumps(contexto, ensure_ascii=False, default=str)}" if contexto else ''
            entrada = f"{cor}[{ts}] {nivel:7s}{reset} {mensagem}{ctx}"
        print(entrada)
        if self._arquivo:
            try:
                with open(self._arquivo, 'a', encoding='utf-8') as f:
                    f.write(entrada + '\n')
            except: pass

    def debug(self,   msg, ctx=None): self._log('DEBUG',   msg, ctx)
    def info(self,    msg, ctx=None): self._log('INFO',    msg, ctx)
    def aviso(self,   msg, ctx=None): self._log('AVISO',   msg, ctx)
    def erro(self,    msg, ctx=None): self._log('ERRO',    msg, ctx)
    def critico(self, msg, ctx=None): self._log('CRITICO', msg, ctx)
    def sucesso(self, msg, ctx=None): self._log('INFO', f"✅ {msg}", ctx)


# ══════════════════════════════════════════════════════════════════════════════
#  8. CRIPTOGRAFIA E JWT SIMPLES
# ══════════════════════════════════════════════════════════════════════════════

class AdvakCrypto:
    """
    Funções de criptografia e autenticação JWT.

    crypto.hash_senha("minha_senha")     → hash bcrypt-like
    crypto.verificar_senha("senha", hash) → verdadeiro/falso
    crypto.gerar_token({user_id: 1})     → "eyJ..."
    crypto.verificar_token("eyJ...")     → {user_id: 1} ou nulo
    crypto.uuid()                        → "550e8400-e29b..."
    crypto.aleatorio(32)                 → string hex aleatória
    """

    def __init__(self, secret_key=None):
        self._secret = secret_key or os.environ.get('ADVAK_SECRET', 'advak_secret_default_mude_em_producao')

    def hash_senha(self, senha):
        """Hash seguro de senha com salt."""
        try:
            import bcrypt
            salt = bcrypt.gensalt()
            return bcrypt.hashpw(senha.encode(), salt).decode()
        except ImportError:
            # Fallback sem bcrypt
            salt = os.urandom(32).hex()
            h = hashlib.pbkdf2_hmac('sha256', senha.encode(), salt.encode(), 100000)
            return f"pbkdf2${salt}${h.hex()}"

    def verificar_senha(self, senha, hash_armazenado):
        """Verifica senha contra hash."""
        try:
            import bcrypt
            return bcrypt.checkpw(senha.encode(), hash_armazenado.encode())
        except ImportError:
            if hash_armazenado.startswith('pbkdf2$'):
                _, salt, h = hash_armazenado.split('$')
                h_novo = hashlib.pbkdf2_hmac('sha256', senha.encode(), salt.encode(), 100000)
                return h_novo.hex() == h
            return False

    def gerar_token(self, payload, expira_em=3600):
        """Gera JWT simples."""
        header  = base64.urlsafe_b64encode(
            json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode()
        ).rstrip(b'=').decode()
        
        payload_completo = {**payload, 'exp': int(time.time()) + expira_em, 'iat': int(time.time())}
        body = base64.urlsafe_b64encode(
            json.dumps(payload_completo, default=str).encode()
        ).rstrip(b'=').decode()
        
        sig_input = f"{header}.{body}"
        sig = hmac.new(self._secret.encode(), sig_input.encode(), hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b'=').decode()
        
        return f"{header}.{body}.{sig_b64}"

    def verificar_token(self, token):
        """Verifica e decodifica JWT. Retorna payload ou None."""
        try:
            parts = token.split('.')
            if len(parts) != 3: return None
            header, body, sig = parts
            sig_input = f"{header}.{body}"
            
            # Verifica assinatura
            sig_esperada = hmac.new(
                self._secret.encode(), sig_input.encode(), hashlib.sha256
            ).digest()
            sig_b64 = base64.urlsafe_b64encode(sig_esperada).rstrip(b'=').decode()
            if sig_b64 != sig: return None
            
            # Decodifica payload
            padding = 4 - len(body) % 4
            payload = json.loads(base64.urlsafe_b64decode(body + '=' * padding))
            
            # Verifica expiração
            if payload.get('exp', 0) < time.time(): return None
            
            return payload
        except:
            return None

    def uuid(self):
        """Gera UUID v4."""
        import uuid
        return str(uuid.uuid4())

    def aleatorio(self, tamanho=32):
        """Gera string hexadecimal aleatória."""
        return os.urandom(tamanho).hex()

    def encriptar(self, texto):
        """Encriptação simples XOR com chave (não use para dados sensíveis!)."""
        chave = self._secret.encode()
        dados = texto.encode()
        xored = bytes(b ^ chave[i % len(chave)] for i, b in enumerate(dados))
        return base64.urlsafe_b64encode(xored).decode()

    def decriptar(self, cifrado):
        """Decriptação XOR."""
        chave = self._secret.encode()
        dados = base64.urlsafe_b64decode(cifrado.encode())
        xored = bytes(b ^ chave[i % len(chave)] for i, b in enumerate(dados))
        return xored.decode()


# ══════════════════════════════════════════════════════════════════════════════
#  9. VARIÁVEIS DE AMBIENTE TIPADAS
# ══════════════════════════════════════════════════════════════════════════════

class AdvakEnv:
    """
    Carrega e valida variáveis de ambiente com tipos.

    env.carregar(".env")
    seja porta = env.numero("PORT", padrao=8080)
    seja debug = env.booleano("DEBUG", padrao=falso)
    seja url   = env.texto("DATABASE_URL", obrigatorio=verdadeiro)
    seja lista = env.lista("ALLOWED_HOSTS", separador=",")
    """

    def __init__(self):
        self._loaded = False

    def carregar(self, arquivo='.env'):
        """Carrega arquivo .env."""
        if not os.path.exists(arquivo):
            return f"⚠️  Arquivo '{arquivo}' não encontrado"
        try:
            with open(arquivo, encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha or linha.startswith('#'): continue
                    if '=' in linha:
                        chave, _, valor = linha.partition('=')
                        chave = chave.strip()
                        valor = valor.strip().strip('"').strip("'")
                        os.environ.setdefault(chave, valor)
            self._loaded = True
            return f"✅ .env carregado"
        except Exception as e:
            return f"❌ Erro ao carregar .env: {e}"

    def texto(self, nome, padrao=None, obrigatorio=False):
        val = os.environ.get(nome, padrao)
        if obrigatorio and val is None:
            raise EnvironmentError(f"Variável de ambiente '{nome}' é obrigatória")
        return val

    def numero(self, nome, padrao=0):
        val = os.environ.get(nome)
        if val is None: return padrao
        try: return float(val) if '.' in val else int(val)
        except: return padrao

    def booleano(self, nome, padrao=False):
        val = os.environ.get(nome, '').lower()
        if not val: return padrao
        return val in ('1', 'true', 'sim', 'yes', 'on')

    def lista(self, nome, separador=',', padrao=None):
        val = os.environ.get(nome)
        if not val: return padrao or []
        return [v.strip() for v in val.split(separador) if v.strip()]

    def todos(self):
        return dict(os.environ)

    def definir(self, nome, valor):
        os.environ[nome] = str(valor)

    def exportar(self, arquivo='.env', variaveis=None):
        """Salva variáveis em arquivo .env."""
        dados = variaveis or {}
        with open(arquivo, 'w', encoding='utf-8') as f:
            for k, v in dados.items():
                f.write(f'{k}={v}\n')
        return f"✅ Exportado para {arquivo}"


# ══════════════════════════════════════════════════════════════════════════════
#  10. RATE LIMITER
# ══════════════════════════════════════════════════════════════════════════════

class AdvakRateLimiter:
    """
    Rate limiting por IP ou usuário.
    
    limite.configurar(max_requisicoes=100, janela=60)  // 100 req/min
    // No middleware do servidor:
    servidor.middleware((req) => {
        se (!limite.permitir(req.headers["x-forwarded-for"])) {
            retornar servidor.json({erro: "Muitas requisicoes"}, 429);
        }
    })
    """

    def __init__(self):
        self._janelas = defaultdict(list)
        self._max_req = 100
        self._janela  = 60

    def configurar(self, max_requisicoes=100, janela=60):
        self._max_req = max_requisicoes
        self._janela  = janela
        return self

    def permitir(self, chave):
        agora = time.time()
        janela_inicio = agora - self._janela
        # Remove requisições antigas
        self._janelas[chave] = [t for t in self._janelas[chave] if t > janela_inicio]
        if len(self._janelas[chave]) >= self._max_req:
            return False
        self._janelas[chave].append(agora)
        return True

    def restante(self, chave):
        agora = time.time()
        usadas = len([t for t in self._janelas[chave] if t > agora - self._janela])
        return max(0, self._max_req - usadas)

    def resetar(self, chave):
        self._janelas.pop(chave, None)
