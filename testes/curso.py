"""
Mantém o curso "Aprenda a programar com Advak" (docs/curso/) honesto: todo código e toda saída mostrados nas aulas
vêm de arquivos de docs/curso/codigos/ EXECUTADOS de verdade.

Nas aulas (.md), três marcadores seguidos de um bloco de código são preenchidos por este script:

    <!--codigo:aula06_exemplo1.dk-->   o texto do arquivo
    <!--saida:aula06_exemplo1.dk-->    a saída real do programa (com as respostas digitadas em aula06_exemplo1.in)
    <!--erro:aula06_erro1.dk-->        a mensagem de erro real (última linha)

Arquivos em docs/curso/codigos/:
    NOME.dk    o programa            NOME.in    respostas digitadas, uma por linha (opcional)
    NOME.http  pedidos HTTP, um por linha ("GET /ola", "POST /x {\"a\": 1}"); o servidor do .dk é ligado e desligado

Uso:
    python testes/curso.py              # confere (código e saída das aulas = o que roda agora) e mostra as diferenças
    python testes/curso.py --extrair    # (ao escrever uma aula) cria os .dk/.in/.http a partir dos blocos do .md
    python testes/curso.py --atualizar  # reescreve os blocos das aulas com o resultado real
    AULA=aula16 python testes/curso.py  # (qualquer modo) só a aula indicada

Ao escrever uma aula, o código vem primeiro dentro do .md: `<!--codigo:NOME.dk-->` + bloco, e as respostas digitadas
em um comentário invisível `<!--entrada:NOME` (uma por linha) `-->` (ou `<!--http:NOME` ... `-->`, ou `<!--repl:NOME` ... `-->` para uma sessão do REPL). `--extrair`
transforma isso em arquivos; depois os arquivos de codigos/ passam a ser a fonte da verdade.
"""
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "testes"))
from rodar_exemplo import executar  # noqa: E402

CURSO = os.path.join(RAIZ, "docs", "curso")
CODIGOS = os.path.join(CURSO, "codigos")
EXT_FONTE = (".dk", ".in", ".http", ".md")
MARCADOR = re.compile(r"(<!--(codigo|saida|erro):([^\s>]+)-->\n```(\w*)\n)(.*?)(```)", re.S)


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def ultima_linha_de_erro(texto):
    """A mensagem de erro que a Advak mostra: as linhas "Localização" e "Problema" da caixa de erro
    (ou, para erros de sintaxe, a última linha da mensagem)."""
    achadas = [l.strip() for l in texto.splitlines() if re.search(r"(Localização|Problema|Tipo|Detalhe):", l) and "ERRO" not in l]
    if achadas:
        return "\n".join(l.replace("📍 ", "").replace("💬 ", "") for l in achadas)
    linhas = [l for l in texto.strip().splitlines() if l.strip()]
    ult = linhas[-1] if linhas else "(sem saída)"
    return re.sub(r"^advak_\w+\.", "", ult)


