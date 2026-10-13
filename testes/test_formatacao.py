"""
Testes de advak_formatacao.py (interpolação com formatação). O uso em programas .dk está em
testes/formatacao.dk.

Rodar:  python -I testes/test_formatacao.py
"""
import datetime
import os
import random
import re
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from advak_formatacao import (dividir_template, separar_formato, formatar_valor, ErroFormato)  # noqa: E402

F = formatar_valor


class TesteDividirTemplate(unittest.TestCase):
    def test_basico(self):
        self.assertEqual(dividir_template("a ${x} b ${y:moeda} c"),
                         [('t', 'a '), ('e', 'x'), ('t', ' b '), ('e', 'y:moeda'), ('t', ' c')])
        self.assertEqual(dividir_template("sem nada"), [('t', 'sem nada')])
        self.assertEqual(dividir_template(""), [])

    def test_vazio_e_sem_fechamento_ficam_literais(self):
        self.assertEqual(dividir_template("a ${} b"), [('t', 'a ${} b')])
        self.assertEqual(dividir_template("a ${  } b"), [('t', 'a ${  } b')])
        self.assertEqual(dividir_template("a ${x"), [('t', 'a ${x')])
        self.assertEqual(dividir_template("${x} ${y"), [('e', 'x'), ('t', ' ${y')])

    def test_chaves_aninhadas_e_textos(self):
        self.assertEqual(dividir_template("${ {a: 1}.a }"), [('e', ' {a: 1}.a ')])
        self.assertEqual(dividir_template('${"}"} fim'), [('e', '"}"'), ('t', ' fim')])
        self.assertEqual(dividir_template("${'}'}x"), [('e', "'}'"), ('t', 'x')])
        self.assertEqual(dividir_template('${f("a\\"}b")}'), [('e', 'f("a\\"}b")')])

    def test_identico_ao_comportamento_antigo_sem_chaves_aninhadas(self):
        """Compara com o divisor antigo (regex) em casos fixos e em milhares de textos aleatórios."""
        def antigo(tmpl):
            saida = []
            for part in re.split(r'(\$\{[^}]*\})', tmpl):
                m = re.match(r'^\$\{([^}]*)\}$', part)
                if m and m.group(1).strip():
                    saida.append(('e', m.group(1)))
                elif part:
                    saida.append(('t', part))
            # junta textos vizinhos (o divisor novo também junta)
            junto = []
            for tipo, c in saida:
                if tipo == 't' and junto and junto[-1][0] == 't':
                    junto[-1] = ('t', junto[-1][1] + c)
                else:
                    junto.append((tipo, c))
            return junto

        casos = ["${a} + ${b} = ${a + b}", "Olá ${nome}!", "${}", "${ }", "a${b}c${d}e", "$ {x}", "${x}${y}",
                 "preço: ${p * 2}", "${a", "x}y", "${a ? b : c}", "${f(1, 2)}", "${[1, 2][0]}", "$${x}"]
        for c in casos:
            self.assertEqual(dividir_template(c), antigo(c), c)
        rnd = random.Random(7)
        alfabeto = list("ab 1+${}()[]?:,.") + ["${", "${x}", "}", " "]
        comparados = 0
        for _ in range(20000):
            t = ''.join(rnd.choice(alfabeto) for _ in range(rnd.randint(0, 12)))
            exprs_antigas = [c for tp, c in antigo(t) if tp == 'e']
            if any('{' in c or '(' in c or '[' in c for c in exprs_antigas):
                continue                                     # casos com agrupamento: o divisor novo é de propósito mais esperto
            self.assertEqual(dividir_template(t), antigo(t), repr(t))
            comparados += 1
        self.assertGreater(comparados, 5000)


