#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mede quais imports do advak.py demoram mais.
Execute: python medir_imports.py
"""
import subprocess, sys, os, re, time

pasta = os.path.dirname(os.path.abspath(__file__))
os.chdir(pasta)

# Criar arquivo de teste
with open('_teste.dk', 'w', encoding='utf-8') as f:
    f.write('imprimir("TESTE_OK")\n')

print("Medindo imports... aguarde ~5s")
print()

# Rodar com importtime
resultado = subprocess.run(
    [sys.executable, '-X', 'importtime', 'advak.py', '_teste.dk'],
    capture_output=True, timeout=60, cwd=pasta
)

stderr = resultado.stderr.decode('utf-8', errors='replace')
stdout = resultado.stdout.decode('utf-8', errors='replace')

print(f"Saida: {stdout.strip()}")
print()

# Parsear import times
dados = []
for linha in stderr.split('\n'):
    m = re.search(r'import time:\s+(\d+)\s+\|\s+(\d+)\s+\|\s+(.+)', linha)
    if m:
        t_proprio = int(m.group(1))
        t_total   = int(m.group(2))
        nome      = m.group(3).strip()
        dados.append((t_proprio, t_total, nome))

# Ordenar por tempo proprio (mais lento primeiro)
dados.sort(reverse=True)

print("=== TOP 20 IMPORTS MAIS LENTOS (microsegundos) ===")
print(f"{'Proprio':>10}  {'Total':>10}  Modulo")
print("-" * 60)
for tp, tt, nome in dados[:20]:
    print(f"{tp:>10,}  {tt:>10,}  {nome}")

total_s = sum(tp for tp, tt, nome in dados) / 1_000_000
print(f"\nTempo total de imports: {total_s:.2f}s")

# Salvar
with open('import_times.txt', 'w', encoding='utf-8') as f:
    f.write(stderr)
print("\nArquivo completo salvo em: import_times.txt")

try:
    os.remove('_teste.dk')
except:
    pass

input("\nPressione ENTER para fechar...")
