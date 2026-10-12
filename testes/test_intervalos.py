"""
Testes de intervalos (1..10, 1..=10, passo) no lexer, no parser e no transpilador.
O comportamento em execução está em testes/intervalos.dk.

Rodar:  python -I testes/test_intervalos.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advak_lexer import AdvakLexer   # noqa: E402
from advak_parser import Parser      # noqa: E402


def tipos(codigo):
    return [(t['type'], t['value']) for t in AdvakLexer(codigo).tokenize()]


def ast(codigo):
    return Parser(AdvakLexer(codigo).tokenize()).parse()


def primeira_expressao(codigo):
    raiz = ast(codigo)
    nos = raiz['body'] if isinstance(raiz, dict) else raiz
    return nos[0]


class TesteLexer(unittest.TestCase):
    def test_tokens_de_intervalo(self):
        self.assertEqual(tipos("1..10"), [('NUMBER', 1), ('RANGE', '..'), ('NUMBER', 10)])
        self.assertEqual(tipos("1..=10"), [('NUMBER', 1), ('RANGE_INC', '..='), ('NUMBER', 10)])
        self.assertEqual([t for t, _ in tipos("a..b")], ['IDENT', 'RANGE', 'IDENT'])

    def test_decimais_e_spread_nao_mudam(self):
        self.assertEqual(tipos("1.5"), [('FLOAT', 1.5)])
        self.assertEqual(tipos("1.5..3")[:2], [('FLOAT', 1.5), ('RANGE', '..')])
        self.assertEqual([t for t, _ in tipos("[...resto]")], ['LBRACKET', 'SPREAD', 'IDENT', 'RBRACKET'])
        self.assertEqual([t for t, _ in tipos("obj.campo")], ['IDENT', 'DOT', 'IDENT'])

    def test_ponto_e_virgula_e_strings_com_pontos_intactos(self):
        self.assertEqual(tipos('"a..b"'), [('STRING', 'a..b')])


class TesteParser(unittest.TestCase):
    def expr(self, codigo):
        return ast(f"seja r = {codigo}")

    def alvo(self, codigo):
        no = primeira_expressao(f"seja r = {codigo}")
        return no.get('value') or no.get('init')

    def test_exclusivo_inclusivo_e_passo(self):
        n = self.alvo("1..10")
        self.assertEqual((n['type'], n['inclusive'], n['step']), ('range', False, None))
        self.assertTrue(self.alvo("1..=10")['inclusive'])
        n = self.alvo("1..=10 passo 2")
        self.assertEqual(n['step'], {'type': 'number', 'value': 2})
        self.assertIsNotNone(self.alvo("1..=10 step 2")['step'])

    def test_precedencia_limites_sao_expressoes(self):
        n = self.alvo("1..n+1")
        self.assertEqual(n['end']['type'], 'binop')
        self.assertEqual(n['end']['op'], '+')
        n = self.alvo("-5..5")
        self.assertEqual(n['start']['type'], 'unary')

    def test_for_in_recebe_o_no_range(self):
        raiz = ast("para (i em 1..=3) { }")
        no = (raiz['body'] if isinstance(raiz, dict) else raiz)[0]
        self.assertEqual(no['type'], 'for_in')
        self.assertEqual(no['iterable']['type'], 'range')

    def test_intervalo_incompleto_e_erro_de_sintaxe(self):
        for ruim in ("seja r = 1..", "seja r = ..5", "seja r = 1..="):
            with self.assertRaises(SyntaxError, msg=ruim):
                ast(ruim)

    def test_passo_continua_sendo_um_nome_valido_fora_de_intervalos(self):
        no = primeira_expressao("seja passo = 3")
        self.assertEqual(no['name'], 'passo')


class TesteFerramentas(unittest.TestCase):
    def test_formatador_nao_separa_o_operador_de_intervalo(self):
        from advak_formatador import Formatador
        norm = Formatador()._normalizar_operadores
        self.assertEqual(norm("para (i em 1..=10) { x=1 }"), "para (i em 1..=10) { x = 1 }")
        self.assertEqual(norm("seja r = 0..=n"), "seja r = 0..=n")

    def test_check_aceita_programa_com_intervalos(self):
        ast("seja soma = 0\npara (i em 1..=10 passo 2) {\n    soma = soma + i\n}\nseja r = 1..5")


class TesteTranspilador(unittest.TestCase):
    def py(self, codigo):
        from advak_nativo import TranspiladorPython
        return TranspiladorPython().transpilar(codigo)

    def test_range_vira_range_do_python_e_executa_igual(self):
        saida = {}
        codigo = self.py("seja a = 1..4\nseja b = 1..=4\nseja c = 5..=1 passo 0-2\nseja d = 0..10 passo 5")
        exec(compile(codigo, "<transpilado>", "exec"), saida)       # código gerado por nós, só para o teste
        self.assertEqual([list(saida[n]) for n in "abcd"], [[1, 2, 3], [1, 2, 3, 4], [5, 3, 1], [0, 5]])

    def test_for_in_com_intervalo(self):
        saida = {}
        exec(compile(self.py("seja s = 0\npara (i em 1..=3) { s = s + i }"), "<transpilado>", "exec"), saida)
        self.assertEqual(saida["s"], 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
