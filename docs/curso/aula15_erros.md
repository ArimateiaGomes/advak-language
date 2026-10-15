# Aula 15 — Tratamento de erros

> **Ao final desta aula você vai saber:** impedir que o programa trave quando algo dá errado, usando `tentar`, `capturar` e `finalmente`; criar seus próprios erros com `lançar`; conferir se um valor é número com `e_numero`; e testar que um erro realmente acontece com `testar` e `afirmar_erro`.

## O que é um erro (e por que tratar)

Até agora, quando algo dava errado, o programa **parava** e mostrava uma caixa de erro. Isso é bom para quem está programando, mas ruim para quem está usando: ninguém quer que o caixa do mercado trave porque alguém digitou uma letra no lugar de um número.

**Tratar o erro** é combinar antes: "se isso der errado, faça este plano B, e o programa continua". Pense em uma viagem: você leva um guarda-chuva *caso* chova. Se não chover, o guarda-chuva nem sai da mochila.

## `tentar` e `capturar`

- `tentar { ... }` é o bloco onde as coisas podem dar errado.
- `capturar (e) { ... }` é o plano B. Ele só roda **se** acontecer um erro. A variável `e` (você escolhe o nome) guarda a mensagem do erro.
- `lançar` cria um erro de propósito, com a mensagem que você quiser.

<!--codigo:aula15_exemplo1.dk-->
```advak
imprimir("Antes")
tentar {
    imprimir("Dentro do tentar")
    lançar "algo deu errado"          // cria um erro; o resto do bloco é pulado
    imprimir("Esta linha nunca aparece")
} capturar (e) {
    imprimir("Plano B:", e)           // e guarda a mensagem
}
imprimir("Depois: o programa continuou")
```

<!--saida:aula15_exemplo1.dk-->
```text
Antes
Dentro do tentar
Plano B: algo deu errado
Depois: o programa continuou
```

Repare: depois do `lançar`, a Advak **pula** o resto do `tentar` e vai direto ao `capturar`. Depois do `capturar`, o programa segue normalmente.

> **Detalhe:** a variável `e` sempre chega como **texto**, mesmo que você lance outra coisa (um número, uma lista...). Por isso, lance mensagens em texto.

## Erros de propósito em funções

O uso mais comum de `lançar` é dentro de uma função, quando alguém a chama com um valor que não faz sentido:

<!--codigo:aula15_exemplo2.dk-->
```advak
função dividir(a, b) {
    se (b == 0) {
        lançar "não dá para dividir por zero"
    }
    retornar a / b
}

tentar {
    imprimir(dividir(6, 3))
    imprimir(dividir(1, 0))           // aqui dá erro
    imprimir("não chega aqui")
} capturar (erro) {
    imprimir("Erro:", erro)
}
```

<!--saida:aula15_exemplo2.dk-->
```text
2.0
Erro: não dá para dividir por zero
```

A função **avisa** que há um problema (`lançar`) e quem a chamou **decide** o que fazer (`capturar`). Sem o `tentar`, o `lançar` faria o programa parar.

## `finalmente`: o que roda sempre

O bloco `finalmente` roda **dando erro ou não**. É o lugar de arrumações que não podem ser esquecidas, como "fechar a loja" no fim do dia:

<!--codigo:aula15_exemplo3.dk-->
```advak
tentar {
    imprimir("Abrindo o caixa")
    lançar "faltou troco"
} capturar (e) {
    imprimir("Aviso:", e)
} finalmente {
    imprimir("Fechando o caixa (sempre acontece)")
}

tentar {
    imprimir("Segundo dia: tudo certo")
} finalmente {
    imprimir("Fechando o caixa de novo")
}
```

<!--saida:aula15_exemplo3.dk-->
```text
Abrindo o caixa
Aviso: faltou troco
Fechando o caixa (sempre acontece)
Segundo dia: tudo certo
Fechando o caixa de novo
```

O segundo `tentar` não tem `capturar`, só `finalmente`, e funciona do mesmo jeito.

