"""
gui.ao_tecla, gui.ao_soltar_tecla, gui.tecla_apertada, area.ao_clicar e area.ao_soltar: o que o tratador recebe,
como chega e como o estado das teclas apertadas se comporta.

Sem esperas por tempo: o que roda em outra thread é aguardado pela fila do despachante (_esperar_tratadores); o
único relógio é um limite de segurança. As classes marcadas com Tk usam uma janela de verdade, mas transparente e
fora da tela (uma janela escondida com withdraw() não recebe evento nenhum, medido), fechada pelo próprio teste.

Cobre: o estado por keycode (testes 1 a 7 e 13), a perda de foco com soltura sintética (8 a 12, com root falso; as
threads em 12 só provam ausência de travamento e de exceção, não de corrida), a mensagem de erro de um nome
desconhecido num programa .dk de verdade (14a e 14b) e dois testes com Tk real (15 e 16, com event_generate).

Não coberto: teclas físicas (o event_generate não é o teclado; a repetição da tecla segurada, o nome da tecla com
Shift e a perda de foco real do Windows foram medidos à mão pelo autor, uma vez, nesta máquina, Windows 10, em um
registro local, não publicado), Shift mais dígito (nenhum teste aperta um dígito com Shift), Linux e janela secundária
(o event_generate de tecla vai sempre para a janela com foco).

Rodar:  python -I testes/test_gui_teclado.py
"""
import os
import subprocess
import sys
import tempfile
import threading
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


# ── Etapa 6: gui.tecla_apertada e gui.ao_soltar_tecla ───────────────────────────────────────────────────────────
# Medido só no Windows 10, uma vez, nesta máquina (registro local, não publicado). Os eventos abaixo
# reproduzem o que a medição viu: keycode 65 para a letra, 16 para os dois Shift, 17 para os dois Ctrl, o KeyRelease do
# Shift direito como Shift_L, KeyRelease com keysym "??" (keycodes 44 e 185). As classes sem Tk chamam os tratadores
# internos com eventos falsos; só TesteTeclasComTkReal usa uma janela de verdade.

VEZES = 20      # repetições dentro do teste nos testes de foco e de thread (sem espera fixa)


def evento_k(keysym, keycode, char="", widget=None):
    """Evento de tecla COM keycode (o evento() de cima não tem). O `char` existe só para provar que é ignorado."""
    return types.SimpleNamespace(keysym=keysym, keycode=keycode, char=char, widget=widget)


EVENTO_FOCO = types.SimpleNamespace(widget=None)      # o código novo não olha o evento de foco


class RootFalso:
    """O pouco do Tk que o código novo usa. after_idle roda na hora, para o teste ser determinístico."""

    def __init__(self):
        self.foco = object()          # o que focus_displayof() devolve; None = a aplicação perdeu o foco
        self.erros = []               # o que foi para report_callback_exception
        self.ligacoes = []

    def bind_all(self, sequencia, tratador, add=None):
        self.ligacoes.append(sequencia)

    def bind(self, sequencia, tratador, add=None):
        self.ligacoes.append(sequencia)

    def after_idle(self, fn):
        fn()

    def focus_displayof(self):
        return self.foco

    def report_callback_exception(self, tipo, valor, tb):
        self.erros.append(valor)


def gui_falso():
    gui = agm.AdvakGUIModern()
    gui._root = RootFalso()
    return gui, gui._root


LISTA_NOMES = ["a", "z", "0", "9", "espaco", "enter", "esc", "esquerda", "direita", "cima", "baixo"]


