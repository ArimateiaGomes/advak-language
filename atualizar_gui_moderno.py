#!/usr/bin/env python3
"""
Advak — Atualiza GUI para versão moderna
Execute: python atualizar_gui_moderno.py
"""
import os, sys, ast

BASE = os.path.dirname(os.path.abspath(__file__))

def patch(arquivo, descricao, old, new):
    path = os.path.join(BASE, arquivo)
    if not os.path.exists(path):
        print(f"  NAO ENCONTRADO: {arquivo}"); return False
    with open(path, encoding='utf-8') as f: c = f.read()
    if old not in c:
        if new.strip()[:40] in c:
            print(f"  JA ATUALIZADO: {descricao}"); return True
        print(f"  FALHA: {descricao}"); return False
    c = c.replace(old, new, 1)
    try: ast.parse(c)
    except SyntaxError as e:
        print(f"  ERRO SINTAXE: {e}"); return False
    with open(path, 'w', encoding='utf-8') as f: f.write(c)
    print(f"  OK: {descricao}"); return True

print("\n╔══════════════════════════════════════════════╗")
print("║  Advak — Ativando GUI Moderno 4.0           ║")
print("╚══════════════════════════════════════════════╝\n")

# Patch 1: usa AdvakGUIModern no interpretador
patch('advak_interpreter.py',
    'Ativa GUI Modern no interpretador',
    """        try:
            from advak_gui import AdvakGUI
            _gui = AdvakGUI()""",
    """        try:
            try:
                from advak_gui_modern import AdvakGUIModern
                _gui = AdvakGUIModern()
            except Exception:
                from advak_gui import AdvakGUI
                _gui = AdvakGUI()"""
)

# Patch 2: adiciona todos os métodos modernos ao dict gui
patch('advak_interpreter.py',
    'Registra metodos modernos no dict gui',
    "                'atualizar':    _gui.atualizar,\n                'tema':         _gui.tema,",
    """                'atualizar':    _gui.atualizar,
                'tema':         _gui.tema,
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
)

# Verifica se matplotlib está instalado
print("\nVerificando dependências...")
try:
    import matplotlib
    print(f"  OK: matplotlib {matplotlib.__version__}")
except ImportError:
    print("  FALTANDO: matplotlib")
    print("  Execute: pip install matplotlib")

try:
    from PIL import Image
    print("  OK: Pillow (PIL)")
except ImportError:
    print("  AVISO: Pillow não instalado (opcional para imagens)")
    print("  Execute: pip install pillow")

print("\n✅ GUI Moderno ativado!")
print("   Execute: python advak.py projetos run gui_moderno_demo.dk")
