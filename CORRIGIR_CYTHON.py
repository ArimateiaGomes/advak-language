#!/usr/bin/env python3
"""
CORRIGIR_CYTHON.py
Localiza e corrige o bug de unicode escape no advak_nativo.py
Execute: python CORRIGIR_CYTHON.py
"""
import os
import re
import sys

ARQUIVO = os.path.join(os.path.dirname(__file__), 'advak_nativo.py')

def linha(msg, c='─'):
    print(c * 54)
    print(f"  {msg}")

def verificar():
    print()
    print("=" * 54)
    print("  DIAGNÓSTICO — advak_nativo.py")
    print("=" * 54)

    with open(ARQUIVO, 'r', encoding='utf-8') as f:
        code = f.read()
    linhas = code.split('\n')

    erros = []

    # ── 1. Verifica _py_str ─────────────────────────────────
    if '_py_str' in code:
        print("  ✅ _py_str() definida")
    else:
        print("  ❌ _py_str() NÃO encontrada")
        erros.append('sem_py_str')

    # ── 2. Verifica se string usa _py_str ───────────────────
    if "_py_str(node['value'])" in code:
        print("  ✅ String transpiler usa _py_str()")
    else:
        print("  ❌ String transpiler ainda usa repr()")
        erros.append('repr_em_string')

    # ── 3. Verifica _decode_escapes (bug) ───────────────────
    if '_decode_escapes' in code:
        # Encontra a linha exata
        for i, l in enumerate(linhas, 1):
            if '_decode_escapes' in l:
                print(f"  ❌ _decode_escapes encontrado na linha {i}: {l.strip()}")
        erros.append('decode_escapes_presente')
    else:
        print("  ✅ _decode_escapes removido")

    # ── 4. Verifica regex com 4 barras ──────────────────────
    if r'\\\\u' in code:
        for i, l in enumerate(linhas, 1):
            if r'\\\\u' in l:
                print(f"  ❌ Regex com 4 barras (linha {i}): {l.strip()}")
        erros.append('regex_4_barras')
    else:
        print("  ✅ Sem regex quebrado")

    # ── 5. Verifica escrita do .pyx ─────────────────────────
    idx = code.find("with open(pyx_path, 'w'")
    if idx >= 0:
        trecho = code[max(0, idx-400):idx+60]
        if '_decode_escapes' in trecho:
            print("  ❌ _decode_escapes ainda é chamado ANTES de escrever .pyx")
            erros.append('decode_antes_write')
        else:
            print("  ✅ Escrita do .pyx limpa")
    else:
        print("  ⚠️  Escrita do .pyx não encontrada")

    # ── 6. Testa geração de string unicode ──────────────────
    print()
    linha("Testando transpilação de string unicode...")
    try:
        from advak_nativo import TranspiladorPython
        tp = TranspiladorPython()
        node = {'type': 'string', 'value': '✅ Razão Áurea (φ) ═══'}
        resultado = tp._transpilar_expr(node)
        escapes = re.findall(r'\\[uU][0-9a-fA-F]{4}', resultado)
        if escapes:
            print(f"  ❌ Ainda gera escapes: {resultado!r}")
            erros.append('ainda_gera_escapes')
        else:
            print(f"  ✅ String limpa: {resultado}")
    except Exception as e:
        print(f"  ❌ Erro ao testar: {e}")
        erros.append('erro_teste')

    return erros, code, linhas