@unittest.skipIf(tk is None, "tkinter não instalado")        # ao_soltar_tecla chama _check()
class TesteEstadoDasTeclas(unittest.TestCase):
    """Testes 1 a 7 e 13: o estado por keycode, sem Tk, com eventos falsos."""

    def setUp(self):
        self.gui, self.root = gui_falso()
        self.soltas = []
        self.gui.ao_soltar_tecla(self.soltas.append)      # função Python: o _chamar roda na hora, na thread do teste

    def aperta(self, keysym, keycode, char=""):
        self.gui._tecla_apertou(evento_k(keysym, keycode, char))

    def solta(self, keysym, keycode, char=""):
        self.gui._tecla_soltou(evento_k(keysym, keycode, char))

    def test_01_aperto_marca_a_soltura_desmarca_e_avisa_com_caractere_vazio(self):
        nomes = [("a", "a"), ("Z", "z"), ("1", "1"), ("space", "espaco"), ("Return", "enter"), ("Escape", "esc"),
                 ("Left", "esquerda"), ("Right", "direita"), ("Up", "cima"), ("Down", "baixo")]
        for i, (keysym, nome) in enumerate(nomes):
            with self.subTest(keysym=keysym):
                self.assertFalse(self.gui.tecla_apertada(nome))
                self.aperta(keysym, 100 + i, char="x")
                self.assertTrue(self.gui.tecla_apertada(nome))
                self.solta(keysym, 100 + i, char="x")
                self.assertFalse(self.gui.tecla_apertada(nome))
        self.assertEqual(self.soltas, [{"tecla": nome, "caractere": ""} for _, nome in nomes])
        # o mesmo formato por um tratador .dk de verdade, que chega pela fila do despachante
        fn, visto = gravador()
        self.gui.ao_soltar_tecla(fn)
        self.aperta("a", 65)
        self.solta("a", 65)
        self.assertTrue(self.gui._esperar_tratadores(5.0), "os tratadores não terminaram")
        self.assertEqual(visto, [{"tecla": "a", "caractere": ""}])

    def test_02_repeticao_da_tecla_segurada_nao_muda_nada(self):
        for _ in range(50):
            self.aperta("z", 90)
        self.assertTrue(self.gui.tecla_apertada("z"))
        self.assertEqual(self.soltas, [])
        self.solta("z", 90)
        self.assertFalse(self.gui.tecla_apertada("z"))
        self.solta("z", 90)                                        # uma segunda soltura não avisa de novo
        self.assertEqual(self.soltas, [{"tecla": "z", "caractere": ""}])

    def test_03_shift_primeiro_depois_a_com_caps_ligado(self):
        """Reproduz o tipo de troca de keysym observada na 6a (o keysym muda com Shift/Caps Lock; o keycode é o mesmo):
        Shift primeiro, aperto "a" (keycode 65); a soltura chega como "A" depois de soltar o Shift."""
        self.aperta("Shift_L", 16)
        self.aperta("a", 65, char="a")
        self.solta("Shift_L", 16)
        self.assertTrue(self.gui.tecla_apertada("a"))
        self.solta("A", 65, char="A")
        self.assertFalse(self.gui.tecla_apertada("a"))
        self.assertEqual(self.soltas, [{"tecla": "a", "caractere": ""}])

    def test_04_letra_primeiro_depois_shift(self):
        """Reproduz o tipo de troca de keysym observada na 6a (o keysym muda com Shift/Caps Lock; o keycode é o mesmo):
        letra primeiro (aperto "A" com o Caps ligado), Shift depois, soltura como "a" com o Shift segurado."""
        self.aperta("A", 65, char="A")
        self.aperta("Shift_L", 16)
        self.assertTrue(self.gui.tecla_apertada("a"))
        self.solta("a", 65, char="a")
        self.solta("Shift_L", 16)
        self.assertFalse(self.gui.tecla_apertada("a"))
        self.assertEqual(self.soltas, [{"tecla": "a", "caractere": ""}])

    def test_05_shift_control_tab_e_f1_a_f12_nao_fazem_nada_nem_dao_erro(self):
        teclas = [("Shift_L", 16), ("Shift_R", 16), ("Control_L", 17), ("Control_R", 17), ("Tab", 9)] + \
                 [(f"F{n}", 111 + n) for n in range(1, 13)]
        for keysym, keycode in teclas:
            with self.subTest(keysym=keysym):
                self.aperta(keysym, keycode)
                self.assertEqual(self.gui._apertadas, {})
                # o Shift direito solta como Shift_L (medido): também não pode fazer nada
                self.solta("Shift_L" if keysym == "Shift_R" else keysym, keycode)
        self.assertEqual(self.soltas, [])
        self.assertFalse(any(self.gui.tecla_apertada(n) for n in LISTA_NOMES))

    def test_06_soltura_de_keycode_desconhecido_e_ignorada(self):
        self.solta("??", 44)              # medido: keycode 44, keysym "??"
        self.solta("??", 185)             # medido: keycode 185, keysym "??"
        self.assertEqual(self.soltas, [])
        self.assertEqual(self.gui._apertadas, {})

    def test_07_nome_fora_da_lista_levanta_erro_em_portugues_com_os_nomes(self):
        with self.assertRaises(AdvakError) as c:
            self.gui.tecla_apertada("xyz")
        msg = str(c.exception)
        self.assertIn("Tecla desconhecida: 'xyz'", msg)
        self.assertIn("a a z, 0 a 9, espaco, enter, esc, esquerda, direita, cima, baixo", msg)

    def test_13_entradas_invalidas_levantam_advak_error_e_nao_value_error(self):
        for invalido in (5, None, True, "", "A", "shift", "control", "tab", "f1", "F1", "xyz", ["a"]):
            with self.subTest(invalido=invalido):
                with self.assertRaises(AdvakError) as c:
                    self.gui.tecla_apertada(invalido)
                self.assertNotIsInstance(c.exception, ValueError)
                self.assertIn("Tecla desconhecida", str(c.exception))


