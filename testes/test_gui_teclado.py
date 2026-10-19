"""
gui.ao_tecla, area.ao_clicar e area.ao_soltar: o que o tratador recebe e como chega.

Sem esperas por tempo: o que roda em outra thread é aguardado pela fila do despachante (_esperar_tratadores); o
único relógio é um limite de segurança. As classes marcadas com Tk usam uma janela de verdade, mas transparente e
fora da tela (uma janela escondida com withdraw() não recebe evento nenhum, medido), fechada pelo próprio teste.

Não coberto: tecla segurada (o Windows repetir ou não a tecla não é medido aqui) e janela secundária (o
event_generate de tecla vai sempre para a janela com foco).

Rodar:  python -I testes/test_gui_teclado.py
"""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import advak_gui_modern as agm                                    # noqa: E402
from advak_interpreter import AdvakError                          # noqa: E402
from test_gui_eventos import FONTE_COM_ERRO, capturar_stderr, funcao_dk   # noqa: E402

try:
    import tkinter as tk
except ImportError:                                               # pragma: no cover
    tk = None


def gravador(nome="t"):
    """Um tratador .dk que anota (tecla, caractere) ou (x, y) numa lista; devolve (função, lista)."""
    visto = []
    fn = funcao_dk(f"funcao {nome}(e) {{ anotar(e) }}", nome, anotar=visto.append)
    return fn, visto


def evento(keysym="a", char="a", x=0, y=0):
    return types.SimpleNamespace(keysym=keysym, char=char, x=x, y=y)


class TesteSemTk(unittest.TestCase):
    def test_dados_da_tecla_com_os_valores_medidos_no_tk(self):
        # (keysym, char) como o Tk entregou; esperado: (tecla, caractere)
        casos = [("a", "a", "a", "a"), ("A", "A", "A", "A"), ("space", " ", "espaco", " "),
                 ("Left", "", "esquerda", ""), ("Right", "", "direita", ""), ("Up", "", "cima", ""),
                 ("Down", "", "baixo", ""), ("Return", "\r", "enter", "\r"), ("Escape", "", "esc", ""),
                 ("F1", "", "F1", ""), ("ccedilla", "ç", "ccedilla", "ç"), ("1", "1", "1", "1")]
        for keysym, char, tecla, caractere in casos:
            with self.subTest(keysym=keysym):
                self.assertEqual(agm.AdvakGUIModern._dados_tecla(evento(keysym, char)),
                                 {"tecla": tecla, "caractere": caractere})

    def test_o_evento_de_tecla_nao_leva_x_nem_y(self):
        self.assertEqual(set(agm.AdvakGUIModern._dados_tecla(evento(x=5, y=6))), {"tecla", "caractere"})

    def test_ponto_do_mouse_usa_a_coordenada_do_desenho(self):
        class CanvasRolado:                       # com rolagem: o desenho começa 98 à direita e 198 abaixo
            def canvasx(self, v): return v + 98.0
            def canvasy(self, v): return v + 198.0
        ponto = agm.Tela(CanvasRolado())._ponto(evento(x=10, y=10))
        self.assertEqual(ponto, {"x": 108, "y": 208})
        self.assertIsInstance(ponto["x"], int)

    def test_tela_sem_gui_da_erro_em_portugues(self):
        class CanvasFalso:
            pass
        fn, _ = gravador()
        for metodo in ("ao_clicar", "ao_soltar"):
            with self.subTest(metodo=metodo):
                with self.assertRaises(AdvakError) as c:
                    getattr(agm.Tela(CanvasFalso()), metodo)(fn)
                self.assertIn("gui.canvas", str(c.exception))

    @unittest.skipIf(tk is None, "tkinter não instalado")
    def test_ao_tecla_antes_da_janela_da_erro_em_portugues(self):
        fn, _ = gravador()
        with self.assertRaises(AdvakError) as c:
            agm.AdvakGUIModern().ao_tecla(fn)
        self.assertIn("gui.janela", str(c.exception))

    def test_o_interpretador_expoe_gui_ao_tecla(self):
        fn = funcao_dk("funcao h(e) { }", "h")
        self.assertIn("ao_tecla", fn.closure.get("gui"))


