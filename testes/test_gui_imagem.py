"""quadro.imagem: programas .dk reais (janela que fecha sozinha) e Tk real; o caminho relativo vale pela pasta do programa."""
import gc, os, re, shutil, subprocess, sys, tempfile, threading, unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGENS = os.path.join(RAIZ, "docs", "curso", "codigos", "imagens")
sys.path.insert(0, RAIZ)

CABECA = 'seja jan = gui.janela("Teste", 500, 360)\nseja quadro = gui.canvas(jan, 480, 320, "branco")\n'
RODAPE = '\ngui.apos(300, () => { gui.parar() })\ngui.iniciar()\nimprimir("fechou")\n'
GIF_1X1 = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00'
           b',\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')


def linhas(saida):
    return [l.strip() for l in saida.splitlines() if l.strip()]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.base = cls._tmp.name
        cls.jogo = os.path.join(cls.base, "jogo")
        cls.outra = os.path.join(cls.base, "outra")      # imagens/heroi.png homônimo, de 16×16
        cls.vazia = os.path.join(cls.base, "vazia")      # sem imagens/
        for p in (cls.jogo, cls.outra, cls.vazia):
            os.makedirs(p)
        im = os.path.join(cls.jogo, "imagens")
        os.makedirs(os.path.join(im, "pasta.png"))
        os.makedirs(os.path.join(cls.outra, "imagens"))
        for n in ("heroi.png", "fundo.png", "moeda1.png"):
            shutil.copy(os.path.join(IMAGENS, n), os.path.join(im, n))
        shutil.copy(os.path.join(IMAGENS, "moeda1.png"), os.path.join(cls.outra, "imagens", "heroi.png"))
        shutil.copy(os.path.join(IMAGENS, "heroi.png"), os.path.join(im, "HEROI2.PNG"))
        with open(os.path.join(IMAGENS, "heroi.png"), "rb") as f:
            quebrado = f.read(40)
        for nome, dados in (("quebrado.png", quebrado), ("vazio.png", b""), ("a.jpg", b"x"), ("a.bmp", b"x"),
                            ("a.gif", GIF_1X1), ("um_gif.png", GIF_1X1)):
            with open(os.path.join(im, nome), "wb") as f:
                f.write(dados)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def rodar(self, corpo, cwd=None, comando=("{arq}",), cabeca=CABECA, rodape=RODAPE):
        arq = os.path.join(self.jogo, "prog.dk")
        with open(arq, "w", encoding="utf-8", newline="\n") as f:
            f.write(cabeca + corpo + rodape)
        args = [a.format(arq=arq) for a in comando]
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py")] + args, cwd=cwd or self.vazia,
                           timeout=60, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONUTF8="1"))
        return r.stdout + r.stderr

    def caminho(self, rel):
        return os.path.normpath(os.path.join(self.jogo, rel))


