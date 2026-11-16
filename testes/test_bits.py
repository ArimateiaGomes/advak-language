"""
Bits (etapa 1.2): binario, hexa, de_binario, de_hexa, limitar, com_sinal, contar_uns, bit, ligar e desligar, com o teto de
65536 (largura de 1 a 65536; posição de 0 a 65535), os erros em português capturáveis com `tentar`, e os casos que ainda não
tinham sido medidos em .dk (hexa, limitar e com_sinal com largura 65537; desligar com posição 65536).

O esperado de cada caso foi escrito antes da primeira execução. Os programas .dk rodam de verdade, com
`python -I advak.py run` numa pasta temporária, sem tocar em arquivo do repositório.

Rodar:  python -I testes/test_bits.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICA = " Use piso(), teto(), arred() ou // para obter um inteiro."


def rodar_dk(fonte):
    """Grava `fonte` em prog.dk numa pasta temporária e roda `python -I advak.py run prog.dk` ali dentro; devolve a saída."""
    env = {k: v for k, v in os.environ.items() if k != "ADVAK_DEBUG"}
    env["PYTHONUTF8"] = "1"
    with tempfile.TemporaryDirectory() as pasta:
        arq = os.path.join(pasta, "prog.dk")
        with open(arq, "w", encoding="utf-8", newline="\n") as f:
            f.write(fonte)
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), "run", arq], cwd=pasta, timeout=120,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                           stdin=subprocess.DEVNULL)
    return (r.stdout + r.stderr).replace("\r\n", "\n")


def valor(expr):
    return f"imprimir({expr})\n"


def erro(expr):
    """Uma linha de saída 'E: <mensagem>' se `expr` falhar; se não falhar, 'SEM ERRO: <resultado>'."""
    return f'tentar {{\n    seja r = {expr}\n    imprimir("SEM ERRO:", r)\n}} capturar (e) {{\n    imprimir("E:", e)\n}}\n'


class Base(unittest.TestCase):
    def linhas(self, *partes):
        saida = rodar_dk("".join(partes))
        return saida.split("\n")[:-1] if saida.endswith("\n") else saida.split("\n")

    def conferir(self, partes, esperado):
        obtido = self.linhas(*partes)
        self.assertEqual(obtido, esperado, "\n".join(obtido))


class TesteBinarioEHexa(Base):
    def test_B1_binario_sem_largura(self):
        self.conferir([valor("Bits.binario(5)"), valor("Bits.binario(0)"), valor("Bits.binario(-5)")],
                      ["101", "0", "-101"])

    def test_B2_binario_com_largura(self):
        self.conferir([valor("Bits.binario(5, 8)"), valor("Bits.binario(-1, 8)"), valor("Bits.binario(255, 8)"),
                       valor("Bits.binario(-128, 8)"), valor("Bits.binario(1, 1)"), valor("Bits.binario(-1, 1)")],
                      ["00000101", "11111111", "11111111", "10000000", "1", "1"])

    def test_B3_binario_nao_cabe(self):
        self.conferir([erro("Bits.binario(256, 8)"), erro("Bits.binario(-129, 8)"), erro("Bits.binario(2, 1)")],
                      ["E: Bits.binario: 256 não cabe em 8 bits (a faixa é de -128 a 255).",
                       "E: Bits.binario: -129 não cabe em 8 bits (a faixa é de -128 a 255).",
                       "E: Bits.binario: 2 não cabe em 1 bit (a faixa é de -1 a 1)."])

    def test_H1_hexa_sem_largura(self):
        self.conferir([valor("Bits.hexa(255)"), valor("Bits.hexa(0)"), valor("Bits.hexa(-255)")],
                      ["ff", "0", "-ff"])

    def test_H2_hexa_com_largura_arredonda_para_cima_em_digitos(self):
        self.conferir([valor("Bits.hexa(255, 8)"), valor("Bits.hexa(-1, 8)"), valor("Bits.hexa(1, 12)"),
                       valor("Bits.hexa(10, 4)"), valor("Bits.hexa(1, 5)")],
                      ["ff", "ff", "001", "a", "01"])

    def test_H3_hexa_nao_cabe(self):
        self.conferir([erro("Bits.hexa(256, 8)")],
                      ["E: Bits.hexa: 256 não cabe em 8 bits (a faixa é de -128 a 255)."])


class TesteDeTexto(Base):
    def test_T1_de_binario(self):
        self.conferir([valor('Bits.de_binario("101")'), valor('Bits.de_binario("0b101")'),
                       valor('Bits.de_binario("0B101")'), valor('Bits.de_binario("-101")'),
                       valor('Bits.de_binario("-0b101")')],
                      ["5", "5", "5", "-5", "-5"])

    def test_T2_de_hexa(self):
        self.conferir([valor('Bits.de_hexa("ff")'), valor('Bits.de_hexa("0xFF")'), valor('Bits.de_hexa("-0x10")')],
                      ["255", "255", "-16"])

    def test_T3_erros_de_texto(self):
        self.conferir([erro('Bits.de_binario("")'), erro('Bits.de_binario("0b")'), erro('Bits.de_binario("102")'),
                       erro('Bits.de_hexa("fg")'), erro("Bits.de_binario(5)")],
                      ["E: Bits.de_binario: o texto '' não tem dígitos.",
                       "E: Bits.de_binario: o texto '0b' não tem dígitos.",
                       "E: Bits.de_binario: dígito '2' inválido em número binário '102'.",
                       "E: Bits.de_hexa: dígito 'g' inválido em número hexadecimal 'fg'.",
                       "E: Bits.de_binario espera um texto com o número binário, mas recebeu 5."])


    def test_T4_rigor_do_texto_binario(self):
        """Espaço, sinal + e sublinhado não são aceitos (nem o segundo sinal -)."""
        self.conferir([erro('Bits.de_binario(" 101")'), erro('Bits.de_binario("+101")'),
                       erro('Bits.de_binario("1_0")'), erro('Bits.de_binario("--1")')],
                      ["E: Bits.de_binario: dígito ' ' inválido em número binário ' 101'.",
                       "E: Bits.de_binario: dígito '+' inválido em número binário '+101'.",
                       "E: Bits.de_binario: dígito '_' inválido em número binário '1_0'.",
                       "E: Bits.de_binario: dígito '-' inválido em número binário '--1'."])

    def test_T5_rigor_do_texto_hexa(self):
        self.conferir([erro('Bits.de_hexa(" ff")'), erro('Bits.de_hexa("+ff")'), erro('Bits.de_hexa("f_f")'),
                       erro('Bits.de_hexa("f f")')],
                      ["E: Bits.de_hexa: dígito ' ' inválido em número hexadecimal ' ff'.",
                       "E: Bits.de_hexa: dígito '+' inválido em número hexadecimal '+ff'.",
                       "E: Bits.de_hexa: dígito '_' inválido em número hexadecimal 'f_f'.",
                       "E: Bits.de_hexa: dígito ' ' inválido em número hexadecimal 'f f'."])


class TesteLimitarComSinalContar(Base):
    def test_L1_limitar(self):
        self.conferir([valor("Bits.limitar(300, 8)"), valor("Bits.limitar(-1, 8)"), valor("Bits.limitar(5, 1)")],
                      ["44", "255", "1"])

    def test_S1_com_sinal(self):
        self.conferir([valor("Bits.com_sinal(255, 8)"), valor("Bits.com_sinal(128, 8)"), valor("Bits.com_sinal(127, 8)"),
                       valor("Bits.com_sinal(-1, 8)")],
                      ["-1", "-128", "127", "-1"])

    def test_S2_com_sinal_nao_cabe(self):
        self.conferir([erro("Bits.com_sinal(256, 8)")],
                      ["E: Bits.com_sinal: 256 não cabe em 8 bits (a faixa é de -128 a 255)."])

    def test_C1_contar_uns(self):
        self.conferir([valor("Bits.contar_uns(255)"), valor("Bits.contar_uns(0)"), valor("Bits.contar_uns(5)"),
                       erro("Bits.contar_uns(-1)")],
                      ["8", "0", "2",
                       "E: Bits.contar_uns não aceita número negativo (recebeu -1). "
                       "Use Bits.limitar(n, largura) antes para escolher a largura."])


class TesteBitAPosicao(Base):
    def test_P1_bit_ligar_desligar(self):
        self.conferir([valor("Bits.bit(5, 0)"), valor("Bits.bit(5, 1)"), valor("Bits.bit(5, 2)"),
                       valor("Bits.bit(-1, 100)"), valor("Bits.ligar(0, 3)"), valor("Bits.ligar(8, 3)"),
                       valor("Bits.desligar(15, 0)"), valor("Bits.desligar(0, 5)"), valor("Bits.desligar(-1, 0)")],
                      ["1", "0", "1", "1", "8", "8", "14", "0", "-2"])

    def test_P2_posicao_negativa(self):
        self.conferir([erro("Bits.bit(5, -1)"), erro("Bits.ligar(5, -1)"), erro("Bits.desligar(5, -1)")],
                      ["E: Bits.bit: a posição precisa ser um inteiro de 0 a 65535, mas recebeu -1.",
                       "E: Bits.ligar: a posição precisa ser um inteiro de 0 a 65535, mas recebeu -1.",
                       "E: Bits.desligar: a posição precisa ser um inteiro de 0 a 65535, mas recebeu -1."])


class TesteTipos(Base):
    def test_Y1_decimal_bool_e_texto(self):
        self.conferir([erro("Bits.binario(1.5)"), erro("Bits.binario(verdadeiro)"), erro('Bits.binario("5")'),
                       erro("Bits.binario(5, 2.5)"), erro("Bits.bit(5, 1.5)")],
                      ["E: Bits.binario espera um número inteiro, mas recebeu 1.5." + DICA,
                       "E: Bits.binario espera um número inteiro, mas recebeu verdadeiro.",
                       "E: Bits.binario espera um número inteiro, mas recebeu '5'.",
                       "E: Bits.binario espera uma largura inteira, mas recebeu 2.5." + DICA,
                       "E: Bits.bit espera uma posição inteira, mas recebeu 1.5." + DICA])


    def test_Y2_nulo_como_largura_e_sem_largura(self):
        self.conferir([valor("Bits.binario(5, nulo)"), valor("Bits.hexa(255, nulo)")], ["101", "ff"])

    def test_Y3_decimal_de_valor_inteiro_continua_sendo_decimal(self):
        """5.0 e 10 / 2 são decimais (float): erro, mesmo valendo 5. A dica de piso()/// aparece."""
        esperado = "E: Bits.binario espera um número inteiro, mas recebeu 5.0." + DICA
        self.conferir([erro("Bits.binario(5.0)"), erro("Bits.binario(10 / 2)")], [esperado, esperado])

    def test_Y4_largura_decimal_ou_booleana_em_limitar_e_com_sinal(self):
        self.conferir([erro("Bits.limitar(5, 2.5)"), erro("Bits.limitar(5, verdadeiro)"),
                       erro("Bits.com_sinal(5, 2.5)"), erro("Bits.com_sinal(5, verdadeiro)")],
                      ["E: Bits.limitar espera uma largura inteira, mas recebeu 2.5." + DICA,
                       "E: Bits.limitar espera uma largura inteira, mas recebeu verdadeiro.",
                       "E: Bits.com_sinal espera uma largura inteira, mas recebeu 2.5." + DICA,
                       "E: Bits.com_sinal espera uma largura inteira, mas recebeu verdadeiro."])


