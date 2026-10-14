"""
Advak 3.0 — Lexer v2
Suporte correto a template strings com ${expressões complexas}.
"""
import re

KEYWORDS = {
    # ── PT-BR ──────────────────────────────────────────────────────────────
    'seja', 'fixo',
    'se', 'senão', 'senao', 'enquanto', 'para', 'retornar', 'quebrar', 'continuar',
    'funcao', 'entao', 'lancar', 'produzir',
    'função', 'aguarda',
    'classe', 'isso', 'herda',
    'importar', 'de', 'como', 'exportar',
    'combinar', 'caso', 'padrão',
    'tentar', 'capturar', 'pegar', 'finalmente', 'lançar',
    'assincrona', 'aguarda', 'async', 'await',
    'ai_perguntar', 'ai_classificar', 'ai_transformar', 'ai_resumir', 'ai_gerar',
    'imprimir', 
    'verdadeiro', 'falso', 'nulo',
    # ── Generators (PT-BR) ────────────────────────────────────────────────
    'produzir', 'gerador',
    # ── Destructuring (PT-BR) ─────────────────────────────────────────────
    'extrair',
    # ── Lógica/Prolog (PT-BR) ─────────────────────────────────────────────
    'fato', 'regra', 'consultar', 'retroceder',
    # ── Canvas 2D (PT-BR) ─────────────────────────────────────────────────
    'tela', 'desenhar',
    # ── C/C++ — Structs tipadas (PT-BR) ───────────────────────────────────
    'estrutura', 'struct',
    # ── C/C++ — Enums com valor (PT-BR) ───────────────────────────────────
    'enumeracao', 'enum',
    # ── C/C++ — Ponteiros/refs (PT-BR) ────────────────────────────────────
    'ref', 'deref', 'endereco',
    # ── C/C++ — Macros/inline (PT-BR) ─────────────────────────────────────
    'macro', 'inline', 'definir',
    # ── Haskell — Tipos Algébricos (PT-BR) ────────────────────────────────
     'variante', 
    # ── Haskell — Imutabilidade (PT-BR) ───────────────────────────────────
    'congelar', 'imutavel', 'puro',
    # ── Haskell — Composição de funções ───────────────────────────────────
    'compor', 'puro',
    # ── English ────────────────────────────────────────────────────────────
    'let', 'const', 'var', 'instanceof', 'e_instancia', 'eh_instancia',
    'if', 'else', 'while', 'for', 'in', 'of',
    'return', 'break', 'continue',
    'function', 'async', 'await',
    'class', 'extends', 'this', 'super',
    'switch', 'case', 'default',
    'try', 'catch', 'finally', 'throw',
    'match',
    'print', 'input',
    'true', 'false', 'null',
    'ai_ask', 'ai_classify', 'ai_transform', 'ai_summarize', 'ai_generate',
    # ── Generators (English) ──────────────────────────────────────────────
    'yield', 'generator',
    # ── Lógica/Prolog (English) ───────────────────────────────────────────
    'fact', 'rule', 'query', 'backtrack',
    # novo/new, banco, modelo, this → tratados como IDENT ou via parse_primary
}

