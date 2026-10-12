#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║  ADVAK STUDIO — Script de Correção de Travamento        ║
║  Execute: python corrigir_studio.py                     ║
╚══════════════════════════════════════════════════════════╝
"""
import sys, os, re, time

VERDE  = "\033[92m"
VERM   = "\033[91m"
AMAREL = "\033[93m"
RESET  = "\033[0m"
AZUL   = "\033[94m"

def ok(msg):   print(f"  {VERDE}✅{RESET} {msg}")
def err(msg):  print(f"  {VERM}❌{RESET} {msg}")
def info(msg): print(f"  {AZUL}→{RESET}  {msg}")
def warn(msg): print(f"  {AMAREL}⚠️{RESET}  {msg}")

print(f"""
{AZUL}╔══════════════════════════════════════════════════════════╗
║  🔧 ADVAK STUDIO — Correção de Travamento               ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")

# ── Verificar pasta ────────────────────────────────────────────────────────
pasta = os.path.dirname(os.path.abspath(__file__))
os.chdir(pasta)
info(f"Pasta: {pasta}")

if not os.path.exists("advak_interpreter.py"):
    err("advak_interpreter.py não encontrado!")
    err("Execute dentro da pasta C:\\Advak_5")
    sys.exit(1)
ok("Pasta Advak encontrada")

# ── Ler arquivos ────────────────────────────────────────────────────────────
with open("advak_interpreter.py", encoding="utf-8") as f:
    interp = f.read()

