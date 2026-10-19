# Aula 24 — Projeto final: sistema completo

> **Ao final desta aula você vai saber:** juntar tudo o que aprendeu em um sistema de verdade — uma **agenda de contatos** com módulo, validação, banco de dados SQLite, testes e uma janela —, e organizar um programa em camadas.

## O que vamos construir

Uma agenda onde se cadastram contatos (nome, telefone, cidade), que aparecem numa tabela, podem ser excluídos e **continuam salvos** no banco. Quase tudo que você viu no curso aparece aqui:

| O que | Aulas |
|---|---|
| funções, listas e mapas | 10, 11, 12 |
| textos | 14 |
| erros: `lançar`, `tentar`, `capturar` | 15 |
| módulos: `exportar`, `importar` | 19 |
| testes | 20 |
| banco de dados | 21 |
| janela | 22 |
| servidor web | 23 |

## O segredo dos programas grandes: camadas

Se você escrever tudo num arquivo só, a regra de validação do telefone fica misturada com o desenho da janela, e fica impossível mudar uma coisa sem quebrar a outra. Por isso separamos em **camadas**, cada uma com uma responsabilidade:

1. **Dados** (`aula24_repositorio.dk`): fala com o banco e aplica as regras (nome obrigatório, telefone válido). **Não sabe** que existe janela.
2. **Testes** (`aula24_testes.dk`): conferem a camada de dados.
3. **Tela** (`aula24_app.dk`): janela com campos e botões. **Não sabe** nada de SQL: só chama funções da camada de dados.

Vantagem: a mesma camada de dados serve para a janela, para um servidor web e para os testes, sem copiar código.

## Camada 1: o repositório

Leia com calma. Tudo isto você já viu:

<!--codigo:aula24_repositorio.dk-->
```advak
// Camada de dados: tudo o que fala com o banco fica aqui.

exportar função abrir(arquivo) {
    seja db = banco.conectar(`sqlite:///${arquivo}`)
    db.tabela("contatos", {id: "autonum", nome: "texto obrigatorio", telefone: "texto obrigatorio", cidade: "texto"})
    retornar db
}

exportar função validar(nome, telefone) {
    se (nome.aparar() == "") {
        lançar "o nome é obrigatório"
    }
    se (!e_numero(telefone) ou telefone.tamanho < 8) {
        lançar "telefone deve ter só números e pelo menos 8 dígitos"
    }
}

exportar função cadastrar(db, nome, telefone, cidade) {
    validar(nome, telefone)
    retornar db.inserir("contatos", {nome: nome.aparar(), telefone: telefone, cidade: cidade})
}

exportar função listar(db) {
    retornar db.buscar("contatos").ordenar("nome").executar()
}

exportar função excluir(db, id) {
    retornar db.deletar("contatos").onde("id = %s", id).executar()
}

exportar função da_cidade(db, cidade) {
    retornar db.buscar("contatos").onde("cidade = %s", cidade).ordenar("nome").executar()
}
```

Repare nas decisões:

- `abrir` cria a tabela se ela não existir e **devolve** o banco aberto; quem chamar decide quando fechar.
- `validar` usa `lançar` (aula 15) para recusar dados ruins. `nome.aparar()` tira espaços do começo e do fim; `e_numero` confere que o telefone só tem números.
- `cadastrar` **sempre valida antes de gravar**. Assim, não importa quem chame (janela, servidor, teste): a regra é aplicada.
- As funções recebem o `db` como parâmetro, o que facilita testar com um banco temporário.

## Camada 2: os testes

Antes de desenhar a janela, conferimos se a camada de dados faz o que prometeu. Cada teste usa um banco de arquivo próprio, apagado no fim.

<!--codigo:aula24_testes.dk-->
```advak
importar { abrir, cadastrar, listar, excluir, da_cidade, validar } de "aula24_repositorio.dk"

seja arquivo = "aula24_testes.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)

testar("cadastrar grava e devolve o contato com id", () => {
    seja c = cadastrar(db, "Ana", "81999990000", "Recife")
    afirmar_igual(c.nome, "Ana")
    afirmar_igual(c.id, 1)
})

