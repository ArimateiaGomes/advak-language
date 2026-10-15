# Aula 21 — Banco de dados: primeiro contato

> **Ao final desta aula você vai saber:** guardar e consultar informações em um banco de dados (SQLite) com a Advak: criar uma tabela, inserir, buscar com filtro e ordem, atualizar, apagar e contar registros.

## O que é um banco de dados

Na aula 16 você guardou dados em arquivos de texto e JSON. Funciona bem para pouca coisa. Mas imagine uma loja com 50 mil produtos: achar "todos os produtos com menos de 5 unidades em estoque" lendo um arquivo inteiro seria lento e trabalhoso.

Um **banco de dados** é um programa especializado em guardar muita informação organizada e **responder perguntas** sobre ela rapidamente. Os dados ficam em **tabelas**, parecidas com uma planilha:

| id | nome | preco | estoque |
|---|---|---|---|
| 1 | Caderno | 20.5 | 10 |
| 2 | Caneta | 3 | 100 |

- cada **linha** é um **registro** (um produto);
- cada **coluna** é um **campo** (uma informação do produto).

Existem muitos bancos (a Advak conversa com vários, veja `docs/BANCOS_DE_DADOS.md`). Aqui usamos o **SQLite**: ele guarda tudo em **um único arquivo** e **não precisa instalar nada**, perfeito para aprender.

## Conectando e criando uma tabela

<!--codigo:aula21_exemplo1.dk-->
```advak
seja arquivo = "aula21_exemplo1.db"
se (Arquivo.existe(arquivo)) {            // (só para o exemplo recomeçar do zero a cada vez)
    Arquivo.apagar(arquivo)
}

seja db = banco.conectar("sqlite:///aula21_exemplo1.db")      // abre (ou cria) o banco

db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "numero", estoque: "inteiro"})

imprimir("Produtos cadastrados:", db.contar("produtos"))
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_exemplo1.dk-->
```text
Produtos cadastrados: 0
```

- `banco.conectar("sqlite:///nome.db")` abre o banco. O começo do texto diz **qual** banco é (`sqlite:///` = arquivo SQLite).
- `db.tabela(nome, campos)` cria a tabela **se ela ainda não existir**. Cada campo tem um tipo: `texto`, `numero`, `inteiro`. `autonum` é um número que aumenta sozinho a cada registro (o `id`), e `obrigatorio` proíbe deixar o campo vazio.
- `db.contar("produtos")` diz quantos registros há na tabela.
- `db.fechar()` fecha o banco quando terminamos.

> Nos exemplos seguintes, as primeiras linhas (`se (Arquivo.existe...)`) e a última (`Arquivo.apagar`) existem **só** para o exemplo recomeçar do zero. Num sistema de verdade, você **não** apaga o banco: o objetivo é justamente guardar os dados.

## Inserindo registros

`db.inserir(tabela, mapa)` grava um registro e devolve o registro completo, já com o `id` que o banco escolheu:

<!--codigo:aula21_exemplo2.dk-->
```advak
seja arquivo = "aula21_exemplo2.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_exemplo2.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "numero", estoque: "inteiro"})

seja caderno = db.inserir("produtos", {nome: "Caderno", preco: 20.5, estoque: 10})
imprimir("Gravei:", caderno)
imprimir("O id escolhido pelo banco foi", caderno.id)

db.inserir("produtos", {nome: "Caneta", preco: 3, estoque: 100})
db.inserir("produtos", {nome: "Mochila", preco: 120, estoque: 0})
imprimir("Total:", db.contar("produtos"))

db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_exemplo2.dk-->
```text
Gravei: {nome: Caderno, preco: 20.5, estoque: 10, id: 1}
O id escolhido pelo banco foi 1
Total: 3
```

## Buscando: `buscar`, `onde`, `ordenar`

`db.buscar("tabela")` começa uma consulta. Você a refina com:

- `.onde("condição", valores...)` — só os registros que obedecem à condição;
- `.ordenar("campo")` (ou `.ordenar("campo", "desc")` para decrescente);
- `.limite(n)` — no máximo `n` registros;
- `.executar()` — roda e devolve uma **lista de mapas** (aula 10 e 11!);
- `.primeiro()` — em vez da lista, devolve só o primeiro registro (ou `nulo` se não houver).

Na condição, o `%s` marca o lugar de um valor, que vai separado depois da vírgula. Isso **protege** o banco: nunca monte a condição juntando textos de quem digitou.

<!--codigo:aula21_exemplo3.dk-->
```advak
seja arquivo = "aula21_exemplo3.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_exemplo3.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "numero", estoque: "inteiro"})
db.inserir("produtos", {nome: "Caderno", preco: 20.5, estoque: 10})
db.inserir("produtos", {nome: "Caneta", preco: 3, estoque: 100})
db.inserir("produtos", {nome: "Mochila", preco: 120, estoque: 0})

