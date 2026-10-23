"""trocar_imagem, colide, para_frente e para_tras: programas .dk reais (janela que fecha sozinha) e Tk real."""
import os, shutil, subprocess, sys, tempfile, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGENS = os.path.join(RAIZ, "docs", "curso", "codigos", "imagens")
sys.path.insert(0, RAIZ)

CABECA = 'seja jan = gui.janela("Teste", 500, 360)\nseja quadro = gui.canvas(jan, 480, 320, "branco")\n'
RODAPE = '\ngui.apos(300, () => { gui.parar() })\ngui.iniciar()\nimprimir("fechou")\n'
NAO_EXISTE = "O item {} não existe nesta tela (já foi apagado ou nunca foi criado)."


def linhas(saida):
    return [l.strip() for l in saida.splitlines() if l.strip()]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.jogo = os.path.join(cls.base_dir(), "jogo")
        im = os.path.join(cls.jogo, "imagens")
        os.makedirs(im)
        for n in ("heroi.png", "moeda1.png"):
            shutil.copy(os.path.join(IMAGENS, n), os.path.join(im, n))
        with open(os.path.join(IMAGENS, "heroi.png"), "rb") as f:
            quebrado = f.read(40)
        for nome, dados in (("quebrado.png", quebrado), ("a.jpg", b"x")):
            with open(os.path.join(im, nome), "wb") as f:
                f.write(dados)

    @classmethod
    def base_dir(cls):
        return cls._tmp.name

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def rodar(self, corpo, cabeca=CABECA, rodape=RODAPE):
        arq = os.path.join(self.jogo, "prog.dk")
        with open(arq, "w", encoding="utf-8", newline="\n") as f:
            f.write(cabeca + corpo + rodape)
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py"), arq], cwd=self.base_dir(), timeout=60,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONUTF8="1"))
        return r.stdout + r.stderr