testar("nome com espaços sobrando é limpo", () => {
    seja c = cadastrar(db, "   Bruno   ", "84988887777", "Natal")
    afirmar_igual(c.nome, "Bruno")
})

testar("listar traz em ordem de nome", () => {
    cadastrar(db, "Carla", "81977776666", "Recife")
    seja nomes = listar(db).mapear((c) => c.nome)
    afirmar_igual(nomes, ["Ana", "Bruno", "Carla"])
})

testar("filtrar por cidade", () => {
    afirmar_igual(da_cidade(db, "Recife").tamanho, 2)
    afirmar_igual(da_cidade(db, "Natal").tamanho, 1)
    afirmar_igual(da_cidade(db, "Paris").tamanho, 0)
})

testar("nome vazio é recusado", () => {
    afirmar_erro(() => validar("", "81999990000"))
    afirmar_erro(() => validar("   ", "81999990000"))
})

testar("telefone inválido é recusado", () => {
    afirmar_erro(() => validar("Dani", "abc"))
    afirmar_erro(() => validar("Dani", "1234"))
})

testar("contato inválido não chega ao banco", () => {
    seja antes = listar(db).tamanho
    afirmar_erro(() => cadastrar(db, "", "81999990000", "Recife"))
    afirmar_igual(listar(db).tamanho, antes)
})

testar("excluir apaga só o contato pedido", () => {
    afirmar_igual(excluir(db, 2), 1)
    afirmar_igual(listar(db).tamanho, 2)
    afirmar_igual(excluir(db, 999), 0)
})

resumo_testes()
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula24_testes.dk-->
```text
  ✅ cadastrar grava e devolve o contato com id
  ✅ nome com espaços sobrando é limpo
  ✅ listar traz em ordem de nome
  ✅ filtrar por cidade
  ✅ nome vazio é recusado
  ✅ telefone inválido é recusado
  ✅ contato inválido não chega ao banco
  ✅ excluir apaga só o contato pedido

  ────────────────────────────────────────────
  Resultado: 8/8 testes passaram  🎉
```

Se algum desses testes quebrar no futuro, você descobre **na hora**, antes de o defeito chegar ao usuário.

## Camada 3: a tela

A janela só **chama** o repositório e mostra o resultado. Duas regras de ouro aqui:

- toda chamada que pode dar erro vai dentro de `tentar`/`capturar`, e a mensagem aparece num label de status (lembre da aula 22: o erro de um botão aparece só no terminal, e a janela segue sem reação!);
- depois de cada mudança, `atualizar_tela()` redesenha a tabela a partir do banco. A verdade está sempre no banco, nunca em uma lista paralela.

Como na aula 22, as últimas linhas **simulam** a pessoa usando a janela (digitar, clicar, escolher uma linha) para o exemplo mostrar o resultado sozinho; num programa de verdade, quem faz isso é o usuário. Um clique de cada vez, com uma folga entre eles.