@unittest.skipIf(tk is None, "tkinter não instalado")
class TesteFocoSemTk(unittest.TestCase):
    """Testes 8 a 12: perda de foco, soltura sintética e threads. Root falso; os de 9 a 12 repetem VEZES vezes."""

    def novo(self):
        gui, root = gui_falso()
        return gui, root

    def test_08_focus_out_entre_campos_nao_limpa(self):
        gui, root = self.novo()
        soltas = []
        gui.ao_soltar_tecla(soltas.append)
        gui._tecla_apertou(evento_k("z", 90))
        gui._foco_mudou(EVENTO_FOCO)                  # FocusOut entre dois campos: focus_displayof() continua não-None
        self.assertTrue(gui.tecla_apertada("z"))
        self.assertEqual(soltas, [])

    def test_09_perda_real_limpa_e_avisa_na_ordem_do_aperto(self):
        for _ in range(VEZES):
            gui, root = self.novo()
            avisos, estados = [], []

            def cb(e, gui=gui):
                avisos.append(e)
                estados.append((gui.tecla_apertada("z"), gui.tecla_apertada("a")))

            gui.ao_soltar_tecla(cb)
            gui._tecla_apertou(evento_k("z", 90))
            gui._tecla_apertou(evento_k("a", 65))
            root.foco = None
            gui._foco_mudou(EVENTO_FOCO)
            self.assertEqual(avisos, [{"tecla": "z", "caractere": ""}, {"tecla": "a", "caractere": ""}])
            self.assertEqual(estados, [(False, False), (False, False)])    # o estado já estava vazio nos callbacks
            self.assertEqual(gui._apertadas, {})

    def test_10_duas_perdas_curtas_e_volta_sem_soltura_em_dobro(self):
        for _ in range(VEZES):
            gui, root = self.novo()
            soltas = []
            gui.ao_soltar_tecla(soltas.append)
            z = evento_k("z", 90)
            gui._tecla_apertou(z)
            root.foco = None
            gui._foco_mudou(EVENTO_FOCO)
            gui._foco_mudou(EVENTO_FOCO)               # dois FocusOut na mesma perda: uma soltura só
            self.assertEqual(len(soltas), 1)
            root.foco = object()
            gui._foco_mudou(EVENTO_FOCO)               # FocusIn: a aplicação voltou
            self.assertFalse(gui.tecla_apertada("z"))
            gui._tecla_apertou(z)                      # o Windows volta a repetir o Z: é um aperto novo
            self.assertTrue(gui.tecla_apertada("z"))
            root.foco = None
            gui._foco_mudou(EVENTO_FOCO)
            self.assertEqual(len(soltas), 2)
            root.foco = object()
            gui._foco_mudou(EVENTO_FOCO)
            gui._tecla_soltou(z)                       # a soltura que chega depois: o keycode já é desconhecido
            self.assertEqual(len(soltas), 2)

    def test_11_erro_num_callback_nao_impede_os_outros(self):
        for _ in range(VEZES):
            gui, root = self.novo()
            chamadas = []

            def cb(e, gui=gui):
                chamadas.append((e["tecla"], gui.tecla_apertada(e["tecla"])))
                if e["tecla"] == "z":
                    raise RuntimeError("erro do tratador")

            gui.ao_soltar_tecla(cb)
            gui._tecla_apertou(evento_k("z", 90))
            gui._tecla_apertou(evento_k("a", 65))
            root.foco = None
            gui._foco_mudou(EVENTO_FOCO)
            self.assertEqual(chamadas, [("z", False), ("a", False)])      # o "a" foi avisado mesmo com o "z" falhando
            self.assertEqual([str(x) for x in root.erros], ["erro do tratador"])
            self.assertEqual(gui._apertadas, {})

    def test_12_threads_leem_enquanto_o_tk_aperta_solta_e_limpa(self):
        for _ in range(VEZES):
            gui, root = self.novo()
            chamadas, erros, nao_bool = [], [], []
            parar = threading.Event()
            # o callback chama tecla_apertada: se rodasse dentro da trava (que não é reentrante), isto travaria
            gui.ao_soltar_tecla(lambda e: chamadas.append(gui.tecla_apertada(e["tecla"])))

            def ler():
                try:
                    while not parar.is_set():
                        for nome in ("a", "z", "1"):
                            v = gui.tecla_apertada(nome)
                            if not isinstance(v, bool):
                                nao_bool.append(v)
                except Exception as e:                                  # pragma: no cover
                    erros.append(e)

            leitores = [threading.Thread(target=ler, daemon=True) for _ in range(3)]
            for t in leitores:
                t.start()
            try:
                for _i in range(200):
                    for ks, code in (("a", 65), ("z", 90), ("1", 49)):
                        gui._tecla_apertou(evento_k(ks, code))
                    gui._tecla_soltou(evento_k("a", 65))                 # soltura real
                    root.foco = None
                    gui._foco_mudou(EVENTO_FOCO)                         # soltura sintética do "z" e do "1"
                    root.foco = object()
            finally:
                parar.set()
                for t in leitores:
                    t.join(10)
            self.assertFalse(any(t.is_alive() for t in leitores), "um leitor travou")
            self.assertEqual(erros, [])
            self.assertEqual(nao_bool, [])
            self.assertEqual(len(chamadas), 200 * 3)
            self.assertFalse(any(chamadas))                              # em todo callback a tecla já estava solta


