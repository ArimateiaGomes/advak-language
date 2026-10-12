@echo off
echo imprimir("TESTE") > _teste.dk
python -X importtime advak.py _teste.dk 2> import_times.txt
echo.
echo === TOP 20 IMPORTS MAIS LENTOS ===
python -c "
import re
linhas = open('import_times.txt', encoding='utf-8', errors='replace').readlines()
dados = []
for l in linhas:
    m = re.search(r'import time:\s+(\d+)\s+\|', l)
    if m:
        t = int(m.group(1))
        nome = l.split('|')[-1].strip() if '|' in l else l.strip()
        dados.append((t, nome))
dados.sort(reverse=True)
for t, n in dados[:20]:
    print(f'{t:8d} us  {n}')
"
del _teste.dk
pause
