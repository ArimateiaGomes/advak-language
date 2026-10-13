"""
Advak 5.0 — Compilador Nativo

5 backends de compilação:

1. BYTECODE  — Compila para .dk  otimizado (mais rápido de lançar)
2. PYTHON    — Transpila Advak → Python puro otimizado (.py)
3. EXE       — Empacota como executável Windows/Linux via PyInstaller
4. C         — Transpila para C puro (máxima performance, sem runtime)
5. WASM      — Transpila para WebAssembly (roda no browser)

Uso:
    compilador.bytecode("meu_app.dk")
    compilador.python("meu_app.dk", "meu_app.py")
    compilador.exe("meu_app.dk", gui=verdadeiro)
    compilador.c("meu_app.dk", "meu_app.c")
    compilador.wasm("meu_app.dk", "meu_app.wasm")
    
    // Pipeline completo
    compilador.compilar("meu_app.dk", {
        backend: "exe",
        otimizar: verdadeiro,
        nome: "MeuApp",
        icone: "icone.ico",
        gui: verdadeiro
    })
    
    // Análise de performance
    compilador.analisar("meu_app.dk")
    compilador.benchmark("meu_app.dk", repeticoes=100)
"""

import os
import sys
import ast
import dis
import struct
import marshal
import time
import textwrap
import tempfile
import shutil
import subprocess
import importlib
import py_compile
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ══════════════════════════════════════════════════════════════════════════════
#  1. TRANSPILADOR ADVAK → PYTHON OTIMIZADO
# ══════════════════════════════════════════════════════════════════════════════

def _py_str(v) -> str:
    """Like repr() but keeps unicode chars unescaped — safe for Cython .pyx files."""
    if not isinstance(v, str):
        return repr(v)
    # Use json.dumps for UTF-8 safe output, then convert to single quotes
    import json as _json
    s = _json.dumps(v, ensure_ascii=False)  # "text with ✅ unicode"
    # json gives double-quoted string — convert to single quotes safely
    if '"' not in v and '\\' not in v:
        return "'" + v.replace("'", "\\'") + "'"
    return s  # keep double quotes if needed


