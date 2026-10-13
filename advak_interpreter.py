"""
Advak 3.0 — Interpretador com PostgreSQL nativo
O objeto 'banco' fica disponível globalmente em qualquer programa .dk
"""
import asyncio, math, re, json, os, sys
import advak_tipos            # tipagem opcional (anotações); módulo pequeno, só biblioteca padrão
sys.setrecursionlimit(max(5000, sys.getrecursionlimit()))
from advak_db import AdvakDB, QueryBuilder, UpdateBuilder, DeleteBuilder

# Módulos opcionais — importados sob demanda (lazy) para startup rápido
_AVANCADO_OK   = None  # advak_advanced
_NATIVO_OK     = None  # advak_nativo
_MOBILE_OK     = None  # advak_mobile
_EMBARCADO_OK  = None  # advak_embarcado

def _get_avancado():
    global _AVANCADO_OK, _criar_avancado
    if _AVANCADO_OK is None:
        try:
            from advak_advanced import criar_todos_sistemas as _criar_avancado
            _AVANCADO_OK = True
        except ImportError:
            _AVANCADO_OK = False
    return _AVANCADO_OK

def _get_nativo():
    global _NATIVO_OK, _criar_compilador_nativo
    if _NATIVO_OK is None:
        try:
            from advak_nativo import criar_sistema_compilador as _criar_compilador_nativo
            _NATIVO_OK = True
        except ImportError:
            _NATIVO_OK = False
    return _NATIVO_OK

def _get_mobile():
    global _MOBILE_OK, _criar_mobile
    if _MOBILE_OK is None:
        try:
            from advak_mobile import criar_sistema_mobile as _criar_mobile
            _MOBILE_OK = True
        except ImportError:
            _MOBILE_OK = False
    return _MOBILE_OK

def _get_embarcado():
    global _EMBARCADO_OK, _criar_embarcado
    if _EMBARCADO_OK is None:
        try:
            from advak_embarcado import criar_sistema_embarcado as _criar_embarcado
            _EMBARCADO_OK = True
        except ImportError:
            _EMBARCADO_OK = False
    return _EMBARCADO_OK


class _BreakSignal(Exception): pass
class _ContinueSignal(Exception): pass
class _ReturnSignal(Exception):
    def __init__(self, v): self.value = v
class _YieldSignal(Exception):
    def __init__(self, v): self.value = v
class _TailCall(Exception):
    """Sinaliza uma chamada de cauda (TCO) para evitar stack overflow."""
    __slots__ = ('fn', 'args', 'scope')
    def __init__(self, fn, args, scope):
        self.fn = fn; self.args = args; self.scope = scope


class AdvakError(Exception): pass
class ImmutableError(AdvakError): pass

_GENERATOR_DONE = object()  # sentinel para fim de gerador


class AdvakFunction:
    def __init__(self, name, params, body, closure, is_async=False, is_generator=False):
        self.name=name; self.params=params; self.body=body
        self.closure=closure; self.is_async=is_async; self.is_generator=is_generator
        self.retorno = None      # tipo de retorno anotado (-> tipo); None = livre
    def __repr__(self): return f"<função {self.name or 'anônima'}>"


class AdvakGenerator:
    """Objeto gerador — iterável produzido por funções com produzir/yield."""
    def __init__(self, coro):
        self._coro = coro
        self._done = False
        self._value = None
    def __repr__(self): return "<gerador>"
    def __aiter__(self): return self
    async def __anext__(self):
        if self._done:
            raise StopAsyncIteration
        try:
            val = await self._coro.__anext__()
            return val
        except StopAsyncIteration:
            self._done = True
            raise


class PrologDB:
    """Motor de inferência lógica estilo Prolog."""
    def __init__(self):
        self.facts = {}   # predicate -> list of arg-tuples
        self.rules = {}   # predicate -> list of {head, body}

    def add_fact(self, predicate, args):
        self.facts.setdefault(predicate, []).append(tuple(args))

    def add_rule(self, predicate, head_args, body_goals):
        self.rules.setdefault(predicate, []).append({'head': head_args, 'body': body_goals})

    def query(self, predicate, args):
        """Retorna lista de dicionários de binding para cada solução."""
        # Identifica variáveis da query original (uppercase, sem sufixo de renomeação)
        query_vars = {a for a in args if isinstance(a, str) and len(a) > 0 and a[0].isupper()}
        solutions = []
        for sol in self._solve(predicate, args, {}):
            clean = {}
            for k, v in sol.items():
                # Só exporta variáveis originais da query (sem sufixo _N)
                base = k.split('_')[0] if '_' in k and k.split('_')[-1].isdigit() else k
                if base in query_vars or k in query_vars:
                    resolved = self._resolve(v, sol)
                    # Resolve encadeamentos
                    seen = set()
                    while isinstance(resolved, str) and resolved[0].isupper() and resolved not in seen:
                        seen.add(resolved)
                        resolved = self._resolve(resolved, sol)
                    clean[base] = resolved
            if clean:
                solutions.append(clean)
        return solutions

    _rule_counter = 0

    def _fresh_rule(self, rule):
        """Renomeia variáveis de uma regra para evitar conflito com query."""
        PrologDB._rule_counter += 1
        suffix = f'_{PrologDB._rule_counter}'
        mapping = {}

        def rename(term):
            if isinstance(term, str) and len(term) > 0 and (term[0].isupper() or term == '_'):
                if term not in mapping:
                    mapping[term] = term + suffix
                return mapping[term]
            return term

        new_head = [rename(a) for a in rule['head']]
        new_body = []
        for g in rule['body']:
            new_body.append({'predicate': g['predicate'], 'args': [rename(a) for a in g['args']]})
        return {'head': new_head, 'body': new_body}

    def _solve(self, predicate, args, bindings):
        # Tenta fatos
        for fact_args in self.facts.get(predicate, []):
            if len(fact_args) != len(args):
                continue
            new_bindings = dict(bindings)
            resolved_args = [self._resolve(a, bindings) for a in args]
            if self._unify_all(resolved_args, list(fact_args), new_bindings):
                yield new_bindings
        # Tenta regras (com renomeação de variáveis)
        for rule in self.rules.get(predicate, []):
            fresh = self._fresh_rule(rule)
            new_bindings = dict(bindings)
            resolved_args = [self._resolve(a, bindings) for a in args]
            if not self._unify_all(resolved_args, fresh['head'], new_bindings):
                continue
            yield from self._solve_goals(fresh['body'], new_bindings)

    def _solve_goals(self, goals, bindings):
        if not goals:
            yield bindings
            return
        g = goals[0]
        rest = goals[1:]
        resolved_args = [self._resolve(a, bindings) for a in g['args']]
        for sol in self._solve(g['predicate'], resolved_args, bindings):
            yield from self._solve_goals(rest, sol)

    def _unify(self, a, b, bindings):
        a = self._resolve(a, bindings)
        b = self._resolve(b, bindings)
        if isinstance(a, str) and a[0].isupper():  # variável Prolog
            bindings[a] = b; return True
        if isinstance(b, str) and b[0].isupper():
            bindings[b] = a; return True
        return a == b

    def _unify_all(self, alist, blist, bindings):
        if len(alist) != len(blist): return False
        for a, b in zip(alist, blist):
            if not self._unify(a, b, bindings): return False
        return True

    def _resolve(self, term, bindings):
        if isinstance(term, str) and term[0].isupper():
            return bindings.get(term, term)
        return term

class AdvakClass:
    def __init__(self, name, superclass, methods, statics=None, getters=None, setters=None):
        self.name=name; self.superclass=superclass; self.methods=methods
        self.statics=statics or {}; self.getters=getters or {}; self.setters=setters or {}
        self.fields={}
    def __repr__(self): return f"<classe {self.name}>"

class AdvakInstance:
    def __init__(self, klass):
        self.klass=klass; self.fields={}
    def get(self, name):
        if name in self.fields: return self.fields[name]
        m = self._find_method(name)
        if m: return m
        raise AdvakError(f"'{name}' não existe em {self.klass.name}")
    def _find_method(self, name):
        k = self.klass
        while k:
            if name in k.methods: return BoundMethod(self, k.methods[name])
            k = k.superclass
        return None
    def _find_setter(self, name):
        k = self.klass
        while k:
            if name in k.setters: return BoundMethod(self, k.setters[name])
            k = k.superclass
        return None
    def __repr__(self): return f"<{self.klass.name}>"

class BoundMethod:
    def __init__(self, inst, func): self.instance=inst; self.func=func


class Scope:
    """Scope otimizado com lookup iterativo para acesso rápido a variáveis."""

    def __init__(self, parent=None):
        self.vars   = {}
        self.parent = parent
        self.tipos  = None      # nome → verificador, para variáveis declaradas com tipo (seja x: inteiro)

    def get(self, name):
        # Unrolled lookup — evita recursão em cadeia longa
        scope = self
        while scope is not None:
            if name in scope.vars:
                return scope.vars[name]
            scope = scope.parent
        raise AdvakError(f"Variável '{name}' não definida")
    def set(self, name, value):
        # Verifica imutabilidade — __const_X marca variável como imutável
        if f'__const_{name}' in self.vars:
            raise ImmutableError(f"[Advak] Erro de imutabilidade: '{name}' é imutável e não pode ser reatribuído")
        if self.parent and f'__const_{name}' in (self.parent.vars if hasattr(self.parent, 'vars') else {}):
            raise ImmutableError(f"[Advak] Erro de imutabilidade: '{name}' é imutável e não pode ser reatribuído")
        if name in self.vars:
            if self.tipos is not None:
                verificador = self.tipos.get(name)
                if verificador is not None:
                    verificador(value)          # levanta AdvakError se o tipo não combinar
            self.vars[name]=value; return
        if self.parent: self.parent.set(name, value); return
        self.vars[name]=value
    def declare(self, name, value): self.vars[name]=value



# ══════════════════════════════════════════════════════════════════════════════
#  C/C++ — Tipos nativos Advak 5.0
# ══════════════════════════════════════════════════════════════════════════════

class AdvakStructType:
    """Tipo de struct — define os campos e defaults."""
    def __init__(self, name, fields):
        self.name   = name    # str
        self.fields = fields  # [{'name', 'type', 'default'}]
    def __repr__(self): return f"<struct {self.name}>"


class AdvakStructInstance:
    """Instância de struct — objeto com campos tipados."""
    def __init__(self, struct_type, values):
        self._type   = struct_type
        self._fields = dict(values)
    def get(self, name):
        if name in self._fields: return self._fields[name]
        if name in ('tipo', 'type'): return self._type.name
        raise AdvakError(f"Campo '{name}' não existe em struct {self._type.name}")
    def set(self, name, value):
        if name not in self._fields:
            raise AdvakError(f"Campo '{name}' não existe em struct {self._type.name}")
        self._fields[name] = value
    def to_dict(self):
        return dict(self._fields)
    def __repr__(self):
        fields = ', '.join(f"{k}: {v!r}" for k, v in self._fields.items())
        return f"{self._type.name} {{ {fields} }}"


class AdvakEnumType:
    """Tipo enum — variantes com valor inteiro ou payload."""
    def __init__(self, name, variants):
        self.name     = name
        self.variants = {}   # nome -> {'value': int, 'payload': [tipos]}
        for v in variants:
            self.variants[v['name']] = v
    def __repr__(self): return f"<enum {self.name}>"
    def __getattr__(self, name):
        if name.startswith('_'): raise AttributeError(name)
        if name == 'get':
            return lambda n, d=None: getattr(self, n) if n in self.variants else d
        if name in self.variants:
            v = self.variants[name]
            if v['payload']:
                # Retorna construtor de variante
                enum_type = self
                vname = name
                def _constructor(*args):
                    return AdvakEnumVariant(enum_type, vname, list(args))
                return _constructor
            return AdvakEnumVariant(self, name, [])
        raise AdvakError(f"Variante '{name}' não existe em enum {self.name}")


class AdvakEnumVariant:
    """Valor de variante enum."""
    def __init__(self, enum_type, variant_name, payload=None):
        self._enum    = enum_type
        self.nome     = variant_name
        self.name     = variant_name
        self.valor    = enum_type.variants[variant_name]['value']
        self.payload  = payload or []
    def get(self, name):
        if name in ('nome', 'name'):   return self.nome
        if name in ('valor', 'value'): return self.valor
        if name == 'payload':          return self.payload
        # Acesso por índice via nome do campo (payload[0], payload[1]...)
        fields = self._enum.variants[self.nome].get('payload', [])
        if name in fields:
            return self.payload[fields.index(name)]
        raise AdvakError(f"Propriedade '{name}' não existe em variante {self.nome}")
    def __eq__(self, other):
        if isinstance(other, AdvakEnumVariant):
            return self._enum is other._enum and self.nome == other.nome
        if isinstance(other, str):
            return self.nome == other
        if isinstance(other, (int, float)):
            return self.valor == other
        return False
    def __repr__(self): return f"{self._enum.name}::{self.nome}"


class AdvakRef:
    """Referência mutável a um valor — simula ponteiro C."""
    def __init__(self, name, scope):
        self._name  = name    # nome da variável no escopo
        self._scope = scope   # escopo onde vive
    @property
    def valor(self):
        return self._scope.get(self._name)
    @valor.setter
    def valor(self, v):
        self._scope.set(self._name, v)
    def get(self, prop):
        if prop in ('valor', 'value', 'deref'): return self.valor
        if prop in ('nome', 'name'): return self._name
        raise AdvakError(f"Propriedade '{prop}' não existe em ref")
    def __repr__(self): return f"<ref {self._name} = {self.valor!r}>"


class AdvakMacro:
    """Macro inline — substituição de texto em tempo de execução."""
    def __init__(self, name, params, body_node, def_scope):
        self.name      = name
        self.params    = params      # ['a', 'b', ...]
        self.body      = body_node   # AST node
        self.def_scope = def_scope
    def __repr__(self): return f"<macro {self.name}>"


# ══════════════════════════════════════════════════════════════════════════════
#  Haskell — Tipos Algébricos de Dados (ADT)
# ══════════════════════════════════════════════════════════════════════════════

class AdvakADTType:
    """
    Tipo Algébrico de Dados — análogo a data em Haskell ou enum em Rust.
    Exemplo:  tipo Arvore { Folha, No(esq, val, dir) }
    """
    def __init__(self, name, variants, type_params=None):
        self.name        = name
        self.type_params = type_params or []
        self.variants    = {}   # nome -> {'name', 'fields': [{'name','type'}]}
        for v in variants:
            self.variants[v['name']] = v
    def __repr__(self): return f"<tipo {self.name}>"
    def __getattr__(self, name):
        if name.startswith('_') or name == 'get':      # hasattr(obj, 'get') não pode virar AdvakError
            raise AttributeError(name)
        if name in self.variants:
            v = self.variants[name]
            if v['fields']:
                adt = self
                vname = name
                def _ctor(*args):
                    if len(args) != len(v['fields']):
                        raise AdvakError(
                            f"{adt.name}::{vname} espera {len(v['fields'])} argumento(s), recebeu {len(args)}")
                    return AdvakADTVariant(adt, vname, list(args))
                return _ctor
            return AdvakADTVariant(self, name, [])
        raise AdvakError(f"Variante '{name}' não existe em tipo {self.name}")


class AdvakADTVariant:
    """
    Valor de variante de um ADT.
    Ex: No(Folha, 5, Folha)  →  AdvakADTVariant(Arvore, 'No', [Folha, 5, Folha])
    """
    def __init__(self, adt_type, variant_name, args):
        self._adt     = adt_type
        self.nome     = variant_name
        self.name     = variant_name
        self._args    = args
        # Mapeia nomes de campos para valores
        fields = adt_type.variants[variant_name]['fields']
        self._fields  = {}
        for i, f in enumerate(fields):
            self._fields[f['name']] = args[i] if i < len(args) else None
    def get(self, prop):
        if prop in ('nome', 'name'):   return self.nome
        if prop in ('tipo', 'type'):   return self._adt.name
        if prop == 'args':             return self._args
        if prop in self._fields:       return self._fields[prop]
        # Acesso por índice: _0, _1, ...
        if prop.startswith('_') and prop[1:].isdigit():
            idx = int(prop[1:])
            return self._args[idx] if idx < len(self._args) else None
        raise AdvakError(f"Campo '{prop}' não existe em {self._adt.name}::{self.nome}")
    def __eq__(self, other):
        if isinstance(other, AdvakADTVariant):
            return self._adt is other._adt and self.nome == other.nome and self._args == other._args
        if isinstance(other, str):
            return self.nome == other
        return False
    def __repr__(self):
        if self._args:
            args = ', '.join(repr(a) for a in self._args)
            return f"{self._adt.name}::{self.nome}({args})"
        return f"{self._adt.name}::{self.nome}"


# ══════════════════════════════════════════════════════════════════════════════
#  Haskell — Imutabilidade profunda
# ══════════════════════════════════════════════════════════════════════════════

class ImmutableError(Exception): pass



def _tipo_pt(valor):
    """Retorna o nome do tipo em português para mensagens de erro."""
    if valor is None:       return 'nulo'
    if isinstance(valor, bool):  return 'booleano'
    if isinstance(valor, int):   return 'número inteiro'
    if isinstance(valor, float): return 'número decimal'
    if isinstance(valor, str):   return 'texto'
    if isinstance(valor, list):  return 'lista'
    if isinstance(valor, dict):  return 'objeto'
    nome = type(valor).__name__
    mapa = {
        'NoneType': 'nulo', 'bool': 'booleano', 'int': 'número',
        'float': 'número', 'str': 'texto', 'list': 'lista',
        'dict': 'objeto', 'AdvakFunction': 'função',
        'AdvakInstance': 'instância', 'AdvakClass': 'classe',
    }
    return mapa.get(nome, nome)


def _deep_freeze(value, seen=None):
    """
    Congela profundamente um valor — dicts e listas tornam-se imutáveis.
    Retorna um wrapper imutável ou o valor original (para tipos já imutáveis).
    """
    if seen is None:
        seen = set()
    vid = id(value)
    if vid in seen:
        return value
    seen.add(vid)

    if isinstance(value, dict):
        frozen = {k: _deep_freeze(v, seen) for k, v in value.items()}
        return FrozenMap(frozen)
    if isinstance(value, list):
        return FrozenList([_deep_freeze(v, seen) for v in value])
    if isinstance(value, AdvakStructInstance):
        value._frozen = True
        for k in value._fields:
            value._fields[k] = _deep_freeze(value._fields[k], seen)
        return value
    if isinstance(value, AdvakADTVariant):
        value._frozen = True
        value._args = [_deep_freeze(a, seen) for a in value._args]
        return value
    # Números, strings, bools, None → já imutáveis
    return value


class FrozenMap:
    """Dicionário imutável — equivalente a Map imutável do Haskell."""
    def __init__(self, data):
        object.__setattr__(self, '_data', dict(data))
        object.__setattr__(self, '_frozen', True)
    def get(self, key):
        d = object.__getattribute__(self, '_data')
        if key in d: return d[key]
        # Métodos de leitura
        if key == 'tamanho': return len(d)
        if key == 'chaves':  return list(d.keys())
        if key == 'valores': return list(d.values())
        if key in ('para_mapa', 'to_dict'): return dict(d)
        if key == 'contem': return lambda k: k in d
        raise AdvakError(f"Chave '{key}' não existe no mapa imutável")
    def __contains__(self, k):
        return k in object.__getattribute__(self, '_data')
    def __iter__(self):
        return iter(object.__getattribute__(self, '_data'))
    def __repr__(self):
        d = object.__getattribute__(self, '_data')
        pairs = ', '.join(f'{k}: {v!r}' for k, v in d.items())
        return f'#{{{pairs}}}'


class FrozenList:
    """Lista imutável — equivalente a lista Haskell."""
    def __init__(self, items):
        object.__setattr__(self, '_items', list(items))
        object.__setattr__(self, '_frozen', True)
    def get(self, prop):
        items = object.__getattribute__(self, '_items')
        if prop in ('tamanho', 'comprimento'): return len(items)
        if prop == 'primeiro':  return items[0] if items else None
        if prop == 'ultimo':    return items[-1] if items else None
        if prop == 'cauda':     return FrozenList(items[1:])
        if prop == 'cabeca':    return items[0] if items else None
        if prop == 'vazia':     return len(items) == 0
        if prop == 'contem':    return lambda x: x in items
        if prop == 'para_lista': return list(items)
        raise AdvakError(f"Propriedade '{prop}' não existe na lista imutável")
    def __getitem__(self, idx):
        return object.__getattribute__(self, '_items')[idx]
    def __len__(self):
        return len(object.__getattribute__(self, '_items'))
    def __iter__(self):
        return iter(object.__getattribute__(self, '_items'))
    def __repr__(self):
        items = object.__getattribute__(self, '_items')
        return '#[' + ', '.join(repr(i) for i in items) + ']'


def _canvas_to_svg(cmds, width=800, height=600):
    """Converte lista de comandos canvas em SVG string."""
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    bg = '#ffffff'
    for c in cmds:
        if c['cmd'] == 'background':
            bg = c['cor']
    lines.insert(1, f'<rect width="{width}" height="{height}" fill="{bg}"/>')
    for c in cmds:
        cmd = c['cmd']
        if cmd == 'rect':
            style = f'fill:{c["cor"]}' if c.get('preenchido', True) else f'fill:none;stroke:{c["cor"]}'
            lines.append(f'<rect x="{c["x"]}" y="{c["y"]}" width="{c["w"]}" height="{c["h"]}" style="{style}"/>')
        elif cmd == 'circle':
            style = f'fill:{c["cor"]}' if c.get('preenchido', True) else f'fill:none;stroke:{c["cor"]}'
            lines.append(f'<circle cx="{c["x"]}" cy="{c["y"]}" r="{c["r"]}" style="{style}"/>')
        elif cmd == 'line':
            lines.append(f'<line x1="{c["x1"]}" y1="{c["y1"]}" x2="{c["x2"]}" y2="{c["y2"]}" stroke="{c["cor"]}" stroke-width="{c.get("espessura",1)}"/>')
        elif cmd == 'text':
            lines.append(f'<text x="{c["x"]}" y="{c["y"]}" fill="{c["cor"]}" font="{c.get("fonte","16px sans-serif")}">{c["txt"]}</text>')
    lines.append('</svg>')
    return '\n'.join(lines)


class _CtxTipos:
    """Contexto da tipagem opcional: reconhece funções e tipos do usuário (classe, estrutura, enum, ADT)."""

    def __init__(self, scope):
        self.scope = scope

    def eh_funcao(self, v):
        return isinstance(v, (AdvakFunction, BoundMethod)) or callable(v)

    def conhece(self, nome):
        # a estrutura é registrada como _struct_<Nome> (o nome comum guarda o construtor)
        for chave in (nome, f"_struct_{nome}"):
            try:
                obj = self.scope.get(chave)
            except AdvakError:
                continue
            if isinstance(obj, (AdvakClass, AdvakStructType, AdvakEnumType, AdvakADTType)):
                return True
        return False

    def instancia_de(self, v, nome):
        if isinstance(v, AdvakInstance):
            k = v.klass
            while k:
                if k.name == nome:
                    return True
                k = k.superclass
            return False
        if isinstance(v, AdvakStructInstance):
            return v._type.name == nome
        if isinstance(v, AdvakEnumVariant):
            return v._enum.name == nome
        if isinstance(v, AdvakADTVariant):
            return v._adt.name == nome
        return False

    def nome_do_valor(self, v):
        if isinstance(v, AdvakInstance):
            return f"instância de {v.klass.name}"
        if isinstance(v, AdvakStructInstance):
            return f"estrutura {v._type.name}"
        if isinstance(v, AdvakEnumVariant):
            return f"enum {v._enum.name}"
        if isinstance(v, AdvakADTVariant):
            return f"tipo {v._adt.name}"
        if self.eh_funcao(v):
            return "funcao"
        return type(v).__name__