class TesteTrocarImagem(Base):
    def test_troca_o_desenho_e_mantem_numero_posicao_e_quantidade(self):
        l = linhas(self.rodar('''
seja h = quadro.imagem(100, 50, "imagens/heroi.png")
quadro.mover(h, 5, 5)
quadro.trocar_imagem(h, "imagens/moeda1.png")
seja b = quadro.widget.bbox(h)
imprimir(h, quadro.quantidade(), b[0], b[1], b[2], b[3])'''))
        self.assertEqual(l[0], "1 1 105 55 121 71")        # 16×16 no mesmo canto superior esquerdo, já movido
        self.assertEqual(l[-1], "fechou")

    def test_varias_trocas_seguidas_e_dentro_de_gui_apos(self):
        l = linhas(self.rodar('''
seja h = quadro.imagem(0, 0, "imagens/heroi.png")
gui.apos(50, () => {
    para (i em 0..6) {
        quadro.trocar_imagem(h, "imagens/moeda1.png")
        quadro.trocar_imagem(h, "imagens/heroi.png")
    }
    quadro.trocar_imagem(h, "imagens/moeda1.png")
    seja b = quadro.widget.bbox(h)
    imprimir("tratador", quadro.quantidade(), b[2] - b[0])
})'''))
        self.assertIn("tratador 1 16", l)
        self.assertEqual(l[-1], "fechou")

    def test_reaproveita_o_cache_do_mesmo_arquivo(self):
        l = linhas(self.rodar('''
seja a = quadro.imagem(0, 0, "imagens/heroi.png")
seja b = quadro.imagem(50, 0, "imagens/moeda1.png")
quadro.trocar_imagem(b, "imagens/heroi.png")
imprimir(quadro.widget.itemcget(a, "image") == quadro.widget.itemcget(b, "image"))'''))
        self.assertEqual(l[0], "verdadeiro")

    def test_item_que_nao_e_imagem_usa_o_nome_em_portugues(self):
        l = linhas(self.rodar('''
seja r = quadro.retangulo(0, 0, 10, 10, "azul")
seja c = quadro.circulo(50, 50, 5, "azul")
seja n = quadro.linha(0, 0, 9, 9, "azul")
seja t = quadro.texto(0, 30, "x", "azul")
tentar { quadro.trocar_imagem(r, "imagens/heroi.png") } capturar (e) { imprimir("E1", e) }
tentar { quadro.trocar_imagem(c, "imagens/heroi.png") } capturar (e) { imprimir("E2", e) }
tentar { quadro.trocar_imagem(n, "imagens/heroi.png") } capturar (e) { imprimir("E3", e) }
tentar { quadro.trocar_imagem(t, "imagens/heroi.png") } capturar (e) { imprimir("E4", e) }'''))
        self.assertEqual(l[0], "E1 O item 1 não é uma imagem (é um retângulo).")
        self.assertEqual(l[1], "E2 O item 2 não é uma imagem (é um círculo).")
        self.assertEqual(l[2], "E3 O item 3 não é uma imagem (é uma linha).")
        self.assertEqual(l[3], "E4 O item 4 não é uma imagem (é um texto).")

    def test_item_inexistente_apagado_ou_de_tipo_errado(self):
        l = linhas(self.rodar('''
seja h = quadro.imagem(0, 0, "imagens/heroi.png")
quadro.apagar(h)
tentar { quadro.trocar_imagem(h, "imagens/heroi.png") } capturar (e) { imprimir("E1", e) }
tentar { quadro.trocar_imagem(99, "imagens/heroi.png") } capturar (e) { imprimir("E2", e) }
tentar { quadro.trocar_imagem("a", "imagens/heroi.png") } capturar (e) { imprimir("E3", e) }
tentar { quadro.trocar_imagem(verdadeiro, "imagens/heroi.png") } capturar (e) { imprimir("E4", e) }'''))
        self.assertEqual(l[0], "E1 " + NAO_EXISTE.format(1))
        self.assertEqual(l[1], "E2 " + NAO_EXISTE.format(99))
        self.assertEqual(l[2], "E3 " + NAO_EXISTE.format("'a'"))
        self.assertEqual(l[3], "E4 " + NAO_EXISTE.format("True"))

    def test_erro_de_caminho_deixa_o_item_como_estava(self):
        s = self.rodar('''
seja h = quadro.imagem(10, 10, "imagens/heroi.png")
seja antes = quadro.widget.itemcget(h, "image")
tentar { quadro.trocar_imagem(h, "imagens/nao_existe.png") } capturar (e) { imprimir("E1", e) }
tentar { quadro.trocar_imagem(h, "imagens/a.jpg") } capturar (e) { imprimir("E2", e) }
tentar { quadro.trocar_imagem(h, "imagens/quebrado.png") } capturar (e) { imprimir("E3", e) }
tentar { quadro.trocar_imagem(h, 5) } capturar (e) { imprimir("E4", e) }
seja b = quadro.widget.bbox(h)
imprimir("igual", quadro.widget.itemcget(h, "image") == antes, b[2] - b[0])''')
        l = linhas(s)
        self.assertTrue(l[0].startswith("E1 Imagem não encontrada: 'imagens/nao_existe.png' (procurei em "), l[0])
        self.assertEqual(l[1], "E2 Formato de imagem não suportado: 'imagens/a.jpg'. Só PNG (.png) é aceito.")
        self.assertEqual(l[2], "E3 Não consegui ler a imagem 'imagens/quebrado.png': o arquivo está corrompido ou não é um PNG válido.")
        self.assertEqual(l[3], "E4 'caminho' deve ser um texto, mas recebeu 5.")
        self.assertEqual(l[4], "igual verdadeiro 32")


