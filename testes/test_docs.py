"""
Testes da documentação: versão, links, âncoras, partes obrigatórias do README e da instalação, e os
exemplos de cada banco de dados em docs/BANCOS_DE_DADOS.md (sintaxe, nomes dos comandos e, no caso do
SQLite, execução de verdade).

Rodar:  python -I testes/test_docs.py
"""
import asyncio
import contextlib
import io
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import advak_conectores as C                       # noqa: E402
from advak_lexer import AdvakLexer                 # noqa: E402
from advak_parser import Parser                    # noqa: E402

# Arquivos que as próximas partes da documentação ainda vão criar (esvaziar quando existirem).
PENDENTES = {"docs/curso/README.md", "docs/GUIA_PRATICO.md"}


def ler(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8") as f:
        return f.read()


def slug(titulo):
    """Âncora do GitHub: minúsculas, sem pontuação (acentos ficam), espaços viram hífen."""
    t = unicodedata.normalize("NFC", titulo.strip().lower())
    t = re.sub(r"[`*_]", "", t)
    t = re.sub(r"[^\w\s\-]", "", t, flags=re.UNICODE)
    return re.sub(r"\s", "-", t)


def ancoras(md):
    saida, vistos = set(), {}
    dentro_codigo = False
    for linha in md.splitlines():
        if linha.startswith("```"):
            dentro_codigo = not dentro_codigo
        if dentro_codigo:
            continue
        m = re.match(r"^(#{1,6})\s+(.*\S)\s*$", linha)
        if m:
            s = slug(m.group(2))
            n = vistos.get(s, 0)
            vistos[s] = n + 1
            saida.add(s if n == 0 else f"{s}-{n}")
    return saida


def links(md):
    sem_codigo = re.sub(r"```.*?```", "", md, flags=re.S)
    sem_codigo = re.sub(r"`[^`\n]*`", "", sem_codigo)
    return re.findall(r"\]\(([^)\s]+)\)", sem_codigo)


ARQUIVOS_MD = ["README.md", "CHANGELOG.md"] + [
    os.path.join("docs", f) for f in sorted(os.listdir(os.path.join(RAIZ, "docs"))) if f.endswith(".md")]


class TesteVersao(unittest.TestCase):
    def test_versao_5_2_0_em_todo_lugar(self):
        self.assertIn('VERSION = "5.2.0"', ler("advak.py"))
        self.assertIn("Versão atual: **5.2.0**", ler("README.md"))
        self.assertIn("## [5.2.0]", ler("CHANGELOG.md"))
        self.assertIn("Advak 5.2.0", ler(os.path.join("docs", "INSTALACAO.md")))

    def test_comando_versao(self):
        p = subprocess.run([sys.executable, "advak.py", "--versao"], cwd=RAIZ, capture_output=True, timeout=60,
                           env=dict(os.environ, PYTHONUTF8="1"))
        self.assertEqual(p.stdout.decode().strip(), "Advak 5.2.0")


class TesteLinks(unittest.TestCase):
    def test_links_relativos_apontam_para_arquivos_que_existem(self):
        faltando = []
        for rel in ARQUIVOS_MD:
            base = os.path.dirname(os.path.join(RAIZ, rel))
            for alvo in links(ler(rel)):
                if re.match(r"^(https?:|mailto:)", alvo):
                    continue
                caminho = alvo.split("#")[0]
                if not caminho:
                    continue
                absoluto = os.path.normpath(os.path.join(base, caminho))
                relativo = os.path.relpath(absoluto, RAIZ).replace("\\", "/")
                if relativo in PENDENTES:
                    continue
                if not os.path.exists(absoluto):
                    faltando.append(f"{rel} -> {alvo}")
        self.assertEqual(faltando, [])

    def test_ancoras_existem(self):
        quebradas = []
        for rel in ARQUIVOS_MD:
            base = os.path.dirname(os.path.join(RAIZ, rel))
            for alvo in links(ler(rel)):
                if re.match(r"^(https?:|mailto:)", alvo) or "#" not in alvo:
                    continue
                caminho, _, ancora = alvo.partition("#")
                arq = os.path.join(RAIZ, rel) if not caminho else os.path.normpath(os.path.join(base, caminho))
                relativo = os.path.relpath(arq, RAIZ).replace("\\", "/")
                if relativo in PENDENTES or not os.path.exists(arq) or not arq.endswith(".md"):
                    continue
                with open(arq, encoding="utf-8") as f:
                    if ancora not in ancoras(f.read()):
                        quebradas.append(f"{rel} -> {alvo}")
        self.assertEqual(quebradas, [])


class TesteReadme(unittest.TestCase):
    def setUp(self):
        self.md = ler("README.md")

    def test_mantem_influencias(self):
        sec = self.md.split("## Influências")[1].split("\n## ")[0]
        for lang in ("Python", "C", "Prolog", "Haskell", "Java"):
            self.assertIn(f"**{lang}**", sec)

    def test_mantem_licenca_mit(self):
        sec = self.md.split("## Licença")[1]
        self.assertIn("**MIT**", sec)
        self.assertIn("(LICENSE)", sec)

    def test_mantem_links_do_postgresql(self):
        for url in ("https://www.enterprisedb.com/downloads/postgres-postgresql-downloads",
                    "https://www.postgresql.org/download/", "https://www.postgresql.org/download/linux/",
                    "https://www.pgadmin.org/download/"):
            self.assertIn(url, self.md)

    def test_destaca_o_curso_no_comeco_e_linka_os_guias(self):
        topo = self.md[:self.md.index("## Influências")]
        self.assertIn("Aprenda a programar com Advak", topo)
        for alvo in ("docs/curso/README.md", "docs/INSTALACAO.md", "docs/GUIA_PRATICO.md",
                     "docs/BANCOS_DE_DADOS.md", "CHANGELOG.md"):
            self.assertIn(alvo, topo)

    def test_lista_os_23_bancos_e_novidades(self):
        for info in C.BANCOS.values():
            self.assertIn(info["nome"].replace("Google ", "").replace("Amazon ", "").replace("IBM ", ""), self.md,
                          info["nome"])
        self.assertEqual(len(C.BANCOS), 23)
        for termo in ("Intervalos", "Compreensão de listas", "Interpolação com formatação", "Tipagem opcional",
                      "23 bancos", "IA (opcional)", "Documentos"):
            self.assertIn(termo, self.md)

    def test_a_ia_e_opcional(self):
        self.assertIn("A IA é opcional", self.md)
        self.assertNotIn("seja ia = ia.conectar", self.md)


class TesteInstalacao(unittest.TestCase):
    def setUp(self):
        self.md = ler(os.path.join("docs", "INSTALACAO.md"))

    def test_links_e_comandos_pedidos(self):
        for texto in (
                "https://www.python.org/downloads/", "Add python.exe to PATH",
                "git clone https://github.com/ArimateiaGomes/advak-language.git", "Download ZIP",
                "INSTALAR.bat", "pip install ttkbootstrap psycopg2-binary pyserial paho-mqtt pyinstaller",
                "https://www.enterprisedb.com/downloads/postgres-postgresql-downloads",
                "https://www.postgresql.org/download/", "https://www.postgresql.org/download/linux/",
                "https://www.pgadmin.org/download/", "5432", "copy .env.exemplo .env",
                "advak --versao", "advak sintaxe_completa.dk", "advak run primeiros_passos.dk --db",
                "chcp 65001", "psycopg2", "PATH"):
            self.assertIn(texto, self.md, texto)

    def test_tem_linux_e_problemas_comuns(self):
        self.assertIn("## 7. Instalação no Linux", self.md)
        problemas = self.md.split("## 8. Problemas comuns")[1]
        for item in ("`python` não é reconhecido", "psycopg2", "Senha do banco errada", "Acentos estranhos",
                     "PATH"):
            self.assertIn(item, problemas, item)

    def test_comandos_do_guia_funcionam_aqui(self):
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, "advak.py", "sintaxe_completa.dk"], cwd=RAIZ, capture_output=True,
                           timeout=120, env=env)
        self.assertIn("TUDO OK!", p.stdout.decode("utf-8", "ignore"))