<!--codigo:aula24_app.dk-->
```advak
importar { abrir, cadastrar, listar, excluir } de "aula24_repositorio.dk"

seja arquivo = "aula24_app.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)

seja jan = gui.janela("Agenda de contatos", 560, 520)
jan.centralizar()
gui.label(jan, "Agenda de contatos", negrito=verdadeiro, tamanho=16)

seja campo_nome = gui.campo(jan, "Nome", largura=30)
seja campo_telefone = gui.campo(jan, "Telefone (só números)", largura=30)
seja campo_cidade = gui.campo(jan, "Cidade", largura=30)
seja status = gui.label(jan, "Pronto.")
seja tabela = gui.tabela(jan, ["ID", "Nome", "Telefone", "Cidade"], altura=8)

função atualizar_tela() {
    tabela.limpar()
    seja contatos = listar(db)
    para (c em contatos) {
        tabela.adicionar([c.id, c.nome, c.telefone, c.cidade])
    }
    status.texto(`${contatos.tamanho} contato(s) na agenda.`)
}

função ao_cadastrar() {
    tentar {
        cadastrar(db, campo_nome.valor(), campo_telefone.valor(), campo_cidade.valor())
        campo_nome.limpar()
        campo_telefone.limpar()
        campo_cidade.limpar()
        atualizar_tela()
    } capturar (e) {
        status.texto(`Não foi possível cadastrar: ${e}`)
    }
}

função ao_excluir() {
    seja escolhido = tabela.selecionado()
    se (escolhido == nulo) {
        status.texto("Selecione um contato na tabela.")
        retornar
    }
    excluir(db, inteiro(escolhido["ID"]))
    atualizar_tela()
}

seja faixa = gui.frame_horizontal(jan)
seja botao_cadastrar = gui.botao(faixa, "Cadastrar", (x) => { ao_cadastrar() }, estilo="sucesso")
seja botao_excluir = gui.botao(faixa, "Excluir selecionado", (x) => { ao_excluir() }, estilo="perigo")

atualizar_tela()

// --- Só para o exemplo: uma pessoa usando a janela, um passo a cada 1,5 segundo ---
gui.apos(1500, () => {
    campo_nome.definir("Ana Souza")
    campo_telefone.definir("81999990000")
    campo_cidade.definir("Recife")
    botao_cadastrar.invoke()
})
gui.apos(3000, () => {
    imprimir("1) Cadastrou a Ana:", status.cget("text"))
    campo_nome.definir("Bruno")
    campo_telefone.definir("123")
    botao_cadastrar.invoke()
})
gui.apos(4500, () => {
    imprimir("2) Telefone curto demais:", status.cget("text"))
    campo_telefone.definir("84988887777")
    campo_cidade.definir("Natal")
    botao_cadastrar.invoke()
})
gui.apos(6000, () => {
    imprimir("3) Cadastrou o Bruno:", status.cget("text"))
    botao_excluir.invoke()
})
gui.apos(7500, () => {
    imprimir("4) Excluir sem escolher:", status.cget("text"))
    tabela.selection_set(lista(tabela.get_children())[0])
    botao_excluir.invoke()
})
gui.apos(9000, () => {
    imprimir("5) Excluiu a primeira linha:", status.cget("text"))
    imprimir("Ficou no banco:", listar(db))
    gui.parar()
})

gui.iniciar()
db.fechar()
Arquivo.apagar(arquivo)
imprimir("Programa encerrado.")
```

<!--saida:aula24_app.dk-->
```text
1) Cadastrou a Ana: 1 contato(s) na agenda.
2) Telefone curto demais: Não foi possível cadastrar: telefone deve ter só números e pelo menos 8 dígitos
3) Cadastrou o Bruno: 2 contato(s) na agenda.
4) Excluir sem escolher: Selecione um contato na tabela.
5) Excluiu a primeira linha: 1 contato(s) na agenda.
Ficou no banco: [{id: 2, nome: Bruno, telefone: 84988887777, cidade: Natal}]
Programa encerrado.
```

Acompanhe a saída: o passo 2 mostra a **validação** protegendo o banco (nada foi gravado); o passo 4 mostra a tela avisando que falta escolher uma linha; e no fim o banco contém só o Bruno.

## A mesma camada de dados, agora numa API

Como a regra mora no repositório, um servidor web (aula 23) reaproveita tudo, sem copiar nenhuma validação:

<!--codigo:aula24_api.dk-->
```advak
importar { abrir, cadastrar, listar, excluir } de "aula24_repositorio.dk"

seja arquivo = "aula24_api.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)

servidor.obter("/contatos", (req) => {
    retornar resposta_json(listar(db))
})

servidor.publicar("/contatos", (req) => {
    se (req.dados == nulo) {
        retornar resposta_json({erro: "envie os dados em JSON"}, 400)
    }
    seja resposta = nulo                                           // guardamos a resposta e devolvemos fora do tentar
    tentar {
        seja novo = cadastrar(db, req.dados.nome ?? "", texto(req.dados.telefone ?? ""), req.dados.cidade ?? "")
        resposta = resposta_json(novo, 201)
    } capturar (e) {
        resposta = resposta_json({erro: e}, 400)
    }
    retornar resposta
})

servidor.iniciar(8841, falso)
```

