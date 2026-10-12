#!/usr/bin/env python3
"""SALVAR_PYX.py - Testa pipeline completo do Cython."""
import os, sys, re, py_compile, subprocess
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
FIB   = os.path.join(BASE, 'projetos', 'fibonacci.dk')
SAIDA = os.path.join(BASE, 'dist', 'fibonacci_DEBUG.pyx')
os.makedirs(os.path.join(BASE, 'dist'), exist_ok=True)

print("\n" + "="*60)
print("  SALVAR_PYX — Pipeline COMPLETO do Cython")
print("="*60)

from advak_nativo import TranspiladorPython, CompiladorCython
import inspect
cc = CompiladorCython()
src = inspect.getsource(cc.compilar)
print(f"  compilar(): {len(src)} chars")
print(f"  fixar_para_cython: {'fixar_para_cython' in src}")

tp = TranspiladorPython()
python_code = tp.transpilar(open(FIB, encoding='utf-8').read(), 'fibonacci')
print(f"  Python: {len(python_code)} chars")

def tornar_ascii_seguro(s):
    out = []
    for linha in s.split('\n'):
        if not any(ord(c)>127 for c in linha):
            out.append(linha); continue
        nova=[]; em=False; qch=None; i=0
        while i<len(linha):
            ch=linha[i]
            if not em and ch in('"',"'"):em=True;qch=ch;nova.append(ch)
            elif em and ch==qch:em=False;nova.append(ch)
            elif em and ord(ch)>127:
                cp=ord(ch)
                nova.append(f'\\u{cp:04x}' if cp<=0xFFFF else f'\\U{cp:08x}')
            else:nova.append(ch)
            i+=1
        out.append(''.join(nova))
    return '\n'.join(out)

def fixar_para_cython(s):
    IGNORE = {'from __future__ import annotations','import asyncio',
              'import json','import os','import re','import sys'}
    BUILTINS = {'True','False','None','int','str','float','bool','list','dict','tuple','set'}
    lins=s.split('\n'); out=[]; i=0
    while i<len(lins):
        l=lins[i]
        if l.strip() in IGNORE or 'asyncio.run(' in l:
            i+=1; continue
        m=re.match(r'^(\s*)(\w+)\s*=\s*([A-Z][A-Za-z0-9_]*)\s*$',l)
        if m:
            indent,var,val=m.group(1),m.group(2),m.group(3)
            if val not in BUILTINS:
                decl=any(re.search(r'\b'+re.escape(val)+r'\b',x)
                         for x in lins[:i] if 'def ' in x or '=' in x)
                if not decl:
                    out.append(f'{indent}{var} = None  # {val} ADT')
                    i+=1; continue
        m2=re.match(r'^(\s*)for (\w+) in (\w+)\(\):',l)
        if m2:
            fn=m2.group(3)
            fb='\n'.join(lins)
            if f'def {fn}(' in fb:
                fs=fb[fb.find(f'def {fn}('):fb.find(f'def {fn}(')+300]
                if 'pass  # [yield]' in fs:
                    out.append(f'{m2.group(1)}pass  # Generator {fn} ignorado')
                    nv=len(l)-len(l.lstrip()); i+=1
                    while i<len(lins):
                        p=lins[i]
                        if not p.strip(): i+=1; break
                        if p.strip() and len(p)-len(p.lstrip())<=nv: break
                        i+=1
                    continue
        if l.strip() in ('print(f"")','print(f\'\')'):
            indent_p = l[:len(l)-len(l.lstrip())]
            out.append(f'{indent_p}print("")'); i+=1; continue
        out.append(l); i+=1
    return '\n'.join(out)

python_safe   = tornar_ascii_seguro(python_code)
python_cython = fixar_para_cython(python_safe)
print(f"  Apos fixar: {len(python_cython)} chars")

cython_code = (
    "# -*- coding: utf-8 -*-\n"
    "# cython: language_level=3\n"
    "# cython: boundscheck=False\n"
    "# Modulo: fibonacci\n\n"
    + python_cython
)

has_inicio_raw  = bool(re.search(r'= Inicio\b', cython_code))
has_inicio_fixed= 'None  # ' in cython_code and 'ADT' in cython_code
print(f"  Inicio sem fix: {has_inicio_raw}")
print(f"  Inicio com ADT: {has_inicio_fixed}")

with open(SAIDA, 'w', encoding='utf-8') as f:
    f.write(cython_code)
print(f"\n  Salvo: {SAIDA}")

r = subprocess.run([sys.executable, '-m', 'cython', SAIDA,
                    '--output-file', SAIDA.replace('.pyx','_out.c')],
                   capture_output=True, text=True)
if r.returncode == 0:
    c = SAIDA.replace('.pyx','_out.c')
    print(f"  ✅ Cython OK! C: {c} ({os.path.getsize(c):,} bytes)")
    print("\n  Execute: python advak.py projetos\\testar_nuitka.dk")
else:
    err = (r.stderr or r.stdout or '').strip()
    print(f"  ❌ Cython falhou:\n  {err[:600]}")
    for m in re.finditer(r':(\d+):', err):
        ln=int(m.group(1))
        lines=cython_code.split('\n')
        for j in range(max(0,ln-3),min(len(lines),ln+3)):
            mk=">>>" if j+1==ln else "   "
            print(f"    {mk} L{j+1}: {lines[j]!r}")
        break
