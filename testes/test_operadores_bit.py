"""
Deslocamento (<< e >>) com contagem negativa: o erro de execução em português, que pode ser capturado com `tentar`, e o que
não pode mudar nos deslocamentos de contagem zero ou positiva. Os programas .dk rodam de verdade, com `python -I advak.py run`
numa pasta temporária, sem tocar em arquivo do repositório.

Rodar:  python -I testes/test_operadores_bit.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MENSAGEM = "Deslocamento com contagem negativa: {conta}. A contagem de bits precisa ser zero ou maior."


def rodar_dk(fonte):
    """Grava `fonte` em prog.dk numa pasta temporária e roda `python -I advak.py run prog.dk` ali dentro; devolve a saída."""
    env = {k: v for k, v in os.environ.items() if k != "ADVAK_DEBUG"}
    env["PYTHONUTF8"] = "1"
    with tempfile.TemporaryDirectory() as pasta:
        arq = os.path.join(pasta, "prog.dk")
        with open(arq, "w", encoding="utf-8", newline="\n") as f:
            f.write(fonte)
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), "run", arq], cwd=pasta, timeout=60,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                           stdin=subprocess.DEVNULL)
    return (r.stdout + r.stderr).replace("\r\n", "\n")


class TesteDeslocamentoNegativo(unittest.TestCase):
    def conferir_erro(self, saida, conta):
        self.assertIn("ERRO DE EXECUÇÃO", saida, saida)
        self.assertIn(MENSAGEM.format(conta=conta), saida, saida)
        for cru in ("ERRO INESPERADO", "ValueError", "negative shift count"):
            self.assertNotIn(cru, saida, saida)

    def test_D1_esquerda_com_contagem_negativa(self):
        self.conferir_erro(rodar_dk("imprimir(1 << -1)\n"), "1 << -1")

    def test_D2_direita_com_contagem_negativa(self):
        self.conferir_erro(rodar_dk("imprimir(8 >> -2)\n"), "8 >> -2")

    def test_D3_contagem_negativa_numa_variavel(self):
        self.conferir_erro(rodar_dk("seja n = -3\nimprimir(1 << n)\n"), "1 << -3")

    def test_D4_o_erro_pode_ser_capturado(self):
        saida = rodar_dk('tentar {\n    imprimir(1 << -1)\n} capturar (e) {\n    imprimir("PEGOU:", e)\n}\n')
        self.assertIn("PEGOU: " + MENSAGEM.format(conta="1 << -1"), saida, saida)

    def test_D5_contagem_decimal_e_truncada_antes(self):
        self.conferir_erro(rodar_dk("imprimir(1 << -1.5)\n"), "1 << -1")

    def test_D6_contagens_zero_e_positivas_nao_mudam(self):
        saida = rodar_dk("imprimir(1 << 0)\nimprimir(-8 >> 1)\nimprimir(5 >> 0)\nimprimir(0xFF >> 8)\n"
                         "imprimir(1 << 100)\n")
        self.assertEqual(saida.split(), ["1", "-4", "5", "0", "1267650600228229401496703205376"], saida)


if __name__ == "__main__":
    unittest.main(verbosity=2)
