"""
Advak 5.0 — Módulo de Recursos Ultra Avançados

8 sistemas de nível sênior:
  1. Sistema de Tipos em Runtime (TypeScript-like)
  2. Canais Assíncronos (Go-like channels)
  3. Sistema de Eventos/Signals (Reactive)
  4. Pipeline de Dados (Lazy Streams)
  5. Sistema de Decoradores/Middlewares
  6. Máquina de Estados Finitos (FSM)
  7. Observáveis (RxPY-like)
  8. Contratos e Pré/Pós-condições (DbC)
"""

import asyncio
import time
import inspect
import functools
import threading
from typing import Any, Callable, Dict, List, Optional

# Injected by interpreter to handle AdvakFunction calls
_ADVAK_FN_CALLER = None  # set to lambda fn, x: _call_sync(fn, [x])


# ══════════════════════════════════════════════════════════════════════════════
#  1. SISTEMA DE TIPOS EM RUNTIME (TypeScript-like)
# ══════════════════════════════════════════════════════════════════════════════

class AdvakType:
    """Define e valida tipos em runtime."""

    # Tipos primitivos
    TIPOS = {
        'Inteiro':  (int,),
        'Float':    (float, int),
        'Numero':   (float, int),
        'Texto':    (str,),
        'Bool':     (bool,),
        'Lista':    (list,),
        'Mapa':     (dict,),
        'Nulo':     type(None),
        'Qualquer': None,  # any
    }

    @staticmethod
    def verificar(valor, tipo_nome: str, nome_var: str = '?') -> bool:
        """Verifica se valor é do tipo esperado. Lança erro claro se não for."""
        if tipo_nome == 'Qualquer':
            return True
        tipos = AdvakType.TIPOS.get(tipo_nome)
        if tipos is None:
            # Tipo não reconhecido — aceita qualquer coisa
            return True
        if tipos == type(None):
            if valor is not None:
                raise TypeError(f"'{nome_var}' deve ser nulo, mas é {type(valor).__name__}")
            return True
        if not isinstance(valor, tipos):
            esperado = tipo_nome
            recebido = type(valor).__name__
            raise TypeError(
                f"Tipo inválido: '{nome_var}' deve ser {esperado}, "
                f"mas recebeu {recebido} ({repr(valor)[:30]})"
            )
        return True

    @staticmethod
    def inferir(valor) -> str:
        """Infere o nome do tipo Advak de um valor Python."""
        if valor is None:             return 'Nulo'
        if isinstance(valor, bool):   return 'Bool'
        if isinstance(valor, int):    return 'Inteiro'
        if isinstance(valor, float):  return 'Float'
        if isinstance(valor, str):    return 'Texto'
        if isinstance(valor, list):   return 'Lista'
        if isinstance(valor, dict):   return 'Mapa'
        return type(valor).__name__

    @staticmethod
    def criar_schema(definicao: dict):
        """
        Cria um schema de validação para mapas/objetos.
        Uso: tipos.schema({nome: 'Texto', idade: 'Inteiro', email: 'Texto?'})
        """
        def validar(obj):
            if not isinstance(obj, dict):
                raise TypeError(f"Schema espera Mapa, recebeu {type(obj).__name__}")
            erros = []
            for campo, tipo in definicao.items():
                opcional = tipo.endswith('?')
                tipo_real = tipo.rstrip('?')
                if campo not in obj:
                    if not opcional:
                        erros.append(f"Campo obrigatório ausente: '{campo}'")
                    continue
                try:
                    AdvakType.verificar(obj[campo], tipo_real, campo)
                except TypeError as e:
                    erros.append(str(e))
            if erros:
                raise TypeError("Validação de schema falhou:\n  " + "\n  ".join(erros))
            return True
        validar._schema = definicao
        return validar

    @staticmethod
    def criar_enum_tipo(*valores):
        """Cria um tipo enumerado de valores permitidos."""
        def validar(v):
            if v not in valores:
                raise TypeError(f"Valor '{v}' não permitido. Valores válidos: {list(valores)}")
            return True
        return validar

    @staticmethod
    def criar_uniao(*tipos):
        """Cria um tipo união (A | B | C)."""
        def validar(v):
            for t in tipos:
                try:
                    AdvakType.verificar(v, t)
                    return True
                except TypeError:
                    pass
            raise TypeError(f"Valor '{repr(v)[:30]}' não bate com nenhum tipo: {list(tipos)}")
        return validar


