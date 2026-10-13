"""
Testes da tipagem opcional: lexer (->), parser (anotações), advak_tipos (conferência) e interpretador.
O comportamento em programas .dk está em testes/tipagem.dk.

Rodar:  python -I testes/test_tipagem.py
"""
import asyncio
import glob
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from advak_lexer import AdvakLexer   # noqa: E402
from advak_parser import Parser      # noqa: E402
import advak_tipos as T              # noqa: E402


def ast(codigo):
    return Parser(AdvakLexer(codigo).tokenize()).parse()


def nos(codigo):
    raiz = ast(codigo)
    return raiz['body'] if isinstance(raiz, dict) else raiz


def tipo(texto):
    """Lê uma anotação isolada, ex.: 'lista[numero]?'."""
    return Parser(AdvakLexer(texto).tokenize()).parse_tipo()


class TesteLexer(unittest.TestCase):
    def tokens(self, c):
        return [t['type'] for t in AdvakLexer(c).tokenize()]

    def test_seta_de_retorno(self):
        self.assertEqual(self.tokens("f() -> numero"), ['IDENT', 'LPAREN', 'RPAREN', 'RET_ARROW', 'IDENT'])

    def test_decremento_e_seta_normal_nao_mudam(self):
        self.assertEqual(self.tokens("i-->0"), ['IDENT', 'DECREMENT', 'GT', 'NUMBER'])
        self.assertEqual(self.tokens("x => y"), ['IDENT', 'ARROW', 'IDENT'])
        self.assertEqual(self.tokens("a - b > c"), ['IDENT', 'OP', 'IDENT', 'GT', 'IDENT'])
        self.assertEqual(self.tokens("a-1"), ['IDENT', 'OP', 'NUMBER'])


class TesteParseTipo(unittest.TestCase):
    def test_simples_e_texto_da_anotacao(self):
        t = tipo("inteiro")
        self.assertEqual(t['texto'], 'inteiro')
        self.assertEqual(t['alts'], [{'nome': 'inteiro', 'args': None, 'nulavel': False}])

    def test_nulavel_uniao_e_genericos(self):
        self.assertEqual(tipo("texto?")['alts'][0]['nulavel'], True)
        u = tipo("inteiro | texto | nulo")
        self.assertEqual([a['nome'] for a in u['alts']], ['inteiro', 'texto', 'nulo'])
        self.assertEqual(u['texto'], 'inteiro | texto | nulo')
        l = tipo("lista[lista[inteiro]]?")
        self.assertEqual(l['texto'], 'lista[lista[inteiro]]?')
        self.assertEqual(l['alts'][0]['args'][0]['alts'][0]['args'][0]['texto'], 'inteiro')
        self.assertEqual(tipo("Pessoa")['alts'][0]['nome'], 'Pessoa')

    def test_nulo_e_null_viram_nulo(self):
        self.assertEqual(tipo("nulo")['alts'][0]['nome'], 'nulo')
        self.assertEqual(tipo("null")['alts'][0]['nome'], 'nulo')

    def test_erros_de_sintaxe(self):
        for ruim in ("seja x: = 5", "seja x: 5 = 5", "seja x: \"t\" = 1", "função f(a: ) { }",
                     "função f(a) -> { }", "seja x: lista[ = 1", "seja x: lista[inteiro = 1",
                     "seja x: inteiro | = 1"):
            with self.assertRaises(SyntaxError, msg=ruim):
                ast(ruim)


