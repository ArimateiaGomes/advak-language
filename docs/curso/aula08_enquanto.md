# Aula 8 — Repetição com `enquanto`

> **Ao final desta aula você vai saber:** repetir um trecho do programa várias vezes usando `enquanto`, contar, acumular valores e sair de uma repetição com `quebrar`.

## Repetir é a força do computador

Imagine escrever "Bom dia!" cem vezes. À mão, é cansativo; o computador faz isso em um piscar de olhos. Uma repetição se chama **laço** (ou *loop*).

O `enquanto` repete o bloco **enquanto a condição for verdadeira**:

```
enquanto (condição) {
    ... repete enquanto a condição for verdadeira
}
```

<!--codigo:aula08_exemplo1.dk-->
```advak
seja contador = 1                     // começa em 1
enquanto (contador <= 3) {            // enquanto contador for menor ou igual a 3
    imprimir("Volta número", contador)
    contador = contador + 1           // MUITO importante: muda o valor, senão o laço nunca termina
}
imprimir("Acabou!")
```

<!--saida:aula08_exemplo1.dk-->
```text
Volta número 1
Volta número 2
Volta número 3
Acabou!
```

O computador fez assim: testa `1 <= 3` (verdadeiro) e roda o bloco; testa `2 <= 3` e roda; testa `3 <= 3` e roda; testa `4 <= 3` (falso) e **sai** do laço.

## Somando valores (acumulador)

Uma variável que vai juntando valores se chama **acumulador**:

<!--codigo:aula08_exemplo2.dk-->
```advak
seja soma = 0                         // acumulador começa em zero
seja n = 1
enquanto (n <= 5) {
    soma = soma + n                   // soma 1, depois 2, depois 3...
    n = n + 1
}
imprimir("A soma de 1 a 5 é", soma)
```

<!--saida:aula08_exemplo2.dk-->
```text
A soma de 1 a 5 é 15
```

Atalhos: `n += 1` é o mesmo que `n = n + 1`, e `n++` soma 1.

## Repetir até a pessoa mandar parar

Quando não sabemos quantas voltas serão, o laço depende do que a pessoa digita. Aqui o programa pede senhas até acertar:

<!--codigo:aula08_exemplo3.dk-->
```advak
seja senha = entrada("Digite a senha: ")
enquanto (senha != "1234") {          // continua enquanto a senha estiver errada
    imprimir("Senha incorreta.")
    senha = entrada("Digite a senha: ")
}
imprimir("Bem-vindo!")
```

Digitando `abc`, `0000` e por fim `1234`:

<!--entrada:aula08_exemplo3
abc
0000
1234
-->
<!--saida:aula08_exemplo3.dk-->
```text
Digite a senha: abc
Senha incorreta.
Digite a senha: 0000
Senha incorreta.
Digite a senha: 1234
Bem-vindo!
```

## Saindo antes com `quebrar` e pulando uma volta com `continuar`

`quebrar` encerra o laço na hora. `continuar` pula o resto da volta atual e vai para a próxima:

<!--codigo:aula08_exemplo4.dk-->
```advak
seja n = 0
enquanto (verdadeiro) {               // condição sempre verdadeira: só sai com quebrar
    n = n + 1
    se (n == 2) {
        continuar                     // pula o imprimir desta volta
    }
    se (n > 4) {
        quebrar                       // sai do laço
    }
    imprimir("n vale", n)
}
imprimir("Fim, n =", n)
```

<!--saida:aula08_exemplo4.dk-->
```text
n vale 1
n vale 3
n vale 4
Fim, n = 5
```

## Erros comuns

**1. Usar uma variável na condição sem criá-la antes:**

<!--codigo:aula08_erro1.dk-->
```advak
enquanto (contador < 3) {
    imprimir(contador)
    contador = contador + 1
}
```

Mensagem real:

<!--erro:aula08_erro1.dk-->
```text
Localização: linha 3
Problema:    Variável 'contador' não definida
```

**Como corrigir:** crie a variável antes do laço com `seja contador = 0`.

**2. Esquecer de mudar a variável dentro do laço.** O programa não dá erro, mas **nunca termina** (laço infinito). Se isso acontecer, pare o programa com `Ctrl + C`. Sempre confira: *alguma coisa dentro do bloco muda a condição?*

**3. Esquecer as chaves:**

<!--codigo:aula08_erro3.dk-->
```advak
seja i = 0
enquanto (i < 3)
    imprimir(i)
```

Mensagem real:

<!--erro:aula08_erro3.dk-->
```text
Localização: linha 3
Problema:    esperado 'LCURLY', encontrado 'imprimir'
```