## A Advak também cria erros sozinha

Você não precisa de `lançar` para ter erros: a própria Advak lança vários. Todos podem ser capturados:

<!--codigo:aula15_exemplo4.dk-->
```advak
seja lista = [10, 20, 30]

tentar {
    imprimir(lista[10])               // posição que não existe
} capturar (e) {
    imprimir("1:", e)
}

tentar {
    imprimir(naoexiste)               // variável que ninguém criou
} capturar (e) {
    imprimir("2:", e)
}

tentar {
    imprimir("a" - 1)                 // não se subtrai de um texto
} capturar (e) {
    imprimir("3:", e)
}

seja pessoa = nulo
tentar {
    imprimir(pessoa.nome)             // nulo não tem "nome"
} capturar (e) {
    imprimir("4:", e)
}
```

<!--saida:aula15_exemplo4.dk-->
```text
1: Índice 10 fora do alcance (tamanho: 3)
2: Variável 'naoexiste' não definida
3: Tipo incompatível: não é possível misturar texto e número — use texto(valor) para converter
4: Não é possível acessar 'nome' em nulo
```

## Cuidado: nem tudo vira erro

Duas situações que **não** dão erro na Advak, e por isso o `capturar` nunca roda:

- `numero("abc")` e `inteiro("abc")` devolvem **0**, em silêncio.
- `10 / 0` devolve `inf` (infinito), como você viu na aula 5.

<!--codigo:aula15_exemplo5.dk-->
```advak
tentar {
    imprimir(numero("abc"))
    imprimir(10 / 0)
} capturar (e) {
    imprimir("nunca aparece:", e)
}
```

<!--saida:aula15_exemplo5.dk-->
```text
0
inf
```

Então, para texto digitado, **valide antes**. A função `e_numero(texto)` responde `verdadeiro` se o texto é um número (inclusive negativo ou decimal) e `falso` se não é:

<!--codigo:aula15_exemplo6.dk-->
```advak
imprimir(e_numero("12"))
imprimir(e_numero("3.5"))
imprimir(e_numero("-4"))
imprimir(e_numero("abc"))
imprimir(e_numero(""))
```

<!--saida:aula15_exemplo6.dk-->
```text
verdadeiro
verdadeiro
verdadeiro
falso
falso
```

Juntando tudo: uma função que **recusa** o que não é número, e um `tentar` que cuida da recusa:

<!--codigo:aula15_exemplo7.dk-->
```advak
função ler_idade(digitado) {
    se (!e_numero(digitado)) {
        lançar "digite só números"
    }
    seja idade = inteiro(digitado)
    se (idade < 0 ou idade > 120) {
        lançar "idade fora do normal"
    }
    retornar idade
}

seja resposta = entrada("Sua idade: ")
tentar {
    seja idade = ler_idade(resposta)
    imprimir(`Daqui a 10 anos você terá ${idade + 10} anos.`)
} capturar (e) {
    imprimir("Não deu certo:", e)
}
```

<!--entrada:aula15_exemplo7
abc
-->
<!--saida:aula15_exemplo7.dk-->
```text
Sua idade: abc
Não deu certo: digite só números
```

Tente de novo no seu computador digitando `17`, depois `-3` e depois `200`, e veja as respostas mudarem.

## Pedir de novo até acertar

Um clássico: repetir a pergunta até a pessoa digitar algo válido. Aqui juntamos `enquanto`, `tentar` e uma variável `pronto`, que começa `falso` e só vira `verdadeiro` quando a pessoa acerta:

<!--codigo:aula15_exemplo8.dk-->
```advak
função ler_nota(digitado) {
    se (!e_numero(digitado)) {
        lançar "isso não é um número"
    }
    seja nota = numero(digitado)
    se (nota < 0 ou nota > 10) {
        lançar "a nota deve ficar entre 0 e 10"
    }
    retornar nota
}

seja pronto = falso
enquanto (!pronto) {
    seja resposta = entrada("Nota (0 a 10): ")
    tentar {
        seja nota = ler_nota(resposta)
        imprimir("Nota registrada:", nota)
        pronto = verdadeiro              // deu certo: a condição do enquanto deixa de valer
    } capturar (e) {
        imprimir("Tente de novo, porque", e)
    }
}
```