def criar_sistema_tipos():
    """Retorna o objeto 'tipos' para o escopo Advak."""
    return {
        'verificar':    lambda v, t, n='?': AdvakType.verificar(v, t, n),
        'inferir':      lambda v: AdvakType.inferir(v),
        'schema':       lambda d: AdvakType.criar_schema(d),
        'enum_tipo':    lambda *vs: AdvakType.criar_enum_tipo(*vs),
        'uniao':        lambda *ts: AdvakType.criar_uniao(*ts),
        'e_inteiro':    lambda v: isinstance(v, int) and not isinstance(v, bool),
        'e_texto':      lambda v: isinstance(v, str),
        'e_lista':      lambda v: isinstance(v, list),
        'e_mapa':       lambda v: isinstance(v, dict),
        'e_nulo':       lambda v: v is None,
        'e_bool':       lambda v: isinstance(v, bool),
        'e_numero':     lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        'e_funcao':     lambda v: callable(v),
        'converter':    lambda v, t: (
            int(v) if t == 'Inteiro' else
            float(v) if t == 'Float' else
            str(v) if t == 'Texto' else
            bool(v) if t == 'Bool' else
            list(v) if t == 'Lista' else v
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  2. CANAIS ASSÍNCRONOS (Go-like channels)
# ══════════════════════════════════════════════════════════════════════════════

class Canal:
    """
    Canal de comunicação assíncrona entre corrotinas.
    Equivalente a channels do Go — produtor/consumidor com buffer.

    canal = Canal(capacidade=10)
    canal.enviar(valor)
    canal.receber()   → valor
    canal.fechar()
    canal.esta_fechado
    """

    def __init__(self, capacidade: int = 0, nome: str = '?'):
        self.nome = nome
        self._capacidade = capacidade
        self._fila: asyncio.Queue = None
        self._fechado = False
        self._sentinela = object()
        self._lock = threading.Lock()
        # Cria fila compatível com threads
        self._buffer = []
        self._waiters = []

    def _get_queue(self):
        """Lazy-init da fila asyncio no loop correto."""
        if self._fila is None:
            try:
                loop = asyncio.get_event_loop()
                maxsize = self._capacidade if self._capacidade > 0 else 0
                self._fila = asyncio.Queue(maxsize=maxsize)
            except RuntimeError:
                pass
        return self._fila

    def enviar(self, valor):
        """Envia valor para o canal (síncrono)."""
        if self._fechado:
            raise RuntimeError(f"Canal '{self.nome}' está fechado")
        with self._lock:
            self._buffer.append(valor)
        return self

    def receber(self):
        """Recebe próximo valor do canal (síncrono, None se vazio)."""
        with self._lock:
            if self._buffer:
                return self._buffer.pop(0)
        return None

    def receber_todos(self):
        """Recebe todos os valores disponíveis."""
        with self._lock:
            vals = list(self._buffer)
            self._buffer.clear()
        return vals

    def fechar(self):
        self._fechado = True

    @property
    def esta_fechado(self):
        return self._fechado

    @property
    def tamanho(self):
        return len(self._buffer)

    @property
    def vazio(self):
        return len(self._buffer) == 0

    def __repr__(self):
        return f"Canal('{self.nome}', {len(self._buffer)} msgs, fechado={self._fechado})"


def criar_sistema_canais():
    """Retorna o objeto 'canal' para o escopo Advak."""
    def novo_canal(capacidade=0, nome='canal'):
        c = Canal(capacidade=capacidade, nome=nome)
        return {
            'enviar':       lambda v: c.enviar(v),
            'receber':      lambda: c.receber(),
            'receber_todos':lambda: c.receber_todos(),
            'fechar':       lambda: c.fechar(),
            'esta_fechado': property(lambda: c.esta_fechado),
            'tamanho':      property(lambda: c.tamanho),
            'vazio':        property(lambda: c.vazio),
            '_canal':       c,
        }
    return {
        'criar':    lambda cap=0, nome='canal': novo_canal(cap, nome),
        'pipeline': lambda *canais: _pipeline_canais(list(canais)),
    }

def _pipeline_canais(canais):
    """Conecta canais em pipeline: A → B → C."""
    return {
        'canais': canais,
        'enviar': lambda v: canais[0]['enviar'](v) if canais else None,
        'receber': lambda: canais[-1]['receber']() if canais else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  3. SISTEMA DE EVENTOS / SIGNALS (Reactive)
# ══════════════════════════════════════════════════════════════════════════════

class SistemaEventos:
    """
    Event bus reativo com suporte a:
    - emit/on/off
    - once (uma vez só)
    - wildcards
    - histórico de eventos
    - middleware

    eventos.on('usuario:criado', fn)
    eventos.emit('usuario:criado', {nome: 'Ana'})
    eventos.once('app:pronto', fn)
    """

    def __init__(self):
        self._listeners: Dict[str, List] = {}
        self._historico: List = []
        self._middlewares: List = []
        self._max_historico = 1000

    def on(self, evento: str, fn: Callable, prioridade: int = 0):
        """Registra listener para um evento."""
        if evento not in self._listeners:
            self._listeners[evento] = []
        self._listeners[evento].append({'fn': fn, 'once': False, 'prio': prioridade})
        self._listeners[evento].sort(key=lambda x: -x['prio'])
        return lambda: self.off(evento, fn)  # retorna função para cancelar

    def once(self, evento: str, fn: Callable):
        """Registra listener que dispara apenas uma vez."""
        if evento not in self._listeners:
            self._listeners[evento] = []
        self._listeners[evento].append({'fn': fn, 'once': True, 'prio': 0})
        return self

    def off(self, evento: str, fn: Callable = None):
        """Remove listener(s) de um evento."""
        if evento in self._listeners:
            if fn is None:
                self._listeners[evento] = []
            else:
                self._listeners[evento] = [
                    l for l in self._listeners[evento] if l['fn'] is not fn
                ]

    def emit(self, evento: str, *args, **kwargs):
        """Dispara um evento com dados."""
        dados = args[0] if len(args) == 1 else args if args else kwargs

        # Histórico
        self._historico.append({
            'evento': evento,
            'dados': dados,
            'tempo': time.time(),
        })
        if len(self._historico) > self._max_historico:
            self._historico.pop(0)

        # Middlewares
        for mw in self._middlewares:
            try:
                resultado = mw(evento, dados)
                if resultado is False:
                    return self  # middleware cancelou o evento
            except Exception:
                pass

        # Listeners diretos
        listeners = list(self._listeners.get(evento, []))

        # Wildcard listeners (ex: 'usuario:*')
        for padrao, ls in self._listeners.items():
            if padrao != evento and padrao.endswith('*'):
                prefix = padrao[:-1]
                if evento.startswith(prefix):
                    listeners.extend(ls)

        para_remover = []
        for l in listeners:
            try:
                l['fn'](dados)
            except Exception:
                pass
            if l['once']:
                para_remover.append(l)

        # Remove once listeners
        for l in para_remover:
            for ev_ls in self._listeners.values():
                if l in ev_ls:
                    ev_ls.remove(l)

        return self

    def use(self, fn: Callable):
        """Adiciona middleware global."""
        self._middlewares.append(fn)
        return self

    def historico(self, evento: str = None, limite: int = 50):
        """Retorna histórico de eventos."""
        h = self._historico
        if evento:
            h = [e for e in h if e['evento'] == evento]
        return h[-limite:]

    def listar(self):
        """Lista todos os eventos registrados."""
        return {ev: len(ls) for ev, ls in self._listeners.items()}

    def limpar(self):
        """Remove todos os listeners."""
        self._listeners.clear()
        self._historico.clear()


_eventos_global = SistemaEventos()

def criar_sistema_eventos():
    ev = _eventos_global
    return {
        'on':          lambda evento, fn, prio=0: ev.on(evento, fn, prio),
        'once':        lambda evento, fn: ev.once(evento, fn),
        'off':         lambda evento, fn=None: ev.off(evento, fn),
        'emit':        lambda evento, *args, **kw: ev.emit(evento, *args, **kw),
        'use':         lambda fn: ev.use(fn),
        'historico':   lambda ev_nome=None, lim=50: ev.historico(ev_nome, lim),
        'listar':      lambda: ev.listar(),
        'limpar':      lambda: ev.limpar(),
        'criar':       lambda: SistemaEventos(),  # novo bus isolado
    }


# ══════════════════════════════════════════════════════════════════════════════
#  4. PIPELINE DE DADOS — Lazy Streams
# ══════════════════════════════════════════════════════════════════════════════

class Stream:
    """
    Pipeline de dados lazy — processa só quando necessário.

    Stream([1,2,3,4,5])
      .map(x => x * 2)
      .filtrar(x => x > 4)
      .take(3)
      .coletар()   → [6, 8, 10]

    Suporta dados infinitos quando combinado com generators.
    """

    def __init__(self, fonte):
        if callable(fonte) and not hasattr(fonte, '__iter__'):
            self._fonte = fonte
        else:
            self._fonte = iter(fonte) if hasattr(fonte, '__iter__') else iter([fonte])
        self._ops = []

    def _aplicar(self):
        """Executa o pipeline lazy."""
        def _call(fn, x):
            """Safe call: handles AdvakFunction, Python callable, or None."""
            if fn is None: return x
            # If already a Python callable (e.g. already wrapped lambda), call directly
            if callable(fn):
                return fn(x)
            # Fall back to AdvakFunction caller for raw AdvakFunction objects
            global _ADVAK_FN_CALLER
            if _ADVAK_FN_CALLER is not None:
                return _ADVAK_FN_CALLER(fn, x)
            return x

        def _call_bool(fn, x):
            result = _call(fn, x)
            return bool(result) if result is not None else False

        def _call_reduce(fn, acc, x):
            global _ADVAK_FN_CALLER
            if _ADVAK_FN_CALLER is not None:
                try:
                    return _ADVAK_FN_CALLER.__self__._call_sync(fn, [acc, x]) if hasattr(_ADVAK_FN_CALLER, '__self__') else fn(acc, x)
                except: pass
            if callable(fn): return fn(acc, x)
            return acc

        # Use factory functions to avoid Python loop variable capture bug
        # (generators in a loop share the same 'op_fn' reference)
        def _make_map(src, fn):
            for x in src: yield _call(fn, x)

        def _make_filtrar(src, fn):
            for x in src:
                if _call_bool(fn, x): yield x

        def _make_flat_map(src, fn):
            for x in src:
                for y in _call(fn, x): yield y

        def _make_ordenar(src, fn, rev):
            key = (lambda x: _call(fn, x)) if fn else (lambda x: x)
            yield from sorted(src, key=key, reverse=bool(rev))

        gen = self._fonte
        for op_tipo, op_fn, op_arg in self._ops:
            if op_tipo == 'map':
                gen = _make_map(gen, op_fn)
            elif op_tipo == 'filtrar':
                gen = _make_filtrar(gen, op_fn)
            elif op_tipo == 'take':
                gen = _take(gen, op_arg)
            elif op_tipo == 'skip':
                gen = _skip(gen, op_arg)
            elif op_tipo == 'flat_map':
                gen = _make_flat_map(gen, op_fn)
            elif op_tipo == 'distinct':
                gen = _distinct(gen)
            elif op_tipo == 'ordenar':
                gen = _make_ordenar(gen, op_fn, op_arg)
            elif op_tipo == 'chunk':
                gen = _chunk(gen, op_arg)
            elif op_tipo == 'zip_com':
                gen = zip(gen, op_arg)
        return gen

    def map(self, fn):
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('map', fn, None)]
        return s

    def filtrar(self, fn):
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('filtrar', fn, None)]
        return s

    def take(self, n):
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('take', None, n)]
        return s

    def skip(self, n):
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('skip', None, n)]
        return s

    def flat_map(self, fn):
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('flat_map', fn, None)]
        return s

    def distinct(self):
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('distinct', None, None)]
        return s

    def ordenar(self, fn=None, reverso=False):
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('ordenar', fn, reverso)]
        return s

    def chunk(self, tamanho):
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('chunk', None, tamanho)]
        return s

    def zip_com(self, outro):
        outro_iter = iter(outro) if hasattr(outro, '__iter__') else iter([outro])
        s = Stream.__new__(Stream)
        s._fonte = self._fonte
        s._ops = self._ops + [('zip_com', None, outro_iter)]
        return s

    # Terminais (executam o pipeline)
    def coletar(self):
        return list(self._aplicar())

    def primeiro(self):
        try: return next(self._aplicar())
        except StopIteration: return None

    def ultimo(self):
        result = None
        for x in self._aplicar():
            result = x
        return result

    def contar(self):
        return sum(1 for _ in self._aplicar())

    def somar(self):
        return sum(self._aplicar())

    def _scall(self, fn, *args):
        """Safe single-arg call through AdvakFunction caller."""
        global _ADVAK_FN_CALLER
        if _ADVAK_FN_CALLER and len(args) == 1:
            return _ADVAK_FN_CALLER(fn, args[0])
        if callable(fn): return fn(*args)
        return None

    def reduzir(self, fn, inicial=None):
        gen = self._aplicar()
        acc = inicial
        if acc is None:
            try: acc = next(gen)
            except StopIteration: return None
        for x in gen:
            if callable(fn): acc = fn(acc, x)
        return acc

    def para_cada(self, fn):
        for x in self._aplicar():
            self._scall(fn, x)
        return None

    def existe(self, fn=None):
        for x in self._aplicar():
            if fn is None or bool(self._scall(fn, x)):
                return True
        return False

    def todos(self, fn):
        return all(bool(self._scall(fn, x)) for x in self._aplicar())

    def min(self, fn=None):
        key = (lambda x: self._scall(fn, x)) if fn else None
        return min(self._aplicar(), key=key or (lambda x: x), default=None)

    def max(self, fn=None):
        key = (lambda x: self._scall(fn, x)) if fn else None
        return max(self._aplicar(), key=key or (lambda x: x), default=None)

    def agrupar(self, fn):
        resultado = {}
        for x in self._aplicar():
            chave = self._scall(fn, x)
            if chave not in resultado:
                resultado[chave] = []
            resultado[chave].append(x)
        return resultado

    def __iter__(self):
        return self._aplicar()

    def __repr__(self):
        return f"Stream({len(self._ops)} ops)"