TOKEN_SPECS = [
    ('COMMENT',        r'//[^\n]*'),
    ('BLOCK_COMMENT',  r'/\*[\s\S]*?\*/'),
    ('STRING',         r'"(?:\\.|[^"\\])*"'),
    ('STRING_SINGLE',  r"'(?:\\.|[^'\\])*'"),
    ('FLOAT',          r'\d+\.\d+'),
    ('NUMBER',         r'\d+'),
    ('ARROW',          r'=>'),
    ('RET_ARROW',      r'->'),        # função f(a: numero) -> numero  (tipo de retorno)
    ('PIPE',           r'\|>'),
    ('SPREAD',         r'\.\.\.'),
    ('RANGE_INC',      r'\.\.='),     # 1..=10  (intervalo com o fim incluído)
    ('RANGE',          r'\.\.'),      # 1..10   (intervalo com o fim excluído)
    ('NULL_COALESCE',  r'\?\?'),
    ('OPTIONAL_CHAIN', r'\?\.'),
    ('POWER',          r'\*\*'),
    ('STRICT_EQ',      r'==='),
    ('STRICT_NEQ',     r'!=='),
    ('EQ',             r'=='),
    ('NEQ',            r'!='),
    ('LTE',            r'<='),
    ('GTE',            r'>='),
    ('LSHIFT',         r'<<'),
    ('RSHIFT',         r'>>'),
    ('LT',             r'<'),
    ('GT',             r'>'),
    ('INCREMENT',      r'\+\+'),
    ('DECREMENT',      r'--'),
    ('AND',            r'&&'),
    ('OR',             r'\|\|'),
    ('NOT',            r'!'),
    ('TERNARY',        r'\?'),
    ('ASSIGN_OP',      r'[+\-*/%]='),
    ('ASSIGN',         r'='),
    ('SEMICOLON',      r';'),
    ('COLON',          r':'),
    ('COMMA',          r','),
    ('DOT',            r'\.'),
    ('LPAREN',         r'\('),
    ('RPAREN',         r'\)'),
    ('LCURLY',         r'\{'),
    ('RCURLY',         r'\}'),
    ('LBRACKET',       r'\['),
    ('RBRACKET',       r'\]'),
    ('OP',             r'[+\-*/%]'),
    ('BIT_AND',        r'&'),
    ('BIT_OR',         r'\|'),
    ('BIT_XOR',        r'\^'),
    ('BIT_NOT',        r'~'),
    ('IDENT',          r'[a-zA-ZáàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ_][a-zA-ZáàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ0-9_]*'),
    ('NEWLINE',        r'\n'),
    ('SKIP',           r'[ \t\r]+'),
    ('MISMATCH',       r'.'),
]

_PARTES_DE_EXPRESSAO = re.compile(r'\d+(?:\.\d+)?|[^\W\d]\w*|[()+\-*/%]|\S')
_SIMBOLOS_DE_EXPRESSAO = '()[]{},;+-*/%<>=!'
_FECHAMENTOS_DE_EXPRESSAO = ')]};,'


def _parece_expressao(texto):
    """True se `texto` pode ser o lado direito de uma divisão: uma expressão (números, nomes, operadores,
    parênteses) sem dois valores seguidos, sem caracteres estranhos e sem terminar em operador.
    Um segundo `//` na linha encerra o trecho (o que vem depois é comentário)."""
    texto = texto.split('//', 1)[0]
    partes = _PARTES_DE_EXPRESSAO.findall(texto)
    if not partes:
        return False
    anterior_e_valor = False
    for parte in partes:
        e_valor = parte[0].isalnum() or parte[0] == '_'
        if e_valor and anterior_e_valor:
            return False                      # dois valores seguidos: é uma frase ("2 elevado a 3")
        if not e_valor and parte not in _SIMBOLOS_DE_EXPRESSAO:
            return False                      # caractere que não faz parte de contas ("?", "$"...)
        anterior_e_valor = e_valor
    return anterior_e_valor or partes[-1] in _FECHAMENTOS_DE_EXPRESSAO


