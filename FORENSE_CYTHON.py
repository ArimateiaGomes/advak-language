#!/usr/bin/env python3
"""
FORENSE_CYTHON.py
Varredura forense completa para encontrar EXATAMENTE onde o \\uXXXX aparece.
Execute: python FORENSE_CYTHON.py
"""
import os, sys, re, tempfile, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
FIB  = os.path.join(BASE, 'projetos', 'fibonacci.dk')
sys.path.insert(0, BASE)

SEP = "─" * 60

def titulo(msg):
    print()
    print(SEP)
    print(f"  {msg}")
    print(SEP)

def check_escapes(texto, label):
    escapes = re.findall(r'\\[uU][0-9a-fA-F]{2,8}', texto)
    if escapes:
        print(f"  ❌ {label}: {len(escapes)} escape(s) encontrado(s)")
        linhas = texto.split('\n')
        for i, linha in enumerate(linhas, 1):
            if re.search(r'\\[uU][0-9a-fA-F]{2,8}', linha):
                print(f"     L{i}: {linha.strip()!r}")
        return escapes
    else:
        print(f"  ✅ {label}: zero escapes")
        return []

# ═══════════════════════════════════════════════════════
titulo("FASE 1 — Teste direto de _py_str()")
# ═══════════════════════════════════════════════════════
from advak_nativo import _py_str, TranspiladorPython

strings_unicode = [
    '✅ Resultados idênticos!',
    '  ✅ Todas as 4 implementações concordam!',
    '─── Razão Áurea (φ) ────────────────────────',
    '  φ real ≈ 1.6180339887...',
    '╔══════════════════════════════════════════╗',
]

print("  _py_str() output:")
for s in strings_unicode:
    r = _py_str(s)
    escapes = re.findall(r'\\[uU][0-9a-fA-F]{2,8}', r)
    status = '❌' if escapes else '✅'
    print(f"  {status} Input: {s!r}")
    print(f"     Output: {r!r}")
    if escapes:
        print(f"     ESCAPES: {escapes}")

# ═══════════════════════════════════════════════════════
titulo("FASE 2 — Transpilador Python: saída de fibonacci.dk")
# ═══════════════════════════════════════════════════════
code_dk = open(FIB, encoding='utf-8').read()
tp = TranspiladorPython()
python_code = tp.transpilar(code_dk, 'fibonacci')

escapes_py = check_escapes(python_code, "TranspiladorPython output")

# ═══════════════════════════════════════════════════════
titulo("FASE 3 — Cython header + python_code concatenados")
# ═══════════════════════════════════════════════════════
cython_header = f"""# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# Gerado pelo Advak Compiler 5.0 — Cython Backend
# Módulo: fibonacci

"""
cython_code = cython_header + python_code
escapes_concat = check_escapes(cython_code, "cython_header + python_code")

# ═══════════════════════════════════════════════════════
titulo("FASE 4 — Simulação EXATA do que CompiladorCython faz")
# ═══════════════════════════════════════════════════════
# Replica exatamente o método compilar() do CompiladorCython
from advak_nativo import CompiladorCython
cc = CompiladorCython()

# Verifica o método _verificar_cython
ok, msg = cc._verificar_cython()
print(f"  Cython disponível: {ok} ({msg})")

# Agora simula o compilar() passo a passo
print()
print("  Simulando CompiladorCython.compilar() passo a passo...")

# Passo 1: transpila
tp2 = TranspiladorPython()
python_code2 = tp2.transpilar(code_dk, 'fibonacci')
print(f"  Passo 1 (transpilar): {len(python_code2)} chars")
check_escapes(python_code2, "  python_code2")

# Passo 2: adiciona header Cython
cython_header2 = f"""# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# Gerado pelo Advak Compiler 5.0 — Cython Backend
# Módulo: fibonacci

"""
cython_code2 = cython_header2 + python_code2
print(f"  Passo 2 (header): {len(cython_code2)} chars")
check_escapes(cython_code2, "  cython_code2")

