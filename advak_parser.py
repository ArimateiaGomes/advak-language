"""
Advak Language 2.0 — Parser
Gera uma AST (Árvore Sintática Abstrata) a partir dos tokens.
"""

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ─── Utilitários ──────────────────────────────────────────────────────────

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def check(self, *types_or_values):
        t = self.peek()
        if t is None:
            return False
        return t['type'] in types_or_values or t['value'] in types_or_values

    def advance(self):
        t = self.tokens[self.pos]
        self.pos += 1
        self._last_token_line = t.get('line', 0)
        return t

    def consume(self, type_or_value, msg=None):
        t = self.peek()
        if t is None or (t['type'] != type_or_value and t['value'] != type_or_value):
            linha = t['line'] if t else '?'
            esperado = type_or_value
            encontrado = t['value'] if t else 'fim do arquivo'
            raise SyntaxError(
                msg or f"[Advak] Linha {linha}: esperado '{esperado}', encontrado '{encontrado}'"
            )
        return self.advance()

    def match(self, *types_or_values):
        for tv in types_or_values:
            if self.check(tv):
                return self.advance()
        return None

    def at_end(self):
        return self.pos >= len(self.tokens)

    # ─── Ponto de entrada ─────────────────────────────────────────────────────

    def parse(self):
        stmts = []
        while not self.at_end():
            s = self.parse_statement()
            if s is not None:
                stmts.append(s)
        return stmts

    # ─── Declarações ──────────────────────────────────────────────────────────

    def parse_statement(self):
        t = self.peek()
        if t is None:
            return None
        v = t['value']
        _linha = t.get('line', None)  # captura linha atual para anotação

        if v in ('seja', 'let', 'fixo', 'const'):
            _ln = t.get('line')
            _nd = self.parse_var_decl()
            if _nd and isinstance(_nd, dict) and not _nd.get('line'): _nd['line'] = _ln
            return _nd
        if v in ('assincrona', 'async'):
            # async function: 'assincrona funcao nome() {...}'
            _ln = t.get('line')
            self.advance()  # consume 'assincrona'
            _nd = self.parse_function_decl()
            if _nd and isinstance(_nd, dict):
                _nd['async'] = True
                if not _nd.get('line'): _nd['line'] = _ln
            return _nd

        if v in ('função', 'funcao', 'function'):
            _ln = t.get('line')
            _nd = self.parse_function_decl()
            if _nd and isinstance(_nd, dict) and not _nd.get('line'): _nd['line'] = _ln
            return _nd
        if v in ('interface',):
            return self.parse_interface_decl()
        if v in ('classe', 'class'):
            return self.parse_class_decl()
        if v in ('importar', 'import'):
            return self.parse_import_decl()
        if v in ('exportar', 'export'):
            return self.parse_export_decl()
        if v in ('retornar', 'return'):
            return self.parse_return()
        if v in ('se', 'if'):
            _ln = t.get('line')
            _nd = self.parse_if()
            if _nd and isinstance(_nd, dict) and not _nd.get('line'): _nd['line'] = _ln
            return _nd
        if v in ('enquanto', 'while'):
            return self.parse_while()
        if v in ('para', 'for'):
            return self.parse_for()
        if v in ('combinar', 'match'):
            return self.parse_match()
        if v in ('tentar', 'try'):
            return self.parse_try()
        if v in ('lançar', 'lancar', 'throw'):
            return self.parse_throw()
        if v in ('imprimir', 'print'):
            _ln = t.get('line')
            _nd = self.parse_print()
            if _nd and isinstance(_nd, dict) and not _nd.get('line'): _nd['line'] = _ln
            return _nd
        if v in ('produzir', 'yield'):
            return self.parse_yield()
        if v in ('fato', 'fact'):
            return self.parse_prolog_fact()
        if v in ('regra', 'rule'):
            return self.parse_prolog_rule()
        if v in ('consultar', 'query'):
            return self.parse_prolog_query()
        if v in ('estrutura', 'struct'):
            return self.parse_struct_decl()
        if v in ('enumeracao', 'enum'):
            return self.parse_enum_decl()
        if v in ('macro', 'definir'):
            return self.parse_macro_decl()
        if v in ('ref',):
            return self.parse_ref_stmt()
        if v in ('tipo', 'dados', 'data', 'type'):
            # BUG 8 FIX: tipo(x) → typeof call; tipo Nome { } → ADT declaration
            # Peek at the next token (after consuming 'tipo')
            self.advance()  # consume 'tipo'
            next_tok = self.peek()
            if next_tok and next_tok['type'] == 'LPAREN':
                self.consume('LPAREN')
                inner = self.parse_expression()
                self.consume('RPAREN')
                return {'type': 'typeof', 'expr': inner}
            # Restore: put back and let parse_adt_decl handle it
            self.pos -= 1
            return self.parse_adt_decl()
        if v in ('congelar', 'freeze'):
            return self.parse_freeze_stmt()
        if v in ('imutavel',):
            return self.parse_immutable_decl()
        if v in ('quebrar', 'break'):
            self.advance()
            self.match('SEMICOLON')
            return {'type': 'break'}
        if v in ('continuar', 'continue'):
            self.advance()
            self.match('SEMICOLON')
            return {'type': 'continue'}
        # senão/else sem if correspondente — consome o bloco e ignora
        if v in ('senão', 'else', 'senao'):
            self.advance()
            bloco = self.parse_block_or_stmt()
            return bloco  # executa o bloco mesmo sem o if
        if v in ('função', 'funcao', 'function') and self.peek(1) and self.peek(1)['value'] == '(':
            return self.parse_function_decl()
        if t['type'] == 'LCURLY':
            return self.parse_block()

        # Expressão / atribuição
        expr = self.parse_expression()
        self.match('SEMICOLON')
        return {'type': 'expr_stmt', 'expr': expr, 'line': _linha}

    # ─── Variáveis ────────────────────────────────────────────────────────────

    def parse_var_decl(self):
        _kw_tok = self.peek()
        _linha   = _kw_tok['line'] if _kw_tok else None
        keyword  = self.advance()['value']
        is_const = keyword in ('fixo', 'const')

        # ── Destructuring: seja {nome, idade} = obj  ou  seja [a, b] = lista ─
        t = self.peek()
        if t and t['type'] == 'LCURLY':
            # Object destructuring
            self.advance()
            fields = []
            while not self.check('RCURLY'):
                key = self.consume('IDENT')['value']
                alias = key
                default = None
                if self.match('COLON'):
                    alias = self.consume('IDENT')['value']
                if self.match('ASSIGN'):
                    default = self.parse_expression()
                fields.append({'key': key, 'alias': alias, 'default': default})
                if not self.check('RCURLY'):
                    self.consume('COMMA')
            self.consume('RCURLY')
            self.match('ASSIGN')
            value = self.parse_expression()
            self.match('SEMICOLON')
            return {'type': 'destructure_obj', 'fields': fields, 'value': value, 'const': is_const}

        if t and t['type'] == 'LBRACKET':
            # Array destructuring
            self.advance()
            items = []
            rest = None
            while not self.check('RBRACKET'):
                if self.check('SPREAD'):
                    self.advance()
                    rest = self.consume('IDENT')['value']
                    break
                if self.match('COMMA'):
                    items.append(None)  # skip
                    continue
                name = self.consume('IDENT')['value']
                default = None
                if self.match('ASSIGN'):
                    default = self.parse_expression()
                items.append({'name': name, 'default': default})
                if not self.check('RBRACKET'):
                    self.consume('COMMA')
            self.consume('RBRACKET')
            self.match('ASSIGN')
            value = self.parse_expression()
            self.match('SEMICOLON')
            return {'type': 'destructure_arr', 'items': items, 'rest': rest, 'value': value, 'const': is_const}

        # ── Declaração normal ─────────────────────────────────────────────────
        name = self.consume('IDENT')['value']
        tipo = None
        if self.check('COLON'):
            self.advance()
            tipo = self.advance()['value']
        value = None
        if self.match('ASSIGN'):
            value = self.parse_expression()
        self.match('SEMICOLON')
        return {'type': 'var_decl', 'name': name, 'value': value, 'const': is_const, 'tipo': tipo}

    # ─── Funções ──────────────────────────────────────────────────────────────

    def parse_function_decl(self):
        self.advance()  # 'função'/'function'
        is_async = False
        is_generator = False
        is_inline = False
        if self.check('async'):
            self.advance()
            is_async = True
        if self.peek() and self.peek()['value'] == 'inline':
            self.advance()
            is_inline = True
        # Generator: função* nome() { } ou função gerador nome() { }
        if self.peek() and self.peek()['type'] == 'OP' and self.peek()['value'] == '*':
            self.advance()
            is_generator = True
        if self.peek() and self.peek()['value'] in ('gerador', 'generator'):
            self.advance()
            is_generator = True
        name = self.consume('IDENT')['value']
        params = self.parse_params()
        body = self.parse_block()
        return {'type': 'func_decl', 'name': name, 'params': params, 'body': body,
                'async': is_async, 'generator': is_generator, 'inline': is_inline}

    def parse_params(self):
        self.consume('LPAREN')
        params = []
        while not self.check('RPAREN'):
            spread = bool(self.match('SPREAD'))
            # Destructuring param: {nome, idade} ou [a, b]
            t = self.peek()
            if t and t['type'] == 'LCURLY':
                # Object destructuring param
                self.advance()
                fields = []
                while not self.check('RCURLY'):
                    key = self.consume('IDENT')['value']
                    alias = key
                    default = None
                    if self.match('COLON'):
                        alias = self.consume('IDENT')['value']
                    if self.match('ASSIGN'):
                        default = self.parse_expression()
                    fields.append({'key': key, 'alias': alias, 'default': default})
                    if not self.check('RCURLY'):
                        self.consume('COMMA')
                self.consume('RCURLY')
                default_obj = None
                if self.match('ASSIGN'):
                    default_obj = self.parse_expression()
                params.append({'name': None, 'destructure': 'object', 'fields': fields,
                                'default': default_obj, 'spread': False})
            elif t and t['type'] == 'LBRACKET':
                # Array destructuring param
                self.advance()
                items = []
                rest = None
                while not self.check('RBRACKET'):
                    if self.check('SPREAD'):
                        self.advance()
                        rest = self.consume('IDENT')['value']
                        break
                    name = self.consume('IDENT')['value']
                    default = None
                    if self.match('ASSIGN'):
                        default = self.parse_expression()
                    items.append({'name': name, 'default': default})
                    if not self.check('RBRACKET'):
                        self.consume('COMMA')
                self.consume('RBRACKET')
                params.append({'name': None, 'destructure': 'array', 'items': items,
                                'rest': rest, 'default': None, 'spread': False})
            else:
                # Accept KEYWORD tokens as parameter names (e.g. 'tipo', 'valor')
                if self.peek() and self.peek()['type'] == 'KEYWORD':
                    name = self.advance()['value']
                else:
                    name = self.consume('IDENT')['value']
                default = None
                if self.match('ASSIGN'):
                    default = self.parse_expression()
                params.append({'name': name, 'default': default, 'spread': spread})
            if not self.check('RPAREN'):
                self.consume('COMMA')
        self.consume('RPAREN')
        return params

    # ─── Classes ──────────────────────────────────────────────────────────────

    def parse_import_decl(self):
        """
        importar "arquivo.dk"
        importar "arquivo.dk" como nome
        importar { func1, func2 } de "arquivo.dk"
        importar NomeModulo de "std:modulo"
        """
        self.advance()  # consume 'importar'/'import'
        t = self.peek()

        # importar { a, b, c } de "arquivo"
        if t and t['type'] == 'LCURLY':
            self.advance()
            names = []
            while not self.check('RCURLY'):
                nm = self.advance()['value']
                alias = nm
                if self.peek() and self.peek()['value'] in ('como', 'as'):
                    self.advance()
                    alias = self.advance()['value']
                names.append({'name': nm, 'alias': alias})
                self.match('COMMA')
            self.consume('RCURLY')
            # expect 'de'/'from'
            if self.peek() and self.peek()['value'] in ('de', 'from'):
                self.advance()
            source = self.consume('STRING')['value']
            self.match('SEMICOLON')
            return {'type': 'import_decl', 'mode': 'named', 'names': names, 'source': source}

        # importar NomeModulo de "arquivo"  OR  importar "arquivo"
        if t and t['type'] == 'IDENT':
            alias = self.advance()['value']
            if self.peek() and self.peek()['value'] in ('de', 'from'):
                self.advance()
                source = self.consume('STRING')['value']
                self.match('SEMICOLON')
                return {'type': 'import_decl', 'mode': 'namespace', 'alias': alias, 'source': source}
            # fallback: treat as source string? unlikely
            self.match('SEMICOLON')
            return {'type': 'import_decl', 'mode': 'namespace', 'alias': alias, 'source': alias}

        # importar "arquivo.dk"
        source = self.consume('STRING')['value']
        alias = None
        if self.peek() and self.peek()['value'] in ('como', 'as'):
            self.advance()
            alias = self.advance()['value']
        self.match('SEMICOLON')
        return {'type': 'import_decl', 'mode': 'default' if not alias else 'alias',
                'source': source, 'alias': alias}

    def parse_export_decl(self):
        """
        exportar função foo() { ... }
        exportar seja PI = 3.14
        exportar classe MinhaClasse { ... }
        exportar { foo, bar }
        """
        self.advance()  # consume 'exportar'/'export'
        t = self.peek()

        # exportar { foo, bar }
        if t and t['type'] == 'LCURLY':
            self.advance()
            names = []
            while not self.check('RCURLY'):
                nm = self.advance()['value']
                alias = nm
                if self.peek() and self.peek()['value'] in ('como', 'as'):
                    self.advance()
                    alias = self.advance()['value']
                names.append({'name': nm, 'alias': alias})
                self.match('COMMA')
            self.consume('RCURLY')
            return {'type': 'export_decl', 'mode': 'list', 'names': names}

        # exportar função/classe/seja/fixo/const/let
        inner = self.parse_statement()
        return {'type': 'export_decl', 'mode': 'inline', 'decl': inner}

    def parse_interface_decl(self):
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

    def parse_class_decl(self):
        self.advance()
        name = self.consume('IDENT')['value']
        superclass = None
        if self.match('herda', 'extends'):
            superclass = self.consume('IDENT')['value']
        interfaces = []
        t = self.peek()
        if t and t['value'] in ('implementa', 'implements'):
            self.advance()
            interfaces.append(self.consume('IDENT')['value'])
            while self.match('COMMA'):
                interfaces.append(self.consume('IDENT')['value'])
        self.consume('LCURLY')
        methods = []
        while not self.check('RCURLY'):
            is_async   = bool(self.match('async'))
            is_static  = False
            is_get     = False
            is_set     = False
            # static — IDENT com valor 'static'
            t = self.peek()
            if t and t['type'] == 'IDENT' and t['value'] == 'static':
                self.advance(); is_static = True
                t = self.peek()
            # get / set — IDENT seguido de outro IDENT (nome do acessor)
            if t and t['type'] == 'IDENT' and t['value'] in ('get', 'set'):
                next2 = self.tokens[self.pos+1] if self.pos+1 < len(self.tokens) else None
                if next2 and next2['type'] == 'IDENT':
                    is_get = t['value'] == 'get'
                    is_set = t['value'] == 'set'
                    self.advance()
                    t = self.peek()
            # nome do método — aceita IDENT ou KEYWORD
            t2 = self.peek()
            if t2 and t2['type'] in ('IDENT', 'KEYWORD'):
                mname = self.advance()['value']
            else:
                mname = self.consume('IDENT')['value']
            params = self.parse_params()
            body   = self.parse_block()
            methods.append({
                'name': mname, 'params': params, 'body': body,
                'async': is_async, 'static': is_static,
                'getter': is_get, 'setter': is_set
            })
        self.consume('RCURLY')
        return {
            'type': 'class_decl', 'name': name,
            'superclass': superclass, 'methods': methods,
            'interfaces': interfaces
        }

    # ─── Controle de fluxo ────────────────────────────────────────────────────

    def parse_return(self):
        self.advance()
        value = None
        if not self.check('SEMICOLON') and not self.check('RCURLY') and not self.at_end():
            value = self.parse_expression()
        self.match('SEMICOLON')
        return {'type': 'return', 'value': value}

    def parse_if(self):
        self.advance()
        self.consume('LPAREN')
        cond = self.parse_expression()
        self.consume('RPAREN')
        then = self.parse_block_or_stmt()
        else_ = None
        if self.check('senão', 'senao', 'else'):
            self.advance()
            else_ = self.parse_block_or_stmt()
        return {'type': 'if', 'cond': cond, 'then': then, 'else': else_}

    def parse_block_or_stmt(self):
        if self.check('LCURLY'):
            return self.parse_block()
        return self.parse_statement()

    def parse_while(self):
        self.advance()
        self.consume('LPAREN')
        cond = self.parse_expression()
        self.consume('RPAREN')
        body = self.parse_block()
        return {'type': 'while', 'cond': cond, 'body': body}

    def parse_for(self):
        self.advance()
        self.consume('LPAREN')
        # for (seja x em lista) ou for (init; cond; step)
        if self.peek(1) and self.peek(1)['value'] in ('em', 'in', 'of'):
            var = self.consume('IDENT')['value']
            self.advance()  # 'em'/'in'/'of'
            iterable = self.parse_expression()
            self.consume('RPAREN')
            body = self.parse_block()
            return {'type': 'for_in', 'var': var, 'iterable': iterable, 'body': body}
        # for clássico
        init = self.parse_statement()
        cond = self.parse_expression()
        self.consume('SEMICOLON')
        step = self.parse_expression()
        self.consume('RPAREN')
        body = self.parse_block()
        return {'type': 'for', 'init': init, 'cond': cond, 'step': step, 'body': body}

    # ─── Match / Case ─────────────────────────────────────────────────────────

    def parse_match(self):
        """
        Pattern Matching avançado (Advak 5.0):
          combinar valor {
            caso (x, y) se x > 0 => "positivo"   // guard + tuple pattern
            caso {nome, idade} => nome             // destructuring pattern
            caso [primeiro, ...resto] => primeiro  // list pattern
            caso Numero(n) se n > 10 => n          // type pattern
            caso _ => "outro"                      // wildcard
          }
        """
        self.advance()
        # Suporte: combinar expr { } OU combinar (expr) { }
        paren = bool(self.match('LPAREN'))
        subject = self.parse_expression()
        if paren:
            self.consume('RPAREN')
        self.consume('LCURLY')
        cases = []
        while not self.check('RCURLY') and not self.at_end():
            if self.check('caso', 'case'):
                self.advance()
                pattern = self._parse_pattern()
                guard = None
                # Guard: 'se'/'if' expr
                if self.peek() and self.peek()['value'] in ('se', 'if'):
                    self.advance()
                    guard = self.parse_expression()
                # Suporte a => (arrow) OU : (colon)
                if self.check('ARROW'):
                    self.advance()
                    expr = self.parse_expression()
                    self.match('SEMICOLON')
                    body = [{'type': 'return', 'value': expr}]
                else:
                    self.consume('COLON')
                    body = []
                    while not self.check('caso', 'case', 'padrão', 'default', 'RCURLY'):
                        body.append(self.parse_statement())
                cases.append({'pattern': pattern, 'guard': guard, 'body': body})
            elif self.check('padrão', 'default'):
                self.advance()
                if self.check('ARROW'):
                    self.advance()
                    expr = self.parse_expression()
                    self.match('SEMICOLON')
                    body = [{'type': 'return', 'value': expr}]
                else:
                    self.consume('COLON')
                    body = []
                    while not self.check('RCURLY'):
                        body.append(self.parse_statement())
                cases.append({'pattern': None, 'guard': None, 'body': body})
            else:
                break
        self.consume('RCURLY')
        return {'type': 'match', 'subject': subject, 'cases': cases}

    def _parse_pattern(self):
        """Analisa um padrão para pattern matching avançado."""
        t = self.peek()
        if t is None:
            raise SyntaxError("[Advak] Padrão esperado")

        # Wildcard: _ ou resto
        if t['type'] == 'IDENT' and t['value'] == '_':
            self.advance()
            return {'ptype': 'wildcard'}

        # Tuple pattern: (a, b, c)
        if t['type'] == 'LPAREN':
            self.advance()
            items = []
            while not self.check('RPAREN'):
                items.append(self._parse_pattern())
                if not self.check('RPAREN'):
                    self.consume('COMMA')
            self.consume('RPAREN')
            return {'ptype': 'tuple', 'items': items}

        # List pattern: [primeiro, ...resto]
        if t['type'] == 'LBRACKET':
            self.advance()
            items = []
            rest = None
            while not self.check('RBRACKET'):
                if self.check('SPREAD'):
                    self.advance()
                    rest = self.consume('IDENT')['value']
                    break
                items.append(self._parse_pattern())
                if not self.check('RBRACKET'):
                    self.consume('COMMA')
            self.consume('RBRACKET')
            return {'ptype': 'list', 'items': items, 'rest': rest}

        # Object destructuring pattern: {nome, idade} ou {nome: n}
        if t['type'] == 'LCURLY':
            self.advance()
            fields = []
            while not self.check('RCURLY'):
                key = self.consume('IDENT')['value']
                alias = key
                if self.match('COLON'):
                    alias = self.consume('IDENT')['value']
                fields.append({'key': key, 'alias': alias})
                if not self.check('RCURLY'):
                    self.consume('COMMA')
            self.consume('RCURLY')
            return {'ptype': 'object', 'fields': fields}

        # Type pattern: Tipo(binding) ou Tipo(b1, b2, ...) — ex: Retangulo(l, a)
        if t['type'] == 'IDENT':
            next_t = self.peek(1)
            if next_t and next_t['type'] == 'LPAREN':
                type_name = self.advance()['value']
                self.advance()  # LPAREN
                bindings_list = []
                while not self.check('RPAREN') and not self.at_end():
                    bindings_list.append(self.consume('IDENT')['value'])
                    if not self.check('RPAREN'):
                        self.consume('COMMA')
                self.consume('RPAREN')
                # Compatibilidade: binding único mantém campo 'binding'
                binding = bindings_list[0] if len(bindings_list) == 1 else None
                return {'ptype': 'type', 'type_name': type_name,
                        'binding': binding, 'bindings': bindings_list}
            # Condição: `caso n >= 9`, `caso x % 2 == 0` — expressão booleana
            if next_t and next_t['type'] in ('GTE', 'LTE', 'GT', 'LT', 'EQ', 'NEQ',
                                             'STRICT_EQ', 'STRICT_NEQ', 'AND', 'OR', 'OP', 'POWER'):
                return {'ptype': 'literal', 'value': self.parse_expression()}
            # Bind pattern: variável simples
            name = self.advance()['value']
            return {'ptype': 'bind', 'name': name}

        # Literal pattern: número, string, bool
        expr = self.parse_expression()
        return {'ptype': 'literal', 'value': expr}

    # ─── Exceções ─────────────────────────────────────────────────────────────

    def parse_try(self):
        self.advance()
        body = self.parse_block()
        catch_var = None
        catch_body = None
        finally_body = None
        if self.check('capturar', 'pegar', 'catch'):
            self.advance()
            self.consume('LPAREN')
            catch_var = self.consume('IDENT')['value']
            self.consume('RPAREN')
            catch_body = self.parse_block()
        if self.check('finalmente', 'finally'):
            self.advance()
            finally_body = self.parse_block()
        return {'type': 'try', 'body': body, 'catch_var': catch_var,
                'catch_body': catch_body, 'finally_body': finally_body}

    def parse_throw(self):
        self.advance()
        value = self.parse_expression()
        self.match('SEMICOLON')
        return {'type': 'throw', 'value': value}

    # ─── I/O ──────────────────────────────────────────────────────────────────

    def parse_print(self):
        self.advance()
        self.consume('LPAREN')
        args = []
        while not self.check('RPAREN'):
            args.append(self.parse_expression())
            if not self.check('RPAREN'):
                self.consume('COMMA')
        self.consume('RPAREN')
        self.match('SEMICOLON')
        return {'type': 'print', 'args': args}

    def parse_yield(self):
        """produzir expr  →  yield statement para generators"""
        self.advance()
        value = None
        if not self.check('SEMICOLON') and not self.check('RCURLY') and not self.at_end():
            # produzir* (delegação)
            delegate = bool(self.peek() and self.peek()['type'] == 'OP' and self.peek()['value'] == '*')
            if delegate:
                self.advance()
            value = self.parse_expression()
            self.match('SEMICOLON')
            return {'type': 'yield', 'value': value, 'delegate': delegate}
        self.match('SEMICOLON')
        return {'type': 'yield', 'value': None, 'delegate': False}

    def parse_prolog_fact(self):
        """
        fato pai(joao, maria)
        fact pai("joao", "maria")
        """
        self.advance()
        predicate = self.consume('IDENT')['value']
        self.consume('LPAREN')
        args = []
        while not self.check('RPAREN'):
            args.append(self.parse_expression())
            if not self.check('RPAREN'):
                self.consume('COMMA')
        self.consume('RPAREN')
        self.match('SEMICOLON')
        return {'type': 'prolog_fact', 'predicate': predicate, 'args': args}

    def parse_prolog_rule(self):
        """
        regra avo(X, Z) :- pai(X, Y), pai(Y, Z)
        rule ancestor(X, Z) :- parent(X, Y), ancestor(Y, Z)
        """
        self.advance()
        head_pred = self.consume('IDENT')['value']
        self.consume('LPAREN')
        head_args = []
        while not self.check('RPAREN'):
            head_args.append(self._parse_prolog_term())
            if not self.check('RPAREN'):
                self.consume('COMMA')
        self.consume('RPAREN')
        # :- (pode ser COLON + OP('-') ou simplesmente ASSIGN)
        t = self.peek()
        if t and t['type'] == 'COLON':
            self.advance()
            t2 = self.peek()
            if t2 and t2['type'] == 'OP' and t2['value'] == '-':
                self.advance()
        elif t and t['type'] == 'ASSIGN':
            self.advance()
        body_goals = []
        while not self.check('SEMICOLON') and not self.at_end() and not self.check('RCURLY'):
            pred = self.consume('IDENT')['value']
            self.consume('LPAREN')
            gargs = []
            while not self.check('RPAREN'):
                gargs.append(self._parse_prolog_term())
                if not self.check('RPAREN'):
                    self.consume('COMMA')
            self.consume('RPAREN')
            body_goals.append({'predicate': pred, 'args': gargs})
            if not self.match('COMMA'):
                break
        self.match('SEMICOLON')
        return {'type': 'prolog_rule', 'head': {'predicate': head_pred, 'args': head_args},
                'body': body_goals}

    def _parse_prolog_term(self):
        """Analisa um termo Prolog: variável (maiúscula), átomo ou literal."""
        t = self.peek()
        if t and t['type'] == 'IDENT':
            val = t['value']
            self.advance()
            # Variável Prolog: começa com maiúscula ou é _
            if val[0].isupper() or val == '_':
                return {'pterm': 'var', 'name': val}
            return {'pterm': 'atom', 'value': val}
        return {'pterm': 'literal', 'expr': self.parse_expression()}

    def parse_prolog_query(self):
        """
        consultar pai(joao, X)   →  retorna lista de soluções
        seja resultado = consultar avo(joao, X)
        """
        self.advance()
        predicate = self.consume('IDENT')['value']
        self.consume('LPAREN')
        args = []
        while not self.check('RPAREN'):
            args.append(self._parse_prolog_term())
            if not self.check('RPAREN'):
                self.consume('COMMA')
        self.consume('RPAREN')
        self.match('SEMICOLON')
        return {'type': 'prolog_query', 'predicate': predicate, 'args': args}

    # ─── C/C++ — Struct ───────────────────────────────────────────────────────

    def parse_struct_decl(self):
        """
        estrutura Ponto { x: Numero, y: Numero }
        struct Cor { r: Numero = 0, g: Numero = 0, b: Numero = 0 }
        """
        self.advance()
        name = self.consume('IDENT')['value']
        self.consume('LCURLY')
        fields = []
        while not self.check('RCURLY') and not self.at_end():
            fname = self.consume('IDENT')['value']
            ftype = None
            if self.match('COLON'):
                t = self.peek()
                if t and t['type'] in ('IDENT', 'KEYWORD'):
                    ftype = self.advance()['value']
            fdefault = None
            if self.match('ASSIGN'):
                fdefault = self.parse_expression()
            fields.append({'name': fname, 'type': ftype, 'default': fdefault})
            self.match('COMMA')
            self.match('SEMICOLON')
        self.consume('RCURLY')
        self.match('SEMICOLON')
        return {'type': 'struct_decl', 'name': name, 'fields': fields}

    # ─── C/C++ — Enum ─────────────────────────────────────────────────────────

    def parse_enum_decl(self):
        """
        enumeracao Direcao { Norte = 0, Sul = 1, Leste = 2, Oeste = 3 }
        enum Status { Ativo, Inativo, Pendente }
        enum Forma { Circulo(Numero), Retangulo(Numero, Numero) }
        """
        self.advance()
        name = self.consume('IDENT')['value']
        self.consume('LCURLY')
        variants = []
        counter = 0
        while not self.check('RCURLY') and not self.at_end():
            vname = self.consume('IDENT')['value']
            vval = None
            if self.match('ASSIGN'):
                vval = self.parse_expression()
                if isinstance(vval, dict) and vval.get('type') == 'number':
                    counter = vval['value'] + 1
                else:
                    counter += 1
            else:
                vval = {'type': 'number', 'value': counter}
                counter += 1
            payload = []
            if self.check('LPAREN'):
                self.advance()
                while not self.check('RPAREN'):
                    pt = self.peek()
                    if pt and pt['type'] in ('IDENT', 'KEYWORD'):
                        payload.append(self.advance()['value'])
                    if not self.check('RPAREN'):
                        self.consume('COMMA')
                self.consume('RPAREN')
            variants.append({'name': vname, 'value': vval, 'payload': payload})
            self.match('COMMA')
        self.consume('RCURLY')
        self.match('SEMICOLON')
        return {'type': 'enum_decl', 'name': name, 'variants': variants}

    # ─── C/C++ — Macro ────────────────────────────────────────────────────────

    def parse_macro_decl(self):
        """
        macro MAX(a, b) => a > b ? a : b
        definir PI 3.14159265358979
        macro QUADRADO(x) => x * x
        """
        self.advance()
        name = self.consume('IDENT')['value']
        params = []
        if self.check('LPAREN'):
            self.advance()
            while not self.check('RPAREN'):
                params.append(self.consume('IDENT')['value'])
                if not self.check('RPAREN'):
                    self.consume('COMMA')
            self.consume('RPAREN')
        if self.check('ARROW'):
            self.advance()
        body = self.parse_expression()
        self.match('SEMICOLON')
        return {'type': 'macro_decl', 'name': name, 'params': params, 'body': body}

    # ─── C/C++ — Ref/Ponteiro ─────────────────────────────────────────────────

    def parse_ref_stmt(self):
        """
        ref ptr = variavel   // cria referência mutável
        """
        self.advance()
        name = self.consume('IDENT')['value']
        self.consume('ASSIGN')
        target = self.parse_expression()
        self.match('SEMICOLON')
        return {'type': 'ref_decl', 'name': name, 'target': target}

    # ─── Haskell — Tipo Algébrico (ADT) ──────────────────────────────────────

    def parse_adt_decl(self):
        """
        Tipo Algébrico de Dados (ADT) estilo Haskell:

          tipo Arvore {
            Folha,
            No(Arvore, Numero, Arvore)
          }

          tipo Resultado {
            Ok(valor),
            Erro(mensagem)
          }

          tipo Lista {
            Vazia,
            Cons(cabeca, cauda: Lista)
          }
        """
        self.advance()   # consome 'tipo'/'dados'
        name = self.consume('IDENT')['value']

        # Parâmetros de tipo genérico: tipo Maybe(T) { ... }
        type_params = []
        if self.check('LPAREN'):
            self.advance()
            while not self.check('RPAREN') and not self.at_end():
                type_params.append(self.consume('IDENT')['value'])
                if not self.check('RPAREN'):
                    self.consume('COMMA')
            self.consume('RPAREN')

        self.consume('LCURLY')
        variants = []
        while not self.check('RCURLY') and not self.at_end():
            vname = self.consume('IDENT')['value']
            fields = []
            if self.check('LPAREN'):
                self.advance()
                while not self.check('RPAREN') and not self.at_end():
                    # campo: nome ou nome: Tipo
                    fname = self.consume('IDENT')['value']
                    ftype = None
                    if self.match('COLON'):
                        t = self.peek()
                        if t and t['type'] in ('IDENT', 'KEYWORD'):
                            ftype = self.advance()['value']
                    fields.append({'name': fname, 'type': ftype})
                    if not self.check('RPAREN'):
                        self.consume('COMMA')
                self.consume('RPAREN')
            variants.append({'name': vname, 'fields': fields})
            self.match('COMMA')
        self.consume('RCURLY')
        self.match('SEMICOLON')
        return {'type': 'adt_decl', 'name': name,
                'type_params': type_params, 'variants': variants}

    # ─── Haskell — Imutabilidade ──────────────────────────────────────────────

    def parse_freeze_stmt(self):
        """
        congelar variavel        // torna variável imutável
        congelar objeto          // congela objeto profundamente
        """
        self.advance()
        target = self.parse_expression()
        self.match('SEMICOLON')
        return {'type': 'freeze_stmt', 'target': target}

    def parse_immutable_decl(self):
        """
        imutavel nome = expr     // declara variável imutável profunda
        """
        self.advance()
        # Suporte a destructuring também
        t = self.peek()
        if t and t['type'] == 'LCURLY':
            # imutavel {a, b} = obj
            node = self.parse_var_decl.__func__(self) if False else None
            # Reutiliza parse_var_decl mas força const e deep-freeze
            self.advance()  # {
            fields = []
            while not self.check('RCURLY'):
                key = self.consume('IDENT')['value']
                alias = key
                if self.match('COLON'):
                    alias = self.consume('IDENT')['value']
                fields.append({'key': key, 'alias': alias, 'default': None})
                if not self.check('RCURLY'):
                    self.consume('COMMA')
            self.consume('RCURLY')
            self.match('ASSIGN')
            value = self.parse_expression()
            self.match('SEMICOLON')
            return {'type': 'immutable_obj_decl', 'fields': fields, 'value': value}

        name = self.consume('IDENT')['value']
        self.consume('ASSIGN')
        value = self.parse_expression()
        self.match('SEMICOLON')
        return {'type': 'immutable_decl', 'name': name, 'value': value}

    # ─── Bloco ────────────────────────────────────────────────────────────────

    def parse_block(self):
        self.consume('LCURLY')
        stmts = []
        while not self.check('RCURLY') and not self.at_end():
            s = self.parse_statement()
            if s:
                stmts.append(s)
        self.consume('RCURLY')
        return {'type': 'block', 'body': stmts}

    # ─── Expressões (precedência crescente) ───────────────────────────────────

    def parse_expression(self):
        return self.parse_assignment()

    def parse_assignment(self):
        left = self.parse_pipeline()
        if self.check('ASSIGN', 'ASSIGN_OP'):
            op = self.advance()['value']
            right = self.parse_assignment()
            return {'type': 'assign', 'op': op, 'target': left, 'value': right}
        return left

    def parse_pipeline(self):
        left = self.parse_ternary()
        while self.check('PIPE'):
            self.advance()
            func = self.parse_ternary()
            left = {'type': 'call', 'func': func, 'args': [left]}
        return left

    def parse_ternary(self):
        cond = self.parse_or()
        if self.check('TERNARY') or (self.peek() and self.peek()['value'] == '?'
                                      and not self.check('OPTIONAL_CHAIN', 'NULL_COALESCE')):
            # Verifica se há '?' que não seja '?.' ou '??'
            t = self.peek()
            if t and t['type'] not in ('OPTIONAL_CHAIN', 'NULL_COALESCE') and t.get('value') == '?':
                self.advance()
                then = self.parse_expression()
                self.consume('COLON')
                else_ = self.parse_expression()
                return {'type': 'ternary', 'cond': cond, 'then': then, 'else': else_}
        return cond

    def parse_or(self):
        left = self.parse_and()
        while self.check('OR') or (self.peek() and self.peek().get('type') in ('KEYWORD','IDENT') and self.peek().get('value') in ('ou','or')):
            op = self.advance()['value']
            right = self.parse_and()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.check('AND') or (self.peek() and self.peek().get('type') in ('KEYWORD','IDENT') and self.peek().get('value') in ('e','and')):
            op = self.advance()['value']
            right = self.parse_equality()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_equality(self):
        left = self.parse_bitwise_or()
        while self.check('EQ', 'NEQ', 'STRICT_EQ', 'STRICT_NEQ'):
            op = self.advance()['value']
            right = self.parse_bitwise_or()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_bitwise_or(self):
        left = self.parse_bitwise_xor()
        while self.check('BIT_OR'):
            self.advance()
            right = self.parse_bitwise_xor()
            left = {'type': 'binop', 'op': '|', 'left': left, 'right': right}
        return left

    def parse_bitwise_xor(self):
        left = self.parse_bitwise_and()
        while self.check('BIT_XOR'):
            self.advance()
            right = self.parse_bitwise_and()
            left = {'type': 'binop', 'op': '^', 'left': left, 'right': right}
        return left

    def parse_bitwise_and(self):
        left = self.parse_comparison()
        while self.check('BIT_AND'):
            self.advance()
            right = self.parse_comparison()
            left = {'type': 'binop', 'op': '&', 'left': left, 'right': right}
        return left

    def parse_comparison(self):
        left = self.parse_null_coalesce()
        while self.check('LT', 'GT', 'LTE', 'GTE'):
            op = self.advance()['value']
            right = self.parse_null_coalesce()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        t = self.peek()
        if t and t['value'] in ('instanceof', 'e_instancia', 'eh_instancia'):
            self.advance()
            t2 = self.peek()
            if t2 and t2['type'] in ('IDENT','KEYWORD'):
                cls_name = self.advance()['value']
            else:
                cls_name = self.consume('IDENT')['value']
            left = {'type': 'instanceof', 'obj': left, 'class': cls_name}
        return left

    def parse_null_coalesce(self):
        left = self.parse_additive()
        while self.check('NULL_COALESCE'):
            self.advance()
            right = self.parse_additive()
            left = {'type': 'null_coalesce', 'left': left, 'right': right}
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek() and self.peek()['type'] == 'OP' and self.peek()['value'] in ('+', '-'):
            op = self.advance()['value']
            right = self.parse_multiplicative()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_multiplicative(self):
        left = self.parse_power()
        while self.peek() and (
            (self.peek()['type'] == 'OP' and self.peek()['value'] in ('*', '/', '//', '%'))
            or self.peek()['type'] in ('LSHIFT', 'RSHIFT')
        ):
            op = self.advance()['value']
            right = self.parse_power()
            left = {'type': 'binop', 'op': op, 'left': left, 'right': right}
        return left

    def parse_power(self):
        left = self.parse_unary()
        if self.check('POWER'):
            self.advance()
            right = self.parse_power()  # direito-associativo
            return {'type': 'binop', 'op': '**', 'left': left, 'right': right}
        return left

    def parse_unary(self):
        # Handle NOT: !, not, nao (but NOT when '!' is inside a string)
        t = self.peek()
        is_not_op = (
            self.check('NOT') or  # type == 'NOT'
            (t and t.get('type') in ('KEYWORD','IDENT') and t.get('value') in ('nao', 'not')) or
            (t and t.get('type') == 'OP' and t.get('value') == '!')
        )
        if is_not_op:
            self.advance()
            operand = self.parse_unary()
            return {'type': 'unary', 'op': '!', 'operand': operand}
        if self.peek() and self.peek()['type'] == 'OP' and self.peek()['value'] == '-':
            self.advance()
            operand = self.parse_unary()
            return {'type': 'unary', 'op': '-', 'operand': operand}
        # deref ptr  — desreferencia um ponteiro/ref
        if self.peek() and self.peek()['value'] == 'deref':
            self.advance()
            operand = self.parse_unary()
            return {'type': 'deref', 'expr': operand}
        # endereco variavel  — pega endereço (alias de ref temporário)
        if self.peek() and self.peek()['value'] == 'endereco':
            self.advance()
            operand = self.parse_unary()
            return {'type': 'deref', 'expr': operand}
        # aguarda (await) expression
        if self.check('aguarda', 'await'):
            self.advance()
            operand = self.parse_unary()
            return {'type': 'await', 'value': operand}
        # ~x — bitwise NOT
        if self.check('BIT_NOT'):
            self.advance()
            operand = self.parse_unary()
            return {'type': 'unary', 'op': '~', 'operand': operand}

        # Prefix ++ and --
        if self.check('INCREMENT'):
            self.advance()
            operand = self.parse_call_chain()
            return {'type': 'assign', 'op': '=',
                    'target': operand,
                    'value': {'type': 'binop', 'op': '+', 'left': operand,
                              'right': {'type': 'number', 'value': 1}}}
        if self.check('DECREMENT'):
            self.advance()
            operand = self.parse_call_chain()
            return {'type': 'assign', 'op': '=',
                    'target': operand,
                    'value': {'type': 'binop', 'op': '-', 'left': operand,
                              'right': {'type': 'number', 'value': 1}}}
        return self.parse_call_chain()

    def parse_call_chain(self):
        _start_line = self.peek()['line'] if self.peek() else 0
        expr = self.parse_primary()
        # Use the line of the LAST token consumed (not next token)
        _expr_line = getattr(self, '_last_token_line', _start_line) or _start_line
        while True:
            if self.check('LPAREN'):
                args = self.parse_args()
                expr = {'type': 'call', 'func': expr, 'args': args}
            elif self.check('LBRACKET'):
                # Only subscript on same line — prevents [0]\n[1,2,3] ambiguity
                _cur_line = self.peek()['line'] if self.peek() else 0
                if _cur_line > 0 and _cur_line > _expr_line and _expr_line > 0:
                    break  # [ on new line = new statement
                self.advance()
                index = self.parse_expression()
                self.consume('RBRACKET')
                expr = {'type': 'index', 'obj': expr, 'index': index}
                _expr_line = self.peek()['line'] if self.peek() else _expr_line
            elif self.check('DOT'):
                self.advance()
                t = self.peek()
                if t and t['type'] in ('IDENT', 'KEYWORD'):
                    prop = self.advance()['value']
                else:
                    prop = self.consume('IDENT')['value']
                expr = {'type': 'member', 'obj': expr, 'prop': prop}
            elif self.check('OPTIONAL_CHAIN'):
                self.advance()
                t = self.peek()
                if t and t['type'] in ('IDENT', 'KEYWORD'):
                    prop = self.advance()['value']
                else:
                    prop = self.consume('IDENT')['value']
                expr = {'type': 'optional_member', 'obj': expr, 'prop': prop}
            elif self.check('INCREMENT') and expr.get('type') in ('ident','member','index'):
                self.advance()
                expr = {'type': 'assign', 'op': '=',
                        'target': expr,
                        'value': {'type': 'binop', 'op': '+',
                                  'left': expr,
                                  'right': {'type': 'number', 'value': 1}}}
            elif self.check('DECREMENT') and expr.get('type') in ('ident','member','index'):
                self.advance()
                expr = {'type': 'assign', 'op': '=',
                        'target': expr,
                        'value': {'type': 'binop', 'op': '-',
                                  'left': expr,
                                  'right': {'type': 'number', 'value': 1}}}
            else:
                break
        return expr

    def parse_args(self):
        self.consume('LPAREN')
        args = []
        while not self.check('RPAREN'):
            if self.check('SPREAD'):
                self.advance()
                args.append({'type': 'spread', 'value': self.parse_expression()})
            else:
                args.append(self.parse_expression())
            if not self.check('RPAREN'):
                self.consume('COMMA')
        self.consume('RPAREN')
        return args

    def parse_primary(self):
        t = self.peek()
        if t is None:
            raise SyntaxError("[Advak] Fim inesperado do arquivo")

        # Literais
        if t['type'] == 'NUMBER':
            self.advance()
            return {'type': 'number', 'value': t['value']}

        if t['type'] == 'FLOAT':
            self.advance()
            return {'type': 'float', 'value': t['value']}

        if t['type'] == 'STRING':
            self.advance()
            return {'type': 'string', 'value': t['value']}

        if t['type'] == 'TEMPLATE_STRING':
            self.advance()
            return {'type': 'template_string', 'value': t['value']}

        if t['type'] == 'BOOL':
            self.advance()
            return {'type': 'bool', 'value': t['value']}

        if t['type'] == 'NULL':
            self.advance()
            return {'type': 'null'}

        # Lista literal [...]
        if t['type'] == 'LBRACKET':
            return self.parse_list_literal()

        # Mapa literal {...}
        if t['type'] == 'LCURLY':
            return self.parse_map_literal()

        # Parênteses / lambda
        if t['type'] == 'LPAREN':
            return self.parse_paren_or_lambda()

        # Funções anônimas: função(...) { }
        if t['value'] in ('função', 'function'):
            return self.parse_anonymous_function()

        # async função
        if t['value'] == 'async':
            return self.parse_async_expr()

        # await / aguarda
        if t['value'] in ('aguarda', 'await'):
            self.advance()
            expr = self.parse_unary()
            return {'type': 'await', 'expr': expr}

        # combinar/match como expressão (ex: retornar combinar x { ... })
        if t['value'] in ('combinar', 'match'):
            return self.parse_match()

        # estrutura/enum como expressão — declaração inline usada em expr_stmt
        if t['value'] in ('estrutura', 'struct'):
            return self.parse_struct_decl()
        if t['value'] in ('enumeracao', 'enum'):
            return self.parse_enum_decl()
        # tipo algébrico como expressão
        # Only treat 'tipo'/'dados' as ADT keyword when followed by IDENT (type name)
        # Otherwise treat as variable reference (e.g. function param named 'tipo')
        if t['value'] in ('tipo', 'dados', 'data'):
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok['type'] == 'IDENT':
                return self.parse_adt_decl()
            elif next_tok and next_tok['type'] == 'LPAREN':
                # BUG 8 FIX: tipo(x) → typeof call
                self.advance()  # consume 'tipo'
                self.consume('LPAREN')
                inner = self.parse_expression()
                self.consume('RPAREN')
                return {'type': 'typeof', 'expr': inner}
            else:
                # Treat as identifier (variable reference)
                self.advance()
                return {'type': 'ident', 'name': t['value']}

        # novo / new — só é operador se seguido de IDENT (nome de classe)
        # Ex: novo Animal("Rex") — operador new
        # Ex: seja novo = banco.inserir(...) — variável chamada 'novo'
        if t['value'] in ('novo', 'new'):
            # Lookahead: próximo token é IDENT? → operador new
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok['type'] == 'IDENT':
                self.advance()  # consome 'novo'
                name = self.consume('IDENT')['value']
                args = self.parse_args() if self.check('LPAREN') else []
                return {'type': 'new', 'class': name, 'args': args}
            # Senão, trata como identificador comum
            self.advance()
            return {'type': 'ident', 'name': t['value']}

        # Identificador
        if t['type'] == 'IDENT':
            self.advance()
            return {'type': 'ident', 'name': t['value']}

        # Palavras-chave usadas como expressão (ex: ai_perguntar(...))
        if t['type'] == 'KEYWORD':
            self.advance()
            if self.check('LPAREN'):
                args = self.parse_args()
                return {'type': 'builtin_call', 'name': t['value'], 'args': args}
            return {'type': 'ident', 'name': t['value']}

        raise SyntaxError(f"[Advak] Linha {t['line']}: token inesperado '{t['value']}'")

    def parse_list_literal(self):
        self.consume('LBRACKET')
        items = []
        while not self.check('RBRACKET'):
            if self.check('SPREAD'):
                self.advance()
                items.append({'type': 'spread', 'value': self.parse_expression()})
            else:
                items.append(self.parse_expression())
            # Allow trailing comma [1, 2, 3,]
            if self.check('COMMA'):
                self.advance()
        self.consume('RBRACKET')
        return {'type': 'list', 'items': items}

    def parse_map_literal(self):
        self.consume('LCURLY')
        pairs = []
        while not self.check('RCURLY'):
            # BUG 2 FIX: spread in object literal {...obj, key: val}
            if self.check('SPREAD'):
                self.advance()
                spread_val = self.parse_expression()
                pairs.append({'spread': True, 'value': spread_val})
                if self.check('COMMA'):
                    self.advance()
                continue
            tok = self.peek()
            next_tok = self.peek(1)
            # Allow IDENT or KEYWORD as map key when followed by COLON
            # This lets reserved words like 'tipo', 'valor', 'nome' be used as map keys
            if tok and tok['type'] in ('IDENT', 'KEYWORD') and \
               next_tok and next_tok['type'] == 'COLON':
                key = self.advance()['value']
                self.consume('COLON')
                value = self.parse_expression()
                pairs.append({'key': key, 'value': value})
            elif tok and tok['type'] == 'STRING':
                key = self.advance()['value']
                self.consume('COLON')
                value = self.parse_expression()
                pairs.append({'key': key, 'value': value})
            elif tok and tok['type'] == 'NUMBER' and \
                 next_tok and next_tok['type'] == 'COLON':
                key = str(self.advance()['value'])
                self.consume('COLON')
                value = self.parse_expression()
                pairs.append({'key': key, 'value': value})
            else:
                # Shorthand: { nome } → { nome: nome }
                name = self.consume('IDENT')['value']
                pairs.append({'key': name, 'value': {'type': 'ident', 'name': name}})
            # BUG 9 FIX: allow trailing comma {a:1, b:2,}
            if self.check('COMMA'):
                self.advance()
        self.consume('RCURLY')
        return {'type': 'map', 'pairs': pairs}

    def parse_paren_or_lambda(self):
        self.consume('LPAREN')
        saved_pos = self.pos

        # ── Lookahead: verifica se é definitivamente lambda ──────────────────
        # Um lambda tem a forma: () => ou (a) => ou (a, b) => ou (a, b=x) =>
        # Precisamos ter certeza ANTES de consumir qualquer token.
        if self._is_lambda_ahead():
            # É lambda — parseia params normalmente
            params = []
            while not self.check('RPAREN'):
                spread = bool(self.match('SPREAD'))
                name = self.consume('IDENT')['value']
                default = None
                if self.check('ASSIGN'):
                    self.advance()
                    default = self.parse_expression()
                params.append({'name': name, 'default': default, 'spread': spread})
                if not self.check('RPAREN'):
                    self.consume('COMMA')
            self.consume('RPAREN')
            self.consume('ARROW')  # consome '=>'
            if self.check('LCURLY'):
                body = self.parse_block()
            else:
                body = {'type': 'return', 'value': self.parse_expression()}
            return {'type': 'lambda', 'params': params, 'body': body}

        # ── Não é lambda — parseia como expressão entre parênteses ───────────
        expr = self.parse_expression()
        self.consume('RPAREN')
        return expr

    def _is_lambda_ahead(self):
        """
        Lookahead sem consumir: verifica se os tokens formam params de lambda.
        Retorna True se encontrar: (ident, ident, ...) =>
        ou () =>  ou (...ident) =>
        """
        pos = self.pos  # já consumiu LPAREN — começa aqui
        toks = self.tokens
        n = len(toks)

        # Caso especial: () =>
        if pos < n and toks[pos]['type'] == 'RPAREN':
            return (pos + 1 < n and toks[pos + 1]['type'] == 'ARROW')

        # Varre os params: devem ser IDENT (com , entre eles) + RPAREN + ARROW
        i = pos
        while i < n:
            t = toks[i]
            # Aceita spread ...
            if t['type'] == 'SPREAD':
                i += 1
                continue
            # Deve ser IDENT
            if t['type'] != 'IDENT':
                return False
            i += 1
            if i >= n: return False
            t2 = toks[i]
            # Após ident: pode ter = (default), , (próximo param), ) (fim)
            if t2['type'] == 'ASSIGN':
                # Tem default: pula até a próxima COMMA ou RPAREN
                i += 1
                depth = 0
                while i < n:
                    tt = toks[i]
                    if tt['type'] in ('LPAREN', 'LCURLY', 'LBRACKET'): depth += 1
                    elif tt['type'] in ('RPAREN', 'RCURLY', 'RBRACKET'):
                        if depth == 0: break
                        depth -= 1
                    elif tt['type'] == 'COMMA' and depth == 0: break
                    i += 1
                if i >= n: return False
                t2 = toks[i]
            if t2['type'] == 'COMMA':
                i += 1  # próximo param
                continue
            if t2['type'] == 'RPAREN':
                # Verifica se tem ARROW depois do RPAREN
                return (i + 1 < n and toks[i + 1]['type'] == 'ARROW')
            return False
        return False

    def parse_anonymous_function(self):
        self.advance()  # 'função'
        is_generator = False
        # função* ou função gerador
        if self.peek() and self.peek()['type'] == 'OP' and self.peek()['value'] == '*':
            self.advance()
            is_generator = True
        if self.peek() and self.peek()['value'] in ('gerador', 'generator'):
            self.advance()
            is_generator = True
        name = None
        if self.peek() and self.peek()['type'] == 'IDENT':
            name = self.advance()['value']
        params = self.parse_params()
        body = self.parse_block()
        return {'type': 'lambda', 'name': name, 'params': params, 'body': body,
                'generator': is_generator}

    def parse_async_expr(self):
        self.advance()  # 'async'
        if self.check('função', 'function'):
            node = self.parse_anonymous_function()
            node['async'] = True
            return node
        expr = self.parse_unary()
        return {'type': 'async_expr', 'expr': expr}


