#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
advak_mini.py — Interpretador Advak 5.1 otimizado para startup rápido.
Usado pelo Studio para execução de código sem os módulos pesados.
Startup: ~100ms vs ~4.5s do advak.py completo.
"""
import asyncio, math, re, json, os, sys

sys.setrecursionlimit(max(5000, sys.getrecursionlimit()))

# Apenas os módulos essenciais (rápidos)
from advak_db import AdvakDB
from advak_lexer import AdvakLexer
from advak_parser import Parser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Configurar encoding UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


def executar(caminho_arquivo):
    """Executa um arquivo .dk com o interpretador Advak."""
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo \'{caminho_arquivo}\' não encontrado")
        return 1

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return 1

    try:
        tokens = AdvakLexer(source).tokenize()
        ast    = Parser(tokens).parse()
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe: {e}")
        return 1
    except Exception as e:
        print(f"❌ Erro ao analisar: {e}")
        return 1

    try:
        # Import do interpretador completo mas já carregado em memória
        from advak_interpreter import AdvakInterpreter
        interp = AdvakInterpreter(ast, db_config=None)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(interp.interpret())
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for t in pending:
                    t.cancel()
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            loop.close()
        return 0
    except Exception as e:
        tn = type(e).__name__
        trad = {
            'RecursionError':    'Recursão muito profunda',
            'MemoryError':       'Memória insuficiente',
            'KeyboardInterrupt': 'Interrompido pelo usuário',
        }
        print(f"❌ {trad.get(tn, tn)}: {e}")
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python advak_mini.py <arquivo.dk>")
        sys.exit(1)
    sys.exit(executar(sys.argv[1]))
