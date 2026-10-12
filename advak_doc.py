"""
Advak 5.0 — Gerador de Documentação
Execute: advak --doc arquivo.dk
Usa comentários /// para gerar documentação.
"""
import re, os, sys

def extrair_docs(source):
    """Extrai comentários /// e o elemento documentado."""
    linhas = source.split("\n")
    docs = []
    buffer_doc = []

    for i, linha in enumerate(linhas):
        l = linha.strip()

        # Acumula comentários ///
        m = re.match(r"^///\s*(.*)", l)
        if m:
            buffer_doc.append(m.group(1))
            continue

        # Elemento após comentários ///
        if buffer_doc:
            # Função
            mf = re.match(r"^(?:função|funcao|function)\s+(\w+)\s*\(([^)]*)\)", l)
            if mf:
                params_raw = [p.strip() for p in mf.group(2).split(",") if p.strip()]
                params = []
                for p in params_raw:
                    if "=" in p:
                        nome, padrao = p.split("=", 1)
                        params.append({"nome": nome.strip(), "padrao": padrao.strip()})
                    else:
                        params.append({"nome": p.strip(), "padrao": None})
                docs.append({
                    "tipo": "função",
                    "nome": mf.group(1),
                    "params": params,
                    "linhas": buffer_doc[:],
                    "linha": i + 1,
                })
                buffer_doc = []
                continue

            # Classe
            mc = re.match(r"^classe\s+(\w+)", l)
            if mc:
                docs.append({
                    "tipo": "classe",
                    "nome": mc.group(1),
                    "linhas": buffer_doc[:],
                    "linha": i + 1,
                })
                buffer_doc = []
                continue

            # Variável/constante
            mv = re.match(r"^(?:seja|fixo|const)\s+(\w+)\s*=\s*(.+)", l)
            if mv:
                docs.append({
                    "tipo": "variável",
                    "nome": mv.group(1),
                    "valor": mv.group(2).strip()[:40],
                    "linhas": buffer_doc[:],
                    "linha": i + 1,
                })
                buffer_doc = []
                continue

        buffer_doc = []

    return docs


