"""
Roda um programa .dk como se uma pessoa estivesse digitando e mostra a "tela" do jeito que ela apareceria
no terminal (o que a Advak escreveu, com cada resposta digitada logo depois da pergunta).

Uso:
    python testes/rodar_exemplo.py programa.dk                      # sem digitar nada
    python testes/rodar_exemplo.py programa.dk "Ana" "3" "8"        # cada argumento é uma linha digitada
    python testes/rodar_exemplo.py programa.dk --linhas arq.txt     # respostas, uma por linha, em um arquivo

Como funciona: a resposta seguinte só é enviada quando o programa para de escrever por um instante
(ou seja, quando ele está esperando a digitação). O que se vê é exatamente a saída real do programa.
"""
import os
import subprocess
import sys
import threading
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def executar(programa, respostas=(), ocioso=0.6, limite=60, cwd=RAIZ, extra_env=None):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONUNBUFFERED="1", **(extra_env or {}))
    p = subprocess.Popen([sys.executable, "-u", os.path.join(RAIZ, "advak.py"), programa], cwd=cwd, env=env,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    pedacos, ultimo, novo = [], [time.time()], [False]   # novo: o programa escreveu algo desde a última resposta

    def ler():
        while True:
            b = p.stdout.read1(4096) if hasattr(p.stdout, "read1") else p.stdout.read(1)
            if not b:
                break
            pedacos.append(b)
            ultimo[0] = time.time()
            novo[0] = True

    t = threading.Thread(target=ler, daemon=True)
    t.start()
    fila, inicio, ecoado = list(respostas), time.time(), []
    enviou = [False]
    while p.poll() is None and time.time() - inicio < limite:
        time.sleep(0.05)
        parou = time.time() - ultimo[0]
        # só responde depois que o programa escreveu algo novo (a pergunta); sem pergunta, espera mais
        chegou_algo = novo[0]
        if parou >= (ocioso if chegou_algo else ocioso * 5) and (chegou_algo or enviou[0]):
            if fila:
                linha = fila.pop(0)
                pedacos.append((linha + "\n").encode("utf-8"))
                ecoado.append(linha)
                try:
                    p.stdin.write((linha + "\n").encode("utf-8"))
                    p.stdin.flush()
                except OSError:
                    break
                ultimo[0] = time.time()
                enviou[0], novo[0] = True, False
            elif parou >= ocioso * 3:
                break                                    # esperando digitação que não virá
    if p.poll() is None:
        p.kill()
    t.join(2)
    try:
        p.stdin.close()
    except OSError:
        pass
    return b"".join(pedacos).decode("utf-8", "replace").replace("\r\n", "\n"), p.returncode


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    prog, resp = args[0], []
    rest = args[1:]
    if rest[:1] == ["--linhas"]:
        with open(rest[1], encoding="utf-8") as f:
            resp = f.read().split("\n")
            if resp and resp[-1] == "":
                resp.pop()
    else:
        resp = rest
    saida, codigo = executar(prog, resp)
    sys.stdout.buffer.write(saida.encode("utf-8"))
    sys.exit(0 if codigo in (0, None) else codigo)
