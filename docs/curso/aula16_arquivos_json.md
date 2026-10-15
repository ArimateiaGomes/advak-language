# Aula 16 — Arquivos e JSON

> **Ao final desta aula você vai saber:** guardar informações em arquivos (para não sumirem quando o programa termina), ler o que já está salvo, trabalhar com linhas de texto e usar o formato JSON para guardar mapas e listas inteiros.

## Por que usar arquivos

Todas as variáveis que você criou até agora **somem** quando o programa termina. Se você cadastra 50 clientes e fecha o programa, perdeu tudo. Um **arquivo** guarda a informação no disco: ela continua lá amanhã.

Pense num caderno: a memória do programa é a sua cabeça (esquece), o arquivo é o caderno (lembra). Na Advak, o objeto `Arquivo` tem os comandos para mexer com cadernos:

| Comando | O que faz |
|---|---|
| `Arquivo.escrever(nome, texto)` | cria o arquivo (se existir, **substitui** o conteúdo) |
| `Arquivo.acrescentar(nome, texto)` | escreve no **fim** do arquivo, sem apagar o que já tinha |
| `Arquivo.ler(nome)` | devolve o conteúdo inteiro como texto |
| `Arquivo.ler_linhas(nome)` | devolve uma lista com uma linha por posição |
| `Arquivo.existe(nome)` | `verdadeiro` ou `falso` |
| `Arquivo.apagar(nome)` | apaga o arquivo |

## Escrever, acrescentar e ler

<!--codigo:aula16_exemplo1.dk-->
```advak
seja nome = "aula16_recado.txt"
imprimir("Existe antes?", Arquivo.existe(nome))

Arquivo.escrever(nome, "Comprar pão\n")          // \n = pular linha
Arquivo.acrescentar(nome, "Comprar leite\n")     // vai para o fim
Arquivo.acrescentar(nome, "Estudar Advak\n")

imprimir("Existe depois?", Arquivo.existe(nome))
imprimir("Conteúdo:")
imprimir(Arquivo.ler(nome))

Arquivo.apagar(nome)                             // limpa a bagunça
imprimir("Existe no fim?", Arquivo.existe(nome))
```

<!--saida:aula16_exemplo1.dk-->
```text
Existe antes? falso
Existe depois? verdadeiro
Conteúdo:
Comprar pão
Comprar leite
Estudar Advak

Existe no fim? falso
```

Os comandos de escrita respondem com uma frase como `✅ 'aula16_recado.txt' salvo`. Neste exemplo ignoramos essa resposta; se quiser vê-la, use `imprimir(Arquivo.escrever(...))`.

> O nome do arquivo sem pasta (`"aula16_recado.txt"`) fica na **pasta onde você está rodando o programa**. Para uma pasta específica, escreva o caminho: `"dados/notas.txt"`.

## Lendo linha por linha

`Arquivo.ler_linhas` devolve uma **lista** (aula 10): cada linha do arquivo é um item. Com um `para`, você processa uma de cada vez:

<!--codigo:aula16_exemplo2.dk-->
```advak
seja nome = "aula16_notas.txt"
Arquivo.escrever(nome, "8\n6.5\n9\n")

seja linhas = Arquivo.ler_linhas(nome)
imprimir("Linhas:", linhas)
imprimir("Quantidade:", linhas.tamanho)

seja soma = 0
para (linha em linhas) {
    soma = soma + numero(linha)       // cada linha chega como texto
}
imprimir("Média:", soma / linhas.tamanho)

Arquivo.apagar(nome)
```

<!--saida:aula16_exemplo2.dk-->
```text
Linhas: ['8', '6.5', '9']
Quantidade: 3
Média: 7.833333333333333
```

Lembre da aula 4: o que vem de um arquivo é **texto**, então convertemos com `numero(...)` antes de somar.

## JSON: guardando mapas e listas

Arquivos de texto simples servem para frases e números soltos. Mas como guardar um cliente inteiro, com nome, idade e uma lista de telefones? Para isso existe o **JSON**: um jeito de escrever mapas e listas como texto. Parece muito com o que você já escreve na Advak:

```text
{"nome": "Ana", "idade": 17, "notas": [8, 9.5], "ativo": true}
```

Dois comandos do objeto `JSON` convertem de um lado para o outro:

