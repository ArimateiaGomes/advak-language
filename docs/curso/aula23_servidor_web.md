# Aula 23 — Servidor web: primeira API

> **Ao final desta aula você vai saber:** criar um servidor web com a Advak, responder a pedidos com páginas e com dados em JSON, receber informações pelo endereço e pelo corpo do pedido, e usar os códigos de status (200, 201, 400, 404).

## Como a web funciona (em 1 minuto)

Quando você digita um endereço no navegador, acontece uma conversa:

1. seu navegador (o **cliente**) faz um **pedido** a um computador (o **servidor**): "me dê a página `/contato`";
2. o servidor devolve uma **resposta**: o conteúdo e um número que diz como foi (o **código de status**).

Pense num restaurante: você (cliente) faz o pedido ao garçom (o endereço e o método), a cozinha (o servidor) prepara, e o garçom traz o prato com um aviso ("pronto", "acabou", "não temos esse prato").

Cada pedido tem:

- um **método**: `GET` (buscar algo), `POST` (enviar algo novo), `PUT` (mudar), `DELETE` (apagar);
- um **caminho**, como `/ola` ou `/tarefas/3`.

Cada resposta tem um **status**. Os mais comuns:

| Status | Significado |
|---|---|
| 200 | deu certo |
| 201 | criado com sucesso |
| 400 | pedido errado (faltou informação) |
| 404 | não encontrado |
| 500 | erro dentro do servidor |

Uma **API** é um servidor feito para ser usado por *outros programas* (um site, um aplicativo de celular), geralmente respondendo com dados em **JSON** (aula 16).

## O primeiro servidor

Você declara **rotas**: "quando chegar um `GET` em tal caminho, execute esta função". A função recebe o pedido (`req`) e devolve a resposta.

<!--codigo:aula23_exemplo1.dk-->
```advak
servidor.obter("/", (req) => {
    retornar html("<h1>Olá, mundo web!</h1><p>Este é o meu primeiro servidor.</p>")
})

servidor.obter("/ola", (req) => {
    retornar resposta_json({mensagem: "Olá, mundo!"})
})

servidor.iniciar(8801, falso)             // porta 8801; o falso = não abrir o navegador sozinho
```

- `servidor.obter(caminho, função)` responde a pedidos `GET`;
- `html("...")` devolve uma página;
- `resposta_json(mapa)` devolve dados em JSON (status 200);
- `servidor.iniciar(porta, abrir_navegador)` liga o servidor. **Ele fica rodando até você apertar `Ctrl+C`.**

Para testar, rode o programa e abra `http://localhost:8801/` e `http://localhost:8801/ola` no navegador. Nesta aula, o resultado que mostramos vem de pedidos feitos automaticamente ao servidor (`GET /`, etc.), então você vê exatamente o que o navegador receberia:

<!--http:aula23_exemplo1
GET /
GET /ola
-->
<!--saida:aula23_exemplo1.dk-->
```text
GET /
  -> 200 <h1>Olá, mundo web!</h1><p>Este é o meu primeiro servidor.</p>
GET /ola
  -> 200 {"mensagem": "Olá, mundo!"}
```

> **`localhost`** quer dizer "este próprio computador". O número depois dos dois-pontos é a **porta**: cada servidor ligado usa uma diferente. Se der erro de porta ocupada, troque o número.

## Parâmetros na rota e na consulta

Dois jeitos de o cliente mandar informação pelo endereço:

- **parâmetro de rota**: um pedaço do caminho marcado com `:nome` (`/ola/:nome`). Dentro da função: `req.parametros.nome`;
- **consulta**: o que vem depois do `?`, como em `/soma?a=2&b=3`. Dentro da função: `req.consulta.a` e `req.consulta.b` (sempre **texto**, converta com `numero`).

<!--codigo:aula23_exemplo2.dk-->
```advak
servidor.obter("/ola/:nome", (req) => {
    retornar resposta_json({mensagem: `Olá, ${req.parametros.nome}!`})
})

servidor.obter("/soma", (req) => {
    seja a = numero(req.consulta.a)
    seja b = numero(req.consulta.b)
    retornar resposta_json({a: a, b: b, soma: a + b})
})

servidor.iniciar(8802, falso)
```