class TesteImagemPrograma(Base):
    def test_1_e_2_numeros_dos_itens_quantidade_e_bbox(self):
        l = linhas(self.rodar('''
seja fundo = quadro.imagem(0, 0, "imagens/fundo.png")
seja heroi = quadro.imagem(100, 50, "imagens/heroi.png")
imprimir(fundo, heroi, quadro.quantidade())
seja b = quadro.widget.bbox(heroi)
imprimir(b[0], b[1], b[2], b[3])'''))
        self.assertEqual(l[0], "1 2 2")
        self.assertEqual(l[1], "100 50 132 82")
        self.assertEqual(l[-1], "fechou")

    def test_3_rodar_de_outra_pasta_resolve_pela_pasta_do_programa(self):
        for cwd in (self.vazia, self.base):
            l = linhas(self.rodar('seja h = quadro.imagem(0, 0, "imagens/heroi.png")\nseja b = quadro.widget.bbox(h)\nimprimir(b[2], b[3])',
                                  cwd=cwd))
            self.assertEqual(l[0], "32 32", cwd)

    def test_4_advak_programa_e_advak_run_dao_o_mesmo(self):
        corpo = 'seja h = quadro.imagem(7, 9, "imagens/heroi.png")\nseja b = quadro.widget.bbox(h)\nimprimir(b[0], b[1], b[2], b[3])'
        a = self.rodar(corpo, comando=("{arq}",))
        b = self.rodar(corpo, comando=("run", "{arq}"))
        self.assertEqual(linhas(a)[0], "7 9 39 41")
        self.assertEqual(linhas(a), linhas(b))

    def test_5_imagem_homonima_do_diretorio_atual_nao_e_lida(self):
        l = linhas(self.rodar('seja h = quadro.imagem(0, 0, "imagens/heroi.png")\nseja b = quadro.widget.bbox(h)\nimprimir(b[2] - b[0], b[3] - b[1])',
                              cwd=self.outra))
        self.assertEqual(l[0], "32 32")             # a de outra/ é 16×16

    def test_6_caminho_absoluto_fica_como_esta(self):
        completo = self.caminho("imagens/moeda1.png").replace("\\", "/")
        l = linhas(self.rodar(f'''
seja a = quadro.imagem(0, 0, Arquivo.do_programa("imagens/moeda1.png"))
seja c = quadro.imagem(0, 0, "{completo}")
seja b = quadro.widget.bbox(a)
seja d = quadro.widget.bbox(c)
imprimir(b[2], b[3], d[2], d[3])''', cwd=self.outra))
        self.assertEqual(l[0], "16 16 16 16")

    def test_8_repl_sem_programa_em_arquivo_resolve_pelo_diretorio_atual(self):
        entrada = "\n".join(['seja jan = gui.janela("t", 300, 200)', 'seja q = gui.canvas(jan, 200, 100, "branco")',
                             'seja h = q.imagem(0, 0, "imagens/heroi.png")', 'imprimir("ITEM", h, q.widget.bbox(h))',
                             'gui.apos(200, () => { gui.parar() })', 'gui.iniciar()', 'imprimir("FIM")']) + "\n"
        r = subprocess.run([sys.executable, "-I", os.path.join(RAIZ, "advak.py")], input=entrada, cwd=self.jogo, timeout=60,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONUTF8="1"))
        self.assertIn("ITEM 1 (0, 0, 32, 32)", r.stdout + r.stderr)
        self.assertIn("FIM", r.stdout)

    def test_9_mover_apagar_e_limpar(self):
        l = linhas(self.rodar('''
seja h = quadro.imagem(10, 10, "imagens/heroi.png")
seja m = quadro.imagem(0, 0, "imagens/moeda1.png")
quadro.mover(h, 5, 7)
seja b = quadro.widget.bbox(h)
imprimir(b[0], b[1])
quadro.apagar(h)
imprimir(quadro.quantidade())
quadro.limpar()
imprimir(quadro.quantidade())'''))
        self.assertEqual(l[:3], ["15 17", "1", "0"])

    def test_10_mesmo_arquivo_duas_vezes_dois_itens_mesma_imagem(self):
        l = linhas(self.rodar('''
seja a = quadro.imagem(0, 0, "imagens/heroi.png")
seja b = quadro.imagem(50, 0, "imagens/heroi.png")
imprimir(a, b, quadro.quantidade(), quadro.widget.itemcget(a, "image") == quadro.widget.itemcget(b, "image"))'''))
        self.assertEqual(l[0], "1 2 2 verdadeiro")

    def test_11_criar_mover_e_apagar_dentro_de_gui_apos(self):
        l = linhas(self.rodar('''
gui.apos(50, () => {
    seja m = quadro.imagem(200, 50, "imagens/moeda1.png")
    quadro.mover(m, 10, 10)
    seja b = quadro.widget.bbox(m)
    imprimir("no tratador", b[0], b[1], b[2], b[3])
    quadro.apagar(m)
    imprimir("depois", quadro.quantidade())
})'''))
        self.assertIn("no tratador 210 60 226 76", l)
        self.assertIn("depois 0", l)
        self.assertEqual(l[-1], "fechou")

    def test_12_erros_de_arquivo_com_o_texto_exato(self):
        s = self.rodar('''
tentar { quadro.imagem(0, 0, "imagens/nao_existe.png") } capturar (e) { imprimir("E1", e) }
tentar { quadro.imagem(0, 0, "imagens/pasta.png") } capturar (e) { imprimir("E2", e) }
tentar { quadro.imagem(0, 0, "imagens/quebrado.png") } capturar (e) { imprimir("E3", e) }
tentar { quadro.imagem(0, 0, "imagens/vazio.png") } capturar (e) { imprimir("E4", e) }
imprimir(quadro.quantidade())''')
        l = linhas(s)
        # o caminho impresso é comparado por realpath + normcase (pasta temporária curta do Windows e caixa do nome)
        m = re.fullmatch(r"E1 Imagem não encontrada: 'imagens/nao_existe\.png' \(procurei em (.+)\)\.", l[0])
        self.assertIsNotNone(m, l[0])
        self.assertEqual(os.path.normcase(os.path.realpath(m.group(1))),
                         os.path.normcase(os.path.realpath(self.caminho("imagens/nao_existe.png"))))
        self.assertEqual(l[1], "E2 'imagens/pasta.png' é uma pasta, não um arquivo de imagem.")
        self.assertEqual(l[2], "E3 Não consegui ler a imagem 'imagens/quebrado.png': o arquivo está corrompido ou não é um PNG válido.")
        self.assertEqual(l[3], "E4 Não consegui ler a imagem 'imagens/vazio.png': o arquivo está corrompido ou não é um PNG válido.")
        self.assertEqual(l[4], "0")                  # nenhum item criado por engano
        self.assertNotIn("Traceback", s)

    def test_13_formatos_recusados_e_png_em_maiuscula_aceito(self):
        s = self.rodar('''
tentar { quadro.imagem(0, 0, "imagens/a.jpg") } capturar (e) { imprimir("E1", e) }
tentar { quadro.imagem(0, 0, "imagens/a.bmp") } capturar (e) { imprimir("E2", e) }
tentar { quadro.imagem(0, 0, "imagens/a.gif") } capturar (e) { imprimir("E3", e) }
seja h = quadro.imagem(0, 0, "imagens/HEROI2.PNG")
imprimir("ok", h, quadro.quantidade())''')
        l = linhas(s)
        for n, ext in ((1, "a.jpg"), (2, "a.bmp"), (3, "a.gif")):
            self.assertEqual(l[n - 1], f"E{n} Formato de imagem não suportado: 'imagens/{ext}'. Só PNG (.png) é aceito.")
        self.assertEqual(l[3], "ok 1 1")

    def test_14_erros_de_tipo(self):
        l = linhas(self.rodar('''
tentar { quadro.imagem(0, 0, 5) } capturar (e) { imprimir("E1", e) }
tentar { quadro.imagem(0, 0, nulo) } capturar (e) { imprimir("E2", e) }
tentar { quadro.imagem("a", 0, "imagens/heroi.png") } capturar (e) { imprimir("E3", e) }
tentar { quadro.imagem(0, nulo, "imagens/heroi.png") } capturar (e) { imprimir("E4", e) }
imprimir(quadro.quantidade())'''))
        self.assertEqual(l[0], "E1 'caminho' deve ser um texto, mas recebeu 5.")
        self.assertEqual(l[1], "E2 'caminho' deve ser um texto, mas recebeu None.")
        self.assertEqual(l[2], "E3 'x' deve ser um número, mas recebeu 'a'.")
        self.assertEqual(l[3], "E4 'y' deve ser um número, mas recebeu None.")
        self.assertEqual(l[4], "0")

    def test_15_gif_1x1_literal_recusado_por_gif_e_lido_com_nome_png(self):
        l = linhas(self.rodar('''
tentar { quadro.imagem(0, 0, "imagens/a.gif") } capturar (e) { imprimir("E1", e) }
seja g = quadro.imagem(0, 0, "imagens/um_gif.png")
seja b = quadro.widget.bbox(g)
imprimir("lido", b[2] - b[0], b[3] - b[1])'''))
        self.assertTrue(l[0].startswith("E1 Formato de imagem não suportado"))
        self.assertEqual(l[1], "lido 1 1")          # limitação conhecida: só o nome é checado