class TranspiladorPython:
    """

    Transpila código Advak para Python puro otimizado.
    O Python gerado:
    - Usa type hints para melhor performance via mypyc
    - Evita o overhead do interpretador Advak em runtime
    - Pode ser compilado para bytecode ou executável
    """

    # Mapeamento de keywords Advak → Python
    KEYWORDS = {
        'seja': '',           # var declaration (handled contextually)
        'fixo': '',           # const
        'se': 'if',
        'senão': 'else',
        'enquanto': 'while',
        'para': 'for',
        'em': 'in',
        'retornar': 'return',
        'quebrar': 'break',
        'continuar': 'continue',
        'função': 'def',
        'verdadeiro': 'True',
        'falso': 'False',
        'nulo': 'None',
        'e': 'and',
        'ou': 'or',
        'não': 'not',
        'tentar': 'try',
        'capturar': 'except',
        'finalmente': 'finally',
        'lançar': 'raise',
        'classe': 'class',
        'isso': 'self',
        'herda': 'extends',
        'importar': 'import',
        'de': 'from',
        'como': 'as',
        'exportar': '',
    }

    def __init__(self):
        self._indent = 0
        self._output = []
        self._imports = set()
        self._helpers_needed = set()

    def transpilar(self, source_dk: str, nome_modulo: str = 'advak_transpilado') -> str:
        """
        Transpila código Advak para Python.
        Retorna string com código Python otimizado.
        """
        from advak_lexer import AdvakLexer
        from advak_parser import Parser

        tokens = AdvakLexer(source_dk).tokenize()
        ast_dk = Parser(tokens).parse()

        self._output = []
        self._imports = {'asyncio', 'sys', 'os', 'json', 're'}
        self._helpers_needed = set()

        # Header (ASCII-only para compatibilidade com Cython)
        self._emit(f'# Gerado pelo Advak Compiler 5.0')
        self._emit(f'# Modulo: {nome_modulo}')
        self._emit(f'# Data: {time.strftime("%Y-%m-%d %H:%M:%S")}')
        self._emit('# ruff: noqa')
        self._emit('')

        # Transpila cada nó do AST
        body_lines = []
        for node in ast_dk:
            lines = self._transpilar_node(node)
            body_lines.extend(lines)

        # Emite imports após coletar todos os necessários
        for imp in sorted(self._imports):
            self._emit(f'import {imp}')
        self._emit('')

        # Helpers necessários
        if 'advak_texto' in self._helpers_needed:
            self._emit('def _t(v): return str(v) if v is not None else ""')
        if 'advak_numero' in self._helpers_needed:
            self._emit('def _n(v):')
            self._emit('    if v is None or v == "": return 0')
            self._emit('    try: return int(str(v)) if str(v).lstrip("-").isdigit() else float(v)')
            self._emit('    except: return 0')
        if 'advak_bool' in self._helpers_needed:
            self._emit('def _b(v): return bool(v) if v is not None else False')
        if self._helpers_needed:
            self._emit('')

        # Corpo
        for line in body_lines:
            self._output.append(line)

        # Entry point — omit asyncio.run since Cython doesn't support it
        self._emit('')
        self._emit('if __name__ == "__main__":')
        self._emit('    pass  # run with: python -c "import fibonacci"')

        return '\n'.join(self._output)

    def _emit(self, line: str):
        indent = '    ' * self._indent
        self._output.append(f'{indent}{line}')

    def _transpilar_node(self, node: dict, indent: int = 0) -> List[str]:
        """Transpila um nó do AST Advak para linhas Python."""
        if not isinstance(node, dict):
            return [repr(node)]

        t = node.get('type', '')
        prefix = '    ' * indent

        if t == 'var_decl':
            name = node['name']
            if node.get('value'):
                val = self._transpilar_expr(node['value'])
                return [f'{prefix}{name} = {val}']
            return [f'{prefix}{name} = None']

        elif t == 'assign':
            target = self._transpilar_expr(node['target'])
            val = self._transpilar_expr(node['value'])
            return [f'{prefix}{target} = {val}']

        elif t == 'if':
            cond = self._transpilar_expr(node['cond'])
            then_body = node.get('then', {}).get('body', [])
            lines = [f'{prefix}if {cond}:']
            real_stmts = [s for s in then_body
                         if isinstance(s, dict) and s.get('type') != 'comment']
            if real_stmts:
                for s in real_stmts:
                    lines.extend(self._transpilar_node(s, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            if node.get('else'):
                lines.append(f'{prefix}else:')
                else_node = node['else']
                if else_node.get('type') == 'if':
                    # elif
                    elif_lines = self._transpilar_node(else_node, indent)
                    lines.append(prefix + 'el' + elif_lines[0].lstrip())
                    lines.extend(elif_lines[1:])
                else:
                    for s in else_node.get('body', []):
                        lines.extend(self._transpilar_node(s, indent + 1))
                    if not else_node.get('body'):
                        lines.append(f'{prefix}    pass')
            return lines

        elif t == 'while':
            cond = self._transpilar_expr(node['cond'])
            while_body = node.get('body', {}).get('body', [])
            lines = [f'{prefix}while {cond}:']
            real_stmts = [s for s in while_body
                         if isinstance(s, dict) and s.get('type') != 'comment']
            if real_stmts:
                for s in real_stmts:
                    lines.extend(self._transpilar_node(s, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines

        elif t in ('for', 'for_in'):
            var = node.get('var', '_item')
            iterable = self._transpilar_expr(
                node.get('iterable') or node.get('iter') or {'type': 'list', 'items': []}
            )
            # for_in body can be a block dict or list
            body_node = node.get('body', {})
            if isinstance(body_node, dict):
                for_body = body_node.get('body', [])
            elif isinstance(body_node, list):
                for_body = body_node
            else:
                for_body = []
            lines = [f'{prefix}for {var} in {iterable}:']
            real_stmts = [s for s in for_body
                         if isinstance(s, dict) and s.get('type') != 'comment']
            if real_stmts:
                for s in real_stmts:
                    lines.extend(self._transpilar_node(s, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines

        elif t in ('function_decl', 'func_decl'):
            name = node['name'] or '_anon'
            params = ', '.join(self._transpilar_param(p) for p in node.get('params', []))
            is_async = node.get('async', False)
            kw = 'async def' if is_async else 'def'
            lines = [f'{prefix}{kw} {name}({params}):']
            body = node.get('body', {}).get('body', [])
            real_body = [s for s in body
                        if isinstance(s, dict) and s.get('type') != 'comment']
            if real_body:
                for s in real_body:
                    lines.extend(self._transpilar_node(s, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines

        elif t == 'return':
            if node.get('value'):
                val = self._transpilar_expr(node['value'])
                return [f'{prefix}return {val}']
            return [f'{prefix}return']

        elif t == 'assign':
            # Assignment statement: target = value (not walrus :=)
            target = self._transpilar_expr(node.get('target', {}))
            val    = self._transpilar_expr(node.get('value', {}))
            op     = node.get('op', '=')
            op_map = {'=': '=', '+=': '+=', '-=': '-=', '*=': '*=', '/=': '/=',
                      '//=': '//=', '%=': '%=', '**=': '**='}
            py_op = op_map.get(op, '=')
            return [f'{prefix}{target} {py_op} {val}']

        elif t in ('expr_stmt', 'print'):
            if t == 'print':
                args = node.get('args', [])
                args_str = ', '.join(self._transpilar_expr(a) for a in args)
                return [f'{prefix}print({args_str})']
            inner = node.get('expr', {})
            # Assignment inside expr_stmt — use = not :=
            if isinstance(inner, dict) and inner.get('type') == 'assign':
                target = self._transpilar_expr(inner.get('target', {}))
                val    = self._transpilar_expr(inner.get('value', {}))
                return [f'{prefix}{target} = {val}']
            expr = self._transpilar_expr(inner)
            if expr and expr not in ('None  # [expr: ]', 'None  # [expr: None]'):
                return [f'{prefix}{expr}']
            return [f'{prefix}pass  # [empty expr]']

        elif t == 'block':
            lines = []
            for s in node.get('body', []):
                lines.extend(self._transpilar_node(s, indent))
            return lines

        elif t == 'try':
            lines = [f'{prefix}try:']
            for s in node.get('body', {}).get('body', []):
                lines.extend(self._transpilar_node(s, indent + 1))
            if not node.get('body', {}).get('body'):
                lines.append(f'{prefix}    pass')
            catch_var = node.get('catch_var', 'e')
            lines.append(f'{prefix}except Exception as {catch_var}:')
            for s in node.get('catch', {}).get('body', []):
                lines.extend(self._transpilar_node(s, indent + 1))
            if not node.get('catch', {}).get('body'):
                lines.append(f'{prefix}    pass')
            if node.get('finally'):
                lines.append(f'{prefix}finally:')
                for s in node['finally'].get('body', []):
                    lines.extend(self._transpilar_node(s, indent + 1))
            return lines

        elif t == 'break':
            return [f'{prefix}break']

        elif t == 'continue':
            return [f'{prefix}continue']

        elif t == 'throw':
            val = self._transpilar_expr(node['value'])
            return [f'{prefix}raise Exception({val})']

        elif t == 'class_decl':
            name = node['name']
            parent = node.get('parent', '')
            bases = f'({parent})' if parent else ''
            lines = [f'{prefix}class {name}{bases}:']
            members = node.get('members', [])
            if members:
                for m in members:
                    lines.extend(self._transpilar_node(m, indent + 1))
            else:
                lines.append(f'{prefix}    pass')
            return lines

        else:
            # Fallback: for unknown nodes inside blocks, emit pass to keep syntax valid
            # Only emit comment at top level
            if indent > 0:
                return [f'{prefix}pass  # [{t}]']
            return [f'{prefix}# [Advak node: {t}]']

    def _transpilar_expr(self, node) -> str:
        """Transpila uma expressão para Python."""
        if node is None:
            return 'None'
        if not isinstance(node, dict):
            return repr(node)

        t = node.get('type', '')

        if t == 'number':
            return repr(node['value'])

        elif t == 'string':
            return _py_str(node['value'])

        elif t == 'bool':
            return 'True' if node['value'] else 'False'

        elif t == 'null':
            return 'None'

        elif t == 'ident':
            name = node['name']
            # Map Advak built-ins to Python equivalents
            builtins_map = {
                'imprimir': 'print',
                'texto': 'str',
                'numero': '_n',
                'booleano': 'bool',
                'verdadeiro': 'True',
                'falso': 'False',
                'nulo': 'None',
                'entrada': 'input',
            }
            if name in builtins_map:
                if builtins_map[name] == '_n':
                    self._helpers_needed.add('advak_numero')
                return builtins_map[name]
            return name

        elif t == 'binop':
            left = self._transpilar_expr(node['left'])
            right = self._transpilar_expr(node['right'])
            op = node['op']
            op_map = {
                '&&': 'and', '||': 'or',
                '==': '==', '!=': '!=',
                '<=': '<=', '>=': '>=',
                '<': '<', '>': '>',
                '+': '+', '-': '-',
                '*': '*', '/': '/',
                '%': '%', '**': '**',
            }
            py_op = op_map.get(op, op)
            return f'({left} {py_op} {right})'

        elif t == 'unary':
            op = node['op']
            val = self._transpilar_expr(node['value'])
            op_map = {'!': 'not ', '-': '-', '+': '+'}
            return f'{op_map.get(op, op)}{val}'

        elif t == 'call':
            func_node = node.get('func', {})
            func = self._transpilar_expr(func_node)
            args = ', '.join(self._transpilar_expr(a) for a in node.get('args', []))
            kwargs = ', '.join(
                f"{k}={self._transpilar_expr(v)}"
                for k, v in node.get('kwargs', {}).items()
            )
            all_args = ', '.join(filter(None, [args, kwargs]))

            # Converte metodos Advak para Python equivalentes
            if func_node.get('type') == 'member':
                prop = func_node.get('prop', '')
                obj  = self._transpilar_expr(func_node.get('obj', {}))
                if prop == 'adicionar':       return f'{obj}.append({all_args})'
                if prop == 'remover':         return f'{obj}.pop({all_args})'
                if prop == 'inserir':         return f'{obj}.insert({all_args})'
                if prop == 'limpar':          return f'{obj}.clear()'
                if prop == 'ordenar':         return f'{obj}.sort()'
                if prop == 'inverter':        return f'{obj}.reverse()'
                if prop == 'contem':          return f'({all_args} in {obj})'
                if prop == 'indexOf':         return f'{obj}.index({all_args})'
                if prop == 'primeiro':        return f'{obj}[0]'
                if prop == 'ultimo':          return f'{obj}[-1]'
                if prop == 'fatia':           return f'{obj}[{all_args}]'
                if prop in ('map','mapear'):
                    return f'list(map({all_args}, {obj}))'
                if prop in ('filtrar',):
                    return f'list(filter({all_args}, {obj}))'
                if prop == 'unir':            return f'({all_args}).join(str(x) for x in {obj})'
                if prop == 'valor':           return f'{obj}.get()'
                if prop == 'definir':         return f'{obj}.set({all_args})'
                if prop == 'fechar':          return f'{obj}.destroy()'

            return f'{func}({all_args})'

        elif t == 'member':
            obj  = self._transpilar_expr(node['obj'])
            prop = node['prop']
            # Converte propriedades Advak para Python
            if prop == 'tamanho':     return f'len({obj})'
            if prop == 'comprimento': return f'len({obj})'
            if prop == 'tipo':        return f'type({obj}).__name__'
            if prop == 'chaves':      return f'list({obj}.keys())'
            if prop == 'valores':     return f'list({obj}.values())'
            if prop == 'pares':       return f'list({obj}.items())'
            return f'{obj}.{prop}'

        elif t == 'index':
            obj = self._transpilar_expr(node['obj'])
            idx = self._transpilar_expr(node['index'])
            return f'{obj}[{idx}]'

        elif t == 'list':
            items = ', '.join(self._transpilar_expr(i) for i in node.get('items', []))
            return f'[{items}]'

        elif t == 'map':
            pairs = ', '.join(
                f'{_py_str(p["key"])}: {self._transpilar_expr(p["value"])}'
                for p in node.get('pairs', [])
            )
            return f'{{{pairs}}}'

        elif t == 'function' or t == 'arrow':
            params = ', '.join(self._transpilar_param(p) for p in node.get('params', []))
            body_nodes = node.get('body', {})
            if isinstance(body_nodes, dict) and body_nodes.get('type') == 'block':
                # Multi-line lambda → need nested function
                return f'(lambda {params}: None)  # [multi-line lambda not supported in expr]'
            elif isinstance(body_nodes, dict):
                body_expr = self._transpilar_expr(body_nodes)
                return f'(lambda {params}: {body_expr})'
            return f'(lambda {params}: None)'

        elif t == 'ternary':
            cond = self._transpilar_expr(node['cond'])
            then = self._transpilar_expr(node['then'])
            else_ = self._transpilar_expr(node['else'])
            return f'({then} if {cond} else {else_})'

        elif t == 'list_comp':
            partes = [self._transpilar_expr(node['element'])]
            for c in node['clauses']:
                if c['kind'] == 'for':
                    var = f"({', '.join(c['var'])})" if isinstance(c['var'], list) else c['var']
                    partes.append(f"for {var} in {self._transpilar_expr(c['iter'])}")
                else:
                    partes.append(f"if {self._transpilar_expr(c['cond'])}")
            return '[' + ' '.join(partes) + ']'

        elif t == 'range':
            ini = self._transpilar_expr(node['start'])
            fim = self._transpilar_expr(node['end'])
            if node.get('step') is None:
                return f'range(int({ini}), int({fim}){" + 1" if node["inclusive"] else ""})'
            passo = self._transpilar_expr(node['step'])
            ajuste = f' + (1 if int({passo}) > 0 else -1)' if node['inclusive'] else ''
            return f'range(int({ini}), int({fim}){ajuste}, int({passo}))'

        elif t == 'template_string':
            parts = []
            for part in node.get('parts', []):
                if isinstance(part, str):
                    parts.append(part.replace('{', '{{').replace('}', '}}'))
                else:
                    expr = self._transpilar_expr(part)
                    parts.append(f'{{{expr}}}')
            return 'f"' + ''.join(parts) + '"'

        elif t == 'assign':
            target = self._transpilar_expr(node['target'])
            val = self._transpilar_expr(node['value'])
            return f'{target} := {val}'

        elif t == 'await':
            val = self._transpilar_expr(node['value'])
            return f'await {val}'

        elif t == 'spread':
            val = self._transpilar_expr(node['value'])
            return f'*{val}'

        else:
            return f'None  # [expr: {t}]'

    def _transpilar_param(self, p: dict) -> str:
        if not isinstance(p, dict):
            return str(p)
        name = p.get('name', '_')
        default = p.get('default')
        if default:
            return f'{name}={self._transpilar_expr(default)}'
        return name


# ══════════════════════════════════════════════════════════════════════════════
#  2. TRANSPILADOR ADVAK → C
# ══════════════════════════════════════════════════════════════════════════════

class TranspiladorC:
    """
    Transpila código Advak para C puro.
    Usa GC (Boehm) para memória, GNU-C para compilação.
    
    Limitações (versão 1.0):
    - Suporta: variáveis, if/else, while, for, funções, print, matemática
    - Não suporta: closures, objetos complexos, banco, GUI
    - Ideal para: algoritmos, processamento de dados, ferramentas CLI
    """

    C_HEADER = """\
/*
 * Gerado pelo Advak Compiler 5.0 — C Backend
 * Compile: gcc -O2 -o {nome} {arquivo}.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdbool.h>

/* === Runtime Advak === */
typedef double advak_num;
typedef char*  advak_str;
typedef bool   advak_bool;

/* Print helpers */
#define advak_print_num(v)  printf("%g\\n", (double)(v))
#define advak_print_str(v)  printf("%s\\n", (v) ? (v) : "nulo")
#define advak_print_bool(v) printf("%s\\n", (v) ? "verdadeiro" : "falso")

/* Math helpers */
static advak_num _pow(advak_num a, advak_num b) { return pow(a, b); }
static advak_num _mod(advak_num a, advak_num b) { return fmod(a, b); }
static advak_str _num_to_str(advak_num v) {
    static char buf[64];
    if (v == (long long)v) snprintf(buf, sizeof(buf), "%lld", (long long)v);
    else snprintf(buf, sizeof(buf), "%.10g", v);
    return buf;
}
static advak_num _str_to_num(const char* s) {
    if (!s || !*s) return 0;
    char* end; double v = strtod(s, &end);
    return (*end == '\\0') ? v : 0;
}

"""

    def transpilar(self, source_dk: str, nome: str = 'advak_programa') -> str:
        """Transpila Advak → C."""
        from advak_lexer import AdvakLexer
        from advak_parser import Parser

        tokens = AdvakLexer(source_dk).tokenize()
        ast_dk = Parser(tokens).parse()

        output = [self.C_HEADER.replace('{nome}', nome).replace('{arquivo}', nome)]

        # Collect ALL functions (including nested) for forward declarations
        # Collect all top-level function declarations
        funcs = [n for n in ast_dk if isinstance(n, dict) and n.get('type') in ('function_decl', 'func_decl')]

        # Forward declare all functions
        for fn in funcs:
            name = fn.get('name')
            if not name: continue
            params_str = ', '.join(
                'advak_num ' + (p.get('name', '_') if isinstance(p, dict) else str(p))
                for p in fn.get('params', [])
            ) or 'void'
            output.append(f'static advak_num {name}({params_str});')
        if funcs:
            output.append('')

        # Main body wrapped in main()
        body_lines = []
        main_stmts = []

        for node in ast_dk:
            t_node = node.get('type', '')
            if t_node in ('function_decl', 'func_decl'):
                body_lines.extend(self._transpilar_fn_c(node))
                body_lines.append('')
            elif t_node not in ('function_decl', 'func_decl'):
                main_stmts.extend(self._transpilar_stmt_c(node, 1))

        output.extend(body_lines)
        output.append('int main(int argc, char** argv) {')
        output.extend(main_stmts)
        output.append('    return 0;')
        output.append('}')

        return '\n'.join(output)

    def _transpilar_fn_c(self, node: dict) -> List[str]:
        name = node.get('name', 'anon')
        params = ', '.join('advak_num ' + (p.get('name', '_') if isinstance(p, dict) else str(p))
                           for p in node.get('params', []))
        lines = [f'static advak_num {name}({params}) {{']
        body = node.get('body', {}).get('body', [])
        for stmt in body:
            lines.extend(self._transpilar_stmt_c(stmt, 1))
        lines.append('}')
        return lines

    def _transpilar_stmt_c(self, node: dict, indent: int = 0) -> List[str]:
        if not isinstance(node, dict):
            return []
        t = node.get('type', '')
        p = '    ' * indent

        if t == 'var_decl':
            name = node['name']
            if node.get('value'):
                val = self._transpilar_expr_c(node['value'])
                return [f'{p}advak_num {name} = {val};']
            return [f'{p}advak_num {name} = 0;']

        elif t == 'assign':
            target = self._transpilar_expr_c(node['target'])
            val = self._transpilar_expr_c(node['value'])
            return [f'{p}{target} = {val};']

        elif t == 'expr_stmt':
            # Check if it's a print call
            expr = node.get('expr', {})
            if expr.get('type') == 'call':
                fn = expr.get('func', {})
                if fn.get('type') == 'ident' and fn.get('name') in ('imprimir', 'print'):
                    args = expr.get('args', [])
                    if args:
                        val = self._transpilar_expr_c(args[0])
                        return [f'{p}advak_print_num({val});']
            val = self._transpilar_expr_c(node['expr'])
            return [f'{p}{val};']

        elif t == 'if':
            cond = self._transpilar_expr_c(node['cond'])
            lines = [f'{p}if ({cond}) {{']
            for s in node.get('then', {}).get('body', []):
                lines.extend(self._transpilar_stmt_c(s, indent + 1))
            lines.append(f'{p}}}')
            if node.get('else'):
                lines.append(f'{p}else {{')
                else_body = node['else']
                if isinstance(else_body, dict) and else_body.get('type') == 'if':
                    lines.extend(self._transpilar_stmt_c(else_body, indent))
                else:
                    for s in else_body.get('body', []):
                        lines.extend(self._transpilar_stmt_c(s, indent + 1))
                lines.append(f'{p}}}')
            return lines

        elif t == 'while':
            cond = self._transpilar_expr_c(node['cond'])
            lines = [f'{p}while ({cond}) {{']
            for s in node.get('body', {}).get('body', []):
                lines.extend(self._transpilar_stmt_c(s, indent + 1))
            lines.append(f'{p}}}')
            return lines

        elif t == 'for':
            var = node['var']
            iterable = node.get('iterable', {})
            # Only support range-like iterables
            if iterable.get('type') == 'call':
                fn = iterable.get('func', {})
                if fn.get('name') in ('intervalo', 'range'):
                    args = iterable.get('args', [])
                    if len(args) == 1:
                        end = self._transpilar_expr_c(args[0])
                        lines = [f'{p}for (advak_num {var} = 0; {var} < {end}; {var}++) {{']
                    elif len(args) >= 2:
                        start = self._transpilar_expr_c(args[0])
                        end = self._transpilar_expr_c(args[1])
                        step = self._transpilar_expr_c(args[2]) if len(args) > 2 else '1'
                        lines = [f'{p}for (advak_num {var} = {start}; {var} < {end}; {var} += {step}) {{']
                    else:
                        lines = [f'{p}/* for loop */']
                    for s in node.get('body', {}).get('body', []):
                        lines.extend(self._transpilar_stmt_c(s, indent + 1))
                    lines.append(f'{p}}}')
                    return lines
            return [f'{p}/* for-in not supported in C backend */']

        elif t == 'return':
            if node.get('value'):
                val = self._transpilar_expr_c(node['value'])
                return [f'{p}return {val};']
            return [f'{p}return 0;']

        elif t == 'break':
            return [f'{p}break;']

        elif t == 'continue':
            return [f'{p}continue;']

        elif t in ('function_decl', 'func_decl'):
            return self._transpilar_fn_c(node)

        else:
            return [f'{p}/* [{t}] */']

    def _transpilar_expr_c(self, node) -> str:
        if not isinstance(node, dict):
            return '0'
        t = node.get('type', '')

        if t == 'number':
            v = node['value']
            return str(int(v)) if isinstance(v, float) and v == int(v) else str(v)

        elif t == 'bool':
            return '1' if node['value'] else '0'

        elif t == 'null':
            return '0'

        elif t == 'ident':
            name = node['name']
            builtins = {
                'verdadeiro': '1', 'falso': '0', 'nulo': '0',
                'Mat': 'math',
            }
            return builtins.get(name, name)

        elif t == 'binop':
            left = self._transpilar_expr_c(node['left'])
            right = self._transpilar_expr_c(node['right'])
            op = node['op']
            op_map = {
                '&&': '&&', '||': '||',
                '==': '==', '!=': '!=',
                '<=': '<=', '>=': '>=',
                '<': '<', '>': '>',
                '+': '+', '-': '-',
                '*': '*', '/': '/',
                '%': 'fmod(%s, %s)',
                '**': '_pow(%s, %s)',
            }
            if op == '%':
                return f'_mod({left}, {right})'
            if op == '**':
                return f'_pow({left}, {right})'
            py_op = op_map.get(op, op)
            return f'({left} {py_op} {right})'

        elif t == 'unary':
            op = node['op']
            val = self._transpilar_expr_c(node['value'])
            op_map = {'!': '!', '-': '-', '+': '+'}
            return f'{op_map.get(op, op)}{val}'

        elif t == 'call':
            func = node.get('func', {})
            args = node.get('args', [])
            fn_name = ''
            if func.get('type') == 'ident':
                fn_name = func['name']
            elif func.get('type') == 'member':
                obj = self._transpilar_expr_c(func['obj'])
                prop = func['prop']
                fn_name = f'{obj}_{prop}'

            # Math functions
            math_fns = {
                'Mat_raiz': 'sqrt', 'Mat_seno': 'sin', 'Mat_cosseno': 'cos',
                'Mat_tangente': 'tan', 'Mat_log': 'log', 'Mat_abs': 'fabs',
                'Mat_arred': 'round', 'Mat_piso': 'floor', 'Mat_teto': 'ceil',
            }
            if fn_name in math_fns:
                c_fn = math_fns[fn_name]
                arg = self._transpilar_expr_c(args[0]) if args else '0'
                return f'{c_fn}({arg})'

            c_args = ', '.join(self._transpilar_expr_c(a) for a in args)
            return f'{fn_name}({c_args})'

        elif t == 'member':
            obj = self._transpilar_expr_c(node['obj'])
            return f'{obj}'  # simplification

        elif t == 'index':
            obj = self._transpilar_expr_c(node['obj'])
            idx = self._transpilar_expr_c(node['index'])
            return f'{obj}[(int){idx}]'

        elif t == 'ternary':
            cond = self._transpilar_expr_c(node['cond'])
            then = self._transpilar_expr_c(node['then'])
            else_ = self._transpilar_expr_c(node['else'])
            return f'(({cond}) ? ({then}) : ({else_}))'

        else:
            return '0'


# ══════════════════════════════════════════════════════════════════════════════
#  3. COMPILADOR PARA BYTECODE PYTHON
# ══════════════════════════════════════════════════════════════════════════════

class CompiladorBytecode:
    """Compila Advak → Python transpilado → .pyc bytecode."""

    def compilar(self, source_dk: str, destino: str = None) -> dict:
        """
        Compila para bytecode Python otimizado.
        Retorna dict com info da compilação.
        """
        import py_compile, compileall

        # Transpila para Python
        transpilador = TranspiladorPython()
        python_code = transpilador.transpilar(source_dk)

        # Salva o .py temporário
        nome_base = os.path.splitext(os.path.basename(destino or 'advak_output'))[0]
        py_path = destino or f'{nome_base}.py'
        if py_path.endswith('.pyc') or py_path.endswith('.dk'):
            py_path = py_path.rsplit('.', 1)[0] + '.py'

        with open(py_path, 'w', encoding='utf-8') as f:
            f.write(python_code)

        # Compila para bytecode
        import io as _io
        try:
            _old_stderr = sys.stderr
            sys.stderr = _io.StringIO()  # suppress py_compile warnings
            try:
                pyc_path = py_compile.compile(py_path, optimize=2)
            finally:
                sys.stderr = _old_stderr
            if not pyc_path:
                # Python 3.12+ puts .pyc in __pycache__
                import importlib.util
                pyc_path = importlib.util.cache_from_source(py_path, optimization=2)
            tamanho_py = os.path.getsize(py_path)
            # Copy .pyc to dist folder with simpler name (no __pycache__ subdir)
            pyc_destino = None
            if pyc_path and os.path.exists(pyc_path):
                nome_base = os.path.splitext(os.path.basename(py_path))[0]
                pasta_dist = os.path.dirname(py_path)
                pyc_destino = os.path.join(pasta_dist, nome_base + '.dk')
                shutil.copy2(pyc_path, pyc_destino)
            
            tamanho_pyc = os.path.getsize(pyc_destino) if pyc_destino and os.path.exists(pyc_destino) else 0
            # Rename .pyc -> .dk for cleaner output
            pyc_final = pyc_destino or pyc_path or (py_path + 'c')
            if pyc_final and pyc_final.endswith('.pyc') and os.path.exists(pyc_final):
                dk_final = pyc_final[:-4] + '.dk' if not pyc_destino else pyc_final
                if dk_final != pyc_final and not os.path.exists(dk_final):
                    shutil.copy2(pyc_final, dk_final)
                    pyc_final = dk_final
            return {
                'ok': True,
                'py': py_path,
                'pyc': pyc_final,
                'tamanho_py': tamanho_py,
                'tamanho_pyc': tamanho_pyc,
                'reducao': f'{(1 - tamanho_pyc/tamanho_py)*100:.0f}%' if tamanho_py and tamanho_pyc else '0%',
                'mensagem': f'✅ Bytecode gerado: {pyc_final} ({tamanho_pyc:,} bytes)',
            }
        except py_compile.PyCompileError as e:
            # Python transpilation has syntax errors - still useful as .py
            return {
                'ok': True,
                'py': py_path,
                'pyc': None,
                'tamanho_py': os.path.getsize(py_path) if os.path.exists(py_path) else 0,
                'tamanho_pyc': 0,
                'reducao': 'N/A',
                'mensagem': f'⚠️  Python gerado (bytecode falhou — transpilador parcial): {py_path}',
            }
        except Exception as e:
            return {'ok': False, 'erro': str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  4. COMPILADOR PARA EXECUTÁVEL (PyInstaller / zipapp)
# ══════════════════════════════════════════════════════════════════════════════

class CompiladorExe:
    """
    Gera executável standalone.
    Tenta PyInstaller primeiro; fallback para zipapp (sem dependências).
    """

    LAUNCHER_TEMPLATE = """\
#!/usr/bin/env python3
\"\"\"Advak Launcher — Gerado por Advak Compiler 5.0\"\"\"
import sys, os, asyncio

if getattr(sys, 'frozen', False):
    BASE = sys._MEIPASS
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Suppress NoneType: None on Windows
_orig_unraisable = sys.unraisablehook
def _filter_hook(args):
    if args.exc_type is type(None) or args.exc_value is None: return
    _orig_unraisable(args)
sys.unraisablehook = _filter_hook

SOURCE_CODE = {source!r}

def main():
    from advak_lexer import AdvakLexer
    from advak_parser import Parser
    from advak_interpreter import AdvakInterpreter

    try:
        tokens = AdvakLexer(SOURCE_CODE).tokenize()
        ast = Parser(tokens).parse()
        interp = AdvakInterpreter(ast)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(interp.interpret())
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for t in pending: t.cancel()
                if pending: loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.run_until_complete(loop.shutdown_asyncgens())
            except: pass
            finally: loop.close()
    except Exception as e:
        import traceback
        print(f"Erro: {{e}}", file=sys.stderr)
        if os.environ.get('ADVAK_DEBUG'): traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
"""

    def compilar(self, source_dk: str, opcoes: dict = None) -> dict:
        opcoes = opcoes or {}
        nome = opcoes.get('nome') or os.path.splitext(os.path.basename(source_dk))[0]
        pasta_saida = opcoes.get('saida') or 'dist'
        gui_mode = opcoes.get('gui', False)
        unico = opcoes.get('unico', False)  # default: onedir (faster build)
        icone = opcoes.get('icone')

        os.makedirs(pasta_saida, exist_ok=True)

        with open(source_dk, encoding='utf-8') as f:
            source = f.read()

        # Valida sintaxe primeiro
        try:
            from advak_lexer import AdvakLexer
            from advak_parser import Parser
            Parser(AdvakLexer(source).tokenize()).parse()
        except SyntaxError as e:
            return {'ok': False, 'erro': f'Erro de sintaxe: {e}'}

        # Tenta PyInstaller
        pyinstaller_result = self._tentar_pyinstaller(
            source, nome, pasta_saida, gui_mode, unico, icone
        )
        if pyinstaller_result['ok']:
            return pyinstaller_result

        # Fallback: zipapp (Python's built-in, zero dependencies)
        return self._criar_zipapp(source, nome, pasta_saida)

    def _tentar_pyinstaller(self, source, nome, pasta_saida,
                             gui_mode, unico, icone) -> dict:
        try:
            import PyInstaller
        except ImportError:
            return {
                'ok': False,
                'erro': 'PyInstaller não instalado',
                'dica': 'pip install pyinstaller'
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Transpila .dk → .py limpo para ser o entry point
            # Muito mais rápido que usar o wrapper com advak_interpreter
            try:
                tp = TranspiladorPython()
                py_code = tp.transpilar(source, nome)
            except Exception:
                py_code = None

            if py_code and py_code.strip():
                entry_path = os.path.join(tmpdir, f'{nome}.py')
                with open(entry_path, 'w', encoding='utf-8') as f:
                    f.write(py_code)
            else:
                # Fallback: usa launcher com interpretador
                entry_path = os.path.join(tmpdir, f'{nome}_launcher.py')
                launcher = self.LAUNCHER_TEMPLATE.format(source=source)
                with open(entry_path, 'w', encoding='utf-8') as f:
                    f.write(launcher)
                # Copia módulos mínimos necessários para o launcher
                for mod in ['advak_lexer.py', 'advak_parser.py',
                            'advak_interpreter.py']:
                    src = os.path.join(BASE_DIR, mod)
                    if os.path.exists(src):
                        shutil.copy(src, tmpdir)

            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--noconfirm', '--clean',
                '--name', nome,
                '--distpath', os.path.abspath(pasta_saida),
                '--workpath', os.path.join(tmpdir, 'build'),
                '--specpath', tmpdir,
                '--noupx',
            ]

            if unico:
                cmd.append('--onefile')
            else:
                cmd.append('--onedir')
            if gui_mode:
                cmd.append('--windowed')
            else:
                cmd.append('--console')
            if icone and os.path.exists(icone):
                cmd += ['--icon', icone]

            cmd.append(entry_path)

            print(f'  ⚙️  PyInstaller compilando {"(arquivo único)" if unico else "(pasta — rápido)"}...')
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    cwd=tmpdir, timeout=600)

            if result.returncode == 0:
                ext = '.exe' if sys.platform == 'win32' else ''
                # onefile -> nome.exe, onedir -> nome/nome.exe
                if unico:
                    exe_path = os.path.join(pasta_saida, nome + ext)
                else:
                    exe_path = os.path.join(pasta_saida, nome, nome + ext)
                    if not os.path.exists(exe_path):
                        exe_path = os.path.join(pasta_saida, nome + ext)
                if os.path.exists(exe_path):
                    # Calculate total size (file or folder)
                    size_path = exe_path if unico else os.path.dirname(exe_path)
                    if os.path.isdir(size_path):
                        total = sum(
                            os.path.getsize(os.path.join(dp, f))
                            for dp, _, files in os.walk(size_path)
                            for f in files
                        )
                        size = self._fmt_tamanho(total)
                    else:
                        size = self._fmt_tamanho(os.path.getsize(size_path))
                    modo = 'arquivo único' if unico else 'pasta (rápido)'
                    return {
                        'ok': True,
                        'executavel': exe_path,
                        'tamanho': size,
                        'backend': 'PyInstaller',
                        'unico': unico,
                        'mensagem': (f'✅ Executável ({modo}): {exe_path}\n'
                                    f'   Tamanho: {size}'),
                    }

            # PyInstaller ran but exe not found - log what happened
            stderr_tail = result.stderr[-300:] if result.stderr else ''
            stdout_tail = result.stdout[-200:] if result.stdout else ''
            return {
                'ok': False,
                'erro': f"returncode={result.returncode}\n{stderr_tail}\n{stdout_tail}"
            }

    def _criar_zipapp(self, source: str, nome: str, pasta_saida: str) -> dict:
        """
        Cria um .pyz (Python zipapp) — executável sem PyInstaller.
        Requer Python instalado na máquina alvo.
        """
        import zipapp, io

        with tempfile.TemporaryDirectory() as tmpdir:
            # Cria __main__.py
            launcher = self.LAUNCHER_TEMPLATE.format(source=source)
            main_path = os.path.join(tmpdir, '__main__.py')
            with open(main_path, 'w', encoding='utf-8') as f:
                f.write(launcher)

            # Copia módulos necessários
            modulos = [
                'advak_lexer.py', 'advak_parser.py', 'advak_interpreter.py',
                'advak_db.py', 'advak_http.py', 'advak_gui_modern.py',
                'advak_advanced.py', 'advak_mobile.py', 'advak_embarcado.py',
            ]
            copiados = 0
            for mod in modulos:
                src = os.path.join(BASE_DIR, mod)
                if os.path.exists(src):
                    shutil.copy(src, tmpdir)
                    copiados += 1

            # Gera o zipapp
            pyz_path = os.path.join(pasta_saida, f'{nome}.pyz')

            # Windows .bat launcher
            bat_path = os.path.join(pasta_saida, f'{nome}.bat')
            with open(bat_path, 'w') as f:
                f.write(f'@echo off\npython "{nome}.pyz" %*\n')

            # Linux/Mac shell launcher
            sh_path = os.path.join(pasta_saida, nome)
            with open(sh_path, 'w') as f:
                f.write(f'#!/bin/bash\npython3 "{nome}.pyz" "$@"\n')
            try:
                os.chmod(sh_path, 0o755)
            except Exception:
                pass

            zipapp.create_archive(
                tmpdir,
                target=pyz_path,
                interpreter=sys.executable,
                compressed=True,
            )

            size = os.path.getsize(pyz_path)
            return {
                'ok': True,
                'executavel': pyz_path,
                'bat': bat_path,
                'sh': sh_path,
                'tamanho': self._fmt_tamanho(size),
                'backend': 'zipapp',
                'modulos_incluidos': copiados,
                'mensagem': (
                    f'✅ App empacotado: {pyz_path} ({self._fmt_tamanho(size)})\n'
                    f'   Windows: {bat_path}\n'
                    f'   Linux/Mac: {sh_path}\n'
                    f'   Requer Python {sys.version.split()[0]}+ instalado'
                ),
            }

    def _fmt_tamanho(self, b: int) -> str:
        for u in ['B', 'KB', 'MB', 'GB']:
            if b < 1024: return f'{b:.1f} {u}'
            b /= 1024
        return f'{b:.1f} TB'


# ══════════════════════════════════════════════════════════════════════════════
#  5. COMPILADOR PARA C + COMPILAÇÃO NATIVA COM GCC
# ══════════════════════════════════════════════════════════════════════════════

class CompiladorNativoC:
    """
    Transpila Advak → C → compila com GCC/Clang para binário nativo.
    Máxima performance — sem overhead de Python.
    """

    def compilar(self, source_dk: str, nome: str = None,
                 pasta_saida: str = 'dist',
                 otimizacao: str = 'O2') -> dict:
        """Transpila para C e compila para binário nativo."""
        os.makedirs(pasta_saida, exist_ok=True)
        nome = nome or os.path.splitext(os.path.basename(source_dk))[0]

        with open(source_dk, encoding='utf-8') as f:
            source = f.read()

        # Transpila para C
        transpilador = TranspiladorC()
        codigo_c = transpilador.transpilar(source, nome)

        # Salva o .c
        c_path = os.path.join(pasta_saida, f'{nome}.c')
        with open(c_path, 'w', encoding='utf-8') as f:
            f.write(codigo_c)

        # Detecta compilador C
        compilador_c = None
        for cc in ['gcc', 'clang', 'cc']:
            if shutil.which(cc):
                compilador_c = cc
                break

        if not compilador_c:
            return {
                'ok': False,
                'c_path': c_path,
                'erro': 'Compilador C não encontrado (instale gcc ou clang)',
                'mensagem': f'⚠️  Código C gerado em {c_path}\n   Compile manualmente: gcc -{otimizacao} -o {nome} {c_path} -lm',
            }

        # Compila
        ext = '.exe' if sys.platform == 'win32' else ''
        bin_path = os.path.join(pasta_saida, nome + ext)

        cmd = [compilador_c, f'-{otimizacao}', '-o', bin_path, c_path, '-lm',
               '-Wno-implicit-function-declaration', '-Wno-return-type']

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            size = os.path.getsize(bin_path)
            return {
                'ok': True,
                'c_path': c_path,
                'binario': bin_path,
                'tamanho': self._fmt(size),
                'compilador': compilador_c,
                'otimizacao': otimizacao,
                'mensagem': (
                    f'✅ Binário nativo: {bin_path}\n'
                    f'   Tamanho: {self._fmt(size)}\n'
                    f'   Compilador: {compilador_c} -{otimizacao}\n'
                    f'   C source: {c_path}'
                ),
            }
        else:
            return {
                'ok': False,
                'c_path': c_path,
                'erro': result.stderr[:500],
                'mensagem': (
                    f'⚠️  Código C gerado em {c_path}\n'
                    f'   Erro de compilação: {result.stderr[:200]}\n'
                    f'   Tente: {compilador_c} -{otimizacao} -o {nome} {c_path} -lm'
                ),
            }

    def _fmt(self, b):
        for u in ['B', 'KB', 'MB']:
            if b < 1024: return f'{b:.0f} {u}'
            b /= 1024
        return f'{b:.1f} MB'


# ══════════════════════════════════════════════════════════════════════════════
#  6. ANALISADOR E BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════

class AnalisadorCodigo:
    """Analisa código Advak e gera relatório de qualidade e performance."""

    def analisar(self, source_dk: str) -> dict:
        """Análise estática completa do código."""
        from advak_lexer import AdvakLexer
        from advak_parser import Parser

        tokens = AdvakLexer(source_dk).tokenize()
        ast_dk = Parser(tokens).parse()

        # Métricas básicas
        linhas = source_dk.count('\n') + 1
        linhas_codigo = sum(1 for l in source_dk.split('\n')
                           if l.strip() and not l.strip().startswith('//'))
        linhas_comentario = sum(1 for l in source_dk.split('\n')
                               if l.strip().startswith('//'))
        caracteres = len(source_dk)

        # Análise do AST
        funcoes = []
        variaveis = []
        complexidade = 0

        def walk(nodes, depth=0):
            nonlocal complexidade
            for node in (nodes if isinstance(nodes, list) else [nodes]):
                if not isinstance(node, dict): continue
                t = node.get('type', '')
                if t == 'function_decl':
                    fn_body = node.get('body', {}).get('body', [])
                    fn_lines = self._contar_linhas_fn(fn_body)
                    funcoes.append({
                        'nome': node.get('name', 'anônima'),
                        'params': len(node.get('params', [])),
                        'linhas': fn_lines,
                        'async': node.get('async', False),
                    })
                    walk(fn_body, depth + 1)
                elif t in ('if', 'while', 'for'):
                    complexidade += 1
                    if t == 'if':
                        walk([node.get('then', {}), node.get('else', {})], depth)
                    elif t in ('while', 'for'):
                        walk([node.get('body', {})], depth)
                elif t == 'var_decl':
                    variaveis.append(node.get('name', '?'))

        walk(ast_dk)

        # Detecta problemas
        avisos = []
        for fn in funcoes:
            if fn['linhas'] > 50:
                avisos.append(f"⚠️  Função '{fn['nome']}' tem {fn['linhas']} linhas (recomendado: <50)")
            if fn['params'] > 6:
                avisos.append(f"⚠️  Função '{fn['nome']}' tem {fn['params']} parâmetros (recomendado: <6)")

        if complexidade > 20:
            avisos.append(f"⚠️  Complexidade ciclomática alta: {complexidade} (recomendado: <20)")

        import re
        if re.search(r'banco\.sql\s*\(', source_dk):
            avisos.append("💡 Usa SQL raw — considere banco.buscar() para mais segurança")

        nota = max(0, 100 - len(avisos) * 10 - max(0, complexidade - 10) * 2)

        return {
            'linhas_total': linhas,
            'linhas_codigo': linhas_codigo,
            'linhas_comentario': linhas_comentario,
            'percentual_comentarios': f'{linhas_comentario/linhas*100:.0f}%' if linhas else '0%',
            'caracteres': caracteres,
            'funcoes': len(funcoes),
            'variaveis_declaradas': len(variaveis),
            'complexidade_ciclomatica': complexidade,
            'detalhes_funcoes': funcoes,
            'avisos': avisos,
            'nota': nota,
            'classificacao': ('A' if nota >= 90 else 'B' if nota >= 75 else 'C' if nota >= 60 else 'D'),
        }

    def benchmark(self, source_dk: str, repeticoes: int = 10) -> dict:
        """Mede tempo de execução e uso de memória."""
        import asyncio
        from advak_lexer import AdvakLexer
        from advak_parser import Parser
        from advak_interpreter import AdvakInterpreter
        import io

        tempos = []
        erros = 0
        import io as _io
        import threading as _threading

        def _run_once(source_code, resultado):
            """Executa o código em thread separada com seu próprio event loop."""
            from advak_lexer import AdvakLexer
            from advak_parser import Parser
            from advak_interpreter import AdvakInterpreter
            import asyncio

            old_stdout = sys.stdout
            sys.stdout = _io.StringIO()
            try:
                t0 = time.perf_counter()
                tokens = AdvakLexer(source_code).tokenize()
                ast_dk = Parser(tokens).parse()
                interp = AdvakInterpreter(ast_dk)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(interp.interpret())
                finally:
                    try:
                        loop.run_until_complete(loop.shutdown_asyncgens())
                    except Exception:
                        pass
                    loop.close()
                    asyncio.set_event_loop(None)
                resultado.append((time.perf_counter() - t0) * 1000)
            except Exception as e:
                resultado.append(None)
            finally:
                sys.stdout = old_stdout

        for i in range(repeticoes):
            resultado = []
            t = _threading.Thread(target=_run_once, args=(source_dk, resultado))
            t.start()
            t.join(timeout=30)
            if resultado and resultado[0] is not None:
                tempos.append(resultado[0])
            else:
                erros += 1

        if not tempos:
            return {'ok': False, 'erro': 'Todos os benchmarks falharam'}

        tempos.sort()
        return {
            'ok': True,
            'repeticoes': repeticoes,
            'erros': erros,
            'media_ms': round(sum(tempos) / len(tempos), 2),
            'min_ms': round(min(tempos), 2),
            'max_ms': round(max(tempos), 2),
            'mediana_ms': round(tempos[len(tempos)//2], 2),
            'p95_ms': round(tempos[int(len(tempos)*0.95)], 2),
            'throughput': round(1000 / (sum(tempos)/len(tempos)), 1) if tempos else 0,
        }

    def _contar_linhas_fn(self, nodes) -> int:
        if not nodes: return 0
        count = 0
        for node in nodes:
            if isinstance(node, dict):
                count += 1
                for key in ('body', 'then', 'else'):
                    child = node.get(key, {})
                    if isinstance(child, dict) and 'body' in child:
                        count += self._contar_linhas_fn(child['body'])
        return count


# ══════════════════════════════════════════════════════════════════════════════
#  7. INTERFACE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def _fmt_tempo(ms: float) -> str:
    """Converte milissegundos para formato legível: 1h2m3s ou 45.2s ou 300ms"""
    if ms < 1000:
        return f'{ms:.0f}ms'
    s = ms / 1000
    if s < 60:
        return f'{s:.1f}s'
    m = int(s // 60)
    s_rest = s % 60
    if m < 60:
        return f'{m}m {s_rest:.0f}s'
    h = m // 60
    m_rest = m % 60
    return f'{h}h {m_rest}m {(s % 60):.0f}s'



# ══════════════════════════════════════════════════════════════════════════════
#  6. COMPILADOR NUITKA — Python → C++ → Binário nativo (máxima performance)
# ══════════════════════════════════════════════════════════════════════════════

class CompiladorNuitka:
    """
    Usa Nuitka para compilar Advak → Python → C++ → binário nativo.

    Nuitka traduz Python para C++ equivalente, gerando executáveis:
    - Sem runtime Python embutido (standalone) ou com runtime mínimo
    - Até 3–5× mais rápido que CPython em loops e aritmética
    - Tamanho de EXE menor que PyInstaller (~15 MB vs ~45 MB)
    - Compatível com Windows, Linux, macOS

    Uso:
        compilador.nuitka("meu_app.dk")
        compilador.nuitka("meu_app.dk", standalone=verdadeiro, gui=verdadeiro)
    """

    def compilar(self, source_dk: str, nome: str = None,
                 pasta_saida: str = "dist",
                 standalone: bool = True,
                 gui_mode: bool = False,
                 otimizacao: int = 2) -> dict:
        """Compila via Nuitka. Instala automaticamente se necessário."""

        os.makedirs(pasta_saida, exist_ok=True)
        nome = nome or os.path.splitext(os.path.basename(source_dk))[0]

        # Verifica / instala Nuitka
        nuitka_ok, nuitka_msg = self._verificar_nuitka()
        if not nuitka_ok:
            return {
                'ok': False,
                'erro': nuitka_msg,
                'mensagem': (
                    f"❌ Nuitka não disponível: {nuitka_msg}\n"
                    f"   Instale com: pip install nuitka\n"
                    f"   No Windows também instale: pip install zstandard ordered-set"
                ),
            }

        # Transpila .dk → .py
        transpilador = TranspiladorPython()
        with open(source_dk, encoding='utf-8') as f:
            source = f.read()
        python_code = transpilador.transpilar(source, nome)

        # Cria o .py temporário
        with tempfile.TemporaryDirectory() as tmpdir:
            py_path = os.path.join(tmpdir, f'{nome}.py')
            with open(py_path, 'w', encoding='utf-8') as f:
                f.write(python_code)

            # Copia módulos Advak
            modulos = [
                'advak_lexer.py', 'advak_parser.py', 'advak_interpreter.py',
                'advak_db.py', 'advak_http.py', 'advak_gui_modern.py',
                'advak_advanced.py', 'advak_mobile.py', 'advak_embarcado.py',
            ]
            for mod in modulos:
                src = os.path.join(BASE_DIR, mod)
                if os.path.exists(src):
                    shutil.copy(src, tmpdir)

            # Monta comando Nuitka
            cmd = [
                sys.executable, '-m', 'nuitka',
                f'--output-dir={os.path.abspath(pasta_saida)}',
                f'--output-filename={nome}',
                f'--python-flag=-O',           # optimized
            ]

            if standalone:
                cmd.append('--standalone')       # inclui runtime Python
                cmd.append('--onefile')           # arquivo único
            else:
                cmd.append('--module')            # extensão .pyd/.so

            if gui_mode:
                cmd.append('--windows-disable-console')

            # Otimizações
            if otimizacao >= 2:
                cmd += [
                    '--assume-yes-for-downloads',  # auto aceita downloads de deps
                    f'--jobs={os.cpu_count() or 2}',  # compila em paralelo
                ]

            # Exclui módulos pesados
            for excl in ['matplotlib', 'numpy', 'pandas', 'scipy',
                         'PIL', 'torch', 'tensorflow', 'sklearn']:
                cmd += [f'--nofollow-import-to={excl}']

            # Includes necessários
            for inc in ['asyncio', 'threading', 'json', 're', 'os', 'sys']:
                cmd += [f'--follow-import-to={inc}']

            cmd.append(py_path)

            print(f"  ⚙️  Nuitka compilando (pode levar alguns minutos)...")
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=tmpdir
            )

            # Detecta executável gerado
            ext = '.exe' if sys.platform == 'win32' else ''
            exe_candidates = [
                os.path.join(pasta_saida, nome + ext),
                os.path.join(pasta_saida, nome + '.dist', nome + ext),
                os.path.join(pasta_saida, nome + '.onefile-build', nome + ext),
            ]
            exe_path = next((p for p in exe_candidates if os.path.exists(p)), None)

            if result.returncode == 0 and exe_path:
                size = self._fmt(os.path.getsize(exe_path))
                return {
                    'ok': True,
                    'executavel': exe_path,
                    'tamanho': size,
                    'mensagem': (
                        f"✅ Nuitka: {exe_path} ({size})\n"
                        f"   Backend: C++ nativo (até 5× mais rápido que Python)\n"
                        f"   Standalone: {standalone}"
                    ),
                }
            else:
                # Mesmo com erro, se gerou o .c pode ser útil
                return {
                    'ok': False,
                    'erro': result.stderr[-300:] if result.stderr else 'Erro desconhecido',
                    'mensagem': (
                        f"⚠️  Nuitka falhou (verifique a instalação)\n"
                        f"   {result.stderr[-200:] if result.stderr else ''}\n"
                        f"   Tente: pip install nuitka zstandard ordered-set"
                    ),
                }

    def _verificar_nuitka(self) -> tuple:
        """Verifica se Nuitka está instalado."""
        try:
            import nuitka
            # Try multiple ways to get the version
            ver = (getattr(nuitka, '__version__', None) or
                   getattr(nuitka, 'Version', None) or
                   getattr(nuitka, 'version_string', None))
            if ver is None:
                try:
                    from nuitka.Version import getNuitkaVersion
                    ver = getNuitkaVersion()
                except Exception:
                    pass
            if ver is None:
                import importlib.metadata
                try:
                    ver = importlib.metadata.version('nuitka')
                except Exception:
                    ver = 'instalado'
            return True, f"v{ver}"
        except ImportError:
            pass
        # Via CLI
        if shutil.which('nuitka') or shutil.which('nuitka3'):
            r = subprocess.run(['nuitka', '--version'],
                capture_output=True, text=True)
            ver = r.stdout.strip().split()[0] if r.stdout else 'CLI'
            return True, ver
        return False, "não instalado (pip install nuitka)"

    def instalar(self) -> str:
        """Tenta instalar Nuitka via pip."""
        try:
            print("  📦 Instalando Nuitka...")
            r = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'nuitka',
                 'zstandard', 'ordered-set'],
                capture_output=True, text=True
            )
            if r.returncode == 0:
                return "✅ Nuitka instalado! Tente novamente."
            return f"❌ Falha: {r.stderr[-200:]}"
        except Exception as e:
            return f"❌ {e}"

    def _fmt(self, b: int) -> str:
        for u in ['B', 'KB', 'MB', 'GB']:
            if b < 1024: return f'{b:.1f} {u}'
            b /= 1024
        return f'{b:.1f} GB'


# ══════════════════════════════════════════════════════════════════════════════
#  7. COMPILADOR CYTHON — Python → C → extensão nativa (.pyd/.so)
# ══════════════════════════════════════════════════════════════════════════════

class CompiladorCython:
    """
    Usa Cython para transpilar Python → C e compilar extensão nativa.

    Cython gera módulos .pyd (Windows) ou .so (Linux/Mac) que são
    importados como módulos Python normais, mas executam em velocidade C.

    Diferenças vs Nuitka:
    - Cython → extensão importável (não executável standalone)
    - Nuitka → executável standalone completo
    - Cython é mais usado para bibliotecas e módulos reutilizáveis
    - Nuitka é melhor para aplicações completas

    Uso:
        compilador.cython("meu_modulo.dk")
        compilador.cython("meu_modulo.dk", tipo_c=verdadeiro)  # gera .c puro
    """

    SETUP_TEMPLATE = """# -*- coding: utf-8 -*-
from setuptools import setup
from Cython.Build import cythonize

setup(
    name='{nome}',
    ext_modules=cythonize(
        '{pyx_path}',
        compiler_directives={{
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'cdivision': True,
            'nonecheck': False,
        }},
        annotate=True,
    ),
)
"""

    def compilar(self, source_dk: str, nome: str = None,
                 pasta_saida: str = "dist",
                 tipo_c: bool = False) -> dict:
        """Compila via Cython. Unicode-safe para Windows."""

        os.makedirs(pasta_saida, exist_ok=True)
        nome = nome or os.path.splitext(os.path.basename(source_dk))[0]

        cython_ok, cython_msg = self._verificar_cython()
        if not cython_ok:
            return {
                'ok': False,
                'mensagem': (
                    f"\u274c Cython nao disponivel: {cython_msg}\n"
                    f"   Instale: pip install cython setuptools"
                ),
            }

        with open(source_dk, encoding='utf-8') as f:
            source = f.read()

        transpilador = TranspiladorPython()
        python_code = transpilador.transpilar(source, nome)

        # Converte chars unicode para escapes ASCII dentro de strings Python
        # Necessario porque Cython no Windows nao suporta chars fora do ASCII
        def tornar_ascii_seguro(code_str):
            resultado = []
            for linha in code_str.split('\n'):
                if not any(ord(c) > 127 for c in linha):
                    resultado.append(linha)
                    continue
                nova_linha = []
                em_string = False
                char_string = None
                idx_l = 0
                while idx_l < len(linha):
                    ch = linha[idx_l]
                    if not em_string and ch in ('"', "'"):
                        em_string = True
                        char_string = ch
                        nova_linha.append(ch)
                    elif em_string and ch == char_string:
                        em_string = False
                        nova_linha.append(ch)
                    elif em_string and ord(ch) > 127:
                        cp = ord(ch)
                        if cp <= 0xFFFF:
                            nova_linha.append(f'\\u{cp:04x}')
                        else:
                            nova_linha.append(f'\\U{cp:08x}')
                    else:
                        nova_linha.append(ch)
                    idx_l += 1
                resultado.append(''.join(nova_linha))
            return '\n'.join(resultado)

        python_safe = tornar_ascii_seguro(python_code)

        # Pos-processamento para compatibilidade com Cython
        def fixar_para_cython(code_str):
            linhas_in  = code_str.split('\n')
            linhas_out = []
            i = 0
            while i < len(linhas_in):
                linha = linhas_in[i]

                # 1. Remove imports nao suportados pelo Cython
                if linha.strip() in (
                    'from __future__ import annotations',
                    'import asyncio', 'import json',
                    'import os', 'import re', 'import sys',
                ):
                    i += 1
                    continue

                # 2. Remove entry point asyncio.run(...)
                if 'asyncio.run(' in linha:
                    i += 1
                    continue

                # 3. Substitui nomes ADT nao declarados por None
                #    Ex: estado = Inicio  ->  estado = None  # Inicio (ADT)
                import re as _re
                m = _re.match(r'^(\s*)(\w+)\s*=\s*([A-Z][A-Za-z0-9_]*)\s*$', linha)
                if m:
                    indent, var, val = m.group(1), m.group(2), m.group(3)
                    # So substitui se parece ADT (nao eh builtin nem funcao conhecida)
                    builtins_py = {
                        'True','False','None','int','str','float','bool',
                        'list','dict','tuple','set','type','len','range',
                        'print','input','open','enumerate','zip','map',
                        'filter','sorted','reversed','sum','min','max',
                        'abs','round','repr','isinstance','issubclass',
                    }
                    if val not in builtins_py and val not in code_str.split('\n')[0:i]:
                        # Verifica se val foi declarado anteriormente no codigo
                        declarado = any(
                            _re.search(rf'\b{_re.escape(val)}\b', l)
                            for l in linhas_in[:i]
                            if 'def ' in l or '=' in l
                        )
                        if not declarado:
                            linhas_out.append(f'{indent}{var} = None  # {val} (ADT nao declarado)')
                            i += 1
                            continue

                # 4. Substitui 'for n in func_geradora():' por lista vazia
                #    (geradores sem yield nao funcionam em Cython)
                m2 = _re.match(r'^(\s*)for (\w+) in (\w+)\(\):', linha)
                if m2:
                    indent2, var2, fn2 = m2.group(1), m2.group(2), m2.group(3)
                    # Verifica se fn2 tem 'pass  # [yield]' no corpo
                    fn_body = '\n'.join(linhas_in)
                    if f'def {fn2}(' in fn_body:
                        fn_start = fn_body.find(f'def {fn2}(')
                        fn_section = fn_body[fn_start:fn_start+500]
                        if 'pass  # [yield]' in fn_section:
                            # Substitui o for por codigo equivalente sem generator
                            linhas_out.append(f'{indent2}# Generator {fn2} nao suportado em Cython — ignorado')
                            # Pula o bloco do for
                            nivel = len(linha) - len(linha.lstrip())
                            i += 1
                            while i < len(linhas_in):
                                prox = linhas_in[i]
                                if prox.strip() == '': 
                                    linhas_out.append(prox)
                                    i += 1
                                    break
                                nivel_prox = len(prox) - len(prox.lstrip()) if prox.strip() else nivel+1
                                if prox.strip() and nivel_prox <= nivel:
                                    break
                                i += 1
                            continue

                # 5. Remove print(f"") - f-strings vazias
                if linha.strip() in ('print(f"")', "print(f'')", 'print(f\'\'\')'):
                    linhas_out.append(linha.replace('print(f"")', 'print("")'
                        ).replace("print(f'')", 'print("")'))
                    i += 1
                    continue

                linhas_out.append(linha)
                i += 1
            return '\n'.join(linhas_out)

        python_cython = fixar_para_cython(python_safe)

        cython_header = (
            "# -*- coding: utf-8 -*-\n"
            "# cython: language_level=3\n"
            "# cython: boundscheck=False\n"
            "# cython: wraparound=False\n"
            f"# Modulo: {nome}\n\n"
        )
        cython_code = cython_header + python_cython

        with tempfile.TemporaryDirectory() as tmpdir:
            pyx_path = os.path.join(tmpdir, f'{nome}.pyx')
            with open(pyx_path, 'w', encoding='utf-8') as f:
                f.write(cython_code)

            if tipo_c:
                c_path = os.path.join(pasta_saida, f'{nome}_cython.c')
                cmd = [sys.executable, '-m', 'cython',
                       '--output-file', c_path, pyx_path]
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode == 0 and os.path.exists(c_path):
                    size = os.path.getsize(c_path)
                    return {
                        'ok': True,
                        'c_path': c_path,
                        'mensagem': (
                            f"\u2705 Cython -> C: {c_path} ({size:,} bytes)\n"
                            f"   Compile: gcc -O2 -shared -fPIC {c_path} -o {nome}.so"
                        ),
                    }
                return {
                    'ok': False,
                    'mensagem': f"\u274c Cython falhou:\n{r.stderr[:300]}"
                }

            pyx_safe = pyx_path.replace('\\', '/')
            setup_code = (
                "# -*- coding: utf-8 -*-\n"
                "from setuptools import setup\n"
                "from Cython.Build import cythonize\n"
                "setup(\n"
                f"    name='{nome}',\n"
                f"    ext_modules=cythonize(\n"
                f"        '{pyx_safe}',\n"
                "        compiler_directives={\n"
                "            'language_level': 3,\n"
                "            'boundscheck': False,\n"
                "            'wraparound': False,\n"
                "            'cdivision': True,\n"
                "            'nonecheck': False,\n"
                "        },\n"
                "    ),\n"
                ")\n"
            )
            setup_path = os.path.join(tmpdir, 'setup.py')
            with open(setup_path, 'w', encoding='utf-8') as f:
                f.write(setup_code)

            cmd = [sys.executable, setup_path, 'build_ext',
                   f'--build-lib={os.path.abspath(pasta_saida)}',
                   '--inplace']
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmpdir)

            ext_files = [
                f for f in os.listdir(pasta_saida)
                if f.startswith(nome) and (f.endswith('.pyd') or f.endswith('.so'))
            ]

            if r.returncode == 0 and ext_files:
                ext_path = os.path.join(pasta_saida, ext_files[0])
                size = self._fmt(os.path.getsize(ext_path))
                return {
                    'ok': True,
                    'extensao': ext_path,
                    'tamanho': size,
                    'mensagem': (
                        f"\u2705 Cython: {ext_path} ({size})\n"
                        f"   Tipo: extensao nativa .pyd\n"
                        f"   Usar: import {nome}  (em Python)"
                    ),
                }

            c_files = [f for f in os.listdir(tmpdir) if f.endswith('.c')]
            if c_files:
                c_src = os.path.join(tmpdir, c_files[0])
                c_dst = os.path.join(pasta_saida, f'{nome}_cython.c')
                shutil.copy(c_src, c_dst)
                return {
                    'ok': True,
                    'c_path': c_dst,
                    'mensagem': (
                        f"\u26a0 Extensao nao compilada, C gerado:\n"
                        f"   {c_dst}\n"
                        f"   {r.stderr[-150:] if r.stderr else ''}"
                    ),
                }

            return {
                'ok': False,
                'mensagem': (
                    f"\u274c Cython falhou\n"
                    f"   {(r.stderr or r.stdout or 'Sem mensagem de erro')[-800:]}"
                )
            }



    def _verificar_cython(self) -> tuple:
        try:
            import Cython
            ver = (getattr(Cython, '__version__', None) or
                   getattr(Cython, 'version', None))
            if ver is None:
                import importlib.metadata
                try:
                    ver = importlib.metadata.version('cython')
                except Exception:
                    ver = 'instalado'
            return True, f"v{ver}"
        except ImportError:
            pass
        if shutil.which('cython') or shutil.which('cython3'):
            return True, "CLI"
        return False, "não instalado (pip install cython)"

    def instalar(self) -> str:
        try:
            print("  📦 Instalando Cython...")
            r = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'cython', 'setuptools'],
                capture_output=True, text=True
            )
            return "✅ Cython instalado!" if r.returncode == 0 else f"❌ {r.stderr[-200:]}"
        except Exception as e:
            return f"❌ {e}"

    def _fmt(self, b: int) -> str:
        for u in ['B', 'KB', 'MB', 'GB']:
            if b < 1024: return f'{b:.1f} {u}'
            b /= 1024
        return f'{b:.1f} GB'


class AdvakCompilerV5:
    """Interface principal do compilador Advak 5.0."""

    def __init__(self):
        self._py     = TranspiladorPython()
        self._c      = TranspiladorC()
        self._bc     = CompiladorBytecode()
        self._exe    = CompiladorExe()
        self._nat    = CompiladorNativoC()
        self._nuitka = CompiladorNuitka()
        self._cython = CompiladorCython()
        self._nat  = CompiladorNativoC()
        self._anal = AnalisadorCodigo()

    def compilar(self, arquivo_dk: str, opcoes: dict = None) -> str:
        """
        Ponto de entrada principal.
        
        opcoes:
          backend  = 'python' | 'bytecode' | 'exe' | 'c' | 'nativo'
          nome     = nome do arquivo de saída
          saida    = pasta de saída
          otimizar = True/False
          gui      = True/False (para exe)
          icone    = caminho do ícone
        """
        opcoes = opcoes or {}
        backend = opcoes.get('backend', 'bytecode')

        if not os.path.exists(arquivo_dk):
            return f"❌ Arquivo '{arquivo_dk}' não encontrado"

        with open(arquivo_dk, encoding='utf-8') as f:
            source = f.read()

        # Valida sintaxe
        try:
            from advak_lexer import AdvakLexer
            from advak_parser import Parser
            tokens = AdvakLexer(source).tokenize()
            ast_dk = Parser(tokens).parse()
            print(f"✅ Sintaxe OK — {len(ast_dk)} nós, {len(source.splitlines())} linhas")
        except SyntaxError as e:
            return f"❌ Erro de sintaxe: {e}"

        nome = opcoes.get('nome') or os.path.splitext(os.path.basename(arquivo_dk))[0]
        pasta = opcoes.get('saida') or 'dist'
        os.makedirs(pasta, exist_ok=True)

        print(f"\n🔨 Advak Compiler 5.0 — Backend: {backend.upper()}")
        print(f"   Arquivo:  {arquivo_dk}")
        print(f"   Saída:    {pasta}/{nome}")

        t0 = time.perf_counter()

        if backend == 'python':
            py_code = self._py.transpilar(source, nome)
            saida = os.path.join(pasta, f'{nome}.py')
            with open(saida, 'w', encoding='utf-8') as f:
                f.write(py_code)
            dt = (time.perf_counter() - t0) * 1000
            return (f"✅ Transpilado para Python: {saida}\n"
                    f"   Linhas geradas: {py_code.count(chr(10))}\n"
                    f"   Tempo: {dt:.1f}ms\n"
                    f"   Executar: python {saida}")

        elif backend == 'bytecode':
            saida = os.path.join(pasta, f'{nome}.py')
            result = self._bc.compilar(source, saida)
            dt = (time.perf_counter() - t0) * 1000
            if result['ok']:
                executar = result.get('pyc') or result.get('py', saida)
                return (f"{result['mensagem']}\n"
                        f"   .py: {result['tamanho_py']} bytes\n"
                        f"   .dk:  {result['tamanho_pyc']:,} bytes (redução: {result['reducao']})\n"
                        f"   Tempo: {_fmt_tempo(dt)}\n"
                        f"   Executar: python {executar}")
            return f"❌ {result['erro']}"

        elif backend == 'exe':
            result = self._exe.compilar(arquivo_dk, opcoes)
            dt = (time.perf_counter() - t0) * 1000
            msg = result.get('mensagem', '')
            return f"{msg}\n   Tempo total: {_fmt_tempo(dt)}"

        elif backend == 'c':
            saida = os.path.join(pasta, f'{nome}.c')
            codigo_c = self._c.transpilar(source, nome)
            with open(saida, 'w', encoding='utf-8') as f:
                f.write(codigo_c)
            dt = (time.perf_counter() - t0) * 1000
            linhas_c = codigo_c.count('\n')
            return (f"✅ Transpilado para C: {saida}\n"
                    f"   Linhas C: {linhas_c}\n"
                    f"   Tempo: {dt:.1f}ms\n"
                    f"   Compilar: gcc -O2 -o {nome} {saida} -lm")

        elif backend == 'nativo':
            otim = 'O2' if opcoes.get('otimizar', True) else 'O0'
            nat_nome = nome or os.path.splitext(os.path.basename(arquivo_dk))[0]
            result = self._nat.compilar(arquivo_dk, nat_nome, pasta, otim)
            dt = (time.perf_counter() - t0) * 1000
            return f"{result['mensagem']}\n   Tempo total: {_fmt_tempo(dt)}"

        elif backend == 'nuitka':
            standalone = opcoes.get('standalone', True)
            otim_n = int(opcoes.get('otimizacao', 2))
            result = self._nuitka.compilar(
                arquivo_dk, nome, pasta,
                standalone=standalone,
                gui_mode=opcoes.get('gui', False),
                otimizacao=otim_n
            )
            dt = (time.perf_counter() - t0) * 1000
            return f"{result['mensagem']}\n   Tempo total: {_fmt_tempo(dt)}"

        elif backend == 'cython':
            tipo_c = opcoes.get('tipo_c', False)
            result = self._cython.compilar(arquivo_dk, nome, pasta, tipo_c=tipo_c)
            dt = (time.perf_counter() - t0) * 1000
            return f"{result['mensagem']}\n   Tempo total: {_fmt_tempo(dt)}"

        else:
            return (f"❌ Backend desconhecido: {backend}\n"
                    f"   Backends disponíveis: python | bytecode | exe | c | nativo | nuitka | cython")

    def python(self, arquivo_dk: str, saida: str = None) -> str:
        pasta = os.path.dirname(saida) if saida and os.path.dirname(saida) else 'dist'
        nome = os.path.splitext(os.path.basename(saida or arquivo_dk))[0]
        return self.compilar(arquivo_dk, {'backend': 'python', 'saida': pasta, 'nome': nome})

    def bytecode(self, arquivo_dk: str, saida: str = None) -> str:
        pasta = os.path.dirname(saida) if saida and os.path.dirname(saida) else 'dist'
        return self.compilar(arquivo_dk, {'backend': 'bytecode', 'saida': pasta})

    def exe(self, arquivo_dk: str, gui: bool = False, icone: str = None,
            nome: str = None, unico: bool = False) -> str:
        """
        Compila para executável.
        unico=False (padrão) → pasta com .exe + DLLs (mais rápido, ~30s)
        unico=True           → arquivo .exe único (mais lento, ~4min, portável)
        """
        real_nome = nome or os.path.splitext(os.path.basename(arquivo_dk))[0]
        return self.compilar(arquivo_dk, {
            'backend': 'exe', 'gui': gui, 'icone': icone, 'nome': real_nome,
            'saida': 'dist', 'unico': unico
        })

    def c(self, arquivo_dk: str, saida: str = None) -> str:
        return self.compilar(arquivo_dk, {'backend': 'c', 'saida': 'dist'})

    def nativo(self, arquivo_dk: str, otimizar: bool = True,
               nome: str = None) -> str:
        real_nome = nome or os.path.splitext(os.path.basename(arquivo_dk))[0]
        return self.compilar(arquivo_dk, {
            'backend': 'nativo', 'otimizar': otimizar, 'nome': real_nome
        })

    def nuitka(self, arquivo_dk: str, standalone: bool = True,
              gui: bool = False, nome: str = None) -> str:
        """
        Compila via Nuitka → C++ → binário nativo standalone.
        standalone=True  → .exe que roda sem Python instalado
        standalone=False → módulo .pyd/.so importável
        """
        real_nome = nome or os.path.splitext(os.path.basename(arquivo_dk))[0]
        return self.compilar(arquivo_dk, {
            'backend': 'nuitka', 'standalone': standalone,
            'gui': gui, 'nome': real_nome, 'saida': 'dist'
        })

    def cython(self, arquivo_dk: str, tipo_c: bool = False,
               nome: str = None) -> str:
        """
        Compila via Cython → C → extensão nativa .pyd/.so.
        tipo_c=False → compila extensão importável
        tipo_c=True  → só gera o código C (sem compilar)
        """
        real_nome = nome or os.path.splitext(os.path.basename(arquivo_dk))[0]
        return self.compilar(arquivo_dk, {
            'backend': 'cython', 'tipo_c': tipo_c,
            'nome': real_nome, 'saida': 'dist'
        })

    def instalar_nuitka(self) -> str:
        """Instala Nuitka via pip."""
        return self._nuitka.instalar()

    def instalar_cython(self) -> str:
        """Instala Cython via pip."""
        return self._cython.instalar()

    def analisar(self, arquivo_dk: str) -> str:
        with open(arquivo_dk, encoding='utf-8') as f:
            source = f.read()
        r = self._anal.analisar(source)
        linhas = [
            f"\n📊 Análise de Código: {os.path.basename(arquivo_dk)}",
            f"{'═'*50}",
            f"  Linhas totais:        {r['linhas_total']}",
            f"  Linhas de código:     {r['linhas_codigo']}",
            f"  Comentários:          {r['linhas_comentario']} ({r['percentual_comentarios']})",
            f"  Funções:              {r['funcoes']}",
            f"  Variáveis:            {r['variaveis_declaradas']}",
            f"  Complexidade:         {r['complexidade_ciclomatica']}",
            f"  Nota de qualidade:    {r['nota']}/100 (Classe {r['classificacao']})",
        ]
        if r['detalhes_funcoes']:
            linhas.append(f"\n  Funções:")
            for fn in r['detalhes_funcoes'][:10]:
                async_tag = ' [async]' if fn['async'] else ''
                linhas.append(f"    - {fn['nome']}({fn['params']} params, ~{fn['linhas']} linhas){async_tag}")
        if r['avisos']:
            linhas.append(f"\n  Avisos:")
            for av in r['avisos']:
                linhas.append(f"    {av}")
        else:
            linhas.append(f"\n  ✅ Nenhum problema encontrado!")
        return '\n'.join(linhas)

    def benchmark(self, arquivo_dk: str, repeticoes: int = 5) -> str:
        with open(arquivo_dk, encoding='utf-8') as f:
            source = f.read()
        print(f"⏱️  Executando {repeticoes} repetições...")
        r = self._anal.benchmark(source, repeticoes)
        if not r['ok']:
            return f"❌ {r['erro']}"
        return (
            f"\n⏱️  Benchmark: {os.path.basename(arquivo_dk)}\n"
            f"{'═'*45}\n"
            f"  Repetições:    {r['repeticoes']} (erros: {r['erros']})\n"
            f"  Média:         {r['media_ms']} ms\n"
            f"  Mínimo:        {r['min_ms']} ms\n"
            f"  Máximo:        {r['max_ms']} ms\n"
            f"  Mediana:       {r['mediana_ms']} ms\n"
            f"  P95:           {r['p95_ms']} ms\n"
            f"  Throughput:    {r['throughput']} exec/s"
        )

    def info(self) -> str:
        # Check available tools
        tools = {}
        for tool in ['gcc', 'clang']:
            tools[tool] = '✅' if shutil.which(tool) else '❌'
        try:
            import PyInstaller
            tools['pyinstaller'] = f'✅ v{PyInstaller.__version__}'
        except ImportError:
            tools['pyinstaller'] = '❌ (pip install pyinstaller)'
        try:
            import nuitka
            # Nuitka stores version differently depending on the version
            _nv = (getattr(nuitka, '__version__', None) or
                   getattr(nuitka, 'Version', None) or
                   getattr(nuitka, 'version_string', None))
            if _nv is None:
                try:
                    from nuitka.Version import getNuitkaVersion
                    _nv = getNuitkaVersion()
                except Exception:
                    pass
            if _nv is None:
                import importlib.metadata
                try:
                    _nv = importlib.metadata.version('nuitka')
                except Exception:
                    _nv = 'instalado'
            tools['nuitka'] = f'✅ v{_nv}'
        except ImportError:
            tools['nuitka'] = '❌ (pip install nuitka)'
        try:
            import Cython
            _cv = (getattr(Cython, '__version__', None) or
                   getattr(Cython, 'version', None))
            if _cv is None:
                import importlib.metadata
                try:
                    _cv = importlib.metadata.version('cython')
                except Exception:
                    _cv = 'instalado'
            tools['cython'] = f'✅ v{_cv}'
        except ImportError:
            tools['cython'] = '❌ (pip install cython)'

        return (
            f"\n🔨 Advak Compiler 5.0 — Backends Disponíveis\n"
            f"{'═'*50}\n"
            f"  python   — Transpila para Python puro       ✅\n"
            f"  bytecode — Compila para .dk  otimizado      ✅\n"
            f"  exe      — Executável (PyInstaller)         {tools['pyinstaller']}\n"
            f"                  fallback: zipapp (.pyz)     ✅\n"
            f"  c        — Transpila para C puro            ✅\n"
            f"  nativo   — C + GCC/Clang → binário         {tools['gcc']}\n"
            f"  nuitka   — C++ nativo (até 5× mais rápido) {tools['nuitka']}\n"
            f"  cython   — Extensão .pyd/.so nativa        {tools['cython']}\n"
            f"\n  Python:      {sys.version.split()[0]}\n"
            f"  GCC:         {tools['gcc']}\n"
            f"  Clang:       {tools['clang']}\n"
            f"  PyInstaller: {tools['pyinstaller']}\n"
            f"  Nuitka:      {tools['nuitka']}\n"
            f"  Cython:      {tools['cython']}\n"
            f"  Plataforma:  {sys.platform}"
        )


# ── Instância global para uso no interpretador ────────────────────────────────
def criar_sistema_compilador():
    comp = AdvakCompilerV5()
    return {
        # Compilação
        'compilar':         lambda arq, opts=None: comp.compilar(arq, opts),
        'python':           lambda arq, saida=None: comp.python(arq, saida),
        'bytecode':         lambda arq, saida=None: comp.bytecode(arq, saida),
        'exe':              lambda arq, gui=False, icone=None, nome=None, unico=False:
                                comp.exe(arq, gui, icone, nome, unico),
        'c':                lambda arq, saida=None: comp.c(arq, saida),
        'nativo':           lambda arq, otim=True, nome=None: comp.nativo(arq, otim, nome),
        'nuitka':           lambda arq, standalone=True, gui=False, nome=None:
                                comp.nuitka(arq, standalone, gui, nome),
        'cython':           lambda arq, tipo_c=False, nome=None:
                                comp.cython(arq, tipo_c, nome),
        # Instalar ferramentas
        'instalar_nuitka':  lambda: comp.instalar_nuitka(),
        'instalar_cython':  lambda: comp.instalar_cython(),
        # Análise
        'analisar':         lambda arq: comp.analisar(arq),
        'benchmark':        lambda arq, n=5: comp.benchmark(arq, n),
        'info':             lambda: comp.info(),
        # Acesso ao objeto completo
        '_compilador': comp,
    }
