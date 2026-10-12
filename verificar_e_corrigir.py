#!/usr/bin/env python3
"""
Advak — Verificador e Corretor Final
Execute: python verificar_e_corrigir.py
"""
import os, sys, ast, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
arq  = os.path.join(BASE, 'advak_interpreter.py')

print("\n╔══════════════════════════════════════════════╗")
print("║   Advak — Verificador e Corretor Final      ║")
print("╚══════════════════════════════════════════════╝\n")

if not os.path.exists(arq):
    print("❌ advak_interpreter.py não encontrado!")
    sys.exit(1)

with open(arq, encoding='utf-8') as f:
    content = f.read()

h = hashlib.md5(content.encode()).hexdigest()[:8]
print(f"Arquivo: {arq}")
print(f"Tamanho: {len(content)} bytes | Hash: {h}")

# Verifica quais fixes já estão aplicados
fixes = {
    'kwargs em _eval_call':    'kw_args' in content and 'pos_args' in content,
    'kwargs em _call_fn':      'kwargs=None' in content,
    'kwargs em params':        'pname in kw' in content,
    'barra_status no gui':     "'barra_status'" in content,
    'toast no gui':            "'toast'" in content,
    'card no gui':             ("'card'" in content and 'barra_status' in content),
    'AdvakGUIModern ativo':    'AdvakGUIModern' in content,
}

print("\nStatus dos fixes:")
todos_ok = True
for nome, ok in fixes.items():
    print(f"  {'✓' if ok else '✗'} {nome}")
    if not ok: todos_ok = False

if todos_ok:
    print("\n✅ Arquivo já está na versão correta!")
    print("   Execute: python advak.py projetos run gui_moderno_demo.dk")
    sys.exit(0)

print("\nAplicando correções necessárias...")
original = content

# ── FIX 1: kwargs em _eval_call ───────────────────────────────
if 'kw_args' not in content:
    OLD = """    async def _eval_call(self, node, scope):
        fn  = await self.eval(node['func'], scope)
        args= [await self.eval(a, scope) for a in node['args']]"""
    NEW = """    async def _eval_call(self, node, scope):
        fn      = await self.eval(node['func'], scope)
        pos_args= []
        kw_args = {}
        for a in node['args']:
            if isinstance(a, dict) and a.get('type') == 'assign' and \\
               isinstance(a.get('target'), dict) and a['target'].get('type') == 'ident':
                kw_args[a['target']['name']] = await self.eval(a['value'], scope)
            else:
                pos_args.append(await self.eval(a, scope))
        args = pos_args"""
    if OLD in content:
        content = content.replace(OLD, NEW, 1)
        print("  OK: kwargs em _eval_call")
    else:
        print("  AVISO: _eval_call não encontrado no formato esperado")

# ── FIX 2: passa kwargs para callable ────────────────────────
if 'pos_args' in content and 'r = fn(*args)' in content:
    content = content.replace(
        'r = fn(*args)\n            return await r if asyncio.iscoroutine(r) else r',
        'r = fn(*pos_args, **kw_args)\n            return await r if asyncio.iscoroutine(r) else r',
        1
    )
    print("  OK: fn chamado com kwargs")

# ── FIX 3: _call_fn aceita kwargs ────────────────────────────
if 'kwargs=None' not in content:
    content = content.replace(
        'async def _call_fn(self, fn, args, caller_scope, this=None):',
        'async def _call_fn(self, fn, args, caller_scope, this=None, kwargs=None):',
        1
    )
    print("  OK: _call_fn aceita kwargs")

# ── FIX 4: BoundMethod passa kwargs ──────────────────────────
if 'kwargs=kw_args' not in content and 'BoundMethod' in content:
    content = content.replace(
        'return await self._call_fn(fn.func, args, scope, this=fn.instance)',
        'return await self._call_fn(fn.func, pos_args if "pos_args" in dir() else args, scope, this=fn.instance, kwargs=kw_args if "kw_args" in dir() else {})',
        1
    )
    content = content.replace(
        'return await self._call_fn(fn, args, scope)',
        'return await self._call_fn(fn, pos_args if "pos_args" in dir() else args, scope, kwargs=kw_args if "kw_args" in dir() else {})',
        1
    )
    print("  OK: BoundMethod e AdvakFunction passam kwargs")

