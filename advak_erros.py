"""
Advak 5.0 — Sistema de Mensagens de Erro Ricas
Exibe erros com contexto de código, dicas e setas apontando o problema.
"""

# ── Dicas por tipo de erro ─────────────────────────────────────────────────────
DICAS = {
    # Variáveis
    "não definida": [
        "Use 'seja {var} = valor' para declarar variáveis",
        "Verifique se o nome está escrito corretamente",
        "Variáveis declaradas dentro de {{ }} não existem fora delas",
    ],
    "imutável": [
        "Use 'seja' em vez de 'fixo' se precisar mudar o valor",
        "'fixo' cria constantes que nunca podem ser reatribuídas",
    ],
    "não é uma função": [
        "Verifique se digitou o nome da função corretamente",
        "Talvez esteja faltando os parênteses: funcao() em vez de funcao",
        "Confirme se a função foi declarada antes de ser chamada",
    ],
    "índice": [
        "Listas começam no índice 0 (primeiro elemento é lista[0])",
        "Use lista.tamanho para saber o tamanho antes de acessar",
        "Índices negativos contam do final: lista[-1] é o último",
    ],
    "não é possível acessar": [
        "Verifique se o objeto tem essa propriedade",
        "Use tipo(objeto) para ver o tipo do valor",
    ],
    "tipo incompatível": [
        "Use texto(valor) para converter para texto",
        "Use numero(valor) para converter para número",
        "Não é possível somar texto com número diretamente",
    ],
    "divisão por zero": [
        "Verifique se o divisor pode ser zero",
        "Use uma condição: se (b != 0) { resultado = a / b }",
    ],
    "esperado": [
        "Verifique se fechou todos os parênteses, colchetes e chaves",
        "Pode estar faltando um operador entre os valores",
        "Verifique a sintaxe: seja, se, para, enquanto, função",
    ],
    "token inesperado": [
        "Verifique se não tem um caractere especial fora do lugar",
        "Confirme se as palavras-chave estão escritas corretamente",
        "Pode estar faltando um operador ou vírgula",
    ],
    "módulo não encontrado": [
        "Verifique o caminho do arquivo .dk",
        "O arquivo deve existir na pasta atual ou em projetos/",
        "Use: importar { funcao } de \"arquivo.dk\"",
    ],
    "recursão muito profunda": [
        "A função está chamando a si mesma sem parar",
        "Adicione um caso base: se (n <= 0) { retornar 0 }",
        "Exemplo correto: funcao f(n) { se(n<=0){retornar 0} retornar f(n-1)+1 }",
    ],
    "arquivo não encontrado": [
        "Verifique se o caminho do arquivo está correto",
        "Use Arquivo.listar() para ver os arquivos disponíveis",
        "Caminhos no Windows usam \\\\ ou / como separador",
    ],
    "permissão negada": [
        "O programa não tem permissão para acessar este arquivo",
        "Tente executar como administrador ou mude o local do arquivo",
    ],
    "tempo esgotado": [
        "O programa demorou mais de 30 segundos para responder",
        "Verifique se há loops infinitos no código",
        "Use quebrar para sair de loops quando necessário",
    ],
}

ERROS_COMUNS = {
    "imprimir x": "Faltou parênteses: use imprimir(x)",
    "seja x == 5": "Use = para atribuir, == para comparar: seja x = 5",
    "funcao sem ()": "Para chamar uma função use: nome()",
}


def _cor(texto, codigo):
    """Adiciona cor ANSI se o terminal suportar."""
    try:
        import sys
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            return f"\033[{codigo}m{texto}\033[0m"
    except Exception:
        pass
    return texto


def _vermelho(t):   return _cor(t, '91')
def _amarelo(t):    return _cor(t, '93')
def _azul(t):       return _cor(t, '94')
def _ciano(t):      return _cor(t, '96')
def _cinza(t):      return _cor(t, '90')
def _negrito(t):    return _cor(t, '1')
def _verde(t):      return _cor(t, '92')


def _encontrar_dica(msg):
    """Encontra a dica mais relevante para a mensagem de erro."""
    msg_lower = msg.lower()
    for chave, dicas in DICAS.items():
        if chave.lower() in msg_lower:
            return dicas
    return []


def _extrair_linha(msg):
    """Extrai o número de linha da mensagem de erro."""
    import re
    # "linha 5" ou "Linha 5" ou "(linha 5)"
    m = re.search(r'[Ll]inha\s+(\d+)', msg)
    if m:
        return int(m.group(1))
    # "[Advak] Linha 5:"
    m = re.search(r'\[Advak\]\s+Linha\s+(\d+)', msg)
    if m:
        return int(m.group(1))
    return None


