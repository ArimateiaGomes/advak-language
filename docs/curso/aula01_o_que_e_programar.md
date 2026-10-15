# Aula 1 — O que é programar, o que é um algoritmo e o primeiro `imprimir`

> **Ao final desta aula você vai saber:** explicar o que é programar, escrever um algoritmo simples em português e fazer o computador escrever mensagens na tela com `imprimir`.

## O que é programar?

**Programar é dar instruções, passo a passo, para o computador fazer uma tarefa.** O computador é muito rápido, mas não pensa sozinho: ele só obedece, na ordem, exatamente o que está escrito.

Pense em uma **receita de bolo**. Quem escreve a receita diz: 1) coloque a farinha na tigela; 2) junte os ovos; 3) misture; 4) asse por 40 minutos. Se a ordem estiver errada (assar antes de misturar), o bolo não dá certo. Com o computador é igual.

Essa lista de passos, em ordem e sem ambiguidade, se chama **algoritmo**. Um programa é um algoritmo escrito em uma **linguagem de programação**. Neste curso usamos a **Advak**, que tem palavras em português.

## O primeiro comando: `imprimir`

`imprimir` manda o computador **escrever algo na tela**. O texto vai entre aspas e dentro de parênteses:

<!--codigo:aula01_exemplo1.dk-->
```advak
// Meu primeiro programa
// Tudo depois de duas barras (//) é comentário: o computador ignora, é só uma nota para você.
imprimir("Olá, mundo!")   // escreve o texto entre aspas na tela
```

Saída:

<!--saida:aula01_exemplo1.dk-->
```text
Olá, mundo!
```

Repare: o texto entre aspas apareceu **sem** as aspas. As aspas só avisam ao computador onde o texto começa e termina.

## Um algoritmo de verdade: a receita

Cada `imprimir` é um passo. O computador executa de cima para baixo, uma linha por vez:

<!--codigo:aula01_exemplo2.dk-->
```advak
// Algoritmo: fazer um bolo simples
imprimir("1) Coloque a farinha na tigela")
imprimir("2) Junte os ovos e o açúcar")
imprimir("3) Misture bem")
imprimir("4) Asse por 40 minutos")
imprimir("Pronto! O bolo está feito.")
```

Saída:

<!--saida:aula01_exemplo2.dk-->
```text
1) Coloque a farinha na tigela
2) Junte os ovos e o açúcar
3) Misture bem
4) Asse por 40 minutos
Pronto! O bolo está feito.
```

Se você trocar a ordem das linhas, a saída muda: **a ordem importa**.

## `imprimir` também faz contas

Fora das aspas, o computador calcula. Dentro das aspas, ele só repete o texto:

<!--codigo:aula01_exemplo3.dk-->
```advak
imprimir(2 + 3)          // sem aspas: o computador calcula e escreve 5
imprimir("2 + 3")        // com aspas: é só texto, escreve 2 + 3
imprimir("Resultado:", 10 * 4)   // vários itens separados por vírgula saem na mesma linha
imprimir(100 - 1, 7 * 6)
```

Saída:

<!--saida:aula01_exemplo3.dk-->
```text
5
2 + 3
Resultado: 40
99 42
```

## Erros comuns

**1. Esquecer de fechar as aspas.** O computador não sabe onde o texto termina:

<!--codigo:aula01_erro1.dk-->
```advak
imprimir("Olá, mundo!)
```

Mensagem real:

<!--erro:aula01_erro1.dk-->
```text
Localização: linha 1
Problema:    [Advak] Caractere inesperado '"' na linha 1, coluna 10
```

**Como corrigir:** feche as aspas: `imprimir("Olá, mundo!")`.

**2. Escrever o nome do comando errado.** Letras trocadas, e o computador não reconhece:

<!--codigo:aula01_erro2.dk-->
```advak
imprmir("Olá")
```

Mensagem real:

<!--erro:aula01_erro2.dk-->
```text
Localização: linha 1
Problema:    Variável 'imprmir' não definida
```

**Como corrigir:** confira a escrita: `imprimir`. O computador não adivinha o que você quis dizer.

## Exercícios

1. Escreva um programa que imprima seu nome.
2. Imprima três linhas: seu nome, sua cidade e sua idade.
3. Escreva um algoritmo (com `imprimir`) para **fazer um café**, com pelo menos 4 passos.
4. Imprima o resultado de `15 + 27` e de `9 * 8`, cada um em uma linha.
5. Imprima a frase `5 * 5` entre aspas e depois sem aspas. Explique a diferença.
6. **Desafio:** imprima um pequeno "cartão de visita" com uma linha de traços (`----------`), seu nome, sua profissão e outra linha de traços.

## Respostas

**Exercício 1**

<!--codigo:aula01_resposta1.dk-->
```advak
imprimir("Ana Souza")
```

<!--saida:aula01_resposta1.dk-->
```text
Ana Souza
```

**Exercício 2**

<!--codigo:aula01_resposta2.dk-->
```advak
imprimir("Ana Souza")
imprimir("Picos")
imprimir(17)
```

<!--saida:aula01_resposta2.dk-->
```text
Ana Souza
Picos
17
```

**Exercício 3**

<!--codigo:aula01_resposta3.dk-->
```advak
imprimir("1) Ferva a água")
imprimir("2) Coloque o pó no filtro")
imprimir("3) Despeje a água quente devagar")
imprimir("4) Adoce a gosto e sirva")
```

<!--saida:aula01_resposta3.dk-->
```text
1) Ferva a água
2) Coloque o pó no filtro
3) Despeje a água quente devagar
4) Adoce a gosto e sirva
```

**Exercício 4**

<!--codigo:aula01_resposta4.dk-->
```advak
imprimir(15 + 27)
imprimir(9 * 8)
```

<!--saida:aula01_resposta4.dk-->
```text
42
72
```

**Exercício 5** — com aspas é texto (aparece como foi escrito); sem aspas é conta (o computador calcula).

<!--codigo:aula01_resposta5.dk-->
```advak
imprimir("5 * 5")
imprimir(5 * 5)
```

<!--saida:aula01_resposta5.dk-->
```text
5 * 5
25
```

**Exercício 6**

<!--codigo:aula01_resposta6.dk-->
```advak
imprimir("----------")
imprimir("Ana Souza")
imprimir("Professora")
imprimir("----------")
```

<!--saida:aula01_resposta6.dk-->
```text
----------
Ana Souza
Professora
----------
```

---

**Próxima aula:** [Aula 2 — Como usar o REPL e como criar e executar um arquivo .dk](aula02_repl_e_arquivos.md)
