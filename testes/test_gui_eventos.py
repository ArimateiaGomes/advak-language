"""
Tratadores (callbacks) da interface gráfica: erro visível, um de cada vez, chamadas ao Tk de dentro do tratador.

Sem janela real, exceto nas classes marcadas com Tk (uma janela escondida, fechada pelo próprio teste).
Nada aqui depende de tempo: as esperas usam Event/fila; o único relógio é um limite de segurança.

Rodar:  python -I testes/test_gui_eventos.py
"""
import asyncio
import contextlib
import io
import os
import sys
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import advak_gui_modern as agm                                    # noqa: E402
from advak_interpreter import AdvakInterpreter                    # noqa: E402
from advak_lexer import AdvakLexer                                # noqa: E402
from advak_parser import Parser                                   # noqa: E402

try:
    import tkinter as tk
except ImportError:                                               # pragma: no cover
    tk = None

# Linha 5 é a que falha (nome que não existe).
FONTE_COM_ERRO = """seja a = 1
seja b = 2
funcao tratador(e) {
    seja c = 3
    imprimir(naoexiste)
    seja d = 4
}
"""


def funcao_dk(fonte, nome, **globais):
    """Roda `fonte` e devolve a função `nome` (uma AdvakFunction). `globais` são declaradas no programa."""
    ast = Parser(AdvakLexer(fonte).tokenize()).parse()
    it = AdvakInterpreter(ast)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(it.interpret())
    finally:
        loop.close()
    for k, v in globais.items():
        it.global_scope.declare(k, v)
    return it.global_scope.get(nome)


@contextlib.contextmanager
def capturar_stderr():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        yield buf


def esperar_ate(condicao, limite=5.0):
    """Espera uma condição que outra thread vai tornar verdadeira. Volta na hora quando ela já é verdadeira."""
    fim = time.monotonic() + limite
    while time.monotonic() < fim:
        if condicao():
            return True
        time.sleep(0.01)
    return condicao()


class TesteErroVisivel(unittest.TestCase):
    """Hoje o erro dentro de um callback é engolido (`except: pass`): a janela segue e ninguém fica sabendo."""

    def test_erro_em_callback_aparece_com_mensagem_e_linha(self):
        fn = funcao_dk(FONTE_COM_ERRO, "tratador")
        gui = agm.AdvakGUIModern()
        with capturar_stderr() as buf:
            gui._chamar(fn, {"tecla": "a"})
            esperar_ate(lambda: "naoexiste" in buf.getvalue())
        saida = buf.getvalue()
        self.assertIn("naoexiste", saida, "a mensagem do erro não apareceu")
        self.assertIn("linha 5", saida)
        self.assertIn("❌", saida)

    def test_erro_em_chamar_com_args_tambem_aparece(self):
        """Há um segundo caminho, _chamar_com_args, com o mesmo `except: pass`."""
        fn = funcao_dk(FONTE_COM_ERRO, "tratador")
        gui = agm.AdvakGUIModern()
        with capturar_stderr() as buf:
            gui._chamar_com_args(fn, [{"tecla": "a"}])
            esperar_ate(lambda: "naoexiste" in buf.getvalue())
        self.assertIn("naoexiste", buf.getvalue())
        self.assertIn("linha 5", buf.getvalue())

    def test_o_nome_da_origem_aparece(self):
        fn = funcao_dk(FONTE_COM_ERRO, "tratador")
        gui = agm.AdvakGUIModern()
        with capturar_stderr() as buf:
            gui._chamar(fn, {"tecla": "a"}, origem="tratador de tecla")
            esperar_ate(lambda: "naoexiste" in buf.getvalue())
        self.assertIn("tratador de tecla", buf.getvalue())

    def test_mesmo_erro_varias_vezes_aparece_uma_vez_e_o_resumo_conta(self):
        fn = funcao_dk(FONTE_COM_ERRO, "tratador")
        gui = agm.AdvakGUIModern()
        with capturar_stderr() as buf:
            for _ in range(3):
                gui._chamar(fn, {"tecla": "a"})
            self.assertTrue(gui._esperar_tratadores(5.0))
        self.assertEqual(buf.getvalue().count("naoexiste"), 1)
        self.assertEqual(gui._despachante.resumo(), (3, 1))
        self.assertEqual(gui._linha_resumo_erros(), "⚠ 3 erros em tratadores (1 diferente).")

    def test_sem_erro_nao_ha_resumo(self):
        gui = agm.AdvakGUIModern()
        self.assertEqual(gui._linha_resumo_erros(), "")

    def test_erro_continua_visivel_com_a_chave_de_seguranca_desligada(self):
        fn = funcao_dk(FONTE_COM_ERRO, "tratador")
        gui = agm.AdvakGUIModern()
        with mock.patch.object(agm, "_SERIALIZAR_CALLBACKS", False):
            with capturar_stderr() as buf:
                gui._chamar(fn, {"tecla": "a"})
                esperar_ate(lambda: "naoexiste" in buf.getvalue())
        self.assertIn("naoexiste", buf.getvalue())
        self.assertIn("linha 5", buf.getvalue())