class TesteSepararFormato(unittest.TestCase):
    def test_tabela(self):
        casos = [
            ("preco:moeda", ("preco", "moeda")),
            ("preco", ("preco", None)),
            ("a + b", ("a + b", None)),
            ("d:dd/mm/aaaa hh:mm", ("d", "dd/mm/aaaa hh:mm")),          # só o primeiro ':' separa
            ("x > 1 ? a : b", ("x > 1 ? a : b", None)),                   # ':' do ternário
            ("x > 1 ? a : 0 :moeda", ("x > 1 ? a : 0 ", "moeda")),
            ("a ? b ? c : d : e", ("a ? b ? c : d : e", None)),            # ternário aninhado
            ("a ?? b", ("a ?? b", None)),
            ("a ?? b :moeda", ("a ?? b ", "moeda")),
            ("a?.b:upper", ("a?.b", "upper")),
            ("(a ? b : c)", ("(a ? b : c)", None)),
            ("{a: 1}.a", ("{a: 1}.a", None)),
            ("f(1, 2):.2f", ("f(1, 2)", ".2f")),
            ("l[0]:>5", ("l[0]", ">5")),
            ('"a:b"', ('"a:b"', None)),
            ('"a:b":upper', ('"a:b"', "upper")),
            ("m['x:y']:moeda", ("m['x:y']", "moeda")),
            ("x:>10", ("x", ">10")),
            ("x:*^9", ("x", "*^9")),
            ("x: moeda ", ("x", "moeda")),
        ]
        for entrada, esperado in casos:
            self.assertEqual(separar_formato(entrada), esperado, entrada)

    def test_formato_vazio_e_erro(self):
        with self.assertRaises(ErroFormato):
            separar_formato("x:")
        with self.assertRaises(ErroFormato):
            separar_formato("x:   ")


class TesteNumeros(unittest.TestCase):
    def test_moeda(self):
        self.assertEqual(F(1500.5, "moeda"), "R$ 1.500,50")
        self.assertEqual(F(1500.5, "moeda.0"), "R$ 1.501")
        self.assertEqual(F(-0.004, "moeda"), "R$ 0,00")
        self.assertEqual(F(-1234.567, "moeda"), "-R$ 1.234,57")
        self.assertEqual(F(Decimal("10.005"), "moeda"), "R$ 10,01")
        self.assertEqual(F(10 ** 30, "moeda"), "R$ 1.000.000.000.000.000.000.000.000.000.000,00")
        self.assertEqual(F(5, "CURRENCY"), "R$ 5,00")

    def test_numero(self):
        self.assertEqual(F(1234567, "numero"), "1.234.567")
        self.assertEqual(F(1234567.0, "numero"), "1.234.567")
        self.assertEqual(F(0.1 + 0.2, "numero"), "0,3")
        self.assertEqual(F(1 / 3, "numero"), "0,333333")
        self.assertEqual(F(123456789012345678901234567890, "numero"), "123.456.789.012.345.678.901.234.567.890")
        self.assertEqual(F(2.5, "numero.0"), "3")

    def test_porcentagem(self):
        self.assertEqual(F(0.75, "porcentagem"), "75%")
        self.assertEqual(F(75, "pct"), "75%")
        self.assertEqual(F(0.0725, "pct.2"), "7,25%")
        self.assertEqual(F(1, "pct"), "100%")                # a regra da função porcentagem(): 0..1 é fração
        self.assertEqual(F(1.5, "pct.1"), "1,5%")
        self.assertEqual(F(0, "pct"), "0%")

    def test_arg_de_casas_invalido(self):
        for ruim in ("moeda.x", "moeda.", "numero.-1", "pct.99", "moeda.1.2"):
            with self.assertRaises(ErroFormato, msg=ruim):
                F(5, ruim)

    def test_tipos_incompativeis(self):
        for valor in ("abc", True, [1], {"a": 1}):
            for fmt in ("moeda", "numero", "pct"):
                with self.assertRaises(ErroFormato, msg=f"{valor!r} {fmt}"):
                    F(valor, fmt)

    def test_nao_finitos(self):
        for v in (float("nan"), float("inf")):
            with self.assertRaises(ErroFormato):
                F(v, "moeda")