def _take(gen, n):
    for i, x in enumerate(gen):
        if i >= n: break
        yield x

def _skip(gen, n):
    for i, x in enumerate(gen):
        if i >= n: yield x

def _distinct(gen):
    seen = set()
    for x in gen:
        key = x if not isinstance(x, (list, dict)) else str(x)
        if key not in seen:
            seen.add(key)
            yield x

def _chunk(gen, n):
    chunk = []
    for x in gen:
        chunk.append(x)
        if len(chunk) == n:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def criar_sistema_stream():
    def novo_stream(fonte):
        s = Stream(fonte)
        return _stream_para_advak(s)

    def _stream_para_advak(s):
        return {
            'map':       lambda fn: _stream_para_advak(s.map(fn)),
            'filtrar':   lambda fn: _stream_para_advak(s.filtrar(fn)),
            'take':      lambda n:  _stream_para_advak(s.take(n)),
            'skip':      lambda n:  _stream_para_advak(s.skip(n)),
            'flat_map':  lambda fn: _stream_para_advak(s.flat_map(fn)),
            'distinct':  lambda:    _stream_para_advak(s.distinct()),
            'ordenar':   lambda fn=None, rev=False: _stream_para_advak(s.ordenar(fn, rev)),
            'chunk':     lambda n:  _stream_para_advak(s.chunk(n)),
            'zip_com':   lambda o:  _stream_para_advak(s.zip_com(o)),
            'coletar':   lambda:    s.coletar(),
            'primeiro':  lambda:    s.primeiro(),
            'ultimo':    lambda:    s.ultimo(),
            'contar':    lambda:    s.contar(),
            'somar':     lambda:    s.somar(),
            'reduzir':   lambda fn, ini=None: s.reduzir(fn, ini),
            'para_cada': lambda fn: s.para_cada(fn),
            'existe':    lambda fn=None: s.existe(fn),
            'todos':     lambda fn: s.todos(fn),
            'min':       lambda fn=None: s.min(fn),
            'max':       lambda fn=None: s.max(fn),
            'agrupar':   lambda fn: s.agrupar(fn),
            '_stream':   s,
        }

    def _inf_stream(fn):
        """Creates infinite stream, converting AdvakFunction at call time."""
        def _gen():
            i = 0
            while True:
                global _ADVAK_FN_CALLER
                if _ADVAK_FN_CALLER:
                    try:
                        yield _ADVAK_FN_CALLER(fn, i)
                        i += 1
                        continue
                    except Exception:
                        pass
                if callable(fn):
                    yield fn(i)
                else:
                    yield i
                i += 1
        return novo_stream(_gen())
    return {
        'de':       novo_stream,
        'de_range': lambda ini, fim, passo=1: novo_stream(range(ini, fim, passo)),
        'de_texto': lambda txt: novo_stream(list(txt)),
        'infinito': _inf_stream,
        'mesclar':  lambda *streams: novo_stream(_mesclar(*streams)),
    }