class TesteUmPorVez(unittest.TestCase):
    """Dois tratadores nunca rodam ao mesmo tempo, e saem na ordem em que chegaram."""

    def setUp(self):
        self.entrou = {1: threading.Event(), 2: threading.Event()}
        self.liberar = threading.Event()
        self.ordem = []
        self.addCleanup(self.liberar.set)
        teste = self

        async def falso(self_interp, fn, args, escopo):
            i = args[0]
            teste.ordem.append(("entrou", i))
            teste.entrou[i].set()
            if i == 1:
                teste.liberar.wait(5)           # o primeiro fica preso até o teste soltar
            teste.ordem.append(("saiu", i))

        patcher = mock.patch.object(AdvakInterpreter, "_call_fn", falso)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.fn = funcao_dk("funcao h(e) { }", "h")

    def test_o_segundo_espera_o_primeiro_terminar(self):
        gui = agm.AdvakGUIModern()
        gui._chamar(self.fn, 1)
        self.assertTrue(self.entrou[1].wait(5))
        gui._chamar(self.fn, 2)
        self.assertFalse(self.entrou[2].wait(1.0), "o 2º tratador começou enquanto o 1º ainda rodava")
        self.liberar.set()
        self.assertTrue(gui._esperar_tratadores(5.0))
        self.assertEqual(self.ordem, [("entrou", 1), ("saiu", 1), ("entrou", 2), ("saiu", 2)])

    def test_com_a_chave_desligada_voltam_a_ser_simultaneos(self):
        """Plano B: desligar _SERIALIZAR_CALLBACKS devolve o comportamento antigo (uma thread por chamada)."""
        gui = agm.AdvakGUIModern()
        with mock.patch.object(agm, "_SERIALIZAR_CALLBACKS", False):
            gui._chamar(self.fn, 1)
            self.assertTrue(self.entrou[1].wait(5))
            gui._chamar(self.fn, 2)
            self.assertTrue(self.entrou[2].wait(5), "com a chave desligada o 2º devia rodar junto")
            self.liberar.set()

    def test_esperar_tratadores_devolve_falso_no_limite_e_verdadeiro_depois(self):
        gui = agm.AdvakGUIModern()
        gui._chamar(self.fn, 1)
        self.assertTrue(self.entrou[1].wait(5))
        self.assertFalse(gui._esperar_tratadores(0.2))     # ainda preso
        self.liberar.set()
        self.assertTrue(gui._esperar_tratadores(5.0))


class TesteChamadaPythonNaoMuda(unittest.TestCase):
    def test_funcao_python_continua_sincrona(self):
        """_chamar com função Python (não .dk) segue chamando na hora, na mesma thread."""
        visto = []
        gui = agm.AdvakGUIModern()
        gui._chamar(lambda x: visto.append((x, threading.get_ident())), 5)
        self.assertEqual(visto, [(5, threading.get_ident())])


class TesteTela(unittest.TestCase):
    def test_tela_continua_aceitando_so_o_canvas(self):
        class CanvasFalso:
            def find_all(self):
                return (1, 2)
        self.assertEqual(agm.Tela(CanvasFalso()).quantidade(), 2)
        self.assertIsNotNone(agm.Tela(CanvasFalso()).widget)


