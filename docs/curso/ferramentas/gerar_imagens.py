"""Gera as imagens do jogo 2D do curso (aula 25) em docs/curso/codigos/imagens/.

Só biblioteca padrão (zlib, struct). Todos os pixels saem de fórmulas escritas aqui: não há arte de terceiros.
Sem relógio, sem acaso e em ordem fixa, para a saída ser a mesma a cada execução.

    python docs/curso/ferramentas/gerar_imagens.py              # escreve os arquivos
    python docs/curso/ferramentas/gerar_imagens.py --conferir   # não escreve; compara com o que está na pasta

O destino vem da localização deste arquivo, não do diretório atual.
"""
import os, struct, sys, zlib

DESTINO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "codigos", "imagens")
TRANSPARENTE = (0, 0, 0, 0)


def png(largura, altura, pixels):
    """PNG RGBA de 8 bits, sem filtro, a partir de linhas de tuplas (r, g, b, a)."""
    bruto = b"".join(b"\x00" + b"".join(bytes(p) for p in linha) for linha in pixels)
    def bloco(tipo, dados):
        corpo = tipo + dados
        return struct.pack(">I", len(dados)) + corpo + struct.pack(">I", zlib.crc32(corpo))
    return (b"\x89PNG\r\n\x1a\n"
            + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 6, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(bruto, 9))
            + bloco(b"IEND", b""))


def grade(largura, altura, cor):
    return [[cor(x, y) for x in range(largura)] for y in range(altura)]


def cor_fundo(x, y):                              # xadrez de quadrados de 32 px em dois verdes
    return (46, 158, 68, 255) if (x // 32 + y // 32) % 2 == 0 else (38, 140, 58, 255)


def cor_heroi(x, y):                              # 32x32: cabeça, olhos, corpo, pés
    if 10 <= x < 22 and 4 <= y < 14:
        return (0, 0, 0, 255) if (x, y) in ((13, 8), (18, 8)) else (255, 213, 170, 255)
    if 8 <= x < 24 and 14 <= y < 28:
        return (30, 102, 245, 255)
    if 28 <= y < 32 and (10 <= x < 14 or 18 <= x < 22):
        return (60, 60, 60, 255)
    return TRANSPARENTE


def cor_moeda(semi_largura):                      # 16x16, elipse: a largura muda de um quadro para o outro (giro)
    def cor(x, y):
        dx, dy = (x - 7.5) / semi_largura, (y - 7.5) / 7.5
        d = dx * dx + dy * dy
        if d <= 1:
            return (249, 215, 28, 255) if d <= 0.6 else (176, 140, 0, 255)
        return TRANSPARENTE
    return cor


def cor_parede(x, y):                             # tijolos de 16x8
    return (139, 90, 43, 255) if (x % 16 != 0 and y % 8 != 0) else (90, 58, 27, 255)


def gerar():
    """Devolve {nome: bytes}, em ordem fixa."""
    return {
        "fundo.png":   png(480, 320, grade(480, 320, cor_fundo)),
        "heroi.png":   png(32, 32, grade(32, 32, cor_heroi)),
        "moeda1.png":  png(16, 16, grade(16, 16, cor_moeda(7.5))),
        "moeda2.png":  png(16, 16, grade(16, 16, cor_moeda(5.5))),
        "moeda3.png":  png(16, 16, grade(16, 16, cor_moeda(3.0))),
        "moeda4.png":  png(16, 16, grade(16, 16, cor_moeda(5.5))),
        "parede.png":  png(32, 32, grade(32, 32, cor_parede)),
    }


def main(argv):
    arquivos = gerar()
    if "--conferir" in argv:
        diferentes = []
        for nome, dados in arquivos.items():
            caminho = os.path.join(DESTINO, nome)
            if not os.path.isfile(caminho) or open(caminho, "rb").read() != dados:
                diferentes.append(nome)
        if diferentes:
            print("Diferentes ou ausentes:", ", ".join(diferentes)); return 1
        print(f"{len(arquivos)} arquivos iguais aos gerados."); return 0
    os.makedirs(DESTINO, exist_ok=True)
    for nome, dados in arquivos.items():
        with open(os.path.join(DESTINO, nome), "wb") as f:
            f.write(dados)
    print(f"{len(arquivos)} arquivos em {DESTINO} ({sum(len(d) for d in arquivos.values())} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