class TesteParseAnotacoes(unittest.TestCase):
    def test_variavel(self):
        n = nos("seja idade: inteiro = 17")[0]
        self.assertEqual(n['type'], 'var_decl')
        self.assertEqual(n['tipo']['texto'], 'inteiro')
        self.assertIsNone(nos("seja x = 1")[0]['tipo'])
        self.assertEqual(nos("fixo n: texto = \"a\"")[0]['tipo']['texto'], 'texto')
        self.assertIsNone(nos("seja x: inteiro")[0]['value'])

    def test_funcao(self):
        n = nos("função somar(a: numero, b: numero = 0, c) -> numero { retornar a }")[0]
        self.assertEqual([p['tipo']['texto'] if p['tipo'] else None for p in n['params']], ['numero', 'numero', None])
        self.assertEqual(n['retorno']['texto'], 'numero')
        self.assertIsNotNone(n['params'][1]['default'])
        sem = nos("função f(a) { retornar a }")[0]
        self.assertIsNone(sem['retorno'])
        self.assertIsNone(sem['params'][0]['tipo'])

    def test_metodos_funcao_anonima_e_interface(self):
        c = nos("classe A { inicio(n: texto) { } m(x: inteiro) -> texto { retornar \"\" } }")[0]
        self.assertEqual(c['methods'][0]['params'][0]['tipo']['texto'], 'texto')
        self.assertEqual(c['methods'][1]['retorno']['texto'], 'texto')
        self.assertIsNone(c['methods'][0]['retorno'])
        a = nos("seja f = função(x: numero) -> numero { retornar x }")[0]['value']
        self.assertEqual(a['retorno']['texto'], 'numero')
        nos("interface I { m(x: inteiro) -> texto; n() }")             # aceita e ignora

    def test_lambda_com_seta_nao_tem_tipos(self):
        n = nos("seja f = (a, b) => a + b")[0]['value']
        self.assertEqual(n['type'], 'lambda')
        with self.assertRaises(SyntaxError):
            ast("seja f = (a: numero) => a")

    def test_dois_pontos_em_outros_lugares_nao_mudam(self):
        nos("seja m = {a: 1}")
        nos("seja t = x ? 1 : 2")
        nos("função f({a, b: c}) { }")                                   # desestruturação com alias
        nos("combinar x { caso 1: imprimir(1) }")

    def test_programas_do_repositorio_nao_usam_tipos(self):
        """Nenhum .dk existente tem anotação: nada deles passa a ser conferido."""
        def varrer(no, achados):
            if isinstance(no, dict):
                if no.get('type') == 'var_decl' and no.get('tipo'):
                    achados.append(('var', no['name']))
                if no.get('retorno'):
                    achados.append(('retorno', no.get('name')))
                for p in no.get('params') or []:
                    if isinstance(p, dict) and p.get('tipo'):
                        achados.append(('param', p.get('name')))
                for v in no.values():
                    varrer(v, achados)
            elif isinstance(no, list):
                for v in no:
                    varrer(v, achados)
        arquivos = glob.glob(os.path.join(RAIZ, '*.dk')) + glob.glob(os.path.join(RAIZ, 'projetos', '*.dk'))
        self.assertGreater(len(arquivos), 30)
        analisados = 0
        for caminho in arquivos:
            with open(caminho, encoding='utf-8') as f:
                try:
                    arvore = ast(f.read())
                except SyntaxError:
                    continue                                              # alguns exemplos antigos já não analisam
            achados = []
            varrer(arvore, achados)
            self.assertEqual(achados, [], caminho)
            analisados += 1
        self.assertGreater(analisados, 30)


class Ctx(T.ContextoTipos):
    """Contexto de teste com uma classe Animal > Cao."""
    def conhece(self, nome):
        return nome in ('Animal', 'Cao')

    def instancia_de(self, valor, nome):
        return isinstance(valor, str) and valor in {'Animal': ('animal', 'cao'), 'Cao': ('cao',)}[nome]