<!--http:aula24_api
GET /contatos
POST /contatos {"nome": "Ana", "telefone": "81999990000", "cidade": "Recife"}
POST /contatos {"nome": "", "telefone": "81999990000"}
POST /contatos {"nome": "Bia", "telefone": "12"}
GET /contatos
-->
<!--saida:aula24_api.dk-->
```text
GET /contatos
  -> 200 []
POST /contatos {"nome": "Ana", "telefone": "81999990000", "cidade": "Recife"}
  -> 201 {"nome": "Ana", "telefone": "81999990000", "cidade": "Recife", "id": 1}
POST /contatos {"nome": "", "telefone": "81999990000"}
  -> 400 {"erro": "o nome é obrigatório"}
POST /contatos {"nome": "Bia", "telefone": "12"}
  -> 400 {"erro": "telefone deve ter só números e pelo menos 8 dígitos"}
GET /contatos
  -> 200 [{"id": 1, "nome": "Ana", "telefone": "81999990000", "cidade": "Recife"}]
```

Dois detalhes: `a ?? b` quer dizer "use `a`, ou `b` se `a` for `nulo`" (assim um campo ausente no JSON vira texto vazio e é recusado pela validação, em vez de dar erro 500); e o `retornar` fica **fora** do `tentar`, como combinamos na aula 15.

Os mesmos testes da camada de dados continuam valendo para a API. Esse é o ganho de separar em camadas.

## Roteiro para criar o seu próprio sistema

1. **Escreva o que o sistema deve fazer**, em frases simples (cadastrar, listar, excluir...).
2. **Desenhe os dados**: quais tabelas e campos?
3. **Faça a camada de dados** com as regras (e `lançar` quando algo for inválido).
4. **Escreva testes** para ela.
5. **Só então faça a interface** (janela ou servidor).
6. Rode, use, tente quebrar o programa, corrija. Repita.

## Erros comuns

**1. Esquecer o `tentar` ao chamar uma função que lança erro.** A validação funciona, mas, sem o `tentar`, o erro derruba o programa:

<!--codigo:aula24_erro1.dk-->
```advak
importar { abrir, cadastrar } de "aula24_repositorio.dk"

seja db = abrir("aula24_erro1.db")
cadastrar(db, "", "81999990000", "Recife")
db.fechar()
```

Mensagem real:

<!--erro:aula24_erro1.dk-->
```text
Problema:    o nome é obrigatório
```

**Como corrigir:** envolva a chamada em `tentar { ... } capturar (e) { ... }` e mostre a mensagem ao usuário.

**2. Importar uma função que o módulo não exportou.** O repositório não exporta nenhuma função chamada `apagar_tudo`:

<!--codigo:aula24_erro2.dk-->
```advak
importar { apagar_tudo } de "aula24_repositorio.dk"
apagar_tudo()
```

Mensagem real:

<!--erro:aula24_erro2.dk-->
```text
Localização: linha 2
Problema:    'apagar_tudo' não exportado por 'aula24_repositorio.dk'
```

**Como corrigir:** confira o nome certo na lista de `exportar` do módulo.

**3. Regra de negócio só na tela.** Se a validação do telefone estivesse apenas no botão da janela, a API e qualquer outro programa poderiam gravar telefones inválidos. Por isso `cadastrar` valida **dentro do repositório**: veja no teste "contato inválido não chega ao banco".

## Exercícios

1. Cadastre três contatos no repositório (sem janela) e mostre-os, um por linha, no formato `Nome - Telefone (Cidade)`.
2. Mostre quantos contatos existem em cada cidade, usando `listar` e um mapa de contagem.
3. Mostre só os contatos de uma cidade, usando `da_cidade`.
4. Escreva, no seu programa, uma função `buscar_nome(db, trecho)` que devolva os contatos cujo nome contenha o trecho (use `.onde("nome LIKE %s", ...)`).
5. Escreva um teste com `afirmar_erro` que garanta que `cadastrar` recusa um telefone com 7 dígitos.
6. Atualize o telefone de um contato com `db.atualizar(...)` e mostre o contato com o telefone novo.
7. Faça uma API com a rota `GET /cidade/:nome`, que devolva os contatos da cidade usando `da_cidade`.
8. **Desafio:** na tela, acrescente um botão `Só Recife` que mostra na tabela apenas os contatos de Recife, e um botão `Todos` que volta a mostrar todos. Simule os cliques e mostre quantas linhas a tabela tem em cada caso.

