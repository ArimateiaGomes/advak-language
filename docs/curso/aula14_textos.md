# Aula 14 — Textos e template strings

> **Ao final desta aula você vai saber:** mexer em textos (maiúsculas, partes, trocas, buscas) e montar frases com valores usando crase e `${ }`.

## Texto é uma sequência de letras

Um texto (também chamado *string*) é uma sequência de caracteres entre aspas. Como numa lista, cada caractere tem uma posição, começando em 0:

<!--codigo:aula14_exemplo1.dk-->
```advak
seja palavra = "Advak"
imprimir(palavra.tamanho)        // quantos caracteres: 5
imprimir(palavra[0])             // o primeiro caractere: A
imprimir(palavra[-1])            // o último: k
imprimir(palavra.fatia(1, 4))    // do índice 1 até o 3 (o 4 não entra): dva
```

<!--saida:aula14_exemplo1.dk-->
```text
5
A
k
dva
```

## Transformando e procurando

<!--codigo:aula14_exemplo2.dk-->
```advak
seja frase = "  Aprender a programar é divertido  "
imprimir(frase.aparar())                       // tira os espaços das pontas
seja limpa = frase.aparar()
imprimir(limpa.maiusculo())                    // TUDO EM MAIÚSCULAS
imprimir(limpa.minusculo())                    // tudo em minúsculas
imprimir(limpa.substituir("divertido", "útil"))  // troca um pedaço por outro
imprimir(limpa.contem("programar"))            // tem esse pedaço? verdadeiro/falso
imprimir(limpa.começa("Aprender"))             // começa com...?
imprimir(limpa.termina("."))                   // termina com...?
```

<!--saida:aula14_exemplo2.dk-->
```text
Aprender a programar é divertido
APRENDER A PROGRAMAR É DIVERTIDO
aprender a programar é divertido
Aprender a programar é útil
verdadeiro
verdadeiro
falso
```

Importante: essas funções **devolvem** um texto novo; o texto original continua igual.

## Quebrando um texto em pedaços

`dividir` corta o texto em uma lista, usando um separador. `unir` faz o caminho inverso:

<!--codigo:aula14_exemplo3.dk-->
```advak
seja linha = "Ana,17,Recife"
seja partes = linha.dividir(",")       // corta em cada vírgula
imprimir(partes)
imprimir(partes[0], "mora em", partes[2])

seja palavras = "o rato roeu".dividir(" ")
imprimir(palavras.tamanho, "palavras")
imprimir(palavras.unir("-"))           // junta com hífen
```

<!--saida:aula14_exemplo3.dk-->
```text
['Ana', '17', 'Recife']
Ana mora em Recife
3 palavras
o-rato-roeu
```

## Template strings: frases com valores dentro

