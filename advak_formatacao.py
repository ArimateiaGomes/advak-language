"""
Advak — Interpolação com formatação:  `Total: ${preco:moeda}`  `Hoje: ${hoje:dd/mm/aaaa}`

Módulo sem dependências e sem rede. O interpretador usa:
    dividir_template(texto)         → [('t', texto), ('e', 'expr[:formato]'), ...]
    separar_formato(expr)           → (expr, formato | None)
    formatar_valor(valor, formato, para_texto) → texto formatado

Formatos com nome (sinônimo em inglês entre parênteses):
    moeda (currency)[.N]   numero (number)[.N]   porcentagem (pct, percent)[.N]
    maiusculo (upper)   minusculo (lower)   titulo (title)
    data (date)   hora (time)   datahora (datetime)
Padrão de data:  aaaa/yyyy  aa/yy  mmmm  mmm  mm  dd  dddd  ddd  hh  ss   ([texto literal])
Estilo Python:   .2f  ,.2f  05d  >10  <10  ^10  *^20  +.1f  x  .1%

Todo formato numérico usa os separadores do Brasil (vírgula decimal, ponto de milhar).
"""

import re
import datetime
from decimal import Decimal, Context, ROUND_HALF_UP, InvalidOperation


class ErroFormato(ValueError):
    """Formato inválido ou incompatível com o valor (mensagem em português)."""


MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro',
         'outubro', 'novembro', 'dezembro']
MESES_ABREV = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
DIAS = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
DIAS_ABREV = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom']


# ══════════════════════════════════════════════════════════════════════════════
#  Leitura do template: ${ ... } com chaves aninhadas e textos entre aspas
# ══════════════════════════════════════════════════════════════════════════════

def _achar_fim(s, j):
    """Índice do '}' que fecha um '${' cujo conteúdo começa em s[j]; -1 se não fechar."""
    profundidade = 1
    n = len(s)
    while j < n:
        c = s[j]
        if c in ('"', "'", '`'):
            aspa = c
            j += 1
            while j < n and s[j] != aspa:
                j += 2 if s[j] == '\\' else 1
            j += 1
            continue
        if c == '{':
            profundidade += 1
        elif c == '}':
            profundidade -= 1
            if profundidade == 0:
                return j
        j += 1
    return -1


def dividir_template(tmpl):
    """Divide o texto do template em partes de texto ('t') e expressões ('e')."""
    partes, buf = [], []
    i, n = 0, len(tmpl)
    while i < n:
        if tmpl.startswith('${', i):
            fim = _achar_fim(tmpl, i + 2)
            if fim == -1:                         # sem fechamento: o resto fica como texto
                buf.append(tmpl[i:])
                break
            conteudo = tmpl[i + 2:fim]
            if not conteudo.strip():              # ${} vazio continua literal
                buf.append(tmpl[i:fim + 1])
            else:
                if buf:
                    partes.append(('t', ''.join(buf)))
                    buf = []
                partes.append(('e', conteudo))
            i = fim + 1
        else:
            buf.append(tmpl[i])
            i += 1
    if buf:
        partes.append(('t', ''.join(buf)))
    return partes


def separar_formato(conteudo):
    """
    Separa 'expr:formato'. O ':' do formato é o primeiro que está fora de (), [], {}, textos
    e que não pertence a um ternário (a ? b : c). Sem formato devolve (conteudo, None).
    """
    profundidade = 0
    ternarios = 0
    i, n = 0, len(conteudo)
    while i < n:
        c = conteudo[i]
        if c in ('"', "'", '`'):
            aspa = c
            i += 1
            while i < n and conteudo[i] != aspa:
                i += 2 if conteudo[i] == '\\' else 1
            i += 1
            continue
        if c in '([{':
            profundidade += 1
        elif c in ')]}':
            profundidade -= 1
        elif profundidade == 0:
            if c == '?':
                proximo = conteudo[i + 1] if i + 1 < n else ''
                if proximo in ('?', '.'):          # ?? e ?.  não são ternário
                    i += 2
                    continue
                ternarios += 1
            elif c == ':':
                if ternarios > 0:
                    ternarios -= 1
                else:
                    formato = conteudo[i + 1:].strip()
                    if not formato:
                        raise ErroFormato("o formato depois de ':' está vazio")
                    return conteudo[:i], formato
        i += 1
    return conteudo, None


