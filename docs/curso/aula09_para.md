# Aula 9 — Repetição com `para`

> **Ao final desta aula você vai saber:** usar o `para` com contador e o `para ... em` para percorrer sequências e listas.

## `para` com contador

Quando sabemos quantas voltas queremos, o `para` é mais enxuto que o `enquanto`. Ele junta, numa linha só, o início, a condição e o passo:

```
para (seja i = 0; i < 3; i++) { ... }
         início     condição  passo
```

<!--codigo:aula09_exemplo1.dk-->
```advak
para (seja i = 1; i <= 5; i++) {      // começa em 1, vai até 5, soma 1 a cada volta
    imprimir("Volta", i)
}
```

<!--saida:aula09_exemplo1.dk-->
```text
Volta 1
Volta 2
Volta 3
Volta 4
Volta 5
```

É o mesmo laço do `enquanto` da aula 8, só que mais curto.

## `para ... em` com intervalos

Dá para escrever "de 1 até 5" assim: `1..=5`. O ponto-ponto cria um **intervalo**:

- `1..5` vai de 1 a **4** (o último **não** entra);
- `1..=5` vai de 1 a **5** (o `=` inclui o último).

<!--codigo:aula09_exemplo2.dk-->
```advak
para (n em 1..4) {                    // 1, 2 e 3
    imprimir("sem incluir o fim:", n)
}
para (n em 1..=3) {                   // 1, 2 e 3
    imprimir("incluindo o fim:", n)
}
```

<!--saida:aula09_exemplo2.dk-->
```text
sem incluir o fim: 1
sem incluir o fim: 2
sem incluir o fim: 3
incluindo o fim: 1
incluindo o fim: 2
incluindo o fim: 3
```

## Percorrendo uma lista

O `para ... em` também passa por cada item de uma lista (veremos listas na aula 10):

<!--codigo:aula09_exemplo3.dk-->
```advak
seja frutas = ["maçã", "banana", "uva"]
para (fruta em frutas) {              // a cada volta, "fruta" guarda um item da lista
    imprimir("Eu gosto de", fruta)
}
```

<!--saida:aula09_exemplo3.dk-->
```text
Eu gosto de maçã
Eu gosto de banana
Eu gosto de uva
```

## `quebrar` e `continuar` também funcionam no `para`

<!--codigo:aula09_exemplo4.dk-->
```advak
para (n em 1..=10) {
    se (n % 2 == 0) {
        continuar                     // pula os pares
    }
    se (n > 7) {
        quebrar                       // para tudo quando passar de 7
    }
    imprimir(n)
}
```

<!--saida:aula09_exemplo4.dk-->
```text
1
3
5
7
```

## Qual usar: `enquanto` ou `para`?

- **`para`**: você sabe quantas vezes repetir, ou vai percorrer uma lista.
- **`enquanto`**: você repete até uma condição mudar (como a senha certa).

## Erros comuns

**1. Usar a variável do `para` depois do laço.** Ela só existe dentro do `para`:

<!--codigo:aula09_erro1.dk-->
```advak
para (seja i = 0; i < 3; i++) {
    imprimir(i)
}
imprimir("Terminou em", i)
```

Mensagem real:

<!--erro:aula09_erro1.dk-->
```text
Localização: linha 4
Problema:    Variável 'i' não definida
```

**Como corrigir:** guarde o que precisa em uma variável criada antes do laço (por exemplo, `seja ultimo = 0` e, dentro do laço, `ultimo = i`).

**2. Contar uma volta a menos por esquecer que `1..5` não inclui o 5.** Use `1..=5` quando o último valor deve entrar.

**3. Mudar o sentido errado:** `para (seja i = 10; i > 0; i++)` soma em vez de diminuir e nunca termina. Para contar para trás, use `i--`.

## Exercícios

1. Escreva de 1 a 10 usando `para` com contador.
2. Escreva a tabuada do 7 (de 1 a 10) usando `1..=10`.
3. Some os números de 1 a 100 e mostre o resultado.
4. Peça um texto e uma quantidade `n`; escreva o texto `n` vezes.
5. Mostre os números de 10 até 1 (contagem regressiva) usando `para` com `i--`.
6. Dada a lista `[4, 9, 2, 7]`, mostre cada número e, no fim, qual é o maior.
7. Desenhe um triângulo de asteriscos de 4 linhas: na linha 1, uma `*`; na 2, duas, e assim por diante. Dica: `"*".repetir(n)`.
8. **Desafio:** mostre todos os números primos de 2 a 30.

## Respostas

**Exercício 1**

<!--codigo:aula09_resposta1.dk-->
```advak
para (seja i = 1; i <= 10; i++) {
    imprimir(i)
}
```

<!--saida:aula09_resposta1.dk-->
```text
1
2
3
4
5
6
7
8
9
10
```

**Exercício 2**

<!--codigo:aula09_resposta2.dk-->
```advak
para (i em 1..=10) {
    imprimir("7 x", i, "=", 7 * i)
}
```

<!--saida:aula09_resposta2.dk-->
```text
7 x 1 = 7
7 x 2 = 14
7 x 3 = 21
7 x 4 = 28
7 x 5 = 35
7 x 6 = 42
7 x 7 = 49
7 x 8 = 56
7 x 9 = 63
7 x 10 = 70
```

**Exercício 3**

<!--codigo:aula09_resposta3.dk-->
```advak
seja soma = 0
para (i em 1..=100) {
    soma = soma + i
}
imprimir("Soma de 1 a 100:", soma)
```

<!--saida:aula09_resposta3.dk-->
```text
Soma de 1 a 100: 5050
```

**Exercício 4**

<!--codigo:aula09_resposta4.dk-->
```advak
seja texto = entrada("Texto: ")
seja n = inteiro(entrada("Quantas vezes? "))
para (i em 0..n) {
    imprimir(texto)
}
```

<!--entrada:aula09_resposta4
Olá
3
-->
<!--saida:aula09_resposta4.dk-->
```text
Texto: Olá
Quantas vezes? 3
Olá
Olá
Olá
```

**Exercício 5**

<!--codigo:aula09_resposta5.dk-->
```advak
para (seja i = 10; i >= 1; i--) {
    imprimir(i)
}
```

<!--saida:aula09_resposta5.dk-->
```text
10
9
8
7
6
5
4
3
2
1
```

**Exercício 6**

<!--codigo:aula09_resposta6.dk-->
```advak
seja numeros = [4, 9, 2, 7]
seja maior = numeros[0]               // começa supondo que o primeiro é o maior
para (n em numeros) {
    imprimir(n)
    se (n > maior) {
        maior = n
    }
}
imprimir("O maior é", maior)
```

<!--saida:aula09_resposta6.dk-->
```text
4
9
2
7
O maior é 9
```

**Exercício 7**

<!--codigo:aula09_resposta7.dk-->
```advak
para (n em 1..=4) {
    imprimir("*".repetir(n))
}
```

<!--saida:aula09_resposta7.dk-->
```text
*
**
***
****
```

**Exercício 8**

<!--codigo:aula09_resposta8.dk-->
```advak
para (n em 2..=30) {
    seja primo = verdadeiro
    para (d em 2..n) {                // testa se algum d entre 2 e n-1 divide n
        se (n % d == 0) {
            primo = falso
            quebrar
        }
    }
    se (primo) {
        imprimir(n)
    }
}
```

<!--saida:aula09_resposta8.dk-->
```text
2
3
5
7
11
13
17
19
23
29
```

---

**Anterior:** [Aula 8](aula08_enquanto.md) · **Próxima aula:** [Aula 10 — Listas](aula10_listas.md)