Juntar textos com `+` fica comprido e confuso. Com a **crase** (`` ` ``, a mesma tecla do acento grave) podemos escrever a frase inteira e colocar variáveis ou contas dentro de `${ }`:

<!--codigo:aula14_exemplo4.dk-->
```advak
seja nome = "Ana"
seja idade = 17
imprimir("Nome: " + nome + ", idade: " + texto(idade))                  // jeito antigo
imprimir(`Nome: ${nome}, idade: ${idade}`)                              // com template
imprimir(`Ano que vem ${nome} terá ${idade + 1} anos.`)                 // dá para fazer contas dentro
```

<!--saida:aula14_exemplo4.dk-->
```text
Nome: Ana, idade: 17
Nome: Ana, idade: 17
Ano que vem Ana terá 18 anos.
```

**Atenção:** só o texto entre **crases** aceita `${ }`. Entre aspas comuns, o `${nome}` é escrito literalmente:

<!--codigo:aula14_exemplo5.dk-->
```advak
seja nome = "Ana"
imprimir("Olá, ${nome}")      // aspas: NÃO troca
imprimir(`Olá, ${nome}`)      // crase: troca
```

<!--saida:aula14_exemplo5.dk-->
```text
Olá, ${nome}
Olá, Ana
```

## Formatando números e datas

Depois de `:` dentro do `${ }`, escolhemos o formato:

<!--codigo:aula14_exemplo6.dk-->
```advak
seja preco = 1234.5
imprimir(`Preço: ${preco:moeda}`)               // R$ 1.234,50
imprimir(`Desconto: ${0.15:porcentagem}`)       // 15%
imprimir(`Pi com 2 casas: ${3.14159:.2f}`)      // 3,14
imprimir(`Pedido nº ${7:03d}`)                  // 007
imprimir(`Data: ${"2024-12-25":dd/mm/aaaa}`)    // 25/12/2024
```

<!--saida:aula14_exemplo6.dk-->
```text
Preço: R$ 1.234,50
Desconto: 15%
Pi com 2 casas: 3,14
Pedido nº 007
Data: 25/12/2024
```

## Erros comuns

**1. Usar `${ }` com aspas comuns.** Não dá erro, mas o resultado sai errado (`Olá, ${nome}`). **Como corrigir:** troque as aspas por crases.

**2. Juntar texto com número sem converter.** Em alguns casos o `+` junta como texto (`"a" + 1` vira `a1`), o que pode surpreender:

<!--codigo:aula14_erro2.dk-->
```advak
imprimir("Idade: " + 17)
imprimir("Soma: " + 2 + 3)
```

<!--saida:aula14_erro2.dk-->
```text
Idade: 17
Soma: 23
```

**Como corrigir:** use template string: `` `Soma: ${2 + 3}` ``.

**3. Esquecer que o texto original não muda:**

<!--codigo:aula14_erro3.dk-->
```advak
seja nome = "ana"
nome.maiusculo()                 // calcula, mas ninguém guarda o resultado
imprimir(nome)
nome = nome.maiusculo()          // agora sim: guarda o novo texto
imprimir(nome)
```

<!--saida:aula14_erro3.dk-->
```text
ana
ANA
```

## Exercícios

1. Peça seu nome e mostre-o em letras maiúsculas e em minúsculas.
2. Peça uma palavra e mostre quantas letras ela tem.
3. Peça uma frase e troque todas as vogais `a` por `o`.
4. Peça nome e cidade e mostre `Olá, <nome> de <cidade>!` usando template string.
5. Peça uma data no formato `dia/mes/ano` (exemplo `25/12/2024`) e mostre cada parte em uma linha. Dica: `dividir("/")`.
6. Peça uma frase e diga quantas palavras ela tem.
7. Peça uma palavra e diga se ela é um **palíndromo** (lê-se igual de trás para frente, como `arara`).
8. **Desafio:** peça um preço e um desconto em porcentagem e mostre `Preço final: R$ ...` com duas casas decimais usando `${ :moeda}`.

## Respostas

**Exercício 1**

<!--codigo:aula14_resposta1.dk-->
```advak
seja nome = entrada("Seu nome: ")
imprimir(nome.maiusculo())
imprimir(nome.minusculo())
```

<!--entrada:aula14_resposta1
Ana Souza
-->
<!--saida:aula14_resposta1.dk-->
```text
Seu nome: Ana Souza
ANA SOUZA
ana souza
```

**Exercício 2**

<!--codigo:aula14_resposta2.dk-->
```advak
seja palavra = entrada("Palavra: ")
imprimir(`A palavra tem ${palavra.tamanho} letras.`)
```

<!--entrada:aula14_resposta2
programar
-->
<!--saida:aula14_resposta2.dk-->
```text
Palavra: programar
A palavra tem 9 letras.
```

**Exercício 3**

<!--codigo:aula14_resposta3.dk-->
```advak
seja frase = entrada("Frase: ")
imprimir(frase.substituir("a", "o"))
```

<!--entrada:aula14_resposta3
a casa amarela
-->
<!--saida:aula14_resposta3.dk-->
```text
Frase: a casa amarela
o coso omorelo
```

**Exercício 4**

<!--codigo:aula14_resposta4.dk-->
```advak
seja nome = entrada("Nome: ")
seja cidade = entrada("Cidade: ")
imprimir(`Olá, ${nome} de ${cidade}!`)
```

<!--entrada:aula14_resposta4
Bia
Recife
-->
<!--saida:aula14_resposta4.dk-->
```text
Nome: Bia
Cidade: Recife
Olá, Bia de Recife!
```

**Exercício 5**

<!--codigo:aula14_resposta5.dk-->
```advak
seja data = entrada("Data (dia/mes/ano): ")
seja partes = data.dividir("/")
imprimir("Dia:", partes[0])
imprimir("Mês:", partes[1])
imprimir("Ano:", partes[2])
```

<!--entrada:aula14_resposta5
25/12/2024
-->
<!--saida:aula14_resposta5.dk-->
```text
Data (dia/mes/ano): 25/12/2024
Dia: 25
Mês: 12
Ano: 2024
```

**Exercício 6**

<!--codigo:aula14_resposta6.dk-->
```advak
seja frase = entrada("Frase: ")
seja palavras = frase.aparar().dividir(" ")
imprimir(`A frase tem ${palavras.tamanho} palavras.`)
```

<!--entrada:aula14_resposta6
o rato roeu a roupa
-->
<!--saida:aula14_resposta6.dk-->
```text
Frase: o rato roeu a roupa
A frase tem 5 palavras.
```

**Exercício 7**

<!--codigo:aula14_resposta7.dk-->
```advak
seja palavra = entrada("Palavra: ").minusculo()
se (palavra == palavra.inverter()) {
    imprimir(palavra, "é um palíndromo")
} senão {
    imprimir(palavra, "não é um palíndromo")
}
```

<!--entrada:aula14_resposta7
Arara
-->
<!--saida:aula14_resposta7.dk-->
```text
Palavra: Arara
arara é um palíndromo
```

**Exercício 8**

<!--codigo:aula14_resposta8.dk-->
```advak
seja preco = numero(entrada("Preço: "))
seja desconto = numero(entrada("Desconto (%): "))
seja final = preco - preco * desconto / 100
imprimir(`Preço final: ${final:moeda}`)
```

<!--entrada:aula14_resposta8
200
15
-->
<!--saida:aula14_resposta8.dk-->
```text
Preço: 200
Desconto (%): 15
Preço final: R$ 170,00
```

---

**Anterior:** [Aula 13](aula13_lambdas.md) · **Próxima aula:** [Aula 15 — Tratamento de erros](aula15_erros.md)