## Respostas

**Exercício 1**

<!--codigo:aula24_resposta1.dk-->
```advak
importar { abrir, cadastrar, listar } de "aula24_repositorio.dk"

seja arquivo = "aula24_resposta1.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)
cadastrar(db, "Ana", "81999990000", "Recife")
cadastrar(db, "Bruno", "84988887777", "Natal")
cadastrar(db, "Carla", "81977776666", "Recife")

para (c em listar(db)) {
    imprimir(`${c.nome} - ${c.telefone} (${c.cidade})`)
}
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula24_resposta1.dk-->
```text
Ana - 81999990000 (Recife)
Bruno - 84988887777 (Natal)
Carla - 81977776666 (Recife)
```

**Exercício 2**

<!--codigo:aula24_resposta2.dk-->
```advak
importar { abrir, cadastrar, listar } de "aula24_repositorio.dk"

seja arquivo = "aula24_resposta2.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)
cadastrar(db, "Ana", "81999990000", "Recife")
cadastrar(db, "Bruno", "84988887777", "Natal")
cadastrar(db, "Carla", "81977776666", "Recife")

seja contagem = {}
para (c em listar(db)) {
    se (contagem[c.cidade] == nulo) {
        contagem[c.cidade] = 0
    }
    contagem[c.cidade] = contagem[c.cidade] + 1
}
imprimir(contagem)
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula24_resposta2.dk-->
```text
{Recife: 2, Natal: 1}
```

**Exercício 3**

<!--codigo:aula24_resposta3.dk-->
```advak
importar { abrir, cadastrar, da_cidade } de "aula24_repositorio.dk"

seja arquivo = "aula24_resposta3.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)
cadastrar(db, "Ana", "81999990000", "Recife")
cadastrar(db, "Bruno", "84988887777", "Natal")
cadastrar(db, "Carla", "81977776666", "Recife")

para (c em da_cidade(db, "Recife")) {
    imprimir(c.nome)
}
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula24_resposta3.dk-->
```text
Ana
Carla
```

**Exercício 4**

<!--codigo:aula24_resposta4.dk-->
```advak
importar { abrir, cadastrar } de "aula24_repositorio.dk"

seja arquivo = "aula24_resposta4.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)
cadastrar(db, "Ana Souza", "81999990000", "Recife")
cadastrar(db, "Bruno Lima", "84988887777", "Natal")
cadastrar(db, "Mariana Souza", "81977776666", "Recife")

função buscar_nome(banco_aberto, trecho) {
    retornar banco_aberto.buscar("contatos").onde("nome LIKE %s", "%" + trecho + "%").ordenar("nome").executar()
}

para (c em buscar_nome(db, "Souza")) {
    imprimir(c.nome)
}
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula24_resposta4.dk-->
```text
Ana Souza
Mariana Souza
```

**Exercício 5**

<!--codigo:aula24_resposta5.dk-->
```advak
importar { abrir, cadastrar, listar } de "aula24_repositorio.dk"

seja arquivo = "aula24_resposta5.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)

testar("telefone com 7 dígitos é recusado", () => {
    afirmar_erro(() => cadastrar(db, "Ana", "1234567", "Recife"))
    afirmar_igual(listar(db).tamanho, 0)
})

testar("telefone com 8 dígitos é aceito", () => {
    cadastrar(db, "Ana", "12345678", "Recife")
    afirmar_igual(listar(db).tamanho, 1)
})

resumo_testes()
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula24_resposta5.dk-->
```text
  ✅ telefone com 7 dígitos é recusado
  ✅ telefone com 8 dígitos é aceito

  ────────────────────────────────────────────
  Resultado: 2/2 testes passaram  🎉
```

**Exercício 6**

<!--codigo:aula24_resposta6.dk-->
```advak
importar { abrir, cadastrar } de "aula24_repositorio.dk"

