"""gui.canvas: programas .dk reais, com janela que fecha sozinha (gui.apos + gui.parar)."""
import os, subprocess, sys, tempfile, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CABECA = 'seja jan = gui.janela("Teste", 400, 300)\nseja quadro = gui.canvas(jan, 200, 120, "branco")\n'
RODAPE = '\ngui.apos(200, () => { gui.parar() })\ngui.iniciar()\nimprimir("fechou")\n'


def rodar(corpo, cabeca=CABECA, rodape=RODAPE):
    with tempfile.TemporaryDirectory() as pasta:
        arq = os.path.join(pasta, "prog.dk")
        with open(arq, "w", encoding="utf-8") as f:
            f.write(cabeca + corpo + rodape)
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), arq], cwd=RAIZ, timeout=60,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONUTF8="1"))
    return r.stdout + r.stderr


def linhas(saida):
    return [l.strip() for l in saida.splitlines() if l.strip()]


class TesteCanvas(unittest.TestCase):
    def test_cada_desenho_devolve_numero_e_quantidade_conta(self):
        s = rodar('''
imprimir(quadro.quantidade())
seja a = quadro.retangulo(10, 10, 50, 30, "vermelho")
seja b = quadro.circulo(100, 60, 20, "azul", preenchido=falso)
seja c = quadro.linha(0, 0, 200, 120, "verde", espessura=3)
seja d = quadro.texto(5, 90, "Olá", "preto", tamanho=14)
imprimir(a, b, c, d)
imprimir(quadro.quantidade())''')
        l = linhas(s)
        self.assertEqual(l[0], "0")
        self.assertEqual(l[1], "1 2 3 4")
        self.assertEqual(l[2], "4")
        self.assertEqual(l[-1], "fechou")

    def test_mover_apagar_limpar(self):
        s = rodar('''
seja r = quadro.retangulo(10, 10, 20, 20, "roxo")
quadro.mover(r, 5, 7)
seja x = quadro.widget.coords(r)
imprimir(x[0], x[1], x[2], x[3])
seja o = quadro.circulo(50, 50, 5, "cinza")
quadro.apagar(r)
imprimir(quadro.quantidade())
quadro.limpar()
imprimir(quadro.quantidade())''')
        l = linhas(s)
        self.assertEqual(l[0], "15.0 17.0 35.0 37.0")
        self.assertEqual(l[1], "1")
        self.assertEqual(l[2], "0")
        self.assertEqual(l[-1], "fechou")

    def test_cores_em_portugues_e_hexadecimal(self):
        nomes = "preto branco vermelho azul verde amarelo laranja roxo cinza rosa marrom".split()
        corpo = "".join(f'quadro.retangulo(0, 0, 5, 5, "{n}")\n' for n in nomes)
        corpo += 'quadro.retangulo(0, 0, 5, 5, "#ff8800")\nquadro.retangulo(0, 0, 5, 5, "#FF8800")\nimprimir(quadro.quantidade())'
        l = linhas(rodar(corpo))
        self.assertEqual(l[0], str(len(nomes) + 2))
        self.assertEqual(l[-1], "fechou")

    def test_cor_do_fundo_aceita_nome_e_hexadecimal(self):
        s = rodar('imprimir(quadro.widget.cget("bg"))\nseja q2 = gui.canvas(jan, 50, 50, "#102030")\nimprimir(q2.widget.cget("bg"))')
        l = linhas(s)
        self.assertEqual(l[0], "#ffffff")
        self.assertEqual(l[1], "#102030")

    def test_erros_em_portugues_e_capturaveis(self):
        s = rodar('''
tentar { quadro.retangulo(0, 0, 5, 5, "turquesa") } capturar (e) { imprimir("E1", e) }
tentar { quadro.retangulo(0, 0, 5, 5, "#12") } capturar (e) { imprimir("E2", e) }
tentar { quadro.mover(99, 1, 1) } capturar (e) { imprimir("E3", e) }
tentar { quadro.apagar(99) } capturar (e) { imprimir("E4", e) }
tentar { quadro.circulo(10, 10, -3, "azul") } capturar (e) { imprimir("E5", e) }
tentar { quadro.retangulo(0, 0, -1, 5, "azul") } capturar (e) { imprimir("E6", e) }
tentar { quadro.linha(0, 0, 5, 5, "azul", espessura=0) } capturar (e) { imprimir("E7", e) }
tentar { quadro.texto(0, 0, "x", "azul", tamanho=-2) } capturar (e) { imprimir("E8", e) }
tentar { quadro.retangulo("a", 0, 5, 5, "azul") } capturar (e) { imprimir("E9", e) }
tentar { gui.canvas(jan, 0, 10) } capturar (e) { imprimir("E10", e) }
tentar { gui.canvas(jan, 10, 10, "lilas") } capturar (e) { imprimir("E11", e) }
seja r = quadro.retangulo(0, 0, 5, 5, "azul")
quadro.apagar(r)
tentar { quadro.apagar(r) } capturar (e) { imprimir("E12", e) }
imprimir(quadro.quantidade())''')
        for n in range(1, 13):
            self.assertTrue(any(l.startswith(f"E{n} ") for l in linhas(s)), f"E{n} não apareceu:\n{s}")
        self.assertIn("preto, branco, vermelho", s)           # lista os nomes que existem
        self.assertIn("não existe nesta tela", s)
        self.assertNotIn("Traceback", s)
        self.assertEqual(linhas(s)[-2], "0")                  # nada foi desenhado por engano
        self.assertEqual(linhas(s)[-1], "fechou")

    def test_gui_canvas_e_o_svg_global_no_mesmo_programa(self):
        # "tela" é palavra reservada (e a global do SVG): por isso a variável do canvas se chama "area"
        s = rodar('''
seja area = gui.canvas(jan, 80, 60)
area.circulo(10, 10, 5, "azul")
tela.retangulo(1, 2, 30, 40, "#ff0000")
imprimir(area.quantidade(), tela.exportar_svg().contem("<rect"))''', cabeca='seja jan = gui.janela("Teste", 400, 300)' + chr(10))
        l = linhas(s)
        self.assertEqual(l[0], "1 verdadeiro")
        self.assertEqual(l[-1], "fechou")

    def test_canvas_svg_global_continua_como_antes(self):
        s = rodar('''
tela.cor_fundo("#112233")
tela.retangulo(1, 2, 30, 40, "#ff0000")
tela.circulo(50, 50, 10, "#00ff00")
seja svg = tela.exportar_svg()
imprimir(svg.contem("<svg"), svg.contem("<rect"), svg.contem("<circle"))''', cabeca="", rodape='')
        self.assertIn("verdadeiro verdadeiro verdadeiro", s)

    def test_widget_existe_aceita_bind_e_janela_fecha_sozinha_com_canvas_aberto(self):
        s = rodar('''
imprimir(tipo(quadro.widget))
quadro.widget.bind("<Button-1>", (e) => { imprimir("clique", e.x, e.y) })
quadro.widget.event_generate("<Button-1>", x=7, y=9)
gui.apos(50, () => { quadro.widget.event_generate("<Button-1>", x=7, y=9) })''')
        l = linhas(s)
        self.assertEqual(l[0], "objeto")
        self.assertIn("clique 7 9", l)
        self.assertEqual(l[-1], "fechou")


if __name__ == "__main__":
    unittest.main(verbosity=2)
