"""
Testes da compreensão de listas no parser, no interpretador (limites) e no transpilador Python.
O comportamento em execução está em testes/compreensao.dk.

Rodar:  python -I testes/test_compreensao.py
"""
import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advak_lexer import AdvakLexer   # noqa: E402
from advak_parser import Parser      # noqa: E402


def ast(codigo):
    return Parser(AdvakLexer(codigo).tokenize()).parse()


def alvo(codigo):
    raiz = ast(f"seja r = {codigo}")
    nos = raiz['body'] if isinstance(raiz, dict) else raiz
    return nos[0]['value']


class TesteParser(unittest.TestCase):
    def test_estrutura_basica(self):
        n = alvo("[x * 2 para x em lista se x > 0]")
        self.assertEqual(n['type'], 'list_comp')
        self.assertEqual(n['element']['type'], 'binop')
        self.assertEqual([c['kind'] for c in n['clauses']], ['for', 'if'])
        self.assertEqual(n['clauses'][0]['var'], 'x')
        self.assertEqual(n['clauses'][0]['iter'], {'type': 'ident', 'name': 'lista'})

    def test_sinonimos_em_ingles(self):
        n = alvo("[x for x in lista if x]")
        self.assertEqual([c['kind'] for c in n['clauses']], ['for', 'if'])
        self.assertEqual(alvo("[x for x of lista]")['type'], 'list_comp')

    def test_varios_para_e_se_na_ordem_escrita(self):
        n = alvo("[x + y para x em a se x > 0 para y em b se y > x]")
        self.assertEqual([c['kind'] for c in n['clauses']], ['for', 'if', 'for', 'if'])

    def test_desmontagem(self):
        n = alvo("[a + b para (a, b) em pares]")
        self.assertEqual(n['clauses'][0]['var'], ['a', 'b'])

    def test_iteravel_pode_ser_intervalo_com_passo(self):
        n = alvo("[x para x em 0..=20 passo 5 se x != 10]")
        self.assertEqual(n['clauses'][0]['iter']['type'], 'range')
        self.assertEqual(n['clauses'][0]['iter']['step'], {'type': 'number', 'value': 5})

    def test_elemento_pode_ser_ternario_lista_ou_outra_compreensao(self):
        self.assertEqual(alvo("[x > 0 ? x : 0 para x em l]")['element']['type'], 'ternary')
        self.assertEqual(alvo("[[i, j] para i em a para j em b]")['element']['type'], 'list')
        self.assertEqual(alvo("[[j para j em b] para i em a]")['element']['type'], 'list_comp')

    def test_listas_comuns_nao_mudam(self):
        self.assertEqual(alvo("[1, 2, 3]")['type'], 'list')
        self.assertEqual(alvo("[]")['items'], [])
        self.assertEqual(len(alvo("[1, 2, 3,]")['items']), 3)
        self.assertEqual([i['type'] for i in alvo("[...a, ...b]")['items']], ['spread', 'spread'])
        self.assertEqual(alvo("[para_cada, para2]")['type'], 'list')       # nomes que começam com 'para'

    def test_erros_de_sintaxe(self):
        for ruim in ("[x para]", "[x para x]", "[x para x em]", "[x para x em l",
                     "[x para (a, ) em l]", "[x para x em l se]"):
            with self.assertRaises(SyntaxError, msg=ruim):
                ast(f"seja r = {ruim}")

    def test_mensagem_pede_o_em(self):
        with self.assertRaises(SyntaxError) as e:
            ast("seja r = [x para x lista]")
        self.assertIn("esperado 'em'", str(e.exception))


class TesteExecucao(unittest.TestCase):
    def rodar(self, codigo, limite=None):
        from advak_interpreter import AdvakInterpreter
        i = AdvakInterpreter(ast(codigo))
        if limite:
            i._MAX_INTERVALO = limite
        asyncio.run(i.interpret())
        return i.global_scope.vars

    def test_resultado_basico(self):
        v = self.rodar("seja r = [x * 2 para x em [1, 2, 3] se x != 2]")
        self.assertEqual(v['r'], [2, 6])

    def test_limite_do_resultado(self):
        from advak_interpreter import AdvakError
        with self.assertRaises(AdvakError) as e:
            self.rodar("seja r = [x para x em 1..=100]", limite=10)
        self.assertIn("passou de 10 itens", str(e.exception))

    def test_intervalo_enorme_so_com_se_seletivo_nao_cria_lista_de_origem(self):
        v = self.rodar("seja r = [x para x em 1..=30000 se x % 10000 == 0]")
        self.assertEqual(v['r'], [10000, 20000, 30000])

    def test_lista_sem_virgulas_continua_aceita_como_antes(self):
        # comportamento antigo do parser (lista tolerante), não relacionado à compreensão
        self.assertEqual(alvo("[para x em l]")['type'], 'list')

    def test_erro_de_origem_nao_iteravel(self):
        from advak_interpreter import AdvakError
        with self.assertRaises(AdvakError) as e:
            self.rodar("seja r = [x para x em 3.5]")
        self.assertIn("número", str(e.exception))


class TesteTranspilador(unittest.TestCase):
    def py(self, codigo):
        from advak_nativo import TranspiladorPython
        saida = {}
        exec(compile(TranspiladorPython().transpilar(codigo), "<transpilado>", "exec"), saida)   # só no teste
        return saida

    def test_equivale_a_compreensao_do_python(self):
        s = self.py("seja a = [x * 2 para x em [1, 0, 3] se x > 0]\n"
                    "seja b = [x + y para x em 1..=2 para y em [10, 20]]\n"
                    "seja c = [p + q para (p, q) em [[1, 2], [3, 4]]]\n"
                    "seja d = [x for x in [1, 2, 3] if x != 2]\n"
                    "seja e = [[i * j para j em 1..=2] para i em 1..=2]")
        self.assertEqual((s['a'], s['b'], s['c'], s['d'], s['e']),
                         ([2, 6], [11, 21, 12, 22], [3, 7], [1, 3], [[1, 2], [2, 4]]))


class TesteFerramentas(unittest.TestCase):
    def test_formatador_nao_estraga_a_compreensao(self):
        from advak_formatador import Formatador
        linha = "seja r = [x * 2 para x em 1..=10 passo 2 se x != 3]"
        self.assertEqual(Formatador()._normalizar_operadores(linha), linha)


if __name__ == "__main__":
    unittest.main(verbosity=2)