# Passo 3: escreve para arquivo temporário
with tempfile.TemporaryDirectory() as tmpdir:
    pyx_path = os.path.join(tmpdir, 'fibonacci.pyx')
    with open(pyx_path, 'w', encoding='utf-8') as f:
        f.write(cython_code2)
    
    # Lê de volta como faria o Cython
    with open(pyx_path, 'r', encoding='utf-8') as f:
        conteudo_lido = f.read()
    
    print(f"  Passo 3 (escrita/leitura .pyx): {len(conteudo_lido)} chars")
    escapes_pyx = check_escapes(conteudo_lido, "  conteudo do .pyx")
    
    if escapes_pyx:
        print()
        print("  🔍 Contexto do escape:")
        for i, linha in enumerate(conteudo_lido.split('\n'), 1):
            if re.search(r'\\[uU][0-9a-fA-F]{2,8}', linha):
                inicio = max(0, i-3)
                fim = min(len(conteudo_lido.split('\n')), i+3)
                for j, l in enumerate(conteudo_lido.split('\n')[inicio:fim], inicio+1):
                    marker = ">>>" if j == i else "   "
                    print(f"     {marker} L{j}: {l!r}")
        
        # Salva o .pyx com problema para inspecao
        pyx_problema = os.path.join(BASE, 'dist', 'fibonacci_PROBLEMA.pyx')
        os.makedirs(os.path.dirname(pyx_problema), exist_ok=True)
        shutil.copy(pyx_path, pyx_problema)
        print(f"\n  💾 .pyx com problema salvo: {pyx_problema}")
    
    # Passo 4: tenta compilar com cython CLI
    import subprocess
    print()
    print("  Passo 4: testando cython CLI...")
    r = subprocess.run(
        [sys.executable, '-m', 'cython', '--version'],
        capture_output=True, text=True
    )
    print(f"  Cython CLI: {r.stdout.strip() or r.stderr.strip()}")

# ═══════════════════════════════════════════════════════
titulo("FASE 5 — Verifica método compilar() no código fonte")
# ═══════════════════════════════════════════════════════
with open(os.path.join(BASE, 'advak_nativo.py'), 'r', encoding='utf-8') as f:
    fonte = f.read()

# Encontra o método compilar da classe CompiladorCython
idx_class = fonte.find('class CompiladorCython:')
idx_compilar = fonte.find('    def compilar(', idx_class)
idx_fim = fonte.find('\n    def ', idx_compilar + 50)

if idx_compilar > 0:
    metodo = fonte[idx_compilar:idx_fim if idx_fim > 0 else idx_compilar+3000]
    print(f"  Método compilar() encontrado ({len(metodo)} chars)")
    
    # Verifica se há qualquer transformação de string
    transformacoes = [
        'encode(', 'decode(', '_decode_escapes', 'raw_unicode',
        'unicode_escape', 'codecs', 'repr(cython', 'repr(python_code',
    ]
    print()
    print("  Verificando transformações no método:")
    for t in transformacoes:
        if t in metodo:
            # Encontra a linha
            for i, linha in enumerate(metodo.split('\n'), 1):
                if t in linha:
                    print(f"  ⚠️  '{t}' encontrado: {linha.strip()!r}")
        else:
            print(f"  ✅ '{t}' ausente")
    
    print()
    print("  Código do método compilar() (primeiras 40 linhas):")
    for i, linha in enumerate(metodo.split('\n')[:40], 1):
        print(f"  {i:3}: {linha}")

# ═══════════════════════════════════════════════════════
titulo("FASE 6 — Verifica a string do cython_header no fonte")
# ═══════════════════════════════════════════════════════
# Encontra onde cython_header é definido
idx_header = fonte.find('cython_header')
while idx_header > 0:
    linha_header = fonte[max(0,idx_header-50):idx_header+200]
    if 'Módulo' in linha_header or 'modulo' in linha_header.lower():
        print("  cython_header encontrado:")
        print(f"  {linha_header!r}")
        # Verifica escapes
        escapes_h = re.findall(r'\\[uU][0-9a-fA-F]{2,8}', linha_header)
        if escapes_h:
            print(f"  ❌ ESCAPES NO HEADER: {escapes_h}")
        else:
            print("  ✅ Header sem escapes")
        break
    idx_header = fonte.find('cython_header', idx_header + 1)

# ═══════════════════════════════════════════════════════
titulo("RESUMO")
# ═══════════════════════════════════════════════════════
total_escapes = len(escapes_py) + len(escapes_concat)
if total_escapes == 0:
    print("""
  ✅ Todos os testes locais passaram.
  
  O problema pode ser:
  1. O Python do Windows tem configuracao diferente de encoding
  2. O arquivo .pyx e criado num tmpdir com encoding diferente
  3. Algum outro modulo interfere
  
  SOLUCAO: veja o arquivo dist\\fibonacci_PROBLEMA.pyx 
  para inspecionar o conteudo exato que o Cython recebe.
""")
else:
    print(f"""
  ❌ Encontrados {total_escapes} escapes unicode.
  Veja os detalhes acima para corrigir.
""")