imprimir("--- todos, em ordem de nome ---")
para (p em db.buscar("produtos").ordenar("nome").executar()) {
    imprimir(`${p.id} | ${p.nome} | R$ ${p.preco} | estoque ${p.estoque}`)
}

imprimir("--- preço maior que 10 ---")
para (p em db.buscar("produtos").onde("preco > %s", 10).executar()) {
    imprimir(p.nome)
}

imprimir("--- os 2 mais caros ---")
para (p em db.buscar("produtos").ordenar("preco", "desc").limite(2).executar()) {
    imprimir(p.nome, p.preco)
}

imprimir("--- só o primeiro que bate ---")
imprimir(db.buscar("produtos").onde("nome = %s", "Caneta").primeiro())
imprimir(db.buscar("produtos").onde("nome = %s", "Inexistente").primeiro())

imprimir("--- sem estoque ---")
seja sem_estoque = db.buscar("produtos").onde("estoque = %s", 0).executar()
imprimir(sem_estoque.tamanho, "produto(s):", sem_estoque[0].nome)

db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_exemplo3.dk-->
```text
--- todos, em ordem de nome ---
1 | Caderno | R$ 20.5 | estoque 10
2 | Caneta | R$ 3 | estoque 100
3 | Mochila | R$ 120 | estoque 0
--- preço maior que 10 ---
Caderno
Mochila
--- os 2 mais caros ---
Mochila 120
Caderno 20.5
--- só o primeiro que bate ---
{id: 2, nome: Caneta, preco: 3, estoque: 100}
nulo
--- sem estoque ---
1 produto(s): Mochila
```

As condições usam a linguagem do banco (SQL): por isso se escreve `AND` e `OR` (em inglês) para combinar condições, e `LIKE` para procurar pedaços de texto (`"nome LIKE %s", "%ca%"` acha nomes que contêm `ca`).

## Atualizando e apagando

- `db.atualizar("tabela", {campo: novo_valor}).onde(...).executar()` muda registros e devolve **quantos** mudaram;
- `db.deletar("tabela").onde(...).executar()` apaga e devolve quantos apagou.

<!--codigo:aula21_exemplo4.dk-->
```advak
seja arquivo = "aula21_exemplo4.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_exemplo4.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "numero", estoque: "inteiro"})
db.inserir("produtos", {nome: "Caderno", preco: 20.5, estoque: 10})
db.inserir("produtos", {nome: "Caneta", preco: 3, estoque: 100})
db.inserir("produtos", {nome: "Mochila", preco: 120, estoque: 0})

seja mudou = db.atualizar("produtos", {estoque: 5}).onde("nome = %s", "Mochila").executar()
imprimir("Registros alterados:", mudou)
imprimir("Estoque da mochila agora:", db.buscar("produtos").onde("nome = %s", "Mochila").primeiro().estoque)

seja apagou = db.deletar("produtos").onde("nome = %s", "Caneta").executar()
imprimir("Registros apagados:", apagou)
imprimir("Restaram:", db.contar("produtos"))

db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_exemplo4.dk-->
```text
Registros alterados: 1
Estoque da mochila agora: 5
Registros apagados: 1
Restaram: 2
```

## Os dados continuam lá

A grande diferença para variáveis: o que está no banco **sobrevive**. Fechamos a conexão, abrimos de novo, e os registros continuam:

<!--codigo:aula21_exemplo5.dk-->
```advak
seja arquivo = "aula21_exemplo5.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}

seja db = banco.conectar("sqlite:///aula21_exemplo5.db")
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.inserir("clientes", {nome: "Ana", cidade: "Recife"})
db.inserir("clientes", {nome: "Bruno", cidade: "Natal"})
imprimir("Antes de fechar:", db.contar("clientes"))
db.fechar()

// Como se fosse "outro dia": abre de novo
seja db2 = banco.conectar("sqlite:///aula21_exemplo5.db")
db2.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})     // já existe: nada é perdido
imprimir("Depois de abrir de novo:", db2.contar("clientes"))
para (c em db2.buscar("clientes").ordenar("nome").executar()) {
    imprimir(`${c.nome} mora em ${c.cidade}`)
}
db2.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_exemplo5.dk-->
```text
Antes de fechar: 2
Depois de abrir de novo: 2
Ana mora em Recife
Bruno mora em Natal
```

