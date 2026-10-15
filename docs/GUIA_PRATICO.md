# Desenvolvendo aplicações do dia a dia com Advak

Neste guia você vai construir **13 aplicativos completos**, um por capítulo. Todos estão prontos na pasta `exemplos/`, e **cada um foi executado com a Advak** antes de entrar aqui. As saídas mostradas são as reais.

> **Como usar:** abra o terminal na pasta da Advak e rode `advak exemplos/NOME.dk`. Se ainda não instalou, veja [INSTALACAO.md](INSTALACAO.md). Leia o código, rode, mude uma coisa e rode de novo: é assim que se aprende.

## Índice

1. [Calculadora de médias escolares](#capítulo-1--calculadora-de-médias-escolares)
2. [Controle de gastos pessoais (arquivo JSON)](#capítulo-2--controle-de-gastos-pessoais)
3. [Cadastro de clientes com banco de dados (CRUD)](#capítulo-3--cadastro-de-clientes-crud)
4. [Controle de estoque com interface gráfica](#capítulo-4--controle-de-estoque-com-interface-gráfica)
5. [API REST de tarefas com servidor web](#capítulo-5--api-rest-de-tarefas)
6. [Relatório que lê um CSV](#capítulo-6--relatório-a-partir-de-um-csv)
7. [Agenda de contatos com busca](#capítulo-7--agenda-de-contatos-com-busca)
8. [Testes unitários para validar regras](#capítulo-8--testes-unitários)
9. [O mesmo cadastro trocando só a conexão](#capítulo-9--trocando-só-a-string-de-conexão)
10. [Relatório de vendas em SQL Server ou Firebird](#capítulo-10--relatório-de-vendas-em-sql-server-ou-firebird)
11. [Cache de consultas com Redis](#capítulo-11--cache-de-consultas-com-redis)
12. [Catálogo de produtos com MongoDB](#capítulo-12--catálogo-de-produtos-com-mongodb)
13. [PDV didático: cadastro, venda, troco e relatório do dia](#capítulo-13--pdv-didático)

Antes de começar, leia a seção [Palavras reservadas](#palavras-reservadas): ela evita o erro mais comum de quem está começando.

### O que foi testado de verdade

| Capítulo | Situação |
|---|---|
| 1, 2, 3, 5, 6, 7, 8, 9, 10, 13 | **Executados de verdade** (os de banco, com SQLite). |
| 4 | Executado de verdade: a janela abre, o cadastro grava no SQLite e o resumo é atualizado. Os cliques em "Dar baixa" e "Excluir" **não** foram simulados. |
| 9 (MySQL, SQL Server) e 10 (SQL Server, Firebird) | **Não testados** nesses bancos (só com SQLite). Não há servidor desses bancos neste computador. |
| 11 (Redis) e 12 (MongoDB) | **Só simulados**: rodaram contra um Redis e um MongoDB de mentira em memória (`testes/rodar_simulado.py`). Prova que o código está certo, **não** que o banco real responde igual. |

---

## Palavras reservadas

Palavras reservadas são palavras que a Advak já usa para o próprio funcionamento da linguagem (`se`, `para`, `classe`...). **Você não pode usá-las como nome de variável ou função.** Se tentar, o erro é este (real):

```advak
seja endereco = "Rua A"
```

```
SyntaxError: [Advak] Linha 1: esperado 'IDENT', encontrado 'endereco'
```

O erro fala em "IDENT" (identificador, isto é, um nome) porque a Advak esperava um nome e encontrou uma palavra reservada. `endereco` parece inocente, mas é reservada (ligada a ponteiros). O mesmo vale para `continuar`, `de`, `como`, `tela`, `regra`, `fato` e outras. **Como corrigir:** escolha outro nome, como `rua`, `url_banco` ou `local_da_entrega`.

**Os nomes têm acento.** A Advak diferencia letras com e sem acento: `função`, `senão`, `padrão` e `lançar` são palavras da linguagem. Algumas têm também a versão sem acento (`funcao`, `senao`, `lancar`), mas **`padrão` só funciona com acento** dentro do `combinar`. Isso vale para os seus nomes também: `media` e `média` são duas variáveis diferentes, e você pode usar acentos nos nomes (`seja média = 8`). Dica para iniciantes: escolha um jeito (com ou sem acento) e use sempre igual, para não criar duas variáveis por engano.

Lista completa (tirada do analisador léxico da Advak, `advak_lexer.py`):

| Grupo | Palavras reservadas |
|---|---|
| Valores e variáveis | `seja` `fixo` `verdadeiro` `falso` `nulo` `let` `const` `var` `true` `false` `null` |
| Decisão | `se` `senão` `senao` `entao` `combinar` `caso` `padrão` `if` `else` `match` `switch` `case` `default` |
| Repetição e geradores | `enquanto` `para` `quebrar` `continuar` `while` `for` `break` `continue` `in` `of` `produzir` `gerador` `yield` `generator` |
| Funções e classes | `função` `funcao` `retornar` `return` `function` `classe` `isso` `herda` `class` `extends` `this` `super` `instanceof` `e_instancia` `eh_instancia` `compor` `puro` `imutavel` `congelar` `inline` `macro` `definir` |
| Tarefas assíncronas | `async` `await` `assincrona` `aguarda` |
| Módulos e erros | `importar` `exportar` `de` `como` `tentar` `capturar` `pegar` `finalmente` `lançar` `lancar` `try` `catch` `finally` `throw` |
| Entrada e saída | `imprimir` `print` `input` |
| Dados avançados | `estrutura` `struct` `enumeracao` `enum` `ref` `deref` `endereco` `variante` `extrair` |
| Lógica e desenho | `fato` `regra` `consultar` `retroceder` `fact` `rule` `query` `backtrack` `tela` `desenhar` |
| Inteligência artificial | `ai_perguntar` `ai_classificar` `ai_transformar` `ai_resumir` `ai_gerar` `ai_ask` `ai_classify` `ai_transform` `ai_summarize` `ai_generate` |

Todas as palavras desta tabela foram testadas: cada uma, usada como nome em `seja palavra = 1`, dá o erro acima. Note que `entrada`, `inteiro`, `numero`, `moeda` e `texto` **não** são reservadas (são funções), mas é melhor não usá-las como nome de variável para não esconder a função.

---

## Capítulo 1 — Calculadora de médias escolares

**Arquivo:** `exemplos/01_medias.dk`  ·  **Você vai aprender:** funções, listas, repetição, decisão.

```advak
função media(notas) {                       // 1
    seja soma = 0                           // 2
    para (n em notas) {                     // 3
        soma += n                           // 4
    }
    retornar soma / notas.tamanho           // 5
}

função situacao(m) {                        // 6
    se (m >= 7) {
        retornar "Aprovado"
    } senão se (m >= 5) {
        retornar "Recuperação"
    } senão {
        retornar "Reprovado"
    }
}

imprimir("=== Calculadora de médias ===")
seja nome = entrada("Nome do aluno: ")                       // 7
seja quantas = inteiro(entrada("Quantas notas? "))           // 8

seja notas = []                                              // 9
para (i em 1..=quantas) {                                    // 10
    seja n = numero(entrada(`Nota ${i}: `))                  // 11
    notas.adicionar(n)                                       // 12
}

seja m = media(notas)
imprimir("")
imprimir(`Aluno: ${nome}`)
imprimir(`Média: ${arred(m, 2)}`)                            // 13
imprimir(`Maior nota: ${Mat.max(notas)}  |  Menor nota: ${Mat.min(notas)}`)
imprimir(`Situação: ${situacao(m)}`)
```

**Explicação linha a linha**

1. `função media(notas)` cria uma "receita" chamada `media` que recebe uma lista de notas.
2. `seja soma = 0` cria uma variável para acumular o total.
3. `para (n em notas)` repete o bloco uma vez para cada nota da lista; em cada volta, `n` vale uma nota.
4. `soma += n` é o mesmo que `soma = soma + n`.
5. `retornar` devolve o resultado: soma dividida pela quantidade de notas (`notas.tamanho`).
6. `situacao` usa `se / senão se / senão` para escolher entre três textos.
7. `entrada("...")` mostra a pergunta e espera você digitar. O que vem é sempre **texto**.
8. `inteiro(...)` transforma o texto em número inteiro (quantidade de notas).
9. `[]` é uma lista vazia, onde vamos guardar as notas.
10. `1..=quantas` vai de 1 até `quantas`, **incluindo** o último (sem o `=`, pararia um antes).
11. A crase `` ` `` cria um texto com `${...}`, que insere o valor de uma variável. `numero(...)` aceita decimais.
12. `adicionar` coloca o valor no fim da lista.
13. `arred(m, 2)` arredonda para 2 casas decimais.

**Saída real** (digitando `Ana`, `3`, `8`, `6.5`, `9`):

```
=== Calculadora de médias ===
Nome do aluno: Ana
Quantas notas? 3
Nota 1: 8
Nota 2: 6.5
Nota 3: 9

Aluno: Ana
Média: 7.83
Maior nota: 9  |  Menor nota: 6.5
Situação: Aprovado
```

**Exercício:** mude o programa para também mostrar quantas notas ficaram **abaixo de 5**. Dica: crie uma variável `baixas = 0` e some 1 dentro do `para` quando `n < 5`.

---

## Capítulo 2 — Controle de gastos pessoais

**Arquivo:** `exemplos/02_gastos.dk`  ·  **Você vai aprender:** `enquanto`, mapas, ler e gravar arquivo JSON.

```advak
fixo ARQUIVO = "exemplos/dados/gastos.json"      // 1

função carregar() {
    se (Arquivo.existe(ARQUIVO)) {               // 2
        retornar Arquivo.ler_json(ARQUIVO)       // 3
    }
    retornar []                                  // 4
}

função salvar(gastos) {
    Arquivo.escrever_json(ARQUIVO, gastos)       // 5
}

função total(gastos) {
    seja soma = 0
    para (g em gastos) {
        soma += g.valor                          // 6
    }
    retornar soma
}

seja gastos = carregar()
imprimir(`Gastos já salvos: ${gastos.tamanho}`)

seja mais_gastos = verdadeiro
enquanto (mais_gastos) {                         // 7
    seja descricao = entrada("Descrição (vazio para terminar): ")
    se (descricao == "") {
        mais_gastos = falso                      // 8
    } senão {
        seja valor = numero(entrada("Valor em R$: "))
        gastos.adicionar({descricao: descricao, valor: valor})   // 9
    }
}

salvar(gastos)

imprimir("")
imprimir("=== Seus gastos ===")
para (g em gastos) {
    imprimir(`${g.descricao}: ${moeda(g.valor)}`)   // 10
}
imprimir(`TOTAL: ${moeda(total(gastos))}`)
```

**Explicação**

1. `fixo` cria uma constante: o valor não muda. Por convenção, o nome fica em maiúsculas.
2. `Arquivo.existe` confere se o arquivo já foi criado (na primeira vez, não foi).
3. `Arquivo.ler_json` lê o arquivo e já devolve uma lista de mapas.
4. Se não existe, começamos com uma lista vazia.
5. `Arquivo.escrever_json` grava a lista inteira no arquivo, em formato JSON.
6. Cada gasto é um **mapa** (`{descricao, valor}`); `g.valor` pega o campo `valor`.
7. `enquanto` repete **enquanto** a condição for verdadeira.
8. Quando a pessoa aperta Enter sem digitar nada, desligamos a "chave" e o laço termina.
9. `{descricao: descricao, valor: valor}` monta um mapa novo e `adicionar` põe na lista.
10. `moeda(...)` escreve como dinheiro brasileiro (`R$ 85,50`).

**Saída real** (1ª execução: `Mercado` 85.5, `Ônibus` 12; depois uma 2ª execução: `Lanche` 9.9):

```
Gastos já salvos: 0
Descrição (vazio para terminar): Mercado
Valor em R$: 85.5
Descrição (vazio para terminar): Ônibus
Valor em R$: 12
Descrição (vazio para terminar):

=== Seus gastos ===
Mercado: R$ 85,50
Ônibus: R$ 12,00
TOTAL: R$ 97,50
```

Na 2ª execução, o programa começa com `Gastos já salvos: 2` e o total sobe para `R$ 107,40`: os dados ficaram guardados no arquivo.

**Exercício:** peça também a **categoria** (mercado, transporte...) e, no fim, mostre o total só da categoria "mercado".

---

## Capítulo 3 — Cadastro de clientes (CRUD)

**Arquivo:** `exemplos/03_clientes_banco.dk`  ·  **Você vai aprender:** banco de dados, menu, `combinar`.

CRUD quer dizer **C**riar, **R**ler, **A**tualizar (*Update*) e **D**eletar. Usamos o SQLite, que guarda tudo em um arquivo e não precisa instalar nada. Para usar o PostgreSQL, troque **só** a linha da conexão (veja o [Capítulo 9](#capítulo-9--trocando-só-a-string-de-conexão)).

```advak
seja db = banco.conectar("sqlite:///exemplos/dados/clientes.db")                // 1
db.tabela("clientes", {id: "autonum", nome: "texto obrigatorio", cidade: "texto", telefone: "texto"})   // 2

função listar() {
    seja todos = db.buscar("clientes").ordenar("nome").executar()               // 3
    se (todos.tamanho == 0) {
        imprimir("  (nenhum cliente cadastrado)")
    }
    para (c em todos) {
        imprimir(`  ${c.id} | ${c.nome} | ${c.cidade} | ${c.telefone}`)
    }
}

função cadastrar() {
    seja nome = entrada("  Nome: ")
    seja cidade = entrada("  Cidade: ")
    seja telefone = entrada("  Telefone: ")
    seja novo = db.inserir("clientes", {nome: nome, cidade: cidade, telefone: telefone})   // 4
    imprimir(`  Cliente ${novo.nome} cadastrado com o número ${novo.id}.`)
}

função alterar() {
    seja id = inteiro(entrada("  Número do cliente: "))
    seja telefone = entrada("  Novo telefone: ")
    seja n = db.atualizar("clientes", {telefone: telefone}).onde("id = %s", id).executar()  // 5
    imprimir(`  ${n} cliente(s) alterado(s).`)
}

função apagar() {
    seja id = inteiro(entrada("  Número do cliente: "))
    seja n = db.deletar("clientes").onde("id = %s", id).executar()              // 6
    imprimir(`  ${n} cliente(s) apagado(s).`)
}

imprimir("=== Cadastro de clientes ===")
seja rodando = verdadeiro
enquanto (rodando) {
    imprimir("")
    imprimir("1) Listar  2) Cadastrar  3) Alterar telefone  4) Apagar  0) Sair")
    seja opcao = entrada("Escolha: ")
    combinar(opcao) {                                                           // 7
        caso "1": listar()
        caso "2": cadastrar()
        caso "3": alterar()
        caso "4": apagar()
        caso "0": rodando = falso
        padrão:   imprimir("  Opção inválida.")
    }
}
imprimir(`Total de clientes: ${db.contar("clientes")}`)                         // 8
db.fechar()                                                                     // 9
```

**Explicação**

1. `banco.conectar` abre o banco. O começo do texto (`sqlite:///`) diz **qual** banco é.
2. `db.tabela` cria a tabela **se ainda não existir**. `autonum` é um número que aumenta sozinho; `obrigatorio` proíbe campo vazio.
3. `buscar(...).ordenar("nome").executar()` é um "SELECT": devolve uma lista de mapas, já em ordem de nome.
4. `inserir` grava e devolve o registro já com o `id` que o banco escolheu.
5. `atualizar(...).onde(...)` muda só as linhas que obedecem à condição. O `%s` é um espaço reservado: o valor vai separado, o que **protege contra ataques** (injeção de SQL). Nunca monte a condição juntando texto. Devolve quantas linhas mudaram.
6. `deletar(...).onde(...)` apaga; também devolve a quantidade.
7. `combinar` escolhe o `caso` igual ao valor; `padrão` roda se nenhum servir.
8. `contar` diz quantas linhas a tabela tem.
9. `fechar` encerra a conexão.

**Saída real** (opções digitadas: `1`, `2` Ana, `2` Bruno, `1`, `3`, `4`, `1`, `0`):

```
=== Cadastro de clientes ===

1) Listar  2) Cadastrar  3) Alterar telefone  4) Apagar  0) Sair
Escolha: 1
  (nenhum cliente cadastrado)

1) Listar  2) Cadastrar  3) Alterar telefone  4) Apagar  0) Sair
Escolha: 2
  Nome: Ana
  Cidade: Picos
  Telefone: 89999
  Cliente Ana cadastrado com o número 1.
...
Escolha: 3
  Número do cliente: 2
  Novo telefone: 8777
  1 cliente(s) alterado(s).
...
Escolha: 4
  Número do cliente: 1
  1 cliente(s) apagado(s).

Escolha: 1
  2 | Bruno | Teresina | 8777

Escolha: 0
Total de clientes: 1
```

**Exercício:** acrescente a opção `5) Buscar por cidade`, usando `db.buscar("clientes").onde("cidade = %s", cidade).executar()`.

---

## Capítulo 4 — Controle de estoque com interface gráfica

**Arquivo:** `exemplos/04_estoque_gui.dk`  ·  **Você vai aprender:** janela, tabela, campos e botões.

```advak
seja db = banco.conectar("sqlite:///exemplos/dados/estoque.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", quantidade: "inteiro padrao 0", preco: "decimal padrao 0"})

seja jan = gui.janela("Controle de Estoque", 720, 520)       // 1
jan.centralizar()

gui.label(jan, "Controle de Estoque", negrito=verdadeiro)    // 2
seja tabela = gui.tabela(jan, ["ID", "Produto", "Quantidade", "Preço"], altura=10)   // 3

seja campo_nome  = gui.campo(jan, "Nome do produto", largura=30)   // 4
seja campo_qtd   = gui.campo(jan, "Quantidade", largura=10)
seja campo_preco = gui.campo(jan, "Preço (ex: 12.5)", largura=10)
seja resumo      = gui.label(jan, "")

função atualizar_tela() {                                    // 5
    seja todos = db.buscar("produtos").ordenar("nome").executar()
    tabela.limpar()
    seja valor_total = 0
    para (p em todos) {
        tabela.adicionar([p.id, p.nome, p.quantidade, moeda(p.preco)])
        valor_total += p.quantidade * p.preco
    }
    resumo.texto(`${todos.tamanho} produtos | valor em estoque: ${moeda(valor_total)}`)   // 6
}

função cadastrar() {
    se (campo_nome.valor() == "") {
        gui.erro("O nome é obrigatório!")                    // 7
        retornar
    }
    tentar {
        db.inserir("produtos", {nome: campo_nome.valor(), quantidade: inteiro(campo_qtd.valor()), preco: numero(campo_preco.valor())})
        campo_nome.limpar()
        campo_qtd.limpar()
        campo_preco.limpar()
        atualizar_tela()
    } capturar (e) {
        gui.erro("Quantidade e preço precisam ser números.") // 8
    }
}

função dar_baixa() {
    seja escolhido = tabela.selecionado()                    // 9
    se (escolhido == nulo) {
        gui.aviso("Selecione um produto na tabela.")
        retornar
    }
    seja qtd = inteiro(escolhido["Quantidade"])
    se (qtd <= 0) {
        gui.aviso("Este produto já está sem estoque.")
        retornar
    }
    db.atualizar("produtos", {quantidade: qtd - 1}).onde("id = %s", inteiro(escolhido["ID"])).executar()
    atualizar_tela()
}

função excluir() {
    seja escolhido = tabela.selecionado()
    se (escolhido == nulo) {
        gui.aviso("Selecione um produto na tabela.")
        retornar
    }
    se (gui.confirmar(`Excluir "${escolhido["Produto"]}"?`)) {   // 10
        db.deletar("produtos").onde("id = %s", inteiro(escolhido["ID"])).executar()
        atualizar_tela()
    }
}

seja botoes = gui.frame_horizontal(jan)
gui.botao(botoes, "Cadastrar", (x) => { cadastrar() }, estilo="sucesso")        // 11
gui.botao(botoes, "Dar baixa (-1)", (x) => { dar_baixa() })
gui.botao(botoes, "Excluir", (x) => { excluir() }, estilo="perigo")

atualizar_tela()
gui.iniciar()                                                // 12
```

**Explicação**

1. `gui.janela(título, largura, altura)` cria a janela; `centralizar` a põe no meio da tela.
2. `gui.label` escreve um texto na janela.
3. `gui.tabela` cria a grade; o segundo argumento são os títulos das colunas.
4. `gui.campo` é uma caixinha de digitação com uma dica escrita dentro.
5. Sempre que o banco muda, chamamos `atualizar_tela()`: ela limpa a tabela e desenha tudo de novo, com o valor total do estoque.
6. Para trocar o texto de um `label` usa-se `.texto(...)`.
7. `gui.erro` abre uma janelinha de erro.
8. Se o aluno digitar letras em Quantidade, `inteiro("abc")` **não dá erro**: devolve `0` (e `inteiro("3.7")` devolve `3`, cortando a parte decimal). Por isso o `capturar` só pega outros problemas, como uma falha ao gravar no banco. O jeito seguro é conferir antes com `e_numero(texto)`, que responde `falso` para `"abc"` e `verdadeiro` para `"12"` e `"3.7"`, e só então converter. Veja a [aula 15 do curso](curso/aula15_erros.md).
9. `tabela.selecionado()` devolve a linha clicada como um mapa (`escolhido["Produto"]`) ou `nulo` se nada foi clicado.
10. `gui.confirmar` pergunta Sim/Não e devolve verdadeiro ou falso.
11. Cada botão recebe uma função que roda ao clicar. `estilo` muda a cor.
12. `gui.iniciar()` deixa a janela aberta esperando seus cliques. **Deve ser a última linha.**

**O que você vê:** uma janela com a tabela no alto, três campos e três botões. Ao cadastrar `Caderno` (10 unidades, 12.5) e `Caneta` (2 unidades, 2), o resumo mostra: `2 produtos | valor em estoque: R$ 129,00`.

**Exercício:** adicione o botão **"Dar entrada (+1)"**, que soma 1 à quantidade do produto selecionado.

---

## Capítulo 5 — API REST de tarefas

**Arquivo:** `exemplos/05_api_tarefas.dk`  ·  **Você vai aprender:** servidor web, rotas, códigos de status.

Uma **API** é um "balcão" que outros programas (um site, um aplicativo de celular) usam para pedir e enviar dados, geralmente em JSON.

```advak
seja db = banco.conectar("sqlite:///exemplos/dados/tarefas.db")
db.tabela("tarefas", {id: "autonum", titulo: "texto obrigatorio", feita: "booleano padrao falso"})

servidor.obter("/api/tarefas", (req) => {                                     // 1
    retornar resposta_json(db.buscar("tarefas").ordenar("id").executar())     // 2
})

servidor.obter("/api/tarefas/:id", (req) => {                                 // 3
    seja t = db.buscar_id("tarefas", inteiro(req.parametros.id))
    se (t == nulo ou t.tamanho == 0) {
        retornar resposta_json({erro: "tarefa não encontrada"}, 404)          // 4
    }
    retornar resposta_json(t)
})

servidor.publicar("/api/tarefas", (req) => {                                  // 5
    se (req.dados == nulo ou !req.dados.titulo) {
        retornar resposta_json({erro: "informe o titulo"}, 400)
    }
    seja nova = db.inserir("tarefas", {titulo: req.dados.titulo, feita: falso})
    retornar resposta_json(nova, 201)
})

servidor.atualizar("/api/tarefas/:id", (req) => { ... })    // PUT
servidor.deletar("/api/tarefas/:id", (req) => { ... })      // DELETE

servidor.iniciar(8080, falso)                                                 // 6
```

(O arquivo completo, com a página inicial e as rotas de `PUT` e `DELETE`, está em `exemplos/05_api_tarefas.dk`.)

**Explicação**

1. `servidor.obter(caminho, função)` responde a pedidos **GET** (ler). A função recebe `req`, o pedido.
2. `resposta_json` devolve os dados em JSON.
3. `:id` no caminho é uma parte variável: em `/api/tarefas/3`, `req.parametros.id` vale `3`.
4. O segundo argumento de `resposta_json` é o **código de status**: 200 = deu certo, 201 = criado, 400 = pedido errado, 404 = não existe.
5. `servidor.publicar` responde a **POST** (criar); o JSON enviado chega em `req.dados`. Os outros: `atualizar` = PUT, `deletar` = DELETE.
6. `servidor.iniciar(8080, falso)` liga o servidor na porta 8080. Pare com `Ctrl+C`.

**Teste real:** com o servidor ligado, o script `testes/cliente_api_tarefas.py` fez estas chamadas e recebeu:

```
GET /api/tarefas                          -> 200 []
POST /api/tarefas {"titulo": "Estudar Advak"}  -> 201 {"titulo": "Estudar Advak", "feita": false, "id": 1}
POST /api/tarefas {}                      -> 400 {"erro": "informe o titulo"}
GET /api/tarefas/1                        -> 200 {"id": 1, "titulo": "Estudar Advak", "feita": 0}
PUT /api/tarefas/1 {"feita": true}        -> 200 {"ok": true}
GET /api/tarefas/99                       -> 404 {"erro": "tarefa não encontrada"}
DELETE /api/tarefas/2                     -> 200 {"ok": true}
```

Você também pode abrir `http://localhost:8080/api/tarefas` no navegador.

**Exercício:** crie a rota `GET /api/tarefas/pendentes`, que devolve só as tarefas com `feita = falso`. (Cuidado: coloque-a **antes** da rota `/api/tarefas/:id`.)

---

## Capítulo 6 — Relatório a partir de um CSV

**Arquivo:** `exemplos/06_relatorio_csv.dk` (dados em `exemplos/dados/vendas.csv`)  ·  **Você vai aprender:** ler linhas, dividir texto, somar por grupo.

Um CSV é uma tabela em texto, com os campos separados por vírgula:

```
data,produto,quantidade,preco
2026-10-01,Caderno,10,12.5
...
```

```advak
seja linhas = Arquivo.ler_linhas("exemplos/dados/vendas.csv")    // 1
seja cabecalho = linhas[0]                                        // 2
imprimir(`Colunas: ${cabecalho}`)

seja total_por_produto = {}                                       // 3
seja total_geral = 0

para (i em 1..linhas.tamanho) {                                   // 4
    seja linha = Texto.aparar(linhas[i])                          // 5
    se (linha != "") {
        seja campos = Texto.dividir(linha, ",")                   // 6
        seja produto = campos[1]
        seja quantidade = numero(campos[2])
        seja preco = numero(campos[3])
        seja subtotal = quantidade * preco

        total_por_produto[produto] = (total_por_produto[produto] ?? 0) + subtotal   // 7
        total_geral += subtotal
    }
}

imprimir("")
imprimir("=== Resumo de vendas ===")
para (produto em total_por_produto.chaves) {                      // 8
    imprimir(`${produto}: ${moeda(total_por_produto[produto])}`)
}
imprimir(`TOTAL GERAL: ${moeda(total_geral)}`)
```

**Explicação**

1. `Arquivo.ler_linhas` devolve uma lista com uma posição por linha do arquivo.
2. A primeira linha (posição `0`) é o cabeçalho; as posições começam em zero.
3. `{}` é um mapa vazio, onde guardaremos "produto → total".
4. `1..linhas.tamanho` vai de 1 até a última linha, **sem** incluir o fim: assim pulamos o cabeçalho.
5. `Texto.aparar` tira espaços e quebras de linha das pontas.
6. `Texto.dividir(linha, ",")` corta a linha em pedaços: `campos[1]` é o produto, `[2]` a quantidade, `[3]` o preço.
7. `??` usa o valor da direita quando o da esquerda é vazio: na primeira vez que o produto aparece, o total anterior é `0`.
8. `.chaves` lista os nomes guardados no mapa.

**Saída real:**

```
Colunas: data,produto,quantidade,preco

=== Resumo de vendas ===
Caderno: R$ 187,50
Caneta: R$ 140,00
Mochila: R$ 179,80
TOTAL GERAL: R$ 507,30
```

**Exercício:** mostre também **qual produto vendeu mais unidades** (some `quantidade`, não o dinheiro).

---

## Capítulo 7 — Agenda de contatos com busca

**Arquivo:** `exemplos/07_agenda.dk`  ·  **Você vai aprender:** lista de mapas, `filtrar` com lambda, `quebrar`.

```advak
seja contatos = [
    {nome: "Ana Souza",    telefone: "(89) 99999-1111", cidade: "Picos"},
    {nome: "Bruno Lima",   telefone: "(89) 98888-2222", cidade: "Teresina"},
    {nome: "Carla Souza",  telefone: "(86) 97777-3333", cidade: "Teresina"},
    {nome: "Diego Alves",  telefone: "(89) 96666-4444", cidade: "Picos"}
]

função buscar(lista, termo) {
    seja t = Texto.minusculo(termo)                                              // 1
    retornar lista.filtrar((c) => Texto.minusculo(c.nome).contem(t) ou Texto.minusculo(c.cidade).contem(t))   // 2
}

função mostrar(lista) {
    se (lista.tamanho == 0) {
        imprimir("  Nenhum contato encontrado.")
    }
    para (c em lista) {
        imprimir(`  ${c.nome} - ${c.telefone} (${c.cidade})`)
    }
}

imprimir("=== Agenda ===")
enquanto (verdadeiro) {                                                          // 3
    seja termo = entrada("Buscar por nome ou cidade (ou 'sair'): ")
    se (termo == "sair") {
        quebrar                                                                  // 4
    }
    mostrar(buscar(contatos, termo))
}
imprimir("Até logo!")
```

**Explicação**

1. Passamos tudo para minúsculas para que "SOUZA" e "souza" sejam a mesma coisa.
2. `filtrar` fica só com os itens para os quais a função devolve verdadeiro. `(c) => ...` é uma **lambda**, uma função pequena sem nome. `.contem(t)` confere se o texto contém o termo.
3. `enquanto (verdadeiro)` repete para sempre... até alguém mandar parar.
4. `quebrar` sai do laço imediatamente.

**Saída real** (digitando `souza`, `picos`, `xyz`, `sair`):

```
=== Agenda ===
Buscar por nome ou cidade (ou 'sair'): souza
  Ana Souza - (89) 99999-1111 (Picos)
  Carla Souza - (86) 97777-3333 (Teresina)
Buscar por nome ou cidade (ou 'sair'): picos
  Ana Souza - (89) 99999-1111 (Picos)
  Diego Alves - (89) 96666-4444 (Picos)
Buscar por nome ou cidade (ou 'sair'): xyz
  Nenhum contato encontrado.
Buscar por nome ou cidade (ou 'sair'): sair
Até logo!
```

**Exercício:** faça a busca também pelo **telefone**, para achar quem tem "(86)".

---

## Capítulo 8 — Testes unitários

**Arquivo:** `exemplos/08_regras_testes.dk`  ·  **Você vai aprender:** `testar`, `afirmar_igual`, `afirmar_erro`.

Um teste é um pequeno programa que confere se outro está certo. Se você mudar a regra e quebrar algo, o teste avisa.

```advak
função desconto(valor, cliente_vip) {
    se (valor <= 0) {
        lançar "valor inválido"                      // 1
    }
    se (cliente_vip) {
        retornar arred(valor * 0.9, 2)               // 10% de desconto
    }
    se (valor >= 100) {
        retornar arred(valor * 0.95, 2)              // 5% de desconto
    }
    retornar valor
}

testar("cliente VIP tem 10% de desconto", () => {    // 2
    afirmar_igual(desconto(50, verdadeiro), 45)      // 3
})

testar("valor zero ou negativo é recusado", () => {
    afirmar_erro(() => desconto(0, falso))           // 4
})
```

(O arquivo tem mais três testes, incluindo `classificar_idade`.)

**Explicação**

1. `lançar` cria um erro de propósito quando a regra é violada.
2. `testar("descrição", função)` define um teste com um nome em português claro.
3. `afirmar_igual(real, esperado)` falha se os dois valores forem diferentes.
4. `afirmar_erro(função)` passa **se a função der erro**, ideal para conferir que valores inválidos são recusados.

**Saída real:**

```
  ✅ cliente comum abaixo de 100 não tem desconto
  ✅ compra a partir de 100 tem 5% de desconto
  ✅ cliente VIP tem 10% de desconto
  ✅ valor zero ou negativo é recusado
  ✅ faixas de idade
```

**Exercício:** mude a regra para 8% de desconto acima de R$ 100 e rode: o teste "5%" vai falhar. Depois ajuste o teste para a regra nova.

---

## Capítulo 9 — Trocando só a string de conexão

**Arquivo:** `exemplos/09_trocar_banco.dk`  ·  **Você vai aprender:** que o mesmo programa roda em bancos diferentes.

Esta é a grande vantagem do conector único da Advak: o código é o mesmo; só o **endereço** muda.

```advak
env.carregar(".env")                                  // 1
seja url_banco = env.texto("ADVAK_CADASTRO_URL", "sqlite:///exemplos/dados/trocar.db")   // 2
seja db = banco.conectar(url_banco)                   // 3

db.tabela("pessoas", {id: "autonum", nome: "texto obrigatorio", cidade: "texto"})
db.deletar("pessoas").executar()                      // começa do zero (para repetir o exemplo)

db.inserir("pessoas", {nome: "Ana", cidade: "Picos"})
db.inserir("pessoas", {nome: "Bruno", cidade: "Teresina"})
db.inserir("pessoas", {nome: "Carla", cidade: "Picos"})
...
```

**Explicação**

1. `env.carregar` lê o arquivo `.env`, onde ficam as senhas (**nunca escreva senha no código**).
2. `env.texto(nome, padrão)` lê a variável; se ela não existir, usa o SQLite.
3. `banco.conectar` descobre o banco pelo começo do endereço.

**Para trocar de banco, escreva no `.env` (sem mexer no `.dk`):**

| Banco | Linha no `.env` | Driver |
|---|---|---|
| SQLite (padrão) | *(nada)* | já vem com o Python |
| MySQL | `ADVAK_CADASTRO_URL=mysql://usuario:senha@localhost:3306/loja` | `pip install pymysql` |
| SQL Server | `ADVAK_CADASTRO_URL=mssql://usuario:senha@localhost:1433/loja` | `pip install pymssql` |

Detalhes de cada banco em [BANCOS_DE_DADOS.md](BANCOS_DE_DADOS.md).

**Saída real (SQLite):**

```
Todas as pessoas:
  1 - Ana (Picos)
  2 - Bruno (Teresina)
  3 - Carla (Picos)
Só de Picos:
  Ana
  Carla
Total: 3
```

> **Atenção:** só o SQLite foi executado de verdade. **MySQL e SQL Server não foram testados** com este exemplo.

**Exercício:** crie uma segunda tabela, `pedidos`, e rode no SQLite. Depois explique, com suas palavras, o que muda no código se um dia a loja migrar para o MySQL (resposta: nada além do `.env`).

---

## Capítulo 10 — Relatório de vendas em SQL Server ou Firebird

**Arquivo:** `exemplos/10_relatorio_vendas_sql.dk`  ·  **Você vai aprender:** `db.sql` com `SUM` e `GROUP BY`.

Muitos sistemas de PDV (caixa de loja) guardam as vendas em **SQL Server** ou **Firebird**. Aqui o programa só **lê** esse banco para montar um relatório; ele não altera nada.

```advak
env.carregar(".env")
seja url_banco = env.texto("ADVAK_RELATORIO_URL", "sqlite:///exemplos/dados/pdv.db")
seja db = banco.conectar(url_banco)

se (url_banco.começa_com("sqlite")) {                 // 1
    // cria vendas de mentira só no banco de teste
}

seja linhas = db.sql("SELECT produto, SUM(quantidade) AS qtd, SUM(quantidade * preco) AS total FROM vendas GROUP BY produto ORDER BY total DESC")   // 2

seja geral = 0
para (l em linhas) {
    imprimir(`${l.produto}: ${l.qtd} unidades, ${moeda(l.total)}`)
    geral += l.total
}
imprimir(`TOTAL GERAL: ${moeda(geral)}`)
db.fechar()
```

**Explicação**

1. Só preenchemos dados de mentira se o banco for o SQLite de teste. Num PDV real a tabela `vendas` já existe (**confira os nomes das tabelas e colunas do seu sistema**: eles variam).
2. `db.sql(...)` executa um SQL escrito por você e devolve uma lista de mapas. `SUM` soma, `GROUP BY` agrupa por produto, `ORDER BY total DESC` coloca o maior primeiro.

**Para ligar ao banco real (`.env`):**

```
ADVAK_RELATORIO_URL=mssql://usuario:senha@servidor:1433/pdv
ADVAK_RELATORIO_URL=firebird://usuario:senha@servidor:3050/C:/pdv/dados.fdb
```

Drivers: `pip install pymssql` (SQL Server) e `pip install firebird-driver` (Firebird). Veja os detalhes e a instalação em [BANCOS_DE_DADOS.md](BANCOS_DE_DADOS.md).

**Saída real (SQLite de teste):**

```
=== Vendas por produto ===
Caderno: 15 unidades, R$ 187,50
Mochila: 2 unidades, R$ 179,80
Caneta: 50 unidades, R$ 100,00
TOTAL GERAL: R$ 467,30
```

> **Atenção:** **SQL Server e Firebird não foram testados** com este exemplo. O SQL usado é comum a todos, mas cada PDV tem suas próprias tabelas. Use um usuário do banco **somente leitura**.

**Exercício:** mude a consulta para mostrar o total vendido **por dia** (`GROUP BY dia`).

---

## Capítulo 11 — Cache de consultas com Redis

**Arquivo:** `exemplos/11_cache_redis.dk`  ·  **Você vai aprender:** guardar resultados para não repetir uma consulta lenta.

O **Redis** guarda dados na memória, por isso é muito rápido. Um **cache** é uma "anotação": se a resposta já foi calculada, usamos a anotação em vez de fazer tudo de novo.

```advak
seja cache = banco.conectar("redis")                  // 1
seja db = banco.conectar("sqlite:///exemplos/dados/cache_demo.db")
...
função listar_produtos() {
    seja guardado = cache.obter_json("produtos")      // 2
    se (guardado != nulo) {
        imprimir("  (veio do cache)")
        retornar guardado
    }
    imprimir("  (veio do banco)")
    seja lista = db.buscar("produtos").ordenar("nome").executar()
    cache.definir("produtos", lista, 30)              // 3
    retornar lista
}
```

**Explicação**

1. Lê `ADVAK_REDIS_URL` do `.env` (ex.: `redis://localhost:6379/0`). Driver: `pip install redis`.
2. `obter_json` procura a anotação; devolve `nulo` se não achar ou se ela já expirou.
3. `definir(chave, valor, segundos)` guarda por 30 segundos. Depois disso o Redis apaga sozinho, e a próxima consulta vai ao banco de novo.

**Saída** (rodando contra um Redis **simulado**):

```
Consulta 1:
  (veio do banco)
  2 produtos
Consulta 2:
  (veio do cache)
  2 produtos
Consulta 3:
  (veio do cache)
  2 produtos
Visitas: 2
```

> **Atenção:** esta saída veio de um Redis de mentira (`python testes/rodar_simulado.py exemplos/11_cache_redis.dk`). **Não foi testado com um servidor Redis real.** Para o Windows, a instalação mais simples é por WSL ou Docker (veja [BANCOS_DE_DADOS.md](BANCOS_DE_DADOS.md#redis)).

**Exercício:** quando você cadastrar um produto novo, o cache fica velho. Faça `cache.excluir("produtos")` logo depois do `inserir`. Por que isso é necessário?

---

## Capítulo 12 — Catálogo de produtos com MongoDB

**Arquivo:** `exemplos/12_catalogo_mongodb.dk`  ·  **Você vai aprender:** banco de documentos, em que cada registro pode ter campos diferentes.

```advak
seja db = banco.conectar("mongodb")                   // 1
db.deletar("produtos").onde({}).executar()            // 2

db.inserir("produtos", {nome: "Caderno", preco: 12.5, categoria: "papelaria"})
db.inserir("produtos", {nome: "Mochila", preco: 89.9, categoria: "acessorios", cores: ["azul", "preto"]})   // 3
db.inserir("produtos", {nome: "Caneta", preco: 2, categoria: "papelaria"})

para (p em db.buscar("produtos").onde("categoria = %s", "papelaria").ordenar("nome").executar()) {   // 4
    imprimir(`  ${p.nome} - ${moeda(p.preco)}`)
}
```

**Explicação**

1. Lê `ADVAK_MONGODB_URL` do `.env` (ex.: `mongodb://localhost:27017/catalogo`). Driver: `pip install pymongo`. Instalação: <https://www.mongodb.com/try/download/community>.
2. `onde({})` é um filtro vazio, que casa com tudo: apaga a coleção para o exemplo ser repetível. **Cuidado com isso em dados de verdade!**
3. A Mochila tem o campo `cores` e os outros não. No MongoDB isso é normal. A coleção `produtos` é criada sozinha.
4. As mesmas palavras (`buscar`, `onde`, `ordenar`) dos bancos SQL funcionam aqui.

**Saída** (rodando contra um MongoDB **simulado**):

```
Papelaria:
  Caderno - R$ 12,50
  Caneta - R$ 2,00
Acima de R$ 10:
  Caderno
  Mochila
Total no catálogo: 3
```

> **Atenção:** a saída veio de um MongoDB de mentira (`python testes/rodar_simulado.py exemplos/12_catalogo_mongodb.dk`). **Não foi testado com um servidor MongoDB real.**

**Exercício:** adicione `estoque: 10` só a um produto e use `.onde("estoque > %s", 5)` para achá-lo.

---

## Capítulo 13 — PDV didático

**Arquivo:** `exemplos/13_pdv_didatico.dk`  ·  **Você vai aprender:** juntar tudo: banco com três tabelas, venda com carrinho, troco e relatório do dia.

> **AVISO IMPORTANTE:** este é um programa para **estudar**. **Ele NÃO é um PDV fiscal:** não emite nota fiscal nem cupom, não se comunica com a SEFAZ, não controla impostos nem caixa. **Não o use para vender de verdade.** Uma loja real precisa de um sistema homologado.

Um **PDV** (ponto de venda) é o "caixa" da loja. O nosso tem quatro funções: cadastrar produtos, vender, calcular o troco e mostrar o relatório do dia. Usa SQLite (nada a instalar). As tabelas são `produtos`, `vendas` (uma linha por compra) e `itens` (uma linha por produto dentro de cada compra).

```advak
seja db = banco.conectar("sqlite:///exemplos/dados/pdv_didatico.db")
db.tabela("produtos", {id: "autonum", nome: "texto obrigatorio", preco: "decimal", estoque: "inteiro padrao 0"})
db.tabela("vendas", {id: "autonum", dia: "texto", total: "decimal", pago: "decimal", troco: "decimal"})
db.tabela("itens", {id: "autonum", venda_id: "inteiro", produto_id: "inteiro", quantidade: "inteiro", subtotal: "decimal"})
```

**Trecho 1 — a venda** (a função `nova_venda`, resumida):

```advak
seja carrinho = []                                     // 1
seja total = 0
...
seja p = db.buscar_id("produtos", inteiro(codigo))     // 2
se (qtd > p.estoque) {                                 // 3
    imprimir(`  Só há ${p.estoque} em estoque.`)
} senão {
    seja subtotal = qtd * p.preco
    carrinho.adicionar({produto: p, quantidade: qtd, subtotal: subtotal})
    total += subtotal
}
...
seja pago = numero(entrada(`  Total ${moeda(total)}. Valor recebido: `))
enquanto (pago < total) {                              // 4
    imprimir("  Valor menor que o total.")
    pago = numero(entrada("  Valor recebido: "))
}
seja troco = pago - total                              // 5
seja venda = db.inserir("vendas", {dia: data_hoje(), total: total, pago: pago, troco: troco})   // 6
para (item em carrinho) {                              // 7
    db.inserir("itens", {venda_id: venda.id, produto_id: item.produto.id, quantidade: item.quantidade, subtotal: item.subtotal})
    db.atualizar("produtos", {estoque: item.produto.estoque - item.quantidade}).onde("id = %s", item.produto.id).executar()
}
```

**Explicação**

1. O carrinho é uma lista de mapas; só gravamos no banco quando o cliente paga.
2. `buscar_id` procura o produto pelo código; se não existir, avisamos.
3. Antes de aceitar, conferimos o estoque.
4. Se o cliente deu menos do que o total, pedimos de novo.
5. **Troco = valor recebido − total.**
6. `data_hoje()` devolve a data de hoje (`aaaa-mm-dd`), que guardamos em `dia` para o relatório.
7. Para cada item, gravamos na tabela `itens` e **baixamos o estoque**.

**Trecho 2 — o relatório do dia:**

```advak
seja vendas = db.buscar("vendas").onde("dia = %s", hoje).executar()
...
seja itens = db.sql("SELECT p.nome AS nome, SUM(i.quantidade) AS qtd FROM itens i JOIN produtos p ON p.id = i.produto_id JOIN vendas v ON v.id = i.venda_id WHERE v.dia = %s GROUP BY p.nome ORDER BY qtd DESC", hoje)
```

O `JOIN` junta tabelas: aqui liga cada item ao nome do produto e à venda (para filtrar pelo dia). O `GROUP BY` soma as quantidades de cada produto.

**Saída real** (cadastrando Caderno R$ 12,50 e Caneta R$ 2,00; vendendo 2 cadernos + 10 canetas e pagando R$ 50; depois 1 caderno pagando R$ 20):

```
=== PDV didático (NÃO é PDV fiscal) ===
...
Escolha: 3
  Código do produto (vazio para fechar a venda): 1
  Quantidade: 2
  + 2 x Caderno = R$ 25,00   (total: R$ 25,00)
  Código do produto (vazio para fechar a venda): 2
  Quantidade: 10
  + 10 x Caneta = R$ 20,00   (total: R$ 45,00)
  Código do produto (vazio para fechar a venda):
  Total R$ 45,00. Valor recebido: 50
  Venda 1 registrada. TROCO: R$ 5,00
...
  Quantidade: 50
  Só há 18 em estoque.
...
  Total R$ 12,50. Valor recebido: 20
  Venda 2 registrada. TROCO: R$ 7,50

Escolha: 4
  Vendas de hoje: 2
  Total vendido: R$ 57,50
  Caneta: 10 unidade(s)
  Caderno: 3 unidade(s)
```

Veja que o estoque foi baixando (Caderno: 20 → 17; Caneta: 100 → 90) e que o programa recusou 50 cadernos quando só havia 18.

**Exercícios:** (1) Faça o programa recusar quantidade zero ou negativa. (2) Acrescente a opção "5) Cancelar a última venda" que devolve os itens ao estoque. (3) Pense: o que falta para este programa ser um PDV de verdade? (Pista: nota fiscal, impostos, controle de caixa, vários usuários.)

---

## Para continuar

* Quer aprender do zero, em aulas curtas? Veja o curso [Aprenda a programar com Advak](curso/README.md).
* Todos os bancos suportados: [BANCOS_DE_DADOS.md](BANCOS_DE_DADOS.md).
* Problemas na instalação: [INSTALACAO.md](INSTALACAO.md).
