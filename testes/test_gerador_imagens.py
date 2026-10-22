"""Gerador das imagens do jogo 2D (docs/curso/ferramentas/gerar_imagens.py).

Confere: (1) a saída é a mesma a cada execução (no mesmo processo, em processos separados, com cwd e
PYTHONHASHSEED diferentes); (2) os arquivos em docs/curso/codigos/imagens/ têm os mesmos PIXELS que o gerador
produz (decodificados aqui; quem reprova é este teste). Se os pixels forem iguais mas os bytes diferirem (provável:
outra versão do zlib), o teste imprime um AVISO e passa; o `--conferir` do gerador continua comparando bytes; (3) o Tk lê cada PNG com o tamanho esperado; (4) um PNG
cortado (os 40 primeiros bytes do herói, criado numa pasta temporária) é recusado pelo Tk; (5) o tamanho total fica abaixo de um limite.

Rodar:  python -I testes/test_gerador_imagens.py
"""
import hashlib, importlib.util, os, struct, subprocess, sys, tempfile, unittest, zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GERADOR = os.path.join(RAIZ, "docs", "curso", "ferramentas", "gerar_imagens.py")
PASTA = os.path.join(RAIZ, "docs", "curso", "codigos", "imagens")

TAMANHOS = {"fundo.png": (480, 320), "heroi.png": (32, 32), "moeda1.png": (16, 16), "moeda2.png": (16, 16),
            "moeda3.png": (16, 16), "moeda4.png": (16, 16), "parede.png": (32, 32)}
COM_TRANSPARENCIA = ("heroi.png", "moeda1.png", "moeda2.png", "moeda3.png", "moeda4.png")   # canto (0, 0) transparente
LIMITE_TOTAL = 16 * 1024                    # bytes de todos os arquivos (medido no protótipo: ~3,5 KB)


def carregar():
    espec = importlib.util.spec_from_file_location("gerar_imagens", GERADOR)
    m = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(m)
    return m


def decodificar(dados):
    """(largura, altura, bytes dos pixels) de um PNG RGBA de 8 bits sem filtro; confere assinatura e CRC."""
    assert dados[:8] == b"\x89PNG\r\n\x1a\n", "assinatura"
    i, idat, ihdr = 8, b"", None
    while i < len(dados):
        n, tipo = struct.unpack(">I4s", dados[i:i + 8])
        corpo = dados[i + 8:i + 8 + n]
        assert struct.unpack(">I", dados[i + 8 + n:i + 12 + n])[0] == zlib.crc32(tipo + corpo), f"CRC de {tipo}"
        if tipo == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", corpo)
        elif tipo == b"IDAT":
            idat += corpo
        i += 12 + n
    l, a, prof, cor, _, _, _ = ihdr
    assert (prof, cor) == (8, 6), "esperado RGBA de 8 bits"
    bruto = zlib.decompress(idat)
    linha = 1 + 4 * l
    assert len(bruto) == linha * a and all(bruto[y * linha] == 0 for y in range(a)), "sem filtro"
    return l, a, b"".join(bruto[y * linha + 1:(y + 1) * linha] for y in range(a))


def sha_em_processo(cwd, semente):
    codigo = ("import importlib.util as u, hashlib; e = u.spec_from_file_location('g', %r); m = u.module_from_spec(e); "
              "e.loader.exec_module(m); print(hashlib.sha256(b''.join(m.gerar()[n] for n in m.gerar())).hexdigest())" % GERADOR)
    r = subprocess.run([sys.executable, "-I", "-c", codigo], cwd=cwd, capture_output=True, text=True, timeout=120,
                       env=dict(os.environ, PYTHONHASHSEED=str(semente)))
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