# ── Exemplos de cada banco em BANCOS_DE_DADOS.md ──────────────────────────────

ROTULOS = ["O que é:", "Quando usar:", "Instalação:", "Driver:", "Conexão (`.env`):", "Exemplo:"]


def secoes_dos_bancos():
    md = ler(os.path.join("docs", "BANCOS_DE_DADOS.md"))
    parte = md.split("# Cada banco")[1].split("## Testar com o seu banco")[0]
    saida = {}
    for bloco in re.split(r"\n(?=### )", parte):
        m = re.match(r"### (.+)", bloco.strip())
        if m:
            saida[m.group(1).strip()] = bloco
    return saida


def construtores(cls):
    """(Consulta, Atualização, Remoção) usados pelo conector."""
    if issubclass(cls, C.ConectorSQL):
        return C.ConsultaSQL, C.AtualizacaoSQL, C.RemocaoSQL
    if issubclass(cls, C.ConectorMongoDB):
        return C.ConsultaMongo, C.AtualizacaoMongo, C.RemocaoMongo
    if issubclass(cls, C.ConectorNeo4j):
        return C.ConsultaGrafo, C.AtualizacaoGrafo, C.RemocaoGrafo
    if issubclass(cls, C.ConectorInfluxDB):
        return C.ConsultaInflux, None, None
    if issubclass(cls, C.ConectorDocumentos):
        return C.ConsultaDoc, C.AtualizacaoDoc, C.RemocaoDoc
    return None, None, None


def nos(arvore):
    if isinstance(arvore, dict):
        yield arvore
        for v in arvore.values():
            yield from nos(v)
    elif isinstance(arvore, list):
        for v in arvore:
            yield from nos(v)


