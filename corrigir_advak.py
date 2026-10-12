#!/usr/bin/env python3
"""
Advak — Script de Atualização Automática
Execute UMA vez: python corrigir_advak.py
Corrige advak_parser.py e advak_gui.py no lugar
"""
import os, sys, re, ast

BASE = os.path.dirname(os.path.abspath(__file__))
erros = []
ok    = []

def patch(nome_arquivo, descricao, old, new):
    path = os.path.join(BASE, nome_arquivo)
    if not os.path.exists(path):
        erros.append(f"  NÃO ENCONTRADO: {nome_arquivo}")
        return False
    with open(path, encoding='utf-8') as f:
        content = f.read()
    if old not in content:
        # já aplicado ou versão diferente
        if new.strip()[:30] in content:
            ok.append(f"  JÁ ATUALIZADO: {nome_arquivo} — {descricao}")
        else:
            erros.append(f"  FALHA: {nome_arquivo} — {descricao} (trecho não encontrado)")
        return False
    content = content.replace(old, new, 1)
    # Valida sintaxe Python
    try:
        ast.parse(content)
    except SyntaxError as e:
        erros.append(f"  ERRO SINTAXE: {nome_arquivo} — {e}")
        return False
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    ok.append(f"  OK: {nome_arquivo} — {descricao}")
    return True

print("\n╔══════════════════════════════════════════════╗")
print("║   Advak — Correção Automática de Arquivos   ║")
print("╚══════════════════════════════════════════════╝\n")

# ── PATCH 1: advak_parser.py — suporte a 'implementa' ────────────
patch('advak_parser.py',
    "suporte a 'implementa' em classe",
    # OLD — parse_class_decl sem implementa
    "        if self.match('herda', 'extends'):\n            superclass = self.consume('IDENT')['value']\n        self.consume('LCURLY')",
    # NEW — com implementa/implements
    """        if self.match('herda', 'extends'):
            superclass = self.consume('IDENT')['value']
        # suporte a: implementa / implements
        interfaces = []
        t = self.peek()
        if t and t['value'] in ('implementa', 'implements'):
            self.advance()
            interfaces.append(self.consume('IDENT')['value'])
            while self.match('COMMA'):
                interfaces.append(self.consume('IDENT')['value'])
        self.consume('LCURLY')"""
)

# ── PATCH 2: advak_parser.py — retorno com interfaces ────────────
patch('advak_parser.py',
    "retorno de class_decl com interfaces",
    "return {'type': 'class_decl', 'name': name, 'superclass': superclass, 'methods': methods}",
    "return {'type': 'class_decl', 'name': name, 'superclass': superclass, 'methods': methods, 'interfaces': interfaces if 'interfaces' in dir() else []}"
)

# ── PATCH 3: advak_parser.py — suporte a 'interface' ─────────────
patch('advak_parser.py',
    "keyword interface no parse_statement",
    "        if v in ('classe', 'class'):\n            return self.parse_class_decl()",
    """        if v in ('interface',):
            return self.parse_interface_decl()
        if v in ('classe', 'class'):
            return self.parse_class_decl()"""
)

# ── PATCH 4: advak_parser.py — método parse_interface_decl ───────
patch('advak_parser.py',
    "método parse_interface_decl",
    "    def parse_class_decl(self):",
    """    def parse_interface_decl(self):
        self.advance()  # 'interface'
        nome = self.consume('IDENT')['value']
        extends = []
        if self.peek() and self.peek()['value'] in ('extends', 'herda'):
            self.advance()
            extends.append(self.consume('IDENT')['value'])
            while self.match('COMMA'):
                extends.append(self.consume('IDENT')['value'])
        self.consume('LCURLY')
        membros = []
        while not self.check('RCURLY'):
            if self.peek() is None: break
            t = self.peek()
            if t['type'] in ('IDENT', 'KEYWORD'):
                membro_nome = self.advance()['value']
                if self.check('LPAREN'):
                    params = self.parse_params()
                    self.match('SEMICOLON')
                    membros.append({'tipo': 'metodo', 'nome': membro_nome, 'params': params})
                else:
                    self.match('SEMICOLON')
                    membros.append({'tipo': 'prop', 'nome': membro_nome})
            else:
                self.advance()
        self.consume('RCURLY')
        return {'type': 'interface_decl', 'nome': nome, 'extends': extends, 'membros': membros}

    def parse_class_decl(self):"""
)