class TesteTkReal(Base):
    def setUp(self):
        import tkinter as tk
        self.tk = tk
        self.root = tk.Tk()
        self.cv = tk.Canvas(self.root, width=300, height=200)
        self.cv.pack()
        import advak_gui_modern as g
        self.tela = g.Tela(self.cv)
        self.img = os.path.join(self.jogo, "imagens", "heroi.png")      # 32×32
        self.moeda = os.path.join(self.jogo, "imagens", "moeda1.png")    # 16×16

    def tearDown(self):
        self.root.destroy()

    def erro(self, f, *args):
        from advak_interpreter import AdvakError
        with self.assertRaises(AdvakError) as c:
            f(*args)
        return str(c.exception)

    # ── trocar_imagem: tipo fora do mapa ────────────────────────────────────────────────────────────
    def test_tipo_fora_do_mapa_usa_o_nome_do_tk(self):
        p = self.cv.create_polygon(0, 0, 10, 0, 10, 10)
        self.assertEqual(self.erro(self.tela.trocar_imagem, p, self.img),
                         f"O item {p} não é uma imagem (é do tipo 'polygon').")

    # ── colide ──────────────────────────────────────────────────────────────────────────────────────
    def test_colide_retangulos_encostando_nao_colidem(self):
        a = self.tela.retangulo(100, 10, 40, 30, "azul")                  # 100..140
        encostando = self.tela.retangulo(140, 10, 40, 30, "azul")
        sobreposto = self.tela.retangulo(139, 10, 40, 30, "azul")
        longe = self.tela.retangulo(200, 10, 40, 30, "azul")
        self.assertIs(self.tela.colide(a, encostando), False)
        self.assertIs(self.tela.colide(a, sobreposto), True)
        self.assertIs(self.tela.colide(a, longe), False)
        self.assertIs(self.tela.colide(sobreposto, a), True)             # simétrico

    def test_colide_circulos_usam_o_retangulo_que_contem_o_circulo(self):
        a = self.tela.circulo(60, 100, 20, "verde")                      # 40..80
        encostando = self.tela.circulo(100, 100, 20, "verde")           # 80..120
        self.assertIs(self.tela.colide(a, encostando), False)
        # nos cantos do retângulo o desenho não encosta, mas a colisão é por retângulo (limitação aprovada)
        canto = self.tela.circulo(95, 115, 16, "verde")                  # 79..111 em x, 99..131 em y
        self.assertIs(self.tela.colide(a, canto), True)

    def test_colide_imagens(self):
        a = self.tela.imagem(10, 10, self.img)                           # 10..42
        encostando = self.tela.imagem(42, 10, self.img)
        sobreposta = self.tela.imagem(41, 10, self.img)
        dentro = self.tela.imagem(20, 20, self.moeda)
        self.assertIs(self.tela.colide(a, encostando), False)
        self.assertIs(self.tela.colide(a, sobreposta), True)
        self.assertIs(self.tela.colide(a, dentro), True)
        self.assertIs(self.tela.colide(dentro, a), True)

    def test_colide_retangulo_com_imagem_e_depois_de_mover(self):
        i = self.tela.imagem(10, 10, self.img)
        r = self.tela.retangulo(60, 10, 20, 20, "azul")
        self.assertIs(self.tela.colide(i, r), False)
        self.tela.mover(r, -30, 0)                                        # 30..50 em x
        self.assertIs(self.tela.colide(i, r), True)
        self.tela.mover(i, 100, 0)
        self.assertIs(self.tela.colide(i, r), False)

    def test_colide_o_retangulo_da_imagem_inclui_os_pixels_transparentes(self):
        i = self.tela.imagem(10, 10, self.img)
        foto = self.tk.PhotoImage(master=self.root, file=self.img)
        self.assertTrue(foto.transparency_get(0, 0))                     # o canto do herói é transparente
        canto = self.tela.retangulo(10, 10, 2, 2, "azul")                # dentro do canto transparente
        self.assertIs(self.tela.colide(i, canto), True)

    def test_colide_linha_e_texto_usam_o_bbox_do_tk_um_pouco_maior_que_o_desenho(self):
        linha = self.tela.linha(100, 150, 160, 150, "preto")             # bbox medido: y 148..152 (a linha está em y=150)
        r = self.tela.retangulo(100, 151, 20, 20, "azul")                # começa 1 px abaixo da linha
        self.assertIs(self.tela.colide(linha, r), True)
        longe = self.tela.retangulo(100, 160, 20, 20, "azul")
        self.assertIs(self.tela.colide(linha, longe), False)
        texto = self.tela.texto(200, 100, "Olá", "preto")
        no_texto = self.tela.retangulo(205, 105, 5, 5, "azul")
        fora = self.tela.retangulo(260, 105, 5, 5, "azul")
        self.assertIs(self.tela.colide(texto, no_texto), True)
        self.assertIs(self.tela.colide(texto, fora), False)

    def test_colide_item_com_ele_mesmo_e_verdadeiro(self):
        r = self.tela.retangulo(10, 10, 20, 20, "azul")
        self.assertIs(self.tela.colide(r, r), True)

    def test_colide_erros_de_item(self):
        r = self.tela.retangulo(10, 10, 20, 20, "azul")
        self.assertEqual(self.erro(self.tela.colide, r, 99), NAO_EXISTE.format(99))
        self.assertEqual(self.erro(self.tela.colide, 99, r), NAO_EXISTE.format(99))
        self.tela.apagar(r)
        self.assertEqual(self.erro(self.tela.colide, r, r), NAO_EXISTE.format(r))
        self.assertEqual(self.erro(self.tela.colide, "a", 1), NAO_EXISTE.format("'a'"))

    # ── para_frente e para_tras ─────────────────────────────────────────────────────────────────────
    def test_ordem_de_desenho(self):
        a = self.tela.retangulo(0, 0, 5, 5, "azul")
        b = self.tela.retangulo(0, 0, 5, 5, "azul")
        c = self.tela.retangulo(0, 0, 5, 5, "azul")
        self.assertEqual(self.cv.find_all(), (a, b, c))
        self.tela.para_frente(a)
        self.assertEqual(self.cv.find_all(), (b, c, a))
        self.tela.para_tras(c)
        self.assertEqual(self.cv.find_all(), (c, b, a))
        self.tela.para_frente(a)                                           # já está na frente: nada muda
        self.tela.para_tras(c)
        self.assertEqual(self.cv.find_all(), (c, b, a))
        self.assertEqual(self.tela.quantidade(), 3)

    def test_ordem_erros_de_item(self):
        r = self.tela.retangulo(0, 0, 5, 5, "azul")
        self.tela.apagar(r)
        for f in (self.tela.para_frente, self.tela.para_tras):
            self.assertEqual(self.erro(f, r), NAO_EXISTE.format(r))
            self.assertEqual(self.erro(f, 99), NAO_EXISTE.format(99))
            self.assertEqual(self.erro(f, None), NAO_EXISTE.format("None"))


class TesteProgramaOrdemEColide(Base):
    def test_ordem_e_colide_em_um_programa_dentro_de_gui_apos(self):
        l = linhas(self.rodar('''
seja fundo = quadro.retangulo(0, 0, 480, 320, "verde")
seja heroi = quadro.imagem(10, 10, "imagens/heroi.png")
seja moeda = quadro.imagem(30, 10, "imagens/moeda1.png")
imprimir("colide", quadro.colide(heroi, moeda), quadro.colide(fundo, moeda))
gui.apos(50, () => {
    quadro.para_frente(fundo)
    quadro.para_tras(moeda)
    seja ordem = quadro.widget.find_all()
    imprimir("ordem", ordem[0], ordem[1], ordem[2], quadro.quantidade())
})'''))
        self.assertIn("colide verdadeiro verdadeiro", l)
        self.assertIn("ordem 3 2 1 3", l)          # moeda atrás de tudo, fundo na frente
        self.assertEqual(l[-1], "fechou")


if __name__ == "__main__":
    unittest.main(verbosity=2)