class TesteImagemTkReal(Base):
    def setUp(self):
        import tkinter as tk
        self.tk = tk
        self.cwd = os.getcwd()
        self.root = tk.Tk()
        self.cv = tk.Canvas(self.root, width=100, height=100)
        self.cv.pack()
        import advak_gui_modern as g
        self.tela = g.Tela(self.cv)

    def tearDown(self):
        os.chdir(self.cwd)
        self.root.destroy()

    def test_7_sem_programa_em_arquivo_o_relativo_resolve_pelo_diretorio_atual(self):
        import advak_interpreter as a
        self.assertIsNone(a._ARQUIVO_DO_PROGRAMA)
        os.chdir(self.outra)
        i = self.tela.imagem(0, 0, "imagens/heroi.png")
        b = self.cv.bbox(i)
        self.assertEqual((b[2] - b[0], b[3] - b[1]), (16, 16))

    def test_16_a_imagem_sobrevive_ao_gc_e_sem_referencia_o_tk_a_apaga(self):
        caminho = os.path.join(self.jogo, "imagens", "heroi.png")
        feito = {}

        def na_thread():
            feito["item"] = self.tela.imagem(0, 0, caminho)
        t = threading.Thread(target=na_thread)

        def espera():
            if t.is_alive():
                self.root.after(20, espera)
            else:
                self.root.quit()
        # o Tk só aceita chamada de outra thread com a principal em mainloop(); update() não basta
        self.root.after(0, t.start)
        self.root.after(20, espera)
        self.root.after(5000, self.root.quit)      # limite de segurança: o teste não fica preso
        self.root.mainloop()
        t.join(1)
        self.assertFalse(t.is_alive(), "a thread não terminou em 5 s")
        self.assertIn("item", feito, "a thread não criou o item")
        gc.collect(); self.root.update()
        nome = self.cv.itemcget(feito["item"], "image")
        self.assertIn(nome, self.root.tk.call("image", "names"))
        b = self.cv.bbox(feito["item"])
        self.assertEqual((b[2] - b[0], b[3] - b[1]), (32, 32))
        # contraprova: o mesmo arquivo sem ninguém guardar a referência é apagado pelo Tk
        solto = self.tk.PhotoImage(master=self.root, file=caminho)
        nome_solto = str(solto)
        self.cv.create_image(0, 0, image=solto, anchor="nw")
        del solto
        gc.collect(); self.root.update()
        self.assertNotIn(nome_solto, self.root.tk.call("image", "names"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
