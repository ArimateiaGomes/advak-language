#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testa studio_executar() com widgets tkinter reais.
Execute: python debug_studio_executar.py
"""
import sys, os, time, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== TESTE: studio_executar() com tkinter real ===")
print()

import tkinter as tk

root = tk.Tk()
root.title("Teste studio_executar")
root.geometry("500x350")

lbl = tk.Label(root, text="Status: aguardando...", fg="blue")
lbl.pack(pady=5)

console = tk.Text(root, bg='#1e1e1e', fg='#d4d4d4', height=15)
console.pack(fill='both', expand=True, padx=5, pady=5)

flag = [True]
resultado_final = []

def mostrar(txt):
    console.configure(state='normal')
    console.insert('end', txt)
    console.see('end')
    console.configure(state='disabled')

mostrar("Iniciando teste...\n")

import advak_gui_modern
advak_gui_modern._root_ref = root

codigo_teste = 'imprimir("Olá do teste!")\nimprimir(1+2+3)\nimprimir(tipo([]))\n'

def rodar_teste():
    import asyncio, builtins
    from advak_interpreter import AdvakInterpreter
    from advak_lexer import AdvakLexer
    from advak_parser import Parser

    builtins.print = lambda *a, **k: None  # suprimir output interno

    async def run():
        code = f'studio_executar({repr(codigo_teste)}, c_w, s_w, f_w)'
        t = AdvakLexer('seja x=1').tokenize()
        a = Parser(t).parse()
        interp = AdvakInterpreter(a)
        interp.global_scope.declare('c_w', console)
        interp.global_scope.declare('s_w', lbl)
        interp.global_scope.declare('f_w', flag)
        t2 = AdvakLexer(code).tokenize()
        a2 = Parser(t2).parse()
        interp2 = AdvakInterpreter(a2)
        interp2.global_scope = interp.global_scope
        await asyncio.wait_for(interp2.interpret(), timeout=15)

    asyncio.run(run())
    builtins.print = print
    print("studio_executar() chamado com sucesso")

def verificar_resultado():
    txt = console.get('1.0', 'end').strip()
    resultado_final.append(txt)
    print()
    print("=== RESULTADO ===")
    print(f"Console: '{txt[:200]}'")
    print(f"Status: '{lbl.cget('text')}'")
    print(f"flag: {flag[0]}")
    if 'Olá do teste!' in txt:
        print("✅ studio_executar() FUNCIONOU!")
    else:
        print("❌ Resultado não apareceu no console")
    root.quit()

root.after(500, rodar_teste)     # Executar após 0.5s
root.after(10000, verificar_resultado)  # Verificar após 10s

print("Janela aberta. Aguardando 10s...")
root.mainloop()
try: root.destroy()
except: pass
print("Teste concluído.")
input("Pressione ENTER para fechar...")