def proteger_literais(linha, dentro_template=False):
    """
    Troca textos ("..." '...' `...`) e comentários (// ...) de UMA linha por marcadores \\x00N\\x00, para
    ferramentas (formatador, verificador) não mexerem no que está dentro deles.
    Devolve (linha_protegida, literais, template_aberto_no_fim). Com dentro_template=True a linha começa
    no meio de um texto de crase de várias linhas.
    """
    saida, lits = [], []
    i, n = 0, len(linha)
    aberto = False
    if dentro_template:
        j = i
        while j < n and linha[j] != '`':
            j += 2 if linha[j] == '\\' else 1
        if j >= n:
            return '\x000\x00', [linha], True
        lits.append(linha[:j + 1])
        saida.append('\x000\x00')
        i = j + 1
    while i < n:
        c = linha[i]
        if c in '"\'`':
            j = i + 1
            while j < n and linha[j] != c:
                j += 2 if linha[j] == '\\' else 1
            fechou = j < n
            j = min(j + 1, n)
            lits.append(linha[i:j])
            saida.append(f'\x00{len(lits) - 1}\x00')
            aberto = (c == '`' and not fechou)
            i = j
            continue
        if c == '/' and linha[i:i + 2] == '//':
            resto = linha[i + 2:].lstrip()
            divisao = bool(''.join(saida).strip()) and resto[:1] in tuple('0123456789(-+') and resto[:1] != ''
            if not divisao:                                 # comentário até o fim da linha
                lits.append(linha[i:])
                saida.append(f'\x00{len(lits) - 1}\x00')
                break
        saida.append(c)
        i += 1
    return ''.join(saida), lits, aberto


def restaurar_literais(linha, lits):
    return re.sub(r'\x00(\d+)\x00', lambda m: lits[int(m.group(1))], linha)


# ══════════════════════════════════════════════════════════════════════════════
#  Números (separadores do Brasil, arredondamento "escolar": 0,5 sobe)
# ══════════════════════════════════════════════════════════════════════════════

def _eh_numero(v):
    return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)


def _exigir_numero(v, formato):
    if not _eh_numero(v):
        raise ErroFormato(f"'{formato}' precisa de um número, mas o valor é "
                          f"{'booleano' if isinstance(v, bool) else 'do tipo ' + _nome_tipo(v)}")
    return v


def _nome_tipo(v):
    if isinstance(v, str):
        return 'texto'
    if isinstance(v, list):
        return 'lista'
    if isinstance(v, dict):
        return 'mapa'
    return type(v).__name__


def _decimal(v):
    try:
        d = v if isinstance(v, Decimal) else Decimal(str(v))
    except InvalidOperation:
        raise ErroFormato(f"não consegui converter {v!r} em número")
    if not d.is_finite():
        raise ErroFormato(f"o valor {v!r} não é um número finito")
    return d


_CTX = Context(prec=80)                       # números grandes sem estourar a precisão padrão (28)


def _arredondar(v, casas):
    d = _decimal(v)
    return d.quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP, context=_CTX)


def _trocar_separadores(texto):
    """1,234.50 (Python) → 1.234,50 (Brasil)."""
    return texto.replace(',', '\0').replace('.', ',').replace('\0', '.')


def _agrupado_ptbr(d, casas):
    """Decimal já arredondado → '1.234,50' (com sinal)."""
    return _trocar_separadores(f"{d:,.{casas}f}")


def _arg_casas(arg, formato, padrao):
    if arg == '':
        return padrao
    if not arg.isdigit() or int(arg) > 20:
        raise ErroFormato(f"'{formato}.{arg}': depois do ponto use o número de casas decimais (0 a 20)")
    return int(arg)


def _fmt_moeda(v, arg):
    _exigir_numero(v, 'moeda')
    casas = _arg_casas(arg, 'moeda', 2)
    d = _arredondar(v, casas)
    sinal = '-' if d < 0 else ''
    return f"{sinal}R$ {_agrupado_ptbr(abs(d), casas)}"


