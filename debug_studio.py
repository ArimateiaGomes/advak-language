#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug: testa passo a passo o que acontece ao pressionar F5.
Execute: python debug_studio.py
"""
import sys, os, subprocess, time, threading, queue

print("="*60)
print("DEBUG DO STUDIO — testando execução passo a passo")
print("="*60)

pasta = os.path.dirname(os.path.abspath(__file__))
os.chdir(pasta)
print(f"\n1. Pasta: {pasta}")
print(f"2. Python: {sys.executable}")

# Teste 1: subprocess simples
print("\n--- TESTE 1: subprocess.run() ---")
codigo = 'imprimir("TESTE_OK")\nimprimir(1+2+3)\n'
arq = os.path.join(pasta, '_debug_temp.dk')
with open(arq, 'w', encoding='utf-8') as f:
    f.write(codigo)

env = dict(os.environ)
env['PYTHONIOENCODING'] = 'utf-8'
env['PYTHONUTF8'] = '1'

t0 = time.time()
r = subprocess.run(
    [sys.executable, os.path.join(pasta, 'advak.py'), '_debug_temp.dk'],
    capture_output=True, timeout=15, env=env, cwd=pasta
)
t1 = time.time()

def dec(b):
    for enc in ('utf-8','utf-8-sig','cp1252','latin-1'):
        try: return b.decode(enc)
        except: pass
    return b.decode('utf-8', errors='replace')

saida = dec(r.stdout)
erro = dec(r.stderr)
print(f"   Tempo: {t1-t0:.2f}s")
print(f"   Código de saída: {r.returncode}")
print(f"   Stdout: '{saida.strip()}'")
if erro.strip():
    print(f"   Stderr: '{erro.strip()[:100]}'")

if 'TESTE_OK' in saida:
    print("   ✅ subprocess.run() FUNCIONA!")
else:
    print("   ❌ subprocess.run() FALHOU!")

# Teste 2: arquivo de saída
print("\n--- TESTE 2: arquivo de saída ---")
arq_saida = os.path.join(pasta, '_debug_output.txt')
resultado = [None]

def rodar_em_thread():
    try:
        r2 = subprocess.run(
            [sys.executable, os.path.join(pasta, 'advak.py'), '_debug_temp.dk'],
            capture_output=True, timeout=15, env=env, cwd=pasta
        )
        saida2 = dec(r2.stdout)
        with open(arq_saida, 'w', encoding='utf-8') as f:
            f.write(saida2 or '__SEM_SAIDA__')
        resultado[0] = saida2
        print(f"   Thread terminou. Saída: '{saida2.strip()}'")
    except Exception as e:
        print(f"   Thread ERRO: {e}")
        with open(arq_saida, 'w', encoding='utf-8') as f:
            f.write(f'ERRO: {e}')

t = threading.Thread(target=rodar_em_thread, daemon=True)
t.start()

print("   Thread iniciada. Aguardando (max 10s)...")
for i in range(50):
    if os.path.exists(arq_saida):
        conteudo = open(arq_saida, encoding='utf-8').read()
        print(f"   Arquivo criado após {i*0.2:.1f}s: '{conteudo.strip()}'")
        break
    time.sleep(0.2)
else:
    print("   ❌ Arquivo não criado em 10s!")

# Teste 3: jan.after() simulado
print("\n--- TESTE 3: tkinter after() ---")
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    
    resultado_after = []
    
    def callback():
        resultado_after.append("after_executou")
        root.quit()
    
    root.after(100, callback)
    root.mainloop()
    
    if resultado_after:
        print("   ✅ root.after() FUNCIONA!")
    else:
        print("   ❌ root.after() NÃO executou!")
    root.destroy()
except Exception as e:
    print(f"   ❌ tkinter erro: {e}")

# Limpeza
for f in [arq, arq_saida]:
    try: os.remove(f)
    except: pass

print("\n" + "="*60)
print("DEBUG CONCLUÍDO")
print("="*60)
input("\nPressione ENTER para fechar...")