seja arquivo = "aula24_resposta6.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)
seja ana = cadastrar(db, "Ana", "81999990000", "Recife")

db.atualizar("contatos", {telefone: "81888880000"}).onde("id = %s", ana.id).executar()
imprimir(db.buscar("contatos").onde("id = %s", ana.id).primeiro())
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula24_resposta6.dk-->
```text
{id: 1, nome: Ana, telefone: 81888880000, cidade: Recife}
```

**Exercício 7**

<!--codigo:aula24_resposta7.dk-->
```advak
importar { abrir, cadastrar, da_cidade } de "aula24_repositorio.dk"

seja arquivo = "aula24_resposta7.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)
cadastrar(db, "Ana", "81999990000", "Recife")
cadastrar(db, "Bruno", "84988887777", "Natal")

servidor.obter("/cidade/:nome", (req) => {
    retornar resposta_json(da_cidade(db, req.parametros.nome))
})

servidor.iniciar(8842, falso)
```

<!--http:aula24_resposta7
GET /cidade/Recife
GET /cidade/Natal
GET /cidade/Paris
-->
<!--saida:aula24_resposta7.dk-->
```text
GET /cidade/Recife
  -> 200 [{"id": 1, "nome": "Ana", "telefone": "81999990000", "cidade": "Recife"}]
GET /cidade/Natal
  -> 200 [{"id": 2, "nome": "Bruno", "telefone": "84988887777", "cidade": "Natal"}]
GET /cidade/Paris
  -> 200 []
```

**Exercício 8**

<!--codigo:aula24_resposta8.dk-->
```advak
importar { abrir, cadastrar, listar, da_cidade } de "aula24_repositorio.dk"

seja arquivo = "aula24_resposta8.db"
se (Arquivo.existe(arquivo)) {
    Arquivo.apagar(arquivo)
}
seja db = abrir(arquivo)
cadastrar(db, "Ana", "81999990000", "Recife")
cadastrar(db, "Bruno", "84988887777", "Natal")
cadastrar(db, "Carla", "81977776666", "Recife")

seja jan = gui.janela("Agenda", 520, 400)
seja tabela = gui.tabela(jan, ["ID", "Nome", "Telefone", "Cidade"], altura=8)

função mostrar(contatos) {
    tabela.limpar()
    para (c em contatos) {
        tabela.adicionar([c.id, c.nome, c.telefone, c.cidade])
    }
}

seja faixa = gui.frame_horizontal(jan)
seja botao_recife = gui.botao(faixa, "Só Recife", (x) => { mostrar(da_cidade(db, "Recife")) })
seja botao_todos = gui.botao(faixa, "Todos", (x) => { mostrar(listar(db)) }, estilo="secundario")

mostrar(listar(db))

gui.apos(1500, () => {
    imprimir("Linhas no começo:", lista(tabela.get_children()).tamanho)
    botao_recife.invoke()
})
gui.apos(3000, () => {
    imprimir("Depois de 'Só Recife':", lista(tabela.get_children()).tamanho)
    botao_todos.invoke()
})
gui.apos(4500, () => {
    imprimir("Depois de 'Todos':", lista(tabela.get_children()).tamanho)
    gui.parar()
})

gui.iniciar()
db.fechar()
Arquivo.apagar(arquivo)
```

<!--saida:aula24_resposta8.dk-->
```text
Linhas no começo: 3
Depois de 'Só Recife': 2
Depois de 'Todos': 3
```

---

## Você chegou ao fim

Parabéns! Em 24 aulas você foi de "o que é um programa" até um sistema com camadas, banco de dados, testes, janela e API. Continue praticando:

- refaça os exercícios sem olhar as respostas;
- invente um sistema seu (uma biblioteca, uma lanchonete, um controle de notas) e siga o roteiro desta aula;
- consulte o [Guia prático](../GUIA_PRATICO.md), com 13 sistemas completos, e o [guia de bancos de dados](../BANCOS_DE_DADOS.md) para usar outros bancos.

**Anterior:** [Aula 23](aula23_servidor_web.md)
