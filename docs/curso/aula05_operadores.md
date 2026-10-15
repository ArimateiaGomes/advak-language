# Aula 5 — Operadores aritméticos, de comparação e lógicos

> **Ao final desta aula você vai saber:** fazer contas, comparar valores e combinar condições com `e`, `ou` e `nao`.

## Operadores aritméticos (contas)

| Operador | Significa | Exemplo | Resultado |
|---|---|---|---|
| `+` | soma | `7 + 2` | 9 |
| `-` | subtração | `7 - 2` | 5 |
| `*` | multiplicação | `7 * 2` | 14 |
| `/` | divisão | `7 / 2` | 3.5 |
| `//` | divisão inteira | `7 // 2` | 3 |
| `%` | resto da divisão | `7 % 2` | 1 |
| `**` | potência | `2 ** 3` | 8 |

<!--codigo:aula05_exemplo1.dk-->
```advak
imprimir(7 + 2)        // soma
imprimir(7 / 2)        // divisão normal: 3.5
imprimir(7 // 2)       // divisão inteira: quantas vezes o 2 cabe no 7 (3)
imprimir(7 % 2)        // resto: sobra 1 (útil para saber se um número é par)
imprimir(2 ** 3)       // 2 elevado a 3 = 2 * 2 * 2
imprimir(2 + 3 * 4)    // a multiplicação vem primeiro: 2 + 12
imprimir((2 + 3) * 4)  // parênteses mandam: 5 * 4
```

Saída:

<!--saida:aula05_exemplo1.dk-->
```text
9
3.5
3
1
8
14
20
```

**A ordem das contas** é a da matemática: primeiro parênteses, depois `**`, depois `*` `/` `%`, por fim `+` `-`. Na dúvida, use parênteses.

### Atalhos

<!--codigo:aula05_exemplo2.dk-->
```advak
seja pontos = 10
pontos += 5       // o mesmo que: pontos = pontos + 5
pontos -= 3       // pontos = pontos - 3
pontos *= 2       // pontos = pontos * 2
imprimir(pontos)
pontos++          // soma 1
imprimir(pontos)
```

Saída:

<!--saida:aula05_exemplo2.dk-->
```text
24
25
```

## Operadores de comparação

Comparam dois valores e respondem `verdadeiro` ou `falso` (tipo **booleano**):

| Operador | Significa |
|---|---|
| `==` | é igual a |
| `!=` | é diferente de |
| `>` `<` | maior que, menor que |
| `>=` `<=` | maior ou igual, menor ou igual |

<!--codigo:aula05_exemplo3.dk-->
```advak
seja idade = 17
imprimir(idade == 17)     // um = guarda valor; dois == comparam
imprimir(idade != 17)
imprimir(idade >= 18)
imprimir(idade < 18)
imprimir("ana" == "ana")  // também compara textos
```

Saída:

<!--saida:aula05_exemplo3.dk-->
```text
verdadeiro
falso
falso
verdadeiro
verdadeiro
```

## Operadores lógicos

Combinam respostas verdadeiro/falso:

| Operador | Significa | Quando dá verdadeiro |
|---|---|---|
| `e` (ou `&&`) | "e" | as **duas** condições são verdadeiras |
| `ou` (ou `\|\|`) | "ou" | **pelo menos uma** é verdadeira |
| `nao` (ou `!`) | "não" | inverte: verdadeiro vira falso e vice-versa |

<!--codigo:aula05_exemplo4.dk-->
```advak
seja idade = 16
seja tem_autorizacao = verdadeiro

// pode entrar no evento se tiver 16 ou mais E autorização
imprimir(idade >= 16 e tem_autorizacao)

// ganha desconto se for jovem OU idoso
seja jovem = idade < 18
seja idoso = idade >= 60
imprimir(jovem ou idoso)

imprimir(nao jovem)        // o contrário de "jovem"
```

Saída:

<!--saida:aula05_exemplo4.dk-->
```text
verdadeiro
verdadeiro
falso
```

## Erros comuns

**1. Confundir `=` com `==`.** `=` **guarda** um valor; `==` **compara**:

<!--codigo:aula05_erro1.dk-->
```advak
seja x = 5
se (x = 5) {
    imprimir("é cinco")
}
```

Mensagem real:

<!--erro:aula05_erro1.dk-->
```text
é cinco
```

**Como corrigir:** use `se (x == 5)`.

**2. Dividir por zero:**

<!--codigo:aula05_erro2.dk-->
```advak
seja total = 10
seja pessoas = 0
imprimir(total / pessoas)
```

Mensagem real:

<!--erro:aula05_erro2.dk-->
```text
inf
```

**Como corrigir:** antes de dividir, confira que o divisor não é zero (você aprende a decidir isso na aula 6).

## Exercícios

1. Calcule `(8 + 4) * 3` e `8 + 4 * 3`. Por que dão resultados diferentes?
2. Descubra o resto da divisão de `17` por `5`.
3. Verifique se `numero % 2 == 0` para `10` e para `7` (par ou ímpar).
4. Escreva uma condição que seja verdadeira quando a nota for **maior ou igual a 7** e a frequência **maior ou igual a 75**.
5. Dado `seja chovendo = verdadeiro`, imprima o contrário usando `nao`.
6. **Desafio:** com `a = 5`, `b = 3` e `c = 8`, imprima se `c` é maior que a soma de `a` e `b`, e se `a` é maior que `b` **ou** `b` é maior que `c`.

## Respostas

**Exercício 1** — a multiplicação tem prioridade; os parênteses mudam a ordem.

<!--codigo:aula05_resposta1.dk-->
```advak
imprimir((8 + 4) * 3)
imprimir(8 + 4 * 3)
```

<!--saida:aula05_resposta1.dk-->
```text
36
20
```

**Exercício 2**

<!--codigo:aula05_resposta2.dk-->
```advak
imprimir(17 % 5)
```

<!--saida:aula05_resposta2.dk-->
```text
2
```

**Exercício 3**

<!--codigo:aula05_resposta3.dk-->
```advak
imprimir(10 % 2 == 0)   // verdadeiro: 10 é par
imprimir(7 % 2 == 0)    // falso: 7 é ímpar
```

<!--saida:aula05_resposta3.dk-->
```text
verdadeiro
falso
```

**Exercício 4**

<!--codigo:aula05_resposta4.dk-->
```advak
seja nota = 7.5
seja frequencia = 80
imprimir(nota >= 7 e frequencia >= 75)
```

<!--saida:aula05_resposta4.dk-->
```text
verdadeiro
```

**Exercício 5**

<!--codigo:aula05_resposta5.dk-->
```advak
seja chovendo = verdadeiro
imprimir(nao chovendo)
```

<!--saida:aula05_resposta5.dk-->
```text
falso
```

**Exercício 6**

<!--codigo:aula05_resposta6.dk-->
```advak
seja a = 5
seja b = 3
seja c = 8
imprimir(c > a + b)            // 8 > 8 ? falso
imprimir(a > b ou b > c)       // 5 > 3 é verdadeiro, então basta uma
```

<!--saida:aula05_resposta6.dk-->
```text
falso
verdadeiro
```

---

**Anterior:** [Aula 4](aula04_entrada_e_conversao.md) · **Próxima aula:** [Aula 6 — Decisões](aula06_decisoes.md)