class TesteProgramaDkReal(unittest.TestCase):
    """Teste 14: um programa .dk de verdade chamando gui.tecla_apertada("xyz"), por `python -I advak.py`.

    Roda numa pasta temporária (cwd e programa): não lê nem grava .db nem env_config.env, e não altera arquivos rastreados
    do repositório (só pode atualizar __pycache__, que o git ignora).

    PREVISÃO, escrita ANTES de medir (2026-11-13), por leitura do código (advak.py:205-225, advak_erros.py:197-253,
    advak_interpreter.py:4891-4898 e 5200-5202), não medida:
      (a) no topo do programa a saída tem "ERRO DE EXECUÇÃO" e "Problema:" seguido da mensagem INTEIRA (113 caracteres),
          e NÃO tem "ERRO INESPERADO" nem "ValueError";
      (b) dentro de tentar/pegar, o programa imprime "PEGOU:" seguido da mesma mensagem inteira.
    """
    RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MENSAGEM = ("Tecla desconhecida: 'xyz'. Use um destes nomes: a a z, 0 a 9, espaco, enter, esc, esquerda, direita, "
                "cima, baixo.")

    def rodar(self, fonte):
        env = {k: v for k, v in os.environ.items() if k != "ADVAK_DEBUG"}
        env["PYTHONUTF8"] = "1"
        with tempfile.TemporaryDirectory() as pasta:
            arq = os.path.join(pasta, "prog.dk")
            with open(arq, "w", encoding="utf-8", newline="\n") as f:
                f.write(fonte)
            r = subprocess.run([sys.executable, "-I", os.path.join(self.RAIZ, "advak.py"), arq], cwd=pasta, timeout=60,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
                               stdin=subprocess.DEVNULL)
        return r.stdout + r.stderr

    def test_14a_no_topo_do_programa_e_erro_de_execucao_com_a_mensagem_inteira(self):
        saida = self.rodar('gui.tecla_apertada("xyz")\n')
        self.assertEqual(len(self.MENSAGEM), 113)
        self.assertIn("ERRO DE EXECUÇÃO", saida, saida)
        self.assertIn("Problema:", saida, saida)
        self.assertIn(self.MENSAGEM, saida, saida)
        self.assertNotIn("ERRO INESPERADO", saida, saida)
        self.assertNotIn("ValueError", saida, saida)

    def test_14b_dentro_de_tentar_pegar_a_mensagem_chega_inteira(self):
        saida = self.rodar('tentar {\n    gui.tecla_apertada("xyz")\n} pegar (e) {\n    imprimir("PEGOU:", e)\n}\n')
        self.assertIn("PEGOU: " + self.MENSAGEM, saida, saida)


