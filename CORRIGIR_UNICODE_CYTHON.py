#!/usr/bin/env python3
"""
CORRIGIR_UNICODE_CYTHON.py
Correcao cirurgica do bug de unicode no Cython.

Execute: python CORRIGIR_UNICODE_CYTHON.py
Nao precisa baixar nenhum ZIP. Corrige o arquivo diretamente.
"""
import os, sys, re, shutil

ARQUIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'advak_nativo.py')

def main():
    print()
    print("=" * 56)
    print("  ADVAK 5.0 — Correcao Cython Unicode")
    print("=" * 56)

    if not os.path.exists(ARQUIVO):
        print(f"  ERRO: {ARQUIVO} nao encontrado!")
        sys.exit(1)

    with open(ARQUIVO, 'r', encoding='utf-8') as f:
        codigo = f.read()

    print(f"  Arquivo: {ARQUIVO}")
    print()

    modificado = False

    # ─────────────────────────────────────────────────────────────
    # PASSO 1: Garante que _py_str() existe e funciona corretamente
    # ─────────────────────────────────────────────────────────────
    PY_STR_CORRETO = '''def _py_str(v) -> str:
    """Converte para string Python sem \\\\uXXXX escapes (seguro para Cython)."""
    if not isinstance(v, str):
        return repr(v)
    import json as _j
    # json.dumps com ensure_ascii=False mantem unicode real, nunca \\\\uXXXX
    s = _j.dumps(v, ensure_ascii=False)
    # Converte aspas duplas -> simples quando possivel
    if '"' not in v and '\\\\' not in v:
        return "'" + v.replace("'", "\\\\'") + "'"
    return s
'''

    if '_py_str' not in codigo:
        # Insere antes de class TranspiladorPython
        anchor = 'class TranspiladorPython:'
        if anchor in codigo:
            codigo = codigo.replace(anchor, PY_STR_CORRETO + '\n\n' + anchor, 1)
            print("  [1] ✅ _py_str() adicionada")
            modificado = True
        else:
            print("  [1] ❌ Nao encontrei 'class TranspiladorPython' — insercao manual necessaria")
    else:
        # Verifica se a versao existente usa ensure_ascii=False
        idx = codigo.find('def _py_str')
        trecho = codigo[idx:idx+400]
        if 'ensure_ascii=False' in trecho:
            print("  [1] ✅ _py_str() correta ja existe")
        else:
            # Substitui pela versao correta
            fim = codigo.find('\n\n', idx + 50)
            if fim == -1:
                fim = codigo.find('\nclass ', idx)
            if fim > idx:
                codigo = codigo[:idx] + PY_STR_CORRETO + codigo[fim:]
                print("  [1] ✅ _py_str() atualizada para versao correta")
                modificado = True

    # ─────────────────────────────────────────────────────────────
    # PASSO 2: String transpiler usa _py_str() em vez de repr()
    # ─────────────────────────────────────────────────────────────
    padroes_repr = [
        # Padrao mais comum
        (r"elif t == 'string':\s+return repr\(node\['value'\]\)",
         "elif t == 'string':\n            return _py_str(node['value'])"),
        # Variacao com aspas duplas
        (r'elif t == "string":\s+return repr\(node\["value"\]\)',
         "elif t == 'string':\n            return _py_str(node['value'])"),
    ]
    for padrao, substituto in padroes_repr:
        novo = re.sub(padrao, substituto, codigo)
        if novo != codigo:
            codigo = novo
            print("  [2] ✅ String transpiler corrigido para _py_str()")
            modificado = True
            break
    else:
        if "_py_str(node['value'])" in codigo or '_py_str(node["value"])' in codigo:
            print("  [2] ✅ String transpiler ja usa _py_str()")
        else:
            print("  [2] ⚠️  String transpiler — padrao nao encontrado, verificar manualmente")

    # ─────────────────────────────────────────────────────────────
    # PASSO 3: Remove QUALQUER _decode_escapes do arquivo
    # ─────────────────────────────────────────────────────────────
    if '_decode_escapes' in codigo:
        linhas = codigo.split('\n')
        novas_linhas = []
        pular = False
        removidas = 0

        for i, linha in enumerate(linhas):
            # Detecta inicio do bloco _decode_escapes
            if ('def _decode_escapes' in linha or
                '# Decode any' in linha or
                '# decode any' in linha.lower() or
                'encode(\'raw_unicode_escape\')' in linha or
                'encode("raw_unicode_escape")' in linha):
                pular = True

            if pular:
                removidas += 1
                # Para de pular quando encontra a linha de escrita do pyx
                if 'with open(pyx_path' in linha:
                    pular = False
                    novas_linhas.append(linha)  # Mantem a linha do open
                elif '_decode_escapes(cython_code)' in linha:
                    pass  # Remove esta linha
                continue

            novas_linhas.append(linha)

        codigo_novo = '\n'.join(novas_linhas)

        if '_decode_escapes' not in codigo_novo:
            codigo = codigo_novo
            print(f"  [3] ✅ _decode_escapes removido ({removidas} linhas)")
            modificado = True
        else:
            # Tenta remover apenas a chamada
            codigo_temp = re.sub(
                r'\s*cython_code\s*=\s*_decode_escapes\(cython_code\)\s*\n',
                '\n', codigo
            )
            # Remove a definicao da funcao
            codigo_temp = re.sub(
                r'\s*def _decode_escapes\(s\):.*?return s\s*\n',
                '\n', codigo_temp, flags=re.DOTALL
            )
            if '_decode_escapes' not in codigo_temp:
                codigo = codigo_temp
                print("  [3] ✅ _decode_escapes removido (regex)")
                modificado = True
            else:
                print("  [3] ⚠️  _decode_escapes ainda presente — remova manualmente as linhas:")
                for i, l in enumerate(codigo.split('\n'), 1):
                    if '_decode_escapes' in l:
                        print(f"         Linha {i}: {l.strip()}")
    else:
        print("  [3] ✅ _decode_escapes nao existe (OK)")

    # ─────────────────────────────────────────────────────────────
    # PASSO 4: Garante que .pyx e escrito direto sem transformacao
    # ─────────────────────────────────────────────────────────────
    if 'raw_unicode_escape' in codigo:
        codigo = re.sub(
            r'try:\s+cython_code = cython_code\.encode\([\'"]raw_unicode_escape[\'"]\).*?except Exception:\s+pass\s*\n',
            '',
            codigo,
            flags=re.DOTALL
        )
        if 'raw_unicode_escape' not in codigo:
            print("  [4] ✅ encode raw_unicode_escape removido")
            modificado = True
        else:
            print("  [4] ⚠️  raw_unicode_escape ainda presente")
    else:
        print("  [4] ✅ Sem encode problematico")

    # ─────────────────────────────────────────────────────────────
    # SALVA E TESTA
    # ─────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────
    # PASSO 5: Corrige backslash do Windows no SETUP_TEMPLATE
    # ─────────────────────────────────────────────────────────────
    OLD_SETUP = "                f.write(self.SETUP_TEMPLATE.format(\n                    nome=nome, pyx_path=pyx_path\n                ))"
    NEW_SETUP = "                # Windows: backslash em paths causa erro \\U no setup.py\n                safe_path = pyx_path.replace('\\\\', '/')\n                f.write(self.SETUP_TEMPLATE.format(\n                    nome=nome, pyx_path=safe_path\n                ))"
    if OLD_SETUP in codigo:
        codigo = codigo.replace(OLD_SETUP, NEW_SETUP)
        print("  [5] ✅ Windows path backslash corrigido no SETUP_TEMPLATE")
        modificado = True
    elif 'safe_path' in codigo:
        print("  [5] ✅ Windows path fix ja aplicado")
    else:
        print("  [5] ⚠️  Padrao SETUP_TEMPLATE nao encontrado")

    if modificado:
        backup = ARQUIVO + '.bak'
        shutil.copy2(ARQUIVO, backup)
        print(f"\n  💾 Backup salvo: {backup}")

        with open(ARQUIVO, 'w', encoding='utf-8') as f:
            f.write(codigo)
        print(f"  💾 Arquivo corrigido: {ARQUIVO}")
    else:
        print("\n  ℹ️  Nenhuma modificacao necessaria")

    # ─────────────────────────────────────────────────────────────
    # TESTE FINAL
    # ─────────────────────────────────────────────────────────────
    print()
    print("=" * 56)
    print("  TESTE FINAL")
    print("=" * 56)

    # Recarrega modulo
    for mod in list(sys.modules.keys()):
        if 'advak_nativo' in mod:
            del sys.modules[mod]

    try:
        sys.path.insert(0, os.path.dirname(ARQUIVO))
        from advak_nativo import TranspiladorPython

        tp = TranspiladorPython()

        # Teste com unicode
        strings_teste = [
            '✅ Resultados identicos!',
            'Razao Aurea (phi)',
            '─── Secao 1 ───',
            '╔══════════════╗',
        ]
        print("  Testando _py_str():")
        erros = 0
        for s in strings_teste:
            node = {'type': 'string', 'value': s}
            resultado = tp._transpilar_expr(node)
            has_escape = bool(re.search(r'\\[uU][0-9a-fA-F]{4}', resultado))
            if has_escape:
                print(f"  ❌ Escape encontrado: {resultado!r}")
                erros += 1
            else:
                print(f"  ✅ OK: {resultado!r}")

        # Transpila fibonacci.dk
        arq_fib = os.path.join(os.path.dirname(ARQUIVO), 'projetos', 'fibonacci.dk')
        if os.path.exists(arq_fib):
            code_dk = open(arq_fib, encoding='utf-8').read()
            py = tp.transpilar(code_dk, 'fibonacci')
            escapes = re.findall(r'\\[uU][0-9a-fA-F]{4}', py)
            if escapes:
                print(f"\n  ❌ fibonacci.dk ainda tem {len(escapes)} escapes!")
                erros += 1
            else:
                print(f"\n  ✅ fibonacci.dk → 0 escapes unicode!")

            # Testa compilacao Python
            import py_compile, tempfile
            with tempfile.NamedTemporaryFile(suffix='.py', mode='w',
                                              encoding='utf-8', delete=False) as f:
                f.write(py)
                tmp = f.name
            try:
                py_compile.compile(tmp, doraise=True)
                print("  ✅ Compila para bytecode sem erros!")
            except Exception as e:
                print(f"  ❌ Erro de compilacao: {e}")
                erros += 1
            finally:
                try: os.unlink(tmp)
                except: pass

        print()
        if erros == 0:
            print("  🎉 SUCESSO! Cython deve funcionar agora.")
            print()
            print("  Execute:")
            print("    python advak.py projetos\\testar_nuitka.dk")
        else:
            print(f"  ⚠️  {erros} problema(s) restante(s).")
            print("  Tente baixar o ZIP mais recente.")

    except Exception as e:
        print(f"  ❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

    print()

if __name__ == '__main__':
    main()