# ── PATCH 5: advak_interpreter.py — handler interface_decl ───────
patch('advak_interpreter.py',
    "handler interface_decl no interpretador",
    "        elif t == 'class_decl':\n            sup = scope.get(node['superclass']) if node['superclass'] else Non",
    """        elif t == 'interface_decl':
            iface = {
                '__tipo__':    'interface',
                '__nome__':    node['nome'],
                '__membros__': node.get('membros', []),
                '__extends__': node.get('extends', []),
            }
            scope.declare(node['nome'], iface)
            return iface

        elif t == 'class_decl':
            sup = scope.get(node['superclass']) if node['superclass'] else Non"""
)

# ── PATCH 6: advak_interpreter.py — validação de interfaces ──────
patch('advak_interpreter.py',
    "validação de interfaces na criação de classe",
    "            scope.declare(node['name'], AdvakClass(node['name'], sup, methods))",
    """            klass = AdvakClass(node['name'], sup, methods)
            scope.declare(node['name'], klass)
            for iface_nome in node.get('interfaces', []):
                try:
                    iface = scope.get(iface_nome)
                    if isinstance(iface, dict) and iface.get('__tipo__') == 'interface':
                        faltando = [m['nome'] for m in iface.get('__membros__', [])
                                    if m['tipo'] == 'metodo' and m['nome'] not in methods
                                    and m['nome'] != 'construtor']
                        if faltando:
                            raise Exception(f"Classe '{node['name']}' não implementa os métodos da interface '{iface_nome}': {faltando}")
                except Exception as e:
                    if 'não implementa' in str(e): raise
            """
)

# ── PATCH 7: advak_gui.py — frame.posicionar() ───────────────────
patch('advak_gui.py',
    "método posicionar() no frame",
    """        widget = tk.Frame(p, **kwargs)
        widget.pack(fill='both', expand=True, pady=4)
        widget._frame = widget
        return widget""",
    """        widget = tk.Frame(p, **kwargs)
        widget.pack(fill='both', expand=True, pady=4)
        widget._frame = widget
        def _pos(lado=None, preencher=None, expandir=False,
                 x=None, y=None, largura=None, altura=None,
                 pady=4, padx=4, ancora=None):
            widget.pack_forget()
            if lado:
                widget.pack(side=lado, fill=preencher or 'both',
                           expand=expandir, padx=padx, pady=pady)
            else:
                widget.pack(fill=preencher or 'both', expand=expandir,
                           padx=padx, pady=pady)
        widget.posicionar = _pos
        return widget"""
)

# ── PATCH 8: advak_gui.py — frame_horizontal.posicionar() ────────
patch('advak_gui.py',
    "método posicionar() no frame_horizontal",
    """        widget = tk.Frame(p)
        widget.pack(fill='x', pady=4)
        widget._frame = widget
        # Override pack para widgets filhos usarem side='left'
        widget._lado = 'left'
        return widget""",
    """        widget = tk.Frame(p)
        widget.pack(fill='x', pady=4)
        widget._frame = widget
        widget._lado  = 'left'
        def _pos_h(lado=None, preencher=None, expandir=False,
                   x=None, y=None, largura=None, altura=None,
                   pady=4, padx=4, ancora=None):
            widget.pack_forget()
            widget.pack(side=lado or 'left', fill=preencher or 'x',
                       expand=expandir, padx=padx, pady=pady)
        widget.posicionar = _pos_h
        return widget"""
)

# ── Resultado ─────────────────────────────────────────────────────
print("Resultado:")
for m in ok:    print(m)
for m in erros: print(m)

total_ok    = len(ok)
total_erro  = len(erros)
print(f"\n{total_ok} patches aplicados, {total_erro} com problemas.")

if total_erro == 0:
    print("\n✅ Tudo atualizado! Execute normalmente:")
    print("   python advak.py projetos run interfaces_exemplo.dk")
    print("   python advak.py projetos run advak_studio.dk")
else:
    print("\n⚠️  Alguns patches falharam — verifique os erros acima.")
    print("   Tente substituir os .py manualmente pelos arquivos baixados.")