<!--http:aula23_exemplo2
GET /ola/Ana
GET /ola/Bruno
GET /soma?a=2&b=3
GET /soma?a=10.5&b=4
-->
<!--saida:aula23_exemplo2.dk-->
```text
GET /ola/Ana
  -> 200 {"mensagem": "Olá, Ana!"}
GET /ola/Bruno
  -> 200 {"mensagem": "Olá, Bruno!"}
GET /soma?a=2&b=3
  -> 200 {"a": 2, "b": 3, "soma": 5}
GET /soma?a=10.5&b=4
  -> 200 {"a": 10.5, "b": 4, "soma": 14.5}
```

## Status e erros

O segundo argumento de `resposta_json` é o status. Use-o para dizer ao cliente o que aconteceu. Veja uma rota que procura um aluno numa lista:

<!--codigo:aula23_exemplo3.dk-->
```advak
seja alunos = [
    {id: 1, nome: "Ana", nota: 9},
    {id: 2, nome: "Bruno", nota: 6.5}
]

servidor.obter("/alunos", (req) => {
    retornar resposta_json(alunos)
})

servidor.obter("/alunos/:id", (req) => {
    seja id = inteiro(req.parametros.id)
    seja achados = alunos.filtrar((a) => a.id == id)
    se (achados.tamanho == 0) {
        retornar resposta_json({erro: "aluno não encontrado"}, 404)
    }
    retornar resposta_json(achados[0])
})

servidor.iniciar(8803, falso)
```

<!--http:aula23_exemplo3
GET /alunos
GET /alunos/2
GET /alunos/99
-->
<!--saida:aula23_exemplo3.dk-->
```text
GET /alunos
  -> 200 [{"id": 1, "nome": "Ana", "nota": 9}, {"id": 2, "nome": "Bruno", "nota": 6.5}]
GET /alunos/2
  -> 200 {"id": 2, "nome": "Bruno", "nota": 6.5}
GET /alunos/99
  -> 404 {"erro": "aluno não encontrado"}
```

Repare no último pedido: o servidor respondeu `404` com uma mensagem explicando. Quem recebe sabe tanto pelo número quanto pelo texto.

## Recebendo dados: `POST`

Para **criar** algo, o cliente envia um `POST` com dados em JSON no corpo do pedido. Na função, eles chegam em `req.dados` (ou `nulo`, se não vieram em JSON). Use `servidor.publicar` para rotas `POST`:

<!--codigo:aula23_exemplo4.dk-->
```advak
seja tarefas = []
seja proximo_id = 1

servidor.obter("/tarefas", (req) => {
    retornar resposta_json(tarefas)
})

servidor.publicar("/tarefas", (req) => {
    se (req.dados == nulo ou !req.dados.titulo) {                   // validação: sem título não cria
        retornar resposta_json({erro: "informe o titulo"}, 400)
    }
    seja nova = {id: proximo_id, titulo: req.dados.titulo, feita: falso}
    proximo_id = proximo_id + 1
    tarefas.adicionar(nova)
    retornar resposta_json(nova, 201)                               // 201 significa criado
})

servidor.iniciar(8804, falso)
```

<!--http:aula23_exemplo4
GET /tarefas
POST /tarefas {"titulo": "Estudar Advak"}
POST /tarefas {"titulo": "Fazer exercícios"}
POST /tarefas {"descricao": "sem título"}
GET /tarefas
-->
<!--saida:aula23_exemplo4.dk-->
```text
GET /tarefas
  -> 200 []
POST /tarefas {"titulo": "Estudar Advak"}
  -> 201 {"id": 1, "titulo": "Estudar Advak", "feita": false}
POST /tarefas {"titulo": "Fazer exercícios"}
  -> 201 {"id": 2, "titulo": "Fazer exercícios", "feita": false}
POST /tarefas {"descricao": "sem título"}
  -> 400 {"erro": "informe o titulo"}
GET /tarefas
  -> 200 [{"id": 1, "titulo": "Estudar Advak", "feita": false}, {"id": 2, "titulo": "Fazer exercícios", "feita": false}]
```

Os dados ficam na lista `tarefas`, **na memória do servidor**: enquanto ele estiver ligado, a lista cresce; se você desligar, tudo some (como as variáveis da aula 3). Para guardar de verdade, use o banco de dados (aula 21), como no exemplo do guia prático.

## Atualizar e apagar: `PUT` e `DELETE`

Completando o ciclo (criar, ler, atualizar, apagar), com `servidor.atualizar` (PUT) e `servidor.deletar` (DELETE):