print(f"\n{AZUL}━━ Diagnóstico ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

# Diagnóstico
tem_v2     = "_executar_studio_v2" in interp
tem_studio = "def _executar_studio(" in interp
tem_after0 = "root.after(0, _atualizar_console)" in interp
tem_after100 = "root.after(100, _verificar)" in interp

if tem_v2:
    ok("executar_studio_v2 presente (versão robusta para Windows)")
else:
    warn("executar_studio_v2 ausente — precisa adicionar")

if tem_studio:
    ok("executar_studio() presente")
else:
    warn("executar_studio() ausente")

if tem_after0:
    ok("root.after(0) configurado")
elif tem_after100:
    ok("root.after(100) configurado (polling)")
else:
    warn("root.after() não configurado")

# ── Studio .dk ─────────────────────────────────────────────────────────────
studio_path = "projetos/advak_studio.dk"
tem_studio_dk = os.path.exists(studio_path)

if tem_studio_dk:
    with open(studio_path, encoding="utf-8") as f:
        studio = f.read()
    usa_exec_studio = "executar_studio(" in studio
    if usa_exec_studio:
        ok("Studio usa executar_studio()")
    else:
        warn("Studio não usa executar_studio() — pode travar")
    info(f"Studio: {len(studio.splitlines())} linhas")
else:
    err("projetos/advak_studio.dk não encontrado!")

print(f"\n{AZUL}━━ Aplicando Correções ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

modificado = False

# ── Correção 1: Adicionar executar_studio_v2 se não existir ────────────────
if not tem_v2:
    novo_builtin = '''
        def _executar_studio_v2(codigo_str, console_tk, status_tk, flag_lista):
            """Versão robusta para Windows com polling via root.after(100ms)."""
            import io, sys, asyncio, threading, builtins as _bi

            codigo_str = str(codigo_str)
            resultado = [None]

            def _run():
                buf = io.StringIO()
                old_out = sys.stdout; old_print = _bi.print
                sys.stdout = buf
                _bi.print = lambda *a, **k: buf.write(
                    k.get("sep"," ").join(str(x) for x in a) + k.get("end","\\n"))
                try:
                    from advak_lexer import AdvakLexer
                    from advak_parser import Parser as _P
                    tokens = AdvakLexer(codigo_str).tokenize()
                    ast    = _P(tokens).parse()
                    interp = AdvakInterpreter(ast)
                    loop   = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(interp.interpret())
                    finally:
                        loop.close(); asyncio.set_event_loop(None)
                    sys.stdout = old_out; _bi.print = old_print
                    resultado[0] = buf.getvalue() or "__sem_saida__"
                except RecursionError:
                    sys.stdout = old_out; _bi.print = old_print
                    resultado[0] = "❌ Recursão muito profunda — adicione um caso base"
                except Exception as e:
                    sys.stdout = old_out; _bi.print = old_print
                    _tn = type(e).__name__
                    _tr = {"TypeError":"Tipo incompatível","ValueError":"Valor inválido",
                           "KeyError":"Chave não encontrada","IndexError":"Índice fora do alcance",
                           "FileNotFoundError":"Arquivo não encontrado",
                           "RecursionError":"Recursão muito profunda"}
                    resultado[0] = f"❌ {_tr.get(_tn, _tn)}: {e}"

            def _verificar():
                if resultado[0] is None:
                    try:
                        import advak_gui_modern as _agm
                        root = _agm._root_ref
                        if root: root.after(100, _verificar)
                    except Exception: pass
                    return
                saida = resultado[0]
                try:
                    console_tk.configure(state="normal")
                    if saida == "__sem_saida__":
                        console_tk.insert("end",
                            "✅ Executado sem saída impressa\\n"
                            "   Dica: use imprimir() para ver resultados\\n")
                    else:
                        console_tk.insert("end", saida)
                        if not saida.endswith("\\n"):
                            console_tk.insert("end", "\\n")
                    console_tk.insert("end", "\\n── Concluído ──\\n")
                    console_tk.see("end")
                    console_tk.configure(state="disabled")
                except Exception: pass
                try: status_tk.configure(text="✅ Pronto", fg="#3FB950")
                except Exception: pass
                try: flag_lista[0] = False
                except Exception: pass

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            try:
                import advak_gui_modern as _agm
                root = _agm._root_ref
                if root: root.after(100, _verificar)
            except Exception: pass

        g.declare("executar_studio", _executar_studio_v2)
'''
    # Inserir antes de g.declare('advak_executar_async'
    marcador = "g.declare('advak_executar_async', _advak_executar_async)"
    if marcador not in interp:
        marcador = 'g.declare("advak_executar_async", _advak_executar_async)'

    if marcador in interp:
        interp = interp.replace(marcador, marcador + "\n" + novo_builtin)
        modificado = True
        ok("executar_studio_v2 adicionado ao interpretador")
    else:
        warn("Não foi possível adicionar v2 automaticamente")

# ── Correção 2: Reescrever executar() no studio se necessário ─────────────
if tem_studio_dk and not usa_exec_studio:
    idx_fn = studio.find("funcao executar() {")
    idx_fim = studio.find("\nfuncao parar()", idx_fn)
    if idx_fn >= 0 and idx_fim > idx_fn:
        nova_fn = """funcao executar() {
    se (_executando[0]) {
        gui.toast("Já está executando! Pressione F6 para parar.", "aviso", 2000)
        retornar
    }
    seja codigo = editor.get("1.0", "end")
    se (codigo.aparar() == "") {
        gui.toast("Editor vazio! Escreva algum código primeiro.", "aviso", 2000)
        retornar
    }
    console_limpar()
    console_escrever("▶ Executando...\\n", C_VERDE)
    lbl_status_topo.configure(text="⏳ Executando...", fg=C_AMAREL)
    _executando[0] = verdadeiro
    abas_direito.selecionar(0)
    executar_studio(codigo, console, lbl_status_topo, _executando)
}"""
        studio = studio[:idx_fn] + nova_fn + studio[idx_fim:]
        with open(studio_path, "w", encoding="utf-8") as f:
            f.write(studio)
        ok("executar() no studio reescrita para usar executar_studio()")

# ── Salvar interpretador se modificado ────────────────────────────────────
if modificado:
    with open("advak_interpreter.py", "w", encoding="utf-8") as f:
        f.write(interp)
    ok("advak_interpreter.py salvo")

print(f"\n{AZUL}━━ Verificação Final ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

import py_compile
try:
    py_compile.compile("advak_interpreter.py", doraise=True)
    ok("advak_interpreter.py compila sem erros")
except Exception as e:
    err(f"advak_interpreter.py: {e}")

if tem_studio_dk:
    try:
        sys.path.insert(0, pasta)
        from advak_lexer import AdvakLexer
        from advak_parser import Parser
        src = open(studio_path, encoding="utf-8").read()
        Parser(AdvakLexer(src).tokenize()).parse()
        ok(f"advak_studio.dk parseia OK ({len(src.splitlines())} linhas)")
    except Exception as e:
        err(f"advak_studio.dk: {e}")

print(f"""
{VERDE}╔══════════════════════════════════════════════════════════╗
║  ✅ Correção concluída!                                 ║
║                                                          ║
║  Execute o Studio:                                       ║
║  > advak projetos\\advak_studio.dk                        ║
║                                                          ║
║  Pressione F5 para executar código.                     ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")
