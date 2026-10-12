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