def _extrair_var(msg):
    """Extrai nome da variável do erro."""
    import re
    m = re.search(r"'([^']+)'\s+não", msg)
    if m:
        return m.group(1)
    return None


def _mostrar_contexto(source, linha, cols=None):
    """Mostra as linhas ao redor do erro com destaque."""
    if not source or not linha:
        return
    linhas = source.split('\n')
    n = len(linhas)
    inicio = max(0, linha - 3)
    fim    = min(n, linha + 2)

    print()
    for i in range(inicio, fim):
        num = i + 1
        conteudo = linhas[i]
        prefixo = f"  {num:4} │ "
        if num == linha:
            # Linha com erro — destaca em vermelho
            print(_vermelho(f"→ {num:4} │ ") + _vermelho(conteudo))
            # Seta apontando para o erro
            indent = " " * (len(prefixo) + 2)
            print(_vermelho(f"       │ {'↑' * max(1, len(conteudo.strip()))}"))
        else:
            print(_cinza(prefixo) + _cinza(conteudo))


def exibir_erro_sintaxe(msg, source=None):
    """Exibe erro de sintaxe formatado."""
    import re

    print()
    print(_vermelho(_negrito("╔══════════════════════════════════════════╗")))
    print(_vermelho(_negrito("║        ❌  ERRO DE SINTAXE               ║")))
    print(_vermelho(_negrito("╚══════════════════════════════════════════╝")))

    # Extrai linha e mensagem limpa
    linha = _extrair_linha(msg)

    # Remove prefixo [Advak] Linha X:
    msg_limpa = re.sub(r'\[Advak\]\s+Linha\s+\d+:\s*', '', msg).strip()
    msg_limpa = re.sub(r'\(linha \d+\)', '', msg_limpa).strip()

    if linha:
        print(f"\n  {_amarelo('📍 Localização:')} linha {_negrito(str(linha))}")
    print(f"  {_vermelho('💬 Problema:')}    {msg_limpa}")

    # Contexto do código
    if source and linha:
        print(f"\n  {_azul('📄 Código:')}")
        _mostrar_contexto(source, linha)

    # Dicas
    dicas = _encontrar_dica(msg_limpa)
    if dicas:
        print(f"\n  {_verde('💡 Dicas:')}")
        for dica in dicas[:2]:
            var = _extrair_var(msg_limpa)
            dica_fmt = dica.replace('{var}', var or 'variavel')
            print(f"     • {dica_fmt}")

    print()


def exibir_erro_advak(msg, source=None):
    """Exibe AdvakError formatado."""
    import re

    print()
    print(_vermelho(_negrito("╔══════════════════════════════════════════╗")))
    print(_vermelho(_negrito("║        ❌  ERRO DE EXECUÇÃO              ║")))
    print(_vermelho(_negrito("╚══════════════════════════════════════════╝")))

    # Extrai linha
    linha = _extrair_linha(msg)

    # Se não tem linha, tenta encontrar no source pela variável/função do erro
    if not linha and source:
        var = _extrair_var(msg)
        if var:
            linhas = source.split('\n')
            for i, l in enumerate(linhas, 1):
                if var in l:
                    linha = i

    # Remove sufixo de linha da mensagem
    msg_limpa = re.sub(r'\s*\(linha \d+\)', '', msg).strip()

    if linha:
        print(f"\n  {_amarelo('📍 Localização:')} linha {_negrito(str(linha))}")
    print(f"  {_vermelho('💬 Problema:')}    {msg_limpa}")

    # Contexto
    if source and linha:
        print(f"\n  {_azul('📄 Código:')}")
        _mostrar_contexto(source, linha)

    # Dicas
    dicas = _encontrar_dica(msg_limpa)
    if dicas:
        print(f"\n  {_verde('💡 Dicas:')}")
        for dica in dicas[:2]:
            var = _extrair_var(msg_limpa)
            dica_fmt = dica.replace('{var}', var or 'variavel')
            print(f"     • {dica_fmt}")

    print()


def exibir_erro_interno(tipo, msg, source=None, debug=False):
    """Exibe erro interno/inesperado."""
    print()
    print(_vermelho(_negrito("╔══════════════════════════════════════════╗")))
    print(_vermelho(_negrito("║        ⚠️  ERRO INESPERADO               ║")))
    print(_vermelho(_negrito("╚══════════════════════════════════════════╝")))
    print(f"\n  {_vermelho('💬 Tipo:')}    {tipo}")
    print(f"  {_vermelho('💬 Detalhe:')} {msg[:100]}")

    if not debug:
        print(f"\n  {_cinza('Dica: defina ADVAK_DEBUG=1 para ver o traceback completo')}")
    print()
