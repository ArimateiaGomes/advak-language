# Aula 2 — Como usar o REPL e como criar e executar um arquivo .dk

> **Ao final desta aula você vai saber:** testar comandos rapidamente no REPL, criar um arquivo `.dk` com um editor de texto e executá-lo pelo terminal.

Antes de começar, confira se a Advak está instalada: veja o guia [INSTALACAO.md](../INSTALACAO.md). No terminal (Prompt de Comando ou PowerShell), `advak --versao` deve mostrar a versão.

## Duas formas de usar a Advak

1. **REPL** (pronuncia-se "répel"): uma conversa rápida com o computador. Você digita **uma linha**, ele responde na hora. É ótimo para testar ideias e tirar dúvidas. O que você digita **não fica salvo**.
2. **Arquivo `.dk`**: um texto com vários comandos, salvo no computador. Você pode rodar de novo quando quiser, mostrar para os colegas, melhorar aos poucos. **É assim que se escrevem programas de verdade.**

## O REPL

Para abrir, digite `advak` e aperte Enter. Aparece uma tela de boas-vindas e o prompt `advak>>`, que significa "pode digitar". Veja uma sessão real, a partir do prompt (o que está depois de `advak>>` foi digitado):

<!--repl:aula02_repl1
2 + 3
seja x = 10
x * 2
imprimir("oi")
.sair
-->
<!--saida:aula02_repl1.repl-->
```text
advak>> 2 + 3
  → 5
advak>> seja x = 10
advak>> x * 2
  → 20
advak>> imprimir("oi")
oi
advak>> .sair
  Até logo! 👋
```

O que aconteceu:

- `2 + 3` → o REPL calculou e mostrou o resultado depois da seta `→`.
- `seja x = 10` → guardou o número 10 em uma "caixinha" chamada `x` (você vai estudar isso na aula 3).
- `x * 2` → usou a caixinha e deu 20.
- `imprimir("oi")` → escreveu `oi` na tela.
- `.sair` → fecha o REPL. (Também funciona `Ctrl+D`.)

Os comandos que começam com ponto são **comandos do REPL**, não da linguagem. Digite `.ajuda` para ver todos.

### Um erro comum no REPL

Escrever `sair` (sem o ponto) faz o REPL achar que `sair` é uma variável:

<!--repl:aula02_repl2
sair
.sair
-->
<!--saida:aula02_repl2.repl-->
```text
advak>> sair
  ❌ Variável 'sair' não definida
advak>> .sair
  Até logo! 👋
```

**Como corrigir:** use `.sair`, com o ponto.

## Criando e executando um arquivo `.dk`

**Passo 1 — criar o arquivo.** Abra um editor de texto simples (Bloco de Notas, Notepad++ ou VS Code). Escreva o programa e salve com a extensão **`.dk`**, por exemplo `meu_programa.dk`. No Bloco de Notas, em "Tipo", escolha **"Todos os arquivos"**, senão ele salva como `meu_programa.dk.txt`. Salve com codificação **UTF-8** (para os acentos saírem certos).

<!--codigo:aula02_exemplo1.dk-->
```advak
// Meu primeiro arquivo .dk
imprimir("Olá! Este programa está salvo em um arquivo.")
imprimir("Posso rodar de novo quantas vezes quiser.")
```

**Passo 2 — abrir o terminal na pasta do arquivo.** No Explorador de Arquivos, entre na pasta, clique na barra de endereço, digite `cmd` e aperte Enter.

**Passo 3 — executar.** Digite:

```
advak meu_programa.dk
```

Saída (a mesma que o computador mostra):

<!--saida:aula02_exemplo1.dk-->
```text
Olá! Este programa está salvo em um arquivo.
Posso rodar de novo quantas vezes quiser.
```

Para mudar o programa, edite o arquivo, salve e rode de novo. O ciclo é sempre: **escrever → salvar → executar → ler o resultado**.

## REPL ou arquivo?

| Quero... | Use |
|---|---|
| testar um cálculo ou um comando rapidinho | REPL |
| guardar o programa e rodar de novo | arquivo `.dk` |
| escrever mais de 3 ou 4 linhas | arquivo `.dk` |

## Erros comuns

**1. Usar uma variável que não existe.** No arquivo, a mensagem diz em qual linha está o problema:

<!--codigo:aula02_erro1.dk-->
```advak
imprimir("Início")
imprimir(nome)
```

Mensagem real:

<!--erro:aula02_erro1.dk-->
```text
Localização: linha 2
Problema:    Variável 'nome' não definida
```

**Como corrigir:** crie a variável antes de usar (`seja nome = "Ana"`), ou confira a escrita do nome.

**2. O arquivo ficou com o nome errado** (por exemplo `meu_programa.dk.txt`) ou você está na pasta errada: o `advak` diz que não achou o arquivo. Use `dir` para ver os arquivos da pasta e confira o nome.

## Exercícios

1. Abra o REPL e calcule `12 * 12`. Qual o resultado?
2. No REPL, crie a variável `idade` com o valor 17 e depois calcule `idade + 1`.
3. Crie um arquivo `.dk` que imprima seu nome e sua cidade, e execute-o.
4. Escreva um arquivo com **três** linhas de `imprimir` e um comentário (`//`) explicando o que o programa faz.
5. Faça um programa que imprima a conta `365 * 24` (horas em um ano) com uma frase explicando.
6. **Desafio:** no REPL, descubra o que acontece ao digitar `.exemplo`. Depois escreva, em um arquivo, um dos exemplos que ele mostrou.

## Respostas

**Exercício 1** — sessão do REPL:

<!--repl:aula02_resposta1
12 * 12
.sair
-->
<!--saida:aula02_resposta1.repl-->
```text
advak>> 12 * 12
  → 144
advak>> .sair
  Até logo! 👋
```

**Exercício 2**

<!--repl:aula02_resposta2
seja idade = 17
idade + 1
.sair
-->
<!--saida:aula02_resposta2.repl-->
```text
advak>> seja idade = 17
advak>> idade + 1
  → 18
advak>> .sair
  Até logo! 👋
```

**Exercício 3**

<!--codigo:aula02_resposta3.dk-->
```advak
imprimir("Ana Souza")
imprimir("Picos")
```

<!--saida:aula02_resposta3.dk-->
```text
Ana Souza
Picos
```

**Exercício 4**

<!--codigo:aula02_resposta4.dk-->
```advak
// Este programa apresenta uma pessoa
imprimir("Nome: Ana Souza")
imprimir("Cidade: Picos")
imprimir("Curso: Aprenda a programar com Advak")
```

<!--saida:aula02_resposta4.dk-->
```text
Nome: Ana Souza
Cidade: Picos
Curso: Aprenda a programar com Advak
```

**Exercício 5**

<!--codigo:aula02_resposta5.dk-->
```advak
// Quantas horas existem em um ano de 365 dias?
imprimir("Horas em um ano:", 365 * 24)
```

<!--saida:aula02_resposta5.dk-->
```text
Horas em um ano: 8760
```

**Exercício 6** — o `.exemplo` mostra exemplos prontos; copie um deles para um arquivo. Um programa equivalente:

<!--codigo:aula02_resposta6.dk-->
```advak
seja lista = [1, 2, 3]
imprimir(lista.mapear((x) => x * 2))
imprimir(moeda(1500))
```

<!--saida:aula02_resposta6.dk-->
```text
[2, 4, 6]
R$ 1.500,00
```

---

**Anterior:** [Aula 1](aula01_o_que_e_programar.md) · **Próxima aula:** [Aula 3 — Variáveis, tipos e constantes](aula03_variaveis_tipos_constantes.md)
