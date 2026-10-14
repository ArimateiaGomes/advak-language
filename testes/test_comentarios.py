"""
Testes de "//": divisão inteira ou comentário? (advak_lexer.py)

Regra: depois de um valor (número, nome, ")" ou "]") na mesma linha, "//" é divisão inteira só quando o
resto da linha é uma expressão (sem dois valores seguidos nem caracteres estranhos). Senão é comentário.

Rodar:  python -I testes/test_comentarios.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advak_lexer import AdvakLexer   # noqa: E402


def tokens(codigo):
    return [(t['type'], t['value']) for t in AdvakLexer(codigo).tokenize()]


def tem_divisao(codigo):
    return ('OP', '//') in tokens(codigo)


class TesteDivisaoInteira(unittest.TestCase):
    def test_divisao_simples(self):
        self.assertEqual(tokens("7 // 2"), [('NUMBER', 7), ('OP', '//'), ('NUMBER', 2)])

    def test_divisao_sem_espacos(self):
        self.assertTrue(tem_divisao("7//2"))

    def test_divisao_em_expressao_maior(self):
        t = tokens("seja r = (10 + 7) // 2 + 1")
        self.assertIn(('OP', '//'), t)
        self.assertEqual(t[-2:], [('OP', '+'), ('NUMBER', 1)])
        self.assertTrue(tem_divisao("imprimir(7 // (1 + 1))"))
        self.assertTrue(tem_divisao("f(7 // 2, 3)"))

    def test_divisao_com_comentario_depois(self):
        t = tokens("imprimir(7 // 2)   // divisão inteira: 3")
        self.assertEqual(t.count(('OP', '//')), 1)
        self.assertNotIn(('IDENT', 'divisão'), t)


class TesteComentarioAposCodigo(unittest.TestCase):
    """Textos que começam como expressão mas são comentário."""
    TEXTOS = ["+", "a + b", "3.5", "8 > 8", "(parênteses)", "7 / 2", "2 elevado a 3", "8 > 8 ? falso"]

    def test_comentarios_da_sondagem(self):
        for texto in self.TEXTOS:
            with self.subTest(texto=texto):
                t = tokens(f"seja x = 1   // {texto}\nseja y = 2")
                self.assertNotIn(('OP', '//'), t)
                self.assertEqual(t, tokens("seja x = 1\nseja y = 2"))

    def test_comentario_apos_chamada(self):
        for texto in self.TEXTOS:
            with self.subTest(texto=texto):
                self.assertEqual(tokens(f"imprimir(5)   // {texto}"), tokens("imprimir(5)"))

    def test_comentario_com_letra_logo_depois(self):
        self.assertEqual(tokens("imprimir(5) // soma"), tokens("imprimir(5)"))


class TesteRegraDoEspaco(unittest.TestCase):
    """Fora de parênteses, 2+ espaços (ou tab) antes do // = comentário alinhado; dentro de parênteses, divisão."""
    def test_um_espaco_e_divisao(self):
        self.assertTrue(tem_divisao("seja r = 7 // 2"))
        self.assertTrue(tem_divisao("seja r = 7//2"))

    def test_dois_espacos_ou_tab_e_comentario(self):
        self.assertFalse(tem_divisao("seja r = 7  // 2"))
        self.assertFalse(tem_divisao("seja r = 7	// 2"))

    def test_dentro_de_parenteses_e_sempre_divisao(self):
        self.assertTrue(tem_divisao("imprimir(7   // 2)"))
        self.assertTrue(tem_divisao("lista[9  // 2]"))


class TesteComentarioEmLinhaPropria(unittest.TestCase):
    def test_linha_propria(self):
        for texto in ["// só comentário", "// 7 // 2", "// 3.5", "// (x)", "// 8 > 8"]:
            with self.subTest(texto=texto):
                self.assertEqual(tokens(f"{texto}\nseja y = 2"), tokens("seja y = 2"))

    def test_linha_propria_indentada_entre_comandos(self):
        self.assertEqual(tokens("seja a = 1\n    // 2 + 2\nseja b = 2"), tokens("seja a = 1\nseja b = 2"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
