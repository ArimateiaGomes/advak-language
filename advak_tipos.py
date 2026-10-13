"""
Advak — Tipagem opcional: conferência em tempo de execução do que foi anotado.

    seja idade: inteiro = 17
    seja apelido: texto? = nulo
    seja valor: inteiro | texto = "10"
    seja notas: lista[numero] = [7, 8.5]
    função somar(a: numero, b: numero = 0) -> numero { retornar a + b }

Código sem anotações não passa por aqui. Este módulo não depende do interpretador: ele recebe um
"contexto" que sabe reconhecer funções e tipos do usuário (classes, estruturas, enums).

Um tipo anotado é um dict:  {'alts': [{'nome': 'lista', 'args': [<tipo>] | None, 'nulavel': bool}, ...],
                             'texto': 'lista[numero]'}   (várias alternativas = união com |)
"""


class ErroTipo(ValueError):
    """Anotação inválida (por exemplo, nome de tipo desconhecido). Mensagem em português."""


# nome escrito pelo usuário → tipo básico canônico (sinônimos em inglês incluídos)
CANONICOS = {
    'inteiro': 'inteiro', 'int': 'inteiro', 'integer': 'inteiro',
    'numero': 'numero', 'número': 'numero', 'decimal': 'numero', 'flutuante': 'numero',
    'float': 'numero', 'number': 'numero',
    'texto': 'texto', 'string': 'texto', 'str': 'texto',
    'booleano': 'booleano', 'bool': 'booleano', 'boolean': 'booleano',
    'lista': 'lista', 'list': 'lista', 'array': 'lista',
    'mapa': 'mapa', 'objeto': 'mapa', 'dict': 'mapa', 'map': 'mapa',
    'funcao': 'funcao', 'função': 'funcao', 'function': 'funcao',
    'nulo': 'nulo', 'null': 'nulo',
    'qualquer': 'qualquer', 'any': 'qualquer',
}

DISPONIVEIS = ("inteiro, numero, texto, booleano, lista, mapa, funcao, nulo, qualquer "
               "(ou o nome de uma classe, estrutura ou enum), com ? para aceitar nulo, | para união "
               "e lista[tipo] / mapa[tipo]")


class ContextoTipos:
    """Contexto padrão (sem tipos do usuário). O interpretador fornece um com classes e enums."""

    def eh_funcao(self, valor):
        return callable(valor)

    def conhece(self, nome):
        return False

    def instancia_de(self, valor, nome):
        return False

    def nome_do_valor(self, valor):
        return type(valor).__name__


def _eh_numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def descrever_tipo(tipo):
    return tipo['texto']


def descrever_valor(valor, ctx=None):
    """Texto curto para as mensagens: texto ("abc"), inteiro (5), lista ([1, 2])..."""
    ctx = ctx or ContextoTipos()
    if valor is None:
        return 'nulo'
    if isinstance(valor, bool):
        return f"booleano ({'verdadeiro' if valor else 'falso'})"
    if isinstance(valor, int):
        return f"inteiro ({valor})"
    if isinstance(valor, float):
        return f"decimal ({valor})"
    if isinstance(valor, str):
        corte = valor if len(valor) <= 30 else valor[:30] + '…'
        return f'texto ("{corte}")'
    if isinstance(valor, (list, tuple)):
        s = repr(list(valor))
        return f"lista ({s if len(s) <= 40 else s[:40] + '…'})"
    if isinstance(valor, dict):
        s = repr(valor)
        return f"mapa ({s if len(s) <= 40 else s[:40] + '…'})"
    return ctx.nome_do_valor(valor)


def _valida_alt(alt, ctx):
    nome = alt['nome']
    canon = CANONICOS.get(nome)
    if canon is None:
        if not ctx.conhece(nome):
            raise ErroTipo(f"tipo desconhecido '{nome}'. Tipos disponíveis: {DISPONIVEIS}")
        if alt.get('args'):
            raise ErroTipo(f"o tipo '{nome}' não aceita [..]")
        return
    if alt.get('args'):
        if canon not in ('lista', 'mapa'):
            raise ErroTipo(f"o tipo '{nome}' não aceita [..]; só lista[tipo] e mapa[tipo]")
        for t in alt['args']:
            validar(t, ctx)


def validar(tipo, ctx):
    """Levanta ErroTipo se algum nome do tipo (ou de um tipo interno) for desconhecido."""
    for alt in tipo['alts']:
        _valida_alt(alt, ctx)


def _confere_alt(valor, alt, ctx):
    if valor is None and alt.get('nulavel'):
        return True
    canon = CANONICOS.get(alt['nome'])
    if canon is None:
        return ctx.instancia_de(valor, alt['nome'])
    if canon == 'qualquer':
        return True
    if canon == 'nulo':
        return valor is None
    if canon == 'inteiro':
        return isinstance(valor, int) and not isinstance(valor, bool)
    if canon == 'numero':
        return _eh_numero(valor)
    if canon == 'texto':
        return isinstance(valor, str)
    if canon == 'booleano':
        return isinstance(valor, bool)
    if canon == 'funcao':
        return ctx.eh_funcao(valor)
    if canon == 'lista':
        if not isinstance(valor, (list, tuple)):
            return False
        if alt.get('args'):
            interno = alt['args'][0]
            return all(confere(x, interno, ctx) for x in valor)
        return True
    if canon == 'mapa':
        if not isinstance(valor, dict):
            return False
        if alt.get('args'):
            interno = alt['args'][0]
            return all(confere(x, interno, ctx) for x in valor.values())
        return True
    return False


def confere(valor, tipo, ctx):
    return any(_confere_alt(valor, alt, ctx) for alt in tipo['alts'])


def verificar(valor, tipo, ctx):
    """True se `valor` combina com `tipo`. Levanta ErroTipo se a anotação tiver nome desconhecido."""
    validar(tipo, ctx)
    return confere(valor, tipo, ctx)