class TesteExemplosDosBancos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.secoes = secoes_dos_bancos()
        cls.por_nome = {info["nome"]: (tipo, info) for tipo, info in C.BANCOS.items()}

    def test_todos_os_23_bancos_tem_secao_completa(self):
        self.assertEqual(sorted(self.secoes), sorted(self.por_nome))
        for nome, texto in self.secoes.items():
            for rotulo in ROTULOS:
                self.assertIn(f"**{rotulo}**", texto, f"{nome}: falta '{rotulo}'")
            self.assertIn("**Testado de verdade?**", texto, nome)
            self.assertRegex(texto, r"\*\*Instalação:\*\*.*https://\S+", nome)

    def test_driver_conexao_e_variavel_do_env_batem_com_o_codigo(self):
        for nome, texto in self.secoes.items():
            tipo, info = self.por_nome[nome]
            pip = re.search(r"\*\*Driver:\*\* (.+)", texto).group(1)
            if tipo != "sqlite":
                self.assertIn(f"pip install {info['pip']}", pip, nome)
            m = re.search(r"`(ADVAK_[A-Z0-9_]+_URL)=([^`]+)`", texto)
            self.assertIsNotNone(m, f"{nome}: sem linha ADVAK_..._URL")
            var, url = m.groups()
            resolvido, params = C.resolver_conexao(url)
            self.assertEqual(resolvido, tipo, f"{nome}: a URL {url} resolve para {resolvido}")
            self.assertIn(var, (f"ADVAK_{tipo.upper()}_URL", "ADVAK_POSTGRESQL_URL", "ADVAK_SQLSERVER_URL"), nome)

    def test_exemplos_tem_sintaxe_valida_e_usam_comandos_que_existem(self):
        for nome, texto in self.secoes.items():
            tipo, info = self.por_nome[nome]
            codigo = re.search(r"```advak\n(.*?)```", texto, flags=re.S).group(1)
            arvore = Parser(AdvakLexer(codigo).tokenize()).parse()
            conector = getattr(C, info["classe"])
            cls_busca, cls_atualiza, cls_remove = construtores(conector)
            variavel, arg = None, None
            for n in nos(arvore):
                if n.get("type") == "var_decl" and isinstance(n.get("value"), dict):
                    v = n["value"]
                    f = v.get("func") or {}
                    if v.get("type") == "call" and f.get("type") == "member" and f["obj"].get("name") == "banco" \
                            and f["prop"] == "conectar":
                        variavel, arg = n["name"], v["args"][0]["value"]
            self.assertIsNotNone(variavel, f"{nome}: o exemplo não chama banco.conectar")
            # a Advak tem que tratar esta chamada como o conector NOVO, e do banco certo
            self.assertTrue(C.eh_conexao_nova((arg,), {}), f"{nome}: banco.conectar({arg!r}) cairia no modo antigo")
            tipo_resolvido, _ = C.resolver_conexao(arg) if "://" in arg else C.resolver_conexao(
                arg, **({"arquivo": ":memory:"} if tipo in ("sqlite", "duckdb") else {}))
            self.assertEqual(tipo_resolvido, tipo, nome)

            def classe_do(no):
                if no.get("type") == "ident" and no.get("name") == variavel:
                    return conector
                if no.get("type") == "call" and (no.get("func") or {}).get("type") == "member":
                    base = classe_do(no["func"]["obj"])
                    prop = no["func"]["prop"]
                    if base is conector:
                        return {"buscar": cls_busca, "atualizar": cls_atualiza, "deletar": cls_remove}.get(prop)
                    if base in (cls_busca, cls_atualiza, cls_remove):
                        return base
                return None

            for n in nos(arvore):
                f = n.get("func") if n.get("type") == "call" else None
                if f and f.get("type") == "member":
                    base = classe_do(f["obj"])
                    if base is not None:
                        self.assertTrue(hasattr(base, f["prop"]),
                                        f"{nome}: {base.__name__} não tem o comando '{f['prop']}'")

    def test_exemplo_do_sqlite_executa_de_verdade(self):
        from advak_interpreter import AdvakInterpreter
        codigo = re.search(r"```advak\n(.*?)```", self.secoes["SQLite"], flags=re.S).group(1)
        antes = os.getcwd()
        env_antes = os.environ.get("ADVAK_SQLITE_URL")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["ADVAK_SQLITE_URL"] = "sqlite:///" + os.path.join(tmp, "loja.db").replace("\\", "/")
            try:
                os.chdir(tmp)
                interp = AdvakInterpreter(Parser(AdvakLexer(codigo).tokenize()).parse())
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    asyncio.run(interp.interpret())
            finally:
                os.chdir(antes)
                if env_antes is None:
                    os.environ.pop("ADVAK_SQLITE_URL", None)
                else:
                    os.environ["ADVAK_SQLITE_URL"] = env_antes
        self.assertEqual(buf.getvalue().strip(), "1 Ana")

    def test_bancos_simulados_nao_dizem_que_foram_testados(self):
        for nome, texto in self.secoes.items():
            testado = texto.split("**Testado de verdade?**")[1]
            tipo, info = self.por_nome[nome]
            if tipo == "sqlite":
                self.assertIn("**Sim.**", testado)
            elif tipo == "duckdb":
                self.assertIn("instável no Windows", testado)
            elif tipo == "postgres":
                self.assertIn("Em parte", testado)
            else:
                self.assertIn("apenas simulado", testado, nome)


if __name__ == "__main__":
    unittest.main(verbosity=2)
