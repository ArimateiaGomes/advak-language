# Aula 13 — Lambdas, `filtrar`, `mapear`, `reduzir` e o pipeline `|>`

> **Ao final desta aula você vai saber:** escrever funções curtas (lambdas), usá-las para filtrar, transformar e somar listas, e encadear funções com o pipeline `|>`.

## Lambda: uma função de uma linha

Na aula 12 criamos funções com `função nome() { ... }`. Quando a função é pequena, podemos escrevê-la numa linha só, sem nome próprio. Isso se chama **lambda** e usa a seta `=>`:

```
(parâmetros) => resultado
```

<!--codigo:aula13_exemplo1.dk-->
```advak
seja dobro = (x) => x * 2          // recebe x e devolve x * 2
seja somar = (a, b) => a + b       // dois parâmetros
imprimir(dobro(5))
imprimir(somar(3, 4))
```

<!--saida:aula13_exemplo1.dk-->
```text
10
7
```

Repare que o resultado é devolvido sozinho: numa lambda não precisa de `retornar`.

## `filtrar`: ficar só com o que interessa

`lista.filtrar(função)` devolve uma **nova lista** só com os itens para os quais a função dá `verdadeiro`:

<!--codigo:aula13_exemplo2.dk-->
```advak
seja notas = [4, 8, 6, 9, 3, 7]
seja aprovados = notas.filtrar((n) => n >= 7)     // fica só quem tem nota >= 7
imprimir(aprovados)
imprimir(notas)                                    // a lista original não muda
```

<!--saida:aula13_exemplo2.dk-->
```text
[8, 9, 7]
[4, 8, 6, 9, 3, 7]
```

## `mapear`: transformar cada item

`lista.mapear(função)` aplica a função a **cada item** e devolve a lista dos resultados:

<!--codigo:aula13_exemplo3.dk-->
```advak
seja precos = [10, 20, 30]
seja com_desconto = precos.mapear((p) => p * 0.9)     // 10% de desconto
imprimir(com_desconto)

seja nomes = ["ana", "bia"]
imprimir(nomes.mapear((n) => n.maiusculo()))
```

<!--saida:aula13_exemplo3.dk-->
```text
[9.0, 18.0, 27.0]
['ANA', 'BIA']
```

## `reduzir`: juntar tudo em um único valor

`lista.reduzir(função, valor_inicial)` percorre a lista guardando um resultado que vai acumulando. A função recebe o **acumulado** e o **item atual**:

<!--codigo:aula13_exemplo4.dk-->
```advak
seja numeros = [1, 2, 3, 4]
seja soma = numeros.reduzir((acumulado, n) => acumulado + n, 0)     // começa em 0
imprimir(soma)
seja produto = numeros.reduzir((acumulado, n) => acumulado * n, 1)  // começa em 1
imprimir(produto)
```

<!--saida:aula13_exemplo4.dk-->
```text
10
24
```

Passo a passo da soma: `0+1=1`, `1+2=3`, `3+3=6`, `6+4=10`.

## Combinando: um relatório em poucas linhas

Os métodos podem ser encadeados com ponto, um depois do outro:

<!--codigo:aula13_exemplo5.dk-->
```advak
seja pedidos = [12.5, 40, 7, 99.9, 25]
seja total_grandes = pedidos
    .filtrar((v) => v >= 20)            // só os pedidos de 20 ou mais
    .reduzir((a, v) => a + v, 0)        // e soma esses
imprimir("Total dos pedidos grandes:", total_grandes)
```

<!--saida:aula13_exemplo5.dk-->
```text
Total dos pedidos grandes: 164.9
```

## O pipeline `|>`

O pipeline passa o resultado da esquerda para a função da direita, como uma linha de montagem. `3 |> dobro |> somar10` significa: pegue 3, aplique `dobro`, aplique `somar10` no resultado.

<!--codigo:aula13_exemplo6.dk-->
```advak
seja dobro = (x) => x * 2
seja somar10 = (x) => x + 10
imprimir(3 |> dobro |> somar10)         // (3 * 2) + 10

seja so_pares = (lista) => lista.filtrar((n) => n % 2 == 0)
seja soma_total = (lista) => lista.reduzir((a, n) => a + n, 0)
imprimir([1, 2, 3, 4, 5, 6] |> so_pares |> soma_total)   // 2 + 4 + 6
```

<!--saida:aula13_exemplo6.dk-->
```text
16
12
```

Regra do `|>` na Advak: o que vem depois dele precisa ser **uma função (ou lambda) de um só parâmetro**, já com nome. Por isso criamos `so_pares` e `soma_total` antes de usá-las.

## Erros comuns

**1. Esquecer os parênteses dos parâmetros da lambda:**