def rodar_http(nome):
    programa = os.path.join(CODIGOS, nome + ".dk")
    porta = int(re.search(r"iniciar\((\d+)", ler(programa)).group(1))
    p = subprocess.Popen([sys.executable, "-u", os.path.join(RAIZ, "advak.py"), nome + ".dk"], cwd=CODIGOS,
                         env=dict(os.environ, PYTHONUTF8="1", ADVAK_CURSO_TESTE="1"),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    base, saida = f"http://localhost:{porta}", []
    try:
        for _ in range(80):
            try:
                urllib.request.urlopen(base + "/__vivo__", timeout=1)
                break
            except urllib.error.HTTPError:
                break
            except Exception:
                time.sleep(0.25)
        for linha in ler(os.path.join(CODIGOS, nome + ".http")).split("\n"):
            linha = linha.strip()
            if not linha:
                continue
            partes = linha.split(" ", 2)
            metodo, caminho = partes[0], partes[1]
            corpo = partes[2].encode("utf-8") if len(partes) > 2 else None
            req = urllib.request.Request(base + caminho, data=corpo, method=metodo,
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    txt, st = r.read().decode("utf-8"), r.status
            except urllib.error.HTTPError as e:
                txt, st = e.read().decode("utf-8"), e.code
            if txt.lstrip().startswith("<!DOCTYPE"):          # página de erro (404/500): só o título e a mensagem
                titulo = re.search(r"<title>(.*?)</title>", txt, re.S)
                msg = re.search(r"<p[^>]*>(.*?)</p>", txt, re.S)
                limpo = re.sub(r"<[^>]+>", "", msg.group(1)).strip() if msg else ""
                txt = f"[página HTML de erro {titulo.group(1) if titulo else ''}: {limpo}]"
            saida.append(f"{linha}\n  -> {st} {txt}")
    finally:
        p.kill()
        p.wait()
        p.stdout.close()
    return "\n".join(saida) + "\n"


def rodar_um(nome):
    """Devolve a saída real do programa `nome` (sem a extensão)."""
    if os.path.exists(os.path.join(CODIGOS, nome + ".http")):
        return rodar_http(nome)
    if os.path.exists(os.path.join(CODIGOS, nome + ".repl")):         # sessão do REPL digitada por uma pessoa
        linhas = ler(os.path.join(CODIGOS, nome + ".repl")).rstrip("\n").split("\n")
        saida, _ = executar("repl", linhas,
                            cwd=CODIGOS, limite=60, ocioso=1.0)
        return saida[saida.index("advak>>"):] if "advak>>" in saida else saida
    arq_in = os.path.join(CODIGOS, nome + ".in")
    respostas = ler(arq_in).split("\n") if os.path.exists(arq_in) else []
    if respostas and respostas[-1] == "":
        respostas.pop()
    saida, _ = executar(nome + ".dk", respostas, cwd=CODIGOS, limite=90,
                        extra_env={"ADVAK_CURSO_TESTE": "1"})
    return saida


def rodar_todos(nomes):
    antes = set(os.listdir(CODIGOS))
    def usa_janela(n):                                      # janelas com temporizador não aguentam a máquina disputada
        caminho = os.path.join(CODIGOS, n + ".dk")
        return os.path.exists(caminho) and "gui." in ler(caminho)
    sequenciais = [n for n in nomes if os.path.exists(os.path.join(CODIGOS, n + ".http")) or usa_janela(n)]
    paralelos = [n for n in nomes if n not in sequenciais]
    resultados = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for n, s in zip(paralelos, ex.map(rodar_um, paralelos)):
            resultados[n] = s
    for n in sequenciais:
        resultados[n] = rodar_um(n)
    for extra in set(os.listdir(CODIGOS)) - antes:        # arquivos que os programas criaram (json, db, txt...)
        caminho = os.path.join(CODIGOS, extra)
        if os.path.isfile(caminho):
            os.remove(caminho)
    return resultados


ENTRADA = re.compile(r"<!--(entrada|http|repl):([^\s>]+)\n(.*?)-->", re.S)


def extrair():
    """Cria os arquivos de codigos/ a partir dos blocos escritos nas aulas."""
    os.makedirs(CODIGOS, exist_ok=True)
    n = 0
    for aula in aulas():
        t = ler(aula)
        for m in MARCADOR.finditer(t):
            if m.group(2) == "codigo" and m.group(5).strip():
                with open(os.path.join(CODIGOS, m.group(3)), "w", encoding="utf-8", newline="\n") as f:
                    f.write(m.group(5).rstrip("\n") + "\n")
                n += 1
        for m in ENTRADA.finditer(t):
            ext = {"entrada": ".in", "http": ".http", "repl": ".repl"}[m.group(1)]
            with open(os.path.join(CODIGOS, m.group(2) + ext), "w", encoding="utf-8", newline="\n") as f:
                f.write(m.group(3).strip("\n") + "\n")
            n += 1
    return n


def aulas():
    """As aulas (.md). Com a variável AULA=aula16 só essa aula é conferida/atualizada (mais rápido ao escrever)."""
    filtro = os.environ.get("AULA", "")
    return sorted(os.path.join(CURSO, f) for f in os.listdir(CURSO) if f.endswith(".md") and f.startswith(filtro))


def processar(atualizar=False):
    """Confere (ou reescreve) os blocos. Devolve a lista de problemas."""
    textos = {a: ler(a) for a in aulas()}
    precisam = sorted({m.group(3).rsplit(".", 1)[0] for t in textos.values() for m in MARCADOR.finditer(t)
                       if m.group(2) in ("saida", "erro")})
    ausentes = [n for n in precisam if not any(os.path.exists(os.path.join(CODIGOS, n + e)) for e in (".dk", ".repl"))]
    problemas = [f"programa inexistente: {n}.dk" for n in ausentes]
    reais = rodar_todos([n for n in precisam if n not in ausentes])
    for aula, texto in textos.items():
        def trocar(m):
            tipo, arquivo = m.group(2), m.group(3)
            nome = arquivo.rsplit(".", 1)[0]
            if tipo == "codigo":
                caminho = os.path.join(CODIGOS, arquivo)
                if not os.path.exists(caminho):
                    problemas.append(f"{os.path.basename(aula)}: arquivo inexistente {arquivo}")
                    return m.group(0)
                novo = ler(caminho).rstrip("\n") + "\n"
            elif nome not in reais:
                return m.group(0)
            elif tipo == "saida":
                novo = reais[nome].replace("\r", "").rstrip("\n") + "\n"
            else:
                novo = ultima_linha_de_erro(reais[nome]) + "\n"
            if novo != m.group(5):
                problemas.append(f"{os.path.basename(aula)}: bloco desatualizado ({tipo}:{arquivo})")
            return m.group(1) + novo + m.group(6)
        novo_texto = MARCADOR.sub(trocar, texto)
        if atualizar and novo_texto != texto:
            with open(aula, "w", encoding="utf-8", newline="\n") as f:
                f.write(novo_texto)
    for nome, saida in reais.items():                  # saída de exemplo/resposta com erro = engano de quem escreveu a aula
        if "_erro" not in nome and ("ERRO DE EXECUÇÃO" in saida or "ERRO INESPERADO" in saida or "Traceback" in saida or "SyntaxError" in saida
                                    or "Problema:" in saida and "repl" not in nome):
            problemas.append(f"ERRO INESPERADO em {nome}: {ultima_linha_de_erro(saida)}")
    return problemas


if __name__ == "__main__":
    if "--extrair" in sys.argv:
        print(f"{extrair()} arquivo(s) criado(s) em docs/curso/codigos/")
        sys.exit(0)
    atualizar = "--atualizar" in sys.argv
    probs = processar(atualizar)
    for p in probs:
        print(("atualizado: " if atualizar else "DIFERENTE: ") + p)
    print("pronto." if atualizar or not probs else f"{len(probs)} diferença(s). Rode com --atualizar.")
    sys.exit(0 if (atualizar or not probs) else 1)
