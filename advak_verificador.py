"""
Advak 5.0 — Verificador de Tipos Estático
Execute: advak --verificar arquivo.dk
"""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from advak_formatacao import proteger_literais

def verificar(source, path=""):
    """Verifica tipos e padrões comuns de erro no código."""
    linhas = source.split("\n")
    problemas = []

    def problema(linha, tipo, msg, dica=""):
        problemas.append({"linha": linha, "tipo": tipo, "msg": msg, "dica": dica})

    # Variáveis declaradas
    declaradas = {}
    usadas = set()

    for i, linha in enumerate(linhas, 1):
        l = linha.strip()
        if not l or l.startswith("//"): continue

        # Detecta declaração: seja x = ...
        m = re.match(r"^(?:seja|fixo)\s+(\w+)\s*=", l)
        if m:
            nome = m.group(1)
            declaradas[nome] = i
            # Detecta tipo pelo valor
            rest = l[m.end():].strip()
            if rest.startswith('"') or rest.startswith("'") or rest.startswith("`"):
                declaradas[nome] = {"linha": i, "tipo": "texto"}
            elif re.match(r"^\d+\.\d+", rest):
                declaradas[nome] = {"linha": i, "tipo": "numero_decimal"}
            elif re.match(r"^\d+", rest):
                declaradas[nome] = {"linha": i, "tipo": "numero"}
            elif rest.startswith("["):
                declaradas[nome] = {"linha": i, "tipo": "lista"}
            elif rest.startswith("{"):
                declaradas[nome] = {"linha": i, "tipo": "mapa"}
            elif rest in ("verdadeiro", "falso"):
                declaradas[nome] = {"linha": i, "tipo": "booleano"}
            elif rest == "nulo":
                declaradas[nome] = {"linha": i, "tipo": "nulo"}
            else:
                declaradas[nome] = {"linha": i, "tipo": "desconhecido"}
            continue

        # Detecta uso de variáveis
        idents = re.findall(r"\b([a-zA-Záéíóúàãõâêôüçñ_][\w_]*)\b", l)
        for ident in idents:
            usadas.add(ident)

        # Detecta concatenação texto+numero: "ola" + numero
        if re.search(r'"[^"]*"\s*\+\s*\d', l) or re.search(r'\d\s*\+\s*"[^"]*"', l):
            problema(i, "⚠️  Aviso",
                "Concatenação de texto com número",
                "Use texto(numero) para converter: \"Olá \" + texto(x)")

        # Detecta / sem verificação de zero
        # (ignora o que está dentro de textos e comentários: "dd/mm/aaaa", `${d:dd/mm/aaaa}`, // a/b)
        l_div = re.sub(r'\x00\d+\x00', ' ', proteger_literais(l)[0])
        if re.search(r"/\s*(?!/)\w", l_div) and "!=" not in l and "se" not in l:
            if re.search(r"\w\s*/\s*\w+[^=]", l_div) and "http" not in l.lower():
                problema(i, "💡 Sugestão",
                    "Possível divisão — verifique se o divisor pode ser zero",
                    "Use: se (b != 0) { resultado = a / b }")

        # Detecta imprimir sem parênteses
        if re.match(r"^imprimir\s+[^(]", l):
            problema(i, "❌ Erro",
                "imprimir sem parênteses",
                "Use: imprimir(valor)")

        # Detecta atribuição com == em vez de =
        if re.match(r"^(?:seja|fixo)\s+\w+\s*==", l):
            problema(i, "❌ Erro",
                "Use = para atribuir, não ==",
                "seja x = 5  (não  seja x == 5)")

        # Detecta função sem retornar
        if re.match(r"^função\s+\w+", l):
            # Check if function has return
            pass

    # Verifica variáveis fixo sendo reatribuídas
    constantes = {k for k, v in declaradas.items()
                  if isinstance(v, dict) and "fixo" in source.split("\n")[v["linha"]-1]}

    # Relatório
    return problemas

def cmd_verificar(path):
    if not os.path.exists(path):
        print(f"❌ Arquivo não encontrado: {path}"); return

    with open(path, encoding="utf-8") as f:
        source = f.read()

    print(f"\n🔍 Verificando: {path}")
    print("─" * 50)

    problemas = verificar(source, path)
    linhas = source.split("\n")

    if not problemas:
        print(f"\n  ✅ Nenhum problema encontrado!")
        print(f"  {len(linhas)} linhas verificadas.\n")
        return

    for p in problemas:
        ln = p["linha"]
        print(f"\n  {p['tipo']} — Linha {ln}")
        print(f"  {p['msg']}")
        if ln <= len(linhas):
            print(f"  → {linhas[ln-1].strip()}")
        if p["dica"]:
            print(f"  💡 {p['dica']}")

    tipos = {"❌ Erro": 0, "⚠️  Aviso": 0, "💡 Sugestão": 0}
    for p in problemas:
        tipos[p["tipo"]] = tipos.get(p["tipo"], 0) + 1

    print(f"\n  Encontrado: ", end="")
    partes = [f"{v} {k}" for k, v in tipos.items() if v > 0]
    print(" | ".join(partes))
    print()