@unittest.skipIf(tk is None, "tkinter não instalado")
class _BaseTk(unittest.TestCase):
    """Janela escondida de verdade. Se não houver tela disponível, os testes são pulados."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as e:                                  # pragma: no cover
            raise unittest.SkipTest(f"sem tela para o Tk: {e}")
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except tk.TclError:
            pass

    def rodar_ate_terminar(self, inicio, limite_ms=10000):
        """Roda o mainloop. `inicio` roda dentro dele; o tratador chama root.quit() quando acabar."""
        self.estourou = []
        self.root.after(0, inicio)
        marca = self.root.after(limite_ms, lambda: (self.estourou.append(True), self.root.quit()))
        self.root.mainloop()
        self.root.after_cancel(marca)


class TesteChamadasAoTkDeDentroDoTratador(_BaseTk):
    """Caracterização: o tratador roda em outra thread e as chamadas ao Tk (area.mover, parar...) são levadas
    à thread da janela pelo próprio _tkinter. Passa antes e depois da mudança; a mudança não pode quebrar isso."""

    def test_chamada_ao_tk_feita_fora_da_thread_da_janela_executa_na_thread_da_janela(self):
        root = self.root
        tk_thread = threading.get_ident()
        cv = tk.Canvas(root, width=100, height=100)
        cv.pack()
        item = cv.create_rectangle(10, 10, 30, 30)
        area = agm.Tela(cv)
        root.tk.createcommand("onde_executa_teste", lambda: threading.get_ident())
        res = {}
        gui = agm.AdvakGUIModern()
        gui._root = root

        def registrar():
            res["thread_do_tratador"] = threading.get_ident()
            res["thread_do_comando_tcl"] = int(root.tk.call("onde_executa_teste"))

        fn = funcao_dk("""funcao tratador(e) {
    registrar()
    area.mover(item, 5, 7)
    terminar()
}""", "tratador", registrar=registrar, area=area, item=item,
                       terminar=lambda: root.after(0, root.quit))
        self.rodar_ate_terminar(lambda: gui._chamar(fn, {"tecla": "a"}))
        self.assertFalse(self.estourou, "o tratador não terminou")
        self.assertNotEqual(res["thread_do_tratador"], tk_thread)
        self.assertEqual(res["thread_do_comando_tcl"], tk_thread)
        self.assertEqual(cv.coords(item), [15.0, 17.0, 35.0, 37.0])
        cv.destroy()

    def test_parar_de_dentro_do_tratador_encerra_o_mainloop(self):
        root = self.root
        fim = []
        gui = agm.AdvakGUIModern()
        gui._root = root
        fn = funcao_dk("funcao tratador(e) { sair() }", "tratador",
                       sair=lambda: (fim.append(True), root.after(0, root.quit)))
        self.rodar_ate_terminar(lambda: gui._chamar(fn, None))
        self.assertEqual(fim, [True])
        self.assertFalse(self.estourou)


class TesteTratadorLento(_BaseTk):
    """Um tratador lento não trava a janela, e os eventos seguintes esperam na fila, na ordem."""

    def test_janela_responde_enquanto_o_tratador_lento_roda_e_os_eventos_esperam(self):
        root = self.root
        ordem = []
        liberar = threading.Event()
        self.addCleanup(liberar.set)
        gui = agm.AdvakGUIModern()
        gui._root = root

        def esperar_liberar():
            liberar.wait(8)

        def rapido(n):
            ordem.append(f"rapido {int(n)}")
            if int(n) == 3:
                root.after(0, root.quit)

        lento = funcao_dk("""funcao lento(e) {
    anotar("lento entrou")
    esperar_liberar()
    anotar("lento saiu")
}""", "lento", anotar=ordem.append, esperar_liberar=esperar_liberar)
        veloz = funcao_dk("funcao veloz(e) { rapido(e) }", "veloz", rapido=rapido)

        def inicio():
            gui._chamar(lento, 1)
            gui._chamar(veloz, 2)
            gui._chamar(veloz, 3)

            def janela_respondeu():
                ordem.append("a janela respondeu")      # só a thread da janela executa isto...
                liberar.set()                           # ...e só então o tratador lento é solto
            root.after(100, janela_respondeu)

        self.rodar_ate_terminar(inicio)
        self.assertFalse(self.estourou, "a fila não terminou")
        self.assertEqual(ordem, ["lento entrou", "a janela respondeu", "lento saiu", "rapido 2", "rapido 3"])


class TesteJanelaFechada(_BaseTk):
    def test_tratador_que_chama_o_tk_depois_de_a_janela_fechar_nao_gera_erro_na_tela(self):
        """Depois do destroy, uma chamada ao Tk de outra thread levanta RuntimeError ('main thread is not in main
        loop'). Isso é a janela já ter fechado, não um erro do programa: não pode aparecer como ❌."""
        gui = agm.AdvakGUIModern()
        raiz = tk.Tk()
        raiz.withdraw()
        gui._root = raiz
        fn = funcao_dk("funcao tratador(e) { mexer() }", "tratador", mexer=lambda: raiz.tk.call("expr", "1"))
        raiz.destroy()
        with capturar_stderr() as buf:
            gui._chamar(fn, None)
            self.assertTrue(gui._esperar_tratadores(5.0))
        self.assertNotIn("❌", buf.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