- `JSON.codificar(valor)` transforma um mapa/lista em **texto JSON**;
- `JSON.decodificar(texto)` transforma texto JSON de volta em mapa/lista;
- `JSON.formatar(valor)` é como `codificar`, mas com quebras de linha e recuos, mais fácil de ler.

<!--codigo:aula16_exemplo3.dk-->
```advak
seja aluno = {"nome": "Ana", "idade": 17, "notas": [8, 9.5], "ativo": verdadeiro, "apelido": nulo}

seja texto_json = JSON.codificar(aluno)
imprimir(texto_json)
imprimir(tipo(texto_json))

imprimir(JSON.formatar(aluno))

seja volta = JSON.decodificar(texto_json)
imprimir(volta.nome, volta.notas[1], volta.ativo)
imprimir(tipo(volta))
```

<!--saida:aula16_exemplo3.dk-->
```text
{"nome": "Ana", "idade": 17, "notas": [8, 9.5], "ativo": true, "apelido": null}
texto
{
  "nome": "Ana",
  "idade": 17,
  "notas": [
    8,
    9.5
  ],
  "ativo": true,
  "apelido": null
}
Ana 9.5 verdadeiro
objeto
```

Repare que `verdadeiro` virou `true` e `nulo` virou `null` no JSON (é como o JSON escreve), e que na volta tudo retorna ao normal.

## Salvar e carregar JSON direto no arquivo

Para não precisar converter na mão, use:

- `Arquivo.escrever_json(nome, valor)` grava o valor no arquivo;
- `Arquivo.ler_json(nome)` lê o arquivo e devolve o mapa ou a lista.

Um exemplo realista, uma agenda que **lembra** os contatos entre uma execução e outra:

<!--codigo:aula16_exemplo4.dk-->
```advak
seja arquivo = "aula16_agenda.json"

função carregar() {
    se (Arquivo.existe(arquivo)) {
        retornar Arquivo.ler_json(arquivo)
    }
    retornar []                           // primeira vez: agenda vazia
}

seja agenda = carregar()
imprimir("Contatos salvos:", agenda.tamanho)

agenda.adicionar({"nome": "Bia", "telefone": "9999-1111"})
agenda.adicionar({"nome": "Caio", "telefone": "9999-2222"})
Arquivo.escrever_json(arquivo, agenda)

// Simulando "outro dia": carregamos de novo do arquivo
seja de_novo = carregar()
imprimir("Contatos depois de salvar:", de_novo.tamanho)
para (c em de_novo) {
    imprimir(`${c.nome}: ${c.telefone}`)
}

Arquivo.apagar(arquivo)
```

<!--saida:aula16_exemplo4.dk-->
```text
Contatos salvos: 0
Contatos depois de salvar: 2
Bia: 9999-1111
Caio: 9999-2222
```

> Num programa de verdade você **não** apagaria a agenda no fim: é justamente ela que guarda os dados para a próxima vez. Aqui apagamos só para o exemplo poder ser rodado quantas vezes você quiser.

## Pastas e caminhos

<!--codigo:aula16_exemplo5.dk-->
```advak
seja pasta = "aula16_pasta"
Arquivo.criar_pasta(pasta)
imprimir("É pasta?", Arquivo.info(pasta).e_pasta)

seja caminho = Arquivo.juntar(pasta, "relatorio.txt")   // monta pasta + arquivo
Arquivo.escrever(caminho, "olá")

imprimir("Arquivos na pasta:", Arquivo.listar(pasta))
imprimir("Extensão:", Arquivo.extensao(caminho))
imprimir("Sem extensão:", Arquivo.sem_extensao("foto.png"))
imprimir("Tamanho em bytes:", Arquivo.info(caminho).tamanho)

Arquivo.apagar(caminho)
```

<!--saida:aula16_exemplo5.dk-->
```text
É pasta? verdadeiro
Arquivos na pasta: ['relatorio.txt']
Extensão: .txt
Sem extensão: foto
Tamanho em bytes: 4
```