Isso é o que permite programas como o cadastro de clientes do [guia prático, capítulo 3](../GUIA_PRATICO.md#capítulo-3--cadastro-de-clientes-com-banco-de-dados): ele guarda tudo no banco e, na próxima vez que abrir, os clientes continuam lá.

## Erros comuns

**1. Deixar um campo obrigatório vazio:**

<!--codigo:aula21_erro1.dk-->
```advak
seja arquivo = "aula21_erro1.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_erro1.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "numero"})
tentar {
    db.inserir("produtos", {preco: 5})
} capturar (e) {
    imprimir("Não gravou:", e)
}
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_erro1.dk-->
```text
Não gravou: Erro no SQLite: NOT NULL constraint failed: produtos.nome
```

**Como corrigir:** informe o campo `nome` ao inserir.

**2. Usar uma tabela ou um campo que não existe:**

<!--codigo:aula21_erro2.dk-->
```advak
seja arquivo = "aula21_erro2.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_erro2.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio"})
tentar {
    db.buscar("produto").executar()                       // faltou o "s"
} capturar (e) {
    imprimir("Tabela:", e)
}
tentar {
    db.inserir("produtos", {nome: "X", cor: "azul"})       // não existe o campo cor
} capturar (e) {
    imprimir("Campo:", e)
}
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_erro2.dk-->
```text
Tabela: Erro no SQLite: no such table: produto
Campo: Erro no SQLite: table produtos has no column named cor
```

**Como corrigir:** confira os nomes das tabelas e campos com o que você escreveu em `db.tabela(...)`.

**3. Atualizar ou apagar sem `onde`.** Sem condição, o comando vale para **todos** os registros:

<!--codigo:aula21_erro3.dk-->
```advak
seja arquivo = "aula21_erro3.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_erro3.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", estoque: "inteiro"})
db.inserir("produtos", {nome: "Caderno", estoque: 10})
db.inserir("produtos", {nome: "Caneta", estoque: 100})

seja n = db.atualizar("produtos", {estoque: 0}).executar()      // faltou o .onde(...)
imprimir("Registros alterados:", n)
imprimir(db.buscar("produtos").executar())
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_erro3.dk-->
```text
Registros alterados: 2
[{id: 1, nome: Caderno, estoque: 0}, {id: 2, nome: Caneta, estoque: 0}]
```

**Como corrigir:** sempre confira se `atualizar` e `deletar` têm o `.onde(...)`. É o erro mais caro em bancos de dados!

**4. Montar a condição juntando texto.** Em vez de `.onde("nome = '" + nome + "'")`, use `.onde("nome = %s", nome)`. O primeiro jeito permite que alguém digite um texto malicioso e mexa no seu banco (*injeção de SQL*); o segundo é seguro.

## Exercícios

1. Crie uma tabela `alunos` com `id` (autonum), `nome` (texto obrigatório) e `nota` (numero). Insira 3 alunos e mostre quantos há.
2. Mostre todos os alunos do exercício 1, em ordem alfabética.
3. Mostre apenas os alunos com nota maior ou igual a 7.
4. Mostre o aluno com a maior nota (use `ordenar` em ordem decrescente e `primeiro()`).
5. Mude a nota de um aluno e mostre a nota nova.
6. Apague um aluno pelo nome e mostre quantos restaram.
7. Peça um nome e uma nota, grave no banco e mostre o `id` que o banco escolheu.
8. **Desafio:** monte um mini-cadastro: grave 3 produtos, depois calcule o valor total do estoque (`preco * estoque` somados) percorrendo o resultado de `buscar`.

## Respostas

**Exercício 1**

<!--codigo:aula21_resposta1.dk-->
```advak
seja arquivo = "aula21_resposta1.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_resposta1.db")
db.tabela("alunos", {id: "autonum", nome: "texto obrigatorio", nota: "numero"})
db.inserir("alunos", {nome: "Carlos", nota: 6.5})
db.inserir("alunos", {nome: "Ana", nota: 9})
db.inserir("alunos", {nome: "Beatriz", nota: 7})
imprimir("Alunos:", db.contar("alunos"))
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_resposta1.dk-->
```text
Alunos: 3
```

**Exercício 2**

