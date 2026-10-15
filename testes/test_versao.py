"""
Testes da versão no REPL: o banner e a linha de abertura leem a VERSION de advak.py (sem cópia escrita à mão).

Rodar:  python -I testes/test_versao.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import advak_repl   # noqa: E402


def versao_do_comando():
    """O que o próprio programa responde em `advak --versao`."""
    saida = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), "--versao"], capture_output=True,
                           text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"), cwd=RAIZ, timeout=60).stdout
    return saida.split()[-1]


class TesteVersaoDoRepl(unittest.TestCase):
    def test_repl_mostra_a_mesma_versao_do_advak_py(self):
        self.assertEqual(advak_repl.ler_versao(), versao_do_comando())

    def test_banner_contem_a_versao_lida(self):
        self.assertIn(advak_repl.ler_versao(), advak_repl.BANNER)
        self.assertNotIn("{versao}", advak_repl.BANNER)

    def test_versao_nova_aparece_sem_mexer_no_repl(self):
        with tempfile.TemporaryDirectory() as pasta:
            with open(os.path.join(pasta, "advak.py"), "w", encoding="utf-8") as f:
                f.write('import os\nVERSION = "9.8.7"\n')
            self.assertEqual(advak_repl.ler_versao(pasta), "9.8.7")
            self.assertIn("9.8.7", advak_repl.montar_banner(advak_repl.ler_versao(pasta)))

    def test_linha_da_versao_tem_sempre_o_mesmo_tamanho(self):
        """O desenho do banner já tem linhas de larguras diferentes; a linha da versão não pode piorar isso."""
        def linha_da_versao(versao):
            return [l for l in advak_repl.montar_banner(versao).splitlines() if "╚═╝  ╚═╝╚═════╝" in l][0]
        tamanhos = {len(linha_da_versao(v)) for v in ("5.2.0", "10.11.12", "1.0")}
        self.assertEqual(len(tamanhos), 1)

    def test_sem_advak_py_nao_quebra(self):
        with tempfile.TemporaryDirectory() as pasta:
            self.assertEqual(advak_repl.ler_versao(pasta), "?")

    def test_nenhuma_versao_escrita_a_mao_no_repl(self):
        with open(os.path.join(RAIZ, "advak_repl.py"), encoding="utf-8") as f:
            codigo = f.read()
        self.assertNotIn("5.2.0", codigo)
        self.assertNotIn("Advak 5.0", codigo.split("AJUDA")[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