`Arquivo.juntar` usa a barra certa para o seu sistema (no Windows, `\`). A pasta `aula16_pasta` fica vazia depois do exemplo; você pode apagá-la pelo explorador de arquivos.

## Quando o arquivo não existe: `tentar`/`capturar`

Ler um arquivo que não existe dá erro. Com o que você aprendeu na aula 15, dá para tratar:

<!--codigo:aula16_exemplo6.dk-->
```advak
tentar {
    seja texto = Arquivo.ler("aula16_nao_existe.txt")
    imprimir(texto)
} capturar (e) {
    imprimir("Não consegui ler:", e)
}

// Outra opção: perguntar antes
se (Arquivo.existe("aula16_nao_existe.txt")) {
    imprimir("existe")
} senão {
    imprimir("O arquivo ainda não foi criado.")
}
```

<!--saida:aula16_exemplo6.dk-->
```text
Não consegui ler: Arquivo não encontrado: 'aula16_nao_existe.txt'
O arquivo ainda não foi criado.
```

## Erros comuns

**1. Ler um arquivo que não existe, sem tratar:**

<!--codigo:aula16_erro1.dk-->
```advak
imprimir(Arquivo.ler("aula16_fantasma.txt"))
```

Mensagem real:

<!--erro:aula16_erro1.dk-->
```text
Problema:    Arquivo não encontrado: 'aula16_fantasma.txt'
```

**Como corrigir:** confira com `Arquivo.existe` ou use `tentar`/`capturar`. Confira também se o nome está certo e se você está rodando o programa na pasta certa.

**2. Usar `escrever` quando queria `acrescentar`.** `escrever` **apaga** o que havia:

<!--codigo:aula16_erro2.dk-->
```advak
seja nome = "aula16_diario.txt"
Arquivo.escrever(nome, "Segunda: estudei\n")
Arquivo.escrever(nome, "Terça: estudei mais\n")      // substituiu a linha anterior!
imprimir(Arquivo.ler(nome))
Arquivo.apagar(nome)
```

<!--saida:aula16_erro2.dk-->
```text
Terça: estudei mais
```

**Como corrigir:** na segunda vez, use `Arquivo.acrescentar`.

**3. JSON com defeito.** Se o arquivo não for um JSON válido (por exemplo, com aspas simples ou chave sem aspas), a leitura falha:

<!--codigo:aula16_erro3.dk-->
```advak
Arquivo.escrever("aula16_ruim.json", "{nome: 'Ana'}")
tentar {
    seja dados = Arquivo.ler_json("aula16_ruim.json")
    imprimir(dados)
} capturar (e) {
    imprimir("JSON inválido:", e)
}
Arquivo.apagar("aula16_ruim.json")
```

<!--saida:aula16_erro3.dk-->
```text
JSON inválido: Erro ao ler JSON 'aula16_ruim.json': Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

**Como corrigir:** em JSON, os nomes e os textos levam **aspas duplas**: `{"nome": "Ana"}`. É mais seguro deixar a Advak escrever o arquivo, com `Arquivo.escrever_json`.

**4. Esquecer de converter o que vem do arquivo.** `ler_linhas` devolve texto: `"8" + "6"` dá `86`, não `14`. Use `numero(linha)`, como no Exemplo 2.

## Exercícios

1. Escreva as palavras `maçã`, `banana` e `uva` (uma por linha) em um arquivo e depois leia e mostre o arquivo inteiro. Apague o arquivo no fim.
2. Peça seu nome e grave `Olá, <nome>!` em um arquivo. Leia o arquivo e mostre o conteúdo.
3. Crie um arquivo com 3 números (um por linha) e mostre a soma deles, lendo com `ler_linhas`.
4. Acrescente 3 linhas, uma de cada vez, em um arquivo de "diário" e depois mostre quantas linhas ele tem.
5. Grave um mapa com `nome`, `idade` e `cidade` em um arquivo JSON, leia de volta e mostre `<nome> mora em <cidade>`.
6. Faça uma função `carregar_lista(arquivo)` que devolve a lista do JSON, ou uma lista vazia se o arquivo não existir. Teste com um arquivo que não existe.
7. Tente ler um arquivo que não existe dentro de `tentar`/`capturar` e mostre `Arquivo não encontrado.`
8. **Desafio:** faça um contador de visitas: o programa lê o número guardado em `aula16_visitas.txt` (ou começa em 0 se o arquivo não existir), soma 1, grava e mostra `Visita número N`. Rode o programa duas vezes seguidas (use duas chamadas no mesmo programa) e depois apague o arquivo.

## Respostas

**Exercício 1**

<!--codigo:aula16_resposta1.dk-->
```advak
seja nome = "aula16_frutas.txt"
Arquivo.escrever(nome, "maçã\nbanana\nuva\n")
imprimir(Arquivo.ler(nome))
Arquivo.apagar(nome)
```

<!--saida:aula16_resposta1.dk-->
```text
maçã
banana
uva
```

**Exercício 2**

<!--codigo:aula16_resposta2.dk-->
```advak
seja nome = entrada("Seu nome: ")
Arquivo.escrever("aula16_ola.txt", `Olá, ${nome}!`)
imprimir(Arquivo.ler("aula16_ola.txt"))
Arquivo.apagar("aula16_ola.txt")
```

<!--entrada:aula16_resposta2
Ana
-->
<!--saida:aula16_resposta2.dk-->
```text
Seu nome: Ana
Olá, Ana!
```

**Exercício 3**

<!--codigo:aula16_resposta3.dk-->
```advak
Arquivo.escrever("aula16_num.txt", "10\n20\n30\n")
seja soma = 0
para (linha em Arquivo.ler_linhas("aula16_num.txt")) {
    soma = soma + numero(linha)
}
imprimir("Soma:", soma)
Arquivo.apagar("aula16_num.txt")
```

<!--saida:aula16_resposta3.dk-->
```text
Soma: 60
```

**Exercício 4**

<!--codigo:aula16_resposta4.dk-->
```advak
seja nome = "aula16_diario4.txt"
Arquivo.escrever(nome, "")
Arquivo.acrescentar(nome, "Dia 1\n")
Arquivo.acrescentar(nome, "Dia 2\n")
Arquivo.acrescentar(nome, "Dia 3\n")
imprimir("Linhas:", Arquivo.ler_linhas(nome).tamanho)
Arquivo.apagar(nome)
```

<!--saida:aula16_resposta4.dk-->
```text
Linhas: 3
```

**Exercício 5**

<!--codigo:aula16_resposta5.dk-->
```advak
seja pessoa = {"nome": "Ana", "idade": 17, "cidade": "Recife"}
Arquivo.escrever_json("aula16_pessoa.json", pessoa)
seja lida = Arquivo.ler_json("aula16_pessoa.json")
imprimir(`${lida.nome} mora em ${lida.cidade}`)
Arquivo.apagar("aula16_pessoa.json")
```

<!--saida:aula16_resposta5.dk-->
```text
Ana mora em Recife
```

**Exercício 6**

<!--codigo:aula16_resposta6.dk-->
```advak
função carregar_lista(arquivo) {
    se (Arquivo.existe(arquivo)) {
        retornar Arquivo.ler_json(arquivo)
    }
    retornar []
}

imprimir(carregar_lista("aula16_nao_existe.json"))
Arquivo.escrever_json("aula16_lista.json", [1, 2, 3])
imprimir(carregar_lista("aula16_lista.json"))
Arquivo.apagar("aula16_lista.json")
```

<!--saida:aula16_resposta6.dk-->
```text
[]
[1, 2, 3]
```

**Exercício 7**

<!--codigo:aula16_resposta7.dk-->
```advak
tentar {
    Arquivo.ler("aula16_sumiu.txt")
} capturar (e) {
    imprimir("Arquivo não encontrado.")
}
```

<!--saida:aula16_resposta7.dk-->
```text
Arquivo não encontrado.
```

**Exercício 8**

<!--codigo:aula16_resposta8.dk-->
```advak
seja arquivo = "aula16_visitas.txt"

função visitar() {
    seja n = 0
    se (Arquivo.existe(arquivo)) {
        n = inteiro(Arquivo.ler(arquivo))
    }
    n = n + 1
    Arquivo.escrever(arquivo, texto(n))
    imprimir(`Visita número ${n}`)
}

visitar()
visitar()
Arquivo.apagar(arquivo)
```

<!--saida:aula16_resposta8.dk-->
```text
Visita número 1
Visita número 2
```

---

**Anterior:** [Aula 15](aula15_erros.md) · **Próxima aula:** [Aula 17 — Classes e objetos](aula17_classes.md)