class AdvakInterpreter:
    def __init__(self, ast, db_config=None, ai_api_key=None):
        self.ast = ast
        self.ai_api_key = ai_api_key
        self._loaded_modules = {}   # cache: path -> exported scope
        self._ai_modelo    = 'llama-3.3-70b-versatile'  # modelo atual
        self._ai_contexto  = []       # histórico da conversa
        self._ai_sistema   = None     # system prompt atual
        self._ai_providers = {        # provedores disponíveis
            'groq':      {'env': 'GROQ_API_KEY',       'modelos': ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'gemma2-9b-it']},
            'openrouter':{'env': 'OPENROUTER_API_KEY',  'modelos': ['meta-llama/llama-3.3-70b-instruct:free', 'qwen/qwen3-235b-a22b:free', 'deepseek/deepseek-r1-0528:free']},
            'deepseek':  {'env': 'DEEPSEEK_API_KEY',    'modelos': ['deepseek-chat', 'deepseek-reasoner']},
            'gemini':    {'env': 'GEMINI_API_KEY',      'modelos': ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']},
        }
        self._ai_provedor  = 'groq'   # provedor atual
        self.prolog_db     = PrologDB()  # base de conhecimento lógico
        self._canvas_cmds  = []          # fila de comandos Canvas 2D
        self.global_scope = Scope()
        # Configuração do banco
        cfg = db_config or {}
        # Lazy: só cria AdvakDB se db_config foi explicitamente passado
        # Isso evita timeout de conexão PostgreSQL ao executar scripts simples
        if db_config:
            self.db = AdvakDB(
                host     = cfg.get('host',     'localhost'),
                port     = cfg.get('port',     5432),
                user     = cfg.get('user',     'postgres'),
                password = cfg.get('password', ''),
                dbname   = cfg.get('dbname',   'postgres'),
            )
        else:
            self.db = AdvakDB()  # sem credenciais — conecta só sob demanda
        self._setup_builtins()

    def _setup_builtins(self):
        g = self.global_scope

        # ── Módulos modernos (Advak 4.0) ─────────────────────────────────────
        try:
            from advak_modern import (
                AdvakTipo, AdvakWebSocket, AdvakORM,
                AdvakCache, AdvakValidator, AdvakFila,
                AdvakLogger, AdvakCrypto, AdvakEnv, AdvakRateLimiter
            )
            _tipos   = AdvakTipo()
            _ws      = AdvakWebSocket()
            _orm     = AdvakORM(self.db)
            _cache   = AdvakCache()
            _validar = AdvakValidator()
            _fila    = AdvakFila()
            _log     = AdvakLogger()
            _crypto  = AdvakCrypto()
            _env     = AdvakEnv()
            _limite  = AdvakRateLimiter()

            g.declare('tipos', {
                'schema':   _tipos.schema,
                'validar':  _tipos.validar,
                'moldar':   _tipos.moldar,
                'inferir':  _tipos.inferir,
                'texto':    'Texto',
                'numero':   'Numero',
                'inteiro':  'Inteiro',
                'decimal':  'Decimal',
                'booleano': 'Booleano',
                'lista':    'Lista',
                'mapa':     'Mapa',
                'nulo':     'Nulo',
            })

            g.declare('ws', {
                'ao_conectar':    _ws.ao_conectar,
                'ao_mensagem':    _ws.ao_mensagem,
                'ao_desconectar': _ws.ao_desconectar,
                'enviar':         _ws.enviar,
                'broadcast':      _ws.broadcast,
                'clientes':       _ws.clientes_conectados,
                'total':          _ws.total_clientes,
                'iniciar':        lambda porta=9001, host='localhost': _ws.iniciar(porta, host),
            })

            g.declare('orm', {
                'modelo': _orm.modelo,
            })

            g.declare('cache', {
                'definir':          _cache.definir,
                'obter':            _cache.obter,
                'remover':          _cache.remover,
                'limpar':           _cache.limpar,
                'ou_buscar':        _cache.ou_buscar,
                'invalidar':        _cache.invalidar_prefixo,
                'estatisticas':     _cache.estatisticas,
                'memoizar':         _cache.memoizar,
                'conectar_redis':   _cache.conectar_redis,
            })

            g.declare('validar', {
                'schema':           _validar.schema,
                'verificar':        _validar.verificar,
                'verificar_ou_erro':_validar.verificar_ou_erro,
                'texto':            _validar.texto,
                'numero':           _validar.numero,
                'email':            _validar.email,
                'booleano':         _validar.booleano,
                'lista':            _validar.lista,
                'regex':            _validar.regex,
                'opcoes':           _validar.opcoes,
                'data':             _validar.data,
            })

            g.declare('fila', {
                'tarefa':       _fila.tarefa,
                'adicionar':    _fila.adicionar,
                'iniciar':      lambda workers=2: _fila.iniciar(workers),
                'parar':        _fila.parar,
                'estatisticas': _fila.estatisticas,
            })

            g.declare('log', {
                'configurar': _log.configurar,
                'debug':      _log.debug,
                'info':       _log.info,
                'aviso':      _log.aviso,
                'erro':       _log.erro,
                'critico':    _log.critico,
                'sucesso':    _log.sucesso,
            })

            g.declare('crypto', {
                'hash_senha':      _crypto.hash_senha,
                'verificar_senha': _crypto.verificar_senha,
                'gerar_token':     _crypto.gerar_token,
                'verificar_token': _crypto.verificar_token,
                'uuid':            _crypto.uuid,
                'aleatorio':       _crypto.aleatorio,
                'encriptar':       _crypto.encriptar,
                'decriptar':       _crypto.decriptar,
            })

            g.declare('env', {
                'carregar':   _env.carregar,
                'texto':      _env.texto,
                'numero':     _env.numero,
                'booleano':   _env.booleano,
                'lista':      _env.lista,
                'todos':      _env.todos,
                'definir':    _env.definir,
                'exportar':   _env.exportar,
            })

            g.declare('limite', {
                'configurar': _limite.configurar,
                'permitir':   _limite.permitir,
                'restante':   _limite.restante,
                'resetar':    _limite.resetar,
            })

        except Exception as _e:
            pass  # módulos opcionais — não quebra se falhar

        # ── Servidor HTTP nativo (substituído por advak_web.py) ───────────────
        pass  # advak_web.py handles this below

        # ── Interface gráfica (lazy — só importa quando gui.janela() é chamado) ─
        class _LazyGUI:
            """Proxy REALMENTE lazy: só importa tkinter quando o método é CHAMADO.
            __getattr__ retorna uma função wrapper, NÃO chama _get() imediatamente.
            Isso evita o import de tkinter durante _setup_builtins.
            """
            _instancia = None

            def _get(self):
                if self._instancia is None:
                    try:
                        from advak_gui_modern import AdvakGUIModern
                        self._instancia = AdvakGUIModern()
                    except Exception:
                        try:
                            from advak_gui import AdvakGUI
                            self._instancia = AdvakGUI()
                        except Exception:
                            self._instancia = None
                return self._instancia

            def __getattr__(self, nome):
                # Retorna wrapper lazy — tkinter só é importado quando o wrapper é CHAMADO
                _self = self
                def _wrapper(*args, **kwargs):
                    inst = _self._get()
                    if inst is None:
                        raise RuntimeError(
                            f"GUI não disponível. Instale tkinter: pip install tk")
                    return getattr(inst, nome)(*args, **kwargs)
                # Para atributos não-callable (propriedades), retornar diretamente
                # mas só quando necessário
                _wrapper._lazy_nome = nome
                _wrapper._lazy_gui  = self
                return _wrapper

        _gui = _LazyGUI()
        try:
            g.declare('gui', {
                'janela':       _gui.janela,
                'label':        _gui.label,
                'botao':        lambda pai, texto='', ao_clicar=None, cor=None, largura=None, estilo='primario': _gui.botao(
                    pai, texto, ao_clicar, cor, largura,
                    # Normaliza estilo: aceita PT-BR e converte para nome interno
                    {'primario':'primario','secundario':'secundario','perigo':'perigo',
                     'sucesso':'sucesso','primary':'primario','secondary':'secundario',
                     'danger':'perigo','success':'sucesso','warning':'secundario',
                     'info':'primario'}.get(str(estilo).lower(), 'primario')
                ),
                'campo':        _gui.campo,
                'area_texto':   _gui.area_texto,
                'tabela':       _gui.tabela,
                'lista':        _gui.lista,
                'caixa_selecao':_gui.caixa_selecao,
                'checkbox':     _gui.checkbox,
                'barra_progresso': _gui.barra_progresso,
                'separador':    _gui.separador,
                'frame':        _gui.frame,
                'frame_horizontal': _gui.frame_horizontal,
                'menu_bar':     _gui.menu_bar,
                'abas':         _gui.abas,
                'alerta':       _gui.alerta,
                'erro':         _gui.erro,
                'aviso':        _gui.aviso,
                'confirmar':    _gui.confirmar,
                'pedir':        _gui.pedir,
                'pedir_numero': _gui.pedir_numero,
                'escolher_arquivo': _gui.escolher_arquivo,
                'abrir_arquivo':    _gui.escolher_arquivo,  # alias PT-BR
                'salvar_arquivo':   _gui.salvar_arquivo,
                'escolher_cor': _gui.escolher_cor,
                'escolher_pasta': _gui.escolher_pasta,
                'iniciar':      _gui.iniciar,
                'parar':        _gui.parar,
                'apos':         _gui.apos,
                'repetir':      _gui.repetir,
                'switch':           getattr(_gui,'switch',  lambda *a,**k: None),
                'toggle':           getattr(_gui,'switch',  lambda *a,**k: None),
                'atualizar':        _gui.atualizar,
                'tema':             _gui.tema,
                # ── Componentes modernos ──────────────────────────────
                'toast':            getattr(_gui,'toast',           lambda *a,**k: None),
                'card':             getattr(_gui,'card',            lambda *a,**k: None),
                'slider':           getattr(_gui,'slider',          lambda *a,**k: None),
                'badge':            getattr(_gui,'badge',           lambda *a,**k: None),
                'barra_status':     getattr(_gui,'barra_status',    lambda *a,**k: None),
                'grafico':          getattr(_gui,'grafico',         lambda *a,**k: None),
                'arvore':           getattr(_gui,'arvore',          lambda *a,**k: None),
                'busca':            getattr(_gui,'busca',           lambda *a,**k: None),
                'calendario':       getattr(_gui,'calendario',      lambda *a,**k: None),
                'modal':            getattr(_gui,'modal',           lambda *a,**k: None),
                'splitter':         getattr(_gui,'splitter',        lambda *a,**k: None),
                'cor_hex':          getattr(_gui,'cor_hex',         lambda v: v),
                'icone':            getattr(_gui,'icone',           lambda v: v),
                # ── C# GUI — DataGrid, MVVM, Animações, Drag&Drop ─────
                'datagrid':         getattr(_gui,'datagrid',           lambda *a,**k: None),
                'criar_viewmodel':  getattr(_gui,'criar_viewmodel',    lambda *a,**k: None),
                'viewmodel':        getattr(_gui,'criar_viewmodel',    lambda *a,**k: None),
                'animar':           getattr(_gui,'animar',             lambda *a,**k: None),
                'animar_sequencia': getattr(_gui,'animar_sequencia',   lambda *a,**k: None),
                'animar_loop':      getattr(_gui,'animar_loop',        lambda *a,**k: None),
                'habilitar_drag':   getattr(_gui,'habilitar_drag',     lambda *a,**k: None),
                'habilitar_drop':   getattr(_gui,'habilitar_drop',     lambda *a,**k: None),
                'kanban':           getattr(_gui,'kanban',             lambda *a,**k: None),
                         })
        except Exception:
            pass

        # ── Compilador ────────────────────────────────────────────────────────
        try:
            from advak_compiler import AdvakCompiler
            _comp = AdvakCompiler()
            g.declare('compilador', {
                'compilar': lambda arq, opts=None: _comp.compilar(arq, opts),
                'limpar':   lambda nome=None: _comp.limpar(nome),
                'info':     _comp.info,
            })
        except Exception:
            pass

        # ── Objeto banco (PostgreSQL nativo) ────────────────────────────────
        banco_obj = {
            # Conexão
            # banco.conectar("mysql://...") / banco.conectar("mysql", host=...) → conector novo;
            # banco.conectar() / banco.conectar("nome_do_banco") → PostgreSQL legado
            'conectar':         self._banco_conectar,
            'bancos':           lambda: __import__('advak_conectores').listar_bancos(),
            'desconectar':      lambda: self.db.desconectar(),
            'usar':             lambda nome: self.db.usar(nome),
            # Bancos
            'criar_banco':      lambda nome: self.db.criar_banco(nome),
            'listar_bancos':    lambda: self.db.listar_bancos(),
            'apagar_banco':     lambda nome: self.db.apagar_banco(nome),
            # Tabelas
            'criar_tabela':     lambda nome, campos, **kw: self.db.criar_tabela(nome, campos, **kw),
            'tabela':           lambda nome, campos, **kw: self.db.criar_tabela(nome, campos, **kw),
            'apagar_tabela':    lambda nome, cas=False: self.db.apagar_tabela(nome, cas),
            'listar_tabelas':   lambda: self.db.listar_tabelas(),
            'descrever_tabela': lambda nome: self.db.descrever_tabela(nome),
            'renomear_tabela':  lambda n, nn: self.db.renomear_tabela(n, nn),
            'adicionar_coluna': lambda t, c, d: self.db.adicionar_coluna(t, c, d),
            'remover_coluna':   lambda t, c: self.db.remover_coluna(t, c),
            'migrar':           lambda nome, campos: self.db.migrar(nome, campos),
            # CRUD
            'inserir':          lambda t, d: self.db.inserir(t, d),
            'inserir_varios':   lambda t, l: self.db.inserir_varios(t, l),
            'buscar':           lambda t: self.db.buscar(t),
            'buscar_id':        lambda t, i: self.db.buscar_por_id(t, i),
            'atualizar':        lambda t, d: self.db.atualizar(t, d),
            'deletar':          lambda t: self.db.deletar(t),
            'contar':           lambda t, *a: self.db.contar(t, *a),
            # SQL puro
            'sql':              lambda q, *p: self.db.sql(q, list(p) if p else None),
            # Transações
            'iniciar':          lambda: self.db.iniciar_transacao(),
            'confirmar':        lambda: self.db.confirmar(),
            'reverter':         lambda: self.db.reverter(),
            # Auto-setup framework
            'auto_setup':       lambda dbname, tabelas: self.db.auto_setup(dbname, tabelas),
            'configurar':       lambda dbname, tabelas: self.db.auto_setup(dbname, tabelas),
        }
        g.declare('banco', banco_obj)

        # ── Matemática ──────────────────────────────────────────────────────
        g.declare('Mat', {
            'pi': math.pi, 'e': math.e,
            'raiz':   math.sqrt, 'abs': abs,
            'piso':   math.floor, 'teto': math.ceil,
            'arred':  round, 'max': max, 'min': min,
            'pot':    pow, 'log': math.log,
            'aleatorio': __import__('random').random,
            'inteiro_aleatorio': __import__('random').randint,
        })
        g.declare('Math', g.get('Mat'))

        # ── Funções matemáticas globais (sem precisar de Mat.) ────────────
        g.declare('arred',   round)
        g.declare('piso',    math.floor)
        g.declare('teto',    math.ceil)
        g.declare('raiz',    math.sqrt)
        g.declare('pot',     pow)
        g.declare('log',     math.log)
        g.declare('sen',     math.sin)
        g.declare('cos',     math.cos)
        g.declare('tan',     math.tan)
        g.declare('abs',     abs)
        g.declare('aleatorio',         __import__('random').random)
        g.declare('inteiro_aleatorio', __import__('random').randint)

        # ── JSON ────────────────────────────────────────────────────────────
        g.declare('JSON', {
            # PT-BR
            'codificar':   lambda v: json.dumps(v, ensure_ascii=False, default=str),
            'decodificar': lambda s: json.loads(str(s)),
            'formatar':    lambda v: json.dumps(v, ensure_ascii=False, indent=2, default=str),
            # EN aliases
            'stringify': lambda v: json.dumps(v, ensure_ascii=False, default=str),
            'parse':     lambda s: json.loads(str(s)),
        })

        # ── Texto ───────────────────────────────────────────────────────────
        g.declare('Texto', {
            # Comprimento
            'tamanho':    lambda s: len(str(s)),
            'comprimento':lambda s: len(str(s)),
            # Transformação
            'maiusculo':  lambda s: str(s).upper(),
            'minusculo':  lambda s: str(s).lower(),
            'capitalizar':lambda s: str(s).capitalize(),
            'titulo':     lambda s: str(s).title(),
            'inverter':   lambda s: str(s)[::-1],
            # Busca e verificação
            'dividir':    lambda s, sep=' ': str(s).split(sep),
            'substituir': lambda s, a, b: str(s).replace(a, b),
            'contem':     lambda s, sub: sub in str(s),
            'começa':     lambda s, p: str(s).startswith(p),
            'termina':    lambda s, p: str(s).endswith(p),
            'encontrar':  lambda s, sub: str(s).find(sub),
            'conta':      lambda s, sub: str(s).count(sub),
            'indice':     lambda s, sub: str(s).index(sub) if sub in str(s) else -1,
            # Limpeza
            'aparar':     lambda s: str(s).strip(),
            'strip':      lambda s: str(s).strip(),
            'lstrip':     lambda s: str(s).lstrip(),
            'rstrip':     lambda s: str(s).rstrip(),
            'upper':      lambda s: str(s).upper(),
            'lower':      lambda s: str(s).lower(),
            'title':      lambda s: str(s).title(),
            'split':      lambda s, sep=None: str(s).split(sep),
            'join':       lambda sep, lst: str(sep).join(str(x) for x in lst),
            'replace':    lambda s, a, b: str(s).replace(a, b),
            'startswith': lambda s, p: str(s).startswith(p),
            'endswith':   lambda s, p: str(s).endswith(p),
            'find':       lambda s, sub: str(s).find(sub),
            'index':      lambda s, sub: str(s).index(sub),
            'count':      lambda s, sub: str(s).count(sub),
            'format':     lambda s, *a, **k: str(s).format(*a, **k),
            'encode':     lambda s, enc='utf-8': str(s).encode(enc),
            'isdigit':    lambda s: str(s).isdigit(),
            'isalpha':    lambda s: str(s).isalpha(),
            'isspace':    lambda s: str(s).isspace(),
            'isnumeric':  lambda s: str(s).isnumeric(),
            'zfill':      lambda s, w: str(s).zfill(w),
            'center':     lambda s, w, c=' ': str(s).center(w, c),
            'ljust':      lambda s, w, c=' ': str(s).ljust(w, c),
            'rjust':      lambda s, w, c=' ': str(s).rjust(w, c),
            'aparar_esq': lambda s: str(s).lstrip(),
            'aparar_dir': lambda s: str(s).rstrip(),
            'remover':    lambda s, chars: str(s).strip(chars),
            # Fatia e extração
            'slice':      lambda s, ini, fim=None: str(s)[ini:fim],
            'fatia':      lambda s, ini, fim=None: str(s)[ini:fim],
            'char':       lambda s, i: str(s)[i] if 0 <= i < len(str(s)) else '',
            'primeiros':  lambda s, n: str(s)[:n],
            'ultimos':    lambda s, n: str(s)[-n:] if n else '',
            # Alias: ultimo char / primeiro char (sem parâmetros)
            'ultimo':     lambda s: str(s)[-1] if str(s) else '',
            'primeiro':   lambda s: str(s)[0]  if str(s) else '',
            # Padding e alinhamento
            'preencher_esq': lambda s, n, c=' ': str(s).rjust(n, c),
            'preencher_dir': lambda s, n, c=' ': str(s).ljust(n, c),
            'centralizar':   lambda s, n, c=' ': str(s).center(n, c),
            'zfill':         lambda s, n: str(s).zfill(n),
            # Formatação
            'formato':    lambda s, *args: str(s).format(*args),
            # Verificação de conteúdo
            'e_numero':   lambda s: str(s).lstrip('-').replace('.','',1).isdigit(),
            'e_inteiro':  lambda s: str(s).lstrip('-').isdigit(),
            'e_alfa':     lambda s: str(s).isalpha(),
            'e_alfanum':  lambda s: str(s).isalnum(),
            'e_vazia':    lambda s: str(s).strip() == '',
            'e_maiusculo':lambda s: str(s).isupper(),
            'e_minusculo':lambda s: str(s).islower(),
            # Conversão
            'para_lista': lambda s: list(str(s)),
            'codificar':  lambda s, enc='utf-8': str(s).encode(enc),
            # Unir lista de strings
            'unir':       lambda sep, lst: sep.join(str(x) for x in lst),
            'juntar':     lambda lst, sep='': sep.join(str(x) for x in lst),
            # Repetir
            'repetir':    lambda s, n: str(s) * n,
            # Regex (básico)
            'padrao':     lambda s, pat: bool(__import__('re').search(pat, str(s))),
            'extrair':    lambda s, pat: __import__('re').findall(pat, str(s)),
            'sub':        lambda s, pat, rep: __import__('re').sub(pat, rep, str(s)),
        })

        # ── Lista ───────────────────────────────────────────────────────────
        g.declare('Lista', {
            'intervalo': lambda a, b=None, s=1: list(range(a,b,s)) if b else list(range(a)),
            'de':        lambda *args: list(args),
            'unir':      lambda lst, sep='': sep.join(str(x) for x in lst),
            'map':       lambda lst, fn: [self._call_sync(fn, [x]) for x in lst],
            'filtrar':   lambda lst, fn: [x for x in lst if self._call_sync(fn, [x])],
            'ordenar':   lambda lst, rev=False: sorted(lst, reverse=rev),
            'unico':     lambda lst: list(dict.fromkeys(lst)),
            'flat':      lambda lst: [x for sub in lst for x in (sub if isinstance(sub, list) else [sub])],
        })

        # ── IA Multi-modelo ──────────────────────────────────────────────────
        _interp = self
        g.declare('IA', {
            'perguntar':    lambda p, sys=None: _interp._ai_call_sync(p, sys),
            'chat':         lambda p: _interp._ai_call_sync(p, usar_contexto=True),
            'sem_contexto': lambda p: _interp._ai_call_sync(p, usar_contexto=False),
            'modelo':       lambda m=None: _interp._ai_set_modelo(m),
            'provedor':     lambda p=None: _interp._ai_set_provedor(p),
            'sistema':      lambda s=None: _interp._ai_set_sistema(s),
            'memoria':      lambda: list(_interp._ai_contexto),
            'limpar':       lambda: _interp._ai_contexto.clear() or 'Contexto limpo',
            'provedores':   lambda: list(_interp._ai_providers.keys()),
            'modelos':      lambda: _interp._ai_providers.get(_interp._ai_provedor, {}).get('modelos', []),
            'info':         lambda: {
                'provedor': _interp._ai_provedor,
                'modelo':   _interp._ai_modelo,
                'mensagens':len(_interp._ai_contexto),
                'sistema':  _interp._ai_sistema or '(nenhum)',
            },
        })

        # ── IA com API única (advak_ia): seja ia = ia.conectar("anthropic") ───
        # O global `IA` (maiúsculo, acima) continua existindo para os programas antigos.
        # A IA é opcional: o módulo advak_ia só é importado quando o programa chama ia.conectar(...)
        # (ou ia.registrar / ia.provedores). Até lá não há import, rede nem custo.
        def _ia_lazy(nome):
            def _f(*a, **k):
                import advak_ia as _nia
                try:
                    return getattr(_nia, nome)(*a, **k)
                except _nia.ErroIA as e:
                    raise AdvakError(str(e))
            return _f
        g.declare('ia', {
            'conectar':   _ia_lazy('conectar'),
            'registrar':  _ia_lazy('registrar'),
            'provedores': _ia_lazy('listar_provedores'),
        })

        # ── Documentos (advak_documentos): documento.ler("a.pdf") ───────────────
        # Também sob demanda: o módulo (e os drivers pypdf, docx...) só são importados ao usar.
        def _doc_lazy(nome):
            def _f(*a, **k):
                import advak_documentos as _nd
                try:
                    return getattr(_nd, nome)(*a, **k)
                except _nd.ErroDocumento as e:
                    raise AdvakError(str(e))
            return _f
        g.declare('documento', {
            'ler':      _doc_lazy('ler'),
            'formatos': _doc_lazy('formatos'),
        })

        # ── Sistema de arquivos ─────────────────────────────────────────────
        # ── Módulo de Arquivos expandido ─────────────────────────────────────
        def _ler_arquivo(p, modo='utf-8'):
            try:
                with open(p, 'r', encoding=modo) as _f: return _f.read()
            except FileNotFoundError:
                raise AdvakError(f"Arquivo não encontrado: '{p}'")
            except Exception as e:
                raise AdvakError(f"Erro ao ler '{p}': {e}")

        def _escrever_arquivo(p, c, modo='utf-8'):
            try:
                os.makedirs(os.path.dirname(p), exist_ok=True) if os.path.dirname(p) else None
                with open(p, 'w', encoding=modo) as _f: _f.write(str(c))
                return f"✅ '{p}' salvo"
            except Exception as e:
                raise AdvakError(f"Erro ao escrever '{p}': {e}")

        def _acrescentar_arquivo(p, c):
            try:
                with open(p, 'a', encoding='utf-8') as _f: _f.write(str(c))
                return f"✅ '{p}' atualizado"
            except Exception as e:
                raise AdvakError(f"Erro ao acrescentar em '{p}': {e}")

        def _ler_linhas(p):
            try:
                with open(p, 'r', encoding='utf-8') as _f:
                    return [l.rstrip('\n') for l in _f.readlines()]
            except FileNotFoundError:
                raise AdvakError(f"Arquivo não encontrado: '{p}'")

        def _ler_json(p):
            import json as _json
            try:
                with open(p, 'r', encoding='utf-8') as _f:
                    return _json.load(_f)
            except Exception as e:
                raise AdvakError(f"Erro ao ler JSON '{p}': {e}")

        def _escrever_json(p, dados, indentado=True):
            import json as _json
            try:
                with open(p, 'w', encoding='utf-8') as _f:
                    _json.dump(dados, _f, ensure_ascii=False,
                               indent=2 if indentado else None, default=str)
                return f"✅ '{p}' salvo"
            except Exception as e:
                raise AdvakError(f"Erro ao salvar JSON '{p}': {e}")

        def _listar_arquivos(p='.', extensao=None):
            try:
                entries = os.listdir(p)
                if extensao:
                    entries = [e for e in entries if e.endswith(extensao)]
                return sorted(entries)
            except Exception as e:
                raise AdvakError(f"Erro ao listar '{p}': {e}")

        def _info_arquivo(p):
            try:
                st = os.stat(p)
                return {
                    'nome':      os.path.basename(p),
                    'caminho':   os.path.abspath(p),
                    'tamanho':   st.st_size,
                    'e_pasta':   os.path.isdir(p),
                    'e_arquivo': os.path.isfile(p),
                }
            except Exception as e:
                raise AdvakError(f"Erro ao inspecionar '{p}': {e}")

        _arquivo_obj = {
            'ler':         _ler_arquivo,
            'escrever':    _escrever_arquivo,
            'acrescentar': _acrescentar_arquivo,
            'ler_linhas':  _ler_linhas,
            'ler_json':    _ler_json,
            'escrever_json':_escrever_json,
            'existe':      os.path.exists,
            'apagar':      lambda p: os.remove(p) or f"✅ '{p}' removido",
            'renomear':    lambda a, b: os.rename(a, b) or f"✅ Renomeado",
            'copiar':      lambda a, b: __import__('shutil').copy2(a, b) or f"✅ Copiado",
            'mover':       lambda a, b: __import__('shutil').move(a, b) or f"✅ Movido",
            'listar':      _listar_arquivos,
            'info':        _info_arquivo,
            'criar_pasta': lambda p: os.makedirs(p, exist_ok=True) or f"✅ Pasta criada",
            'pasta_atual': os.getcwd,
            'juntar':      os.path.join,
            'nome':        os.path.basename,
            'extensao':    lambda p: os.path.splitext(p)[1],
            'sem_extensao':lambda p: os.path.splitext(p)[0],
        }
        g.declare('Arquivo', _arquivo_obj)

        # ── HTTP simplificado (sem importar) ─────────────────────────────────
        def _http_get(url, como_json=False):
            try:
                import urllib.request as _req
                resp = _req.urlopen(url).read().decode()
                return __import__('json').loads(resp) if como_json else resp
            except Exception as e:
                raise AdvakError(f"Erro HTTP GET '{url}': {e}")

        def _http_post(url, dados=None, cabecalhos=None):
            try:
                import urllib.request as _req, json as _j
                corpo = _j.dumps(dados or {}).encode()
                hdrs  = {'Content-Type': 'application/json'}
                if cabecalhos: hdrs.update(cabecalhos)
                req  = _req.Request(url, data=corpo, headers=hdrs)
                return _req.urlopen(req).read().decode()
            except Exception as e:
                raise AdvakError(f"Erro HTTP POST '{url}': {e}")

        _http_obj = {
            'get':    _http_get,
            'post':   _http_post,
            'json':   lambda url: _http_get(url, como_json=True),
            'baixar': lambda url, dest: (__import__('urllib.request').urlretrieve(url, dest), f"✅ {dest}")[1],
        }
        g.declare('HTTP', _http_obj)
        def _os_capturar(cmd):
            """Executa comando e retorna saída como texto (subprocesso separado)."""
            import subprocess, sys as _sys
            try:
                resultado = subprocess.run(
                    cmd, shell=True, capture_output=True, timeout=30
                )
                # Decodificar bytes com UTF-8 primeiro, depois fallback do sistema
                def _decodificar(b):
                    if not b: return ''
                    for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1',
                                getattr(_sys.stdout, 'encoding', 'utf-8') or 'utf-8'):
                        try: return b.decode(enc)
                        except: pass
                    return b.decode('utf-8', errors='replace')
                saida = _decodificar(resultado.stdout)
                erro  = _decodificar(resultado.stderr)
                if erro and not saida:
                    saida = erro
                return saida
            except subprocess.TimeoutExpired:
                return '❌ Tempo esgotado (30s)'
            except Exception as e:
                return f'❌ Erro ao executar: {e}'

        async def _os_executar_obj_async(cmd):
            """Executa comando assíncrono — não bloqueia o event loop."""""
            import asyncio
            try:
                env_filho = dict(os.environ)
                env_filho['PYTHONIOENCODING'] = 'utf-8'
                env_filho['PYTHONUTF8'] = '1'
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env_filho
                )
                try:
                    stdout_b, stderr_b = await asyncio.wait_for(
                        proc.communicate(), timeout=15
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    return {'saida':'','erro':'⏱️ Tempo esgotado (15s)','codigo':-1,'ok':False}
                def _dec(b):
                    if not b: return ''
                    for enc in ('utf-8','utf-8-sig','cp1252','latin-1'):
                        try: return b.decode(enc)
                        except: pass
                    return b.decode('utf-8', errors='replace')
                return {
                    'saida':  _dec(stdout_b),
                    'erro':   _dec(stderr_b),
                    'codigo': proc.returncode,
                    'ok':     proc.returncode == 0,
                }
            except Exception as e:
                return {'saida':'','erro':str(e),'codigo':-1,'ok':False}

        def _os_executar_obj(cmd):
            """Executa e retorna objeto {saida, erro, codigo, ok}."""
            import subprocess, sys as _sys, os as _os_sub
            def _dec(b):
                if not b: return ''
                for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1',
                            getattr(_sys.stdout, 'encoding', 'utf-8') or 'utf-8'):
                    try: return b.decode(enc)
                    except: pass
                return b.decode('utf-8', errors='replace')
            # Passar UTF-8 para o processo filho
            env_filho = dict(_os_sub.environ)
            env_filho['PYTHONIOENCODING'] = 'utf-8'
            env_filho['PYTHONUTF8'] = '1'
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True,
                                   timeout=30, env=env_filho)
                return {
                    'saida':  _dec(r.stdout),
                    'erro':   _dec(r.stderr),
                    'codigo': r.returncode,
                    'ok':     r.returncode == 0,
                }
            except subprocess.TimeoutExpired:
                return {'saida':'','erro':'Tempo esgotado (30s)','codigo':-1,'ok':False}
            except Exception as e:
                return {'saida':'','erro':str(e),'codigo':-1,'ok':False}


        def _os_popen(cmd_lista_ou_str):
            import subprocess, sys, os as _os
            env = dict(_os.environ)
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            advak_dir = _os.path.dirname(_os.path.abspath(__file__))
            if isinstance(cmd_lista_ou_str, list):
                cmd = cmd_lista_ou_str
            else:
                # String: dividir em argumentos simples
                cmd = [sys.executable, _os.path.join(advak_dir, 'advak.py')] +                       str(cmd_lista_ou_str).split()
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, cwd=advak_dir
            )
            # Wrapper com métodos em português
            def _dec(b):
                if not b: return ''
                for enc in ('utf-8','utf-8-sig','cp1252','latin-1'):
                    try: return b.decode(enc)
                    except: pass
                return b.decode('utf-8', errors='replace')
            class ProcWrapper:
                def poll(self): return proc.poll()
                def esperar(self, timeout=30): proc.wait(timeout=timeout)
                def terminar(self): proc.terminate()
                @property
                def saida(self):
                    return _dec(proc.stdout.read() if proc.stdout else b'')
                @property
                def erro(self):
                    return _dec(proc.stderr.read() if proc.stderr else b'')
                @property
                def codigo(self): return proc.returncode
            return ProcWrapper()




        def _os_capturar_em_thread(arq_codigo, arq_saida):
            """Roda advak.py <arq_codigo> em thread separada.
            Escreve resultado em arq_saida quando terminar.
            O studio usa jan.after() para verificar arq_saida periodicamente.
            """
            import subprocess, sys, os, threading

            advak_dir  = os.path.dirname(os.path.abspath(__file__))
            python_exe = sys.executable
            advak_py   = os.path.join(advak_dir, 'advak.py')
            arq_dk_abs = os.path.join(advak_dir, str(arq_codigo))
            arq_out_abs= os.path.join(advak_dir, str(arq_saida))

            env = dict(os.environ)
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8']       = '1'

            def _dec(b):
                if not b: return ''
                for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1'):
                    try: return b.decode(enc)
                    except: pass
                return b.decode('utf-8', errors='replace')

            def _rodar():
                try:
                    r = subprocess.run(
                        [python_exe, advak_py, str(arq_codigo)],
                        capture_output=True, timeout=30,
                        env=env, cwd=advak_dir
                    )
                    saida = _dec(r.stdout)
                    erro  = _dec(r.stderr)
                    # Filtrar warnings Python
                    linhas_e = [l for l in erro.split('\n')
                                if l.strip()
                                and 'DeprecationWarning' not in l
                                and 'UserWarning' not in l
                                and 'warnings.warn' not in l
                                and 'site-packages' not in l]
                    erro_limpo = '\n'.join(linhas_e).strip()
                    resultado = saida
                    if erro_limpo:
                        resultado += ('\n' if resultado else '') + '⚠️ ' + erro_limpo
                    resultado = resultado or ''
                except subprocess.TimeoutExpired:
                    resultado = '⏱️ Tempo esgotado (30s)'
                except Exception as exc:
                    resultado = f'❌ Erro ao executar: {exc}'

                # Escrever resultado no arquivo (sinal para o studio)
                try:
                    with open(arq_out_abs, 'w', encoding='utf-8') as _f:
                        _f.write(resultado)
                except Exception as exc:
                    try:
                        with open(arq_out_abs, 'w', encoding='utf-8') as _f:
                            _f.write(f'❌ Erro: {exc}')
                    except Exception:
                        pass

            threading.Thread(target=_rodar, daemon=True).start()


        def _studio_executar(codigo_str, console_tk, status_tk, flag_lista):
            """
            Executa código Advak e mostra resultado no console tkinter.
            Usa root.after_idle() da thread de resultado — thread-safe no tkinter!
            NÃO bloqueia a thread principal.
            """
            import subprocess, sys, os, threading

            codigo_str = str(codigo_str)
            advak_dir  = os.path.dirname(os.path.abspath(__file__))
            arq_dk     = os.path.join(advak_dir, '_studio_temp.dk')
            python_exe = sys.executable
            advak_py   = os.path.join(advak_dir, 'advak.py')

            try:
                with open(arq_dk, 'w', encoding='utf-8') as _f:
                    _f.write(codigo_str)
            except Exception as e:
                return

            env = dict(os.environ)
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8']       = '1'

            def _dec(b):
                if not b: return ''
                for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1'):
                    try: return b.decode(enc)
                    except: pass
                return b.decode('utf-8', errors='replace')

            def _mostrar(resultado):
                """Atualiza console — deve ser chamada na thread principal."""
                try:
                    console_tk.configure(state='normal')
                    if resultado and resultado.strip():
                        console_tk.insert('end', resultado)
                        if not resultado.endswith('\n'):
                            console_tk.insert('end', '\n')
                    else:
                        console_tk.insert('end',
                            '\u2705 Executado sem sa\u00edda impressa\n'
                            '   Dica: use imprimir() para ver resultados\n')
                    console_tk.insert('end', '\n\u2500\u2500 Conclu\u00eddo \u2500\u2500\n')
                    console_tk.see('end')
                    console_tk.configure(state='disabled')
                except Exception: pass
                try: status_tk.configure(text='\u2705 Pronto', fg='#3FB950')
                except Exception: pass
                try: flag_lista[0] = False
                except Exception: pass
                try: os.remove(arq_dk)
                except Exception: pass

            def _thread():
                """Roda em thread separada — não bloqueia tkinter."""
                _log_path = None  # log removido
                try:
                    # Usar advak_mini.py para startup rápido (~500ms no Windows)
                    advak_mini = os.path.join(advak_dir, 'advak_mini.py')
                    if not os.path.exists(advak_mini):
                        advak_mini = advak_py  # fallback para advak.py
                    r = subprocess.run(
                        [python_exe, advak_mini, '_studio_temp.dk'],
                        capture_output=True, timeout=30,
                        env=env, cwd=advak_dir
                    )
                    saida = _dec(r.stdout)
                    erro  = _dec(r.stderr)
                    linhas_e = [l for l in erro.split('\n')
                                if l.strip()
                                and 'DeprecationWarning' not in l
                                and 'UserWarning' not in l
                                and 'warnings.warn' not in l
                                and 'site-packages' not in l]
                    erro_limpo = '\n'.join(linhas_e).strip()
                    resultado = saida
                    if erro_limpo:
                        resultado += ('\n' if resultado else '') + '\u26a0\ufe0f ' + erro_limpo
                except subprocess.TimeoutExpired:
                    resultado = '\u23f1\ufe0f Tempo esgotado (30s)'
                except Exception as exc:
                    resultado = f'\u274c Erro: {exc}'



                # Chamar _mostrar na thread principal via root.after_idle
                # after_idle é thread-safe — pode ser chamado de qualquer thread!
                agendado = False

                # Tentativa 1: root.after_idle (mais direto)
                try:
                    import advak_gui_modern as _agm
                    root = _agm._root_ref
                    if root and root.winfo_exists():
                        root.after_idle(lambda r=resultado: _mostrar(r))
                        agendado = True
                except Exception: pass

                # Tentativa 2: console_tk.after_idle
                if not agendado:
                    try:
                        console_tk.after_idle(lambda r=resultado: _mostrar(r))
                        agendado = True
                    except Exception: pass

                # Tentativa 3: root.after(0) — equivalente a after_idle
                if not agendado:
                    try:
                        import advak_gui_modern as _agm
                        root = _agm._root_ref
                        if root:
                            root.after(0, lambda r=resultado: _mostrar(r))
                            agendado = True
                    except Exception: pass

                # Tentativa 4: console_tk.after(0)
                if not agendado:
                    try:
                        console_tk.after(0, lambda r=resultado: _mostrar(r))
                        agendado = True
                    except Exception: pass

                if not agendado:
                    # Fallback: chamar diretamente (pode ter problemas de thread)
                    _mostrar(resultado)

            threading.Thread(target=_thread, daemon=True).start()


        # ══════════════════════════════════════════════════════════════════════
        # RECURSOS ULTRA AVANÇADOS — Advak 5.1
        # ══════════════════════════════════════════════════════════════════════

        # ── 1. GRAFICO — Matplotlib integrado ─────────────────────────────────
        def _grafico_barras(titulos, valores, titulo='Gráfico', cor='steelblue',
                            largura=8, altura=5, eixo_x='', eixo_y=''):
            try:
                import matplotlib; matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import tempfile, os
                fig, ax = plt.subplots(figsize=(largura, altura))
                ax.bar(titulos if isinstance(titulos, list) else list(titulos),
                       valores if isinstance(valores, list) else list(valores),
                       color=cor)
                ax.set_title(str(titulo)); ax.set_xlabel(str(eixo_x)); ax.set_ylabel(str(eixo_y))
                plt.tight_layout()
                path = os.path.join(tempfile.gettempdir(), 'advak_grafico.png')
                plt.savefig(path, dpi=100); plt.close()
                return path
            except Exception as e:
                return f'❌ Gráfico: {e}'

        def _grafico_linha(titulos, valores, titulo='Gráfico', cor='#e74c3c',
                           largura=8, altura=5, eixo_x='', eixo_y=''):
            try:
                import matplotlib; matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import tempfile, os
                fig, ax = plt.subplots(figsize=(largura, altura))
                xs = titulos if isinstance(titulos, list) else list(titulos)
                ys = valores if isinstance(valores, list) else list(valores)
                ax.plot(xs, ys, color=cor, linewidth=2, marker='o')
                ax.set_title(str(titulo)); ax.set_xlabel(str(eixo_x)); ax.set_ylabel(str(eixo_y))
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                path = os.path.join(tempfile.gettempdir(), 'advak_grafico.png')
                plt.savefig(path, dpi=100); plt.close()
                return path
            except Exception as e:
                return f'❌ Gráfico: {e}'

        def _grafico_pizza(rotulos, valores, titulo='Pizza'):
            try:
                import matplotlib; matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import tempfile, os
                fig, ax = plt.subplots(figsize=(7, 7))
                ax.pie(valores if isinstance(valores, list) else list(valores),
                       labels=rotulos if isinstance(rotulos, list) else list(rotulos),
                       autopct='%1.1f%%', startangle=90)
                ax.set_title(str(titulo))
                plt.tight_layout()
                path = os.path.join(tempfile.gettempdir(), 'advak_grafico.png')
                plt.savefig(path, dpi=100); plt.close()
                return path
            except Exception as e:
                return f'❌ Gráfico: {e}'

        g.declare('Grafico', {
            'barras':    _grafico_barras,
            'linha':     _grafico_linha,
            'pizza':     _grafico_pizza,
        })

        # ── 2. TABELA — DataFrame simplificado ────────────────────────────────
        class _Tabela:
            def __init__(self, colunas=None, linhas=None):
                self.colunas = list(colunas) if colunas else []
                self.linhas  = [list(l) for l in linhas] if linhas else []

            def adicionar_linha(self, linha):
                self.linhas.append(list(linha) if isinstance(linha, (list, tuple)) else [linha])
                return self

            def adicionar_coluna(self, nome, valores=None):
                self.colunas.append(str(nome))
                for i, l in enumerate(self.linhas):
                    l.append(valores[i] if valores and i < len(valores) else None)
                return self

            def filtrar(self, fn):
                def _chamar_fn(linha_dict):
                    try:
                        # AdvakFunction tem .params
                        if hasattr(fn, 'params'):
                            import asyncio
                            loop = asyncio.new_event_loop()
                            try:
                                coro = fn.call([linha_dict], None)
                                if asyncio.iscoroutine(coro):
                                    r = loop.run_until_complete(coro)
                                else:
                                    r = coro
                            finally:
                                loop.close()
                            return bool(r) and r is not False and r != 0
                        return bool(fn(linha_dict))
                    except Exception:
                        return False
                linhas = [l for l in self.linhas if _chamar_fn(dict(zip(self.colunas, l)))]
                return _Tabela(self.colunas[:], linhas)

            def ordenar(self, coluna, decrescente=False):
                idx = self.colunas.index(str(coluna)) if str(coluna) in self.colunas else 0
                linhas = sorted(self.linhas, key=lambda l: (l[idx] is None, l[idx]),
                                reverse=bool(decrescente))
                return _Tabela(self.colunas[:], linhas)

            def selecionar(self, *colunas):
                idxs = [self.colunas.index(c) for c in colunas if c in self.colunas]
                cols = [self.colunas[i] for i in idxs]
                linhas = [[l[i] for i in idxs] for l in self.linhas]
                return _Tabela(cols, linhas)

            def soma(self, coluna):
                idx = self.colunas.index(str(coluna))
                return sum(l[idx] for l in self.linhas if l[idx] is not None)

            def media(self, coluna):
                idx = self.colunas.index(str(coluna))
                vals = [l[idx] for l in self.linhas if l[idx] is not None]
                return sum(vals) / len(vals) if vals else 0

            def max(self, coluna):
                idx = self.colunas.index(str(coluna))
                vals = [l[idx] for l in self.linhas if l[idx] is not None]
                return __builtins__['max'](vals) if vals else None

            def min(self, coluna):
                idx = self.colunas.index(str(coluna))
                vals = [l[idx] for l in self.linhas if l[idx] is not None]
                return __builtins__['min'](vals) if vals else None

            def para_json(self):
                import json
                return json.dumps([dict(zip(self.colunas, l)) for l in self.linhas],
                                  ensure_ascii=False, default=str)

            def de_csv(self, caminho, separador=','):
                import csv
                with open(caminho, encoding='utf-8', newline='') as f:
                    reader = csv.reader(f, delimiter=separador)
                    rows = list(reader)
                if rows:
                    self.colunas = rows[0]
                    self.linhas  = rows[1:]
                return self

            def para_csv(self, caminho, separador=','):
                import csv
                with open(caminho, 'w', encoding='utf-8', newline='') as f:
                    w = csv.writer(f, delimiter=separador)
                    w.writerow(self.colunas)
                    w.writerows(self.linhas)
                return caminho

            def imprimir(self):
                if not self.colunas:
                    print('(tabela vazia)')
                    return
                # Calcular larguras
                larguras = [len(c) for c in self.colunas]
                for linha in self.linhas:
                    for i, v in enumerate(linha):
                        if i < len(larguras):
                            larguras[i] = max(larguras[i], len(str(v) if v is not None else 'nulo'))
                sep = '+' + '+'.join('-' * (l + 2) for l in larguras) + '+'
                print(sep)
                header = '|' + '|'.join(f' {c:<{larguras[i]}} ' for i, c in enumerate(self.colunas)) + '|'
                print(header); print(sep)
                for linha in self.linhas:
                    row = '|'
                    for i, v in enumerate(linha):
                        val = str(v) if v is not None else 'nulo'
                        l = larguras[i] if i < len(larguras) else 10
                        row += f' {val:<{l}} |'
                    print(row)
                print(sep)
                print(f'  {len(self.linhas)} linhas × {len(self.colunas)} colunas')

            @property
            def tamanho(self):
                return len(self.linhas)

        def _nova_tabela(colunas=None, linhas=None):
            return _Tabela(colunas, linhas)

        g.declare('Tabela', {
            'nova':   _nova_tabela,
            'de_csv': lambda caminho, sep=',': _Tabela().de_csv(caminho, sep),
        })

        # ── 3. HASH — Criptografia e integridade ──────────────────────────────
        import hashlib as _hashlib

        def _hash_sha256(texto_str):
            return _hashlib.sha256(str(texto_str).encode('utf-8')).hexdigest()
        def _hash_md5(texto_str):
            return _hashlib.md5(str(texto_str).encode('utf-8')).hexdigest()
        def _hash_sha1(texto_str):
            return _hashlib.sha1(str(texto_str).encode('utf-8')).hexdigest()
        def _hash_sha512(texto_str):
            return _hashlib.sha512(str(texto_str).encode('utf-8')).hexdigest()
        def _hash_arquivo(caminho):
            h = _hashlib.sha256()
            try:
                with open(str(caminho), 'rb') as f:
                    for bloco in iter(lambda: f.read(65536), b''):
                        h.update(bloco)
                return h.hexdigest()
            except Exception as e:
                return f'❌ {e}'

        g.declare('Hash', {
            'sha256':  _hash_sha256,
            'md5':     _hash_md5,
            'sha1':    _hash_sha1,
            'sha512':  _hash_sha512,
            'arquivo': _hash_arquivo,
        })

        # ── 4. BASE64 — Codificação ────────────────────────────────────────────
        import base64 as _b64

        def _b64_codificar(texto_str):
            return _b64.b64encode(str(texto_str).encode('utf-8')).decode('utf-8')
        def _b64_decodificar(texto_str):
            try:
                return _b64.b64decode(str(texto_str)).decode('utf-8')
            except Exception as e:
                return f'❌ {e}'
        def _b64_codificar_arquivo(caminho):
            try:
                with open(str(caminho), 'rb') as f:
                    return _b64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                return f'❌ {e}'

        g.declare('Base64', {
            'codificar':          _b64_codificar,
            'decodificar':        _b64_decodificar,
            'codificar_arquivo':  _b64_codificar_arquivo,
        })

        # ── 5. COMPRESSAO — ZIP e GZIP ────────────────────────────────────────
        def _compressao_criar_zip(nome_zip, *arquivos):
            import zipfile
            caminho = str(nome_zip)
            if not caminho.endswith('.zip'): caminho += '.zip'
            with zipfile.ZipFile(caminho, 'w', zipfile.ZIP_DEFLATED) as zf:
                for arq in arquivos:
                    zf.write(str(arq), os.path.basename(str(arq)))
            return caminho

        def _compressao_extrair_zip(nome_zip, destino='.'):
            import zipfile
            with zipfile.ZipFile(str(nome_zip), 'r') as zf:
                zf.extractall(str(destino))
            return str(destino)

        def _compressao_listar_zip(nome_zip):
            import zipfile
            with zipfile.ZipFile(str(nome_zip), 'r') as zf:
                return [info.filename for info in zf.infolist()]

        def _compressao_gzip(caminho):
            import gzip, shutil
            saida = str(caminho) + '.gz'
            with open(str(caminho), 'rb') as f_in:
                with gzip.open(saida, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return saida

        g.declare('Compressao', {
            'criar_zip':   _compressao_criar_zip,
            'extrair_zip': _compressao_extrair_zip,
            'listar_zip':  _compressao_listar_zip,
            'gzip':        _compressao_gzip,
        })

        # ── 6. CRONOMETRO — Timer de alta precisão ────────────────────────────
        import time as _time_mod

        class _Cronometro:
            def __init__(self):
                self._inicio = None
                self._pausado = 0.0
                self._inicio_pausa = None

            def iniciar(self):
                self._inicio = _time_mod.perf_counter()
                self._pausado = 0.0
                self._inicio_pausa = None
                return self

            def pausar(self):
                if self._inicio and not self._inicio_pausa:
                    self._inicio_pausa = _time_mod.perf_counter()
                return self

            def retomar(self):
                if self._inicio_pausa:
                    self._pausado += _time_mod.perf_counter() - self._inicio_pausa
                    self._inicio_pausa = None
                return self

            def parar(self):
                elapsed = self.elapsed
                self._inicio = None
                return elapsed

            @property
            def elapsed(self):
                if not self._inicio: return 0.0
                if self._inicio_pausa:
                    return self._inicio_pausa - self._inicio - self._pausado
                return _time_mod.perf_counter() - self._inicio - self._pausado

            @property
            def ms(self):  return self.elapsed * 1000
            @property
            def segundos(self): return self.elapsed
            @property
            def minutos(self): return self.elapsed / 60

            def formatar(self):
                t = self.elapsed
                h, rem = divmod(t, 3600)
                m, s = divmod(rem, 60)
                return f'{int(h):02d}:{int(m):02d}:{s:06.3f}'

        def _novo_cronometro():
            return _Cronometro()

        g.declare('Cronometro', {
            'novo':       _novo_cronometro,
            'agora_ms':   lambda: _time_mod.perf_counter() * 1000,
            'agora_ns':   lambda: _time_mod.perf_counter_ns(),
            'medir':      lambda fn: (lambda t0=_time_mod.perf_counter(): (fn(), (_time_mod.perf_counter()-t0)*1000))()[1],
        })

        # ── 7. TEXTO AVANCADO — Processamento de texto ────────────────────────
        def _txt_contar_palavras(texto_str):
            return len(str(texto_str).split())

        def _txt_contar_caracteres(texto_str, incluir_espacos=True):
            s = str(texto_str)
            return len(s) if incluir_espacos else len(s.replace(' ', ''))

        def _txt_pluralizar(palavra, quantidade, plural=None):
            if int(quantidade) == 1:
                return f'{quantidade} {palavra}'
            return f'{quantidade} {plural or palavra + "s"}'

        def _txt_truncar(texto_str, tamanho, sufixo='...'):
            s = str(texto_str)
            n = int(tamanho)
            if len(s) <= n: return s
            corte = n - len(str(sufixo))
            return s[:max(0, corte)] + str(sufixo)

        def _txt_slugify(texto_str):
            import re as _re
            s = str(texto_str).lower()
            s = s.replace('ã','a').replace('â','a').replace('á','a').replace('à','a')
            s = s.replace('ê','e').replace('é','e').replace('è','e')
            s = s.replace('î','i').replace('í','i').replace('ï','i')
            s = s.replace('ô','o').replace('ó','o').replace('õ','o').replace('ö','o')
            s = s.replace('û','u').replace('ú','u').replace('ü','u')
            s = s.replace('ç','c').replace('ñ','n')
            s = _re.sub(r'[^a-z0-9]+', '-', s).strip('-')
            return s

        def _txt_similaridade(a, b):
            """Distância de Levenshtein normalizada (0=diferente, 1=igual)"""
            a, b = str(a), str(b)
            if a == b: return 1.0
            la, lb = len(a), len(b)
            if not la or not lb: return 0.0
            matrix = [[0]*(lb+1) for _ in range(la+1)]
            for i in range(la+1): matrix[i][0] = i
            for j in range(lb+1): matrix[0][j] = j
            for i in range(1, la+1):
                for j in range(1, lb+1):
                    custo = 0 if a[i-1] == b[j-1] else 1
                    matrix[i][j] = min(matrix[i-1][j]+1, matrix[i][j-1]+1, matrix[i-1][j-1]+custo)
            dist = matrix[la][lb]
            return round(1 - dist / max(la, lb), 4)

        def _txt_extrair_numeros(texto_str):
            import re as _re
            nums = _re.findall(r'-?\d+\.?\d*', str(texto_str))
            return [float(n) if '.' in n else int(n) for n in nums]

        def _txt_palindromo(texto_str):
            s = ''.join(c.lower() for c in str(texto_str) if c.isalnum())
            return s == s[::-1]

        def _txt_anagrama(a, b):
            def normalizar(s):
                return sorted(c.lower() for c in str(s) if c.isalnum())
            return normalizar(a) == normalizar(b)

        g.declare('TextoAvancado', {
            'contar_palavras':    _txt_contar_palavras,
            'contar_caracteres':  _txt_contar_caracteres,
            'truncar':            _txt_truncar,
            'slugify':            _txt_slugify,
            'similaridade':       _txt_similaridade,
            'extrair_numeros':    _txt_extrair_numeros,
            'palindromo':         lambda t: 'verdadeiro' if _txt_palindromo(t) else 'falso',
            'anagrama':           lambda a, b: 'verdadeiro' if _txt_anagrama(a, b) else 'falso',
        })

        # ── 8. MATEMATICA AVANCADA ────────────────────────────────────────────
        import math as _math_mod, statistics as _stats

        g.declare('MatAvancada', {
            'fatorial':       _math_mod.factorial,
            'combinacao':     _math_mod.comb,
            'permutacao':     _math_mod.perm,
            'mmc':            _math_mod.lcm,
            'mdc':            _math_mod.gcd,
            'primo':          lambda n: 'verdadeiro' if (n > 1 and all(n % i for i in range(2, int(n**0.5)+1))) else 'falso',
            'primos_ate':     lambda n: [x for x in range(2, int(n)+1)
                               if all(x % i for i in range(2, int(x**0.5)+1))],
            'fibonacci':      lambda n: (lambda f: f(f, int(n)))(lambda f, n: n if n <= 1 else f(f,n-1)+f(f,n-2)),
            'media':          lambda lst: _stats.mean(lst),
            'mediana':        lambda lst: _stats.median(lst),
            'moda':           lambda lst: _stats.mode(lst),
            'desvio_padrao':  lambda lst: _stats.stdev(lst) if len(lst) > 1 else 0,
            'variancia':      lambda lst: _stats.variance(lst) if len(lst) > 1 else 0,
            'percentil':      lambda lst, p: sorted(lst)[int(len(lst)*p/100)],
            'clamp':          lambda v, mn, mx: max(mn, min(mx, v)),
            'mapear_range':   lambda v, a1, b1, a2, b2: a2 + (v-a1)*(b2-a2)/(b1-a1),
            'log2':           _math_mod.log2,
            'log10':          _math_mod.log10,
            'log':            _math_mod.log,
            'hipotenusa':     _math_mod.hypot,
        })

        # ── 9. REDE — Utilitários de rede ─────────────────────────────────────
        def _rede_ip_local():
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return '127.0.0.1'

        def _rede_hostname():
            import socket
            return socket.gethostname()

        def _rede_ping(host, timeout=3):
            import subprocess as _sp
            cmd = ['ping', '-n' if os.name == 'nt' else '-c', '1',
                   '-w' if os.name == 'nt' else '-W', str(timeout*1000 if os.name=='nt' else timeout),
                   str(host)]
            try:
                r = _sp.run(cmd, capture_output=True, timeout=timeout+2)
                return r.returncode == 0
            except Exception:
                return False

        def _rede_portas_abertas(host, portas):
            import socket
            abertas = []
            for porta in (portas if isinstance(portas, list) else [portas]):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1)
                    if s.connect_ex((str(host), int(porta))) == 0:
                        abertas.append(int(porta))
                    s.close()
                except Exception: pass
            return abertas

        g.declare('Rede', {
            'ip_local':      _rede_ip_local,
            'hostname':      _rede_hostname,
            'ping':          _rede_ping,
            'portas_abertas': _rede_portas_abertas,
        })

        # ── 10. SISTEMA — Info do sistema ─────────────────────────────────────
        def _sistema_info():
            import platform, sys as _s
            return {
                'so':         platform.system(),
                'versao_so':  platform.version(),
                'maquina':    platform.machine(),
                'processador': platform.processor(),
                'python':     _s.version,
                'hostname':   platform.node(),
                'arquitetura': platform.architecture()[0],
            }

        def _sistema_memoria():
            try:
                import psutil
                m = psutil.virtual_memory()
                return {
                    'total_mb':     round(m.total / 1024**2),
                    'disponivel_mb': round(m.available / 1024**2),
                    'usado_mb':     round(m.used / 1024**2),
                    'porcentagem':  m.percent,
                }
            except Exception:
                return {'erro': 'psutil não instalado. Execute: pip install psutil'}

        def _sistema_cpu():
            try:
                import psutil
                return {
                    'nucleos':    psutil.cpu_count(),
                    'porcentagem': psutil.cpu_percent(interval=0.5),
                    'frequencia':  round(psutil.cpu_freq().current) if psutil.cpu_freq() else 0,
                }
            except Exception:
                return {'nucleos': os.cpu_count() or 1, 'porcentagem': 0}

        def _sistema_disco(caminho='.'):
            import shutil
            total, usado, livre = shutil.disk_usage(str(caminho))
            return {
                'total_gb':  round(total / 1024**3, 2),
                'usado_gb':  round(usado / 1024**3, 2),
                'livre_gb':  round(livre / 1024**3, 2),
                'porcentagem': round(usado / total * 100, 1),
            }

        g.declare('Sistema', {
            'info':    _sistema_info,
            'memoria': _sistema_memoria,
            'cpu':     _sistema_cpu,
            'disco':   _sistema_disco,
            'pid':     lambda: os.getpid(),
            'env':     lambda nome, padrao='': os.environ.get(str(nome), str(padrao)),
        })



        # ── Funções de performance (operações rápidas em Python nativo) ────────
        g.declare('somar_ate',    lambda n: int(n) * (int(n) - 1) // 2)  # soma 0+1+...+(n-1)
        g.declare('somar_range',  lambda a, b: sum(range(int(a), int(b))))
        g.declare('produto_lista', lambda lst: (lambda r: [r := r * x for x in lst] and r)(1))
        g.declare('max_lista',    lambda lst: max(lst) if lst else None)
        g.declare('min_lista',    lambda lst: min(lst) if lst else None)
        g.declare('ordenar_lista', lambda lst, dec=False: sorted(lst, reverse=bool(dec)))
        g.declare('contar_onde',  lambda lst, fn: sum(1 for x in lst if fn(x)))

        g.declare('studio_executar', _studio_executar)

        # ══════════════════════════════════════════════════════════════════════
        # RECURSOS ULTRA AVANÇADOS — Advak 5.1
        # ══════════════════════════════════════════════════════════════════════

        # ── 1. GRAFICO — Matplotlib integrado ─────────────────────────────────
        def _grafico_barras(titulos, valores, titulo='Gráfico', cor='steelblue',
                            largura=8, altura=5, eixo_x='', eixo_y=''):
            try:
                import matplotlib; matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import tempfile, os
                fig, ax = plt.subplots(figsize=(largura, altura))
                ax.bar(titulos if isinstance(titulos, list) else list(titulos),
                       valores if isinstance(valores, list) else list(valores),
                       color=cor)
                ax.set_title(str(titulo)); ax.set_xlabel(str(eixo_x)); ax.set_ylabel(str(eixo_y))
                plt.tight_layout()
                path = os.path.join(tempfile.gettempdir(), 'advak_grafico.png')
                plt.savefig(path, dpi=100); plt.close()
                return path
            except Exception as e:
                return f'❌ Gráfico: {e}'

        def _grafico_linha(titulos, valores, titulo='Gráfico', cor='#e74c3c',
                           largura=8, altura=5, eixo_x='', eixo_y=''):
            try:
                import matplotlib; matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import tempfile, os
                fig, ax = plt.subplots(figsize=(largura, altura))
                xs = titulos if isinstance(titulos, list) else list(titulos)
                ys = valores if isinstance(valores, list) else list(valores)
                ax.plot(xs, ys, color=cor, linewidth=2, marker='o')
                ax.set_title(str(titulo)); ax.set_xlabel(str(eixo_x)); ax.set_ylabel(str(eixo_y))
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                path = os.path.join(tempfile.gettempdir(), 'advak_grafico.png')
                plt.savefig(path, dpi=100); plt.close()
                return path
            except Exception as e:
                return f'❌ Gráfico: {e}'

        def _grafico_pizza(rotulos, valores, titulo='Pizza'):
            try:
                import matplotlib; matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                import tempfile, os
                fig, ax = plt.subplots(figsize=(7, 7))
                ax.pie(valores if isinstance(valores, list) else list(valores),
                       labels=rotulos if isinstance(rotulos, list) else list(rotulos),
                       autopct='%1.1f%%', startangle=90)
                ax.set_title(str(titulo))
                plt.tight_layout()
                path = os.path.join(tempfile.gettempdir(), 'advak_grafico.png')
                plt.savefig(path, dpi=100); plt.close()
                return path
            except Exception as e:
                return f'❌ Gráfico: {e}'

        g.declare('Grafico', {
            'barras':    _grafico_barras,
            'linha':     _grafico_linha,
            'pizza':     _grafico_pizza,
        })

        # ── 2. TABELA — DataFrame simplificado ────────────────────────────────
        class _Tabela:
            def __init__(self, colunas=None, linhas=None):
                self.colunas = list(colunas) if colunas else []
                self.linhas  = [list(l) for l in linhas] if linhas else []

            def adicionar_linha(self, linha):
                self.linhas.append(list(linha) if isinstance(linha, (list, tuple)) else [linha])
                return self

            def adicionar_coluna(self, nome, valores=None):
                self.colunas.append(str(nome))
                for i, l in enumerate(self.linhas):
                    l.append(valores[i] if valores and i < len(valores) else None)
                return self

            def filtrar(self, fn):
                def _chamar_fn(linha_dict):
                    try:
                        # AdvakFunction tem .params
                        if hasattr(fn, 'params'):
                            import asyncio
                            loop = asyncio.new_event_loop()
                            try:
                                coro = fn.call([linha_dict], None)
                                if asyncio.iscoroutine(coro):
                                    r = loop.run_until_complete(coro)
                                else:
                                    r = coro
                            finally:
                                loop.close()
                            return bool(r) and r is not False and r != 0
                        return bool(fn(linha_dict))
                    except Exception:
                        return False
                linhas = [l for l in self.linhas if _chamar_fn(dict(zip(self.colunas, l)))]
                return _Tabela(self.colunas[:], linhas)

            def ordenar(self, coluna, decrescente=False):
                idx = self.colunas.index(str(coluna)) if str(coluna) in self.colunas else 0
                linhas = sorted(self.linhas, key=lambda l: (l[idx] is None, l[idx]),
                                reverse=bool(decrescente))
                return _Tabela(self.colunas[:], linhas)

            def selecionar(self, *colunas):
                idxs = [self.colunas.index(c) for c in colunas if c in self.colunas]
                cols = [self.colunas[i] for i in idxs]
                linhas = [[l[i] for i in idxs] for l in self.linhas]
                return _Tabela(cols, linhas)

            def soma(self, coluna):
                idx = self.colunas.index(str(coluna))
                return sum(l[idx] for l in self.linhas if l[idx] is not None)

            def media(self, coluna):
                idx = self.colunas.index(str(coluna))
                vals = [l[idx] for l in self.linhas if l[idx] is not None]
                return sum(vals) / len(vals) if vals else 0

            def max(self, coluna):
                idx = self.colunas.index(str(coluna))
                vals = [l[idx] for l in self.linhas if l[idx] is not None]
                return __builtins__['max'](vals) if vals else None

            def min(self, coluna):
                idx = self.colunas.index(str(coluna))
                vals = [l[idx] for l in self.linhas if l[idx] is not None]
                return __builtins__['min'](vals) if vals else None

            def para_json(self):
                import json
                return json.dumps([dict(zip(self.colunas, l)) for l in self.linhas],
                                  ensure_ascii=False, default=str)

            def de_csv(self, caminho, separador=','):
                import csv
                with open(caminho, encoding='utf-8', newline='') as f:
                    reader = csv.reader(f, delimiter=separador)
                    rows = list(reader)
                if rows:
                    self.colunas = rows[0]
                    self.linhas  = rows[1:]
                return self

            def para_csv(self, caminho, separador=','):
                import csv
                with open(caminho, 'w', encoding='utf-8', newline='') as f:
                    w = csv.writer(f, delimiter=separador)
                    w.writerow(self.colunas)
                    w.writerows(self.linhas)
                return caminho

            def imprimir(self):
                if not self.colunas:
                    print('(tabela vazia)')
                    return
                # Calcular larguras
                larguras = [len(c) for c in self.colunas]
                for linha in self.linhas:
                    for i, v in enumerate(linha):
                        if i < len(larguras):
                            larguras[i] = max(larguras[i], len(str(v) if v is not None else 'nulo'))
                sep = '+' + '+'.join('-' * (l + 2) for l in larguras) + '+'
                print(sep)
                header = '|' + '|'.join(f' {c:<{larguras[i]}} ' for i, c in enumerate(self.colunas)) + '|'
                print(header); print(sep)
                for linha in self.linhas:
                    row = '|'
                    for i, v in enumerate(linha):
                        val = str(v) if v is not None else 'nulo'
                        l = larguras[i] if i < len(larguras) else 10
                        row += f' {val:<{l}} |'
                    print(row)
                print(sep)
                print(f'  {len(self.linhas)} linhas × {len(self.colunas)} colunas')

            @property
            def tamanho(self):
                return len(self.linhas)

        def _nova_tabela(colunas=None, linhas=None):
            return _Tabela(colunas, linhas)

        g.declare('Tabela', {
            'nova':   _nova_tabela,
            'de_csv': lambda caminho, sep=',': _Tabela().de_csv(caminho, sep),
        })

        # ── 3. HASH — Criptografia e integridade ──────────────────────────────
        import hashlib as _hashlib

        def _hash_sha256(texto_str):
            return _hashlib.sha256(str(texto_str).encode('utf-8')).hexdigest()
        def _hash_md5(texto_str):
            return _hashlib.md5(str(texto_str).encode('utf-8')).hexdigest()
        def _hash_sha1(texto_str):
            return _hashlib.sha1(str(texto_str).encode('utf-8')).hexdigest()
        def _hash_sha512(texto_str):
            return _hashlib.sha512(str(texto_str).encode('utf-8')).hexdigest()
        def _hash_arquivo(caminho):
            h = _hashlib.sha256()
            try:
                with open(str(caminho), 'rb') as f:
                    for bloco in iter(lambda: f.read(65536), b''):
                        h.update(bloco)
                return h.hexdigest()
            except Exception as e:
                return f'❌ {e}'

        g.declare('Hash', {
            'sha256':  _hash_sha256,
            'md5':     _hash_md5,
            'sha1':    _hash_sha1,
            'sha512':  _hash_sha512,
            'arquivo': _hash_arquivo,
        })

        # ── 4. BASE64 — Codificação ────────────────────────────────────────────
        import base64 as _b64

        def _b64_codificar(texto_str):
            return _b64.b64encode(str(texto_str).encode('utf-8')).decode('utf-8')
        def _b64_decodificar(texto_str):
            try:
                return _b64.b64decode(str(texto_str)).decode('utf-8')
            except Exception as e:
                return f'❌ {e}'
        def _b64_codificar_arquivo(caminho):
            try:
                with open(str(caminho), 'rb') as f:
                    return _b64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                return f'❌ {e}'

        g.declare('Base64', {
            'codificar':          _b64_codificar,
            'decodificar':        _b64_decodificar,
            'codificar_arquivo':  _b64_codificar_arquivo,
        })

        # ── 5. COMPRESSAO — ZIP e GZIP ────────────────────────────────────────
        def _compressao_criar_zip(nome_zip, *arquivos):
            import zipfile
            caminho = str(nome_zip)
            if not caminho.endswith('.zip'): caminho += '.zip'
            with zipfile.ZipFile(caminho, 'w', zipfile.ZIP_DEFLATED) as zf:
                for arq in arquivos:
                    zf.write(str(arq), os.path.basename(str(arq)))
            return caminho

        def _compressao_extrair_zip(nome_zip, destino='.'):
            import zipfile
            with zipfile.ZipFile(str(nome_zip), 'r') as zf:
                zf.extractall(str(destino))
            return str(destino)

        def _compressao_listar_zip(nome_zip):
            import zipfile
            with zipfile.ZipFile(str(nome_zip), 'r') as zf:
                return [info.filename for info in zf.infolist()]

        def _compressao_gzip(caminho):
            import gzip, shutil
            saida = str(caminho) + '.gz'
            with open(str(caminho), 'rb') as f_in:
                with gzip.open(saida, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return saida

        g.declare('Compressao', {
            'criar_zip':   _compressao_criar_zip,
            'extrair_zip': _compressao_extrair_zip,
            'listar_zip':  _compressao_listar_zip,
            'gzip':        _compressao_gzip,
        })

        # ── 6. CRONOMETRO — Timer de alta precisão ────────────────────────────
        import time as _time_mod

        class _Cronometro:
            def __init__(self):
                self._inicio = None
                self._pausado = 0.0
                self._inicio_pausa = None

            def iniciar(self):
                self._inicio = _time_mod.perf_counter()
                self._pausado = 0.0
                self._inicio_pausa = None
                return self

            def pausar(self):
                if self._inicio and not self._inicio_pausa:
                    self._inicio_pausa = _time_mod.perf_counter()
                return self

            def retomar(self):
                if self._inicio_pausa:
                    self._pausado += _time_mod.perf_counter() - self._inicio_pausa
                    self._inicio_pausa = None
                return self

            def parar(self):
                elapsed = self.elapsed
                self._inicio = None
                return elapsed

            @property
            def elapsed(self):
                if not self._inicio: return 0.0
                if self._inicio_pausa:
                    return self._inicio_pausa - self._inicio - self._pausado
                return _time_mod.perf_counter() - self._inicio - self._pausado

            @property
            def ms(self):  return self.elapsed * 1000
            @property
            def segundos(self): return self.elapsed
            @property
            def minutos(self): return self.elapsed / 60

            def formatar(self):
                t = self.elapsed
                h, rem = divmod(t, 3600)
                m, s = divmod(rem, 60)
                return f'{int(h):02d}:{int(m):02d}:{s:06.3f}'

        def _novo_cronometro():
            return _Cronometro()

        g.declare('Cronometro', {
            'novo':       _novo_cronometro,
            'agora_ms':   lambda: _time_mod.perf_counter() * 1000,
            'agora_ns':   lambda: _time_mod.perf_counter_ns(),
            'medir':      lambda fn: (lambda t0=_time_mod.perf_counter(): (fn(), (_time_mod.perf_counter()-t0)*1000))()[1],
        })

        # ── 7. TEXTO AVANCADO — Processamento de texto ────────────────────────
        def _txt_contar_palavras(texto_str):
            return len(str(texto_str).split())

        def _txt_contar_caracteres(texto_str, incluir_espacos=True):
            s = str(texto_str)
            return len(s) if incluir_espacos else len(s.replace(' ', ''))

        def _txt_pluralizar(palavra, quantidade, plural=None):
            if int(quantidade) == 1:
                return f'{quantidade} {palavra}'
            return f'{quantidade} {plural or palavra + "s"}'

        def _txt_truncar(texto_str, tamanho, sufixo='...'):
            s = str(texto_str)
            n = int(tamanho)
            if len(s) <= n: return s
            corte = n - len(str(sufixo))
            return s[:max(0, corte)] + str(sufixo)

        def _txt_slugify(texto_str):
            import re as _re
            s = str(texto_str).lower()
            s = s.replace('ã','a').replace('â','a').replace('á','a').replace('à','a')
            s = s.replace('ê','e').replace('é','e').replace('è','e')
            s = s.replace('î','i').replace('í','i').replace('ï','i')
            s = s.replace('ô','o').replace('ó','o').replace('õ','o').replace('ö','o')
            s = s.replace('û','u').replace('ú','u').replace('ü','u')
            s = s.replace('ç','c').replace('ñ','n')
            s = _re.sub(r'[^a-z0-9]+', '-', s).strip('-')
            return s

        def _txt_similaridade(a, b):
            """Distância de Levenshtein normalizada (0=diferente, 1=igual)"""
            a, b = str(a), str(b)
            if a == b: return 1.0
            la, lb = len(a), len(b)
            if not la or not lb: return 0.0
            matrix = [[0]*(lb+1) for _ in range(la+1)]
            for i in range(la+1): matrix[i][0] = i
            for j in range(lb+1): matrix[0][j] = j
            for i in range(1, la+1):
                for j in range(1, lb+1):
                    custo = 0 if a[i-1] == b[j-1] else 1
                    matrix[i][j] = min(matrix[i-1][j]+1, matrix[i][j-1]+1, matrix[i-1][j-1]+custo)
            dist = matrix[la][lb]
            return round(1 - dist / max(la, lb), 4)

        def _txt_extrair_numeros(texto_str):
            import re as _re
            nums = _re.findall(r'-?\d+\.?\d*', str(texto_str))
            return [float(n) if '.' in n else int(n) for n in nums]

        def _txt_palindromo(texto_str):
            s = ''.join(c.lower() for c in str(texto_str) if c.isalnum())
            return s == s[::-1]

        def _txt_anagrama(a, b):
            def normalizar(s):
                return sorted(c.lower() for c in str(s) if c.isalnum())
            return normalizar(a) == normalizar(b)

        g.declare('TextoAvancado', {
            'contar_palavras':    _txt_contar_palavras,
            'contar_caracteres':  _txt_contar_caracteres,
            'truncar':            _txt_truncar,
            'slugify':            _txt_slugify,
            'similaridade':       _txt_similaridade,
            'extrair_numeros':    _txt_extrair_numeros,
            'palindromo':         lambda t: 'verdadeiro' if _txt_palindromo(t) else 'falso',
            'anagrama':           lambda a, b: 'verdadeiro' if _txt_anagrama(a, b) else 'falso',
        })

        # ── 8. MATEMATICA AVANCADA ────────────────────────────────────────────
        import math as _math_mod, statistics as _stats

        g.declare('MatAvancada', {
            'fatorial':       _math_mod.factorial,
            'combinacao':     _math_mod.comb,
            'permutacao':     _math_mod.perm,
            'mmc':            _math_mod.lcm,
            'mdc':            _math_mod.gcd,
            'primo':          lambda n: 'verdadeiro' if (n > 1 and all(n % i for i in range(2, int(n**0.5)+1))) else 'falso',
            'primos_ate':     lambda n: [x for x in range(2, int(n)+1)
                               if all(x % i for i in range(2, int(x**0.5)+1))],
            'fibonacci':      lambda n: (lambda f: f(f, int(n)))(lambda f, n: n if n <= 1 else f(f,n-1)+f(f,n-2)),
            'media':          lambda lst: _stats.mean(lst),
            'mediana':        lambda lst: _stats.median(lst),
            'moda':           lambda lst: _stats.mode(lst),
            'desvio_padrao':  lambda lst: _stats.stdev(lst) if len(lst) > 1 else 0,
            'variancia':      lambda lst: _stats.variance(lst) if len(lst) > 1 else 0,
            'percentil':      lambda lst, p: sorted(lst)[int(len(lst)*p/100)],
            'clamp':          lambda v, mn, mx: max(mn, min(mx, v)),
            'mapear_range':   lambda v, a1, b1, a2, b2: a2 + (v-a1)*(b2-a2)/(b1-a1),
            'log2':           _math_mod.log2,
            'log10':          _math_mod.log10,
            'log':            _math_mod.log,
            'hipotenusa':     _math_mod.hypot,
        })

        # ── 9. REDE — Utilitários de rede ─────────────────────────────────────
        def _rede_ip_local():
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return '127.0.0.1'

        def _rede_hostname():
            import socket
            return socket.gethostname()

        def _rede_ping(host, timeout=3):
            import subprocess as _sp
            cmd = ['ping', '-n' if os.name == 'nt' else '-c', '1',
                   '-w' if os.name == 'nt' else '-W', str(timeout*1000 if os.name=='nt' else timeout),
                   str(host)]
            try:
                r = _sp.run(cmd, capture_output=True, timeout=timeout+2)
                return r.returncode == 0
            except Exception:
                return False

        def _rede_portas_abertas(host, portas):
            import socket
            abertas = []
            for porta in (portas if isinstance(portas, list) else [portas]):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(1)
                    if s.connect_ex((str(host), int(porta))) == 0:
                        abertas.append(int(porta))
                    s.close()
                except Exception: pass
            return abertas

        g.declare('Rede', {
            'ip_local':      _rede_ip_local,
            'hostname':      _rede_hostname,
            'ping':          _rede_ping,
            'portas_abertas': _rede_portas_abertas,
        })

        # ── 10. SISTEMA — Info do sistema ─────────────────────────────────────
        def _sistema_info():
            import platform, sys as _s
            return {
                'so':         platform.system(),
                'versao_so':  platform.version(),
                'maquina':    platform.machine(),
                'processador': platform.processor(),
                'python':     _s.version,
                'hostname':   platform.node(),
                'arquitetura': platform.architecture()[0],
            }

        def _sistema_memoria():
            try:
                import psutil
                m = psutil.virtual_memory()
                return {
                    'total_mb':     round(m.total / 1024**2),
                    'disponivel_mb': round(m.available / 1024**2),
                    'usado_mb':     round(m.used / 1024**2),
                    'porcentagem':  m.percent,
                }
            except Exception:
                return {'erro': 'psutil não instalado. Execute: pip install psutil'}

        def _sistema_cpu():
            try:
                import psutil
                return {
                    'nucleos':    psutil.cpu_count(),
                    'porcentagem': psutil.cpu_percent(interval=0.5),
                    'frequencia':  round(psutil.cpu_freq().current) if psutil.cpu_freq() else 0,
                }
            except Exception:
                return {'nucleos': os.cpu_count() or 1, 'porcentagem': 0}

        def _sistema_disco(caminho='.'):
            import shutil
            total, usado, livre = shutil.disk_usage(str(caminho))
            return {
                'total_gb':  round(total / 1024**3, 2),
                'usado_gb':  round(usado / 1024**3, 2),
                'livre_gb':  round(livre / 1024**3, 2),
                'porcentagem': round(usado / total * 100, 1),
            }

        g.declare('Sistema', {
            'info':    _sistema_info,
            'memoria': _sistema_memoria,
            'cpu':     _sistema_cpu,
            'disco':   _sistema_disco,
            'pid':     lambda: os.getpid(),
            'env':     lambda nome, padrao='': os.environ.get(str(nome), str(padrao)),
        })



        # ── Funções de performance (operações rápidas em Python nativo) ────────
        g.declare('somar_ate',    lambda n: int(n) * (int(n) - 1) // 2)  # soma 0+1+...+(n-1)
        g.declare('somar_range',  lambda a, b: sum(range(int(a), int(b))))
        g.declare('produto_lista', lambda lst: (lambda r: [r := r * x for x in lst] and r)(1))
        g.declare('max_lista',    lambda lst: max(lst) if lst else None)
        g.declare('min_lista',    lambda lst: min(lst) if lst else None)
        g.declare('ordenar_lista', lambda lst, dec=False: sorted(lst, reverse=bool(dec)))
        g.declare('contar_onde',  lambda lst, fn: sum(1 for x in lst if fn(x)))

        g.declare('studio_executar', _studio_executar)

        g.declare('OS', {
            'env':      lambda k, d='': os.environ.get(k, d),
            'executar': _os_executar_obj,
                'capturar_em_thread': _os_capturar_em_thread,
                'executar_async': _os_executar_obj_async,
                'popen': _os_popen,   # retorna {saida, erro, codigo}
            'capturar': _os_capturar,       # retorna string da saída
            'sistema':  lambda cmd: os.system(cmd),  # retorna int (código de saída)
            'pwd':      os.getcwd,
            'cd':       os.chdir,
            'args':     sys.argv[1:],
            'existe':   os.path.exists,
            'pasta':    os.path.isdir,
            'arquivo':  os.path.isfile,
        })

        # ── Literais ────────────────────────────────────────────────────────
        g.declare('verdadeiro', True)
        g.declare('falso',      False)
        g.declare('nulo',       None)
        g.declare('imprimir',   print)
        g.declare('entrada',    input)
        g.declare('texto',      str)
        def _numero_seguro(x):
            if x is None: return 0
            s = str(x).strip()
            if not s: return 0
            try: return int(s) if s.lstrip('-').isdigit() else float(s)
            except: return 0
        g.declare('numero', _numero_seguro)
        g.declare('booleano',   bool)

        # ── Funções de tipo ──────────────────────────────────────────────────
        def _tipo(v):
            if v is None:               return 'nulo'
            if isinstance(v, bool):     return 'booleano'
            if isinstance(v, int):      return 'numero'
            if isinstance(v, float):    return 'numero'
            if isinstance(v, str):      return 'texto'
            if isinstance(v, list):     return 'lista'
            if isinstance(v, dict):     return 'mapa'
            if isinstance(v, tuple):    return 'lista'
            if isinstance(v, AdvakInstance):
                return getattr(getattr(v, 'klass', None), 'name', 'objeto')
            if isinstance(v, AdvakClass):
                return 'classe'
            if isinstance(v, AdvakFunction):
                return 'funcao'
            return type(v).__name__

        def _inteiro(v):
            try: return int(float(str(v).strip()))
            except: return 0

        def _lista_cast(v):
            if v is None: return []
            if isinstance(v, list): return v
            if isinstance(v, str): return list(v)
            if isinstance(v, dict): return list(v.keys())
            try: return list(v)
            except: return [v]

        def _mapa_cast(v):
            if isinstance(v, dict): return v
            if isinstance(v, list): return dict(enumerate(v))
            return {}

        def _e_numero(v):
            try: float(str(v)); return True
            except: return False

        def _e_texto(v):   return isinstance(v, str)
        def _e_lista(v):   return isinstance(v, (list, tuple))
        def _e_mapa(v):    return isinstance(v, dict)
        def _e_nulo(v):    return v is None
        def _e_logico(v):  return isinstance(v, bool)

        g.declare('tipo',          _tipo)

        # ── Depuração ────────────────────────────────────────────────────────
        def _parar():
            """Pausa a execução e abre o depurador interativo."""
            try:
                import advak_debug as _dbg
                dep = _dbg._depurador_global
                if dep:
                    linha = getattr(self, '_current_line', 0)
                    # parar() SEMPRE pausa, independente do modo
                    dep.passo_a_passo = True
                    _dbg.parar_aqui(linha, self.global_scope, 'global')
                    dep.passo_a_passo = False
            except ImportError:
                # Sem depurador: avisa e continua
                print("  ⚠️  parar() chamado mas depurador não está ativo")
                print("     Execute com: advak --debug arquivo.dk")

        def _inspecionar(val):
            """Inspeciona um valor no depurador."""
            try:
                import advak_debug as _dbg
                dep = _dbg._depurador_global
                if dep:
                    print(f"  🔍 {dep._val_str(val, detalhado=True)}")
                    print(f"     tipo: {dep._tipo_str(val)}")
                else:
                    print(f"  🔍 {repr(val)}")
            except ImportError:
                print(f"  🔍 {repr(val)}")
            return val

        def _rastrear():
            """Mostra pilha de chamadas atual."""
            try:
                import advak_debug as _dbg
                if _dbg._depurador_global:
                    _dbg._depurador_global.mostrar_pilha()
            except ImportError:
                pass

        # ── Sistema de Testes Unitários ─────────────────────────────────────
        _testes_resultados = []  # [(nome, passou, mensagem)]
        _testes_contexto   = [None]  # nome do teste atual

        def _testar(nome, fn):
            """testar('descrição', () => { afirmar(x == 5) })"""
            import threading as _thr
            _testes_contexto[0] = nome
            erro_holder = [None]
            def _run_fn():
                try:
                    if hasattr(fn, 'params'):
                        import asyncio as _aio
                        loop = _aio.new_event_loop()
                        _aio.set_event_loop(loop)
                        try: loop.run_until_complete(self._call_fn(fn, [], self.global_scope))
                        finally: loop.close()
                    else:
                        fn()
                except _AfirmarError as e:
                    erro_holder[0] = e
                except AdvakError as e:
                    erro_holder[0] = _AfirmarError(str(e))
                except Exception as e:
                    erro_holder[0] = _AfirmarError(f"Erro: {e}")
            t = _thr.Thread(target=_run_fn, daemon=True)
            t.start(); t.join(timeout=10)
            if t.is_alive():
                _testes_resultados.append((nome, False, "Timeout (>10s)"))
                print(f"  ❌ {nome}: Timeout")
            elif erro_holder[0]:
                _testes_resultados.append((nome, False, str(erro_holder[0])))
                print(f"  ❌ {nome}")
                print(f"     {erro_holder[0]}")
            else:
                _testes_resultados.append((nome, True, None))
                print(f"  ✅ {nome}")
            _testes_contexto[0] = None
            return None

        class _AfirmarError(Exception): pass

        def _afirmar(cond, mensagem=None):
            if not cond:
                msg = mensagem or "Condição falsa"
                raise _AfirmarError(f"Falhou: {msg}")

        def _afirmar_igual(a, b, msg=None):
            if a != b:
                raise _AfirmarError(msg or f"Esperado {b!r}, obteve {a!r}")

        def _afirmar_diferente(a, b, msg=None):
            if a == b:
                raise _AfirmarError(msg or f"Esperado diferente de {b!r}")

        def _afirmar_verdadeiro(v, msg=None):
            if not v:
                raise _AfirmarError(msg or f"Esperado verdadeiro, obteve {v!r}")

        def _afirmar_falso(v, msg=None):
            if v:
                raise _AfirmarError(msg or f"Esperado falso, obteve {v!r}")

        def _afirmar_nulo(v, msg=None):
            if v is not None:
                raise _AfirmarError(msg or f"Esperado nulo, obteve {v!r}")

        def _afirmar_contem(colecao, item, msg=None):
            if item not in colecao:
                raise _AfirmarError(msg or f"{item!r} não encontrado em {colecao!r}")

        def _afirmar_erro(fn, msg=None):
            """Verifica que a função lança um erro."""
            import threading as _thr
            erro_holder = [None]; lançou = [False]
            def _run():
                try:
                    if hasattr(fn, 'params'):
                        import asyncio as _aio
                        loop = _aio.new_event_loop(); _aio.set_event_loop(loop)
                        try: loop.run_until_complete(self._call_fn(fn, [], self.global_scope))
                        finally: loop.close()
                    else: fn()
                except (AdvakError, Exception): lançou[0] = True
            t = _thr.Thread(target=_run, daemon=True); t.start(); t.join(5)
            if not lançou[0]:
                raise _AfirmarError(msg or "Era esperado um erro, mas nenhum foi lançado")

        def _resumo_testes():
            total   = len(_testes_resultados)
            passou  = sum(1 for _, p, _ in _testes_resultados if p)
            falhou  = total - passou
            print()
            print("  " + "─" * 44)
            print(f"  Resultado: {passou}/{total} testes passaram", end="")
            if falhou: print(f"  ({falhou} falharam)")
            else: print("  🎉")
            return {'total': total, 'passou': passou, 'falhou': falhou}

        g.declare('testar',           _testar)
        g.declare('afirmar',          _afirmar)
        g.declare('afirmar_igual',    _afirmar_igual)
        g.declare('afirmar_diferente',_afirmar_diferente)
        g.declare('afirmar_verdadeiro',_afirmar_verdadeiro)
        g.declare('afirmar_falso',    _afirmar_falso)
        g.declare('afirmar_nulo',     _afirmar_nulo)
        g.declare('afirmar_contem',   _afirmar_contem)
        g.declare('afirmar_erro',     _afirmar_erro)
        g.declare('resumo_testes',    _resumo_testes)

        g.declare('parar',      _parar)
        g.declare('inspecionar',_inspecionar)
        g.declare('rastrear',   _rastrear)

        # ── Servidor Web ─────────────────────────────────────────────────
        try:
            import advak_web as _aweb
            _srv = _aweb._get_servidor()

            def _html_fn(conteudo, status=200):
                return _aweb._html(str(conteudo), int(status))
            def _json_fn(dados, status=200):
                return _aweb._json_resp(dados, int(status))
            def _texto_fn(conteudo, status=200):
                return _aweb._texto_resp(str(conteudo), int(status))
            def _redir_fn(url, status=302):
                return _aweb._redirecionar(str(url), int(status))
            def _render_fn(tmpl, ctx=None):
                return _aweb._renderizar(str(tmpl), ctx)

            # Store interpreter reference for async handler calls
            _interp_ref = self
            _main_loop  = [None]  # will be set when iniciar() is called

            def _rota_fn(caminho, handler, metodo="GET"):
                # Aceita (caminho, handler[, metodo]) e (caminho, metodo, handler)
                if isinstance(handler, str) and not isinstance(metodo, str):
                    handler, metodo = metodo, handler
                _srv.rota(str(caminho), _wrap_handler(handler), str(metodo))
                return _srv

            async def _iniciar_servidor_coro(p=8080, auto=True):
                import asyncio as _aio, threading as _th, atexit as _ax
                _srv.porta(int(p))
                _srv.auto_abrir(bool(auto))
                _main_loop[0] = _aio.get_running_loop()
                _done = _th.Event()

                def _run_http():
                    try:
                        _srv.iniciar(bloquear=True)
                    except Exception:
                        pass
                    finally:
                        _done.set()

                _t = _th.Thread(target=_run_http, daemon=True)
                _t.name = "AdvakWebServer"

                # Register clean shutdown
                _ax.register(lambda: _srv.parar() if _srv._servidor else None)

                _t.start()
                try:
                    while not _done.is_set():
                        await _aio.sleep(0.05)
                except (_aio.CancelledError, KeyboardInterrupt, SystemExit):
                    try:
                        _srv.parar()
                    except Exception:
                        pass

            def _iniciar_servidor(p=8080, auto=True):
                # Return the coroutine directly so _eval_call awaits it.
                # This keeps the asyncio loop alive until the server stops.
                return _iniciar_servidor_coro(p, auto)

            def _wrap_handler_no_args(handler):
                """Wraps an AdvakFunction that takes no arguments (for transacao, callbacks)."""
                if not hasattr(handler, 'params'):
                    return handler  # already Python callable
                import concurrent.futures as _cf
                def _py_wrap():
                    loop = _main_loop[0]
                    if loop and loop.is_running():
                        fut = _cf.Future()
                        async def _r(fut=fut):
                            try:
                                r = await _interp_ref._call_fn(handler, [], _interp_ref.global_scope)
                                fut.set_result(r)
                            except Exception as e:
                                fut.set_exception(e)
                        import asyncio as _aio
                        _aio.run_coroutine_threadsafe(_r(), loop)
                        return fut.result(timeout=30)
                    else:
                        import asyncio as _aio
                        nl = _aio.new_event_loop()
                        try:
                            return nl.run_until_complete(
                                _interp_ref._call_fn(handler, [], _interp_ref.global_scope))
                        finally:
                            nl.close()
                return _py_wrap

            def _wrap_handler(handler):
                """Wraps an AdvakFunction so it can be called from Python threads."""
                if not hasattr(handler, 'params'):
                    return handler  # already a Python callable
                import concurrent.futures as _cf
                def _py_wrap(req):
                    req_obj = {
                        'metodo': getattr(req, 'metodo', getattr(req, 'method', 'GET')),
                        'caminho': getattr(req, 'caminho', getattr(req, 'path', '/')),
                        'consulta': getattr(req, 'consulta', getattr(req, 'query', {})),
                        'corpo': getattr(req, 'corpo', getattr(req, 'body', '')),
                        'cabecalhos': getattr(req, 'cabecalhos', getattr(req, 'headers', {})),
                        'parametros': getattr(req, 'parametros', getattr(req, 'params', {})),
                        'dados': getattr(req, 'dados', getattr(req, 'json', None)),
                        'sessao': getattr(req, 'sessao', {}),
                        'usuario': getattr(req, 'usuario', None),
                        'eh_get': getattr(req, 'eh_get', False),
                        'eh_post': getattr(req, 'eh_post', False),
                        'method': getattr(req, 'method', getattr(req, 'metodo', 'GET')),
                        'path': getattr(req, 'path', getattr(req, 'caminho', '/')),
                        'query': getattr(req, 'query', getattr(req, 'consulta', {})),
                        'params': getattr(req, 'params', getattr(req, 'parametros', {})),
                        'json': getattr(req, 'json', getattr(req, 'dados', None)),
                    }
                    loop = _main_loop[0]
                    if loop and loop.is_running():
                        import asyncio as _aio
                        fut = _cf.Future()
                        async def _r(fut=fut, req_obj=req_obj):
                            try:
                                r = await _interp_ref._call_fn(
                                    handler, [req_obj], _interp_ref.global_scope)
                                fut.set_result(r)
                            except Exception as e:
                                fut.set_exception(e)
                        _aio.run_coroutine_threadsafe(_r(), loop)
                        return fut.result(timeout=30)
                    else:
                        import asyncio as _aio
                        nl = _aio.new_event_loop()
                        try:
                            return nl.run_until_complete(
                                _interp_ref._call_fn(handler, [req_obj], _interp_ref.global_scope))
                        finally:
                            nl.close()
                return _py_wrap

            def _srv_obj():
                return {
                    # ── Configuração ─────────────────────────────
                    'porta':       lambda p: (_srv.porta(p), _srv)[1],
                    'hospedeiro':  lambda h: (_srv.host(h), _srv)[1],
                    'host':        lambda h: (_srv.host(h), _srv)[1],

                    # ── Rotas (PT-BR completo) ────────────────────
                    'rota':        _rota_fn,
                    'obter':       lambda c, h: _rota_fn(c, h, "GET"),
                    'publicar':    lambda c, h: _rota_fn(c, h, "POST"),
                    'atualizar':   lambda c, h: _rota_fn(c, h, "PUT"),
                    'deletar':     lambda c, h: _rota_fn(c, h, "DELETE"),
                    'qualquer':    lambda c, h: _rota_fn(c, h, "*"),

                    # ── Aliases em inglês (compatibilidade) ───────
                    'get':         lambda c, h: _rota_fn(c, h, "GET"),
                    'post':        lambda c, h: _rota_fn(c, h, "POST"),
                    'put':         lambda c, h: _rota_fn(c, h, "PUT"),
                    'delete':      lambda c, h: _rota_fn(c, h, "DELETE"),

                    # ── Respostas: servidor.json(...), servidor.html(...) ─────
                    'json':         _json_fn,
                    'html':         _html_fn,
                    'texto':        _texto_fn,
                    'redirecionar': _redir_fn,
                    'renderizar':   _render_fn,

                    # ── Arquivos estáticos ────────────────────────
                    'estatico':   lambda url, pasta: _srv.estatico(str(url), str(pasta)),
                    'arquivos':    lambda url, pasta: _srv.estatico(str(url), str(pasta)),

                    # ── Controle ──────────────────────────────────
                    'iniciar':     lambda p=8080, auto=True: _iniciar_servidor(p, auto),
                    'parar':       _srv.parar,

                    # ── Middleware de erro ────────────────────────
                    'erro_404':    lambda fn: setattr(_srv, '_erro_404', fn),
                    'erro_500':    lambda fn: setattr(_srv, '_erro_500', fn),
                    # ── Banco integrado ────────────────────────────
                    'usar_banco':    lambda arq="app.db": _srv.usar_banco(str(arq)),
                    'criar_tabela':  lambda nome, campos: _srv.criar_tabela(str(nome), campos),
                    # ── Auth integrado ─────────────────────────────
                    'proteger':      lambda rota, fn, nivel=None: _srv.proteger(str(rota), fn, nivel),
                    'usar':          lambda fn: _srv.usar(_wrap_handler(fn)),
                    # ── WebSocket integrado ────────────────────────
                    'ao_conexao_ws': lambda fn: _srv.ao_conexao_ws(fn),
                    'ao_mensagem_ws':lambda ev, fn: _srv.ao_mensagem_ws(str(ev), fn),
                    'transmitir':    lambda dados, sala=None: _srv.ws.transmitir(dados, sala),
                }

            # ── Banco Automático (PostgreSQL → SQLite fallback) ──────────────
            try:
                from advak_bancoweb import BancoWeb as _BancoWeb
                _banco_web_disponivel = True
            except ImportError:
                _banco_web_disponivel = False

            def _banco_auto_fn(nome="app", **kwargs):
                if _banco_web_disponivel:
                    db = _BancoWeb(str(nome), **{str(k): v for k, v in kwargs.items()})
                else:
                    # Ultra fallback: SQLite via advak_web.BancoAuto
                    arq = str(nome) if str(nome).endswith('.db') else str(nome)+'.db'
                    db  = _aweb.BancoAuto(arq) if hasattr(_aweb, 'BancoAuto') else None
                    if not db: raise RuntimeError("Nenhum banco disponível")

                def _tabela_wrapper(nome_tab, tab_obj=None):
                    """Cria um objeto de tabela com métodos em PT-BR."""
                    if tab_obj is None:
                        tab_obj = db._tabela_obj(str(nome_tab)) if hasattr(db, '_tabela_obj') else {}

                    def _sql_param(n):
                        """Cria marcador de parâmetro correto para o banco atual."""
                        if hasattr(db, 'modo') and db.modo == 'pg':
                            return f'${n}'
                        return '?'

                    return {
                        'nome':       str(nome_tab),
                        'inserir':    tab_obj.get('inserir',   lambda d: db.inserir(str(nome_tab), d)),
                        'buscar':     tab_obj.get('buscar',    lambda c=None,p=None,o=None,l=None: db.buscar(str(nome_tab),c,p,o,l)),
                        'buscar_um':  tab_obj.get('buscar_um', lambda c,p=None: db.buscar_um(str(nome_tab),c,p)),
                        'buscar_id':  tab_obj.get('buscar_id', lambda id: db.buscar_um(str(nome_tab), _sql_param(1)+'id='+_sql_param(1) if False else ('id=$1' if hasattr(db,'modo') and db.modo=='pg' else 'id=?'), [id])),
                        'atualizar':  tab_obj.get('atualizar', lambda d,c,p=None: db.atualizar(str(nome_tab),d,c,p)),
                        'atualizar_id': tab_obj.get('atualizar_id', lambda id,d: db.atualizar_id(str(nome_tab),id,d) if hasattr(db,'atualizar_id') else db.atualizar(str(nome_tab),d,'id=?',[id])),
                        'excluir':    tab_obj.get('excluir',   lambda c=None,p=None: db.excluir(str(nome_tab),c,p)),
                        'excluir_id': tab_obj.get('excluir_id',lambda id: db.excluir(str(nome_tab),'id=$1' if hasattr(db,'modo') and db.modo=='pg' else 'id=?',[id])),
                        'contar':     tab_obj.get('contar',    lambda c=None,p=None: db.contar(str(nome_tab),c,p)),
                        'existe':     tab_obj.get('existe',    lambda c,p=None: db.contar(str(nome_tab),c,p) > 0),
                        'todos':      tab_obj.get('todos',     lambda o='id': db.buscar(str(nome_tab),ordenar=o)),
                        'sql':        lambda s,p=None: db.sql(s,p) if hasattr(db,'sql') else db.sql_direto(s,p),
                        'limpar':     tab_obj.get('limpar',    lambda: db.excluir(str(nome_tab))),
                    }

                def _criar_tabela(nome_tab, campos):
                    if hasattr(db, 'criar_tabela'):
                        tab = db.criar_tabela(str(nome_tab), campos)
                        return _tabela_wrapper(nome_tab, tab)
                    return _tabela_wrapper(nome_tab)

                def _banco_obj():
                    return {
                        # ── Criação de tabelas ───────────────────────────────────────
                        'criar_tabela': _criar_tabela,
                        # ── SQL direto ───────────────────────────────────────────────
                        'sql':          lambda s, p=None: (db.sql(s,p) if hasattr(db,'sql') else db.sql_direto(s,p)),
                        # ── Informações ─────────────────────────────────────────────
                        'info':         lambda: (db.info() if hasattr(db,'info') else {'modo':'desconhecido'}),
                        'modo':         getattr(db, 'modo', 'desconhecido'),
                        'eh_postgres':  getattr(db, 'eh_postgres', False),
                        'eh_sqlite':    getattr(db, 'eh_sqlite', True),
                        # ── Controle ────────────────────────────────────────────────
                        'fechar':       db.fechar,
                        'transacao':    lambda fn: (
                                        db.transacao(_wrap_handler_no_args(fn))
                                        if hasattr(db,'transacao') else fn()
                                    ),
                        # ── CRUD direto (sem tabela) ─────────────────────────────────
                        'inserir':      lambda tab, d: db.inserir(str(tab), d),
                        'buscar':       lambda tab, c=None, p=None, o=None, l=None: db.buscar(str(tab),c,p,o,l),
                        'atualizar':    lambda tab, d, c, p=None: db.atualizar(str(tab),d,c,p),
                        'excluir':      lambda tab, c=None, p=None: db.excluir(str(tab),c,p),
                        'contar':       lambda tab, c=None, p=None: db.contar(str(tab),c,p),
                    }

                return _banco_obj()

            # ── Autenticação ───────────────────────────────────────────────
            def _auth_obj():
                auth = _srv.auth
                return {
                    'cadastrar':     lambda login, senha, nome="", nivel="usuario", dados=None:
                                        auth.cadastrar(str(login), str(senha), str(nome), str(nivel), dados),
                    'fazer_login':   lambda login, senha: (lambda sid, u: {
                                        'sucesso': sid is not None,
                                        'sid': sid, 'usuario': u
                                    })(*auth.fazer_login(str(login), str(senha))),
                    'fazer_logout':  lambda sid: auth.fazer_logout(str(sid)),
                    'usuario_atual': lambda sid: auth.usuario_atual(str(sid)),
                    'autenticar':    lambda l, s: auth.autenticar(str(l), str(s)),
                }

            # ── Sessões ───────────────────────────────────────────────────
            def _sessoes_obj():
                s = _srv.sessoes
                return {
                    'criar':   lambda d=None: s.criar(d),
                    'obter':   lambda sid: s.obter(str(sid)),
                    'salvar':  lambda sid, d: s.salvar(str(sid), d),
                    'destruir':lambda sid: s.destruir(str(sid)),
                }

            # ── WebSocket ──────────────────────────────────────────────────
            def _ws_obj():
                ws = _srv.ws
                return {
                    'enviar':     lambda cid, dados: ws.enviar(str(cid), dados),
                    'transmitir': lambda dados, sala=None, exceto=None:
                                    ws.transmitir(dados, sala, exceto),
                    'entrar_sala':lambda cid, sala: ws.entrar_sala(str(cid), str(sala)),
                    'sair_sala':  lambda cid, sala: ws.sair_sala(str(cid), str(sala)),
                    'contar':     lambda sala=None: ws.contar(sala),
                    'ao_mensagem':lambda evento, fn: ws.ao_mensagem(str(evento), fn),
                    'ao_conexao': lambda fn: setattr(ws, '_handler_conexao', fn),
                }

            g.declare('servidor',       _srv_obj())
            g.declare('banco_auto',     _banco_auto_fn)
            g.declare('autenticacao',   _auth_obj())
            g.declare('sessoes',        _sessoes_obj())
            g.declare('ws',             _ws_obj())

            # ── Respostas HTTP (PT-BR) ─────────────────────────────────────
            g.declare('html',            _html_fn)
            g.declare('resposta_html',   _html_fn)
            g.declare('resposta_json',   _json_fn)
            g.declare('json_resp',       _json_fn)
            g.declare('resposta_texto',  _texto_fn)
            g.declare('texto_resp',      _texto_fn)
            g.declare('redirecionar',    _redir_fn)
            g.declare('renderizar',      _render_fn)

            # ── Memoização (@memorizar) ──────────────────────────────────────
            _memo_cache = {}
            def _memorizar_fn(fn):
                """Decora uma função para memoizar resultados (cache automático)."""
                _cache = {}
                if hasattr(fn, 'params'):  # AdvakFunction
                    import functools
                    async def _memoized(*args, **kwargs):
                        key = str(args)
                        if key not in _cache:
                            _cache[key] = await self._call_fn(fn, list(args), self.global_scope)
                        return _cache[key]
                    return _memoized
                else:
                    def _memoized_py(*args):
                        key = str(args)
                        if key not in _cache:
                            _cache[key] = fn(*args)
                        return _cache[key]
                    return _memoized_py
            g.declare('memorizar', _memorizar_fn)
            g.declare('memo',      _memorizar_fn)

        except ImportError:
            pass  # advak_web.py not found — web server not available


        # ── Regex ─────────────────────────────────────────────────────────────
        import re as _re
        def _regex_testar(padrao, texto_alvo):
            try: return bool(_re.search(padrao, str(texto_alvo)))
            except: return False
        def _regex_extrair(padrao, texto_alvo):
            try:
                m = _re.search(padrao, str(texto_alvo))
                if not m: return nulo
                return list(m.groups()) if m.groups() else m.group(0)
            except: return None
        def _regex_extrair_todos(padrao, texto_alvo):
            try: return _re.findall(padrao, str(texto_alvo))
            except: return []
        def _regex_substituir(padrao, subst, texto_alvo):
            try: return _re.sub(padrao, subst, str(texto_alvo))
            except: return texto_alvo
        def _regex_dividir(padrao, texto_alvo):
            try: return _re.split(padrao, str(texto_alvo))
            except: return [texto_alvo]

        _regex_obj = {
            'testar':       _regex_testar,
            'extrair':      _regex_extrair,
            'extrair_todos':_regex_extrair_todos,
            'substituir':   _regex_substituir,
            'dividir':      _regex_dividir,
        }
        g.declare('Regex', _regex_obj)
        g.declare('inteiro',       _inteiro)
        g.declare('lista',         _lista_cast)
        g.declare('mapa',          _mapa_cast)
        g.declare('e_numero',      _e_numero)
        g.declare('e_texto',       _e_texto)
        g.declare('e_lista',       _e_lista)
        g.declare('e_mapa',        _e_mapa)
        g.declare('e_nulo',        _e_nulo)
        g.declare('e_logico',      _e_logico)
        g.declare('e_booleano',    _e_logico)


        # ── Canvas 2D ────────────────────────────────────────────────────────
        canvas_api = self._make_canvas_api()
        g.declare('tela',       canvas_api)
        g.declare('canvas',     canvas_api)

        # ── Lógica / Prolog ──────────────────────────────────────────────────
        _db = self.prolog_db
        g.declare('logica',     _db)
        g.declare('logic',      _db)

        # ── Generators — auxiliares ──────────────────────────────────────────
        async def _range_gen(start, stop=None, step=1):
            if stop is None: start, stop = 0, start
            i = start
            while (step > 0 and i < stop) or (step < 0 and i > stop):
                yield i
                i += step

        def _advak_range(a, b=None, c=1):
            import asyncio
            gen = _range_gen(a, b, c)
            return AdvakGenerator(gen)

        g.declare('intervalo',  _advak_range)
        g.declare('range',      _advak_range)

        # ── advak_executar — executa código .dk e retorna saída como texto ────
        def _advak_executar(codigo_str):
            """Executa código Advak e retorna saída como string.
            Thread-safe: usa Queue global para comunicar com a main thread.
            """
            import io, sys, asyncio, threading
            from advak_lexer import AdvakLexer
            from advak_parser import Parser as _Parser

            codigo_str = str(codigo_str)
            tem_gui = any(kw in codigo_str for kw in
                         ('gui.janela','gui.tema','gui.botao','gui.label',
                          'gui.campo','gui.tabela','gui.abas','gui.iniciar',
                          'gui.frame','gui.area_texto','gui.datagrid'))

            if tem_gui:
                import advak_gui_modern as _gm
                root = _gm._root_ref
                if not root:
                    return "❌ Interface gráfica não disponível"

                result_holder = [None]
                done_evt = threading.Event()

                def _executar_gui():
                    """Agendado na main thread — só cria o Toplevel.
                    O asyncio roda em thread separada para não bloquear o event loop.
                    """
                    _orig_janela  = _gm.AdvakGUIModern.janela
                    _orig_iniciar = _gm.AdvakGUIModern.iniciar
                    popup_holder  = [None]

                    def _popup(self2, titulo='App', largura=800, altura=600, **kw):
                        import tkinter as tk
                        try:
                            p = tk.Toplevel(root)
                            p.title(titulo)
                            p.geometry(f"{largura}x{altura}")
                            p.configure(bg=_gm._t('bg'))
                            self2._root = p
                            self2._tema_nome = _gm._tema_atual
                            popup_holder[0] = p
                            return p
                        except Exception:
                            return None

                    def _noop(self2): pass

                    _gm.AdvakGUIModern.janela  = _popup
                    _gm.AdvakGUIModern.iniciar = _noop

                    def _run_asyncio():
                        """Roda o interpretador em thread separada com asyncio próprio."""
                        import warnings
                        warnings.filterwarnings('ignore', category=RuntimeWarning,
                                                message='coroutine.*never awaited')
                        buf = io.StringIO()
                        old_out = sys.stdout
                        sys.stdout = buf
                        try:
                            tokens    = AdvakLexer(codigo_str).tokenize()
                            ast_inner = _Parser(tokens).parse()
                            interp_i  = AdvakInterpreter(ast_inner)
                            loop_i = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop_i)
                            try:
                                loop_i.run_until_complete(interp_i.interpret())
                            finally:
                                loop_i.close()
                            sys.stdout = old_out
                            out = buf.getvalue()
                            result_holder[0] = out if out.strip() else "✅ Janela aberta!"
                        except SyntaxError as e:
                            sys.stdout = old_out
                            result_holder[0] = f"❌ Sintaxe: {e}"
                        except Exception as e:
                            sys.stdout = old_out
                            _tn = type(e).__name__
                            _trad = {'RecursionError':'Recursão muito profunda','TypeError':'Tipo incompatível','ValueError':'Valor inválido','KeyError':'Chave não encontrada','IndexError':'Índice fora do alcance','MemoryError':'Memória insuficiente','AttributeError':'Propriedade não encontrada'}
                            result_holder[0] = f"❌ {_trad.get(_tn, _tn)}: {e}"
                        finally:
                            _gm.AdvakGUIModern.janela  = _orig_janela
                            _gm.AdvakGUIModern.iniciar = _orig_iniciar
                            done_evt.set()

                    # Lança o interpretador numa thread separada (asyncio seguro)
                    threading.Thread(target=_run_asyncio, daemon=True).start()

                # Usa a fila global de tarefas GUI (evita root.after de thread errada)
                if hasattr(_gm, '_gui_task_queue'):
                    _gm._gui_task_queue.put(_executar_gui)
                    done_evt.wait(timeout=20)
                    return result_holder[0] or "⏱️ Timeout"
                else:
                    # Fallback: executa em thread separada
                    t = threading.Thread(target=_executar_gui, daemon=True)
                    t.start()
                    done_evt.wait(timeout=20)
                    return result_holder[0] or "⏱️ Timeout"
            else:
                # Sem GUI — executa em thread separada para evitar conflito de event loop
                import threading
                buf = io.StringIO()
                resultado_holder = [None]
                erro_holder = [None]
                done = threading.Event()

                def _executar_em_thread():
                    import builtins as _builtins
                    old_out = sys.stdout
                    old_print = _builtins.print
                    sys.stdout = buf
                    # Redirecionar builtins.print para o buffer
                    def _print_cap(*a, **k):
                        sep = k.get('sep', ' ')
                        end = k.get('end', '\n')
                        txt = sep.join(str(x) for x in a) + end
                        buf.write(txt)
                    _builtins.print = _print_cap
                    try:
                        tokens    = AdvakLexer(codigo_str).tokenize()
                        ast_inner = _Parser(tokens).parse()
                        interp_i  = AdvakInterpreter(ast_inner)
                        # Cria event loop próprio nesta thread
                        loop_i = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop_i)
                        try:
                            loop_i.run_until_complete(interp_i.interpret())
                        finally:
                            loop_i.close()
                            asyncio.set_event_loop(None)
                        sys.stdout = old_out
                        _builtins.print = old_print
                        out = buf.getvalue()
                        resultado_holder[0] = out if out.strip() else '✅ Executado sem saída'
                    except SyntaxError as e:
                        sys.stdout = old_out
                        _builtins.print = old_print
                        resultado_holder[0] = f'❌ Sintaxe: {e}'
                    except Exception as e:
                        sys.stdout = old_out
                        _builtins.print = old_print
                        _tn2 = type(e).__name__
                        _trad2 = {'RecursionError':'Recursão muito profunda — verifique o caso base da função','TypeError':'Tipo incompatível','ValueError':'Valor inválido','KeyError':'Chave não encontrada','IndexError':'Índice fora do alcance','MemoryError':'Memória insuficiente'}
                        resultado_holder[0] = f'❌ {_trad2.get(_tn2, _tn2)}: {e}'
                    finally:
                        done.set()

                t = threading.Thread(target=_executar_em_thread, daemon=True)
                t.start()
                # Aguardar conclusão com timeout — sem root.update() para evitar
                # processamento de eventos reentrantes que podem corromper o estado
                done.wait(timeout=15)
                return resultado_holder[0] or ('⏱️ Tempo esgotado — código demorou mais de 15s' if not done.is_set() else '✅ Sem saída')


        
        def _aplicar_highlight(widget_obj):
            """Aplica syntax highlighting Advak ao widget Text tkinter."""
            import re as _re
            try:
                w = widget_obj  # é o widget tkinter Text

                # ── Cores (VS Code Dark+ style) ──────────────────────────
                CORES = {
                    'kw_controle': {'foreground': '#569CD6', 'font': ('Consolas', 11, 'bold')},
                    'kw_decl':     {'foreground': '#4EC9B0', 'font': ('Consolas', 11, 'bold')},
                    'kw_valor':    {'foreground': '#569CD6'},
                    'string':      {'foreground': '#CE9178'},
                    'comentario':  {'foreground': '#6A9955', 'font': ('Consolas', 11, 'italic')},
                    'numero':      {'foreground': '#B5CEA8'},
                    'builtin':     {'foreground': '#DCDCAA'},
                    'funcao_nome': {'foreground': '#DCDCAA'},
                    'classe_nome': {'foreground': '#4EC9B0', 'font': ('Consolas', 11, 'bold')},
                    'propriedade': {'foreground': '#9CDCFE'},
                    'pontuacao':   {'foreground': '#FFD700'},
                    'operador':    {'foreground': '#D4D4D4'},
                    'template':    {'foreground': '#CE9178'},
                }

                # Configurar tags
                for nome, opts in CORES.items():
                    w.tag_configure(nome, **opts)

                # Remover tags antigas
                for nome in CORES:
                    w.tag_remove(nome, '1.0', 'end')

                # ── Tokens Advak ─────────────────────────────────────────
                KW_CONTROLE = {'se','senão','senao','para','enquanto','retornar',
                               'quebrar','continuar','tentar','pegar','finalmente',
                               'lançar','lancar','combinar','caso','e','ou','nao'}
                KW_DECL     = {'seja','fixo','funcao','classe','herda','importar',
                               'exportar','de','como','assincrona','aguarda','produzir'}
                KW_VALOR    = {'verdadeiro','falso','nulo','isso','super'}
                BUILTINS    = {'imprimir','entrada','texto','numero','inteiro','arred',
                               'piso','teto','abs','raiz','aleatorio','tipo','booleano',
                               'data_hoje','data_agora','moeda','memorizar','memo',
                               'banco_auto','servidor','gui','Arquivo','Regex','JSON',
                               'HTTP','OS','Math','resposta_json','html','redirecionar'}

                src = w.get('1.0', 'end')
                linhas = src.split('\n')

                for ln_idx, linha in enumerate(linhas):
                    ln_num = ln_idx + 1
                    n = len(linha)
                    i = 0

                    while i < n:
                        ch = linha[i]

                        # Comentário //
                        if ch == '/' and i+1 < n and linha[i+1] == '/':
                            inicio = f'{ln_num}.{i}'
                            fim    = f'{ln_num}.{n}'
                            w.tag_add('comentario', inicio, fim)
                            break

                        # Template string `...`
                        if ch == '`':
                            j = i + 1
                            while j < n:
                                if linha[j] == '\\' and j+1 < n: j += 2; continue
                                if linha[j] == '`': j += 1; break
                                j += 1
                            w.tag_add('template', f'{ln_num}.{i}', f'{ln_num}.{j}')
                            i = j; continue

                        # String aspas duplas
                        if ch == '"':
                            j = i + 1
                            while j < n:
                                if linha[j] == '\\' and j+1 < n: j += 2; continue
                                if linha[j] == '"': j += 1; break
                                j += 1
                            w.tag_add('string', f'{ln_num}.{i}', f'{ln_num}.{j}')
                            i = j; continue

                        # String aspas simples
                        if ch == "'":
                            j = i + 1
                            while j < n:
                                if linha[j] == '\\' and j+1 < n: j += 2; continue
                                if linha[j] == "'": j += 1; break
                                j += 1
                            w.tag_add('string', f'{ln_num}.{i}', f'{ln_num}.{j}')
                            i = j; continue

                        # Números
                        if ch.isdigit() or (ch == '.' and i+1 < n and linha[i+1].isdigit()):
                            j = i
                            while j < n and (linha[j].isdigit() or linha[j] in '.eE_'):
                                j += 1
                            w.tag_add('numero', f'{ln_num}.{i}', f'{ln_num}.{j}')
                            i = j; continue

                        # Identificadores
                        if ch.isalpha() or ch == '_':
                            j = i
                            while j < n and (linha[j].isalnum() or linha[j] == '_'):
                                j += 1
                            palavra = linha[i:j]
                            ini = f'{ln_num}.{i}'
                            fim = f'{ln_num}.{j}'

                            if palavra in KW_CONTROLE:
                                w.tag_add('kw_controle', ini, fim)
                            elif palavra in KW_DECL:
                                w.tag_add('kw_decl', ini, fim)
                                # Nome de função/classe logo após a keyword
                                k = j
                                while k < n and linha[k] == ' ': k += 1
                                if k < n and (linha[k].isalpha() or linha[k] == '_'):
                                    m = k
                                    while m < n and (linha[m].isalnum() or linha[m] == '_'): m += 1
                                    tag = 'classe_nome' if palavra == 'classe' else 'funcao_nome'
                                    w.tag_add(tag, f'{ln_num}.{k}', f'{ln_num}.{m}')
                            elif palavra in KW_VALOR:
                                w.tag_add('kw_valor', ini, fim)
                            elif palavra in BUILTINS:
                                w.tag_add('builtin', ini, fim)
                            else:
                                # Acesso de propriedade (precedido de ".")
                                if i > 0 and linha[i-1] == '.':
                                    w.tag_add('propriedade', ini, fim)
                                # Chamada de função (seguida de "(")
                                elif j < n and linha[j] == '(':
                                    w.tag_add('funcao_nome', ini, fim)

                            i = j; continue

                        # Pontuação
                        if ch in '()[]{}':
                            w.tag_add('pontuacao', f'{ln_num}.{i}', f'{ln_num}.{i+1}')

                        # Operadores
                        if ch in '+-*/%=<>!&|^~':
                            w.tag_add('operador', f'{ln_num}.{i}', f'{ln_num}.{i+1}')

                        i += 1

            except Exception as _e:
                pass  # Silently ignore highlight errors

        g.declare('aplicar_highlight_editor', _aplicar_highlight)

        g.declare('advak_executar', _advak_executar)

        def _advak_executar_async(codigo_str, callback_fn):
            """Executa código Advak em thread separada.
            Quando terminar, chama callback_fn(resultado) de forma thread-safe
            via _gui_task_queue — sem bloquear o tkinter."""
            import io, sys, asyncio, threading
            try:
                import advak_gui_modern as _agm
                fila = _agm._gui_task_queue
            except Exception:
                # Sem GUI, executar síncrono
                resultado = _advak_executar(codigo_str)
                if callable(callback_fn):
                    try: callback_fn(resultado)
                    except Exception: pass
                return

            codigo_str = str(codigo_str)
            buf = io.StringIO()
            done = threading.Event()

            def _run():
                import builtins as _bi
                old_out = sys.stdout
                old_print = _bi.print
                sys.stdout = buf
                def _cap(*a, **k):
                    sep = k.get('sep',' '); end = k.get('end','\n')
                    buf.write(sep.join(str(x) for x in a) + end)
                _bi.print = _cap
                try:
                    from advak_lexer import AdvakLexer
                    from advak_parser import Parser as _P
                    tokens = AdvakLexer(codigo_str).tokenize()
                    ast    = _P(tokens).parse()
                    interp = AdvakInterpreter(ast)
                    loop   = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(interp.interpret())
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)
                    sys.stdout = old_out
                    _bi.print = old_print
                    resultado = buf.getvalue() or '✅ Executado sem saída'
                except RecursionError:
                    sys.stdout = old_out; _bi.print = old_print
                    resultado = '❌ Recursão muito profunda — adicione um caso base'
                except Exception as e:
                    sys.stdout = old_out; _bi.print = old_print
                    _tn = type(e).__name__
                    _trad = {'TypeError':'Tipo incompatível','ValueError':'Valor inválido',
                             'KeyError':'Chave não encontrada','IndexError':'Índice fora do alcance',
                             'FileNotFoundError':'Arquivo não encontrado','PermissionError':'Permissão negada'}
                    resultado = f'❌ {_trad.get(_tn, _tn)}: {e}'
                finally:
                    # Enfileirar callback para ser executado na thread tkinter
                    def _callback_safe():
                        try:
                            if callable(callback_fn):
                                callback_fn(resultado)
                        except Exception:
                            pass
                    try:
                        fila.put_nowait(_callback_safe)
                    except Exception:
                        pass

            t = threading.Thread(target=_run, daemon=True)
            t.start()

        g.declare('advak_executar_async', _advak_executar_async)

        def _executar_em_thread(codigo_str, resultado_lista):
            """Executa código em thread separada, guarda resultado em resultado_lista[0].
            Não bloqueia. O studio usa jan.after() para verificar o resultado."""
            import io, sys, asyncio, threading, builtins as _bi

            codigo_str = str(codigo_str)
            buf = io.StringIO()

            def _run():
                old_out = sys.stdout
                old_print = _bi.print
                sys.stdout = buf
                def _cap(*a, **k):
                    sep = k.get('sep',' '); end = k.get('end','\n')
                    buf.write(sep.join(str(x) for x in a) + end)
                _bi.print = _cap
                try:
                    from advak_lexer import AdvakLexer
                    from advak_parser import Parser as _P
                    tokens = AdvakLexer(codigo_str).tokenize()
                    ast    = _P(tokens).parse()
                    interp = AdvakInterpreter(ast)
                    loop   = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(interp.interpret())
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)
                    sys.stdout = old_out; _bi.print = old_print
                    out = buf.getvalue()
                    resultado_lista[0] = out if out.strip() else '✅ Executado sem saída'
                except RecursionError:
                    sys.stdout = old_out; _bi.print = old_print
                    resultado_lista[0] = '❌ Recursão muito profunda — adicione um caso base'
                except Exception as e:
                    sys.stdout = old_out; _bi.print = old_print
                    _tn = type(e).__name__
                    _tr = {'TypeError':'Tipo incompatível','ValueError':'Valor inválido',
                           'KeyError':'Chave não encontrada','IndexError':'Índice fora do alcance',
                           'FileNotFoundError':'Arquivo não encontrado','PermissionError':'Permissão negada',
                           'RecursionError':'Recursão muito profunda'}
                    resultado_lista[0] = f'❌ {_tr.get(_tn, _tn)}: {e}'

            t = threading.Thread(target=_run, daemon=True)
            t.start()

        g.declare('executar_em_thread', _executar_em_thread)

        def _executar_studio_popen(codigo_str, console_tk, status_tk, flag_lista,
                                  cor_verde='#3FB950', cor_cinza='#484F58'):
            """Execução via Popen nao-bloqueante - funciona no Windows.
            Usa subprocess.Popen() + root.after(100ms) para polling.
            """
            import subprocess, sys, os

            codigo_str = str(codigo_str)

            # Salvar codigo em arquivo temporario
            advak_dir  = os.path.dirname(os.path.abspath(__file__))
            # Usar caminho relativo ao advak_dir (funciona Windows/Linux)
            arq_temp   = '_studio_temp.dk'
            arq_temp_abs = os.path.join(advak_dir, arq_temp)
            try:
                with open(arq_temp_abs, 'w', encoding='utf-8') as _f:
                    _f.write(codigo_str)
            except Exception as e:
                try:
                    console_tk.configure(state='normal')
                    console_tk.insert('end', f'Erro ao salvar: {e}\n')
                    console_tk.configure(state='disabled')
                except Exception: pass
                try: flag_lista[0] = False
                except Exception: pass
                return

            env = dict(os.environ)
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8']       = '1'

            python_exe   = sys.executable
            advak_script = os.path.join(advak_dir, 'advak.py')

            try:
                proc = subprocess.Popen(
                    [python_exe, advak_script, arq_temp],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env, cwd=advak_dir
                )
            except Exception as e:
                try:
                    console_tk.configure(state='normal')
                    console_tk.insert('end', f'Erro ao iniciar: {e}\n')
                    console_tk.configure(state='disabled')
                except Exception: pass
                try: flag_lista[0] = False
                except Exception: pass
                return

            def _dec(b):
                if not b: return ''
                for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1'):
                    try: return b.decode(enc)
                    except: pass
                return b.decode('utf-8', errors='replace')

            def _mostrar(saida, erro_limpo):
                try:
                    console_tk.configure(state='normal')
                    if saida.strip():
                        console_tk.insert('end', saida)
                        if not saida.endswith('\n'):
                            console_tk.insert('end', '\n')
                    elif not erro_limpo:
                        console_tk.insert('end',
                            '\u2705 Executado sem saida impressa\n'
                            '   Dica: use imprimir() para ver resultados\n')
                    if erro_limpo:
                        console_tk.insert('end', '\u26a0\ufe0f ' + erro_limpo + '\n')
                    console_tk.insert('end', '\n\u2500\u2500 Conclu\u00eddo \u2500\u2500\n')
                    console_tk.see('end')
                    console_tk.configure(state='disabled')
                except Exception: pass
                try: status_tk.configure(text='\u2705 Pronto', fg='#3FB950')
                except Exception: pass
                try: flag_lista[0] = False
                except Exception: pass
                try: os.remove(arq_temp_abs)
                except Exception: pass

            def _verificar():
                if proc.poll() is None:
                    # Ainda rodando
                    try: console_tk.after(100, _verificar); return
                    except Exception: pass
                    try:
                        import advak_gui_modern as _agm
                        r = _agm._root_ref
                        if r: r.after(100, _verificar); return
                    except Exception: pass
                    proc.wait(timeout=15)

                saida = _dec(proc.stdout.read() if proc.stdout else b'')
                erro  = _dec(proc.stderr.read()  if proc.stderr else b'')
                linhas_erro = [l for l in erro.split('\n')
                               if l.strip() and
                               'DeprecationWarning' not in l and
                               'UserWarning' not in l and
                               'warnings.warn' not in l]
                _mostrar(saida, '\n'.join(linhas_erro).strip())

            # Agendar primeira verificacao via widget (mais confiavel no Windows)
            try:
                console_tk.after(100, _verificar)
            except Exception:
                try:
                    import advak_gui_modern as _agm
                    r = _agm._root_ref
                    if r: r.after(100, _verificar)
                except Exception: pass


        # ── dormir(segundos) — pausa assíncrona que libera o event loop ──
        async def _dormir(segundos):
            import asyncio
            await asyncio.sleep(float(segundos))
        g.declare('dormir', _dormir)

        # ── OS.popen() — Popen não-bloqueante como objeto ─────────────────

        def _executar_codigo_em_thread(codigo_str, console_tk, status_tk, flag_lista):
            """Executa código via subprocess em thread. Resultado em arquivo temporário.
            Thread escreve _studio_output.txt → studio.dk lê via Arquivo.ler()
            """
            import subprocess, sys, os, threading

            codigo_str = str(codigo_str)
            advak_dir  = os.path.dirname(os.path.abspath(__file__))
            arq_temp   = os.path.join(advak_dir, '_studio_temp.dk')
            arq_saida  = os.path.join(advak_dir, '_studio_output.txt')

            # Marcar como em execução
            try:
                with open(arq_saida, 'w', encoding='utf-8') as _f:
                    _f.write('__EXECUTANDO__')
            except Exception: pass

            # Salvar código
            try:
                with open(arq_temp, 'w', encoding='utf-8') as _f:
                    _f.write(codigo_str)
            except Exception as e:
                try:
                    with open(arq_saida, 'w', encoding='utf-8') as _f:
                        _f.write(f'❌ Erro ao salvar: {e}')
                except Exception: pass
                try: flag_lista[0] = False
                except Exception: pass
                return

            env = dict(os.environ)
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8']       = '1'

            def _dec(b):
                if not b: return ''
                for enc in ('utf-8', 'utf-8-sig', 'cp1252', 'latin-1'):
                    try: return b.decode(enc)
                    except: pass
                return b.decode('utf-8', errors='replace')

            def _rodar():
                try:
                    r = subprocess.run(
                        [sys.executable, os.path.join(advak_dir, 'advak.py'),
                         '_studio_temp.dk'],
                        capture_output=True, timeout=30, env=env, cwd=advak_dir
                    )
                    saida = _dec(r.stdout)
                    erro  = _dec(r.stderr)
                    linhas_e = [l for l in erro.split('\n')
                                if l.strip()
                                and 'DeprecationWarning' not in l
                                and 'UserWarning' not in l
                                and 'warnings.warn' not in l
                                and 'site-packages' not in l]
                    erro_limpo = '\n'.join(linhas_e).strip()
                    resultado = saida
                    if erro_limpo:
                        resultado += ('\n' if resultado else '') + '⚠️ ' + erro_limpo
                    if not resultado.strip():
                        resultado = '__SEM_SAIDA__'
                except subprocess.TimeoutExpired:
                    resultado = '⏱️ Tempo esgotado (30s)'
                except Exception as exc:
                    resultado = f'❌ Erro: {exc}'

                # Escrever resultado em arquivo (thread-safe, sem tkinter)
                try:
                    with open(arq_saida, 'w', encoding='utf-8') as _f:
                        _f.write(resultado)
                except Exception:
                    pass

                # Atualizar via after_idle (thread-safe no tkinter Windows/Linux)
                def _atualizar_direto():
                    try:
                        with open(arq_saida, 'r', encoding='utf-8') as _fr:
                            resultado2 = _fr.read()
                        try: os.remove(arq_saida)
                        except Exception: pass
                        try: os.remove(arq_temp)
                        except Exception: pass

                        console_tk.configure(state='normal')
                        if resultado2.strip() and resultado2 != '__SEM_SAIDA__':
                            console_tk.insert('end', resultado2)
                            if not resultado2.endswith('\n'):
                                console_tk.insert('end', '\n')
                        else:
                            console_tk.insert('end',
                                '\u2705 Executado sem sa\u00edda impressa\n'
                                '   Dica: use imprimir() para ver resultados\n')
                        console_tk.insert('end', '\n\u2500\u2500 Conclu\u00eddo \u2500\u2500\n')
                        console_tk.see('end')
                        console_tk.configure(state='disabled')
                    except Exception as _e:
                        try:
                            console_tk.configure(state='normal')
                            console_tk.insert('end', f'Erro ao mostrar: {_e}\n')
                            console_tk.configure(state='disabled')
                        except Exception: pass

                    try: status_tk.configure(text='\u2705 Pronto', fg='#3FB950')
                    except Exception: pass
                    try: flag_lista[0] = False
                    except Exception: pass

                # after_idle agenda na thread PRINCIPAL do tkinter — thread-safe!
                try:
                    import advak_gui_modern as _agm
                    root = _agm._root_ref
                    if root and root.winfo_exists():
                        root.after_idle(_atualizar_direto)
                    else:
                        _agm._gui_task_queue.put_nowait(_atualizar_direto)
                except Exception:
                    _atualizar_direto()

            threading.Thread(target=_rodar, daemon=True).start()

        def _mostrar_resultado_studio(console_tk, status_tk, flag_lista,
                                      arq_saida, arq_temp):
            """Lê resultado do arquivo e atualiza console. Thread-safe."""
            import os
            try:
                with open(arq_saida, 'r', encoding='utf-8') as _f:
                    resultado = _f.read()
                if resultado == '__EXECUTANDO__':
                    return  # ainda rodando
                os.remove(arq_saida)
            except Exception:
                return

            try:
                console_tk.configure(state='normal')
                if resultado == '__SEM_SAIDA__':
                    console_tk.insert('end',
                        '✅ Executado sem saída impressa\n'
                        '   Dica: use imprimir() para ver resultados\n')
                else:
                    console_tk.insert('end', resultado)
                    if not resultado.endswith('\n'):
                        console_tk.insert('end', '\n')
                console_tk.insert('end', '\n── Concluído ──\n')
                console_tk.see('end')
                console_tk.configure(state='disabled')
            except Exception: pass
            try: status_tk.configure(text='✅ Pronto', fg='#3FB950')
            except Exception: pass
            try: flag_lista[0] = False
            except Exception: pass
            try: os.remove(arq_temp)
            except Exception: pass

        g.declare('executar_codigo_em_thread', _executar_codigo_em_thread)
        g.declare('mostrar_resultado_studio', _mostrar_resultado_studio)

        g.declare('executar_codigo_em_thread', _executar_codigo_em_thread)


        g.declare('executar_studio', _executar_studio_popen)


        def _jan_after(widget_obj, ms, fn):
            """Agenda chamada de função fn após ms milissegundos no tkinter."""""
            ms_int = int(ms)
            try:
                # widget_obj é o widget tkinter da janela (jan)
                widget_obj.after(ms_int, lambda: fn() if callable(fn) else None)
            except Exception:
                pass

        g.declare('jan_after_fn', _jan_after)

        # ── Formatação de números ─────────────────────────────────────────
        def _moeda(valor, simbolo='R$', decimais=2, sep_milhar='.', sep_dec=','):
            """Formata número como moeda: moeda(1500.50) → 'R$ 1.500,50'"""
            try:
                v = float(valor)
                # Format with thousands separator
                partes = f"{abs(v):,.{decimais}f}".split('.')
                inteiro = partes[0].replace(',', sep_milhar)
                decimal = partes[1] if decimais > 0 else ''
                sinal = '-' if v < 0 else ''
                if decimais > 0:
                    return f"{sinal}{simbolo} {inteiro}{sep_dec}{decimal}"
                return f"{sinal}{simbolo} {inteiro}"
            except: return str(valor)

        def _porcentagem(valor, decimais=0):
            """Formata número como porcentagem: porcentagem(0.75) → '75%'"""
            try:
                v = float(valor)
                if 0.0 <= v <= 1.0:
                    v = v * 100
                if decimais == 0 and v == int(v):
                    return str(int(v)) + '%'
                return f"{v:.{decimais}f}".replace('.', ',') + '%'
            except: return str(valor)

        def _num_fmt(valor, decimais=2, sep_milhar='.', sep_dec=','):
            """Formata número: num_fmt(1234567.89) → '1.234.567,89'"""
            try:
                v = float(valor)
                partes = f"{abs(v):,.{decimais}f}".split('.')
                inteiro = partes[0].replace(',', sep_milhar)
                decimal = partes[1] if decimais > 0 else ''
                sinal = '-' if v < 0 else ''
                if decimais > 0:
                    return f"{sinal}{inteiro}{sep_dec}{decimal}"
                return f"{sinal}{inteiro}"
            except: return str(valor)

        def _num_abrev(valor):
            """Abrevia número grande: num_abrev(1500000) → '1,5M'"""
            try:
                v = float(valor)
                for unit, threshold in [('T',1e12),('Bi',1e9),('M',1e6),('K',1e3)]:
                    if abs(v) >= threshold:
                        n = v / threshold
                        fmt = f"{n:.1f}".rstrip('0').rstrip('.')
                        return f"{fmt}{unit}"
                return str(int(v)) if v == int(v) else str(round(v, 2))
            except: return str(valor)

        _MESES_PT = {
            'January':'janeiro','February':'fevereiro','March':'março',
            'April':'abril','May':'maio','June':'junho',
            'July':'julho','August':'agosto','September':'setembro',
            'October':'outubro','November':'novembro','December':'dezembro',
            'Jan':'jan','Feb':'fev','Mar':'mar','Apr':'abr','May':'mai',
            'Jun':'jun','Jul':'jul','Aug':'ago','Sep':'set','Oct':'out',
            'Nov':'nov','Dec':'dez',
        }
        def _formatar_data(data_str, formato_saida='%d/%m/%Y', formato_entrada=None):
            """Formata data: formatar_data('2024-12-25') → '25/12/2024'"""
            import datetime
            try:
                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y',
                            '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']
                if formato_entrada:
                    formatos = [formato_entrada] + formatos
                dt = None
                for fmt in formatos:
                    try:
                        dt = datetime.datetime.strptime(str(data_str), fmt)
                        break
                    except ValueError:
                        continue
                if dt is None:
                    return str(data_str)
                result = dt.strftime(formato_saida)
                # Translate month names to Portuguese
                for en, pt in _MESES_PT.items():
                    result = result.replace(en, pt)
                return result
            except: return str(data_str)

        def _data_agora(formato='%d/%m/%Y %H:%M'):
            """Retorna data/hora atual formatada"""
            import datetime
            return datetime.datetime.now().strftime(formato)

        def _data_hoje(formato='%d/%m/%Y'):
            """Retorna data de hoje formatada"""
            import datetime
            return datetime.date.today().strftime(formato)

        g.declare('moeda',         _moeda)
        g.declare('porcentagem',   _porcentagem)
        g.declare('num_fmt',       _num_fmt)
        g.declare('num_abrev',     _num_abrev)
        g.declare('formatar_data', _formatar_data)
        g.declare('data_agora',    _data_agora)
        g.declare('data_hoje',     _data_hoje)

        # ── Sistemas Ultra Avançados (Advak 5.0) ─────────────────────────────
        try:
            if _get_avancado():
                _interp_ref = self

                def _advak_callable(fn):
                    """Converte AdvakFunction em callable Python para sistemas avançados."""
                    if fn is None: return None
                    if isinstance(fn, AdvakFunction):
                        return lambda *args: _interp_ref._call_sync(fn, list(args))
                    if callable(fn): return fn
                    return fn

                def _wrap_stream_ops(stream_obj):
                    """Wraps stream functions to handle AdvakFunction args."""
                    if not isinstance(stream_obj, dict): return stream_obj

                    # Methods that take a fn arg and return a new stream
                    CHAIN_METHODS = ['map','filtrar','flat_map','distinct','take','skip','chunk','zip_com','ordenar']
                    # Methods that take a fn arg and return a terminal value
                    TERMINAL_FN   = ['reduzir','para_cada','existe','todos','min','max','agrupar']
                    # Methods that take no fn arg and return a stream
                    CHAIN_NO_FN   = ['distinct']
                    # Terminal methods that return values directly
                    TERMINAL_NOFN = ['coletar','contar','somar','primeiro','ultimo']

                    orig = dict(stream_obj)

                    def _make_chain(key):
                        def wrapper(*args):
                            # Convert any AdvakFunction args to Python callables
                            py_args = [_advak_callable(a) if callable(a) or hasattr(a, 'params') else a for a in args]
                            result = orig[key](*py_args)
                            if isinstance(result, dict) and ('_stream' in result or 'coletar' in result):
                                return _wrap_stream_ops(result)
                            return result
                        return wrapper

                    def _make_terminal(key):
                        def wrapper(*args):
                            py_args = [_advak_callable(a) if callable(a) or hasattr(a, 'params') else a for a in args]
                            return orig[key](*py_args)
                        return wrapper

                    for k in CHAIN_METHODS + TERMINAL_FN + TERMINAL_NOFN:
                        if k in stream_obj:
                            if k in TERMINAL_NOFN:
                                stream_obj[k] = _make_terminal(k)
                            else:
                                stream_obj[k] = _make_chain(k)

                    # wrap .de, .de_range, etc.
                    for k in ['de','de_range','de_texto','infinito','mesclar']:
                        if k in stream_obj:
                            orig_k = orig[k]
                            def _make_factory(fn):
                                def factory(*args):
                                    r = fn(*args)
                                    if isinstance(r, dict) and 'coletar' in r:
                                        return _wrap_stream_ops(r)
                                    return r
                                return factory
                            stream_obj[k] = _make_factory(orig_k)

                    return stream_obj

                _sistemas = _criar_avancado()

                # Inject safe caller into advak_advanced module
                import advak_advanced as _adv_mod
                def _safe_caller(fn, x):
                    if fn is None: return None
                    if isinstance(fn, AdvakFunction):
                        return _interp_ref._call_sync(fn, [x])
                    return fn(x)
                _adv_mod._ADVAK_FN_CALLER = _safe_caller

                # Fix canal to return values not property objects
                _canal_base = _sistemas['canal']
                _canal_criar_orig = _canal_base['criar']
                def _canal_criar_fixed(cap=0, nome='canal'):
                    c_raw = _canal_criar_orig(cap, nome)
                    _c_obj = c_raw.get('_canal')
                    # Create a proxy dict that updates dynamic properties
                    c = {
                        'enviar':        c_raw['enviar'],
                        'receber':       c_raw['receber'],
                        'receber_todos': c_raw['receber_todos'],
                        'fechar':        c_raw['fechar'],
                        # Property-like getters as callables
                        'tamanho':       lambda: _c_obj.tamanho,
                        'vazio':         lambda: _c_obj.vazio,
                        'esta_fechado':  lambda: _c_obj.esta_fechado,
                        '_canal':        _c_obj,
                    }
                    return c
                _canal_base['criar'] = _canal_criar_fixed

                # Fix eventos to properly call AdvakFunction listeners
                _ev_base = _sistemas['eventos']
                _ev_on_orig = _ev_base['on']
                _ev_once_orig = _ev_base['once']
                _ev_use_orig = _ev_base['use']
                _ev_base['on']   = lambda ev, fn, prio=0: _ev_on_orig(ev, _advak_callable(fn), prio)
                _ev_base['once'] = lambda ev, fn: _ev_once_orig(ev, _advak_callable(fn))
                _ev_base['use']  = lambda fn: _ev_use_orig(_advak_callable(fn))

                # Fix stream to handle AdvakFunction
                _stream_base = _wrap_stream_ops(_sistemas['stream'])

                # Fix deco to wrap AdvakFunction args
                _deco_base = _sistemas['deco']
                _deco_memo_orig = _deco_base['memoizar']
                _deco_log_orig  = _deco_base['com_log']
                _deco_med_orig  = _deco_base['medir_tempo']
                _deco_comp_orig = _deco_base['compor']
                _deco_pipe_orig = _deco_base['pipeline']
                _deco_base['memoizar']    = lambda fn, mx=128: _deco_memo_orig(_advak_callable(fn), mx)
                _deco_base['com_log']     = lambda fn, nome=None: _deco_log_orig(_advak_callable(fn), nome)
                _deco_base['medir_tempo'] = lambda fn, nome=None: _deco_med_orig(_advak_callable(fn), nome)
                _deco_base['compor']      = lambda *fns: _deco_comp_orig(*[_advak_callable(f) for f in fns])
                _deco_base['pipeline']    = lambda *fns: _deco_pipe_orig(*[_advak_callable(f) for f in fns])

                # Fix fsm callbacks
                _fsm_base = _sistemas['fsm']
                _fsm_criar_orig = _fsm_base['criar']
                def _fsm_criar_fixed(estado_inicial):
                    api = _fsm_criar_orig(estado_inicial)
                    _ao_entrar_orig = api['ao_entrar']
                    _ao_sair_orig   = api['ao_sair']
                    _ao_trans_orig  = api['ao_transicionar']
                    _trans_orig     = api['transicao']
                    api['ao_entrar']       = lambda est, fn: _ao_entrar_orig(est, _advak_callable(fn))
                    api['ao_sair']         = lambda est, fn: _ao_sair_orig(est, _advak_callable(fn))
                    api['ao_transicionar'] = lambda fn: _ao_trans_orig(_advak_callable(fn))
                    api['transicao']       = lambda de, ev, para, guarda=None, acao=None: _trans_orig(
                        de, ev, para,
                        _advak_callable(guarda) if guarda else None,
                        _advak_callable(acao) if acao else None
                    )
                    return api
                _fsm_base['criar'] = _fsm_criar_fixed
                _fsm_base['criar_fsm'] = _fsm_criar_fixed

                # Fix obs
                _obs_base = _sistemas['obs']
                _obs_de_orig = _obs_base['de']
                def _obs_de_fixed(fonte):
                    obs_api = _obs_de_orig(fonte)
                    def _wrap_obs(o):
                        _map_orig   = o['map']
                        _fil_orig   = o['filtrar']
                        _sub_orig   = o['subscribir']
                        o['map']     = lambda fn: _wrap_obs(_map_orig(_advak_callable(fn)))
                        o['filtrar'] = lambda fn: _wrap_obs(_fil_orig(_advak_callable(fn)))
                        o['subscribir'] = lambda proximo=None, erro=None, completo=None: _sub_orig(
                            _advak_callable(proximo) if proximo else None,
                            _advak_callable(erro) if erro else None,
                            _advak_callable(completo) if completo else None,
                        )
                        return o
                    return _wrap_obs(obs_api)
                _obs_base['de'] = _obs_de_fixed

                # Fix contrato
                _cont_base = _sistemas['contrato']
                _cont_orig = _cont_base['contratar']
                _cont_base['contratar'] = lambda fn, pre=None, pos=None, inv=None, nome=None: _cont_orig(
                    _advak_callable(fn),
                    _advak_callable(pre) if pre else None,
                    _advak_callable(pos) if pos else None,
                    _advak_callable(inv) if inv else None,
                    nome
                )

                g.declare('tipos',     _sistemas['tipos'])
                g.declare('canal',     _canal_base)
                g.declare('eventos',   _ev_base)
                g.declare('stream',    _stream_base)
                g.declare('deco',      _deco_base)
                g.declare('fsm',       _fsm_base)
                g.declare('obs',       _obs_base)
                g.declare('contrato',  _cont_base)
        except Exception as _e:
            import traceback; traceback.print_exc()
            pass  # sistemas avançados opcionais

        # ── Sistema Mobile (PWA, QR Code, UI Responsivo) ──────────────────────
        try:
            if _get_mobile():
                g.declare('mobile', _criar_mobile())
        except Exception:
            pass

        # ── Compilador Nativo ─────────────────────────────────────────────────
        try:
            if _get_nativo():
                g.declare('compilador', _criar_compilador_nativo())
        except Exception:
            pass

        # ── Sistema Embarcado (Serial, MQTT, GPIO, Firmware) ──────────────────
        try:
            if _get_embarcado():
                _emb = _criar_embarcado()
                # Inject safe caller so automacao can call AdvakFunctions from threads
                import advak_embarcado as _emb_mod
                def _emb_safe_call(fn, *args):
                    if isinstance(fn, AdvakFunction):
                        return _interp_ref._call_sync(fn, list(args))
                    if callable(fn): return fn(*args)
                    return None
                _emb_mod._ADVAK_CALL = _emb_safe_call

                # Wrap automacao.a_cada and .se to convert AdvakFunction callbacks
                _auto_criar_orig = _emb.get('automacao')
                if _auto_criar_orig:
                    def _auto_criar_wrapped():
                        api = _auto_criar_orig()
                        _a_cada_orig = api['a_cada']
                        _se_orig     = api['se']
                        def _wrap(fn):
                            if isinstance(fn, AdvakFunction):
                                return lambda *a: _interp_ref._call_sync(fn, list(a))
                            return fn
                        api['a_cada'] = lambda seg, fn, nome="": _a_cada_orig(seg, _wrap(fn), nome)
                        api['se']     = lambda cond, entao, nome="": _se_orig(_wrap(cond), _wrap(entao), nome)
                        return api
                    _emb['automacao'] = _auto_criar_wrapped

                # Wrap mqtt.subscrever callback
                _mqtt_orig = _emb.get('mqtt', {})
                if _mqtt_orig:
                    _mqtt_con_orig = _mqtt_orig.get('conectar')
                    if _mqtt_con_orig:
                        def _mqtt_con_wrapped(broker, porta=1883, usuario=None, senha=None, tls=False):
                            cli_api = _mqtt_con_orig(broker, porta, usuario, senha, tls)
                            _sub_orig = cli_api['subscrever']
                            def _sub_wrapped(topico, fn, qos=0):
                                py_fn = (lambda *a: _interp_ref._call_sync(fn, list(a))
                                         if isinstance(fn, AdvakFunction) else fn)
                                return _sub_orig(topico, py_fn, qos)
                            cli_api['subscrever'] = _sub_wrapped
                            return cli_api
                        _emb['mqtt']['conectar'] = _mqtt_con_wrapped

                # Wrap serial.ao_receber callback
                _ser_orig = _emb.get('serial', {})
                _ser_con_orig = _ser_orig.get('conectar') if _ser_orig else None
                if _ser_con_orig:
                    def _ser_con_wrapped(porta, baud=9600, timeout=1.0):
                        ser_api = _ser_con_orig(porta, baud, timeout)
                        _ao_rec_orig = ser_api['ao_receber']
                        def _ao_rec_wrapped(fn, ms=50):
                            py_fn = (lambda *a: _interp_ref._call_sync(fn, list(a))
                                     if isinstance(fn, AdvakFunction) else fn)
                            return _ao_rec_orig(py_fn, ms)
                        ser_api['ao_receber'] = _ao_rec_wrapped
                        return ser_api
                    _emb['serial']['conectar'] = _ser_con_wrapped

                g.declare('embarcado', _emb)
        except Exception:
            pass

    # ── Execução ──────────────────────────────────────────────────────────────

    async def interpret(self):
        # Injeta db e ai_key no scope global para callbacks da GUI
        if hasattr(self, 'db') and self.db:
            self.global_scope._db     = self.db
        if hasattr(self, 'ai_api_key') and self.ai_api_key:
            self.global_scope._ai_key = self.ai_api_key
        try:
            for node in self.ast:
                await self.exec_node(node, self.global_scope)
        except RecursionError:
            raise AdvakError(
                "Recursão muito profunda — a função chamou a si mesma vezes demais.\n"
                "   Adicione um caso base: se (n <= 0) { retornar resultado }")
        except MemoryError:
            raise AdvakError("Memória insuficiente — o programa usou memória demais.")

    async def exec_node(self, node, scope):
        if node is None: return None
        t = node.get('type', '')
        # Track current line for debugger and error messages
        _ln = node.get('line')
        if _ln: self._current_line = _ln

        if t == 'var_decl':
            v = await self.eval(node['value'], scope) if node['value'] else None
            tipo = node.get('tipo')
            if isinstance(tipo, dict):
                # seja x: inteiro = 5  → confere agora e em toda reatribuição
                nome = node['name']
                verificador = self._verificador_de_variavel(nome, tipo, scope)
                if node['value'] is not None:
                    verificador(v)
                else:
                    self._validar_anotacao(tipo, scope, f"variável '{nome}'")
                if scope.tipos is None:
                    scope.tipos = {}
                scope.tipos[nome] = verificador
            elif scope.tipos and node['name'] in scope.tipos:
                del scope.tipos[node['name']]            # seja x de novo, sem tipo: a anotação antiga cai
            scope.declare(node['name'], v)
            # BUG 11 FIX: fixo/const marks variable as immutable
            if node.get('const'):
                scope.vars[f"__const_{node['name']}"] = True

        elif t == 'func_decl':
            fn = AdvakFunction(node['name'], node['params'], node['body'],
                               scope, node.get('async', False), node.get('generator', False))
            fn.retorno = node.get('retorno')
            scope.declare(node['name'], fn)

        elif t == 'interface_decl':
            iface = {
                '__tipo__':    'interface',
                '__nome__':    node['nome'],
                '__membros__': node.get('membros', []),
                '__extends__': node.get('extends', []),
            }
            scope.declare(node['nome'], iface)
            return iface

        elif t == 'export_decl':
            if node['mode'] == 'inline':
                await self.exec_node(node['decl'], scope)
                # Mark exported name
                decl = node['decl']
                name = (decl.get('name') or decl.get('func_name') or
                        (decl.get('decl', {}) or {}).get('name'))
                if name:
                    if not hasattr(scope, '_exports'): scope._exports = set()
                    scope._exports.add(name)
            elif node['mode'] == 'list':
                if not hasattr(scope, '_exports'): scope._exports = set()
                for item in node['names']:
                    scope._exports.add(item['name'])
            return

        elif t == 'import_decl':
            await self._exec_import(node, scope)
            return

        elif t == 'class_decl':
            sup=scope.get(node['superclass']) if node['superclass'] else None
            methods={}; statics={}; getters={}; setters={}
            for m in node['methods']:
                fn=AdvakFunction(m['name'],m['params'],m['body'],scope,m.get('async',False))
                fn.retorno = m.get('retorno')
                if m.get('static'): statics[m['name']]=fn
                elif m.get('getter'): getters[m['name']]=fn
                elif m.get('setter'): setters[m['name']]=fn
                else: methods[m['name']]=fn
            klass=AdvakClass(node['name'],sup,methods,statics,getters,setters)
            for sn,sf in statics.items(): klass.fields[sn]=BoundMethod(klass,sf)
            scope.declare(node['name'], klass)

            # Valida interfaces declaradas com 'implementa'
            for iface_nome in node.get('interfaces', []):
                try:
                    iface = scope.get(iface_nome)
                    if isinstance(iface, dict) and iface.get('__tipo__') == 'interface':
                        faltando = [
                            m['nome'] for m in iface.get('__membros__', [])
                            if m['tipo'] == 'metodo'
                            and m['nome'] not in methods
                            and m['nome'] != 'construtor'
                        ]
                        if faltando:
                            raise AdvakError(
                                f"Classe '{node['name']}' não implementa os métodos "
                                f"da interface '{iface_nome}': {faltando}"
                            )
                except AdvakError:
                    raise
                except Exception:
                    pass

        elif t == 'print':
            vals = [await self.eval(a, scope) for a in node['args']]
            print(*[self._to_str(v) for v in vals])

        elif t == 'return':
            v = await self.eval(node['value'], scope) if node['value'] else None
            raise _ReturnSignal(v)

        elif t == 'break':    raise _BreakSignal()
        elif t == 'continue': raise _ContinueSignal()

        elif t == 'if':
            cond = await self.eval(node['cond'], scope)
            if self._truthy(cond):
                await self.exec_node(node['then'], Scope(scope))
            elif node['else']:
                await self.exec_node(node['else'], Scope(scope))

        elif t == 'while':
            while self._truthy(await self.eval(node['cond'], scope)):
                try:    await self.exec_node(node['body'], Scope(scope))
                except _BreakSignal:    break
                except _ContinueSignal: continue

        elif t == 'for':
            ls = Scope(scope)
            await self.exec_node(node['init'], ls)
            while self._truthy(await self.eval(node['cond'], ls)):
                try:    await self.exec_node(node['body'], Scope(ls))
                except _BreakSignal:    break
                except _ContinueSignal: pass
                await self.eval(node['step'], ls)

        elif t == 'for_in':
            iterable = await self._eval_iteravel(node['iterable'], scope)
            if isinstance(iterable, dict): iterable = list(iterable.keys())
            # Suporte a generators Advak
            if isinstance(iterable, AdvakGenerator):
                async for item in iterable:
                    inner = Scope(scope)
                    inner.declare(node['var'], item)
                    try:    await self.exec_node(node['body'], inner)
                    except _BreakSignal:    break
                    except _ContinueSignal: continue
            else:
                for item in (iterable or []):
                    inner = Scope(scope)
                    inner.declare(node['var'], item)
                    try:    await self.exec_node(node['body'], inner)
                    except _BreakSignal:    break
                    except _ContinueSignal: continue

        elif t == 'match':
            subj = await self.eval(node['subject'], scope)
            for case in node['cases']:
                if case['pattern'] is None:
                    # default case
                    case_scope = Scope(scope)
                    for s in case['body']:
                        await self.exec_node(s, case_scope)
                    break
                # Pattern matching avançado
                bindings = {}
                pat = case['pattern']
                if pat.get('ptype') == 'literal' and pat['value'].get('type') not in (
                        'number', 'float', 'string', 'bool', 'null', 'ident'):
                    # Expressão/condição: com combinar(verdadeiro) casa se for verdadeira;
                    # caso contrário compara por igualdade com o valor.
                    res = await self.eval(pat['value'], scope)
                    matched = self._truthy(res) if subj is True else (res == subj)
                else:
                    matched = self._match_pattern(pat, subj, bindings)
                if matched:
                    # Verifica guard
                    if case.get('guard'):
                        guard_scope = Scope(scope)
                        for k, v in bindings.items():
                            guard_scope.declare(k, v)
                        if not self._truthy(await self.eval(case['guard'], guard_scope)):
                            continue
                    case_scope = Scope(scope)
                    for k, v in bindings.items():
                        case_scope.declare(k, v)
                    try:
                        for s in case['body']:
                            await self.exec_node(s, case_scope)
                    except _ReturnSignal as _ret:
                        # => syntax generates a 'return' node — treat as expression result
                        # Only re-raise if we're inside a function (propagate normally)
                        # For match at statement level, just use the value
                        pass
                    break

        elif t == 'destructure_obj':
            val = await self.eval(node['value'], scope)
            for field in node['fields']:
                if isinstance(val, dict):
                    fv = val.get(field['key'])
                elif isinstance(val, AdvakInstance):
                    try: fv = val.get(field['key'])
                    except: fv = None
                else:
                    fv = None
                if fv is None and field.get('default') is not None:
                    fv = await self.eval(field['default'], scope)
                scope.declare(field['alias'], fv)

        elif t == 'destructure_arr':
            val = await self.eval(node['value'], scope)
            if not isinstance(val, list):
                raise AdvakError(f"Desestruturação de lista requer uma lista, recebeu {_tipo_pt(val)}")
            for i, item in enumerate(node.get('items') or []):
                if item is None: continue
                fv = val[i] if i < len(val) else None
                if fv is None and item.get('default') is not None:
                    fv = await self.eval(item['default'], scope)
                scope.declare(item['name'], fv)
            if node.get('rest'):
                rest_start = len(node.get('items') or [])
                scope.declare(node['rest'], val[rest_start:])

        elif t == 'yield':
            raise _YieldSignal(await self.eval(node['value'], scope) if node['value'] else None)

        elif t == 'prolog_fact':
            args = []
            for a in node['args']:
                args.append(await self.eval(a, scope))
            self.prolog_db.add_fact(node['predicate'], args)

        elif t == 'prolog_rule':
            # Resolve apenas os átomos literais do head; variáveis ficam como strings
            head_args = []
            for a in node['head']['args']:
                if a['pterm'] == 'var':
                    head_args.append(a['name'])  # variável Prolog (string maiúscula)
                elif a['pterm'] == 'atom':
                    head_args.append(a['value'])
                else:
                    head_args.append(await self.eval(a['expr'], scope))
            # Body goals
            body_goals = []
            for g in node['body']:
                g_args = []
                for a in g['args']:
                    if a['pterm'] == 'var':
                        g_args.append(a['name'])
                    elif a['pterm'] == 'atom':
                        g_args.append(a['value'])
                    else:
                        g_args.append(await self.eval(a['expr'], scope))
                body_goals.append({'predicate': g['predicate'], 'args': g_args})
            self.prolog_db.add_rule(node['head']['predicate'], head_args, body_goals)

        elif t == 'prolog_query':
            args = []
            for a in node['args']:
                if a['pterm'] == 'var':
                    args.append(a['name'])
                elif a['pterm'] == 'atom':
                    args.append(a['value'])
                else:
                    args.append(await self.eval(a['expr'], scope))
            results = self.prolog_db.query(node['predicate'], args)
            # Injeta variáveis da primeira solução no escopo (como Prolog)
            if results:
                for k, v in results[0].items():
                    if k[0].isupper():
                        scope.declare(k, v)
            # Também salva todas as soluções em _solucoes/_solutions
            scope.declare('_solucoes', results)
            scope.declare('_solutions', results)

        # ── C/C++ — Struct ────────────────────────────────────────────────
        elif t == 'struct_decl':
            struct_type = AdvakStructType(node['name'], node['fields'])
            interp = self

            async def _make_struct_constructor(st):
                """Retorna função construtora da struct."""
                async def _ctor(*args, **kwargs):
                    values = {}
                    for i, field in enumerate(st.fields):
                        fname = field['name']
                        if fname in kwargs:
                            values[fname] = kwargs[fname]
                        elif i < len(args):
                            values[fname] = args[i]
                        elif field.get('default') is not None:
                            values[fname] = await interp.eval(field['default'], scope)
                        else:
                            values[fname] = None
                    return AdvakStructInstance(st, values)
                return _ctor

            ctor = await _make_struct_constructor(struct_type)
            # Registra o tipo E o construtor no escopo
            scope.declare(node['name'], ctor)
            scope.declare(f"_struct_{node['name']}", struct_type)
            # Também registra método ::novo / ::criar
            struct_type._ctor = ctor

        # ── C/C++ — Enum ──────────────────────────────────────────────────
        elif t == 'enum_decl':
            # Avalia valores das variantes
            evaluated_variants = []
            for v in node['variants']:
                val = await self.eval(v['value'], scope) if v['value'] else 0
                evaluated_variants.append({
                    'name': v['name'], 'value': val, 'payload': v['payload']
                })
            enum_type = AdvakEnumType(node['name'], evaluated_variants)
            scope.declare(node['name'], enum_type)

        # ── C/C++ — Macro ─────────────────────────────────────────────────
        elif t == 'macro_decl':
            macro = AdvakMacro(node['name'], node['params'], node['body'], scope)
            # Macro sem parâmetros → avalia imediatamente como constante
            if not node['params']:
                val = await self.eval(node['body'], scope)
                scope.declare(node['name'], val)
            else:
                # Macro com parâmetros → registra como função inline
                interp = self
                macro_node = node
                macro_scope = scope

                async def _macro_fn(*args, _m=macro_node, _s=macro_scope):
                    inner = Scope(_s)
                    for pname, pval in zip(_m['params'], args):
                        inner.declare(pname, pval)
                    return await interp.eval(_m['body'], inner)

                scope.declare(node['name'], _macro_fn)

        # ── C/C++ — Ref ───────────────────────────────────────────────────
        elif t == 'ref_decl':
            target_node = node['target']
            if target_node.get('type') == 'ident':
                ref = AdvakRef(target_node['name'], scope)
            else:
                val = await self.eval(target_node, scope)
                scope.declare(f"_ref_{node['name']}_slot", val)
                ref = AdvakRef(f"_ref_{node['name']}_slot", scope)
            scope.declare(node['name'], ref)

        # ── Haskell — Tipo Algébrico (ADT) ───────────────────────────────
        elif t == 'adt_decl':
            adt = AdvakADTType(node['name'], node['variants'], node.get('type_params', []))
            scope.declare(node['name'], adt)
            for vname, v in adt.variants.items():
                if v['fields']:
                    _adt = adt; _vname = vname; _fields = v['fields']
                    def _make_ctor(a, vn, fs):
                        def _ctor(*args):
                            if len(args) != len(fs):
                                raise AdvakError(f"{a.name}::{vn} espera {len(fs)} argumento(s)")
                            return AdvakADTVariant(a, vn, list(args))
                        return _ctor
                    scope.declare(vname, _make_ctor(_adt, _vname, _fields))
                else:
                    scope.declare(vname, AdvakADTVariant(adt, vname, []))

        # ── Haskell — Congelar / Imutabilidade ───────────────────────────
        elif t == 'freeze_stmt':
            target = node['target']
            if target.get('type') == 'ident':
                val = scope.get(target['name'])
                frozen = _deep_freeze(val)
                scope.set(target['name'], frozen)

        elif t == 'immutable_decl':
            val = await self.eval(node['value'], scope)
            frozen = _deep_freeze(val)
            scope.declare(node['name'], frozen)
            scope.vars[f"__const_{node['name']}"] = True

        elif t == 'immutable_obj_decl':
            val = await self.eval(node['value'], scope)
            for field in node['fields']:
                if isinstance(val, (dict, FrozenMap)):
                    fv = val.get(field['key']) if isinstance(val, dict) else val.get(field['key'])
                else:
                    fv = None
                frozen = _deep_freeze(fv)
                scope.declare(field['alias'], frozen)
                scope.vars[f"__const_{field['alias']}"] = True

        elif t == 'try':
            try:
                await self.exec_node(node['body'], Scope(scope))
            except (AdvakError, Exception) as e:
                if node['catch_body']:
                    inner = Scope(scope)
                    inner.declare(node['catch_var'] or 'e', str(e))
                    await self.exec_node(node['catch_body'], inner)
            finally:
                if node['finally_body']:
                    await self.exec_node(node['finally_body'], Scope(scope))

        elif t == 'throw':
            raise AdvakError(str(await self.eval(node['value'], scope)))

        elif t == 'block':
            block_scope = Scope(scope)
            for s in node['body']: await self.exec_node(s, block_scope)

        elif t == 'expr_stmt':
            await self.eval(node['expr'], scope)

        else:
            await self.eval(node, scope)

    # ── Avaliação ─────────────────────────────────────────────────────────────

    async def eval(self, node, scope):
        if node is None: return None
        t = node.get('type', '')

        if t == 'number':  return node['value']
        if t == 'float':   return node['value']
        if t == 'bool':    return node['value']
        if t == 'null':    return None
        if t == 'string':  return node['value']
        if t == 'template_string':
            return await self._interp_template(node['value'], scope)

        if t == 'ident':
            name = node['name']
            # Palavras-chave que podem aparecer como ident por erro de encoding
            if name in ('senão', 'senao', 'então', 'entao'):
                return None
            return scope.get(name)

        if t == 'list':
            res = []
            for item in node['items']:
                if item.get('type') == 'spread':
                    res.extend(await self.eval(item['value'], scope))
                else:
                    res.append(await self.eval(item, scope))
            return res

        if t == 'map':
            d = {}
            for pair in node['pairs']:
                if pair.get('spread'):
                    spread_val = await self.eval(pair['value'], scope)
                    if isinstance(spread_val, dict):
                        d.update(spread_val)
                    continue
                d[pair['key']] = await self.eval(pair['value'], scope)
            return d

        if t == 'lambda':
            fn = AdvakFunction(node.get('name'), node['params'],
                               node['body'], scope, node.get('async', False),
                               node.get('generator', False))
            fn.retorno = node.get('retorno')
            return fn

        if t == 'await':
            val = await self.eval(node['value'], scope)
            if asyncio.iscoroutine(val): return await val
            if asyncio.isfuture(val):   return await val
            return val  # synchronous value — just return it

        if t == 'assign':
            val = await self.eval(node['value'], scope)
            return await self._do_assign(node['target'], node['op'], val, scope)

        if t == 'binop':
            l = await self.eval(node['left'],  scope)
            r = await self.eval(node['right'], scope)
            return self._binop(l, node['op'], r)

        if t == 'unary':
            op = node['op']
            v  = await self.eval(node['operand'], scope)
            if op in ('!', 'nao', 'not'): return not self._truthy(v)
            if op == '-':  return -v
            if op == '+':  return +v
            if op == '~':  return ~int(v)   # bitwise NOT
            return v  # fallback: return value unchanged

        if t == 'typeof':
            # BUG 8 FIX: tipo(x) → returns PT-BR type name
            try:
                v = await self.eval(node['expr'], scope)
            except:
                return 'indefinido'
            if v is None:          return 'nulo'
            if isinstance(v, bool):return 'booleano'
            if isinstance(v, int): return 'numero'
            if isinstance(v, float):return 'numero'
            if isinstance(v, str): return 'texto'
            if isinstance(v, list):return 'lista'
            if isinstance(v, dict):return 'objeto'
            if callable(v) or hasattr(v, 'params'): return 'funcao'
            return 'objeto'

        if t == 'null_coalesce':
            l = await self.eval(node['left'], scope)
            return l if l is not None else await self.eval(node['right'], scope)

        if t == 'list_comp':
            saida = []
            await self._comp_rec(node, 0, Scope(scope), saida)
            return saida

        if t == 'range':
            # Fora de um laço o intervalo vira uma lista (com teto de tamanho)
            r = await self._eval_intervalo(node, scope)
            if len(r) > self._MAX_INTERVALO:
                raise AdvakError(f"Intervalo grande demais para virar lista ({len(r)} itens; limite "
                                 f"{self._MAX_INTERVALO}). Use-o direto em um laço: para (i em {r.start}..{r.stop}) {{ }}.")
            return list(r)

        if t == 'ternary':
            c = await self.eval(node['cond'], scope)
            return await self.eval(node['then'] if self._truthy(c) else node['else'], scope)

        if t == 'call':     return await self._eval_call(node, scope)
        if t == 'builtin_call': return await self._eval_builtin(node['name'], node['args'], scope)

        if t == 'member':
            obj  = await self.eval(node['obj'], scope)
            prop = node['prop']
            if isinstance(obj, AdvakInstance):
                k = obj.klass
                while k:
                    if prop in k.getters:
                        return await self._call_fn(k.getters[prop], [], scope, this=obj)
                    k = k.superclass
            return self._get_member(obj, prop)

        if t == 'optional_member':
            obj = await self.eval(node['obj'], scope)
            if obj is None: return None
            prop = node['prop']
            if isinstance(obj, AdvakInstance):
                k = obj.klass
                while k:
                    if prop in k.getters:
                        return await self._call_fn(k.getters[prop], [], scope, this=obj)
                    k = k.superclass
            return self._get_member(obj, prop)

        if t == 'index':
            obj = await self.eval(node['obj'],   scope)
            idx = await self.eval(node['index'], scope)
            # Converte idx para int de forma segura
            if isinstance(obj, (list, str, FrozenList)):
                try:
                    i = int(idx)
                    if i >= len(obj) or i < -len(obj):
                        raise AdvakError(f"Índice {i} fora do alcance (tamanho: {len(obj)})")
                    return obj[i]
                except (TypeError, ValueError):
                    # idx não é número (ex: widget tkinter) — retorna None
                    return None
            if isinstance(obj, dict):        return obj.get(idx)
            if isinstance(obj, FrozenMap):   return obj.get(idx)
            # Para outros tipos, tenta acessar via get ou index
            if hasattr(obj, '__getitem__'):
                try:
                    return obj[idx]
                except Exception:
                    return None
            raise AdvakError(f"Não é possível usar índice em {_tipo_pt(obj)}")

        if t == 'await':
            v = await self.eval(node['expr'], scope)
            return await v if asyncio.iscoroutine(v) else v

        # ── C/C++ deref como expressão: deref ptr ─────────────────────────
        if t == 'deref':
            v = await self.eval(node['expr'], scope)
            if isinstance(v, AdvakRef): return v.valor
            return v

        if t == 'instanceof':
            obj = await self.eval(node['obj'], scope)
            try: klass = scope.get(node['class'])
            except: return False
            if isinstance(obj, AdvakInstance):
                k = obj.klass
                while k:
                    if k is klass or k.name == node['class']: return True
                    k = k.superclass
            return False

        if t == 'new':
            klass = scope.get(node['class'])
            if not isinstance(klass, AdvakClass):
                raise AdvakError(f"'{node['class']}' não é uma classe")
            inst = AdvakInstance(klass)
            _k = klass
            while _k:
                _found = next((c for c in ('construtor', 'constructor', 'início', 'inicio', '__init__')
                               if c in _k.methods), None)
                if _found:
                    args = [await self.eval(a, scope) for a in node['args']]
                    await self._call_fn(_k.methods[_found], args, scope, this=inst, owner_class=_k)
                    break
                _k = getattr(_k, 'superclass', None)
            return inst

        try:
            await self.exec_node(node, scope)
        except _ReturnSignal as r:
            return r.value
        return None

    async def _eval_call(self, node, scope):
        fn      = await self.eval(node['func'], scope)
        pos_args= []
        kw_args = {}

        for a in node['args']:
            # Arg nomeado: lado="left", preencher="x", etc.
            if isinstance(a, dict) and a.get('type') == 'assign' and                isinstance(a.get('target'), dict) and a['target'].get('type') == 'ident':
                nome  = a['target']['name']
                valor = await self.eval(a['value'], scope)
                kw_args[nome] = valor
            elif isinstance(a, dict) and a.get('type') == 'spread':
                # Spread: f(...args) → expande lista em argumentos posicionais
                val = await self.eval(a['value'], scope)
                if isinstance(val, (list, tuple)):
                    pos_args.extend(val)
                else:
                    pos_args.append(val)
            else:
                pos_args.append(await self.eval(a, scope))

        args = pos_args  # compatibilidade com código existente

        # lista.primeiro() / lista.ultimo(): propriedades chamadas com ()
        if (isinstance(node['func'], dict) and node['func'].get('type') == 'member'
                and node['func'].get('prop') in ('primeiro', 'ultimo') and not callable(fn)
                and not pos_args):
            return fn

        # Query/Update/Delete builders — encadeia métodos
        if isinstance(fn, (QueryBuilder, UpdateBuilder, DeleteBuilder)):
            return fn

        if isinstance(fn, BoundMethod):
            # Use _super_owner tag if present (set by _SuperProxy.get)
            if hasattr(fn, '_super_owner'):
                _ow = fn._super_owner
            else:
                _ow=None
                if isinstance(fn.instance, AdvakInstance):
                    _kk=fn.instance.klass
                    while _kk:
                        if any(m is fn.func for m in _kk.methods.values()): _ow=_kk; break
                        _kk=_kk.superclass
            return await self._call_fn(fn.func, pos_args, scope, this=fn.instance, kwargs=kw_args, owner_class=_ow)

        if isinstance(fn, AdvakFunction):
            return await self._call_fn(fn, pos_args, scope, kwargs=kw_args)

        # super() call — detect _SuperProxy or _SuperCallMarker
        if hasattr(fn, '_klass') and hasattr(fn, '_instance') and callable(fn):
            # _SuperProxy called directly: super(args...) → constructor
            _sup_klass = fn._klass; _sup_inst = fn._instance
            for _cn in ('início', 'inicio', 'construtor', 'constructor', '__init__'):
                if _cn in _sup_klass.methods:
                    return await self._call_fn(_sup_klass.methods[_cn], pos_args,
                        scope, this=_sup_inst, owner_class=_sup_klass)
            return None
        if hasattr(fn, 'klass') and hasattr(fn, 'instance') and hasattr(fn, 'args') and type(fn).__name__ == '_SuperCallMarker':
            for _cn in ('início', 'inicio', 'construtor', 'constructor', '__init__'):
                if _cn in fn.klass.methods:
                    return await self._call_fn(fn.klass.methods[_cn], fn.args,
                        scope, this=fn.instance, owner_class=fn.klass)
            return None

        # Instanciação de classe: Animal("x") equivale a novo Animal("x")
        if isinstance(fn, AdvakClass):
            inst = AdvakInstance(fn)
            # Search constructor in class and superclass chain
            klass = fn
            while klass:
                for cname in ('início', 'inicio', 'construtor', 'constructor', '__init__'):
                    if cname in klass.methods:
                        await self._call_fn(klass.methods[cname], pos_args, scope,
                                            this=inst, kwargs=kw_args, owner_class=fn)
                        klass = None  # found — stop searching
                        break
                else:
                    klass = getattr(klass, 'superclass', None)
                    continue
                break
            return inst

        if callable(fn):
            r = fn(*pos_args, **kw_args)
            return await r if asyncio.iscoroutine(r) else r

        raise AdvakError(
                f"'{fn}' não é uma função — verifique se declarou a função com 'funcao nome() {{ }}'" +
                (f" (linha {self._current_line})" if hasattr(self, '_current_line') and self._current_line else ""))

    async def _call_fn(self, fn, args, caller_scope, this=None, kwargs=None, owner_class=None):
        inner = Scope(fn.closure)
        if this:
            inner.declare('isso', this)
            inner.declare('this', this)
            if isinstance(this, AdvakInstance):
                oc = owner_class
                if oc is None:
                    _k = this.klass
                    while _k:
                        if any(m is fn for m in _k.methods.values()): oc=_k; break
                        _k = _k.superclass
                _sup = oc.superclass if (oc and oc.superclass) else None
                if not _sup:
                    # No superclass — clear 'super' to prevent closure leakage
                    inner.declare('super', None)
                    inner.declare('Super', None)
                if _sup:
                    _ir=self; _sc=_sup; _this_ref=this; _inner_ref=inner

                    # super() call marker (resolved asynchronously in _eval_call)
                    class _SuperCallMarker:
                        def __init__(self_m, klass, instance, args, interp, scope):
                            self_m.klass=klass; self_m.instance=instance
                            self_m.args=args; self_m.interp=interp; self_m.scope=scope

                    # super object — supports both super() and super.metodo()
                    class _SuperProxy:
                        def __init__(self_p, klass, instance, interp, scope):
                            self_p._klass    = klass
                            self_p._instance = instance
                            self_p._interp   = interp
                            self_p._scope    = scope

                        def __call__(self_p, *a):
                            # Returns a special marker — actual execution via _eval_call
                            return _SuperCallMarker(self_p._klass, self_p._instance, list(a), self_p._interp, self_p._scope)

                        def get(self_p, name):
                            # super.metodo → looks up method in superclass chain
                            k = self_p._klass
                            while k:
                                if name in k.methods:
                                    fn   = k.methods[name]
                                    inst = self_p._instance
                                    # BoundMethod(instance, func) — correct order
                                    bm = BoundMethod(inst, fn)
                                    # Tag the BoundMethod with the owner class
                                    # so _call_fn uses correct super chain
                                    bm._super_owner = k
                                    return bm
                                k = k.superclass
                            return None

                    _super_obj = _SuperProxy(_sc, this, self, inner)
                    inner.declare('super', _super_obj)
                    inner.declare('Super', _super_obj)
        kw = kwargs or {}
        for i, param in enumerate(fn.params):
            pname = param.get('name')
            # ── Destructuring param ──────────────────────────────────────
            if param.get('destructure') == 'object':
                val = args[i] if i < len(args) else {}
                if val is None: val = {}
                for field in param['fields']:
                    if isinstance(val, dict):
                        fv = val.get(field['key'])
                    elif isinstance(val, AdvakInstance):
                        try: fv = val.get(field['key'])
                        except: fv = None
                    else:
                        fv = None
                    if fv is None and field.get('default') is not None:
                        fv = await self.eval(field['default'], caller_scope)
                    inner.declare(field['alias'], fv)
                continue
            if param.get('destructure') == 'array':
                val = args[i] if i < len(args) else []
                if not isinstance(val, list): val = []
                for j, item in enumerate(param.get('items') or []):
                    if item is None: continue
                    fv = val[j] if j < len(val) else None
                    if fv is None and item.get('default') is not None:
                        fv = await self.eval(item['default'], caller_scope)
                    inner.declare(item['name'], fv)
                if param.get('rest'):
                    inner.declare(param['rest'], val[len(param.get('items') or []):])
                continue
            # ── Normal param ─────────────────────────────────────────────
            if param.get('spread'):
                inner.declare(pname, list(args[i:]))
                break
            if pname in kw:
                inner.declare(pname, kw[pname])
            elif i < len(args):
                inner.declare(pname, args[i])
            elif param.get('default') is not None:
                inner.declare(pname, await self.eval(param['default'], caller_scope))
            else:
                inner.declare(pname, None)
            if param.get('tipo'):                       # a: numero  → confere o valor recebido
                self._conferir_parametro(fn, pname, inner.vars[pname], param['tipo'], fn.closure)

        # ── Generator function ────────────────────────────────────────────
        if fn.is_generator:
            interp = self
            body   = fn.body
            _inner = inner

            async def _advak_gen():
                """Async generator: executa corpo e coleta yields."""
                collected = []
                try:
                    await interp._collect_yields(body, _inner, collected, max_yields=10000)
                except (_ReturnSignal, _BreakSignal):
                    pass
                for v in collected:
                    yield v

            return AdvakGenerator(_advak_gen())

        retornou = False
        try:
            await self.exec_node(fn.body, inner)
            valor = None
        except _ReturnSignal as r:
            valor, retornou = r.value, True
        if fn.retorno is not None:                      # -> numero  → confere o valor devolvido
            self._conferir_retorno(fn, valor, retornou, fn.closure)
        return valor

    async def _collect_yields(self, body, scope, collected, max_yields=10000):
        """
        Executa um corpo de gerador coletando todos os valores produzidos por 'produzir/yield'.
        Suporta: while, for, if, blocos, e qualquer stmt.
        Respeita max_yields para evitar loops infinitos.
        """
        if len(collected) >= max_yields:
            return

        t = body.get('type', '')

        if t == 'block':
            for stmt in body['body']:
                if len(collected) >= max_yields: return
                await self._collect_yields(stmt, scope, collected, max_yields)
            return

        if t == 'yield':
            val = await self.eval(body['value'], scope) if body.get('value') else None
            collected.append(val)
            return

        if t == 'if':
            cond = await self.eval(body['cond'], scope)
            if self._truthy(cond):
                await self._collect_yields(body['then'], scope, collected, max_yields)
            elif body.get('else'):
                await self._collect_yields(body['else'], scope, collected, max_yields)
            return

        if t == 'while':
            iters = 0
            while self._truthy(await self.eval(body['cond'], scope)):
                iters += 1
                if iters > max_yields or len(collected) >= max_yields:
                    break
                inner = Scope(scope)
                try:
                    await self._collect_yields(body['body'], inner, collected, max_yields)
                except _BreakSignal:
                    break
                except _ContinueSignal:
                    continue
            return

        if t == 'for_in':
            iterable = await self._eval_iteravel(body['iterable'], scope)
            if isinstance(iterable, dict): iterable = list(iterable.keys())
            if isinstance(iterable, AdvakGenerator):
                async for item in iterable:
                    if len(collected) >= max_yields: break
                    inner = Scope(scope)
                    inner.declare(body['var'], item)
                    try:
                        await self._collect_yields(body['body'], inner, collected, max_yields)
                    except _BreakSignal: break
                    except _ContinueSignal: continue
            else:
                for item in (iterable or []):
                    if len(collected) >= max_yields: break
                    inner = Scope(scope)
                    inner.declare(body['var'], item)
                    try:
                        await self._collect_yields(body['body'], inner, collected, max_yields)
                    except _BreakSignal: break
                    except _ContinueSignal: continue
            return

        if t == 'var_decl':
            val = await self.eval(body.get('value'), scope) if body.get('value') else None
            scope.declare(body['name'], val)
            return

        if t == 'expr_stmt':
            await self.eval(body['expr'], scope)
            return

        if t in ('break',): raise _BreakSignal()
        if t in ('continue',): raise _ContinueSignal()
        if t in ('return',):
            v = await self.eval(body['value'], scope) if body.get('value') else None
            raise _ReturnSignal(v)

        # Fallback — tenta exec_node (captura yields via _YieldSignal)
        try:
            await self.exec_node(body, scope)
        except _YieldSignal as ys:
            collected.append(ys.value)

    async def _exec_generator(self, body, scope, queue):
        """Legacy — mantido por compatibilidade. Usa _collect_yields internamente."""
        collected = []
        await self._collect_yields(body, scope, collected)
        for v in collected:
            await queue.put(v)

    async def _eval_builtin(self, name, arg_nodes, scope):
        args = [await self.eval(a, scope) for a in arg_nodes]

        if name == 'ai_perguntar':
            return await self._ai_call(str(args[0]) if args else '', usar_contexto=True)
        if name == 'ai_classificar':
            t = str(args[0]) if args else ''
            cats = args[1] if len(args)>1 else []
            return await self._ai_call(t,
                system=f"Classifique em UMA categoria: {cats}. Responda APENAS a categoria.")
        if name == 'ai_transformar':
            d = str(args[0]) if args else ''
            i = str(args[1]) if len(args)>1 else 'Melhore'
            return await self._ai_call(f"{i}:\n\n{d}")
        if name == 'ai_resumir':
            return await self._ai_call(str(args[0]) if args else '',
                system="Resuma em português de forma concisa.")
        if name == 'ai_gerar':
            return await self._ai_call(str(args[0]) if args else '',
                system="Você é criativo. Responda em português.")
        # English AI aliases
        if name == 'ai_ask':
            return await self._ai_call(str(args[0]) if args else '')
        if name == 'ai_classify':
            t = str(args[0]) if args else ''
            cats = args[1] if len(args)>1 else []
            return await self._ai_call(t,
                system=f"Classify into ONE category: {cats}. Reply ONLY the category.")
        if name == 'ai_transform':
            d = str(args[0]) if args else ''
            i = str(args[1]) if len(args)>1 else 'Improve'
            return await self._ai_call(f"{i}:\n\n{d}")
        if name == 'ai_summarize':
            return await self._ai_call(str(args[0]) if args else '',
                system="Summarize this text concisely.")
        if name == 'ai_generate':
            return await self._ai_call(str(args[0]) if args else '',
                system="You are a creative assistant. Generate content.")

        if name in ('imprimir', 'print'):
            print(*[self._to_str(a) for a in args]); return None
        if name in ('entrada', 'input'):
            return input(str(args[0]) if args else '')

        raise AdvakError(f"Função embutida '{name}' não reconhecida")


    async def _exec_import(self, node, scope):
        """Execute an import_decl node."""
        source = node['source']

        # ── Standard library modules ──────────────────────────────────────
        std_modules = {
            'std:math': {
                'PI':       __import__('math').pi,
                'pi':       __import__('math').pi,
                'E':        __import__('math').e,
                'e':        __import__('math').e,
                'sen':      __import__('math').sin,
                'cos':      __import__('math').cos,
                'tan':      __import__('math').tan,
                'raiz':     __import__('math').sqrt,
                'sqrt':     __import__('math').sqrt,
                'abs':      abs,
                'piso':     __import__('math').floor,
                'teto':     __import__('math').ceil,
                'arred':    round,
                'log':      __import__('math').log,
                'log10':    __import__('math').log10,
                'pow':      __import__('math').pow,
                'aleatorio':__import__('random').random,
                'inteiro_aleatorio': __import__('random').randint,
            },
            'std:texto': {
                'formatar':   lambda tmpl, *a: tmpl.format(*a),
                'repetir':    lambda s, n: s * n,
                'inverter':   lambda s: s[::-1],
                'palindromo': lambda s: s == s[::-1],
                'contar':     lambda s, sub: s.count(sub),
                'substituir': lambda s, a, b: s.replace(a, b),
                'dividir':    lambda s, sep='': s.split(sep) if sep else list(s),
                'unir':       lambda lst, sep='': sep.join(str(x) for x in lst),
                'maiusculo':  lambda s: s.upper(),
                'minusculo':  lambda s: s.lower(),
                'titulo':     lambda s: s.title(),
                'remover_espacos': lambda s: s.strip(),
                'começa_com': lambda s, p: s.startswith(p),
                'termina_com':lambda s, p: s.endswith(p),
                'contem':     lambda s, p: p in s,
            },
            'std:lista': {
                'intervalo':  lambda a, b=None, s=1: list(range(int(a), int(b), int(s))) if b is not None else list(range(int(a))),
                'ordenar':    lambda lst, rev=False: sorted(lst, reverse=rev),
                'filtrar':    lambda lst, fn: [x for x in lst if self._call_sync(fn, [x])],
                'mapear':     lambda lst, fn: [self._call_sync_vargs(fn, x, i) for i, x in enumerate(lst)],
                'reduzir':    lambda lst, fn, ini=None: (lambda: [ini := self._call_sync(fn, [ini, x]) for x in lst] and ini)() if ini is not None else (lambda: [r := lst[0]] or [r := self._call_sync(fn, [r, x]) for x in lst[1:]] and r)(),
                'unico':      lambda lst: list(dict.fromkeys(lst)),
                'achatar':    lambda lst: [x for sub in lst for x in (sub if isinstance(sub, list) else [sub])],
                'primeiro':   lambda lst: lst[0] if lst else None,
                'ultimo':     lambda lst: lst[-1] if lst else None,
                'contem':     lambda lst, v: v in lst,
                'indice':     lambda lst, v: lst.index(v) if v in lst else -1,
                'embaralhar': lambda lst: (__import__('random').shuffle(lst), lst)[1],
                'amostra':    lambda lst, n: __import__('random').sample(lst, n),
            },
            'std:data': {
                'agora':      lambda: __import__('datetime').datetime.now().isoformat(),
                'hoje':       lambda: __import__('datetime').date.today().isoformat(),
                'formatar':   lambda d, fmt='%Y-%m-%d': __import__('datetime').datetime.fromisoformat(d).strftime(fmt),
                'diff_dias':  lambda d1, d2: (__import__('datetime').date.fromisoformat(d2) - __import__('datetime').date.fromisoformat(d1)).days,
            },
            'std:json': {
                'parsear':    lambda s: __import__('json').loads(s),
                'serializar': lambda v: __import__('json').dumps(v, ensure_ascii=False),
                'formatar':   lambda v: __import__('json').dumps(v, indent=2, ensure_ascii=False),
            },
            'std:http': {
                'get':    lambda url, **kw: __import__('urllib.request', fromlist=['urlopen']).urlopen(url).read().decode(),
                'json':   lambda url: __import__('json').loads(__import__('urllib.request', fromlist=['urlopen']).urlopen(url).read()),
                'post':   lambda url, dados=None: (lambda: (
                    __import__('urllib.request', fromlist=['urlopen', 'Request']),
                    __import__('json')
                ) and __import__('urllib.request', fromlist=['urlopen']).urlopen(
                    __import__('urllib.request', fromlist=['Request']).Request(
                        url, data=__import__('json').dumps(dados or {}).encode(),
                        headers={'Content-Type': 'application/json'}
                    )
                ).read().decode())(),
                'baixar': lambda url, dest: (
                    __import__('urllib.request').urlretrieve(url, dest), f"✅ Baixado: {dest}"
                )[1],
            },
        }

        if source in std_modules:
            exports = std_modules[source]
            self._apply_imports(node, scope, exports, source)
            return

        # ── File modules ──────────────────────────────────────────────────
        import os
        if not source.endswith('.dk'):
            source = source + '.dk'
        # Search order: 1) absolute, 2) relative to cwd, 3) relative to projetos/
        search_dirs = [
            os.getcwd(),
            os.path.join(os.getcwd(), 'projetos'),
            os.path.dirname(os.path.abspath(__file__)),
        ]
        # Also check if there's a _current_file set on the interpreter
        if hasattr(self, '_current_file') and self._current_file:
            search_dirs.insert(0, os.path.dirname(os.path.abspath(self._current_file)))

        path = None
        if os.path.isabs(source):
            path = source
        else:
            for d in search_dirs:
                candidate = os.path.join(d, source)
                if os.path.exists(candidate):
                    path = candidate
                    break

        if not path or not os.path.exists(path):
            searched = ', '.join(search_dirs)
            raise AdvakError(f"Módulo não encontrado: '{source}'\n  Buscado em: {searched}")

        # Use cache to avoid re-executing
        if path in self._loaded_modules:
            exports = self._loaded_modules[path]
            self._apply_imports(node, scope, exports, source)
            return

        # Execute the module file
        from advak_lexer import AdvakLexer
        from advak_parser import Parser as AdvakParser
        module_src = open(path, encoding='utf-8').read()
        tokens = AdvakLexer(module_src).tokenize()
        ast    = AdvakParser(tokens).parse()

        # Create module scope
        mod_scope = Scope(self.global_scope)
        mod_scope._exports = set()

        # Execute module
        for node_m in ast:
            await self.exec_node(node_m, mod_scope)

        # Collect exports
        if mod_scope._exports:
            exports = {name: mod_scope.vars[name]
                      for name in mod_scope._exports
                      if name in mod_scope.vars}
        else:
            # If no explicit exports, export everything declared at top level
            exports = dict(mod_scope.vars)

        self._loaded_modules[path] = exports
        self._apply_imports(node, scope, exports, source)

    def _apply_imports(self, node, scope, exports, source):
        """Apply imported names to scope based on import mode."""
        mode = node['mode']

        if mode == 'named':
            for item in node['names']:
                name  = item['name']
                alias = item['alias']
                if name not in exports:
                    raise AdvakError(f"'{name}' não exportado por '{source}'")
                scope.declare(alias, exports[name])

        elif mode == 'namespace':
            alias = node['alias']
            scope.declare(alias, exports)

        elif mode == 'alias':
            alias = node['alias']
            scope.declare(alias, exports)

        else:  # default — import all into current scope
            for name, val in exports.items():
                if not name.startswith('_'):
                    scope.declare(name, val)

    def _ai_set_modelo(self, modelo):
        if modelo:
            self._ai_modelo = modelo
            return f"Modelo: {modelo}"
        return self._ai_modelo

    def _ai_set_provedor(self, provedor):
        if provedor:
            if provedor not in self._ai_providers:
                return f"[IA] Provedor desconhecido: {provedor}. Use: {list(self._ai_providers.keys())}"
            self._ai_provedor = provedor
            # Set default model for provider
            modelos = self._ai_providers[provedor]['modelos']
            if modelos: self._ai_modelo = modelos[0]
            return f"Provedor: {provedor}, Modelo: {self._ai_modelo}"
        return self._ai_provedor

    def _ai_set_sistema(self, sistema):
        self._ai_sistema = sistema
        return f"Sistema: {sistema[:50] if sistema else '(limpo)'}..."

    def _ai_call_sync(self, prompt, system=None, usar_contexto=True):
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(lambda: asyncio.run(self._ai_call(prompt, system, usar_contexto)))
            return future.result()

    async def _ai_call(self, prompt, system=None, usar_contexto=True):
        try:
            prov = self._ai_provedor
            pinfo = self._ai_providers.get(prov, {})
            key = self.ai_api_key or os.environ.get(pinfo.get('env','GROQ_API_KEY'), '')
            if not key:
                env_name = pinfo.get('env', 'GROQ_API_KEY')
                return f'[IA] Defina {env_name} no arquivo .env'

            # Build messages with context
            messages = []
            sys_prompt = system or self._ai_sistema
            if sys_prompt:
                messages.append({'role': 'system', 'content': sys_prompt})
            if usar_contexto:
                messages.extend(self._ai_contexto[-10:])  # last 10 messages
            messages.append({'role': 'user', 'content': str(prompt)})

            # Call the right provider
            resposta = await self._ai_call_provider(prov, key, messages)

            # Save to context
            if usar_contexto:
                self._ai_contexto.append({'role': 'user', 'content': str(prompt)})
                self._ai_contexto.append({'role': 'assistant', 'content': resposta})

            return resposta
        except Exception as e:
            return f"[Erro IA] {e}"

    async def _ai_call_provider(self, prov, key, messages):
        modelo = self._ai_modelo

        if prov == 'groq':
            from groq import Groq
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model=modelo, messages=messages, max_tokens=2048)
            return resp.choices[0].message.content

        elif prov == 'openrouter':
            import urllib.request, urllib.error
            url = 'https://openrouter.ai/api/v1/chat/completions'
            payload = {'model': modelo, 'messages': messages, 'max_tokens': 2048}
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST',
                headers={'Content-Type':'application/json',
                         'Authorization':f'Bearer {key}',
                         'HTTP-Referer':'https://advak.dev',
                         'X-Title':'Advak Studio'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())['choices'][0]['message']['content']

        elif prov == 'deepseek':
            import urllib.request
            url = 'https://api.deepseek.com/chat/completions'
            payload = {'model': modelo, 'messages': messages, 'max_tokens': 2048}
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST',
                headers={'Content-Type':'application/json',
                         'Authorization':f'Bearer {key}'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())['choices'][0]['message']['content']

        elif prov == 'gemini':
            import urllib.request
            url = f'https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={key}'
            # Convert messages to Gemini format
            parts_text = '\n'.join(f"{m['role'].upper()}: {m['content']}" for m in messages)
            payload = {'contents': [{'parts': [{'text': parts_text}]}],
                      'generationConfig': {'maxOutputTokens': 2048}}
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST',
                headers={'Content-Type':'application/json; charset=utf-8'})
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.loads(r.read().decode())
                return result['candidates'][0]['content']['parts'][0]['text']

        else:
            raise AdvakError(f"Provedor desconhecido: {prov}")
    async def _do_assign(self, target, op, value, scope):
        if target['type'] == 'ident':
            if op != '=':
                cur = scope.get(target['name'])
                value = self._binop(cur, op[0], value)
            scope.set(target['name'], value)
            return value
        if target['type'] == 'member':
            obj  = await self.eval(target['obj'], scope)
            prop = target['prop']
            if op != '=':
                cur = self._get_member(obj, prop)
                value = self._binop(cur, op[0], value)
            if isinstance(obj, dict):
                obj[prop] = value
            elif isinstance(obj, AdvakStructInstance):
                obj.set(prop, value)
            elif isinstance(obj, AdvakRef):
                # deref via .valor = x
                if prop in ('valor', 'value', 'deref'):
                    obj._scope.set(obj._name, value)
                else:
                    raise AdvakError(f"Não é possível atribuir '{prop}' em ref")
            elif isinstance(obj, AdvakInstance):
                setter = obj._find_setter(prop)
                if setter: await self._call_fn(setter.func, [value], scope, this=obj)
                else: obj.fields[prop] = value
            elif isinstance(obj, AdvakClass):
                obj.fields[prop] = value
            return value
        if target['type'] == 'index':
            obj = await self.eval(target['obj'],   scope)
            idx = await self.eval(target['index'], scope)
            if isinstance(obj, list):
                try:
                    i = int(idx)
                    if op != '=':
                        cur = obj[i] if 0 <= i < len(obj) else 0
                        value = self._binop(cur, op[0], value)
                    obj[i] = value
                except (TypeError, ValueError, IndexError):
                    pass
            elif isinstance(obj, dict):
                if op != '=':
                    cur = obj.get(idx, 0)
                    value = self._binop(cur, op[0], value)
                obj[idx] = value
            return value
        raise AdvakError("Alvo de atribuição inválido")

    def _get_member(self, obj, prop):
        # SuperProxy — super.metodo() access
        if hasattr(obj, 'get') and hasattr(obj, '_klass') and hasattr(obj, '_instance'):
            result = obj.get(prop)
            if result is not None: return result
            raise AdvakError(f"Método '{prop}' não encontrado na superclasse")

        # Query builder — encadeia .onde(), .ordenar(), .limite(), .executar()
        if isinstance(obj, (QueryBuilder, UpdateBuilder, DeleteBuilder)):
            method = getattr(obj, prop, None)
            if method: return method
            raise AdvakError(f"Método '{prop}' não existe no builder")

        # Generator — propriedades úteis
        if isinstance(obj, AdvakGenerator):
            if prop in ('feito', 'done'):   return obj._done
            if prop in ('proximo', 'next'):
                async def _next_val():
                    try: return await obj.__anext__()
                    except StopAsyncIteration: return None
                return _next_val
            raise AdvakError(f"Propriedade '{prop}' não existe no gerador")

        # PrologDB — interface OO
        if isinstance(obj, PrologDB):
            if prop in ('fato', 'fact'):
                return lambda pred, *args: obj.add_fact(pred, list(args))
            if prop in ('regra', 'rule'):
                return lambda pred, head_args, body: obj.add_rule(pred, head_args, body)
            if prop in ('consultar', 'query'):
                return lambda pred, *args: obj.query(pred, list(args))
            if prop in ('fatos', 'facts'):   return dict(obj.facts)
            if prop in ('regras', 'rules'):  return dict(obj.rules)
            raise AdvakError(f"Propriedade '{prop}' não existe em logica/logic")

        # ── Haskell — FrozenMap (mapa imutável) ──────────────────────────
        if isinstance(obj, FrozenMap):
            return obj.get(prop)

        # ── Haskell — FrozenList (lista imutável) ─────────────────────────
        if isinstance(obj, FrozenList):
            return obj.get(prop)

        # ── Haskell — ADT type (acesso a variantes: Arvore.No) ────────────
        if isinstance(obj, AdvakADTType):
            if prop in obj.variants:
                v = obj.variants[prop]
                if v['fields']:
                    _adt = obj; _vname = prop; _fields = v['fields']
                    def _make_ctor(a, vn, fs):
                        def _ctor(*args):
                            return AdvakADTVariant(a, vn, list(args))
                        return _ctor
                    return _make_ctor(_adt, _vname, _fields)
                return AdvakADTVariant(obj, prop, [])
            if prop in ('variantes', 'variants'):
                return list(obj.variants.keys())
            if prop in ('nome', 'name'): return obj.name
            raise AdvakError(f"Variante '{prop}' não existe em tipo {obj.name}")

        # ── Haskell — ADT variant ─────────────────────────────────────────
        if isinstance(obj, AdvakADTVariant):
            return obj.get(prop)

        # ── C/C++ — Struct instance ───────────────────────────────────────
        if isinstance(obj, AdvakStructInstance):
            if prop in ('para_mapa', 'to_dict', 'to_map'):
                return obj.to_dict
            if prop in ('tipo', 'type'):
                return obj._type.name
            return obj.get(prop)

        # ── C/C++ — Enum type (acesso a variantes: Direcao.Norte) ─────────
        if isinstance(obj, AdvakEnumType):
            if prop in obj.variants:
                v = obj.variants[prop]
                if v['payload']:
                    enum_ref = obj
                    vname = prop
                    def _variant_ctor(*args, _e=enum_ref, _n=vname):
                        return AdvakEnumVariant(_e, _n, list(args))
                    return _variant_ctor
                return AdvakEnumVariant(obj, prop, [])
            if prop in ('variantes', 'variants'):
                return list(obj.variants.keys())
            if prop in ('nome', 'name'):
                return obj.name
            raise AdvakError(f"Variante '{prop}' não existe em enum {obj.name}")

        # ── C/C++ — Enum variant ──────────────────────────────────────────
        if isinstance(obj, AdvakEnumVariant):
            return obj.get(prop)

        # ── C/C++ — Ref ───────────────────────────────────────────────────
        if isinstance(obj, AdvakRef):
            return obj.get(prop)

        if isinstance(obj, dict):
            # If the key exists in the dict, return it directly
            # (allows gui dict and other named dicts to work correctly)
            if prop in obj:
                return obj[prop]
            # Meta-properties for dicts (only when key not in dict)
            if prop == 'chaves':     return list(obj.keys())
            if prop == 'valores':    return list(obj.values())
            if prop == 'pares':      return list(obj.items())
            if prop == 'tamanho':    return len(obj)
            if prop == 'comprimento':return len(obj)
            if prop == 'keys':       return list(obj.keys())
            if prop == 'values':     return list(obj.values())
            if prop == 'items':      return list(obj.items())
            if prop == 'length':     return len(obj)
            if prop == 'vazio':      return len(obj) == 0
            if prop == 'contem':     return lambda k: k in obj
            if prop == 'tem':        return lambda k: k in obj
            if prop == 'has':        return lambda k: k in obj
            if prop == 'get':        return lambda k, d=None: obj.get(k, d)
            if prop == 'obter':      return lambda k, d=None: obj.get(k, d)
            if prop == 'definir':    return lambda k=None, v=None: obj.update({k: v}) if k else None
            if prop == 'remover':    return lambda k=None: obj.pop(k, None) if k else None
            if prop == 'pop':        return lambda k, d=None: obj.pop(k, d)
            if prop == 'atualizar':  return lambda d=None: obj.update(d) if d else None
            if prop == 'update':     return lambda d=None: obj.update(d) if d else None
            if prop == 'limpar':     return obj.clear
            if prop == 'copia':      return lambda: dict(obj)
            if prop == 'copy':       return lambda: dict(obj)
            if prop == 'mapear':     return lambda fn: {k: self._call_sync(fn,[k,v]) for k,v in obj.items()}
            if prop == 'filtrar':    return lambda fn: {k:v for k,v in obj.items() if self._call_sync(fn,[k,v])}
            if prop == 'para_cada':  return lambda fn: [self._call_sync(fn,[k,v]) for k,v in obj.items()]
            # Return None for missing dict keys (DB rows may have missing columns)
            return None

        if isinstance(obj, list):
            attrs = {
                # Propriedades
                'tamanho':    len(obj), 'comprimento': len(obj),
                'length':     len(obj), 'size': len(obj),
                # primeiro/ultimo: valor direto; `lista.primeiro()` é tolerado em _eval_call
                'primeiro':   obj[0] if obj else None,
                'ultimo':     obj[-1] if obj else None,
                'vazia':      len(obj) == 0,
                # Mutação
                'adicionar':  obj.append,
                'inserir':    obj.insert,
                'remover':    lambda *a: (obj.pop(*a) if obj else (_ for _ in ()).throw(Exception("Lista vazia — não é possível remover elementos de uma lista vazia"))),
                'limpar':     obj.clear,
                'inverter':   lambda: (obj.reverse() or obj),  # BUG 6: return list
                'ordenar':    obj.sort,
                'extend':     obj.extend,
                'append':     obj.append,
                'push':       obj.append,       # JS alias
                'pop':        obj.pop,
                'shift':      lambda: obj.pop(0) if obj else None,
                'unshift':    lambda x: obj.insert(0, x),
                'includes':   lambda x: x in obj,
                'indexOf':    lambda x: obj.index(x) if x in obj else -1,
                'length':     len(obj),
                'insert':     obj.insert,
                'clear':      obj.clear,
                'reverse':    obj.reverse,
                'sort':       obj.sort,
                # Busca
                'contem':     lambda x: x in obj,
                'inclui':     lambda x: x in obj,   # BUG 3: lista.inclui()
                'incluir':    lambda x: x in obj,
                'tem':        lambda x: x in obj,
                'indexOf':    lambda x: obj.index(x) if x in obj else -1,
                'indice_de':  lambda x: obj.index(x) if x in obj else -1,
                'index':      lambda x: obj.index(x) if x in obj else -1,
                # Fatiamento
                'slice':      lambda a, b=None: obj[a:b],
                'fatia':      lambda a, b=None: obj[a:b],
                'primeiros':  lambda n: obj[:n],
                'ultimos':    lambda n: obj[-n:] if n else [],
                # Funcionais
                'map':        lambda fn: [self._call_sync(fn, [x]) for x in obj],
                'mapear':     lambda fn: [self._call_sync_vargs(fn, x, i) for i, x in enumerate(obj)],
                'filtrar':    lambda fn: [x for x in obj if self._call_sync(fn, [x])],
                'filter':     lambda fn: [x for x in obj if self._call_sync(fn, [x])],
                'reduzir':    lambda fn, ini=None: (
                    __import__('functools').reduce(
                        lambda a, b: self._call_sync(fn, [a, b]), obj, ini
                    ) if ini is not None else
                    __import__('functools').reduce(
                        lambda a, b: self._call_sync(fn, [a, b]), obj
                    ) if obj else None
                ),
                'reduce':     lambda fn, ini=None: (
                    __import__('functools').reduce(
                        lambda a, b: self._call_sync(fn, [a, b]), obj, ini
                    ) if ini is not None else
                    __import__('functools').reduce(
                        lambda a, b: self._call_sync(fn, [a, b]), obj
                    ) if obj else None
                ),
                'encontrar':  lambda fn: next((x for x in obj if self._call_sync(fn,[x])), None),
                'find':       lambda fn: next((x for x in obj if self._call_sync(fn,[x])), None),
                'todo':       lambda fn: all(self._call_sync(fn, [x]) for x in obj),
                'todos':      lambda fn: all(self._call_sync(fn, [x]) for x in obj),
                'every':      lambda fn: all(self._call_sync(fn, [x]) for x in obj),
                'algum':      lambda fn: any(self._call_sync(fn, [x]) for x in obj),
                'some':       lambda fn: any(self._call_sync(fn, [x]) for x in obj),
                'any':        lambda fn: any(self._call_sync(fn, [x]) for x in obj),
                'para_cada':  lambda fn: [self._call_sync(fn, [x]) for x in obj],
                'forEach':    lambda fn: [self._call_sync(fn, [x]) for x in obj],
                'para_cada_com_indice': lambda fn: [self._call_sync(fn, [x, i]) for i, x in enumerate(obj)] and None,
                'forEach_com_indice':   lambda fn: [self._call_sync(fn, [x, i]) for i, x in enumerate(obj)] and None,
                'forEachIndexed':       lambda fn: [self._call_sync(fn, [x, i]) for i, x in enumerate(obj)] and None,
                # Agregação
                'unir':       lambda sep='': sep.join(str(x) for x in obj),
                'join':       lambda sep='': sep.join(str(x) for x in obj),
                'soma':       lambda: sum(obj),
                'min':        lambda: min(obj) if obj else None,
                'max':        lambda: max(obj) if obj else None,
                'media':      lambda: sum(obj)/len(obj) if obj else 0,
                'copia':      lambda: list(obj),
                'copy':       lambda: list(obj),
                'flat':       lambda: [y for x in obj for y in (x if isinstance(x, list) else [x])],
                'unico':      lambda: list(dict.fromkeys(obj)),
                'unique':     lambda: list(dict.fromkeys(obj)),
                'contar':     lambda x=None: obj.count(x) if x is not None else len(obj),
                'count':      lambda x=None: obj.count(x) if x is not None else len(obj),
                'ordenar_por': lambda fn: sorted(obj, key=lambda x: self._call_sync(fn,[x])),
                'sortBy':      lambda fn: sorted(obj, key=lambda x: self._call_sync(fn,[x])),
            }
            if prop in attrs: return attrs[prop]

        if isinstance(obj, str):
            attrs = {
                # PT-BR
                'tamanho': len(obj), 'comprimento': len(obj),
                'maiusculo': obj.upper, 'minusculo': obj.lower,
                'capitalizar': obj.capitalize, 'titulo': obj.title,
                'aparar': obj.strip, 'aparar_esq': obj.lstrip, 'aparar_dir': obj.rstrip,
                'dividir': obj.split, 'substituir': obj.replace,
                'contem': lambda s: s in obj,
                'começa': obj.startswith, 'começa_com': obj.startswith,
                'ultimo': lambda: obj[-1] if obj else '',
                'primeiro': lambda: obj[0] if obj else '',
                'termina': obj.endswith, 'termina_com': obj.endswith,
                'encontrar': obj.find, 'indice': lambda s: obj.index(s) if s in obj else -1,
                'slice': lambda a, b=None: obj[a:b],
                'fatia': lambda a, b=None: obj[a:b],
                'char': lambda i: obj[i] if -len(obj) <= i < len(obj) else '',
                'primeiros': lambda n: obj[:n],
                'ultimos': lambda n: obj[-n:] if n else '',
                'repetir': lambda n: obj * n,
                'inverter': lambda: obj[::-1],
                'e_numero': lambda: obj.isdigit(),
                'e_vazia': lambda: obj.strip() == '',
                'zfill': obj.zfill,
                'contar': obj.count,
                # Python aliases (compatibilidade)
                'strip': obj.strip, 'lstrip': obj.lstrip, 'rstrip': obj.rstrip,
                'upper': obj.upper, 'lower': obj.lower,
                'title': obj.title, 'capitalize': obj.capitalize,
                'split': obj.split, 'join': lambda lst: obj.join(str(x) for x in lst),
                'replace': obj.replace, 'find': obj.find,
                'startswith': obj.startswith, 'endswith': obj.endswith,
                'includes':   lambda s: s in obj,
                'length':     len(obj),
                'isdigit': obj.isdigit, 'isalpha': obj.isalpha,
                'isnumeric': obj.isnumeric, 'isspace': obj.isspace,
                'format': obj.format, 'count': obj.count,
                'index': lambda s: obj.index(s) if s in obj else -1,
                'encode': obj.encode,
                'center': obj.center, 'ljust': obj.ljust, 'rjust': obj.rjust,
                # JS/extra aliases
                'trim':      obj.strip,
                'trimStart': obj.lstrip, 'trimEnd': obj.rstrip,
                'padStart':  lambda n, c=' ': str(obj).rjust(int(n), str(c)[-1] if c else ' '),
                'padEnd':    lambda n, c=' ': str(obj).ljust(int(n), str(c)[-1] if c else ' '),
                'substr':    lambda s, e=None: obj[int(s):(int(s)+int(e) if e is not None else None)],
                'substring': lambda s, e=None: obj[int(min(s,e or len(obj))):int(max(s,e or len(obj)))],
                'charAt':    lambda i: obj[int(i)] if 0 <= int(i) < len(obj) else '',
                'charCodeAt':lambda i: ord(obj[int(i)]) if 0 <= int(i) < len(obj) else 0,
                'indexOf':   lambda s: obj.find(str(s)),
                'lastIndexOf':lambda s: obj.rfind(str(s)),
                'slice':     lambda s, e=None: obj[int(s):(int(e) if e is not None else None)],
                'repeat':    lambda n: obj * int(n),
                'match':     lambda p: __import__('re').findall(p, obj),
                'mapear':    lambda fn: [self._call_sync_vargs(fn, c, i) for i, c in enumerate(obj)],
                'dividir_chars': lambda: list(obj),
                'para_cada': lambda fn: [self._call_sync_vargs(fn, c) for c in obj] and None,
            }
            if prop in attrs: return attrs[prop]
            # Tenta acessar como atributo/método Python nativo
            if hasattr(obj, prop):
                return getattr(obj, prop)
            # Unknown string property → return None
            return None

        if isinstance(obj, AdvakClass):
            if prop in obj.fields: return obj.fields[prop]
            if prop in obj.statics: return BoundMethod(obj, obj.statics[prop])
            if prop in ('nome','name'): return obj.name
            raise AdvakError(f"'{prop}' não existe na classe {obj.name}")
        if isinstance(obj, AdvakInstance):
            return obj.get(prop)

        # Objetos Python com atributos (ex: ttk.Treeview com métodos customizados)
        if hasattr(obj, prop):
            attr = getattr(obj, prop)
            # ── Wrap tkinter widget's bind/after to handle AdvakFunction ──────
            try:
                import tkinter as _tk
                if isinstance(obj, (_tk.Misc, _tk.BaseWidget)):
                    gui_mod = None
                    try:
                        import advak_gui_modern as _gm
                        gui_mod = _gm
                    except ImportError:
                        pass

                    if prop == 'bind' and gui_mod:
                        def _safe_bind(event_key, fn, _obj=obj, _gm=gui_mod):
                            inst = getattr(_gm, '_gui_instance', None)
                            def _handler(event, _f=fn, _i=inst):
                                if _i: _i._chamar(_f, event)
                            _obj.bind(event_key, _handler)
                        return _safe_bind

                    elif prop == 'after' and gui_mod:
                        def _safe_after(ms, fn, _obj=obj, _gm=gui_mod):
                            inst = getattr(_gm, '_gui_instance', None)
                            def _handler(_f=fn, _i=inst):
                                if _i: _i._chamar(_f, None)
                            _obj.after(int(ms), _handler)
                        return _safe_after

                    elif prop in ('pack', 'grid', 'place', 'configure', 'config'):
                        # Translate PT-BR parameter names to English tkinter names
                        _PT_TO_EN = {
                            # pack() parameters
                            'lado':       'side',
                            'preencher':  'fill',
                            'expandir':   'expand',
                            'espaco_x':   'padx',
                            'espaco_y':   'pady',
                            'espaco_ix':  'ipadx',
                            'espaco_iy':  'ipady',
                            'ancora':     'anchor',
                            # configure() parameters
                            'texto':      'text',
                            'estado':     'state',
                            'largura':    'width',
                            'altura':     'height',
                            'cursor_bg':  'insertbackground',
                            'relevo':     'relief',
                            # Side values
                            'esquerda':   'left',
                            'direita':    'right',
                            'topo':       'top',
                            'fundo':      'bottom',
                            # Fill values
                            'ambos':      'both',
                            'nenhum':     'none',
                            # State values
                            'habilitado': 'normal',
                            'desabilitado': 'disabled',
                            'somente_leitura': 'readonly',
                            # Anchor values
                            'centro':     'center',
                            'norte':      'n',
                            'sul':        's',
                            'leste':      'e',
                            'oeste':      'w',
                        }
                        _method = getattr(obj, prop)
                        # Parâmetros cujos VALORES não devem ser traduzidos
                        _NO_TRANSLATE_VALUE = {
                            'text', 'font', 'bg', 'fg', 'background', 'foreground',
                            'insertbackground', 'selectbackground', 'highlightcolor',
                            'activebackground', 'activeforeground', 'disabledforeground',
                            'cursor', 'relief', 'image', 'title', 'variable',
                        }
                        def _font_str_para_tupla(s):
                            """Converte 'Nome Com Espaço 12 bold' → ('Nome Com Espaço', 12, 'bold')
                            Necessário para Windows/Tcl que parseia strings de fonte por espaço."""
                            if not isinstance(s, str): return s
                            tokens = s.strip().split()
                            if len(tokens) < 2: return s
                            # Encontrar o tamanho (inteiro) — geralmente o segundo token
                            # mas pode ser o último antes de estilos
                            size_idx = -1
                            for i, tok in enumerate(tokens):
                                try:
                                    int(tok); size_idx = i; break
                                except ValueError: pass
                            if size_idx < 0: return s  # sem tamanho → retorna como está
                            nome  = ' '.join(tokens[:size_idx])
                            size  = int(tokens[size_idx])
                            resto = tokens[size_idx+1:]
                            if resto:
                                return (nome, size, ' '.join(resto))
                            return (nome, size)

                        def _pt_wrapper(*args, _m=_method, _tr=_PT_TO_EN,
                                        _ntv=_NO_TRANSLATE_VALUE, **kwargs):
                            # Translate kwargs
                            new_kw = {}
                            for k, v in kwargs.items():
                                en_k = _tr.get(k, k)
                                if en_k == 'font' and isinstance(v, str):
                                    # CRÍTICO: converter font string → tupla Python
                                    # Evita TclError "expected integer but got UI"
                                    # com fontes cujo nome tem espaço (ex: "Segoe UI 9 bold")
                                    en_v = _font_str_para_tupla(v)
                                elif isinstance(v, str) and en_k not in _ntv:
                                    en_v = _tr.get(v, v)
                                else:
                                    en_v = v
                                new_kw[en_k] = en_v
                            # Translate positional string args (apenas side/fill/anchor values)
                            new_args = []
                            for a in args:
                                if isinstance(a, str):
                                    new_args.append(_tr.get(a, a))
                                else:
                                    new_args.append(a)
                            return _m(*new_args, **new_kw)
                        return _pt_wrapper
            except Exception:
                pass
            return attr

        raise AdvakError(f"Não é possível acessar '{prop}' em {_tipo_pt(obj)}")

    def _call_sync_vargs(self, fn, *args):
        """Call fn with as many args as it accepts (up to len(args))."""
        if hasattr(fn, 'params'):
            n = len(fn.params)
            actual = list(args)[:n] if n > 0 else []
        elif callable(fn):
            import inspect
            try:
                sig = inspect.signature(fn)
                n = len([p for p in sig.parameters.values()
                         if p.default is inspect.Parameter.empty])
                actual = list(args)[:max(n, 1)]
            except Exception:
                actual = [args[0]] if args else []
        else:
            actual = [args[0]] if args else []
        return self._call_sync(fn, actual)

    def _call_sync(self, fn, args):
        if isinstance(fn, AdvakFunction):
            import concurrent.futures, asyncio
            async def _run():
                return await self._call_fn(fn, args, self.global_scope)
            try:
                # If there's a running loop, run in a thread
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(lambda: asyncio.run(_run()))
                        return future.result()
                else:
                    return loop.run_until_complete(_run())
            except RuntimeError:
                return asyncio.run(_run())
        if callable(fn): return fn(*args)
        raise AdvakError(
                f"'{fn}' não é uma função — verifique se declarou a função com 'funcao nome() {{ }}'" +
                (f" (linha {self._current_line})" if hasattr(self, '_current_line') and self._current_line else ""))

    async def _interp_template(self, tmpl, scope):
        # `${expr}` e `${expr:formato}` (moeda, data, .2f ...); veja advak_formatacao.py
        from advak_lexer import AdvakLexer
        from advak_parser import Parser
        from advak_formatacao import dividir_template, separar_formato, formatar_valor, ErroFormato
        cache = self.__dict__.setdefault('_cache_interp', {})
        res = []
        for tipo, conteudo in dividir_template(tmpl):
            if tipo == 't':
                res.append(conteudo)
                continue
            try:
                expr, formato = separar_formato(conteudo)
            except ErroFormato as e:
                raise AdvakError(f"Formato inválido em ${{{conteudo.strip()}}}: {e}")
            expr = expr.strip()
            if not expr:
                raise AdvakError(f"Falta a expressão antes do formato em ${{{conteudo.strip()}}}")
            node = cache.get(expr)
            if node is None:
                node = cache[expr] = Parser(AdvakLexer(expr).tokenize()).parse_expression()
            valor = await self.eval(node, scope)
            if formato is None:
                res.append(self._to_str(valor))
                continue
            try:
                res.append(formatar_valor(valor, formato, self._to_str))
            except ErroFormato as e:
                raise AdvakError(f"Formato inválido em ${{{conteudo.strip()}}}: {e}")
        return ''.join(res)

    # ── Tipagem opcional: seja x: inteiro / função f(a: numero) -> numero ──────

    def _validar_anotacao(self, tipo, scope, onde):
        try:
            advak_tipos.validar(tipo, _CtxTipos(scope))
            tipo['_validado'] = True
        except advak_tipos.ErroTipo as e:
            raise AdvakError(f"Tipo inválido em {onde}: {e}")

    def _combina(self, valor, tipo, scope, onde):
        """(True/False, contexto); anotação inválida (tipo desconhecido) vira AdvakError em português."""
        ctx = _CtxTipos(scope)
        try:
            if not tipo.get('_validado'):
                advak_tipos.validar(tipo, ctx)
                tipo['_validado'] = True               # nomes conferidos uma vez só (a anotação é fixa)
            return advak_tipos.confere(valor, tipo, ctx), ctx
        except advak_tipos.ErroTipo as e:
            raise AdvakError(f"Tipo inválido em {onde}: {e}")

    def _verificador_de_variavel(self, nome, tipo, scope):
        def verificador(valor):
            if tipo.get('_validado') and advak_tipos.confere(valor, tipo, _CtxTipos(scope)):
                return                                  # caminho rápido
            ok, ctx = self._combina(valor, tipo, scope, f"variável '{nome}'")
            if not ok:
                raise AdvakError(f"Tipo incorreto: '{nome}' é {advak_tipos.descrever_tipo(tipo)}, "
                                 f"mas recebeu {advak_tipos.descrever_valor(valor, ctx)}.")
        return verificador

    def _conferir_parametro(self, fn, pname, valor, tipo, scope):
        if tipo.get('_validado') and advak_tipos.confere(valor, tipo, _CtxTipos(scope)):
            return                                      # caminho rápido
        onde = f"parâmetro '{pname}' de {fn.name or 'função anônima'}()"
        ok, ctx = self._combina(valor, tipo, scope, onde)
        if not ok:
            dica = " (faltou passar este argumento?)" if valor is None else ""
            raise AdvakError(f"Tipo incorreto no {onde}: esperava {advak_tipos.descrever_tipo(tipo)}, "
                             f"mas recebeu {advak_tipos.descrever_valor(valor, ctx)}.{dica}")

    def _conferir_retorno(self, fn, valor, retornou, scope):
        tipo = fn.retorno
        if tipo.get('_validado') and advak_tipos.confere(valor, tipo, _CtxTipos(scope)):
            return                                      # caminho rápido
        onde = f"retorno de {fn.name or 'função anônima'}()"
        ok, ctx = self._combina(valor, tipo, scope, onde)
        if not ok:
            if not retornou:
                raise AdvakError(f"Tipo incorreto no {onde}: esperava {advak_tipos.descrever_tipo(tipo)}, "
                                 "mas a função terminou sem 'retornar' um valor (nulo).")
            raise AdvakError(f"Tipo incorreto no {onde}: esperava {advak_tipos.descrever_tipo(tipo)}, "
                             f"mas retornou {advak_tipos.descrever_valor(valor, ctx)}.")
    # ── Intervalos: 1..10, 1..=10, 1..=10 passo 2 ──────────────────────────────

    _MAX_INTERVALO = 10_000_000

    @staticmethod
    def _inteiro_intervalo(valor, o_que):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise AdvakError(f"Intervalo: o {o_que} deve ser um número inteiro (recebi {valor!r}).")
        if isinstance(valor, float):
            if valor != int(valor):
                raise AdvakError(f"Intervalo: o {o_que} deve ser um número inteiro (recebi {valor}). "
                                 "Use piso(), teto() ou arred() para converter.")
            valor = int(valor)
        return valor

    async def _eval_intervalo(self, node, scope):
        """Devolve um `range` do Python (preguiçoso). `..` exclui o fim; `..=` inclui."""
        ini = self._inteiro_intervalo(await self.eval(node['start'], scope), 'início')
        fim = self._inteiro_intervalo(await self.eval(node['end'], scope), 'fim')
        passo = 1
        if node.get('step') is not None:
            passo = self._inteiro_intervalo(await self.eval(node['step'], scope), 'passo')
            if passo == 0:
                raise AdvakError("Intervalo: o passo não pode ser zero.")
        if node['inclusive']:
            fim += 1 if passo > 0 else -1
        return range(ini, fim, passo)

    # ── Compreensão de listas: [x * 2 para x em lista se x > 0] ─────────────────

    @staticmethod
    def _nome_tipo(v):
        if v is None:
            return 'nulo'
        if isinstance(v, bool):
            return 'booleano'
        if isinstance(v, (int, float)):
            return 'número'
        return type(v).__name__

    async def _comp_rec(self, node, i, escopo, saida):
        clausulas = node['clauses']
        if i == len(clausulas):
            saida.append(await self.eval(node['element'], escopo))
            if len(saida) > self._MAX_INTERVALO:
                raise AdvakError(f"Compreensão de lista: o resultado passou de {self._MAX_INTERVALO} itens. "
                                 "Filtre mais com 'se' ou processe em partes.")
            return
        c = clausulas[i]
        if c['kind'] == 'if':
            if self._truthy(await self.eval(c['cond'], escopo)):
                await self._comp_rec(node, i + 1, escopo, saida)
            return
        fonte = await self._eval_iteravel(c['iter'], escopo)
        if isinstance(fonte, dict):
            fonte = list(fonte.keys())
        nomes = c['var'] if isinstance(c['var'], list) else None

        async def passo(item):
            interno = Scope(escopo)
            if nomes is None:
                interno.declare(c['var'], item)
            else:
                if not isinstance(item, (list, tuple)) or len(item) != len(nomes):
                    raise AdvakError(f"Compreensão de lista: esperava {len(nomes)} valores em cada item "
                                     f"(para ({', '.join(nomes)}) em ...), mas recebi {item!r}.")
                for nome, valor in zip(nomes, item):
                    interno.declare(nome, valor)
            await self._comp_rec(node, i + 1, interno, saida)

        if isinstance(fonte, AdvakGenerator):
            async for item in fonte:
                await passo(item)
        elif isinstance(fonte, (list, tuple, str, range, set)):
            for item in fonte:
                await passo(item)
        else:
            raise AdvakError(f"Compreensão de lista: não é possível percorrer um valor do tipo "
                             f"{self._nome_tipo(fonte)}. Use uma lista, um texto, um mapa ou um intervalo.")

    async def _eval_iteravel(self, expr, scope):
        """Valor sobre o qual o laço `para` itera; intervalos ficam preguiçosos (sem criar lista)."""
        if isinstance(expr, dict) and expr.get('type') == 'range':
            return await self._eval_intervalo(expr, scope)
        return await self.eval(expr, scope)

    # ── Conexão com bancos (advak_conectores) ─────────────────────────────────

    def _banco_conectar(self, *a, **kw):
        import advak_conectores as _c
        if _c.eh_conexao_nova(a, kw):
            try:
                return _c.conectar(*a, **kw)
            except _c.ErroBanco as e:
                raise AdvakError(str(e))
        return self.db.conectar(*a)

    # ── Pattern Matching ──────────────────────────────────────────────────────

    def _match_pattern(self, pattern, value, bindings):
        """Verifica se value casa com pattern, preenchendo bindings. Retorna bool."""
        pt = pattern.get('ptype')

        if pt == 'wildcard':
            return True

        if pt == 'bind':
            bname = pattern['name']
            # Wildcard _ sempre casa
            if bname == '_':
                return True
            # Se o valor é um ADT variant — verifica nome antes de fazer bind
            if isinstance(value, AdvakADTVariant):
                if value.nome == bname and not value._args:
                    # Ex: caso Folha  →  casa com Arvore::Folha (sem campos)
                    return True
                elif value.nome != bname:
                    # Ex: caso Folha  vs  Arvore::No  →  NÃO casa
                    # (mas só bloqueia se bname parece ser um nome de variante,
                    #  i.e., começa com maiúscula)
                    if bname[0].isupper():
                        return False
            # Se o valor é um Enum variant — verifica nome
            if isinstance(value, AdvakEnumVariant):
                if value.nome == bname and not value.payload:
                    return True
                elif value.nome != bname and bname[0].isupper():
                    return False
            # Bind normal — liga o nome ao valor
            bindings[bname] = value
            return True

        if pt == 'literal':
            # Comparação simples — o valor do padrão já foi avaliado como nó AST
            # Resolve literais inline (number/string/bool/null)
            node = pattern['value']
            nt = node.get('type', '')
            if nt in ('number', 'float', 'string', 'bool'):
                return value == node['value']
            if nt == 'null':
                return value is None
            # Para idents simples — compara como string
            if nt == 'ident':
                return str(value) == node['name']
            return False

        if pt == 'tuple':
            if not isinstance(value, (list, tuple)):
                return False
            items = pattern['items']
            if len(value) != len(items):
                return False
            for pat_i, val_i in zip(items, value):
                if not self._match_pattern(pat_i, val_i, bindings):
                    return False
            return True

        if pt == 'list':
            if not isinstance(value, list):
                return False
            items = pattern.get('items') or []
            if len(value) < len(items):
                return False
            if pattern.get('rest') is None and len(value) != len(items):
                return False
            for pat_i, val_i in zip(items, value):
                if not self._match_pattern(pat_i, val_i, bindings):
                    return False
            if pattern.get('rest'):
                bindings[pattern['rest']] = value[len(items):]
            return True

        if pt == 'object':
            if not isinstance(value, dict):
                if not isinstance(value, AdvakInstance):
                    return False
            for field in pattern['fields']:
                if isinstance(value, dict):
                    fv = value.get(field['key'])
                else:
                    try: fv = value.get(field['key'])
                    except: return False
                bindings[field['alias']] = fv
            return True

        if pt == 'type':
            type_name = pattern['type_name']
            matches = False
            if isinstance(value, AdvakInstance):
                matches = value.klass.name == type_name
            elif isinstance(value, AdvakStructInstance):
                matches = value._type.name == type_name
            elif isinstance(value, AdvakEnumVariant):
                matches = (value.nome == type_name or
                           f'{value._enum.name}::{value.nome}' == type_name)
            elif isinstance(value, AdvakADTVariant):
                # Suporte: caso No(e,v,d) ou caso Arvore::No(e,v,d)
                matches = (value.nome == type_name or
                           f'{value._adt.name}::{value.nome}' == type_name)
            elif type_name in ('Numero', 'Number') and isinstance(value, (int, float)):
                matches = True
            elif type_name in ('Texto', 'String') and isinstance(value, str):
                matches = True
            elif type_name in ('Lista', 'List') and isinstance(value, (list, FrozenList)):
                matches = True
            elif type_name in ('Mapa', 'Map') and isinstance(value, (dict, FrozenMap)):
                matches = True
            elif type_name in ('Vazia', 'Empty') and isinstance(value, (FrozenList, list)) and len(value) == 0:
                matches = True
            if matches:
                blist = pattern.get('bindings') or []
                if blist:
                    # ADT variant: liga cada binding ao argumento posicional
                    if isinstance(value, AdvakADTVariant):
                        for i, bname in enumerate(blist):
                            bindings[bname] = value._args[i] if i < len(value._args) else None
                    elif isinstance(value, AdvakEnumVariant) and value.payload:
                        for i, bname in enumerate(blist):
                            bindings[bname] = value.payload[i] if i < len(value.payload) else None
                    elif len(blist) == 1:
                        bindings[blist[0]] = value
                    elif isinstance(value, AdvakStructInstance):
                        field_vals = list(value._fields.values())
                        for i, bname in enumerate(blist):
                            bindings[bname] = field_vals[i] if i < len(field_vals) else None
                elif pattern.get('binding'):
                    bindings[pattern['binding']] = value
            return matches

        # Fallback — compara por igualdade
        return value == pattern

    # ── Canvas 2D ─────────────────────────────────────────────────────────────

    def _make_canvas_api(self):
        """Retorna objeto 'tela' com métodos de desenho Canvas 2D."""
        cmds = self._canvas_cmds

        def _cmd(name, **kwargs):
            cmds.append({'cmd': name, **kwargs})

        class CanvasAPI:
            pass

        api = CanvasAPI()

        def retangulo(x, y, w, h, cor='#000', preenchido=True):
            _cmd('rect', x=x, y=y, w=w, h=h, cor=cor, preenchido=preenchido)
        def circulo(x, y, r, cor='#000', preenchido=True):
            _cmd('circle', x=x, y=y, r=r, cor=cor, preenchido=preenchido)
        def linha(x1, y1, x2, y2, cor='#000', espessura=1):
            _cmd('line', x1=x1, y1=y1, x2=x2, y2=y2, cor=cor, espessura=espessura)
        def texto(txt, x, y, cor='#000', fonte='16px sans-serif'):
            _cmd('text', txt=str(txt), x=x, y=y, cor=cor, fonte=fonte)
        def limpar():
            _cmd('clear')
        def cor_fundo(cor):
            _cmd('background', cor=cor)
        def exportar_svg():
            return _canvas_to_svg(cmds)

        api.__dict__['retangulo'] = retangulo
        api.__dict__['circulo']   = circulo
        api.__dict__['linha']     = linha
        api.__dict__['texto']     = texto
        api.__dict__['limpar']    = limpar
        api.__dict__['cor_fundo'] = cor_fundo
        api.__dict__['exportar_svg'] = exportar_svg
        # aliases EN
        api.__dict__['rect']       = retangulo
        api.__dict__['circle']     = circulo
        api.__dict__['line']       = linha
        api.__dict__['clear']      = limpar
        api.__dict__['background'] = cor_fundo
        return api

    def _binop(self, l, op, r):
        # Convert None to safe defaults for comparisons/arithmetic
        def _coerce(a, b):
            if a is None and b is None: return 0, 0
            if a is None:
                return (0 if isinstance(b, (int, float)) else '', b)
            if b is None:
                return (a, 0 if isinstance(a, (int, float)) else '')
            # str + non-str: auto-convert to str
            if op == '+' and isinstance(a, str) and not isinstance(b, str):
                return a, str(b) if not isinstance(b, bool) else ('verdadeiro' if b else 'falso')
            if op == '+' and isinstance(b, str) and not isinstance(a, str):
                return str(a) if not isinstance(a, bool) else ('verdadeiro' if a else 'falso'), b
            return a, b

        ops = {
            '+': lambda a,b: a+b, '-': lambda a,b: a-b,
            '*': lambda a,b: a*b,
            '/': lambda a,b: (float('inf') if a > 0 else float('-inf') if a < 0 else float('nan')) if b == 0 else a/b,
            '//': lambda a,b: int(a)//int(b) if b else 0,
            '%': lambda a,b: a%b, '**': lambda a,b: a**b,
            '==':  lambda a,b: a==b,  '!=':  lambda a,b: a!=b,
            '===': lambda a,b: a==b and type(a)==type(b),
            '!==': lambda a,b: a!=b or  type(a)!=type(b),
            '<':  lambda a,b: a<b,  '>':  lambda a,b: a>b,
            '<=': lambda a,b: a<=b, '>=': lambda a,b: a>=b,
            '&&': lambda a,b: b if self._truthy(a) else a,
            '||': lambda a,b: a if self._truthy(a) else b,
            'e':  lambda a,b: b if self._truthy(a) else a,
            'ou': lambda a,b: a if self._truthy(a) else b,
            'nao': lambda a,b: not self._truthy(a),
            # BUG 10 FIX: operadores bit
            '&':  lambda a,b: int(a) & int(b),
            '|':  lambda a,b: int(a) | int(b),
            '^':  lambda a,b: int(a) ^ int(b),
            '<<': lambda a,b: int(a) << int(b),
            '>>': lambda a,b: int(a) >> int(b),
        }
        if op not in ops: raise AdvakError(f"Operador '{op}' não suportado")
        try:
            cl, cr = _coerce(l, r)
            return ops[op](cl, cr)
        except TypeError as e:
            msg = str(e)
            # Traduzir mensagem do TypeError Python → português
            if 'str' in msg and ('int' in msg or 'float' in msg):
                raise AdvakError("Tipo incompatível: não é possível misturar texto e número — use texto(valor) para converter")
            elif 'unsupported operand' in msg or 'operando não suportado' in msg:
                # Extrair tipos da mensagem do Python e traduzir
                tipos_pt = {'str':'texto','int':'número','float':'número',
                            'list':'lista','dict':'objeto','bool':'booleano',
                            'NoneType':'nulo','tuple':'tupla'}
                partes = re.findall(r"'(\w+)'", msg)
                tipos = [tipos_pt.get(p, p) for p in partes if p in tipos_pt or p in ('str','int','float','list','dict','bool','NoneType')]
                if tipos:
                    raise AdvakError(f"Tipo incompatível: operação '{op}' não suportada entre {' e '.join(tipos)}")
                raise AdvakError(f"Tipo incompatível: operação '{op}' não suportada entre esses tipos")
            elif 'dict' in msg or 'mapping' in msg:
                raise AdvakError(f"Tipo incompatível: não é possível usar operador '{op}' com objetos")
            else:
                # Tradução genérica
                raise AdvakError(f"Tipo incompatível: operador '{op}' não pode ser usado com esses valores")

    def _truthy(self, v):
        if v is None or v is False: return False
        if isinstance(v, (int, float)) and v == 0: return False
        if isinstance(v, (str, list, dict)) and len(v) == 0: return False
        return True

    def _to_str(self, v):
        if v is None:  return 'nulo'
        if v is True:  return 'verdadeiro'
        if v is False: return 'falso'
        if isinstance(v, list):
            def _item_str(x):
                # Strings inside lists show with quotes (like Python repr)
                if isinstance(x, str): return repr(x)
                return self._to_str(x)
            return '[' + ', '.join(_item_str(x) for x in v) + ']'
        if isinstance(v, dict):
            pairs = ', '.join(f'{k}: {self._to_str(val)}' for k, val in v.items())
            return '{' + pairs + '}'
        if isinstance(v, AdvakStructInstance):
            fields = ', '.join(f'{k}: {self._to_str(fv)}' for k, fv in v._fields.items())
            return f'{v._type.name} {{ {fields} }}'
        if isinstance(v, AdvakEnumVariant):
            if v.payload:
                args = ', '.join(self._to_str(x) for x in v.payload)
                return f'{v._enum.name}::{v.nome}({args})'
            return f'{v._enum.name}::{v.nome}'
        if isinstance(v, AdvakEnumType):
            return f'<enum {v.name}>'
        if isinstance(v, AdvakADTVariant):
            if v._args:
                args = ', '.join(self._to_str(x) for x in v._args)
                return f'{v._adt.name}::{v.nome}({args})'
            return f'{v._adt.name}::{v.nome}'
        if isinstance(v, AdvakADTType):
            return f'<tipo {v.name}>'
        if isinstance(v, FrozenMap):
            d = object.__getattribute__(v, '_data')
            pairs = ', '.join(f'{k}: {self._to_str(fv)}' for k, fv in d.items())
            return '#{ ' + pairs + ' }'
        if isinstance(v, FrozenList):
            items = object.__getattribute__(v, '_items')
            return '#[' + ', '.join(self._to_str(x) for x in items) + ']'
        if isinstance(v, AdvakRef):
            return f'ref({v._name} = {self._to_str(v.valor)})'
        if isinstance(v, AdvakMacro):
            return f'<macro {v.name}>'
        return str(v)