@unittest.skipIf(tk is None, "tkinter não instalado")
class TesteTeclasComTkReal(_BaseTk):
    """Testes 15 e 16: janela de verdade, transparente e fora da tela (_BaseTk), destruída no fim de cada teste."""

    def test_15_ligar_teclado_com_root_destruido_nao_levanta_e_desfaz_a_bandeira(self):
        self.root.destroy()
        self.gui._ligar_teclado()                     # bind_all num root destruído levanta TclError por dentro
        self.assertFalse(self.gui._teclado_ligado)

    def test_16_integracao_os_bindings_ligam_o_estado_a_soltura_e_a_destruicao(self):
        fn, visto = gravador()
        self.gui._ligar_teclado()
        self.gui._ligar_teclado()                     # idempotente
        self.gui.ao_soltar_tecla(fn)
        # Shift não faz nada
        self.gerar(self.root, "<KeyPress>", keysym="Shift_L", keycode=16)
        self.assertEqual(self.gui._apertadas, {})
        # aperta o "a" (keycode 65), com repetição; um estado só
        for _ in range(3):
            self.gerar(self.root, "<KeyPress>", keysym="a", keycode=65)
        self.assertTrue(self.gui.tecla_apertada("a"))
        self.assertEqual(self.gui._apertadas, {65: "a"})
        # solta como "A" (keysym diferente, mesmo keycode)
        self.gerar(self.root, "<KeyRelease>", keysym="A", keycode=65)
        self.assertFalse(self.gui.tecla_apertada("a"))
        self.terminar()
        self.assertEqual(visto, [{"tecla": "a", "caractere": ""}])
        # uma tecla apertada quando a janela é destruída: limpa o estado SEM soltura sintética
        self.gerar(self.root, "<KeyPress>", keysym="b", keycode=66)
        self.assertTrue(self.gui.tecla_apertada("b"))
        with capturar_stderr() as erro:
            self.root.destroy()
        self.assertEqual(erro.getvalue(), "", "o tratador de <Destroy> deixou um erro do Tk")
        self.assertEqual(self.gui._apertadas, {})
        self.assertFalse(self.gui._teclado_ligado)
        self.terminar()
        self.assertEqual(len(visto), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