**Como corrigir:** o bloco do `enquanto` sempre vai entre `{ }`.

> `LCURLY` é o nome interno da chave `{` ("left curly brace"). A mensagem quer dizer: "eu esperava a chave `{` e encontrei `imprimir`".

## Exercícios

1. Escreva os números de 1 a 10, um por linha.
2. Escreva os números pares de 2 a 20.
3. Peça um número e escreva a **tabuada** dele (de 1 a 10), no formato `3 x 4 = 12`.
4. Peça números até a pessoa digitar `0`; no fim, mostre a **soma** de todos.
5. Faça uma contagem regressiva de 5 até 1 e depois escreva `Fogo!`.
6. Peça um número `n` e calcule o **fatorial** (`5! = 5 x 4 x 3 x 2 x 1 = 120`).
7. **Desafio:** o computador "pensa" no número 7. A pessoa chuta até acertar; a cada erro diga se o chute foi `maior` ou `menor`, e no fim mostre quantas tentativas foram necessárias.

## Respostas

**Exercício 1**

<!--codigo:aula08_resposta1.dk-->
```advak
seja i = 1
enquanto (i <= 10) {
    imprimir(i)
    i = i + 1
}
```

<!--saida:aula08_resposta1.dk-->
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

<!--codigo:aula08_resposta2.dk-->
```advak
seja i = 2
enquanto (i <= 20) {
    imprimir(i)
    i = i + 2                         // pula de 2 em 2
}
```

<!--saida:aula08_resposta2.dk-->
```text
2
4
6
8
10
12
14
16
18
20
```

**Exercício 3**

<!--codigo:aula08_resposta3.dk-->
```advak
seja n = numero(entrada("Tabuada de qual número? "))
seja i = 1
enquanto (i <= 10) {
    imprimir(n, "x", i, "=", n * i)
    i = i + 1
}
```

<!--entrada:aula08_resposta3
3
-->
<!--saida:aula08_resposta3.dk-->
```text
Tabuada de qual número? 3
3 x 1 = 3
3 x 2 = 6
3 x 3 = 9
3 x 4 = 12
3 x 5 = 15
3 x 6 = 18
3 x 7 = 21
3 x 8 = 24
3 x 9 = 27
3 x 10 = 30
```

**Exercício 4**

<!--codigo:aula08_resposta4.dk-->
```advak
seja soma = 0
seja n = numero(entrada("Número (0 para terminar): "))
enquanto (n != 0) {
    soma = soma + n
    n = numero(entrada("Número (0 para terminar): "))
}
imprimir("Soma total:", soma)
```

<!--entrada:aula08_resposta4
5
10
2
0
-->
<!--saida:aula08_resposta4.dk-->
```text
Número (0 para terminar): 5
Número (0 para terminar): 10
Número (0 para terminar): 2
Número (0 para terminar): 0
Soma total: 17
```

**Exercício 5**

<!--codigo:aula08_resposta5.dk-->
```advak
seja i = 5
enquanto (i >= 1) {
    imprimir(i)
    i = i - 1
}
imprimir("Fogo!")
```

<!--saida:aula08_resposta5.dk-->
```text
5
4
3
2
1
Fogo!
```

**Exercício 6**

<!--codigo:aula08_resposta6.dk-->
```advak
seja n = inteiro(entrada("Fatorial de: "))
seja resultado = 1
seja i = n
enquanto (i > 1) {
    resultado = resultado * i
    i = i - 1
}
imprimir(n, "! =", resultado)
```

<!--entrada:aula08_resposta6
5
-->
<!--saida:aula08_resposta6.dk-->
```text
Fatorial de: 5
5 ! = 120
```

**Exercício 7**

<!--codigo:aula08_resposta7.dk-->
```advak
seja segredo = 7
seja tentativas = 1
seja chute = inteiro(entrada("Seu chute: "))
enquanto (chute != segredo) {
    se (chute > segredo) {
        imprimir("Menor!")
    } senão {
        imprimir("Maior!")
    }
    chute = inteiro(entrada("Seu chute: "))
    tentativas = tentativas + 1
}
imprimir("Acertou em", tentativas, "tentativas!")
```

<!--entrada:aula08_resposta7
3
10
7
-->
<!--saida:aula08_resposta7.dk-->
```text
Seu chute: 3
Maior!
Seu chute: 10
Menor!
Seu chute: 7
Acertou em 3 tentativas!
```

---

**Anterior:** [Aula 7](aula07_combinar.md) · **Próxima aula:** [Aula 9 — Repetição com `para`](aula09_para.md)