def _infinito_gen(fn):
    i = 0
    while True:
        global _ADVAK_FN_CALLER
        if _ADVAK_FN_CALLER:
            yield _ADVAK_FN_CALLER(fn, i)
        elif callable(fn):
            yield fn(i)
        else:
            yield i
        i += 1

def _mesclar(*streams):
    for s in streams:
        yield from s


# ══════════════════════════════════════════════════════════════════════════════
#  5. DECORADORES / MIDDLEWARES
# ══════════════════════════════════════════════════════════════════════════════

class GerenciadorDecorators:
    """
    Sistema de decoradores para funções Advak.
    Permite compor comportamentos: memoizar, log, retry, timeout, etc.
    """

    @staticmethod
    def memoizar(fn, max_cache=128):
        """Cacheia resultados de função pura baseado nos argumentos."""
        _cache = {}
        _ordem = []
        def wrapper(*args):
            chave = str(args)
            if chave not in _cache:
                if len(_cache) >= max_cache:
                    mais_velho = _ordem.pop(0)
                    del _cache[mais_velho]
                _cache[chave] = fn(*args)
                _ordem.append(chave)
            return _cache[chave]
        wrapper._cache = _cache
        wrapper._limpar = lambda: (_cache.clear(), _ordem.clear())
        return wrapper

    @staticmethod
    def tentar_novamente(fn, tentativas=3, espera=1.0, exceções=(Exception,)):
        """Retenta a função N vezes antes de desistir."""
        def wrapper(*args, **kwargs):
            ultimo_erro = None
            for i in range(tentativas):
                try:
                    return fn(*args, **kwargs)
                except exceções as e:
                    ultimo_erro = e
                    if i < tentativas - 1:
                        time.sleep(espera)
            raise RuntimeError(
                f"Falhou após {tentativas} tentativas. Último erro: {ultimo_erro}"
            )
        return wrapper

    @staticmethod
    def com_log(fn, nome=None, logger=None):
        """Loga chamadas e retornos da função."""
        fn_nome = nome or getattr(fn, '__name__', '?')
        log = logger or (lambda msg: print(f"  [LOG] {msg}"))
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            log(f"→ {fn_nome}({', '.join(repr(a)[:20] for a in args)})")
            try:
                resultado = fn(*args, **kwargs)
                dt = (time.perf_counter() - t0) * 1000
                log(f"← {fn_nome} = {repr(resultado)[:30]} [{dt:.1f}ms]")
                return resultado
            except Exception as e:
                dt = (time.perf_counter() - t0) * 1000
                log(f"✗ {fn_nome} ERRO: {e} [{dt:.1f}ms]")
                raise
        return wrapper

    @staticmethod
    def debounce(fn, espera_ms=300):
        """Executa só depois de N ms sem novas chamadas (ideal para eventos GUI)."""
        timer = [None]
        def wrapper(*args, **kwargs):
            if timer[0]:
                timer[0].cancel()
            def executar():
                fn(*args, **kwargs)
                timer[0] = None
            timer[0] = threading.Timer(espera_ms / 1000, executar)
            timer[0].start()
        wrapper._cancelar = lambda: timer[0].cancel() if timer[0] else None
        return wrapper

    @staticmethod
    def throttle(fn, intervalo_ms=300):
        """Limita execução a no máximo 1 vez por N ms."""
        ultimo = [0]
        def wrapper(*args, **kwargs):
            agora = time.time() * 1000
            if agora - ultimo[0] >= intervalo_ms:
                ultimo[0] = agora
                return fn(*args, **kwargs)
        return wrapper

    @staticmethod
    def medir_tempo(fn, nome=None):
        """Mede e retorna tempo de execução."""
        fn_nome = nome or getattr(fn, '__name__', '?')
        tempos = []
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            resultado = fn(*args, **kwargs)
            dt = (time.perf_counter() - t0) * 1000
            tempos.append(dt)
            return resultado
        wrapper._tempos = tempos
        wrapper._media = lambda: sum(tempos) / len(tempos) if tempos else 0
        wrapper._total = lambda: sum(tempos)
        return wrapper

    @staticmethod
    def compor(*fns):
        """Compõe múltiplas funções: f ∘ g ∘ h (aplica da direita para esquerda)."""
        def composicao(x):
            resultado = x
            for fn in reversed(fns):
                resultado = fn(resultado)
            return resultado
        return composicao

    @staticmethod
    def pipeline(*fns):
        """Pipeline de funções (da esquerda para direita): h(g(f(x)))."""
        def pipe(x):
            resultado = x
            for fn in fns:
                resultado = fn(resultado)
            return resultado
        return pipe