class TesteDeterminismo(unittest.TestCase):
    def test_duas_geracoes_no_mesmo_processo_sao_iguais(self):
        g = carregar()
        self.assertEqual(g.gerar(), g.gerar())

    def test_processos_separados_dao_o_mesmo_sha256(self):
        with tempfile.TemporaryDirectory() as outra:
            shas = {sha_em_processo(RAIZ, 0), sha_em_processo(outra, 1), sha_em_processo(outra, 12345)}
        self.assertEqual(len(shas), 1, shas)

    def test_ordem_e_nomes_fixos(self):
        self.assertEqual(list(carregar().gerar()), ["fundo.png", "heroi.png", "moeda1.png", "moeda2.png", "moeda3.png",
                                                    "moeda4.png", "parede.png"])

    def test_conferir_nao_escreve_e_aceita_a_pasta_atual(self):
        def estado():
            return {n: open(os.path.join(PASTA, n), "rb").read() for n in sorted(os.listdir(PASTA))}
        antes = estado()
        r = subprocess.run([sys.executable, "-I", GERADOR, "--conferir"], cwd=tempfile.gettempdir(),
                           capture_output=True, text=True, timeout=120)
        # `--conferir` compara BYTES: 0 se iguais aos do gerador, 1 se diferirem (ex.: outro zlib). Não escreve nada.
        esperado = 0 if estado() == carregar().gerar() else 1
        self.assertEqual(r.returncode, esperado, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(estado(), antes)


class TesteArquivosGerados(unittest.TestCase):
    def test_pasta_tem_exatamente_os_arquivos_do_gerador(self):
        self.assertEqual(sorted(os.listdir(PASTA)), sorted(carregar().gerar()))

    def test_pixels_iguais_aos_do_gerador(self):
        """Reprova se os pixels diferirem. Bytes diferentes com pixels iguais: AVISO visível, e passa."""
        bytes_diferentes = []
        for nome, dados in carregar().gerar().items():
            with open(os.path.join(PASTA, nome), "rb") as f:
                no_disco = f.read()
            self.assertEqual(decodificar(no_disco), decodificar(dados), nome)
            if no_disco != dados:
                bytes_diferentes.append(nome)
        if bytes_diferentes:
            print("\n  AVISO: pixels iguais, mas os bytes diferem do que este gerador produz agora (%s). Provável causa: "
                  "outra versão do zlib. Rode `gerar_imagens.py --conferir` para ver; os arquivos versionados são a "
                  "fonte da verdade." % ", ".join(bytes_diferentes), file=sys.stderr, flush=True)

    def test_tamanho_total(self):
        total = sum(os.path.getsize(os.path.join(PASTA, n)) for n in os.listdir(PASTA))
        self.assertLess(total, LIMITE_TOTAL, total)
        print(f"\n  total: {total} bytes em {len(os.listdir(PASTA))} arquivos", file=sys.stderr)


class TesteLeituraPeloTk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import tkinter
        cls.tk = tkinter
        cls.raiz = tkinter.Tk()
        cls.raiz.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.raiz.destroy()

    def imagem(self, nome):
        return self.tk.PhotoImage(master=self.raiz, file=os.path.join(PASTA, nome))

    def test_tamanho_em_pixels_de_cada_png(self):
        for nome, (l, a) in TAMANHOS.items():
            im = self.imagem(nome)
            self.assertEqual((im.width(), im.height()), (l, a), nome)

    def test_cantos_transparentes_so_onde_deve(self):
        for nome in TAMANHOS:
            self.assertEqual(self.imagem(nome).transparency_get(0, 0), nome in COM_TRANSPARENCIA, nome)

    def test_png_cortado_e_recusado(self):
        """Os 40 primeiros bytes do herói (o que o exemplo de arquivo corrompido da aula vai usar)."""
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "quebrado.png")
            with open(caminho, "wb") as f:
                f.write(carregar().gerar()["heroi.png"][:40])
            with self.assertRaises(self.tk.TclError):
                self.tk.PhotoImage(master=self.raiz, file=caminho)


if __name__ == "__main__":
    unittest.main(verbosity=2)