class TesteConferencia(unittest.TestCase):
    def ok(self, valor, texto):
        return T.verificar(valor, tipo(texto), Ctx())

    def test_tabela(self):
        casos = [
            (5, 'inteiro', True), (5.0, 'inteiro', False), (True, 'inteiro', False), ('5', 'inteiro', False),
            (5, 'numero', True), (5.5, 'numero', True), (True, 'numero', False), (None, 'numero', False),
            ('a', 'texto', True), (1, 'texto', False),
            (True, 'booleano', True), (0, 'booleano', False),
            ([1], 'lista', True), ((1, 2), 'lista', True), ({}, 'lista', False),
            ({'a': 1}, 'mapa', True), ([], 'mapa', False),
            (None, 'nulo', True), (0, 'nulo', False),
            (None, 'qualquer', True), (object(), 'qualquer', True),
            (len, 'funcao', True), (3, 'funcao', False),
            (None, 'texto?', True), ('a', 'texto?', True), (1, 'texto?', False),
            (1, 'inteiro | texto', True), ('a', 'inteiro | texto', True), (1.5, 'inteiro | texto', False),
            (None, 'inteiro | texto | nulo', True),
            ([1, 2.5], 'lista[numero]', True), ([1, 'a'], 'lista[numero]', False), ([], 'lista[inteiro]', True),
            ([[1], [2]], 'lista[lista[inteiro]]', True), ([[1], [2.5]], 'lista[lista[inteiro]]', False),
            ({'a': 1}, 'mapa[inteiro]', True), ({'a': 'x'}, 'mapa[inteiro]', False),
            ([1, 'a'], 'lista[inteiro | texto]', True),
            ('cao', 'Animal', True), ('animal', 'Cao', False), (3, 'Animal', False), (None, 'Animal?', True),
            (3, 'int', True), (3, 'integer', True), (2.5, 'float', True), ('a', 'string', True), (True, 'bool', True),
            ([], 'list', True), ({}, 'dict', True), (None, 'null', True), (1, 'any', True), (len, 'function', True),
        ]
        for valor, texto, esperado in casos:
            self.assertEqual(self.ok(valor, texto), esperado, f"{valor!r} em {texto}")

    def test_nome_desconhecido_levanta_erro(self):
        for texto in ('Foo', 'lista[Foo]', 'Foo?', 'inteiro | Foo', 'mapa[lista[Foo]]'):
            with self.assertRaises(T.ErroTipo, msg=texto):
                self.ok(1, texto)
        with self.assertRaises(T.ErroTipo):
            self.ok(1, 'inteiro[texto]')
        with self.assertRaises(T.ErroTipo):
            self.ok(1, 'Animal[texto]')

    def test_nome_desconhecido_mesmo_quando_outra_alternativa_ja_combina(self):
        with self.assertRaises(T.ErroTipo):
            self.ok(1, 'inteiro | Foo')

    def test_descrever_valor(self):
        d = T.descrever_valor
        self.assertEqual(d(None), 'nulo')
        self.assertEqual(d(True), 'booleano (verdadeiro)')
        self.assertEqual(d(0), 'inteiro (0)')
        self.assertEqual(d(2.5), 'decimal (2.5)')
        self.assertEqual(d('abc'), 'texto ("abc")')
        self.assertTrue(d('x' * 100).endswith('…")'))
        self.assertEqual(d([1, 'a']), "lista ([1, 'a'])")
        self.assertTrue(d(list(range(100))).endswith("…)"))
        self.assertEqual(d({'a': 1}), "mapa ({'a': 1})")


class TesteInterpretador(unittest.TestCase):
    def rodar(self, codigo):
        from advak_interpreter import AdvakInterpreter
        i = AdvakInterpreter(ast(codigo))
        asyncio.run(i.interpret())
        return i.global_scope

    def erro(self, codigo):
        from advak_interpreter import AdvakError
        with self.assertRaises(AdvakError) as e:
            self.rodar(codigo)
        return str(e.exception)

    def test_programa_sem_tipos_nao_cria_mapa_de_tipos(self):
        esc = self.rodar("seja a = 1\na = 'x'\nfunção f(x) { retornar x }\nf(2)")
        self.assertIsNone(esc.tipos)

    def test_variavel_tipada_registra_e_confere(self):
        esc = self.rodar("seja a: inteiro = 1\na = 2")
        self.assertIn('a', esc.tipos)
        self.assertEqual(esc.vars['a'], 2)
        self.assertIn("'a' é inteiro", self.erro("seja a: inteiro = 1\na = 'x'"))

    def test_mensagens(self):
        self.assertEqual(self.erro("seja a: texto = 5"), "Tipo incorreto: 'a' é texto, mas recebeu inteiro (5).")
        self.assertEqual(self.erro("função f(a: numero) { }\nf('x')"),
                         "Tipo incorreto no parâmetro 'a' de f(): esperava numero, mas recebeu texto (\"x\").")
        self.assertEqual(self.erro("função f() -> inteiro { retornar 'x' }\nf()"),
                         "Tipo incorreto no retorno de f(): esperava inteiro, mas retornou texto (\"x\").")
        self.assertIn("terminou sem 'retornar'", self.erro("função f() -> inteiro { }\nf()"))
        self.assertIn("tipo desconhecido 'Int'", self.erro("seja a: Int = 5"))

    def test_escopo_interno_nao_vaza_a_anotacao(self):
        esc = self.rodar("função f() { seja a: inteiro = 1\nretornar a }\nseja a = 'texto livre'\nf()")
        self.assertEqual(esc.vars['a'], 'texto livre')

    def test_desempenho_de_atribuicao_sem_tipos_nao_piora_muito(self):
        import time
        t0 = time.time()
        self.rodar("seja s = 0\npara (i em 1..=15000) { s = s + i }")
        livre = time.time() - t0
        t0 = time.time()
        self.rodar("seja s: inteiro = 0\npara (i em 1..=15000) { s = s + i }")
        tipado = time.time() - t0
        self.assertLess(tipado, livre * 5 + 1.0)                           # a conferência não pode ser absurda


if __name__ == "__main__":
    unittest.main(verbosity=2)