def criar_sistema_decoradores():
    d = GerenciadorDecorators
    return {
        'memoizar':        lambda fn, max=128: d.memoizar(fn, max),
        'tentar_novamente':lambda fn, n=3, esp=1.0: d.tentar_novamente(fn, n, esp),
        'com_log':         lambda fn, nome=None: d.com_log(fn, nome),
        'debounce':        lambda fn, ms=300: d.debounce(fn, ms),
        'throttle':        lambda fn, ms=300: d.throttle(fn, ms),
        'medir_tempo':     lambda fn, nome=None: d.medir_tempo(fn, nome),
        'compor':          lambda *fns: d.compor(*fns),
        'pipeline':        lambda *fns: d.pipeline(*fns),
        'identidade':      lambda x: x,
        'constante':       lambda v: (lambda *_: v),
        'negar':           lambda fn: (lambda *a, **kw: not fn(*a, **kw)),
        'uma_vez':         lambda fn: (functools.lru_cache(maxsize=1)(fn)),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  6. MÁQUINA DE ESTADOS FINITOS (FSM)
# ══════════════════════════════════════════════════════════════════════════════

class MaquinaEstados:
    """
    Finite State Machine (FSM) para modelar fluxos complexos.

    fsm = MaquinaEstados('rascunho')
    fsm.transicao('rascunho', 'enviar', 'pendente')
    fsm.transicao('pendente', 'aprovar', 'ativo')
    fsm.transicao('pendente', 'rejeitar', 'rascunho')
    fsm.transicao('ativo', 'arquivar', 'arquivado')

    fsm.ao_entrar('ativo', fn)
    fsm.ao_sair('pendente', fn)
    fsm.ao_transicionar(fn)  # global

    fsm.disparar('enviar')    → 'pendente'
    fsm.pode('aprovar')       → verdadeiro/falso
    fsm.estado                → estado atual
    fsm.historico             → [('rascunho', 'enviar', 'pendente'), ...]
    """

    def __init__(self, estado_inicial: str):
        self._estado = estado_inicial
        self._transicoes: Dict[str, Dict[str, str]] = {}
        self._ao_entrar: Dict[str, List] = {}
        self._ao_sair: Dict[str, List] = {}
        self._ao_transicionar: List = []
        self._historico: List = []
        self._guardas: Dict[str, List] = {}  # (estado, evento) → [fn_guarda]

    def transicao(self, de: str, evento: str, para: str,
                  guarda: Callable = None, acao: Callable = None):
        """Define uma transição de estado."""
        if de not in self._transicoes:
            self._transicoes[de] = {}
        self._transicoes[de][evento] = {'para': para, 'acao': acao}
        if guarda:
            chave = f"{de}:{evento}"
            if chave not in self._guardas:
                self._guardas[chave] = []
            self._guardas[chave].append(guarda)
        return self

    def ao_entrar(self, estado: str, fn: Callable):
        """Callback executado ao entrar num estado."""
        if estado not in self._ao_entrar:
            self._ao_entrar[estado] = []
        self._ao_entrar[estado].append(fn)
        return self

    def ao_sair(self, estado: str, fn: Callable):
        """Callback executado ao sair de um estado."""
        if estado not in self._ao_sair:
            self._ao_sair[estado] = []
        self._ao_sair[estado].append(fn)
        return self

    def ao_transicionar(self, fn: Callable):
        """Callback global para qualquer transição."""
        self._ao_transicionar.append(fn)
        return self

    def disparar(self, evento: str, *args):
        """Dispara um evento e realiza a transição se possível."""
        if self._estado not in self._transicoes:
            raise RuntimeError(
                f"Estado '{self._estado}' não tem transições definidas"
            )
        transicoes_estado = self._transicoes[self._estado]
        if evento not in transicoes_estado:
            eventos_validos = list(transicoes_estado.keys())
            raise RuntimeError(
                f"Evento '{evento}' inválido no estado '{self._estado}'. "
                f"Eventos válidos: {eventos_validos}"
            )

        info = transicoes_estado[evento]
        proximo = info['para']

        # Verifica guardas
        chave = f"{self._estado}:{evento}"
        for guarda in self._guardas.get(chave, []):
            if not guarda(*args):
                raise RuntimeError(
                    f"Guarda bloqueou transição '{evento}' em '{self._estado}'"
                )

        estado_anterior = self._estado

        # Callbacks ao sair
        for fn in self._ao_sair.get(estado_anterior, []):
            try: fn(estado_anterior, evento, proximo)
            except: pass

        # Ação da transição
        if info.get('acao'):
            try: info['acao'](*args)
            except: pass

        # Muda estado
        self._estado = proximo
        self._historico.append({
            'de': estado_anterior,
            'evento': evento,
            'para': proximo,
            'tempo': time.time(),
        })

        # Callbacks ao entrar
        for fn in self._ao_entrar.get(proximo, []):
            try: fn(estado_anterior, evento, proximo)
            except: pass

        # Callbacks globais
        for fn in self._ao_transicionar:
            try: fn(estado_anterior, evento, proximo)
            except: pass

        return proximo

    def pode(self, evento: str) -> bool:
        """Verifica se evento é válido no estado atual."""
        return (self._estado in self._transicoes and
                evento in self._transicoes[self._estado])

    def eventos_possiveis(self) -> List[str]:
        """Lista eventos disponíveis no estado atual."""
        return list(self._transicoes.get(self._estado, {}).keys())

    def resetar(self, estado_inicial: str = None):
        """Volta ao estado inicial ou a um estado específico."""
        if estado_inicial:
            self._estado = estado_inicial
        elif self._historico:
            self._estado = self._historico[0]['de']
        self._historico.clear()

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def historico(self) -> List:
        return list(self._historico)

    def __repr__(self):
        return f"FSM(estado='{self._estado}', transições={sum(len(v) for v in self._transicoes.values())})"


def criar_sistema_fsm():
    def nova_maquina(estado_inicial):
        fsm = MaquinaEstados(estado_inicial)
        def _api():
            return {
                'transicao':          lambda de, ev, para, guarda=None, acao=None:
                                        (fsm.transicao(de, ev, para, guarda, acao), _api())[1],
                'ao_entrar':          lambda est, fn: (fsm.ao_entrar(est, fn), _api())[1],
                'ao_sair':            lambda est, fn: (fsm.ao_sair(est, fn), _api())[1],
                'ao_transicionar':    lambda fn: (fsm.ao_transicionar(fn), _api())[1],
                'disparar':           lambda ev, *args: fsm.disparar(ev, *args),
                'pode':               lambda ev: fsm.pode(ev),
                'eventos':            lambda: fsm.eventos_possiveis(),
                'resetar':            lambda est=None: fsm.resetar(est),
                'estado':             property(lambda: fsm.estado),
                'historico':          property(lambda: fsm.historico),
                '_fsm':               fsm,
                'obter_estado':       lambda: fsm.estado,
                'obter_historico':    lambda: fsm.historico,
            }
        return _api()
    return {
        'criar':    nova_maquina,
        'criar_fsm': nova_maquina,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  7. OBSERVÁVEIS (Observable/Reactive)
# ══════════════════════════════════════════════════════════════════════════════

class Observable:
    """
    Implementação leve de Observáveis (RxJS-like).
    Permite programação reativa com operadores.

    obs = Observable.de([1, 2, 3, 4, 5])
    obs.map(x => x * 2)
       .filtrar(x => x > 4)
       .subscribir(
           proximo=fn,
           erro=fn_erro,
           completo=fn_fim
       )
    """

    def __init__(self, fonte_fn: Callable):
        self._fonte = fonte_fn
        self._ops = []

    @classmethod
    def de(cls, valor):
        """Cria Observable a partir de lista, gerador, valor único."""
        def _fonte(observador):
            try:
                if hasattr(valor, '__iter__') and not isinstance(valor, str):
                    for item in valor:
                        observador['proximo'](item)
                else:
                    observador['proximo'](valor)
                if observador.get('completo'):
                    observador['completo']()
            except Exception as e:
                if observador.get('erro'):
                    observador['erro'](e)
        return cls(_fonte)

    @classmethod
    def de_evento(cls, evento: str, bus: SistemaEventos):
        """Cria Observable a partir de eventos."""
        def _fonte(observador):
            bus.on(evento, observador['proximo'])
        return cls(_fonte)

    @classmethod
    def intervalo(cls, ms: int, limite: int = None):
        """Observable que emite a cada N ms."""
        def _fonte(obs):
            count = 0
            def tick():
                nonlocal count
                if limite is not None and count >= limite:
                    if obs.get('completo'): obs['completo']()
                    return
                obs['proximo'](count)
                count += 1
                if limite is None or count < limite:
                    threading.Timer(ms / 1000, tick).start()
            tick()
        return cls(_fonte)

    def map(self, fn):
        obs = Observable.__new__(Observable)
        obs._fonte = self._fonte
        obs._ops = self._ops + [('map', fn)]
        return obs

    def filtrar(self, fn):
        obs = Observable.__new__(Observable)
        obs._fonte = self._fonte
        obs._ops = self._ops + [('filtrar', fn)]
        return obs

    def take(self, n):
        obs = Observable.__new__(Observable)
        obs._fonte = self._fonte
        obs._ops = self._ops + [('take', n)]
        return obs

    def distinct(self):
        obs = Observable.__new__(Observable)
        obs._fonte = self._fonte
        obs._ops = self._ops + [('distinct', None)]
        return obs

    def _criar_observador(self, proximo_fn, erro_fn=None, completo_fn=None):
        ops = list(self._ops)
        conta = [0]
        seen = set()

        def processar(valor):
            try:
                v = valor
                for op, arg in ops:
                    if op == 'map':
                        v = arg(v)
                    elif op == 'filtrar':
                        if not arg(v): return
                    elif op == 'take':
                        if conta[0] >= arg:
                            return
                    elif op == 'distinct':
                        key = str(v)
                        if key in seen: return
                        seen.add(key)
                conta[0] += 1
                proximo_fn(v)
            except Exception as e:
                if erro_fn: erro_fn(e)

        return {'proximo': processar, 'erro': erro_fn, 'completo': completo_fn}

    def subscribir(self, proximo=None, erro=None, completo=None):
        """Subscreve ao Observable e começa a receber valores."""
        obs = self._criar_observador(
            proximo or (lambda v: None),
            erro,
            completo
        )
        try:
            self._fonte(obs)
        except Exception as e:
            if erro: erro(e)
        return lambda: None  # unsubscribe (simplificado)

    def coletar(self):
        """Coleta todos os valores em lista (síncrono)."""
        resultado = []
        self.subscribir(proximo=resultado.append)
        return resultado

    def primeiro(self):
        result = [None]
        def _cap(v):
            if result[0] is None:
                result[0] = v
        self.subscribir(proximo=_cap)
        return result[0]


def criar_sistema_observable():
    def novo_obs(fonte):
        obs = Observable.de(fonte)
        return _obs_para_advak(obs)

    def _obs_para_advak(obs):
        return {
            'map':       lambda fn: _obs_para_advak(obs.map(fn)),
            'filtrar':   lambda fn: _obs_para_advak(obs.filtrar(fn)),
            'take':      lambda n:  _obs_para_advak(obs.take(n)),
            'distinct':  lambda:    _obs_para_advak(obs.distinct()),
            'subscribir':lambda proximo=None, erro=None, completo=None:
                            obs.subscribir(proximo, erro, completo),
            'coletar':   lambda: obs.coletar(),
            'primeiro':  lambda: obs.primeiro(),
            '_obs':      obs,
        }

    return {
        'de':          novo_obs,
        'de_evento':   lambda evento, bus: _obs_para_advak(
                           Observable.de_evento(evento, bus.get('_bus', _eventos_global))
                       ),
        'intervalo':   lambda ms, lim=None: _obs_para_advak(Observable.intervalo(ms, lim)),
        'mesclar':     lambda *obs_list: novo_obs([
                           v for obs in obs_list for v in obs.get('coletar', lambda: [])()
                       ]),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  8. CONTRATOS / DESIGN BY CONTRACT (DbC)
# ══════════════════════════════════════════════════════════════════════════════

class ViolacaoContrato(Exception):
    def __init__(self, tipo, descricao, fn_nome='?', valor=None):
        self.tipo = tipo
        self.fn_nome = fn_nome
        msg = f"[Contrato:{tipo}] em '{fn_nome}': {descricao}"
        if valor is not None:
            msg += f" (valor: {repr(valor)[:50]})"
        super().__init__(msg)


def contratar(fn, pre=None, pos=None, invariante=None, nome=None):
    """
    Decora uma função com pré-condições, pós-condições e invariantes.

    fn_segura = contratar(dividir,
        pre=lambda a, b: b != 0,
        pos=lambda r, a, b: r * b == a,
        nome='dividir'
    )

    pre:        função(*args) → bool
    pos:        função(resultado, *args) → bool
    invariante: função(resultado) → bool
    """
    fn_nome = nome or getattr(fn, '__name__', '?')

    def wrapper(*args, **kwargs):
        # Verifica pré-condição
        if pre is not None:
            try:
                ok = pre(*args, **kwargs)
            except Exception as e:
                raise ViolacaoContrato('PRE', f'Exceção na verificação: {e}', fn_nome)
            if not ok:
                raise ViolacaoContrato('PRE', 'Pré-condição falhou', fn_nome, args)

        # Executa a função
        resultado = fn(*args, **kwargs)

        # Verifica pós-condição
        if pos is not None:
            try:
                ok = pos(resultado, *args, **kwargs)
            except Exception as e:
                raise ViolacaoContrato('POS', f'Exceção na verificação: {e}', fn_nome)
            if not ok:
                raise ViolacaoContrato('POS', 'Pós-condição falhou', fn_nome, resultado)

        # Verifica invariante
        if invariante is not None:
            try:
                ok = invariante(resultado)
            except Exception as e:
                raise ViolacaoContrato('INV', f'Exceção na verificação: {e}', fn_nome)
            if not ok:
                raise ViolacaoContrato('INV', 'Invariante violado', fn_nome, resultado)

        return resultado

    wrapper._original = fn
    wrapper._contrato = {'pre': pre, 'pos': pos, 'invariante': invariante}
    return wrapper


def criar_sistema_contratos():
    return {
        'contratar':      lambda fn, pre=None, pos=None, inv=None, nome=None:
                              contratar(fn, pre, pos, inv, nome),
        'pre':            lambda cond, msg='Pré-condição falhou': (
                              lambda *a, **kw: (lambda ok: ok if ok else (_ for _ in ()).throw(
                                  ViolacaoContrato('PRE', msg)))(cond(*a, **kw))
                          ),
        'afirmar':        lambda cond, msg='Asserção falhou': (
                              None if cond else (_ for _ in ()).throw(
                                  AssertionError(f"[Advak:afirmar] {msg}"))
                          ),
        'garantir':       lambda val, fn, msg='Garantia falhou': (
                              val if fn(val) else (_ for _ in ()).throw(
                                  ViolacaoContrato('GAR', msg, '?', val))
                          ),
        'nao_nulo':       lambda val, nome='valor': (
                              val if val is not None else (_ for _ in ()).throw(
                                  ViolacaoContrato('GAR', f"'{nome}' não pode ser nulo"))
                          ),
        'positivo':       lambda val, nome='valor': (
                              val if (isinstance(val, (int,float)) and val > 0)
                              else (_ for _ in ()).throw(
                                  ViolacaoContrato('GAR', f"'{nome}' deve ser positivo", '?', val))
                          ),
        'no_intervalo':   lambda val, mi, ma, nome='valor': (
                              val if mi <= val <= ma
                              else (_ for _ in ()).throw(
                                  ViolacaoContrato('GAR', f"'{nome}' deve estar em [{mi}, {ma}]", '?', val))
                          ),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORTAÇÃO — retorna todos os sistemas para o interpretador
# ══════════════════════════════════════════════════════════════════════════════

def criar_todos_sistemas():
    """Cria e retorna todos os sistemas avançados."""
    return {
        'tipos':       criar_sistema_tipos(),
        'canal':       criar_sistema_canais(),
        'eventos':     criar_sistema_eventos(),
        'stream':      criar_sistema_stream(),
        'deco':        criar_sistema_decoradores(),
        'fsm':         criar_sistema_fsm(),
        'obs':         criar_sistema_observable(),
        'contrato':    criar_sistema_contratos(),
    }
