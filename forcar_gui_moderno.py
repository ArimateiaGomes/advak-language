#!/usr/bin/env python3
"""
Advak — FORÇA atualização completa do GUI Moderno
Execute: python forcar_gui_moderno.py
"""
import os, sys, re, ast

BASE = os.path.dirname(os.path.abspath(__file__))
arq  = os.path.join(BASE, 'advak_interpreter.py')

print("\n╔══════════════════════════════════════════════╗")
print("║  Advak — Forçando GUI Moderno 4.0           ║")
print("╚══════════════════════════════════════════════╝\n")

if not os.path.exists(arq):
    print("❌ advak_interpreter.py não encontrado!")
    sys.exit(1)

with open(arq, encoding='utf-8') as f:
    content = f.read()

# ── Passo 1: garante que usa AdvakGUIModern ───────────────────
if 'AdvakGUIModern' not in content:
    content = content.replace(
        "from advak_gui import AdvakGUI\n            _gui = AdvakGUI()",
        "try:\n                from advak_gui_modern import AdvakGUIModern\n                _gui = AdvakGUIModern()\n            except Exception:\n                from advak_gui import AdvakGUI\n                _gui = AdvakGUI()"
    )
    print("  OK: AdvakGUIModern ativado")
else:
    print("  JA OK: AdvakGUIModern já ativo")

# ── Passo 2: localiza o bloco gui dict e substitui COMPLETO ──
NOVOS_METODOS = """
                # ── Modernos (GUI 4.0) ────────────────────────────────
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

# Verifica se barra_status já está registrado
if "'barra_status'" in content:
    print("  JA OK: barra_status já registrado")
else:
    # Insere após 'tema'
    marcadores = [
        ("'tema':         _gui.tema,", "'tema':         _gui.tema," + NOVOS_METODOS),
        ("'tema':         lambda t: _gui.tema(t),", "'tema':         lambda t: _gui.tema(t)," + NOVOS_METODOS),
        ("'atualizar':    _gui.atualizar,", "'atualizar':    _gui.atualizar," + NOVOS_METODOS),
    ]
    aplicado = False
    for old, new in marcadores:
        if old in content and not aplicado:
            content = content.replace(old, new, 1)
            aplicado = True
            print("  OK: métodos modernos registrados")
            break
    if not aplicado:
        print("  AVISO: não encontrou ponto de inserção — tentando método direto")
        # Último recurso: encontra 'tema' no bloco gui e insere depois
        idx = content.rfind("'tema'")
        if idx > 0:
            # Acha o fim da linha
            fim_linha = content.find('\n', idx)
            content = content[:fim_linha] + NOVOS_METODOS + content[fim_linha:]
            print("  OK: inserido via posição direta")

# ── Passo 3: valida e salva ───────────────────────────────────
try:
    ast.parse(content)
    with open(arq, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  OK: arquivo salvo e válido")
except SyntaxError as e:
    print(f"  ❌ ERRO de sintaxe — arquivo NÃO foi salvo: {e}")
    sys.exit(1)

# ── Passo 4: verifica resultado ───────────────────────────────
with open(arq, encoding='utf-8') as f:
    final = f.read()

metodos = ['barra_status','toast','card','slider','badge',
           'grafico','arvore','busca','modal','splitter','toggle']
print("\nVerificação final:")
todos_ok = True
for m in metodos:
    ok = f"'{m}'" in final
    print(f"  {'✓' if ok else '✗'} {m}")
    if not ok: todos_ok = False

print()
if todos_ok:
    print("✅ GUI Moderno 4.0 totalmente ativo!")
    print("   Execute: python advak.py projetos run gui_moderno_demo.dk")
else:
    print("⚠️  Alguns métodos não foram registrados.")
    print("   Substitua manualmente o advak_interpreter.py pelo arquivo baixado.")