<!--entrada:aula15_exemplo8
abc
15
8.5
-->
<!--saida:aula15_exemplo8.dk-->
```text
Nota (0 a 10): abc
Tente de novo, porque isso não é um número
Nota (0 a 10): 15
Tente de novo, porque a nota deve ficar entre 0 e 10
Nota (0 a 10): 8.5
Nota registrada: 8.5
```

## Conferindo que o erro acontece: `testar` e `afirmar_erro`

Como saber se a sua função realmente recusa os valores ruins? Escrevendo **testes**. Você verá testes com calma na aula 20; aqui vai só uma amostra, com as três peças que importam:

- `testar("descrição", () => { ... })` roda um teste e mostra ✅ se passou ou ❌ se falhou;
- `afirmar_igual(real, esperado)` falha se os dois valores forem diferentes;
- `afirmar_erro(() => ...)` **passa** se o código lançar um erro, e falha se não lançar nenhum.

<!--codigo:aula15_exemplo9.dk-->
```advak
função dividir(a, b) {
    se (b == 0) {
        lançar "não dá para dividir por zero"
    }
    retornar a / b
}

testar("8 dividido por 2 é 4", () => {
    afirmar_igual(dividir(8, 2), 4)
})

testar("dividir por zero dá erro", () => {
    afirmar_erro(() => dividir(5, 0))
})

testar("este teste falha de propósito", () => {
    afirmar_igual(dividir(9, 3), 4)
})

resumo_testes()                          // mostra quantos passaram
```

<!--saida:aula15_exemplo9.dk-->
```text
  ✅ 8 dividido por 2 é 4
  ✅ dividir por zero dá erro
  ❌ este teste falha de propósito
     Esperado 4, obteve 3.0

  ────────────────────────────────────────────
  Resultado: 2/3 testes passaram  (1 falharam)
```

O terceiro teste falhou e a Advak disse exatamente por quê (`Esperado 4, obteve 3.0`). É assim que os testes ajudam a achar defeitos.

## Erros comuns

**1. Lançar um erro e não capturar.** O programa para na hora:

<!--codigo:aula15_erro1.dk-->
```advak
imprimir("Começou")
lançar "ninguém me captura"
imprimir("Isto nunca aparece")
```

Mensagem real:

<!--erro:aula15_erro1.dk-->
```text
Problema:    ninguém me captura
```

**Como corrigir:** coloque o `lançar` (ou a chamada da função que lança) dentro de um `tentar { }` com `capturar`.

**2. Achar que `numero("abc")` dá erro.** Não dá: vira 0 e o programa segue com um valor errado, o que é pior que travar.

<!--codigo:aula15_erro2.dk-->
```advak
seja preco = numero("abc")
imprimir("Total de 3 itens:", preco * 3)
```

<!--saida:aula15_erro2.dk-->
```text
Total de 3 itens: 0
```

**Como corrigir:** confira com `e_numero(texto)` antes de converter, como no Exemplo 7.

**3. Esperar que o código depois do `lançar` rode.** Tudo que vem depois do `lançar`, dentro do mesmo bloco, é pulado:

<!--codigo:aula15_erro3.dk-->
```advak
tentar {
    lançar "parou aqui"
    imprimir("pulado")
} capturar (e) {
    imprimir("capturei:", e)
}
```

<!--saida:aula15_erro3.dk-->
```text
capturei: parou aqui
```

**Como corrigir:** coloque dentro do `tentar` só o que depende do trecho que pode falhar, e o que deve rodar sempre em `finalmente`.

