"""Pasta do programa: Arquivo.pasta_do_programa() e Arquivo.do_programa("...").

Duas partes:
  * TesteComportamentoAtual FIXA o que já existia e NÃO muda: Arquivo.* e importar resolvem caminhos relativos pelo
    DIRETÓRIO ATUAL (onde o comando foi rodado), não pela pasta do .dk. Inclui a limitação conhecida: um módulo
    homônimo do diretório atual é carregado sem aviso.
  * TestePastaDoPrograma cobre as duas funções novas (rodando de outra pasta, por `advak programa.dk` e por
    `advak run`, REPL, dentro de um tratador da GUI).

Cada programa roda em subprocesso (`python -I advak.py ...`) com `cwd` escolhido pelo teste. Os caminhos são
comparados com realpath, porque a pasta temporária do Windows pode vir no formato curto (SUPORT~1).

Rodar:  python -I testes/test_pasta_programa.py
"""
import os, subprocess, sys, tempfile, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def igual(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


class Cenario:
    """Três pastas: jogo/ (o .dk e dados.txt = A, util.dk), outra/ (dados.txt = B, util.dk homônimo) e vazia/."""

    def __init__(self, prog):
        self._tmp = tempfile.TemporaryDirectory(prefix="pasta com espaço ")
        base = self._tmp.name
        self.jogo, self.outra, self.vazia = (os.path.join(base, n) for n in ("jogo", "outra", "vazia"))
        for p in (self.jogo, self.outra, self.vazia):
            os.makedirs(p)
        self._escrever(self.jogo, "dados.txt", "A")
        self._escrever(self.outra, "dados.txt", "B")
        self._escrever(self.jogo, "util.dk", 'exportar função oi() { retornar "modulo-da-pasta-do-dk" }\n')
        self._escrever(self.outra, "util.dk", 'exportar função oi() { retornar "modulo-do-diretorio-atual" }\n')
        self._escrever(self.jogo, "prog.dk", prog)
        self.prog = os.path.join(self.jogo, "prog.dk")

    @staticmethod
    def _escrever(pasta, nome, texto):
        with open(os.path.join(pasta, nome), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)

    def rodar(self, cwd, comando=None, entrada=None):
        """Devolve (stdout + stderr). `comando`: lista de argumentos depois de advak.py (padrão: o caminho do .dk)."""
        args = comando if comando is not None else [self.prog]
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), *args], cwd=cwd, timeout=90,
                           input=entrada, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONUTF8="1"))
        return r.stdout + r.stderr

    def fechar(self):
        self._tmp.cleanup()


def linhas(saida):
    return [l.strip() for l in saida.splitlines() if l.strip()]


class Base(unittest.TestCase):
    def cenario(self, prog):
        c = Cenario(prog)
        self.addCleanup(c.fechar)
        return c


class TesteComportamentoAtual(Base):
    """Passam antes e depois da mudança: nada disto pode mudar."""

    def test_arquivo_ler_usa_o_diretorio_atual(self):
        c = self.cenario('imprimir(Arquivo.ler("dados.txt"))\n')
        self.assertEqual(linhas(c.rodar(c.jogo))[-1], "A")
        self.assertEqual(linhas(c.rodar(c.outra))[-1], "B")           # outra pasta: lê o dados.txt de lá, sem erro

    def test_arquivo_ler_sem_arquivo_no_diretorio_atual_falha(self):
        c = self.cenario('tentar { imprimir(Arquivo.ler("dados.txt")) } capturar (e) { imprimir("ERRO", e) }\n')
        s = c.rodar(c.vazia)
        self.assertIn("ERRO Arquivo não encontrado: 'dados.txt'", s)

    def test_arquivo_pasta_atual_e_o_diretorio_de_onde_rodou(self):
        c = self.cenario('imprimir(Arquivo.pasta_atual())\n')
        self.assertTrue(igual(linhas(c.rodar(c.outra))[-1], c.outra))

    def test_importar_da_mesma_pasta_funciona(self):
        c = self.cenario('importar { oi } de "util.dk"\nimprimir(oi())\n')
        self.assertEqual(linhas(c.rodar(c.jogo))[-1], "modulo-da-pasta-do-dk")

    def test_importar_homonimo_do_diretorio_atual_e_carregado_sem_aviso(self):
        """Limitação conhecida, NÃO tratada (T2): vence o util.dk do diretório atual, não o da pasta do .dk."""
        c = self.cenario('importar { oi } de "util.dk"\nimprimir(oi())\n')
        s = c.rodar(c.outra)
        self.assertEqual(linhas(s)[-1], "modulo-do-diretorio-atual")
        self.assertNotIn("Erro", s)

    def test_importar_modulo_so_na_pasta_do_dk_nao_e_achado_de_outra_pasta(self):
        c = self.cenario('importar { oi } de "util.dk"\nimprimir(oi())\n')
        s = c.rodar(c.vazia)
        self.assertIn("Módulo não encontrado: 'util.dk'", s)
        self.assertNotIn("modulo-da-pasta-do-dk", s)


