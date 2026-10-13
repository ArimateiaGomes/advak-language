# Novos recursos da linguagem (Advak 5.2) — notas de trabalho

Este arquivo cresce a cada recurso novo da Etapa 2. O conteúdo alimenta o README, o CHANGELOG e o guia da
Etapa 3. Cada recurso tem testes em `testes/`.

## Intervalos

```
para (i em 1..4) { }            // 1, 2, 3              — o fim fica de FORA
para (i em 1..=4) { }           // 1, 2, 3, 4           — o fim fica DENTRO
para (i em 0..=100 passo 5) { } // 0, 5, 10 ... 100     — passo (sinônimo em inglês: step)
para (i em 5..=1 passo -1) { }  // 5, 4, 3, 2, 1        — para contar para trás use passo negativo
seja pares = 2..=10 passo 2     // [2, 4, 6, 8, 10]     — fora de um laço o intervalo vira uma lista
seja n = 4
para (i em 1..n + 1) { }        // 1..(n + 1): os limites são expressões completas
```

Regras:

- `..` exclui o fim (como `Lista.intervalo(a, b)` e o `range` do Python); `..=` inclui o fim.
- **Não há inversão automática**: `10..1` é um intervalo vazio. Para contar para trás escreva `10..=1 passo -1`.
- Início, fim e passo precisam ser **números inteiros**. Um decimal que é inteiro (`4.0`, resultado de `8 / 2`)
  é aceito; `2.5` dá erro com a dica de usar `piso()`, `teto()` ou `arred()`. Passo `0` dá erro.
- Em `para (i em a..b)` o intervalo é **preguiçoso**: `para (i em 1..=100000000) { ... quebrar }` não cria
  uma lista de 100 milhões de itens. Fora de um laço o intervalo vira lista, com limite de 10 milhões de itens.
- `passo`/`step` só vale logo depois de um intervalo; fora dele continua sendo um nome comum (`seja passo = 3`).
  Atenção: `1..passo` (sem espaço antes de passo e sem outro número) lê `passo` como a variável do fim.

Onde está o código: tokens `..` e `..=` em `advak_lexer.py`; `parse_range` em `advak_parser.py` (acima de
`+`/`-` e abaixo das comparações); `_eval_intervalo` em `advak_interpreter.py`; `advak_nativo.py` (transpilador
Python) e `advak_formatador.py` (não separa mais `..=`).

Testes: `testes/intervalos.dk` (comportamento, 13 casos), `testes/test_intervalos.py` (lexer, parser,
formatador e transpilador).

Observação encontrada no caminho (não é do recurso): o transpilador Python (`advak_nativo.py`) falha com
`KeyError: 'value'` em qualquer número negativo literal (`seja x = -2`). O formatador também separa `+=`,
`-=` e `=>` com espaços indevidos. Ficam anotados para corrigir à parte.

## Compreensão de listas

```
[x * 2 para x em lista se x > 0]                  // transforma e filtra
[x * x para x em 1..=10]                           // combina com intervalos
[x para x em 0..=20 passo 5 se x != 10]
[[x, y] para x em 1..=3 para y em 1..=3 se x < y]  // laços aninhados: [[1, 2], [1, 3], [2, 3]]
[a + b para (a, b) em [[1, 2], [3, 4]]]            // desmonta cada par: [3, 7]
[c para c em "banana" se c != "a"]                  // percorre texto: ["b", "n", "n"]
[x > 0 ? x : 0 para x em numeros]                  // o elemento pode ser qualquer expressão
[x * 2 for x in lista if x > 0]                    // sinônimos em inglês: for / in (of) / if
```

Regras:

- O resultado é sempre uma **lista nova**. O que vem depois de `em` pode ser lista, texto, mapa (percorre as
  chaves, como o `para-em`), intervalo ou gerador. Outro valor (número, nulo...) dá erro em português.
- Pode haver **vários `para`** (laços aninhados, da esquerda para a direita) e **vários `se`**; cada `se`
  filtra o que vem antes dele.
- `para (a, b) em pares` desmonta cada item em nomes; se o item não tiver a quantidade certa de valores, dá erro.
- A variável do `para` existe **só dentro da compreensão**: não vaza e não altera uma variável de fora com o
  mesmo nome. As cláusulas enxergam as variáveis de fora e as variáveis das cláusulas anteriores.
- Sem parênteses em volta do `para` (diferente do laço de instrução `para (i em lista) { }`).
- A origem é percorrida de forma preguiçosa (um intervalo não vira lista antes), mas o **resultado** tem teto de
  10 milhões de itens.
- Não existe tupla em Advak: para devolver dois valores use uma lista (`[x, y]`), não `(x, y)`.
- Fica de fora desta versão: compreensão de **mapa** (`{k: v para ...}`) e de conjunto.

Observação: o parser de listas sempre foi tolerante e aceita itens sem vírgula (`[a b c]` vira lista de três
itens). Isso não mudou; por isso `[para x em l]` (sem o elemento antes do `para`) continua sendo uma lista de
quatro nomes e não um erro de sintaxe.

Onde está o código: `parse_list_literal` e `_parse_compreensao` em `advak_parser.py`; `_comp_rec` em
`advak_interpreter.py`; `advak_nativo.py` gera a compreensão equivalente em Python.

Testes: `testes/compreensao.dk` (16 casos) e `testes/test_compreensao.py` (parser, erros de sintaxe, limite,
transpilador, formatador).