# ── Patch: adiciona suporte a switch/case inglês e super ──────────────────────
# O parser já trata match/case, class/extends, if/else, for/while, try/catch.
# Aqui garantimos que 'switch' redireciona para parse_match,
# e 'super' funciona como expressão.
_orig_parse_statement = Parser.parse_statement

def _patched_parse_statement(self):
    t = self.peek()
    if t and t['value'] == 'switch':
        t['value'] = 'match'   # reescreve token em memória
    if t and t['value'] == 'var':
        t['value'] = 'let'
    return _orig_parse_statement(self)

Parser.parse_statement = _patched_parse_statement

_orig_primary = Parser.parse_primary

def _patched_primary(self):
    t = self.peek()
    # 'this' como alias de 'isso'
    # BUG FIX: only intercept if NOT a STRING token
    if t and t['value'] == 'this' and t['type'] != 'STRING':
        self.advance()
        return {'type': 'ident', 'name': 'isso'}
    # 'super' → acessa superclasse via 'isso' (simplificado)
    # BUG FIX: only intercept if NOT a STRING token (e.g. "super" in a list should stay as string)
    if t and t['value'] == 'super' and t['type'] != 'STRING':
        self.advance()
        return {'type': 'ident', 'name': 'super'}
    # 'undefined' → null
    if t and t['value'] == 'undefined' and t['type'] != 'STRING':
        self.advance()
        return {'type': 'null'}
    # Palavras reservadas usadas como identificadores (ex: gui.switch, gui.toggle)
    if t and t['type'] == 'KEYWORD' and t['value'] in (
        'switch','case','default','toggle','in','of','async','await'
    ):
        self.advance()
        return {'type': 'ident', 'name': t['value']}
    return _orig_primary(self)

Parser.parse_primary = _patched_primary