class TesteEstiloPython(unittest.TestCase):
    def test_casas_e_milhar_com_separadores_do_brasil(self):
        self.assertEqual(F(3.14159, ".2f"), "3,14")
        self.assertEqual(F(1234.5, ",.2f"), "1.234,50")
        self.assertEqual(F(1234567, ",d"), "1.234.567")
        self.assertEqual(F(2.675, ".2f"), "2,68")                  # arredondamento escolar, não binário
        self.assertEqual(F(0.5, ".0f"), "1")
        self.assertEqual(F(7, ".2f"), "7,00")
        self.assertEqual(F(0.256, ".1%"), "25,6%")
        self.assertEqual(F(1234.5, ".3e"), "1,234e+03")

    def test_zeros_sinais_e_bases(self):
        self.assertEqual(F(7, "03d"), "007")
        self.assertEqual(F(-7, "03d"), "-07")
        self.assertEqual(F(7, "+d"), "+7")
        self.assertEqual(F(255, "x"), "ff")
        self.assertEqual(F(255, "X"), "FF")
        self.assertEqual(F(5, "b"), "101")
        self.assertEqual(F(3.5, "08.2f"), "00003,50")
        self.assertEqual(F(3.5, "+08.2f"), "+0003,50")

    def test_alinhamento(self):
        self.assertEqual(F("Ana", ">6"), "   Ana")
        self.assertEqual(F("Ana", "<6"), "Ana   ")
        self.assertEqual(F("Ana", "^7"), "  Ana  ")
        self.assertEqual(F("Ana", "*^9"), "***Ana***")
        self.assertEqual(F("Ana", ".2"), "An")
        self.assertEqual(F("Ana", "5"), "Ana  ")                    # texto: esquerda por padrão
        self.assertEqual(F(42, "5"), "   42")                       # número: direita por padrão
        self.assertEqual(F(42, "<5"), "42   ")
        self.assertEqual(F(42, "=+6"), "+   42")
        self.assertEqual(F(1234.5, ".>12,.2f"), "....1.234,50")     # o '.' como preenchimento não é trocado
        self.assertEqual(F([1, 2], ">8"), "  [1, 2]"[-8:])

    def test_erros(self):
        with self.assertRaises(ErroFormato):
            F(5.5, "d")
        with self.assertRaises(ErroFormato):
            F("abc", ".2f")
        with self.assertRaises(ErroFormato):
            F(True, ".2f")
        with self.assertRaises(ErroFormato):
            F("abc", "+")
        with self.assertRaises(ErroFormato):
            F(5, "coisa")

    def test_texto(self):
        self.assertEqual(F("ana maria", "maiusculo"), "ANA MARIA")
        self.assertEqual(F("ANA", "minusculo"), "ana")
        self.assertEqual(F("ana maria", "titulo"), "Ana Maria")
        self.assertEqual(F(42, "upper"), "42")
        self.assertEqual(F([1, "a"], "maiusculo", lambda v: "LISTA"), "LISTA")

    def test_nulo(self):
        for fmt in ("moeda", "dd/mm/aaaa", ".2f", "upper", "coisa-invalida"):
            self.assertEqual(F(None, fmt), "nulo")