**4. Usar `retornar` ou `quebrar` dentro de um `tentar`.** Nesta versão da Advak, o `capturar` acaba "pegando" também essas saídas, como se fossem erros. Veja um caso real, em que a função deveria devolver 1:

<!--codigo:aula15_erro4.dk-->
```advak
função confusa() {
    tentar {
        retornar 1
    } capturar (e) {
        retornar 2
    }
}
imprimir(confusa())
```

<!--saida:aula15_erro4.dk-->
```text
2
```

E o mesmo acontece com `quebrar`: o laço abaixo deveria sair na primeira volta e o `capturar` não deveria rodar:

<!--codigo:aula15_erro5.dk-->
```advak
para (i em 1..4) {
    tentar {
        imprimir("volta", i)
        quebrar
    } capturar (e) {
        imprimir("capturar rodou sem erro nenhum!")
    }
}
```

<!--saida:aula15_erro5.dk-->
```text
volta 1
capturar rodou sem erro nenhum!
volta 2
capturar rodou sem erro nenhum!
volta 3
capturar rodou sem erro nenhum!
```

**Como corrigir:** guarde o resultado em uma variável dentro do `tentar` e use `retornar` **fora** dele (como na função `tentar_dividir` dos exercícios); para sair de um laço, use uma variável como `pronto` (como no Exemplo 8).

## Exercícios

1. Faça uma função `raiz_positiva(n)` que lance o erro `"número negativo"` quando `n < 0` e devolva `n ** 0.5` caso contrário. Chame-a com `16` e com `-4`, cada uma dentro de um `tentar`.
2. Peça dois números e mostre a divisão. Se o segundo for zero, a função `dividir` lança um erro e você mostra `Não dá para dividir por zero.`
3. Peça um número com `entrada`. Se o que foi digitado não for número (use `e_numero`), mostre `Isso não é um número!`; senão, mostre o dobro.
4. Use `finalmente` para mostrar `Obrigado por usar o programa!` depois de uma divisão que pode dar errado (com `lançar`), sendo que a mensagem deve aparecer nos dois casos.
5. Peça uma posição de 0 a 4 e mostre o item da lista `["pão", "leite", "café", "açúcar", "sal"]`. Se a posição não existir, capture o erro e mostre `Posição inválida.`
6. Peça uma idade repetidamente até a pessoa digitar um número entre 0 e 120 (use `enquanto`, `tentar`, `lançar` e uma variável `pronto`).
7. Escreva `tentar_dividir(a, b)`, que **devolve** `0` (e avisa) quando `b` é zero, sem usar `retornar` dentro do `tentar`.
8. **Desafio:** faça uma função `sacar(saldo, valor)` que lance `"valor inválido"` se `valor <= 0` e `"saldo insuficiente"` se `valor > saldo`; senão, devolva o novo saldo. Peça o valor e mostre o resultado ou a mensagem de erro.

## Respostas

**Exercício 1**

<!--codigo:aula15_resposta1.dk-->
```advak
função raiz_positiva(n) {
    se (n < 0) {
        lançar "número negativo"
    }
    retornar n ** 0.5
}

tentar {
    imprimir(raiz_positiva(16))
} capturar (e) {
    imprimir("Erro:", e)
}

tentar {
    imprimir(raiz_positiva(-4))
} capturar (e) {
    imprimir("Erro:", e)
}
```

<!--saida:aula15_resposta1.dk-->
```text
4.0
Erro: número negativo
```

**Exercício 2**

<!--codigo:aula15_resposta2.dk-->
```advak
função dividir(a, b) {
    se (b == 0) {
        lançar "divisão por zero"
    }
    retornar a / b
}

seja a = numero(entrada("Primeiro número: "))
seja b = numero(entrada("Segundo número: "))
tentar {
    imprimir("Resultado:", dividir(a, b))
} capturar (e) {
    imprimir("Não dá para dividir por zero.")
}
```

<!--entrada:aula15_resposta2
10
0
-->
<!--saida:aula15_resposta2.dk-->
```text
Primeiro número: 10
Segundo número: 0
Não dá para dividir por zero.
```