class TestePastaDoPrograma(Base):
    def test_pasta_do_programa_de_outra_pasta(self):
        c = self.cenario('imprimir(Arquivo.pasta_do_programa())\n')
        for cwd in (c.jogo, c.outra, c.vazia):
            self.assertTrue(igual(linhas(c.rodar(cwd))[-1], c.jogo), cwd)

    def test_mesma_resposta_por_advak_run(self):
        c = self.cenario('imprimir(Arquivo.pasta_do_programa())\n')
        s = c.rodar(c.outra, comando=["run", c.prog])
        self.assertTrue(igual(linhas(s)[-1], c.jogo), s)

    def test_do_programa_junta_a_pasta_do_programa(self):
        c = self.cenario('imprimir(Arquivo.do_programa("imagens/heroi.png"))\n')
        esperado = os.path.join(c.jogo, "imagens", "heroi.png")
        self.assertTrue(igual(linhas(c.rodar(c.outra))[-1], esperado))

    def test_do_programa_com_arquivo_ler_le_o_da_pasta_do_programa(self):
        """De outra pasta, que tem OUTRO dados.txt: Arquivo.ler("dados.txt") lê B; do_programa leva ao A."""
        c = self.cenario('imprimir(Arquivo.ler("dados.txt"))\n'
                         'imprimir(Arquivo.ler(Arquivo.do_programa("dados.txt")))\n')
        self.assertEqual(linhas(c.rodar(c.outra))[-2:], ["B", "A"])

    def test_do_programa_deixa_caminho_absoluto_como_esta(self):
        absoluto = os.path.join(tempfile.gettempdir(), "x", "y.png").replace("\\", "/")
        c = self.cenario(f'imprimir(Arquivo.do_programa("{absoluto}"))\n')
        self.assertEqual(linhas(c.rodar(c.outra))[-1], absoluto)

    def test_do_programa_so_aceita_texto(self):
        c = self.cenario('tentar { Arquivo.do_programa(5) } capturar (e) { imprimir("ERRO", e) }\n'
                         'tentar { Arquivo.do_programa(nulo) } capturar (e) { imprimir("ERRO", e) }\n')
        s = linhas(c.rodar(c.outra))
        self.assertEqual(len([l for l in s if l.startswith("ERRO Arquivo.do_programa espera um texto")]), 2, s)

    def test_cd_no_programa_nao_muda_a_pasta_do_programa(self):
        c = self.cenario('OS.cd(Arquivo.pasta_atual() + "/..")\n'
                         'imprimir(Arquivo.pasta_do_programa())\n')
        self.assertTrue(igual(linhas(c.rodar(c.outra))[-1], c.jogo))

    def test_caminho_relativo_do_comando_vira_absoluto(self):
        """`advak ../jogo/prog.dk` (relativo ao cwd) deve dar a mesma pasta absoluta."""
        c = self.cenario('imprimir(Arquivo.pasta_do_programa())\n')
        s = c.rodar(c.outra, comando=[os.path.join("..", "jogo", "prog.dk")])
        self.assertTrue(igual(linhas(s)[-1], c.jogo), s)

    def test_repl_sem_arquivo_cai_no_diretorio_atual(self):
        c = self.cenario("")
        s = c.rodar(c.outra, comando=["repl"],
                    entrada='imprimir(Arquivo.pasta_do_programa() == Arquivo.pasta_atual())\n')
        self.assertIn("verdadeiro", s)

    def test_sem_cmd_run_vale_o_diretorio_atual(self):
        """Interpretador usado direto (testes, compilado): nenhum programa definido."""
        codigo = ("import sys, os; sys.path.insert(0, %r); import advak_interpreter as a; "
                  "print(a.pasta_do_programa() == os.getcwd())" % RAIZ)
        r = subprocess.run([sys.executable, "-I", "-c", codigo], cwd=tempfile.gettempdir(), capture_output=True,
                           text=True, timeout=60)
        self.assertEqual(r.stdout.strip(), "True", r.stderr)

    def test_dentro_de_um_tratador_da_gui(self):
        """O tratador roda em outra thread, com interpretador criado por __new__ (sem __init__)."""
        c = self.cenario('seja jan = gui.janela("t", 200, 100)\n'
                         'gui.apos(100, () => {\n'
                         '    imprimir("no tratador:", Arquivo.pasta_do_programa())\n'
                         '    gui.parar()\n'
                         '})\n'
                         'gui.iniciar()\n')
        s = c.rodar(c.outra)
        ult = [l for l in linhas(s) if l.startswith("no tratador:")]
        self.assertEqual(len(ult), 1, s)
        self.assertTrue(igual(ult[0].split(":", 1)[1].strip(), c.jogo), s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
