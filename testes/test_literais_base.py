"""
Literais com base 0x, 0b e 0o (maiúsculas ou minúsculas): os tokens do lexer, as mensagens de erro em português e o que
não pode mudar nos números decimais. Também roda programas .dk de verdade, com `python -I advak.py` (run, check e
formatar) numa pasta temporária, sem tocar em arquivo do repositório.

Rodar:  python -I testes/test_literais_base.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from advak_lexer import AdvakLexer   # noqa: E402


def tipos(codigo):
    return [(t['type'], t['value']) for t in AdvakLexer(codigo).tokenize()]


def erro_do_lexer(testcase, codigo):
    with testcase.assertRaises(SyntaxError) as ctx:
        AdvakLexer(codigo).tokenize()
    return str(ctx.exception)


def rodar_dk(fonte, comando="run"):
    """Grava `fonte` em prog.dk numa pasta temporária e roda `python -I advak.py <comando> prog.dk` ali dentro.
    Devolve (código de saída, saída com \\n, conteúdo do arquivo depois)."""
    env = {k: v for k, v in os.environ.items() if k != "ADVAK_DEBUG"}
    env["PYTHONUTF8"] = "1"
    with tempfile.TemporaryDirectory() as pasta:
        arq = os.path.join(pasta, "prog.dk")
        with open(arq, "w", encoding="utf-8", newline="\n") as f:
            f.write(fonte)
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), comando, arq], cwd=pasta, timeout=60,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                           stdin=subprocess.DEVNULL)
        with open(arq, encoding="utf-8", newline="") as f:
            depois = f.read()
    return r.returncode, (r.stdout + r.stderr).replace("\r\n", "\n"), depois


class TesteTokens(unittest.TestCase):
    def test_L1_hexadecimal(self):
        for codigo in ("0x1F", "0X1f"):
            with self.subTest(codigo=codigo):
                self.assertEqual(tipos(codigo), [('NUMBER', 31)])

    def test_L2_binario(self):
        for codigo in ("0b101", "0B101"):
            with self.subTest(codigo=codigo):
                self.assertEqual(tipos(codigo), [('NUMBER', 5)])

    def test_L3_octal(self):
        for codigo in ("0o17", "0O17"):
            with self.subTest(codigo=codigo):
                self.assertEqual(tipos(codigo), [('NUMBER', 15)])

    def test_L4_hexadecimal_com_letras_maiusculas_e_minusculas(self):
        self.assertEqual(tipos("0xDEADbeef"), [('NUMBER', 3735928559)])

    def test_L5_zeros(self):
        for codigo in ("0x0", "0b0", "0o0"):
            with self.subTest(codigo=codigo):
                self.assertEqual(tipos(codigo), [('NUMBER', 0)])

    def test_L6_numero_grande(self):
        self.assertEqual(tipos("0xFFFFFFFFFFFFFFFFFFFF"), [('NUMBER', 1208925819614629174706175)])

    def test_L7_linha_e_coluna_do_literal(self):
        numeros = [t for t in AdvakLexer("seja a = 0x1F").tokenize() if t['type'] == 'NUMBER']
        self.assertEqual(len(numeros), 1)
        self.assertEqual((numeros[0]['value'], numeros[0]['line'], numeros[0]['col']), (31, 1, 10))

    def test_L8_sem_separador_underscore(self):
        self.assertEqual(tipos("0x1_F"), [('NUMBER', 1), ('IDENT', '_F')])

    def test_L9_sem_expoente(self):
        self.assertEqual(tipos("1e3"), [('NUMBER', 1), ('IDENT', 'e3')])


class TesteErrosDoLexer(unittest.TestCase):
    def test_E1_prefixo_hexadecimal_sem_digitos(self):
        msg = erro_do_lexer(self, "0x")
        for parte in ("hexadecimal", "sem dígitos", "'0x'"):
            self.assertIn(parte, msg)

    def test_E2_prefixo_binario_sem_digitos(self):
        msg = erro_do_lexer(self, "0b")
        self.assertIn("binário", msg)
        self.assertIn("sem dígitos", msg)

    def test_E3_prefixo_octal_maiusculo_sem_digitos(self):
        msg = erro_do_lexer(self, "0O")
        self.assertIn("octal", msg)
        self.assertIn("sem dígitos", msg)

    def test_E4_digito_invalido_no_binario(self):
        msg = erro_do_lexer(self, "0b2")
        for parte in ("Dígito '2' inválido", "binário", "'0b2'"):
            self.assertIn(parte, msg)

    def test_E5_digito_invalido_no_octal(self):
        msg = erro_do_lexer(self, "0o8")
        self.assertIn("Dígito '8' inválido", msg)
        self.assertIn("octal", msg)

    def test_E6_digito_invalido_no_hexadecimal(self):
        msg = erro_do_lexer(self, "0xG1")
        self.assertIn("Dígito 'G' inválido", msg)
        self.assertIn("hexadecimal", msg)

    def test_E7_letras_depois_do_binario(self):
        msg = erro_do_lexer(self, "0b101abc")
        self.assertIn("Dígito 'a' inválido", msg)
        self.assertIn("binário", msg)


class TesteRegressao(unittest.TestCase):
    def test_R1_zero_e_inteiros_decimais(self):
        self.assertEqual(tipos("0"), [('NUMBER', 0)])
        self.assertEqual(tipos("10"), [('NUMBER', 10)])
        self.assertEqual(tipos("007"), [('NUMBER', 7)])

    def test_R2_decimal(self):
        self.assertEqual(tipos("0.5"), [('FLOAT', 0.5)])

    def test_R3_intervalo_a_partir_do_zero(self):
        self.assertEqual(tipos("0..3"), [('NUMBER', 0), ('RANGE', '..'), ('NUMBER', 3)])

    def test_R4_identificadores_com_prefixo_no_meio(self):
        self.assertEqual(tipos("x0b1"), [('IDENT', 'x0b1')])
        self.assertEqual(tipos("a0x1"), [('IDENT', 'a0x1')])

    def test_R5_texto_com_prefixo_continua_texto(self):
        self.assertEqual(tipos('"0x1F"'), [('STRING', '0x1F')])

    def test_R6_comentario_com_prefixo_continua_comentario(self):
        self.assertEqual(tipos("// 0x1F"), [])


class TesteExecucao(unittest.TestCase):
    """P1 a P17: programas .dk de verdade, cada um por `python -I advak.py` numa pasta temporária."""

    def saida(self, fonte):
        return rodar_dk(fonte)[1].strip()

    def test_P01_soma_com_hexadecimal(self):
        self.assertEqual(self.saida("imprimir(0x1F + 1)\n"), "32")

    def test_P02_e_bit_a_bit_com_binarios(self):
        self.assertEqual(self.saida("imprimir(0b101 & 0b011)\n"), "1")

    def test_P03_deslocamento_a_direita(self):
        self.assertEqual(self.saida("imprimir(0xFF >> 4)\n"), "15")

    def test_P04_divisao_inteira_depois_de_um_literal_com_base(self):
        self.assertEqual(self.saida("imprimir(7 // 0x2)\n"), "3")

    def test_P05_divisao_inteira_entre_dois_literais_com_base(self):
        self.assertEqual(self.saida("imprimir(0x10 // 0x4)\n"), "4")

    def test_P06_interpolacao_sem_formato(self):
        self.assertEqual(self.saida("imprimir(`${0xFF}`)\n"), "255")

    def test_P07_interpolacao_com_formato_x(self):
        self.assertEqual(self.saida("imprimir(`${0xFF:x}`)\n"), "ff")

    def test_P08_interpolacao_com_formato_08b(self):
        self.assertEqual(self.saida("imprimir(`${0b101:08b}`)\n"), "00000101")

    def test_P09_variavel_octal_e_tipo(self):
        self.assertEqual(self.saida("seja x = 0o17\nimprimir(x, tipo(x))\n"), "15 numero")

    def test_P10_negativo_de_hexadecimal(self):
        self.assertEqual(self.saida("imprimir(-0x1F)\n"), "-31")

    def test_P11_deslocamento_com_hexadecimal(self):
        self.assertEqual(self.saida("imprimir(1 << 0x4)\n"), "16")

    def test_P12_nao_bit_a_bit_de_hexadecimal(self):
        self.assertEqual(self.saida("imprimir(~0x0F)\n"), "-16")

    def test_P13_numero_de_texto_hexadecimal_continua_zero(self):
        self.assertEqual(self.saida('imprimir(numero("0x1F"))\n'), "0")

    def test_P14_prefixo_sem_digitos_da_erro_de_sintaxe_em_portugues(self):
        saida = self.saida("imprimir(0x)\n")
        self.assertIn("ERRO DE SINTAXE", saida)
        self.assertIn("sem dígitos", saida)

    def test_P15_advak_check_aceita_literal_hexadecimal(self):
        codigo, saida, _ = rodar_dk("seja a = 0x1F\n", "check")
        self.assertIn("sintaxe válida", saida)

    def test_P16_advak_formatar_mantem_os_literais_escritos_assim(self):
        codigo, saida, depois = rodar_dk("seja a=0x1F\nseja   b = 0b101\nimprimir(a+b)\n", "formatar")
        self.assertEqual(codigo, 0, saida)
        self.assertIn("0x1F", depois)
        self.assertIn("0b101", depois)

    def test_P17_advak_check_aceita_octal(self):
        codigo, saida, _ = rodar_dk("seja x = 0o17\nimprimir(x)\n", "check")
        self.assertEqual(codigo, 0, saida)
        self.assertIn("sintaxe válida", saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