def corrigir(erros, code):
    print()
    print("=" * 54)
    print("  CORRIGINDO...")
    print("=" * 54)

    modificado = False

    # ── Correção 1: Adiciona _py_str se não existe ──────────
    if 'sem_py_str' in erros or not '_py_str' in code:
        py_str_fn = '''
def _py_str(v) -> str:
    """Converte valor para string Python sem \\\\uXXXX escapes."""
    if not isinstance(v, str):
        return repr(v)
    import json as _j
    s = _j.dumps(v, ensure_ascii=False)
    if '"' not in v and '\\\\' not in v:
        return "'" + v.replace("'", "\\\\'") + "'"
    return s


'''
        # Insere antes de class TranspiladorPython
        anchor = 'class TranspiladorPython:'
        if anchor in code:
            code = code.replace(anchor, py_str_fn + anchor, 1)
            print("  ✅ _py_str() adicionada")
            modificado = True

    # ── Correção 2: String transpiler usa _py_str ───────────
    old_repr = "        elif t == 'string':\n            return repr(node['value'])"
    new_repr = "        elif t == 'string':\n            return _py_str(node['value'])"
    if old_repr in code:
        code = code.replace(old_repr, new_repr)
        print("  ✅ String transpiler corrigido")
        modificado = True
    elif 'repr_em_string' in erros:
        # Busca e corrige variações
        code = re.sub(
            r"(elif t == 'string':\s+)return repr\(node\['value'\]\)",
            r"\1return _py_str(node['value'])",
            code
        )
        print("  ✅ String transpiler corrigido (regex)")
        modificado = True

    # ── Correção 3: Remove _decode_escapes inteiro ───────────
    if '_decode_escapes' in code:
        # Remove o bloco completo entre "# Decode any" e a linha do write
        padrao = (
            r'# Decode any.*?'
            r'cython_code = _decode_escapes\(cython_code\)\n\s*'
        )
        novo_code = re.sub(padrao, '', code, flags=re.DOTALL)
        if novo_code != code:
            code = novo_code
            print("  ✅ _decode_escapes removido")
            modificado = True
        else:
            # Tenta remover linha por linha
            linhas = code.split('\n')
            novas = []
            skip = False
            for l in linhas:
                if '# Decode any' in l or '# decode any' in l.lower():
                    skip = True
                if '_decode_escapes(cython_code)' in l:
                    skip = False
                    continue  # Remove esta linha
                if not skip:
                    novas.append(l)
                elif 'with open(pyx_path' in l:
                    skip = False
                    novas.append(l)
            code = '\n'.join(novas)
            if '_decode_escapes' not in code:
                print("  ✅ _decode_escapes removido (linha a linha)")
                modificado = True
            else:
                print("  ⚠️  _decode_escapes ainda presente — remoção manual necessária")

    # ── Salva ────────────────────────────────────────────────
    if modificado:
        # Backup
        backup = ARQUIVO + '.backup'
        with open(ARQUIVO, 'r', encoding='utf-8') as f:
            orig = f.read()
        with open(backup, 'w', encoding='utf-8') as f:
            f.write(orig)
        print(f"  💾 Backup: {backup}")

        with open(ARQUIVO, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"  💾 Salvo: {ARQUIVO}")
    else:
        print("  Nenhuma correção automática necessária")

    return code


def verificar_final():
    print()
    print("=" * 54)
    print("  VERIFICAÇÃO FINAL")
    print("=" * 54)

    # Recarrega o módulo
    if 'advak_nativo' in sys.modules:
        del sys.modules['advak_nativo']

    try:
        from advak_nativo import TranspiladorPython
        tp = TranspiladorPython()

        # Teste 1: string com unicode
        node = {'type': 'string', 'value': '✅ Razão Áurea (φ) ═══ \u2705'}
        resultado = tp._transpilar_expr(node)
        escapes = re.findall(r'\\[uU][0-9a-fA-F]{4}', resultado)
        if escapes:
            print(f"  ❌ AINDA gera escapes: {resultado!r}")
            return False
        print(f"  ✅ String unicode: {resultado}")

        # Teste 2: transpila fibonacci.dk
        arq = os.path.join(os.path.dirname(ARQUIVO), 'projetos', 'fibonacci.dk')
        if os.path.exists(arq):
            import py_compile, tempfile
            code_dk = open(arq, encoding='utf-8').read()
            py = tp.transpilar(code_dk, 'fibonacci')
            escapes_py = re.findall(r'\\[uU][0-9a-fA-F]{4}', py)
            with tempfile.NamedTemporaryFile(suffix='.py', mode='w',
                                              encoding='utf-8', delete=False) as f:
                f.write(py)
                tmp = f.name
            try:
                py_compile.compile(tmp, doraise=True)
                print(f"  ✅ fibonacci.dk → .py compila OK ({len(escapes_py)} escapes)")
                if escapes_py:
                    print(f"     ⚠️  Escapes encontrados: {escapes_py[:3]}")
                    return False
            except Exception as e:
                print(f"  ❌ fibonacci.dk compile error: {e}")
                return False
            finally:
                os.unlink(tmp)

        print()
        print("  🎉 CYTHON DEVE FUNCIONAR AGORA!")
        print("  Execute: python advak.py projetos\\testar_nuitka.dk")
        return True

    except Exception as e:
        print(f"  ❌ Erro ao importar: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║  ADVAK — Corretor de Bug Cython Unicode     ║")
    print("╚══════════════════════════════════════════════╝")

    erros, code, linhas = verificar()

    print()
    if not erros:
        print("  ✅ Nenhum bug encontrado!")
        print("  Se Cython ainda falha, o problema pode ser")
        print("  outro. Rode verificar_final() para confirmar.")
        verificar_final()
    else:
        print(f"  ❌ {len(erros)} problema(s) encontrado(s): {erros}")
        resp = input("\n  Corrigir automaticamente? (s/n): ").strip().lower()
        if resp == 's':
            code_corrigido = corrigir(erros, code)
            ok = verificar_final()
            if ok:
                print()
                print("  ✅ CORREÇÃO APLICADA COM SUCESSO!")
            else:
                print()
                print("  ⚠️  Correção parcial. Verifique manualmente.")
        else:
            print("  Correção cancelada.")
