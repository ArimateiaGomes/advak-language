"""
Testes do transpilador Python/C (advak_nativo.py): números negativos e decimais literais, operadores
unários. O resultado do código Python gerado é comparado com o do interpretador da Advak.

Rodar:  python -I testes/test_transpilador.py
"""
import asyncio
import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advak_lexer import AdvakLexer    # noqa: E402
from advak_parser import Parser       # noqa: E402
from advak_interpreter import AdvakInterpreter   # noqa: E402
from advak_nativo import TranspiladorPython, TranspiladorC   # noqa: E402


def interpretar(codigo):
    i = AdvakInterpreter(Parser(AdvakLexer(codigo).tokenize()).parse())
    with contextlib.redirect_stdout(io.StringIO()):
        asyncio.run(i.interpret())
    return i.global_scope.vars


def transpilar_e_executar(codigo):
    py = TranspiladorPython().transpilar(codigo)
    ns = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(py, "<transpilado>", "exec"), ns)      # código gerado por nós, só para comparar no teste
    return py, ns


class TesteNegativosEDecimais(unittest.TestCase):
    CASOS = [
        ("seja x = -2", ["x"]),
        ("seja x = -2.5", ["x"]),
        ("seja y = 5 - -3", ["y"]),
        ("seja z = -(2 + 3)", ["z"]),
        ("seja a = 4\nseja b = -a", ["a", "b"]),
        ("seja p = 2 ** -1", ["p"]),
        ("seja q = -2 ** 2", ["q"]),                                  # na Advak vale (-2) ** 2 = 4
        ("seja w = nao verdadeiro", ["w"]),
        ("seja t = 3 > -1 && !falso", ["t"]),
        ("seja l = [-1, -2.5, 3.5]", ["l"]),
        ("seja m = {a: -1, b: 2.5}", ["m"]),
        ("funcao f(a, b = -1) { retornar -a + b }\nseja r = f(3)\nseja r2 = f(3, -4)", ["r", "r2"]),
        ("seja v = 0\nse (v == -0) { v = -7.25 }", ["v"]),
        ("seja d = 2.5 * -2 + 10 / -4", ["d"]),
        ("seja n = [-3, -1, -2]\nseja s = n[0] - n[1]", ["s"]),
        ("seja i = 3\nseja j = -i * -i", ["j"]),
        ("seja u = verdadeiro e nao falso ou falso", ["u"]),
    ]

    def test_resultado_igual_ao_do_interpretador(self):
        for codigo, nomes in self.CASOS:
            esperado = {n: interpretar(codigo)[n] for n in nomes}
            _, ns = transpilar_e_executar(codigo)
            obtido = {n: ns[n] for n in nomes}
            self.assertEqual(obtido, esperado, codigo)

    def test_antes_dava_keyerror(self):
        py = TranspiladorPython().transpilar("seja x = -2")             # antes: KeyError: 'value'
        self.assertIn("x = (-2)", py)

    def test_decimal_literal_nao_vira_none(self):
        py = TranspiladorPython().transpilar("seja x = 2.5\nseja l = [1.5, 2]")
        self.assertIn("x = 2.5", py)
        self.assertIn("l = [1.5, 2]", py)
        self.assertNotIn("None  # [expr", py)

    def test_precedencia_fica_protegida_por_parenteses(self):
        py, ns = transpilar_e_executar("seja a = 3\nseja b = -a ** 2\nseja c = nao falso e verdadeiro")
        self.assertEqual(ns['b'], 9)                                      # (-3) ** 2, como na Advak
        self.assertIn("(-a)", py)

    def test_transpilador_c_tambem_aceita_unarios_e_decimais(self):
        c = TranspiladorC().transpilar("seja x = -2\nseja y = !verdadeiro\nseja z = -2.5")
        self.assertIn("advak_num x = (-2);", c)
        self.assertIn("advak_num y = (!1);", c)
        self.assertIn("advak_num z = (-2.5);", c)

    def test_programas_do_repositorio_com_negativos_ainda_transpilam(self):
        for nome in ("fibonacci.dk", "matematica_utils.dk", "utils_math.dk"):
            caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "projetos", nome)
            if not os.path.exists(caminho):
                continue
            with open(caminho, encoding="utf-8") as f:
                TranspiladorPython().transpilar(f.read())               # não pode levantar exceção


if __name__ == "__main__":
    unittest.main(verbosity=2)
