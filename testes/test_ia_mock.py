"""
Testes SIMULADOS (mock) do módulo advak_ia: nenhuma rede, nenhum crédito gasto.
A função de rede (advak_ia._abrir_url) é trocada por respostas falsas.

Rodar:  python -I testes/test_ia_mock.py
Testes reais (com chave no .env) estão em testes/ia_real.dk.
"""
import io
import json
import os
import socket
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import advak_ia as ia   # noqa: E402

CHAVE_FALSA = "sk-TESTE-1234567890abcdef"


class Base(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        for k in list(os.environ):
            if k.startswith("ADVAK_") and (k.endswith("_API_KEY") or k.endswith("_MODELO") or k == "ADVAK_OLLAMA_URL"):
                del os.environ[k]
        self._carregar = ia._carregar_env
        ia._carregar_env = lambda: None
        self._abrir = ia._abrir_url
        self.chamadas = []
        self.respostas = []                  # fila: dict (JSON) ou exceção
        ia._abrir_url = self._falso

    def tearDown(self):
        ia._abrir_url = self._abrir
        ia._carregar_env = self._carregar
        os.environ.clear()
        os.environ.update(self._env)
        ia._PERSONALIZADOS.clear()

    def _falso(self, url, dados, cabecalhos, timeout):
        self.chamadas.append((url, json.loads(dados.decode()), dict(cabecalhos), timeout))
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return json.dumps(r).encode()

    @staticmethod
    def openai_ok(texto):
        return {"choices": [{"message": {"content": texto}}]}

    @staticmethod
    def http_erro(codigo, corpo=""):
        return urllib.error.HTTPError("http://x", codigo, "erro", {}, io.BytesIO(corpo.encode()))


class TesteRequisicoes(unittest.TestCase):
    MSGS = [{"papel": "usuario", "texto": "Oi", "imagens": [{"mime": "image/png", "b64": "AAAA"}]}]

    def test_anthropic(self):
        url, corpo, cab = ia.montar_requisicao(ia.PROVEDORES["anthropic"], "modelo-x", "CHAVE", self.MSGS, "seja breve", 100, 0.2)
        self.assertEqual(url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(cab["x-api-key"], "CHAVE")
        self.assertEqual(cab["anthropic-version"], "2023-06-01")
        self.assertEqual(corpo["system"], "seja breve")
        self.assertEqual(corpo["messages"][0]["content"][0],
                         {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAAA"}})
        self.assertEqual(corpo["messages"][0]["content"][1], {"type": "text", "text": "Oi"})
        self.assertEqual((corpo["max_tokens"], corpo["temperature"]), (100, 0.2))

    def test_openai_e_compativeis(self):
        url, corpo, cab = ia.montar_requisicao(ia.PROVEDORES["openai"], "m", "CHAVE", [{"papel": "usuario", "texto": "Oi"}], "sis", 50)
        self.assertEqual(cab["Authorization"], "Bearer CHAVE")
        self.assertEqual(corpo["messages"], [{"role": "system", "content": "sis"}, {"role": "user", "content": "Oi"}])
        self.assertIn("max_completion_tokens", corpo)
        _, corpo2, _ = ia.montar_requisicao(ia.PROVEDORES["groq"], "m", "CHAVE", self.MSGS, None, 50)
        self.assertIn("max_tokens", corpo2)
        self.assertEqual(corpo2["messages"][0]["content"][1]["image_url"]["url"], "data:image/png;base64,AAAA")

    def test_gemini_chave_no_cabecalho_e_nao_na_url(self):
        url, corpo, cab = ia.montar_requisicao(ia.PROVEDORES["gemini"], "gemini-x", "CHAVE", self.MSGS, "sis", 10)
        self.assertTrue(url.endswith("/models/gemini-x:generateContent"))
        self.assertNotIn("CHAVE", url)
        self.assertEqual(cab["x-goog-api-key"], "CHAVE")
        self.assertEqual(corpo["systemInstruction"], {"parts": [{"text": "sis"}]})
        self.assertEqual(corpo["contents"][0]["parts"][1], {"inline_data": {"mime_type": "image/png", "data": "AAAA"}})

    def test_ollama_sem_chave(self):
        url, corpo, cab = ia.montar_requisicao(ia.PROVEDORES["ollama"], "llama3.2", "", [{"papel": "assistente", "texto": "x"}], "sis")
        self.assertEqual(url, "http://localhost:11434/api/chat")
        self.assertFalse(corpo["stream"])
        self.assertEqual(corpo["messages"][1]["role"], "assistant")
        self.assertNotIn("Authorization", cab)

    def test_extrair_texto(self):
        P = ia.PROVEDORES
        self.assertEqual(ia.extrair_texto(P["anthropic"], {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}), "ab")
        self.assertEqual(ia.extrair_texto(P["openai"], {"choices": [{"message": {"content": "oi"}}]}), "oi")
        self.assertEqual(ia.extrair_texto(P["gemini"], {"candidates": [{"content": {"parts": [{"text": "x"}]}}]}), "x")
        self.assertEqual(ia.extrair_texto(P["ollama"], {"message": {"content": "o"}}), "o")
        with self.assertRaises(ia.ErroIA) as e:
            ia.extrair_texto(P["gemini"], {"promptFeedback": {"blockReason": "SAFETY"}})
        self.assertEqual(e.exception.tipo, "bloqueado")
        with self.assertRaises(ia.ErroIA) as e:
            ia.extrair_texto(P["openai"], {"inesperado": 1})
        self.assertEqual(e.exception.tipo, "formato")


class TesteChaves(Base):
    def test_chave_ausente_explica_o_env_sem_vazar_nada(self):
        c = ia.conectar("anthropic")
        with self.assertRaises(ia.ErroIA) as e:
            c.perguntar("oi")
        msg = str(e.exception)
        self.assertIn("ADVAK_ANTHROPIC_API_KEY", msg)
        self.assertIn(".env", msg)
        self.assertEqual(e.exception.tipo, "chave_ausente")
        self.assertEqual(self.chamadas, [])            # nem tentou a rede

    def test_chave_vem_so_do_ambiente_e_vai_no_cabecalho(self):
        os.environ["ADVAK_OPENAI_API_KEY"] = CHAVE_FALSA
        self.respostas = [self.openai_ok("Olá!")]
        self.assertEqual(ia.conectar("openai").perguntar("oi"), "Olá!")
        self.assertEqual(self.chamadas[0][2]["Authorization"], "Bearer " + CHAVE_FALSA)

    def test_repr_info_e_tabela_nao_mostram_a_chave(self):
        os.environ["ADVAK_OPENAI_API_KEY"] = CHAVE_FALSA
        c = ia.conectar(["openai", "ollama"])
        tudo = repr(c) + repr(c._provedores) + json.dumps(c.info()) + ia.tabela_provedores() + json.dumps(ia.listar_provedores())
        self.assertNotIn(CHAVE_FALSA, tudo)
        self.assertIn("configurada", json.dumps(c.info()))

    def test_erro_http_que_ecoa_a_chave_e_mascarado(self):
        os.environ["ADVAK_OPENAI_API_KEY"] = CHAVE_FALSA
        self.respostas = [self.http_erro(400, f'{{"erro": "chave invalida {CHAVE_FALSA} Authorization: Bearer {CHAVE_FALSA}"}}')]
        with self.assertRaises(ia.ErroIA) as e:
            ia.conectar("openai").perguntar("oi")
        self.assertNotIn(CHAVE_FALSA, str(e.exception))
        self.assertNotIn("1234567890abcdef", str(e.exception))

    def test_mascarar_padroes_comuns(self):
        for segredo in ("sk-abcdefghijkl1234", "gsk_abcdefghijkl1234", "AIzaSyA-abcdefghijklmnop12345",
                        "Bearer abcdefgh12345678", "x-api-key: abcdefgh12345678", 'api_key="abcdefgh12345678"'):
            self.assertNotIn(segredo.split()[-1].strip('"'), ia.mascarar(f"falha {segredo} fim"))

    def test_codigo_nunca_aceita_chave_por_parametro(self):
        c = ia.conectar("openai", modelo="gpt-x")
        self.assertEqual(c._provedores[0].modelo, "gpt-x")
        for nome in ("chave", "api_key", "token"):
            with self.assertRaises(ia.ErroIA) as e:
                ia.conectar("openai", **{nome: "sk-abc"})    # não existe parâmetro de chave
            self.assertIn(".env", str(e.exception))
            self.assertNotIn("sk-abc", str(e.exception))


class TesteErros(Base):
    def setUp(self):
        super().setUp()
        os.environ["ADVAK_GROQ_API_KEY"] = CHAVE_FALSA

    def erro(self, resposta, nome="groq"):
        self.respostas = [resposta]
        with self.assertRaises(ia.ErroIA) as e:
            ia.conectar(nome).perguntar("oi")
        return e.exception

    def test_401_chave_invalida(self):
        e = self.erro(self.http_erro(401))
        self.assertEqual(e.tipo, "chave")
        self.assertIn("ADVAK_GROQ_API_KEY", str(e))

    def test_429_limite_de_uso(self):
        e = self.erro(self.http_erro(429))
        self.assertEqual(e.tipo, "limite")
        self.assertIn("limite de uso", str(e))

    def test_404_modelo(self):
        self.assertEqual(self.erro(self.http_erro(404)).tipo, "modelo")

    def test_500_servidor(self):
        self.assertEqual(self.erro(self.http_erro(503)).tipo, "servidor")

    def test_sem_internet(self):
        e = self.erro(urllib.error.URLError(socket.gaierror("sem dns")))
        self.assertEqual(e.tipo, "rede")
        self.assertIn("internet", str(e))
        self.assertIn("Ollama", str(e))

    def test_tempo_esgotado(self):
        self.assertEqual(self.erro(socket.timeout()).tipo, "tempo")

    def test_ollama_desligado(self):
        e = self.erro(urllib.error.URLError(ConnectionRefusedError()), "ollama")
        self.assertIn("ollama serve", str(e))
        self.assertIn("ollama pull llama3.2", str(e))

    def test_resposta_que_nao_e_json(self):
        ia._abrir_url = lambda *a: b"<html>"
        self.assertEqual(self.erro(None).tipo, "formato") if False else None
        with self.assertRaises(ia.ErroIA) as e:
            ia.conectar("groq").perguntar("oi")
        self.assertEqual(e.exception.tipo, "formato")

    def test_provedor_desconhecido(self):
        with self.assertRaises(ia.ErroIA) as e:
            ia.conectar("fantasia")
        self.assertIn("advak ia", str(e.exception))


class TesteReservaEOpcoes(Base):
    def test_reserva_quando_o_primeiro_falha(self):
        os.environ["ADVAK_GROQ_API_KEY"] = CHAVE_FALSA          # anthropic fica sem chave
        self.respostas = [self.openai_ok("resposta do groq")]
        c = ia.conectar(["anthropic", "groq"])
        self.assertEqual(c.perguntar("oi"), "resposta do groq")
        self.assertEqual(c.ultimo_provedor, "groq")
        self.assertIn("groq.com", self.chamadas[0][0])

    def test_reserva_em_limite_e_sem_rede(self):
        os.environ.update({"ADVAK_OPENAI_API_KEY": CHAVE_FALSA, "ADVAK_GROQ_API_KEY": CHAVE_FALSA})
        self.respostas = [self.http_erro(429), urllib.error.URLError("x"), {"message": {"content": "ollama ok"}}]
        c = ia.conectar(["openai", "groq", "ollama"])
        self.assertEqual(c.perguntar("oi"), "ollama ok")
        self.assertEqual(c.ultimo_provedor, "ollama")

    def test_todos_falham_lista_cada_motivo(self):
        os.environ["ADVAK_GROQ_API_KEY"] = CHAVE_FALSA
        self.respostas = [self.http_erro(429)]
        with self.assertRaises(ia.ErroIA) as e:
            ia.conectar(["anthropic", "groq"]).perguntar("oi")
        msg = str(e.exception)
        self.assertIn("anthropic", msg)
        self.assertIn("groq", msg)
        self.assertNotIn(CHAVE_FALSA, msg)

    def test_escolher_por_nome(self):
        os.environ.update({"ADVAK_OPENAI_API_KEY": CHAVE_FALSA, "ADVAK_GROQ_API_KEY": CHAVE_FALSA})
        self.respostas = [self.openai_ok("do groq")]
        c = ia.conectar(["openai", "groq"])
        self.assertEqual(c.perguntar("oi", {"provedor": "groq"}), "do groq")
        self.assertIn("groq.com", self.chamadas[0][0])
        with self.assertRaises(ia.ErroIA):
            c.perguntar("oi", {"provedor": "mistral"})

    def test_sistema_modelo_e_apelidos(self):
        os.environ["ADVAK_ANTHROPIC_API_KEY"] = CHAVE_FALSA
        self.respostas = [{"content": [{"type": "text", "text": "ok"}]}]
        c = ia.conectar("claude", modelo="claude-x", sistema="padrão")
        c.perguntar("oi", {"sistema": "só nesta pergunta"})
        _, corpo, cab, _ = self.chamadas[0]
        self.assertEqual((corpo["model"], corpo["system"]), ("claude-x", "só nesta pergunta"))
        self.assertEqual(cab["x-api-key"], CHAVE_FALSA)

    def test_modelo_pelo_env(self):
        os.environ["ADVAK_OLLAMA_MODELO"] = "qwen2.5"
        os.environ["ADVAK_OLLAMA_URL"] = "http://servidor:11434"
        self.respostas = [{"message": {"content": "ok"}}]
        ia.conectar("ollama").perguntar("oi")
        self.assertEqual(self.chamadas[0][0], "http://servidor:11434/api/chat")
        self.assertEqual(self.chamadas[0][1]["model"], "qwen2.5")

    def test_registrar_provedor_proprio(self):
        ia.registrar("escola", {"url": "http://srv:1234/v1/chat/completions", "modelo": "qwen", "chave": False})
        self.respostas = [self.openai_ok("da escola")]
        self.assertEqual(ia.conectar("escola").perguntar("oi"), "da escola")
        self.assertEqual(self.chamadas[0][0], "http://srv:1234/v1/chat/completions")
        with self.assertRaises(ia.ErroIA):
            ia.registrar("sem_url", {})

    def test_conversar_guarda_historico_e_desfaz_se_falhar(self):
        os.environ["ADVAK_GROQ_API_KEY"] = CHAVE_FALSA
        self.respostas = [self.openai_ok("r1"), self.openai_ok("r2")]
        c = ia.conectar("groq")
        self.assertEqual(c.conversar("p1"), "r1")
        self.assertEqual(c.conversar("p2"), "r2")
        enviado = self.chamadas[1][1]["messages"]
        self.assertEqual([m["content"] for m in enviado], ["p1", "r1", "p2"])
        self.respostas = [self.http_erro(500)]
        with self.assertRaises(ia.ErroIA):
            c.conversar("p3")
        self.assertEqual(len(c.historico()), 4)                  # p3 não ficou no histórico
        c.limpar()
        self.assertEqual(c.historico(), [])

    def test_conversar_com_lista_explicita_nao_usa_memoria(self):
        os.environ["ADVAK_GROQ_API_KEY"] = CHAVE_FALSA
        self.respostas = [self.openai_ok("ok")]
        c = ia.conectar("groq")
        c.conversar([{"papel": "usuario", "texto": "a"}, {"papel": "assistente", "texto": "b"}, {"role": "user", "content": "c"}])
        self.assertEqual([m["role"] for m in self.chamadas[0][1]["messages"]], ["user", "assistant", "user"])
        self.assertEqual(c.historico(), [])

    def test_anexos_sem_modulo_de_documentos(self):
        os.environ["ADVAK_GROQ_API_KEY"] = CHAVE_FALSA
        sys.modules["advak_documentos"] = None            # simula módulo ausente
        try:
            with self.assertRaises(ia.ErroIA) as e:
                ia.conectar("groq").perguntar("resuma", {"anexos": ["a.pdf"]})
            self.assertIn("documentos", str(e.exception))
        finally:
            sys.modules.pop("advak_documentos", None)


BOM = "```dk\nseja total = 0\npara (seja i = 1; i <= 3; i++) {\n    total = total + i\n}\nimprimir(\"Total:\", total)\n```"
RUIM = "```dk\nse (x > {\n```"


class TesteGerarCodigo(Base):
    def setUp(self):
        super().setUp()
        os.environ["ADVAK_GROQ_API_KEY"] = CHAVE_FALSA
        self.dir = tempfile.mkdtemp()
        self.alvo = os.path.join(self.dir, "medias.dk")
        self.client = ia.conectar("groq")

    def gerar(self, respostas, resp_sn, arquivo=True):
        self.respostas = [self.openai_ok(r) for r in respostas]
        perguntas = []

        def confirmar(p):
            perguntas.append(p)
            return resp_sn.pop(0)
        buf = io.StringIO()
        with redirect_stdout(buf):
            codigo = self.client.gerar_codigo("somar números", self.alvo if arquivo else None, {"confirmar_fn": confirmar})
        return codigo, buf.getvalue(), perguntas

    def test_fixtures_sao_validas_e_invalidas(self):
        self.assertIsNone(ia.validar_sintaxe(ia.extrair_codigo(BOM)))
        self.assertIsNotNone(ia.validar_sintaxe(ia.extrair_codigo(RUIM)))

    def test_mostra_valida_pergunta_e_salva_so_com_sim(self):
        codigo, saida, perguntas = self.gerar([BOM], ["s"])
        self.assertIn("imprimir(\"Total:\", total)", saida)           # mostrou o código
        self.assertIn("Sintaxe válida", saida)
        self.assertIn("NÃO foi executado", saida)
        self.assertEqual(len(perguntas), 1)
        self.assertTrue(os.path.exists(self.alvo))
        with open(self.alvo, encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), codigo.strip())
        self.assertNotIn("Total: 6", saida)                          # nada foi executado

    def test_resposta_nao_nao_salva(self):
        _, saida, _ = self.gerar([BOM], ["n"])
        self.assertFalse(os.path.exists(self.alvo))
        self.assertIn("não salvo", saida)

    def test_sem_terminal_e_sem_funcao_de_confirmacao_nao_salva(self):
        self.respostas = [self.openai_ok(BOM)]
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.client.gerar_codigo("x", self.alvo)                  # stdin dos testes não é terminal
        self.assertFalse(os.path.exists(self.alvo))

    def test_arquivo_existente_pede_segunda_confirmacao(self):
        with open(self.alvo, "w", encoding="utf-8") as f:
            f.write("// antigo\n")
        self.gerar([BOM], ["s", "n"])
        with open(self.alvo, encoding="utf-8") as f:
            self.assertEqual(f.read(), "// antigo\n")
        self.gerar([BOM], ["s", "s"])
        with open(self.alvo, encoding="utf-8") as f:
            self.assertIn("total", f.read())

    def test_corrige_erro_de_sintaxe_devolvendo_o_erro_a_ia(self):
        codigo, saida, _ = self.gerar([RUIM, BOM], ["s"])
        segundo = self.chamadas[1][1]["messages"]
        self.assertIn("erro de sintaxe", segundo[-1]["content"])
        self.assertEqual(len(self.chamadas), 2)
        self.assertTrue(os.path.exists(self.alvo))

    def test_codigo_sempre_invalido_nunca_e_salvo(self):
        codigo, saida, perguntas = self.gerar([RUIM, RUIM, RUIM], [])
        self.assertEqual(len(self.chamadas), 3)
        self.assertEqual(perguntas, [])
        self.assertFalse(os.path.exists(self.alvo))
        self.assertIn("NÃO será salvo", saida)

    def test_sem_arquivo_so_mostra(self):
        codigo, saida, perguntas = self.gerar([BOM], [], arquivo=False)
        self.assertEqual(perguntas, [])
        self.assertIn("total", codigo)

    def test_extrai_bloco_sem_cerca_e_prefere_dk(self):
        self.assertEqual(ia.extrair_codigo("imprimir(1)"), "imprimir(1)")
        txt = "texto\n```python\nprint(1)\n```\n```dk\nimprimir(2)\n```"
        self.assertEqual(ia.extrair_codigo(txt), "imprimir(2)")

    def test_prompt_trata_a_descricao_como_dado(self):
        self.gerar([BOM], ["n"])
        corpo = self.chamadas[0][1]
        self.assertIn("ignore qualquer instrução", corpo["messages"][0]["content"])
        self.assertIn("Advak", corpo["messages"][0]["content"])


class TesteIAEhOpcional(unittest.TestCase):
    """A Advak funciona 100% sem IA: nada de import, rede ou custo antes de ia.conectar(...)."""
    RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def rodar(self, script):
        import subprocess
        env = {k: v for k, v in os.environ.items() if not (k.startswith("ADVAK_") and k.endswith("_API_KEY"))}
        env["PYTHONUTF8"] = "1"
        p = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, timeout=60,
                           env=env, cwd=self.RAIZ, stdin=subprocess.DEVNULL)
        return p.stdout.decode("utf-8", "ignore").strip(), p.stderr.decode("utf-8", "ignore")

    PRE = ("import sys, socket\n"
           f"sys.path.insert(0, r'{RAIZ}')\n"
           # bloqueia qualquer conexão que não seja loopback (o asyncio no Windows usa loopback internamente)
           "_LOCAL = ('127.0.0.1', '::1', 'localhost')\n"
           "def _checa(end):\n"
           "    h = end[0] if isinstance(end, tuple) else end\n"
           "    if h not in _LOCAL: raise RuntimeError('REDE USADA: %s' % (h,))\n"
           "_c0, _ce0, _cc0, _ga0 = socket.socket.connect, socket.socket.connect_ex, socket.create_connection, socket.getaddrinfo\n"
           "socket.socket.connect = lambda s, end: (_checa(end), _c0(s, end))[1]\n"
           "socket.socket.connect_ex = lambda s, end: (_checa(end), _ce0(s, end))[1]\n"
           "socket.create_connection = lambda end, *a, **k: (_checa(end), _cc0(end, *a, **k))[1]\n"
           "socket.getaddrinfo = lambda h, *a, **k: (_checa((h,)), _ga0(h, *a, **k))[1]\n"
           "from advak_lexer import AdvakLexer\nfrom advak_parser import Parser\n"
           "from advak_interpreter import AdvakInterpreter\n")

    def test_criar_o_interpretador_nao_importa_advak_ia_nem_usa_rede(self):
        saida, erro = self.rodar(self.PRE + "ast = Parser(AdvakLexer('seja x = 1').tokenize()).parse()\n"
                                 "i = AdvakInterpreter(ast)\n"
                                 "print('advak_ia' in sys.modules, 'ia' in i.global_scope.vars)\n")
        self.assertEqual(saida, "False True", erro)

    def test_executar_programa_comum_nao_carrega_a_ia(self):
        saida, erro = self.rodar(
            self.PRE + "import asyncio\n"
            "ast = Parser(AdvakLexer('seja a = 2 + 3\\nimprimir(a)').tokenize()).parse()\n"
            "i = AdvakInterpreter(ast)\nasyncio.run(i.interpret())\n"
            "print('IA-CARREGADA' if 'advak_ia' in sys.modules else 'sem-ia')\n")
        self.assertTrue(saida.endswith("sem-ia"), saida + erro)

    def test_so_ia_conectar_carrega_o_modulo(self):
        saida, erro = self.rodar(
            self.PRE + "import asyncio\n"
            "ast = Parser(AdvakLexer('seja assistente = ia.conectar(\"ollama\")\\nimprimir(assistente.provedores())').tokenize()).parse()\n"
            "i = AdvakInterpreter(ast)\nasyncio.run(i.interpret())\n"
            "print('IA-CARREGADA' if 'advak_ia' in sys.modules else 'sem-ia')\n")
        self.assertIn("ollama", saida, erro)
        self.assertTrue(saida.endswith("IA-CARREGADA"), saida + erro)

    def test_chave_ausente_no_dk_vira_erro_em_portugues_sem_rede(self):
        saida, erro = self.rodar(
            self.PRE + "import asyncio\n"
            "src = 'seja assistente = ia.conectar(\"openai\")\\ntentar { assistente.perguntar(\"oi\") } pegar (e) { imprimir(\"ERRO:\", e) }'\n"
            "i = AdvakInterpreter(Parser(AdvakLexer(src).tokenize()).parse())\nasyncio.run(i.interpret())\n")
        self.assertIn("ADVAK_OPENAI_API_KEY", saida, erro)
        self.assertNotIn("REDE USADA", saida + erro)


class TesteSeguranca(unittest.TestCase):
    def test_modulo_nunca_executa_codigo(self):
        caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "advak_ia.py")
        with open(caminho, encoding="utf-8") as f:
            fonte = f.read()
        for proibido in ("exec(", "eval(", "subprocess", "os.system", "os.popen", "Interpreter", "runpy"):
            self.assertNotIn(proibido, fonte, proibido)


if __name__ == "__main__":
    unittest.main(verbosity=2)