def _fmt_numero(v, arg):
    _exigir_numero(v, 'numero')
    if arg != '':
        casas = _arg_casas(arg, 'numero', 0)
        return _agrupado_ptbr(_arredondar(v, casas), casas)
    d = _decimal(v)
    if d == d.to_integral_value():
        return _trocar_separadores(f"{int(d):,}")
    d = _arredondar(d, 6) if -d.as_tuple().exponent > 6 else d
    casas = max(0, -d.normalize(_CTX).as_tuple().exponent)
    return _agrupado_ptbr(d, casas)


def _fmt_porcentagem(v, arg):
    """Igual à função porcentagem(): valores de 0 a 1 são tratados como fração (0.75 → 75%)."""
    _exigir_numero(v, 'porcentagem')
    casas = _arg_casas(arg, 'porcentagem', 0)
    d = _decimal(v)
    if Decimal(0) <= d <= Decimal(1):
        d = d * 100
    return _agrupado_ptbr(_arredondar(d, casas), casas) + '%'


def _texto(v, para_texto):
    return v if isinstance(v, str) else para_texto(v)


# ── estilo Python ($ .2f, 05d, >10 ...) ──────────────────────────────────────

_RE_PY = re.compile(r'^(?:(?P<fill>.)?(?P<align>[<>=^]))?(?P<sign>[+\- ])?(?P<alt>#)?(?P<zero>0)?'
                    r'(?P<width>\d+)?(?P<group>[,_])?(?:\.(?P<prec>\d+))?(?P<type>[bcdeEfFgGnosxX%])?$')


def _eh_estilo_python(spec):
    return bool(spec) and _RE_PY.match(spec) is not None


def _formatar_python(valor, spec, para_texto):
    m = _RE_PY.match(spec)
    g = m.groupdict()
    fill, align = g['fill'] or ' ', g['align']
    largura = int(g['width']) if g['width'] else 0
    tipo = g['type']
    if g['zero'] and not align:
        fill, align = '0', '='

    if not _eh_numero(valor):
        if isinstance(valor, bool) and (tipo or g['sign'] or g['group']):
            raise ErroFormato(f"'{spec}' precisa de um número, mas o valor é booleano")
        if tipo not in (None, 's') or g['sign'] or g['group'] or g['alt'] or g['zero']:
            raise ErroFormato(f"'{spec}' precisa de um número, mas o valor é do tipo {_nome_tipo(valor)}")
        texto = _texto(valor, para_texto)
        if g['prec']:
            texto = texto[:int(g['prec'])]
        return _preencher(texto, largura, fill, align or '<')

    # número: formata o "miolo" sem preenchimento, troca os separadores e preenche depois
    prec = int(g['prec']) if g['prec'] is not None else None
    valor_fmt = valor
    if tipo in ('f', 'F') and prec is not None:
        valor_fmt = _arredondar(valor, prec)                              # 0,5 sobe (arredondamento escolar)
    elif tipo == '%' and prec is not None:
        valor_fmt = _arredondar(_decimal(valor) * 100, prec) / 100         # o Python multiplica por 100 de novo
    miolo = (g['sign'] or '') + (g['alt'] or '') + (g['group'] or '') + \
        (f".{prec}" if prec is not None else '') + (tipo or '')
    try:
        texto = format(valor_fmt, miolo)
    except (ValueError, TypeError):
        if tipo in ('d', 'b', 'o', 'x', 'X', 'c') and isinstance(valor, (float, Decimal)):
            raise ErroFormato(f"o formato '{tipo}' só vale para números inteiros (o valor é decimal)")
        raise ErroFormato(f"o formato '{spec}' não vale para este número")
    if tipo not in ('b', 'o', 'x', 'X', 'c'):
        texto = _trocar_separadores(texto)
    return _preencher(texto, largura, fill, align or '>')


def _preencher(texto, largura, fill, align):
    falta = largura - len(texto)
    if falta <= 0:
        return texto
    if align == '<':
        return texto + fill * falta
    if align == '^':
        esq = falta // 2
        return fill * esq + texto + fill * (falta - esq)
    if align == '=':                                # preenche depois do sinal: -007
        sinal = texto[0] if texto and texto[0] in '+- ' else ''
        return sinal + fill * falta + texto[len(sinal):]
    return fill * falta + texto