class AdvakLexer:
    def __init__(self, source_code):
        # Bloco de Notas do Windows grava BOM UTF-8 no início do arquivo
        self.source = source_code.lstrip('﻿') if isinstance(source_code, str) else source_code
        self.tokens = []
        self._combined = re.compile(
            '|'.join(f'(?P<{n}>{p})' for n, p in TOKEN_SPECS), re.UNICODE)

    def tokenize(self):
        segments = self._split_templates(self.source)
        tokens = []
        for seg_type, seg_content, seg_line in segments:
            if seg_type == 'code':
                tokens.extend(self._tokenize_code(seg_content, seg_line))
            else:
                tokens.append({'type': 'TEMPLATE_STRING', 'value': seg_content,
                                'line': seg_line, 'col': 1})
        self.tokens = tokens
        return tokens

    def _split_templates(self, source):
        segments = []
        i = 0
        n = len(source)
        start = 0

        while i < n:
            ch = source[i]
            # Pula strings normais
            if ch in ('"', "'"):
                q = ch; i += 1
                while i < n:
                    if source[i] == '\\': i += 2; continue
                    if source[i] == q: i += 1; break
                    i += 1
                continue
            # Pula comentários de linha
            if ch == '/' and i+1 < n and source[i+1] == '/':
                while i < n and source[i] != '\n': i += 1
                continue
            # Pula comentários de bloco
            if ch == '/' and i+1 < n and source[i+1] == '*':
                i += 2
                while i < n-1:
                    if source[i] == '*' and source[i+1] == '/': i += 2; break
                    i += 1
                continue
            # Template string
            if ch == '`':
                code_before = source[start:i]
                if code_before:
                    segments.append(('code', code_before, source[:start].count('\n')+1))
                tmpl_line = source[:i].count('\n') + 1
                i += 1
                content = []
                while i < n:
                    c = source[i]
                    if c == '\\': content.append(source[i:i+2]); i += 2; continue
                    if c == '$' and i+1 < n and source[i+1] == '{':
                        content.append('${'); i += 2
                        depth = 1
                        while i < n and depth > 0:
                            ic = source[i]
                            if ic in ('"', "'"):
                                q2 = ic; content.append(ic); i += 1
                                while i < n:
                                    if source[i] == '\\': content.append(source[i:i+2]); i += 2; continue
                                    if source[i] == q2: content.append(source[i]); i += 1; break
                                    content.append(source[i]); i += 1
                            elif ic == '`':
                                # Template aninhado — captura respeitando ${} internos
                                content.append(ic); i += 1
                                inner_depth = 0
                                while i < n:
                                    nc = source[i]
                                    if nc == '\\':
                                        content.append(source[i:i+2]); i += 2; continue
                                    if nc == '$' and i+1 < n and source[i+1] == '{':
                                        # ${} dentro do template interno — rastreia profundidade
                                        content.append('${'); i += 2; inner_depth += 1; continue
                                    if nc == '{' and inner_depth > 0:
                                        inner_depth += 1; content.append(nc); i += 1; continue
                                    if nc == '}' and inner_depth > 0:
                                        inner_depth -= 1; content.append(nc); i += 1; continue
                                    if nc == '`' and inner_depth == 0:
                                        content.append(nc); i += 1; break
                                    content.append(nc); i += 1
                            elif ic == '{': depth += 1; content.append(ic); i += 1
                            elif ic == '}':
                                depth -= 1; content.append(ic); i += 1
                            else: content.append(ic); i += 1
                        continue
                    if c == '`': i += 1; break
                    content.append(c); i += 1
                segments.append(('template', ''.join(content), tmpl_line))
                start = i
                continue
            i += 1

        remaining = source[start:]
        if remaining:
            segments.append(('code', remaining, source[:start].count('\n')+1))
        return segments

    def _tokenize_code(self, code, base_line):
        tokens = []
        line = base_line
        col  = 1
        last_token_line = 0
        for m in self._combined.finditer(code):
            kind = m.lastgroup
            value = m.group()
            if kind in ('SKIP', 'BLOCK_COMMENT'):
                nl = value.count('\n')
                if nl: line += nl; col = len(value) - value.rfind('\n')
                else: col += len(value)
                continue

            if kind == 'COMMENT':
                # // is floor division ONLY when there is non-whitespace code
                # before it on the SAME LINE as the previous token.
                # Strategy: look at the raw source before the match position.
                prev = tokens[-1] if tokens else None
                src_before = m.string[:m.start()]
                # Text on the current line before the //
                line_prefix = src_before.rsplit('\n', 1)[-1]
                has_code_before = bool(line_prefix.strip())
                prev_same_line  = prev is not None and prev.get('line', -1) == line
                expr_type = prev is not None and prev['type'] in (
                    'NUMBER', 'FLOAT', 'IDENT', 'RPAREN', 'RBRACKET', 'BOOL')

                # Only treat as floor div if followed by digit or (
                rest_check = value[2:].lstrip()
                first_char = rest_check[0] if rest_check else ''
                looks_numeric = first_char.isdigit() or first_char in ('(', '-', '+')
                if looks_numeric and not _parece_expressao(rest_check):
                    looks_numeric = False

                # Fora de parênteses/colchetes, "valor   // texto" (2 ou mais espaços, ou um tab, antes do //)
                # é o estilo de comentário alinhado. A divisão se escreve "a // b" (um espaço) ou "a//b".
                abertos = (sum(1 for k in tokens if k['type'] in ('LPAREN', 'LBRACKET'))
                           - sum(1 for k in tokens if k['type'] in ('RPAREN', 'RBRACKET')))
                alinhado = line_prefix.endswith('\t') or line_prefix.endswith('  ')
                if looks_numeric and abertos <= 0 and alinhado:
                    looks_numeric = False

                if has_code_before and prev_same_line and expr_type and looks_numeric:
                    # Floor division: tokenize the rest after //
                    rest = value[2:]
                    tokens.append({'type': 'OP', 'value': '//', 'line': line, 'col': col})
                    col += 2
                    rest_stripped = rest.lstrip()
                    col += len(rest) - len(rest_stripped)
                    for m2 in self._combined.finditer(rest_stripped):
                        k2, v2 = m2.lastgroup, m2.group()
                        if k2 in ('NEWLINE',):
                            break
                        if k2 in ('BLOCK_COMMENT',):
                            break
                        if k2 == 'SKIP':
                            col += len(v2)
                            continue
                        if k2 == 'COMMENT':
                            # Could be another // (floor div again) or real comment
                            # Check: any non-skip token on this line before → floor div
                            rest2 = v2[2:].strip()
                            valida2 = _parece_expressao(rest2)
                            if valida2 and tokens and tokens[-1].get('line') == line:
                                tokens.append({'type':'OP','value':'//','line':line,'col':col})
                                col += 2
                                for m3 in self._combined.finditer(rest2):
                                    k3, v3 = m3.lastgroup, m3.group()
                                    if k3 in ('SKIP','COMMENT','NEWLINE','BLOCK_COMMENT'):
                                        break
                                    t3 = self._make_token(k3, v3, line, col)
                                    if t3:
                                        tokens.append(t3)
                                        last_token_line = line
                                    col += len(v3)
                            break
                        t2 = self._make_token(k2, v2, line, col)
                        if t2:
                            tokens.append(t2)
                            last_token_line = line
                        col += len(v2)
                else:
                    # Regular comment: skip it
                    nl = value.count('\n')
                    if nl:
                        line += nl
                        col = len(value) - value.rfind('\n')
                    else:
                        col += len(value)
                continue

            if kind == 'NEWLINE': line += 1; col = 1; continue
            if kind == 'MISMATCH':
                raise SyntaxError(f"[Advak] Caractere inesperado '{value}' na linha {line}, coluna {col}")
            tok = self._make_token(kind, value, line, col)
            if tok:
                tokens.append(tok)
                last_token_line = line
            col += len(value)
        return tokens

    # Literais booleanos e nulo — verificados ANTES das keywords
    _BOOL_TRUE  = {'verdadeiro', 'true'}
    _BOOL_FALSE = {'falso', 'false'}
    _NULL_VALS  = {'nulo', 'null', 'undefined'}

    def _make_token(self, kind, value, line, col):
        tok = {'type': kind, 'value': value, 'line': line, 'col': col}

        if kind == 'NUMBER':
            tok['value'] = int(value)

        elif kind == 'FLOAT':
            tok['value'] = float(value)

        elif kind in ('STRING', 'STRING_SINGLE'):
            # Strip quotes and process escape sequences
            raw = value[1:-1]
            # Process escape sequences in order
            result = []
            i = 0
            while i < len(raw):
                if raw[i] == '\\' and i + 1 < len(raw):
                    nxt = raw[i+1]
                    if   nxt == 'n':  result.append('\n');  i += 2
                    elif nxt == 't':  result.append('\t');  i += 2
                    elif nxt == 'r':  result.append('\r');  i += 2
                    elif nxt == '\\': result.append('\\'); i += 2
                    elif nxt == '"':  result.append('"');   i += 2
                    elif nxt == "'":  result.append("'");   i += 2
                    elif nxt == '0':  result.append('\0');  i += 2
                    else:             result.append(raw[i]); i += 1
                else:
                    result.append(raw[i]); i += 1
            tok['value'] = ''.join(result)
            tok['type']  = 'STRING'

        elif kind == 'IDENT':
            # ── Literais vêm ANTES da verificação de keywords ──
            if value in self._BOOL_TRUE:
                return {'type': 'BOOL', 'value': True,  'line': line, 'col': col}
            if value in self._BOOL_FALSE:
                return {'type': 'BOOL', 'value': False, 'line': line, 'col': col}
            if value in self._NULL_VALS:
                return {'type': 'NULL', 'value': None,  'line': line, 'col': col}
            if value in KEYWORDS:
                tok['type'] = 'KEYWORD'

        return tok