<!--codigo:aula13_erro1.dk-->
```advak
seja dobro = x => x * 2
imprimir(dobro(5))
```

Mensagem real:

<!--erro:aula13_erro1.dk-->
```text
Localização: linha 1
Problema:    token inesperado '=>'
```

**Como corrigir:** escreva `(x) => x * 2`, sempre com parênteses.

**2. Usar `filtrar` solto depois do `|>`.** `filtrar`, `mapear` e `reduzir` são métodos da lista (`lista.filtrar(...)`), não funções soltas:

<!--codigo:aula13_erro2.dk-->
```advak
seja numeros = [1, 2, 3, 4]
imprimir(numeros |> filtrar((n) => n > 2))
```

Mensagem real:

<!--erro:aula13_erro2.dk-->
```text
Localização: linha 2
Problema:    Variável 'filtrar' não definida
```

**Como corrigir:** escreva `numeros.filtrar((n) => n > 2)`, ou crie uma lambda de um parâmetro (como `so_pares` acima) e use `numeros |> so_pares`.

**3. Esquecer o valor inicial do `reduzir`.** Escreva sempre `reduzir(função, 0)` para somas e `reduzir(função, 1)` para produtos.

## Exercícios

1. Crie a lambda `triplo` e mostre `triplo(7)`.
2. Dada `[3, 8, 12, 5]`, use `filtrar` para ficar só com os maiores que 5.
3. Dada `[1, 2, 3]`, use `mapear` para obter os quadrados `[1, 4, 9]`.
4. Dada `[5, 10, 15]`, use `reduzir` para somar tudo.
5. Dada a lista de nomes `["ana", "bia", "caio"]`, deixe todos em maiúsculas.
6. Dada `[10, 25, 30, 45]`, calcule a soma só dos números maiores que 20.
7. Use o pipeline: `5 |> dobro |> somar10 |> quadrado`, criando as três lambdas.
8. **Desafio:** com `precos = [100, 250, 80, 40]`, aplique 10% de desconto aos preços maiores que 90 e mostre o total.

## Respostas

**Exercício 1**

<!--codigo:aula13_resposta1.dk-->
```advak
seja triplo = (x) => x * 3
imprimir(triplo(7))
```

<!--saida:aula13_resposta1.dk-->
```text
21
```

**Exercício 2**

<!--codigo:aula13_resposta2.dk-->
```advak
seja numeros = [3, 8, 12, 5]
imprimir(numeros.filtrar((n) => n > 5))
```

<!--saida:aula13_resposta2.dk-->
```text
[8, 12]
```

**Exercício 3**

<!--codigo:aula13_resposta3.dk-->
```advak
seja numeros = [1, 2, 3]
imprimir(numeros.mapear((n) => n * n))
```

<!--saida:aula13_resposta3.dk-->
```text
[1, 4, 9]
```

**Exercício 4**

<!--codigo:aula13_resposta4.dk-->
```advak
seja numeros = [5, 10, 15]
imprimir(numeros.reduzir((a, n) => a + n, 0))
```

<!--saida:aula13_resposta4.dk-->
```text
30
```

**Exercício 5**

<!--codigo:aula13_resposta5.dk-->
```advak
seja nomes = ["ana", "bia", "caio"]
imprimir(nomes.mapear((n) => n.maiusculo()))
```

<!--saida:aula13_resposta5.dk-->
```text
['ANA', 'BIA', 'CAIO']
```

**Exercício 6**

<!--codigo:aula13_resposta6.dk-->
```advak
seja numeros = [10, 25, 30, 45]
seja soma = numeros.filtrar((n) => n > 20).reduzir((a, n) => a + n, 0)
imprimir(soma)
```

<!--saida:aula13_resposta6.dk-->
```text
100
```

**Exercício 7**

<!--codigo:aula13_resposta7.dk-->
```advak
seja dobro = (x) => x * 2
seja somar10 = (x) => x + 10
seja quadrado = (x) => x ** 2
imprimir(5 |> dobro |> somar10 |> quadrado)    // ((5*2)+10)² = 400
```

<!--saida:aula13_resposta7.dk-->
```text
400
```

**Exercício 8**

<!--codigo:aula13_resposta8.dk-->
```advak
seja precos = [100, 250, 80, 40]
seja final = precos.mapear((p) => p > 90 ? p * 0.9 : p)    // desconto só nos maiores que 90
imprimir(final)
imprimir("Total:", final.reduzir((a, p) => a + p, 0))
```

<!--saida:aula13_resposta8.dk-->
```text
[90.0, 225.0, 80, 40]
Total: 435.0
```

---

**Anterior:** [Aula 12](aula12_funcoes.md) · **Próxima aula:** [Aula 14 — Textos e template strings](aula14_textos.md)