class TesteDatas(unittest.TestCase):
    def test_nomes(self):
        self.assertEqual(F("2024-12-25", "data"), "25/12/2024")
        self.assertEqual(F("2024-12-25", "date"), "25/12/2024")
        self.assertEqual(F("2024-12-25 14:30", "datahora"), "25/12/2024 14:30")
        self.assertEqual(F("2024-12-25T14:30:59", "hora"), "14:30")
        self.assertEqual(F("14:30", "hora"), "14:30")

    def test_padroes_e_nomes_de_mes_e_dia(self):
        d = "2024-03-09"
        self.assertEqual(F(d, "dd/mm/aaaa"), "09/03/2024")
        self.assertEqual(F(d, "DD/MM/AAAA"), "09/03/2024")
        self.assertEqual(F(d, "yyyy-mm-dd"), "2024-03-09")
        self.assertEqual(F(d, "dd/mm/aa"), "09/03/24")
        self.assertEqual(F(d, "dddd"), "sábado")
        self.assertEqual(F(d, "ddd, dd mmm"), "sáb, 09 mar")
        self.assertEqual(F(d, "dd [de] mmmm [de] aaaa"), "09 de março de 2024")
        self.assertEqual(F("2024-01-01", "dddd"), "segunda-feira")
        self.assertEqual(F("2024-12-29", "dddd"), "domingo")
        self.assertEqual(F("2024-12-25", "mmmm"), "dezembro")

    def test_mm_mes_ou_minuto(self):
        dh = "2024-03-09 07:05:09"
        self.assertEqual(F(dh, "dd/mm/aaaa hh:mm"), "09/03/2024 07:05")
        self.assertEqual(F(dh, "hh:mm:ss"), "07:05:09")
        self.assertEqual(F(dh, "mm:ss"), "05:09")                     # antes de ':ss' são minutos
        self.assertEqual(F(dh, "mm/dd hh[h]mm"), "03/09 07h05")
        self.assertEqual(F(dh, "hh mm"), "07 05")
        self.assertEqual(F(dh, "dd/mm hh:mm"), "09/03 07:05")
        self.assertEqual(F(dh, "mmmm hh:mm"), "março 07:05")

    def test_formatos_de_entrada(self):
        for entrada in ("2024-12-25", "25/12/2024", "25-12-2024", "2024-12-25T00:00:00", "2024-12-25 00:00",
                        "2024-12-25T10:30:00.123456", "2024-12-25T10:30:00Z", "2024-12-25T10:30:00-03:00",
                        " 2024-12-25 ", "05/12/2024"):
            F(entrada, "data")
        self.assertEqual(F("5/3/2024", "dd/mm/aaaa"), "05/03/2024")
        self.assertEqual(F("25/12/2024 18:30", "datahora"), "25/12/2024 18:30")

    def test_objetos_python(self):
        self.assertEqual(F(datetime.date(2024, 12, 25), "data"), "25/12/2024")
        self.assertEqual(F(datetime.datetime(2024, 12, 25, 9, 5, 7), "dd/mm/aaaa hh:mm:ss"), "25/12/2024 09:05:07")
        self.assertEqual(F(datetime.time(9, 5), "hora"), "09:05")
        with self.assertRaises(ErroFormato):
            F(datetime.date(2024, 12, 25), "hora")                       # date não tem hora
        with self.assertRaises(ErroFormato):
            F(datetime.time(9, 5), "data")

    def test_erros(self):
        for valor, fmt in [("ontem", "data"), ("2024-13-45", "data"), ("31/02/2024", "data"), (123, "data"),
                           (True, "data"), ("2024-12-25", "hora"), ("2024-12-25", "hh:mm"),
                           ("2024-12-25", "dd [de")]:
            with self.assertRaises(ErroFormato, msg=f"{valor!r} {fmt}"):
                F(valor, fmt)

    def test_padrao_de_data_nao_confunde_com_estilo_python(self):
        self.assertEqual(F(5, "d"), "5")
        self.assertEqual(F(5, "03d"), "005")
        self.assertEqual(F("2024-12-25", "dd"), "25")
        self.assertEqual(F("2024-12-25", "aaaa"), "2024")