**Exercício 3**

<!--codigo:aula15_resposta3.dk-->
```advak
seja digitado = entrada("Digite um número: ")
se (e_numero(digitado)) {
    imprimir("O dobro é", numero(digitado) * 2)
} senão {
    imprimir("Isso não é um número!")
}
```

<!--entrada:aula15_resposta3
abc
-->
<!--saida:aula15_resposta3.dk-->
```text
Digite um número: abc
Isso não é um número!
```

**Exercício 4**

<!--codigo:aula15_resposta4.dk-->
```advak
função dividir(a, b) {
    se (b == 0) {
        lançar "divisão por zero"
    }
    retornar a / b
}

tentar {
    imprimir(dividir(10, 0))
} capturar (e) {
    imprimir("Erro:", e)
} finalmente {
    imprimir("Obrigado por usar o programa!")
}
```

<!--saida:aula15_resposta4.dk-->
```text
Erro: divisão por zero
Obrigado por usar o programa!
```

**Exercício 5**

<!--codigo:aula15_resposta5.dk-->
```advak
seja itens = ["pão", "leite", "café", "açúcar", "sal"]
seja posicao = inteiro(entrada("Posição (0 a 4): "))
tentar {
    imprimir("Item:", itens[posicao])
} capturar (e) {
    imprimir("Posição inválida.")
}
```

<!--entrada:aula15_resposta5
9
-->
<!--saida:aula15_resposta5.dk-->
```text
Posição (0 a 4): 9
Posição inválida.
```

**Exercício 6**

<!--codigo:aula15_resposta6.dk-->
```advak
seja pronto = falso
enquanto (!pronto) {
    seja digitado = entrada("Idade: ")
    tentar {
        se (!e_numero(digitado)) {
            lançar "digite um número"
        }
        seja idade = inteiro(digitado)
        se (idade < 0 ou idade > 120) {
            lançar "idade fora do normal"
        }
        imprimir("Idade registrada:", idade)
        pronto = verdadeiro
    } capturar (e) {
        imprimir("Inválido:", e)
    }
}
```

<!--entrada:aula15_resposta6
oi
200
35
-->
<!--saida:aula15_resposta6.dk-->
```text
Idade: oi
Inválido: digite um número
Idade: 200
Inválido: idade fora do normal
Idade: 35
Idade registrada: 35
```

**Exercício 7**

<!--codigo:aula15_resposta7.dk-->
```advak
função dividir(a, b) {
    se (b == 0) {
        lançar "divisão por zero"
    }
    retornar a / b
}

função tentar_dividir(a, b) {
    seja resultado = 0
    tentar {
        resultado = dividir(a, b)
    } capturar (e) {
        imprimir("Aviso:", e)
        resultado = 0
    }
    retornar resultado
}

imprimir(tentar_dividir(8, 2))
imprimir(tentar_dividir(8, 0))
```

<!--saida:aula15_resposta7.dk-->
```text
4.0
Aviso: divisão por zero
0
```

**Exercício 8**

<!--codigo:aula15_resposta8.dk-->
```advak
função sacar(saldo, valor) {
    se (valor <= 0) {
        lançar "valor inválido"
    }
    se (valor > saldo) {
        lançar "saldo insuficiente"
    }
    retornar saldo - valor
}

seja saldo = 100
seja valor = numero(entrada("Quanto quer sacar? "))
tentar {
    saldo = sacar(saldo, valor)
    imprimir("Saque feito. Novo saldo:", saldo)
} capturar (e) {
    imprimir("Não foi possível sacar:", e)
}
```

<!--entrada:aula15_resposta8
250
-->
<!--saida:aula15_resposta8.dk-->
```text
Quanto quer sacar? 250
Não foi possível sacar: saldo insuficiente
```

---

**Anterior:** [Aula 14](aula14_textos.md) · **Próxima aula:** [Aula 16 — Arquivos e JSON](aula16_arquivos_json.md)