<!--codigo:aula23_exemplo5.dk-->
```advak
seja tarefas = [
    {id: 1, titulo: "Estudar", feita: falso},
    {id: 2, titulo: "Descansar", feita: falso}
]

servidor.obter("/tarefas", (req) => {
    retornar resposta_json(tarefas)
})

servidor.atualizar("/tarefas/:id", (req) => {
    seja id = inteiro(req.parametros.id)
    seja achadas = tarefas.filtrar((t) => t.id == id)
    se (achadas.tamanho == 0) {
        retornar resposta_json({erro: "tarefa não encontrada"}, 404)
    }
    achadas[0].feita = req.dados.feita
    retornar resposta_json(achadas[0])
})

servidor.deletar("/tarefas/:id", (req) => {
    seja id = inteiro(req.parametros.id)
    tarefas = tarefas.filtrar((t) => t.id != id)
    retornar resposta_json({ok: verdadeiro})
})

servidor.iniciar(8805, falso)
```

<!--http:aula23_exemplo5
PUT /tarefas/1 {"feita": true}
DELETE /tarefas/2
GET /tarefas
PUT /tarefas/99 {"feita": true}
-->
<!--saida:aula23_exemplo5.dk-->
```text
PUT /tarefas/1 {"feita": true}
  -> 200 {"id": 1, "titulo": "Estudar", "feita": true}
DELETE /tarefas/2
  -> 200 {"ok": true}
GET /tarefas
  -> 200 [{"id": 1, "titulo": "Estudar", "feita": true}]
PUT /tarefas/99 {"feita": true}
  -> 404 {"erro": "tarefa não encontrada"}
```

## Erros comuns

**1. Pedir um caminho que não existe, ou usar o método errado.** O servidor responde `404`:

<!--codigo:aula23_erro1.dk-->
```advak
servidor.obter("/ola", (req) => {
    retornar resposta_json({mensagem: "oi"})
})
servidor.iniciar(8811, falso)
```

<!--http:aula23_erro1
GET /oi
POST /ola {}
GET /ola
-->
<!--saida:aula23_erro1.dk-->
```text
GET /oi
  -> 404 [página HTML de erro 404: /oi]
POST /ola {}
  -> 404 [página HTML de erro 404: /ola]
GET /ola
  -> 200 {"mensagem": "oi"}
```

O primeiro pedido tem o caminho errado (`/oi`); o segundo usa `POST` numa rota que só aceita `GET`. O terceiro, certo, funciona. (A resposta 404 é uma página HTML inteira; acima mostramos só o título e a mensagem dela.)

**2. Um erro dentro da rota vira status 500.** O servidor **não cai**: ele responde 500 e segue funcionando para o próximo pedido. O motivo aparece no terminal onde o servidor roda.

<!--codigo:aula23_erro2.dk-->
```advak
servidor.obter("/quebrado", (req) => {
    seja lista = [1, 2, 3]
    retornar resposta_json({valor: lista[10]})        // posição que não existe
})
servidor.obter("/saudavel", (req) => {
    retornar resposta_json({ok: verdadeiro})
})
servidor.iniciar(8812, falso)
```

<!--http:aula23_erro2
GET /quebrado
GET /saudavel
-->
<!--saida:aula23_erro2.dk-->
```text
GET /quebrado
  -> 500 [página HTML de erro 500: Índice 10 fora do alcance (tamanho: 3)]
GET /saudavel
  -> 200 {"ok": true}
```

**Como corrigir:** trate o que pode falhar com `tentar`/`capturar` (aula 15) e devolva um status adequado (como 400 ou 404) no lugar do 500.

**3. Esquecer de validar o que o cliente mandou.** `req.dados` pode ser `nulo` (corpo que não é JSON). Sem o teste `req.dados == nulo`, acessar `req.dados.titulo` daria erro. Foi por isso que o Exemplo 4 testou antes. Repare que um pedido sem JSON recebe `400`, não `500`:

<!--codigo:aula23_erro3.dk-->
```advak
servidor.publicar("/cadastro", (req) => {
    se (req.dados == nulo) {
        retornar resposta_json({erro: "envie os dados em JSON"}, 400)
    }
    retornar resposta_json({recebido: req.dados}, 201)
})
servidor.iniciar(8813, falso)
```

<!--http:aula23_erro3
POST /cadastro isso não é json
POST /cadastro {"nome": "Ana"}
-->
<!--saida:aula23_erro3.dk-->
```text
POST /cadastro isso não é json
  -> 400 {"erro": "envie os dados em JSON"}
POST /cadastro {"nome": "Ana"}
  -> 201 {"recebido": {"nome": "Ana"}}
```