class TesteFerramentas(unittest.TestCase):
    """O formatador e o verificador não podem estragar nem acusar o conteúdo de textos e templates."""

    def fmt(self, codigo):
        from advak_formatador import Formatador
        return Formatador().formatar(codigo)

    def test_formatador_nao_mexe_dentro_de_textos(self):
        origem = 'se (x) {\nimprimir(`${p:,.2f} e "a,b"  fim`)\nseja t = \'a,b=c\'\n}'
        esperado = 'se (x) {\n    imprimir(`${p:,.2f} e "a,b"  fim`)\n    seja t = \'a,b=c\'\n}'
        self.assertEqual(self.fmt(origem), esperado)

    def test_formatador_ainda_normaliza_o_codigo_fora_dos_textos(self):
        self.assertEqual(self.fmt('seja y=1\nseja l=[1,2,3]\nseja s="a"'), 'seja y = 1\nseja l = [1, 2, 3]\nseja s = "a"')

    def test_formatador_preserva_o_recuo(self):
        self.assertEqual(self.fmt('para (i em 1..3) {\nse (i) {\nx=1\n}\n}'),
                         'para (i em 1..3) {\n    se (i) {\n        x = 1\n    }\n}')

    def test_formatador_nao_mexe_em_comentarios(self):
        self.assertEqual(self.fmt('x=1 // a,b=c  d'), 'x = 1 // a,b=c  d')
        self.assertEqual(self.fmt('a=b // 2'), 'a = b // 2')                    # divisão inteira, não comentário

    def test_formatador_respeita_texto_de_varias_linhas(self):
        origem = 'seja t = `linha1,x\n   linha2=3,a\nfim` \nseja z=1'
        saida = self.fmt(origem).split('\n')
        self.assertEqual(saida[1], '   linha2=3,a')                              # intacta (inclusive o recuo)
        self.assertEqual(saida[0], 'seja t = `linha1,x')
        self.assertEqual(saida[-1], 'seja z = 1')

    def test_formatador_intervalos_e_formatos_juntos(self):
        linha = 'para (i em 1..=10 passo 2) { imprimir(`${i:03d}`) }'
        self.assertEqual(self.fmt(linha), linha)

    def test_verificador_nao_acusa_divisao_dentro_de_textos(self):
        from advak_verificador import verificar
        textos = ['imprimir(`Hoje: ${d:dd/mm/aaaa}`)', 'imprimir("dd/mm/aaaa")', "seja f = 'a/b'",
                  'seja x = 1 // a/b c/d']
        for t in textos:
            self.assertEqual([p for p in verificar(t) if 'divisão' in p['msg']], [], t)

    def test_verificador_continua_acusando_divisao_de_verdade(self):
        from advak_verificador import verificar
        achados = verificar('imprimir(a / b + 1)')
        self.assertTrue(any('divisão' in p['msg'] for p in achados))

    def test_proteger_e_restaurar_sao_inversas(self):
        from advak_formatacao import proteger_literais, restaurar_literais
        for linha in ['x = "a" + \'b\' + `c ${d}` // fim', 'sem nada', '"\\"escapado\\""', '`aberto sem fechar',
                      'a // 2 + b']:
            protegida, lits, _ = proteger_literais(linha)
            self.assertEqual(restaurar_literais(protegida, lits), linha)
        self.assertTrue(proteger_literais('seja t = `abre')[2])
        self.assertFalse(proteger_literais('seja t = `fecha`')[2])
        self.assertTrue(proteger_literais('meio sem fechar', True)[2])
        self.assertFalse(proteger_literais('fecha` e acaba', True)[2])


class TesteInterpretador(unittest.TestCase):
    """Integração com o interpretador (templates reais)."""

    def rodar(self, codigo):
        import asyncio
        from advak_lexer import AdvakLexer
        from advak_parser import Parser
        from advak_interpreter import AdvakInterpreter
        i = AdvakInterpreter(Parser(AdvakLexer(codigo).tokenize()).parse())
        asyncio.run(i.interpret())
        return i.global_scope.vars

    def test_template_com_formato(self):
        v = self.rodar("seja p = 1500.5\nseja r = `Total: ${p:moeda} em ${\"2024-12-25\":dd/mm/aaaa}`")
        self.assertEqual(v['r'], "Total: R$ 1.500,50 em 25/12/2024")

    def test_expressao_e_cacheada_e_reavaliada_a_cada_vez(self):
        v = self.rodar("seja saida = []\npara (i em 1..=3) { saida.adicionar(`${i * 1000:moeda.0}`) }")
        self.assertEqual(v['saida'], ["R$ 1.000", "R$ 2.000", "R$ 3.000"])

    def test_erro_de_formato_vira_erro_de_execucao_em_portugues(self):
        from advak_interpreter import AdvakError
        with self.assertRaises(AdvakError) as e:
            self.rodar("seja r = `${\"abc\":moeda}`")
        self.assertIn("Formato inválido em ${\"abc\":moeda}", str(e.exception))
        with self.assertRaises(AdvakError) as e:
            self.rodar("seja r = `${5:coisa}`")
        self.assertIn("Disponíveis", str(e.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