class TesteTeto(Base):
    def test_X1_largura_fora_de_1_a_65536(self):
        msg = "a largura precisa ser um inteiro de 1 a 65536, mas recebeu {}."
        self.conferir([erro("Bits.binario(0, 0)"), erro("Bits.binario(0, -1)"), erro("Bits.binario(0, 65537)"),
                       erro("Bits.limitar(0, 0)")],
                      ["E: Bits.binario: " + msg.format(0), "E: Bits.binario: " + msg.format(-1),
                       "E: Bits.binario: " + msg.format(65537), "E: Bits.limitar: " + msg.format(0)])

    def test_X2_largura_65536_e_aceita(self):
        saida = rodar_dk(valor("Bits.binario(0, 65536)") + valor("Bits.binario(-1, 65536)") +
                         valor("Bits.contar_uns(Bits.limitar(-1, 65536))") + valor("Bits.hexa(0, 65536)"))
        a, b, c, d = saida.strip("\n").split("\n")
        self.assertEqual(a, "0" * 65536)
        self.assertEqual(b, "1" * 65536)
        self.assertEqual(c, "65536")
        self.assertEqual(d, "0" * 16384)

    def test_X3_posicao_65535_e_aceita_e_65536_nao(self):
        self.conferir([valor("Bits.bit(Bits.ligar(0, 65535), 65535)"),
                       valor("Bits.bit(Bits.desligar(Bits.ligar(0, 65535), 65535), 65535)"),
                       erro("Bits.bit(0, 65536)"), erro("Bits.ligar(0, 65536)")],
                      ["1", "0",
                       "E: Bits.bit: a posição precisa ser um inteiro de 0 a 65535, mas recebeu 65536.",
                       "E: Bits.ligar: a posição precisa ser um inteiro de 0 a 65535, mas recebeu 65536."])

    def test_X4_nao_medidos_antes_em_dk(self):
        """hexa, limitar e com_sinal com largura 65537 e desligar com posição 65536."""
        msg = "a largura precisa ser um inteiro de 1 a 65536, mas recebeu 65537."
        self.conferir([erro("Bits.hexa(0, 65537)"), erro("Bits.limitar(0, 65537)"), erro("Bits.com_sinal(0, 65537)"),
                       erro("Bits.desligar(0, 65536)")],
                      ["E: Bits.hexa: " + msg, "E: Bits.limitar: " + msg, "E: Bits.com_sinal: " + msg,
                       "E: Bits.desligar: a posição precisa ser um inteiro de 0 a 65535, mas recebeu 65536."])


if __name__ == "__main__":
    unittest.main(verbosity=2)