**4. Esquecer o `Ctrl+C`.** O servidor não termina sozinho: ele fica esperando pedidos para sempre. Para parar, aperte `Ctrl+C` no terminal onde ele está rodando.

## Exercícios

(Como os exemplos, cada resposta traz os pedidos de teste. No seu computador você pode abrir o endereço no navegador.)

1. Crie uma rota `GET /hora-do-curso` que responda `{"curso": "Advak", "aula": 23}`.
2. Crie `GET /dobro/:n` que devolva `{"n": ..., "dobro": ...}`.
3. Crie `GET /media?a=...&b=...` que devolva a média dos dois números.
4. Crie `GET /saudacao/:nome` que devolva uma página HTML com `<h1>Bem-vindo, <nome>!</h1>`.
5. Crie uma lista de produtos na memória e a rota `GET /produtos` que a devolva e `GET /produtos/:id` que devolva um produto, ou 404.
6. Crie `POST /produtos` que receba `nome` e `preco`, recuse com 400 se faltar algum e crie com 201.
7. Crie `DELETE /produtos/:id` que apague o produto e responda 404 se ele não existir.
8. **Desafio:** monte uma API de contador: `GET /contador` mostra o valor, `POST /contador/somar` com `{"valor": N}` soma N (recuse com 400 se `valor` não for número), e `POST /contador/zerar` volta a zero.

## Respostas

**Exercício 1**

<!--codigo:aula23_resposta1.dk-->
```advak
servidor.obter("/hora-do-curso", (req) => {
    retornar resposta_json({curso: "Advak", aula: 23})
})
servidor.iniciar(8821, falso)
```

<!--http:aula23_resposta1
GET /hora-do-curso
-->
<!--saida:aula23_resposta1.dk-->
```text
GET /hora-do-curso
  -> 200 {"curso": "Advak", "aula": 23}
```

**Exercício 2**

<!--codigo:aula23_resposta2.dk-->
```advak
servidor.obter("/dobro/:n", (req) => {
    seja n = numero(req.parametros.n)
    retornar resposta_json({n: n, dobro: n * 2})
})
servidor.iniciar(8822, falso)
```

<!--http:aula23_resposta2
GET /dobro/21
GET /dobro/2.5
-->
<!--saida:aula23_resposta2.dk-->
```text
GET /dobro/21
  -> 200 {"n": 21, "dobro": 42}
GET /dobro/2.5
  -> 200 {"n": 2.5, "dobro": 5.0}
```

**Exercício 3**

<!--codigo:aula23_resposta3.dk-->
```advak
servidor.obter("/media", (req) => {
    seja a = numero(req.consulta.a)
    seja b = numero(req.consulta.b)
    retornar resposta_json({media: (a + b) / 2})
})
servidor.iniciar(8823, falso)
```

<!--http:aula23_resposta3
GET /media?a=8&b=5
-->
<!--saida:aula23_resposta3.dk-->
```text
GET /media?a=8&b=5
  -> 200 {"media": 6.5}
```

**Exercício 4**

<!--codigo:aula23_resposta4.dk-->
```advak
servidor.obter("/saudacao/:nome", (req) => {
    retornar html(`<h1>Bem-vindo, ${req.parametros.nome}!</h1>`)
})
servidor.iniciar(8824, falso)
```

<!--http:aula23_resposta4
GET /saudacao/Carla
-->
<!--saida:aula23_resposta4.dk-->
```text
GET /saudacao/Carla
  -> 200 <h1>Bem-vindo, Carla!</h1>
```

**Exercício 5**

<!--codigo:aula23_resposta5.dk-->
```advak
seja produtos = [
    {id: 1, nome: "Caderno", preco: 20},
    {id: 2, nome: "Caneta", preco: 3}
]

servidor.obter("/produtos", (req) => {
    retornar resposta_json(produtos)
})

servidor.obter("/produtos/:id", (req) => {
    seja id = inteiro(req.parametros.id)
    seja achados = produtos.filtrar((p) => p.id == id)
    se (achados.tamanho == 0) {
        retornar resposta_json({erro: "produto não encontrado"}, 404)
    }
    retornar resposta_json(achados[0])
})

servidor.iniciar(8825, falso)
```