@unittest.skipIf(tk is None, "tkinter não instalado")
class _BaseTk(unittest.TestCase):
    """Uma janela transparente e fora da tela por teste: recebe os eventos gerados, sem aparecer."""

    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as e:                                  # pragma: no cover
            raise unittest.SkipTest(f"sem tela para o Tk: {e}")
        self.addCleanup(self._fechar)
        self.root.attributes("-alpha", 0.0)
        self.root.geometry("+30000+30000")
        self.root.update()
        self.root.focus_force()                  # evento de tecla vai para a janela com foco; sem foco ele se perde
        self.root.update()
        self.assertIs(self.root.focus_get(), self.root, "a janela não ficou com o foco")
        self.gui = agm.AdvakGUIModern()
        self.gui._root = self.root

    def _fechar(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def gerar(self, widget, sequencia, **kw):
        widget.event_generate(sequencia, **kw)
        self.root.update()

    def terminar(self):
        self.assertTrue(self.gui._esperar_tratadores(5.0), "os tratadores não terminaram")


class TesteTecla(_BaseTk):
    def test_as_teclas_chegam_em_ordem_com_tecla_e_caractere(self):
        fn, visto = gravador()
        self.gui.ao_tecla(fn)
        for ks in ("a", "A", "space", "Left", "Return", "Escape", "F1", "ccedilla"):
            self.gerar(self.root, "<KeyPress>", keysym=ks)
        self.terminar()
        self.assertEqual([(d["tecla"], d["caractere"]) for d in visto],
                         [("a", "a"), ("A", "A"), ("espaco", " "), ("esquerda", ""), ("enter", "\r"),
                          ("esc", ""), ("F1", ""), ("ccedilla", "ç")])

    def test_chamar_de_novo_troca_o_tratador(self):
        antigo, visto_antigo = gravador("antigo")
        novo, visto_novo = gravador("novo")
        self.gui.ao_tecla(antigo)
        self.gui.ao_tecla(novo)
        self.gerar(self.root, "<KeyPress>", keysym="a")
        self.terminar()
        self.assertEqual((len(visto_antigo), len(visto_novo)), (0, 1))

    def test_nao_apaga_outra_tecla_ja_ligada_na_janela(self):
        marcou = []
        self.root.bind("<F11>", lambda e: marcou.append("F11"))      # como o atalho do tema, em janela()
        fn, visto = gravador()
        self.gui.ao_tecla(fn)
        self.gerar(self.root, "<KeyPress>", keysym="F11")
        self.terminar()
        self.assertEqual(marcou, ["F11"])
        self.assertEqual([d["tecla"] for d in visto], ["F11"])

    def test_tecla_digitada_num_campo_com_foco_tambem_chega(self):
        """Caracterização medida: o campo recebe o texto e o tratador da janela também é chamado."""
        campo = tk.Entry(self.root)
        campo.pack()
        self.root.update()
        campo.focus_force()
        self.root.update()
        fn, visto = gravador()
        self.gui.ao_tecla(fn)
        self.gerar(campo, "<KeyPress>", keysym="a")
        self.terminar()
        self.assertEqual(campo.get(), "a")
        self.assertEqual([d["tecla"] for d in visto], ["a"])

    def test_erro_no_tratador_de_tecla_aparece_com_a_origem_e_a_linha(self):
        fn = funcao_dk(FONTE_COM_ERRO, "tratador")
        self.gui.ao_tecla(fn)
        with capturar_stderr() as buf:
            self.gerar(self.root, "<KeyPress>", keysym="a")
            self.terminar()
        self.assertIn("tratador de tecla", buf.getvalue())
        self.assertIn("naoexiste", buf.getvalue())
        self.assertIn("linha 5", buf.getvalue())


class TesteMouseNaTela(_BaseTk):
    def nova_tela(self):
        area = self.gui.canvas(self.root, 200, 120, "branco")
        self.root.update()
        return area

    def test_clique_e_soltar_chegam_com_x_e_y(self):
        area = self.nova_tela()
        fn_clique, cliques = gravador("clicou")
        fn_solta, soltos = gravador("soltou")
        area.ao_clicar(fn_clique)
        area.ao_soltar(fn_solta)
        self.gerar(area.widget, "<ButtonPress-1>", x=7, y=9)
        self.gerar(area.widget, "<ButtonRelease-1>", x=7, y=9)
        self.terminar()
        self.assertEqual(cliques, [{"x": 7, "y": 9}])
        self.assertEqual(soltos, [{"x": 7, "y": 9}])

    def test_outros_botoes_do_mouse_nao_chamam(self):
        area = self.nova_tela()
        fn, visto = gravador()
        area.ao_clicar(fn)
        area.ao_soltar(fn)
        for seq in ("<ButtonPress-2>", "<ButtonPress-3>", "<ButtonRelease-3>"):
            self.gerar(area.widget, seq, x=1, y=1)
        self.terminar()
        self.assertEqual(visto, [])

    def test_trocar_o_tratador_do_clique_substitui_o_anterior(self):
        area = self.nova_tela()
        antigo, visto_antigo = gravador("antigo")
        novo, visto_novo = gravador("novo")
        area.ao_clicar(antigo)
        area.ao_clicar(novo)
        self.gerar(area.widget, "<ButtonPress-1>", x=3, y=4)
        self.terminar()
        self.assertEqual((len(visto_antigo), len(visto_novo)), (0, 1))

    def test_com_rolagem_o_tratador_recebe_a_coordenada_do_desenho(self):
        area = self.nova_tela()
        area.widget.configure(scrollregion=(0, 0, 1000, 1000))
        area.widget.xview_moveto(0.1)
        area.widget.yview_moveto(0.2)
        self.root.update()
        esperado = {"x": int(round(area.widget.canvasx(10))), "y": int(round(area.widget.canvasy(10)))}
        self.assertNotEqual(esperado, {"x": 10, "y": 10}, "a rolagem não deslocou o canvas")
        fn, visto = gravador()
        area.ao_clicar(fn)
        self.gerar(area.widget, "<ButtonPress-1>", x=10, y=10)
        self.terminar()
        self.assertEqual(visto, [esperado])

    def test_ao_clicar_nao_apaga_um_bind_feito_pelo_programa_em_area_widget(self):
        area = self.nova_tela()
        do_programa = []
        area.widget.bind("<ButtonPress-1>", lambda e: do_programa.append((e.x, e.y)))
        fn, visto = gravador()
        area.ao_clicar(fn)
        self.gerar(area.widget, "<ButtonPress-1>", x=5, y=6)
        self.terminar()
        self.assertEqual(do_programa, [(5, 6)])
        self.assertEqual(visto, [{"x": 5, "y": 6}])

    def test_area_widget_continua_o_mesmo_objeto_tk(self):
        area = self.nova_tela()
        self.assertIsInstance(area.widget, tk.Canvas)
        self.assertEqual(area.quantidade(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