<!--codigo:aula21_resposta2.dk-->
```advak
seja arquivo = "aula21_resposta2.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_resposta2.db")
db.tabela("alunos", {id: "autonum", nome: "texto obrigatorio", nota: "numero"})
db.inserir("alunos", {nome: "Carlos", nota: 6.5})
db.inserir("alunos", {nome: "Ana", nota: 9})
db.inserir("alunos", {nome: "Beatriz", nota: 7})

para (a em db.buscar("alunos").ordenar("nome").executar()) {
    imprimir(a.nome, a.nota)
}
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_resposta2.dk-->
```text
Ana 9
Beatriz 7
Carlos 6.5
```

**Exercício 3**

<!--codigo:aula21_resposta3.dk-->
```advak
seja arquivo = "aula21_resposta3.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_resposta3.db")
db.tabela("alunos", {id: "autonum", nome: "texto obrigatorio", nota: "numero"})
db.inserir("alunos", {nome: "Carlos", nota: 6.5})
db.inserir("alunos", {nome: "Ana", nota: 9})
db.inserir("alunos", {nome: "Beatriz", nota: 7})

para (a em db.buscar("alunos").onde("nota >= %s", 7).ordenar("nome").executar()) {
    imprimir(a.nome, a.nota)
}
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_resposta3.dk-->
```text
Ana 9
Beatriz 7
```

**Exercício 4**

<!--codigo:aula21_resposta4.dk-->
```advak
seja arquivo = "aula21_resposta4.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_resposta4.db")
db.tabela("alunos", {id: "autonum", nome: "texto obrigatorio", nota: "numero"})
db.inserir("alunos", {nome: "Carlos", nota: 6.5})
db.inserir("alunos", {nome: "Ana", nota: 9})
db.inserir("alunos", {nome: "Beatriz", nota: 7})

seja melhor = db.buscar("alunos").ordenar("nota", "desc").primeiro()
imprimir(`Maior nota: ${melhor.nome} com ${melhor.nota}`)
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_resposta4.dk-->
```text
Maior nota: Ana com 9
```

**Exercício 5**

<!--codigo:aula21_resposta5.dk-->
```advak
seja arquivo = "aula21_resposta5.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_resposta5.db")
db.tabela("alunos", {id: "autonum", nome: "texto obrigatorio", nota: "numero"})
db.inserir("alunos", {nome: "Carlos", nota: 6.5})

db.atualizar("alunos", {nota: 8}).onde("nome = %s", "Carlos").executar()
imprimir("Nota nova:", db.buscar("alunos").onde("nome = %s", "Carlos").primeiro().nota)
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_resposta5.dk-->
```text
Nota nova: 8
```

**Exercício 6**

<!--codigo:aula21_resposta6.dk-->
```advak
seja arquivo = "aula21_resposta6.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_resposta6.db")
db.tabela("alunos", {id: "autonum", nome: "texto obrigatorio", nota: "numero"})
db.inserir("alunos", {nome: "Carlos", nota: 6.5})
db.inserir("alunos", {nome: "Ana", nota: 9})
db.inserir("alunos", {nome: "Beatriz", nota: 7})

db.deletar("alunos").onde("nome = %s", "Carlos").executar()
imprimir("Restaram:", db.contar("alunos"))
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_resposta6.dk-->
```text
Restaram: 2
```

**Exercício 7**

<!--codigo:aula21_resposta7.dk-->
```advak
seja arquivo = "aula21_resposta7.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_resposta7.db")
db.tabela("alunos", {id: "autonum", nome: "texto obrigatorio", nota: "numero"})

seja nome = entrada("Nome: ")
seja nota = numero(entrada("Nota: "))
seja gravado = db.inserir("alunos", {nome: nome, nota: nota})
imprimir(`Gravei ${gravado.nome} com o id ${gravado.id}`)
db.fechar()
Arquivo.apagar(arquivo)
```

<!--entrada:aula21_resposta7
Marina
8.5
-->
<!--saida:aula21_resposta7.dk-->
```text
Nome: Marina
Nota: 8.5
Gravei Marina com o id 1
```

**Exercício 8**

<!--codigo:aula21_resposta8.dk-->
```advak
seja arquivo = "aula21_resposta8.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = banco.conectar("sqlite:///aula21_resposta8.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "numero", estoque: "inteiro"})
db.inserir("produtos", {nome: "Caderno", preco: 20, estoque: 10})
db.inserir("produtos", {nome: "Caneta", preco: 3, estoque: 100})
db.inserir("produtos", {nome: "Mochila", preco: 120, estoque: 2})

seja total = 0
para (p em db.buscar("produtos").executar()) {
    total = total + p.preco * p.estoque
}
imprimir("Valor total do estoque: R$", total)
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula21_resposta8.dk-->
```text
Valor total do estoque: R$ 740
```

---

**Anterior:** [Aula 20](aula20_testes.md) · **Próxima aula:** [Aula 22 — Interface gráfica: primeira janela](aula22_interface_grafica.md)