<!--http:aula23_resposta5
GET /produtos
GET /produtos/2
GET /produtos/7
-->
<!--saida:aula23_resposta5.dk-->
```text
GET /produtos
  -> 200 [{"id": 1, "nome": "Caderno", "preco": 20}, {"id": 2, "nome": "Caneta", "preco": 3}]
GET /produtos/2
  -> 200 {"id": 2, "nome": "Caneta", "preco": 3}
GET /produtos/7
  -> 404 {"erro": "produto não encontrado"}
```

**Exercício 6**

<!--codigo:aula23_resposta6.dk-->
```advak
seja produtos = []
seja proximo = 1

servidor.publicar("/produtos", (req) => {
    se (req.dados == nulo ou !req.dados.nome ou !req.dados.preco) {
        retornar resposta_json({erro: "informe nome e preco"}, 400)
    }
    seja novo = {id: proximo, nome: req.dados.nome, preco: req.dados.preco}
    proximo = proximo + 1
    produtos.adicionar(novo)
    retornar resposta_json(novo, 201)
})

servidor.obter("/produtos", (req) => {
    retornar resposta_json(produtos)
})

servidor.iniciar(8826, falso)
```

<!--http:aula23_resposta6
POST /produtos {"nome": "Mochila", "preco": 120}
POST /produtos {"nome": "Sem preço"}
GET /produtos
-->
<!--saida:aula23_resposta6.dk-->
```text
POST /produtos {"nome": "Mochila", "preco": 120}
  -> 201 {"id": 1, "nome": "Mochila", "preco": 120}
POST /produtos {"nome": "Sem preço"}
  -> 400 {"erro": "informe nome e preco"}
GET /produtos
  -> 200 [{"id": 1, "nome": "Mochila", "preco": 120}]
```

**Exercício 7**

<!--codigo:aula23_resposta7.dk-->
```advak
seja produtos = [
    {id: 1, nome: "Caderno", preco: 20},
    {id: 2, nome: "Caneta", preco: 3}
]

servidor.deletar("/produtos/:id", (req) => {
    seja id = inteiro(req.parametros.id)
    seja antes = produtos.tamanho
    produtos = produtos.filtrar((p) => p.id != id)
    se (produtos.tamanho == antes) {
        retornar resposta_json({erro: "produto não encontrado"}, 404)
    }
    retornar resposta_json({ok: verdadeiro})
})

servidor.obter("/produtos", (req) => {
    retornar resposta_json(produtos)
})

servidor.iniciar(8827, falso)
```

<!--http:aula23_resposta7
DELETE /produtos/1
DELETE /produtos/1
GET /produtos
-->
<!--saida:aula23_resposta7.dk-->
```text
DELETE /produtos/1
  -> 200 {"ok": true}
DELETE /produtos/1
  -> 404 {"erro": "produto não encontrado"}
GET /produtos
  -> 200 [{"id": 2, "nome": "Caneta", "preco": 3}]
```

**Exercício 8**

<!--codigo:aula23_resposta8.dk-->
```advak
seja total = 0

servidor.obter("/contador", (req) => {
    retornar resposta_json({valor: total})
})

servidor.publicar("/contador/somar", (req) => {
    se (req.dados == nulo ou !e_numero(texto(req.dados.valor))) {
        retornar resposta_json({erro: "valor deve ser um número"}, 400)
    }
    total = total + numero(req.dados.valor)
    retornar resposta_json({valor: total})
})

servidor.publicar("/contador/zerar", (req) => {
    total = 0
    retornar resposta_json({valor: total})
})

servidor.iniciar(8828, falso)
```

<!--http:aula23_resposta8
GET /contador
POST /contador/somar {"valor": 5}
POST /contador/somar {"valor": 10}
POST /contador/somar {"valor": "abc"}
GET /contador
POST /contador/zerar {}
GET /contador
-->
<!--saida:aula23_resposta8.dk-->
```text
GET /contador
  -> 200 {"valor": 0}
POST /contador/somar {"valor": 5}
  -> 200 {"valor": 5}
POST /contador/somar {"valor": 10}
  -> 200 {"valor": 15}
POST /contador/somar {"valor": "abc"}
  -> 400 {"erro": "valor deve ser um número"}
GET /contador
  -> 200 {"valor": 15}
POST /contador/zerar {}
  -> 200 {"valor": 0}
GET /contador
  -> 200 {"valor": 0}
```

---

**Anterior:** [Aula 22](aula22_interface_grafica.md) · **Próxima aula:** [Aula 24 — Projeto final: sistema completo](aula24_projeto_final.md)
