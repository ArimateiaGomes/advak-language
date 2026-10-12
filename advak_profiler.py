#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
advak_profiler.py — Profiler de performance para Advak 5.0

Uso:  advak --perfil arquivo.dk
"""
import time, asyncio, sys, collections
from pathlib import Path

class AdvakProfiler:
    def __init__(self):
        self._chamadas  = collections.defaultdict(int)
        self._tempos    = collections.defaultdict(float)
        self._ativo     = False
    
    def iniciar(self):
        self._ativo = True
        self._inicio = time.perf_counter()
    
    def registrar(self, nome, tempo_ms):
        if self._ativo:
            self._chamadas[nome] += 1
            self._tempos[nome]   += tempo_ms
    
    def relatorio(self):
        total = time.perf_counter() - self._inicio
        print(f"\n  ⏱️  PERFIL DE EXECUÇÃO")
        print(f"  {'─'*55}")
        print(f"  {'Função':35} {'Chamadas':>8} {'Total ms':>10} {'Média ms':>10}")
        print(f"  {'─'*55}")
        
        itens = sorted(self._tempos.items(), key=lambda x: x[1], reverse=True)
        for nome, tempo in itens[:20]:
            chamadas = self._chamadas[nome]
            media    = tempo / chamadas if chamadas else 0
            print(f"  {nome:35} {chamadas:>8} {tempo:>10.2f} {media:>10.4f}")
        
        print(f"  {'─'*55}")
        print(f"  Tempo total: {total*1000:.1f}ms")

_profiler_global = AdvakProfiler()

def perfil_ativo():
    return _profiler_global

if __name__ == '__main__':
    print("Use: advak --perfil arquivo.dk")
