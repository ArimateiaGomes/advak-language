"""Sobe exemplos/05_api_tarefas.dk, faz as requisições do guia e derruba o servidor. Mostra a saída real."""
import json, os, subprocess, sys, time, urllib.request, urllib.error
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://localhost:8080"
db = os.path.join(RAIZ, "exemplos", "dados", "tarefas.db")
if os.path.exists(db):
    os.remove(db)
p = subprocess.Popen([sys.executable, "advak.py", "exemplos/05_api_tarefas.dk"], cwd=RAIZ,
                     env=dict(os.environ, PYTHONUTF8="1"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def req(metodo, caminho, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    r = urllib.request.Request(BASE + caminho, data=dados, method=metodo, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            txt, st = resp.read().decode(), resp.status
    except urllib.error.HTTPError as e:
        txt, st = e.read().decode(), e.code
    print(f"{metodo} {caminho}" + (f"  {json.dumps(corpo, ensure_ascii=False)}" if corpo is not None else ""))
    print(f"  -> {st} {txt}")

try:
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + "/", timeout=1); break
        except Exception:
            time.sleep(0.25)
    req("GET", "/api/tarefas")
    req("POST", "/api/tarefas", {"titulo": "Estudar Advak"})
    req("POST", "/api/tarefas", {"titulo": "Fazer o exercício"})
    req("POST", "/api/tarefas", {})
    req("GET", "/api/tarefas/1")
    req("PUT", "/api/tarefas/1", {"feita": True})
    req("GET", "/api/tarefas")
    req("GET", "/api/tarefas/99")
    req("DELETE", "/api/tarefas/2")
    req("GET", "/api/tarefas")
finally:
    p.kill(); p.wait()
    if os.path.exists(db):
        try: os.remove(db)
        except OSError: pass
