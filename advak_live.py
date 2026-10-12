"""
Advak 5.0 — Hot Reload
Execute: advak --live arquivo.dk
Reexecuta automaticamente quando o arquivo é salvo.
"""
import os, sys, time, subprocess, threading

def cmd_live(path):
    if not os.path.exists(path):
        print(f"❌ Arquivo não encontrado: {path}"); return

    print(f"""
╔══════════════════════════════════════════════╗
║    🔥  ADVAK HOT RELOAD                      ║
╠══════════════════════════════════════════════╣
║  Arquivo: {path[:36]:<36}║
║  Salve o arquivo para reexecutar             ║
║  Ctrl+C para sair                            ║
╚══════════════════════════════════════════════╝
""")

    ultima_modificacao = 0
    processo_atual = [None]

    def executar():
        if processo_atual[0]:
            try: processo_atual[0].terminate()
            except: pass

        print(f"\n  ▶  Executando... ({time.strftime('%H:%M:%S')})")
        print("  " + "─" * 44)
        processo_atual[0] = subprocess.Popen(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'advak.py'), path],
            stdout=None, stderr=None
        )
        processo_atual[0].wait()
        print("\n  " + "─" * 44)
        print("  ⏳ Aguardando mudanças...")

    try:
        # Primeira execução
        executar()

        while True:
            try:
                mod_time = os.path.getmtime(path)
                if mod_time != ultima_modificacao:
                    if ultima_modificacao > 0:  # não na primeira vez
                        print(f"\n  🔄 Arquivo modificado! Reexecutando...")
                    ultima_modificacao = mod_time
                    if ultima_modificacao > 0 or processo_atual[0] is None:
                        executar()
                time.sleep(0.5)
            except FileNotFoundError:
                print(f"\n  ⚠️  Arquivo não encontrado: {path}")
                time.sleep(1)
    except KeyboardInterrupt:
        if processo_atual[0]:
            try: processo_atual[0].terminate()
            except: pass
        print("\n\n  👋 Hot Reload encerrado.")