# ── FIX 5: params mapeiam kwargs ─────────────────────────────
if 'pname in kw' not in content and 'fn.params' in content:
    OLD_P = """        for i, param in enumerate(fn.params):
            if param.get('spread'):
                inner.declare(param['name'], list(args[i:]))
                break
            if i < len(args):
                inner.declare(param['name'], args[i])
            elif param.get('default') is not None:"""
    NEW_P = """        kw = kwargs or {}
        for i, param in enumerate(fn.params):
            pname = param['name']
            if param.get('spread'):
                inner.declare(pname, list(args[i:]))
                break
            if pname in kw:
                inner.declare(pname, kw[pname])
            elif i < len(args):
                inner.declare(pname, args[i])
            elif param.get('default') is not None:"""
    if OLD_P in content:
        content = content.replace(OLD_P, NEW_P, 1)
        print("  OK: params mapeiam kwargs")

# ── FIX 6: AdvakGUIModern ────────────────────────────────────
if 'AdvakGUIModern' not in content:
    OLD_G = "from advak_gui import AdvakGUI\n            _gui = AdvakGUI()"
    NEW_G = """try:
                from advak_gui_modern import AdvakGUIModern
                _gui = AdvakGUIModern()
            except Exception:
                from advak_gui import AdvakGUI
                _gui = AdvakGUI()"""
    if OLD_G in content:
        content = content.replace(OLD_G, NEW_G, 1)
        print("  OK: AdvakGUIModern ativo")

# ── FIX 7: métodos modernos no dict gui ──────────────────────
if "'barra_status'" not in content:
    MARCADORES = [
        "'tema':         _gui.tema,",
        "'tema':         lambda t: _gui.tema(t),",
        "'atualizar':    _gui.atualizar,",
    ]
    NOVOS = """
                'toggle':       getattr(_gui,'switch',       lambda *a,**k: None),
                'toast':        getattr(_gui,'toast',        lambda *a,**k: None),
                'card':         getattr(_gui,'card',         lambda *a,**k: None),
                'slider':       getattr(_gui,'slider',       lambda *a,**k: None),
                'badge':        getattr(_gui,'badge',        lambda *a,**k: None),
                'barra_status': getattr(_gui,'barra_status', lambda *a,**k: None),
                'grafico':      getattr(_gui,'grafico',      lambda *a,**k: None),
                'arvore':       getattr(_gui,'arvore',       lambda *a,**k: None),
                'busca':        getattr(_gui,'busca',        lambda *a,**k: None),
                'calendario':   getattr(_gui,'calendario',   lambda *a,**k: None),
                'modal':        getattr(_gui,'modal',        lambda *a,**k: None),
                'splitter':     getattr(_gui,'splitter',     lambda *a,**k: None),
                'cor_hex':      getattr(_gui,'cor_hex',      lambda v: v),
                'icone':        getattr(_gui,'icone',        lambda v: v),"""
    for m in MARCADORES:
        if m in content:
            content = content.replace(m, m + NOVOS, 1)
            print("  OK: métodos modernos registrados")
            break

# ── Valida e salva ────────────────────────────────────────────
try:
    ast.parse(content)
except SyntaxError as e:
    print(f"\n❌ ERRO de sintaxe: {e}")
    print("   O arquivo NÃO foi modificado.")
    sys.exit(1)

with open(arq, 'w', encoding='utf-8') as f:
    f.write(content)

# ── Verifica resultado ────────────────────────────────────────
print("\nVerificação final:")
checks = [
    ('kwargs em _eval_call',   'kw_args' in content),
    ('kwargs em _call_fn',     'kwargs=None' in content),
    ('barra_status registrado','barra_status' in content),
    ('AdvakGUIModern ativo',   'AdvakGUIModern' in content),
]
ok_count = 0
for nome, ok in checks:
    print(f"  {'✓' if ok else '✗'} {nome}")
    if ok: ok_count += 1

print(f"\n{ok_count}/{len(checks)} verificações OK")
if ok_count == len(checks):
    print("\n✅ Tudo corrigido!")
    print("   Execute: python advak.py projetos run gui_moderno_demo.dk")
else:
    print("\n⚠️  Substitua manualmente o advak_interpreter.py pelo arquivo baixado.")