# ══════════════════════════════════════════════════════════════════════════════
#  Datas e horas
# ══════════════════════════════════════════════════════════════════════════════

_RE_ISO = re.compile(r'^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{1,2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?)?'
                     r'(?:Z|[+-]\d{2}:?\d{2})?$')
_RE_BR = re.compile(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?$')
_RE_HORA = re.compile(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$')


def _ler_data(valor):
    """→ (datetime, tem_data, tem_hora). Aceita texto (ISO, dd/mm/aaaa, hh:mm) e date/datetime/time."""
    if isinstance(valor, datetime.datetime):
        return valor, True, True
    if isinstance(valor, datetime.date):
        return datetime.datetime(valor.year, valor.month, valor.day), True, False
    if isinstance(valor, datetime.time):
        return datetime.datetime(1900, 1, 1, valor.hour, valor.minute, valor.second), False, True
    if not isinstance(valor, str):
        raise ErroFormato(f"formato de data precisa de uma data (texto como \"2024-12-25\" ou \"25/12/2024\"), "
                          f"mas o valor é {'booleano' if isinstance(valor, bool) else 'do tipo ' + _nome_tipo(valor)}")
    t = valor.strip()
    try:
        m = _RE_ISO.match(t)
        if m:
            a, me, d, h, mi, s = m.groups()
            return (datetime.datetime(int(a), int(me), int(d), int(h or 0), int(mi or 0), int(s or 0)),
                    True, h is not None)
        m = _RE_BR.match(t)
        if m:
            d, me, a, h, mi, s = m.groups()
            return (datetime.datetime(int(a), int(me), int(d), int(h or 0), int(mi or 0), int(s or 0)),
                    True, h is not None)
        m = _RE_HORA.match(t)
        if m:
            h, mi, s = m.groups()
            return datetime.datetime(1900, 1, 1, int(h), int(mi), int(s or 0)), False, True
    except ValueError:
        raise ErroFormato(f"\"{valor}\" não é uma data válida")
    raise ErroFormato(f"não reconheci \"{valor}\" como data. Use \"2024-12-25\", \"25/12/2024\" ou \"14:30\"")


_TOKENS = ['aaaa', 'yyyy', 'mmmm', 'dddd', 'mmm', 'ddd', 'aa', 'yy', 'mm', 'dd', 'hh', 'ss']
_RE_TOKEN_DATA = re.compile(r'aaaa|yyyy|mmmm|dddd|mmm|ddd|aa|yy|mm|dd|hh|ss', re.IGNORECASE)


def _eh_padrao_data(spec):
    return bool(_RE_TOKEN_DATA.search(re.sub(r'\[[^\]]*\]', '', spec)))


def _tokenizar_data(padrao):
    """Divide o padrão em ('lit', texto) e ('tok', nome); 'mm' vira 'min' quando são minutos."""
    itens = []
    i, n = 0, len(padrao)
    while i < n:
        if padrao[i] == '[':
            fim = padrao.find(']', i)
            if fim == -1:
                raise ErroFormato("falta fechar o colchete ']' no padrão de data")
            itens.append(('lit', padrao[i + 1:fim]))
            i = fim + 1
            continue
        achou = None
        for t in _TOKENS:
            if padrao[i:i + len(t)].lower() == t:
                achou = t
                break
        if achou is None:
            itens.append(('lit', padrao[i]))
            i += 1
            continue
        nome = {'yyyy': 'aaaa', 'yy': 'aa'}.get(achou, achou)
        if nome == 'mm':
            # minutos: o token anterior (pulando um separador curto como ':', 'h' ou ' ') é 'hh'
            depois_de_hora = False
            soma_literal = 0
            for tipo_ant, valor_ant in reversed(itens):
                if tipo_ant == 'lit':
                    soma_literal += len(valor_ant)
                    if soma_literal > 3:
                        break
                    continue
                depois_de_hora = valor_ant == 'hh'
                break
            antes_de_segundo = padrao[i + 2:i + 5].lower() == ':ss'
            if depois_de_hora or antes_de_segundo:
                nome = 'min'
        itens.append(('tok', nome))
        i += len(achou)
    return itens


_PRECISA_DATA = {'aaaa', 'aa', 'mmmm', 'mmm', 'mm', 'dd', 'dddd', 'ddd'}
_PRECISA_HORA = {'hh', 'min', 'ss'}


def _fmt_data(valor, padrao, formato):
    dt, tem_data, tem_hora = _ler_data(valor)
    itens = _tokenizar_data(padrao)
    nomes = {n for t, n in itens if t == 'tok'}
    if nomes & _PRECISA_DATA and not tem_data:
        raise ErroFormato(f"o formato '{formato}' precisa de uma data, mas o valor só tem hora")
    if nomes & _PRECISA_HORA and not tem_hora:
        raise ErroFormato(f"o formato '{formato}' precisa de hora, mas o valor só tem data "
                          "(use um valor com hora, como \"2024-12-25 14:30\")")
    saida = []
    for tipo, x in itens:
        if tipo == 'lit':
            saida.append(x)
        else:
            saida.append({
                'aaaa': f"{dt.year:04d}", 'aa': f"{dt.year % 100:02d}",
                'mmmm': MESES[dt.month - 1], 'mmm': MESES_ABREV[dt.month - 1], 'mm': f"{dt.month:02d}",
                'dd': f"{dt.day:02d}", 'dddd': DIAS[dt.weekday()], 'ddd': DIAS_ABREV[dt.weekday()],
                'hh': f"{dt.hour:02d}", 'min': f"{dt.minute:02d}", 'ss': f"{dt.second:02d}",
            }[x])
    return ''.join(saida)


# ══════════════════════════════════════════════════════════════════════════════
#  Entrada principal
# ══════════════════════════════════════════════════════════════════════════════

_NOMES_DATA = {'data': 'dd/mm/aaaa', 'date': 'dd/mm/aaaa', 'hora': 'hh:mm', 'time': 'hh:mm',
               'datahora': 'dd/mm/aaaa hh:mm', 'datetime': 'dd/mm/aaaa hh:mm'}
_NOMES_NUM = {'moeda': _fmt_moeda, 'currency': _fmt_moeda, 'numero': _fmt_numero, 'número': _fmt_numero,
              'number': _fmt_numero, 'porcentagem': _fmt_porcentagem, 'pct': _fmt_porcentagem,
              'percent': _fmt_porcentagem}
_NOMES_TEXTO = {'maiusculo': str.upper, 'maiúsculo': str.upper, 'upper': str.upper,
                'minusculo': str.lower, 'minúsculo': str.lower, 'lower': str.lower,
                'titulo': str.title, 'título': str.title, 'title': str.title}

DISPONIVEIS = ("moeda, numero, porcentagem (pct), maiusculo, minusculo, titulo, data, hora, datahora, "
               "padrões de data (ex.: dd/mm/aaaa hh:mm) e estilo Python (ex.: .2f, 05d, >10)")


def formatar_valor(valor, formato, para_texto=str):
    """Aplica `formato` ao valor. `para_texto` converte valores não textuais (ex.: listas)."""
    spec = formato.strip()
    if not spec:
        raise ErroFormato("o formato está vazio")
    if valor is None:
        return 'nulo'
    nome, ponto, arg = spec.partition('.')
    chave = nome.lower()
    if ponto and chave in _NOMES_NUM:
        if arg == '':
            raise ErroFormato(f"'{spec}': depois do ponto use o número de casas decimais (ex.: {chave}.2)")
        return _NOMES_NUM[chave](valor, arg)
    if not ponto and chave in _NOMES_NUM:
        return _NOMES_NUM[chave](valor, '')
    if chave in _NOMES_TEXTO and not ponto:
        return _NOMES_TEXTO[chave](_texto(valor, para_texto))
    if chave in _NOMES_DATA and not ponto:
        return _fmt_data(valor, _NOMES_DATA[chave], spec)
    if _eh_estilo_python(spec):
        return _formatar_python(valor, spec, para_texto)
    if _eh_padrao_data(spec):
        return _fmt_data(valor, spec, spec)
    raise ErroFormato(f"formato '{spec}' desconhecido. Disponíveis: {DISPONIVEIS}")