def gerar_html(docs, titulo, caminho_fonte):
    """Gera documentação em HTML."""
    funcoes  = [d for d in docs if d["tipo"] == "função"]
    classes  = [d for d in docs if d["tipo"] == "classe"]
    variaveis= [d for d in docs if d["tipo"] == "variável"]

    def _params_html(params):
        if not params: return "()"
        ps = []
        for p in params:
            if p["padrao"]:
                ps.append(f'<span class="param">{p["nome"]}</span><span class="default">={p["padrao"]}</span>')
            else:
                ps.append(f'<span class="param">{p["nome"]}</span>')
        return "(" + ", ".join(ps) + ")"

    itens_html = ""
    for d in docs:
        desc = " ".join(d["linhas"])
        linhas_doc = "<br>".join(d["linhas"]) if d["linhas"] else "<em>Sem documentação.</em>"

        if d["tipo"] == "função":
            params_html = _params_html(d.get("params", []))
            itens_html += f"""
            <div class="item funcao">
              <div class="assinatura">função <span class="nome">{d['nome']}</span>{params_html}</div>
              <div class="descricao">{linhas_doc}</div>
              <div class="linha">Linha {d['linha']}</div>
            </div>"""
        elif d["tipo"] == "classe":
            itens_html += f"""
            <div class="item classe">
              <div class="assinatura">classe <span class="nome">{d['nome']}</span></div>
              <div class="descricao">{linhas_doc}</div>
              <div class="linha">Linha {d['linha']}</div>
            </div>"""
        elif d["tipo"] == "variável":
            itens_html += f"""
            <div class="item variavel">
              <div class="assinatura"><span class="kw">fixo</span> <span class="nome">{d['nome']}</span> = <span class="val">{d.get('valor','')}</span></div>
              <div class="descricao">{linhas_doc}</div>
            </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>{titulo} — Documentação Advak 5.0</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 0; }}
  .header {{ background: #1e293b; padding: 24px 40px; border-bottom: 2px solid #3b82f6; }}
  .header h1 {{ margin: 0; color: #3b82f6; font-size: 1.8em; }}
  .header p {{ margin: 4px 0 0; color: #64748b; }}
  .container {{ max-width: 900px; margin: 0 auto; padding: 32px 40px; }}
  .stats {{ display: flex; gap: 16px; margin-bottom: 32px; }}
  .stat {{ background: #1e293b; border-radius: 8px; padding: 12px 20px; }}
  .stat .n {{ font-size: 1.8em; font-weight: bold; color: #3b82f6; }}
  .stat .l {{ color: #64748b; font-size: 0.85em; }}
  .item {{ background: #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 16px; border-left: 4px solid #334155; }}
  .item.funcao {{ border-left-color: #3b82f6; }}
  .item.classe {{ border-left-color: #7c3aed; }}
  .item.variavel {{ border-left-color: #22c55e; }}
  .assinatura {{ font-family: monospace; font-size: 1.05em; color: #f1f5f9; margin-bottom: 8px; }}
  .nome {{ color: #38bdf8; font-weight: bold; }}
  .kw {{ color: #7c3aed; }}
  .param {{ color: #fbbf24; }}
  .default {{ color: #64748b; }}
  .val {{ color: #22c55e; }}
  .descricao {{ color: #94a3b8; line-height: 1.6; }}
  .linha {{ color: #475569; font-size: 0.8em; margin-top: 8px; }}
  h2 {{ color: #3b82f6; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
  .empty {{ color: #475569; font-style: italic; }}
</style>
</head>
<body>
<div class="header">
  <h1>📖 {titulo}</h1>
  <p>Documentação gerada automaticamente — Advak 5.0</p>
  <p style="color:#475569;font-size:0.85em">Fonte: {caminho_fonte}</p>
</div>
<div class="container">
  <div class="stats">
    <div class="stat"><div class="n">{len(funcoes)}</div><div class="l">Funções</div></div>
    <div class="stat"><div class="n">{len(classes)}</div><div class="l">Classes</div></div>
    <div class="stat"><div class="n">{len(variaveis)}</div><div class="l">Constantes</div></div>
    <div class="stat"><div class="n">{len(docs)}</div><div class="l">Total</div></div>
  </div>
  {('<h2>⚙️ Funções</h2>' + ''.join(d for d in [itens_html] if 'funcao' in d)) if funcoes else ''}
  {('<h2>🏗️ Classes</h2>') if classes else ''}
  {('<h2>📌 Constantes</h2>') if variaveis else ''}
  {itens_html if docs else '<p class="empty">Nenhum elemento documentado encontrado.<br>Use <code>///</code> para documentar funções e classes.</p>'}
</div>
</body>
</html>"""


def cmd_doc(path):
    if not os.path.exists(path):
        print(f"❌ Arquivo não encontrado: {path}"); return

    with open(path, encoding="utf-8") as f:
        source = f.read()

    docs  = extrair_docs(source)
    titulo = os.path.splitext(os.path.basename(path))[0]
    html  = gerar_html(docs, titulo, path)

    out = path.replace(".dk", "_doc.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  📖 Documentação gerada: {out}")
    print(f"  Elementos documentados: {len(docs)}")
    funcoes  = [d for d in docs if d['tipo'] == 'função']
    classes  = [d for d in docs if d['tipo'] == 'classe']
    variaveis= [d for d in docs if d['tipo'] == 'variável']
    if funcoes:   print(f"  ⚙️  Funções:    {len(funcoes)}")
    if classes:   print(f"  🏗️  Classes:    {len(classes)}")
    if variaveis: print(f"  📌 Constantes: {len(variaveis)}")
    if not docs:
        print(f"\n  💡 Use /// antes de funções para documentar:")
        print(f"     /// Calcula a soma de dois números")
        print(f"     função soma(a, b) {{ retornar a + b }}")
    print()
    return out
