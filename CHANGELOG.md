# Histórico de versões

Todas as mudanças importantes da Advak Language. Datas no formato ano-mês-dia.

## [Não lançado]

### Bancos de dados

- **Banco automático ou manual (SQLite e PostgreSQL)**, escolhido por projeto: `banco.conectar(url, modo="manual"|"automatico"|"perguntar", tabelas=mapa)`
  ou `ADVAK_BANCO_MODO` no `.env`. O padrão é **`manual`** (igual a antes: nada é criado sozinho, só o arquivo SQLite).
  - `db.preparar(mapa)` cria as tabelas e as colunas novas que faltam, **sem apagar nada** nem alterar tipos, e
    devolve um relatório; `db.diferencas(mapa)` só lista o que falta, sem alterar; `db.adicionar_coluna(tabela, campo, definicao)`.
    O mapa é um mapa comum: `{"clientes": {"id": "autonum", "nome": "texto obrigatorio"}}`. Com `tabelas=mapa` na conexão,
    `db.preparar()` dispensa o argumento. Em `automatico` o mapa é criado ao conectar.
  - **Coluna `obrigatorio` sem `padrao`** em tabela com dados é **recusada com explicação** (no SQLite, também em tabela
    vazia, e `unico` ao adicionar coluna). As outras colunas do mapa seguem.
  - **`perguntar` é para programas de console**: mostra o que falta e pergunta `[s/N]`. Sem entrada para ler a resposta,
    vira `manual` com um aviso e **nunca trava**.
  - `db.criar_banco(nome)` no conector PostgreSQL; em `automatico` o banco que não existe é criado ao conectar
    (testado com driver falso e confirmado no PostgreSQL 17.4 local; ver "Teste em servidor real" abaixo).
  - **Mensagens em português para o PostgreSQL**: servidor que não responde, porta errada, senha/usuário errados e banco
    inexistente (mais driver ausente, que já existia), sempre com o texto original do driver no final
    (`Detalhe do driver: ...`). Erro desconhecido passa sem conversão, como antes.
  - **PostgreSQL em português do Windows (cp1252), banco inexistente**: o psycopg2 levanta `UnicodeDecodeError` em vez de
    um erro com texto, então o texto não pode ser classificado. Achado ao tentar um servidor real. Agora, nesse caso, a
    Advak reconecta ao banco `postgres` e consulta `pg_database`: se o banco não existe, segue o fluxo de "banco
    inexistente" (mensagem própria, ou criação em `automatico`); se existe, ou se a reconexão também falha com
    `UnicodeDecodeError` (não dá para distinguir), mantém a mensagem genérica "senha, usuário ou banco incorretos?".
    Em ambos os casos o detalhe do servidor aparece depois de `Detalhe do driver:`, lido como cp1252 só para exibir.
    Coberto por testes com driver falso (`testes/test_banco_automatico.py`) e **confirmado no PostgreSQL 17.4
    local** (ver "Teste em servidor real" abaixo).
  - Erros `no such table` / `no column named` do SQLite e do PostgreSQL ganham, **depois** da mensagem original, uma linha de
    `Dica:` em português (a saída registrada da aula 21 foi atualizada).
  - Fora desta versão: instalar servidor, a palavra `modelo`, outros bancos, o caminho legado do PostgreSQL.
    Testes: `testes/test_banco_automatico.py`. Proposta e decisões: `docs/BANCO_AUTOMATICO_PROPOSTA.md`.
  - **Teste em servidor real (2026-10-16)**: PostgreSQL 17.4 no Windows, mensagens em português (cp1252), em bancos
    `advak_teste_*` criados só para isso. Nenhum banco existente foi tocado e nada foi apagado.
    - `UnicodeDecodeError` em banco inexistente: o psycopg2 puro levanta `UnicodeDecodeError` (bytes cp1252 do servidor).
      Em `modo="automatico"` a Advak cria o banco e conecta; em `modo="manual"` dá a mensagem em português
      ("O banco '...' não existe neste servidor...", com `Detalhe do driver:`) e **não cria** nada.
    - `db.preparar` duas vezes: a 1ª cria as tabelas; a 2ª diz "Nada a fazer", sem duplicar.
    - `db.diferencas` lista o que falta (coluna e tabela) sem alterar nada, comprovado por snapshot independente
      (psql, `information_schema.columns`) idêntico antes e depois.
    - `db.adicionar_coluna` e recusas: coluna nova entra, repetida avisa "já existe", `obrigatorio` sem `padrao`
      em tabela com dados é recusada com explicação, as demais do mapa seguem.
    - `modo="perguntar"`: com `n` não cria nada (tabelas faltando, e banco inexistente: o banco continua inexistente
      e o programa **para com a mensagem de erro de banco inexistente**, não segue em silêncio);
      com `s` cria (tabelas faltando em banco existente; banco inexistente: uma pergunta do banco e uma das tabelas).
    - Três falhas esperadas, com mensagem em português e `Detalhe do driver:`, nenhuma cria banco: porta errada,
      usuário falso (mensagem genérica "senha, usuário ou banco incorretos?"; não dá para distinguir de outros
      motivos) e banco inexistente em `manual`.
  - **Defeito achado nesse teste e corrigido (`e581630`)**: no `modo="perguntar"` com mapa, a confirmação ao conectar
    era pedida **duas vezes** com resposta `s` (a 2ª, em `preparar`); isso foi visto no servidor real. Pelo fluxo do
    código, em console um `n` na 2ª impediria a criação apesar do `s` anterior; isso foi **deduzido da leitura do código
    e não foi reproduzido no servidor real**. Agora é uma pergunta só (confirmado no servidor real, nos passos com
    `s`). Teste: `TestePerguntarUmaVezSo` conta as chamadas de `input`.
  - **Limites do que foi testado em servidor real**: só PostgreSQL local, versão 17.4, Windows em português. Os bytes
    das mensagens de erro do servidor chegaram em cp1252; a consulta mostrou `server_encoding = UTF8` e
    `lc_messages = pt-BR`, e nada além disso foi verificado sobre a codificação. MySQL, SQL Server, Firebird, Redis,
    MongoDB e os demais **continuam não testados em servidor real**. O quadro de erro de porta errada e de usuário
    falso aparece sem "Localização" nem trecho do código; é cosmético e ainda não foi investigado.
- **`db.tabela` não diz mais "criada" quando a tabela já existe com colunas diferentes** das pedidas (conectores
  SQL). Agora devolve `ℹ️  Tabela 'x' já existe com colunas diferentes das pedidas (faltam na tabela: ...; a mais
  na tabela: ...). Nada foi alterado.` A tabela e os dados continuam intactos (a coluna nova **não** é adicionada).
  Tabela nova, ou já existente com as mesmas colunas, mantém o texto de antes. Teste: `testes/test_tabela_existente.py`.

### Interface gráfica

- **`gui.canvas(janela, largura, altura, fundo)`**: área de desenho 2D em português. Devolve uma tela com
  `retangulo`, `circulo`, `linha`, `texto`, `mover`, `apagar`, `limpar` e `quantidade`. A origem (0, 0) fica no
  canto superior esquerdo e o `y` cresce para baixo. Cada desenho devolve um número de item, usado para mover
  ou apagar. Cores por nome em português (`vermelho`, `azul`...) ou hexadecimal (`"#ff8800"`). Erros (cor
  desconhecida, tamanho negativo, item inexistente) saem em português e podem ser capturados com `tentar`.
  O `canvas` SVG global continua como antes. Teste: `testes/test_gui_canvas.py`.
- **Atenção:** `tela` é palavra reservada da Advak, então a variável que guarda o canvas precisa de outro
  nome, como `area` (`seja area = gui.canvas(janela, 400, 300, "preto")`).
- **Ordem dos argumentos diferente do SVG:** `area.texto(x, y, texto, cor, tamanho=12)` não segue a ordem de
  `tela.texto(txt, x, y)` do canvas SVG global (aí o texto vem primeiro).
- **`area.widget` é um atalho provisório** que expõe o objeto tkinter (hoje usado para `bind` de mouse e
  teclado). Será substituído por eventos em português num passo futuro; não conte com ele a longo prazo.

## [5.2.0] — 2026-10-13

Versão com mais recursos de linguagem, 23 bancos de dados, IA opcional, leitura de documentos e
documentação completa. **Programas escritos para a 5.1 continuam funcionando**: os recursos novos só
valem onde você os usa.

### Linguagem

- **Intervalos**: `1..10` (sem o fim), `1..=10` (com o fim), `passo`/`step` (`10..=0 passo -5`). Dentro de
  `para (i em 1..=100000000)` o intervalo é preguiçoso (não cria lista); fora de laço vira lista.
- **Compreensão de listas**: `[x * 2 para x em lista se x > 0]`, vários `para`/`se`, desmontagem
  (`para (a, b) em pares`), sinônimos `for`/`in`/`if`.
- **Interpolação com formatação** em textos com crase: `${preco:moeda}`, `${0.075:porcentagem.1}`,
  `${7:03d}`, `${d:dd/mm/aaaa hh:mm}`, alinhamento (`>10`, `^10`), `maiusculo`, `titulo`... com separadores
  do Brasil e arredondamento escolar. `${}` agora aceita chaves e textos dentro da expressão.
- **Tipagem opcional**: `seja idade: inteiro = 17`, `função somar(a: numero, b: numero = 0) -> numero`,
  `texto?`, `inteiro | texto`, `lista[numero]`, nomes de classe/estrutura/enum. Conferida em tempo de
  execução só onde foi escrita; mensagens em português. Lambdas com seta e campos de `estrutura` ainda não.
- Novos símbolos: `..`, `..=` e `->`.

### Bancos de dados

- **Conectores de 23 bancos** (`advak_conectores.py`) com a mesma API em português: SQLite, PostgreSQL,
  MySQL, MariaDB, SQL Server, Oracle, Firebird, IBM Db2, CockroachDB, TimescaleDB, DuckDB, ClickHouse,
  Snowflake, Google BigQuery, Cassandra, MongoDB, CouchDB, Google Firestore, Amazon DynamoDB, Elasticsearch,
  Redis, Neo4j e InfluxDB. Conexão por URL (`banco.conectar("mysql://...")`), por dados separados ou pelo
  `.env` (`ADVAK_<BANCO>_URL`). Drivers opcionais, com mensagem do `pip install` exato quando faltam.
- Comando `advak bancos`.
- O modo antigo (`banco.conectar()`, `advak run ... --db`) não mudou.
- **Testes honestos**: o SQLite e o PostgreSQL (conector novo, no `testes/bancos_externos.dk`, em um banco
  descartável) foram testados contra servidor real; CockroachDB e TimescaleDB, que usam o mesmo driver, não. Os
  outros 21 têm testes com driver simulado (89 testes). O **DuckDB** está marcado como *em teste / instável no Windows* (travamento ao
  usar parâmetros de texto dentro de threads). Veja `docs/BANCOS_DE_DADOS.md`.

### IA e documentos (opcionais)

- **IA com API única** (`advak_ia.py`): Anthropic, OpenAI, Gemini, Mistral, Groq, DeepSeek, OpenRouter e
  Ollama (local). Vários provedores com reserva automática, chaves só no `.env`, `gerar_codigo` que valida a
  sintaxe, pede confirmação e **nunca executa** o que gerou. Só é carregada quando o programa usa
  `ia.conectar(...)`. Comando `advak ia`. A Advak funciona 100% sem ela.
- **Leitura de documentos** (`advak_documentos.py`): `documento.ler(...)` para TXT, MD, JSON, CSV, XLSX,
  PDF, DOCX, PPTX e imagens (OCR), e `{anexos: [...]}` nas perguntas à IA, com o texto tratado como dado
  (e a regra reforçada no prompt de sistema). Comando `advak documentos`.
- Nenhuma API de IA real foi chamada nos testes (não havia chaves); os testes usam respostas simuladas e
  um servidor local falso.

### Correções

- `caso` aceita condições: `combinar(verdadeiro) { caso n >= 9: ... }`.
- `importar { x } de "arquivo.dk";` aceita o `;` no fim.
- `servidor.rota("/x", "GET", fn)` (as duas ordens de argumentos) e `servidor.json/html/texto/redirecionar`.
- `banco.sql(q, valor)` e `banco.sql(q, [valores])` com `%s` e `$1` (a lista não vira mais *ARRAY* no PostgreSQL).
- `enum` e tipos algébricos: `Cor.VERDE` / `Arvore.Folha` não dão mais "Variante 'get' não existe".
- Geradores: `produzir 1;` com ponto e vírgula.
- `inicio(...)` funciona como construtor (também herdado); `lista.primeiro` e `lista.ultimo` sem parênteses.
- Arquivos `.dk` salvos com BOM pelo Bloco de Notas do Windows funcionam.
- **`advak formatar`**: `+=`, `-=`, `*=`, `/=`, `=>` etc. ganham espaços sem quebrar; textos e comentários de várias
  linhas não são mais reindentados nem alterados; o recuo não é mais colapsado.
- **`advak --verificar`**: não acusa "possível divisão" para o `/` de textos e comentários.
- **Transpilador Python/C**: números negativos literais (`-2`) e decimais (`2.5`) e os operadores `e`/`ou`.
- `gerar_codigo` (IA): as instruções passadas à IA estavam erradas sobre interpolação de textos.

### Documentação

- Novos: `docs/INSTALACAO.md`, `docs/BANCOS_DE_DADOS.md`, `docs/IA.md`, `docs/DOCUMENTOS.md`,
  `docs/RECURSOS_5_2.md` e este `CHANGELOG.md`. README atualizado (novidades, 23 bancos, links).
- Dezenas de testes novos em `testes/` (arquivos `.dk` e Python), um por recurso.

### Notas de compatibilidade

- O formatador de código mudou de comportamento (para melhor): rode `advak formatar --ver arquivo.dk`
  antes de formatar um arquivo antigo.
- `->` agora é um símbolo da linguagem (tipo de retorno). Em `i-->0` continua sendo o decremento.
- `//` : divisão inteira ou comentário? Depois de um valor na mesma linha, `//` é **divisão inteira** quando o
  resto da linha é uma conta completa (sem dois valores seguidos, sem caracteres estranhos, sem terminar em
  operador) **e** ele está escrito com um espaço (`7 // 2`, `7//2`) ou dentro de parênteses/colchetes
  (`imprimir(7   // 2)`, `lista[9 // 2]`). Em qualquer outro caso é **comentário**: texto que parece frase
  (`// 2 elevado a 3`), símbolos soltos (`// 8 > 8 ? falso`, `// +`) e, fora dos parênteses, comentário alinhado
  com 2 ou mais espaços (ou tab) antes (`seja x = 1   // 3.5`). Em linha própria, `//` é sempre comentário.
  Antes, `imprimir(2 ** 3)  // 2 elevado a 3` dava "token inesperado '//'" e `seja x = 1  // 3.5` virava, em
  silêncio, uma divisão. Quem escreve divisão com 2 ou mais espaços fora de parênteses (`7  //  2`) deve usar
  um espaço só ou parênteses. Os 46 exemplos do repositório geram exatamente os mesmos tokens de antes.
  Dentro de parênteses/colchetes, textos entre aspas contam como valores (`imprimir(7 // 2, "x")` e
  `tentar { imprimir(10 // 0) } capturar (e) { imprimir("A:", e) }` são divisão; a primeira versão desta regra
  os lia como comentário).
- `banco.conectar("postgres")` sozinho continua significando "o banco chamado postgres" do modo antigo; para
  o PostgreSQL pelo conector novo, use `postgresql://...` ou `banco.conectar("postgresql")`.

### Conhecido / pendente

- Bancos de dados: 21 dos 23 ainda sem teste contra servidor real (SQLite e PostgreSQL passaram em teste real).
- IA: nenhum provedor foi testado contra a API real. OCR: só simulado (falta o Tesseract no computador de testes).
- Ficaram para uma próxima versão: `async`/`await` com concorrência real, tipo `Resultado` com `?`,
  gerenciador de pacotes e extensão do VS Code.

## [5.1.0] — 2026-10-11

Primeira versão publicada no GitHub: interpretador em Python com palavras-chave em português (`seja`, `se`,
`para`, `função`, `classe`...), banco PostgreSQL embutido (com SQLite como reserva), servidor web, interface
gráfica, testes unitários, compilação para `.exe`, REPL, formatador, verificador, depurador e exemplos.
Licença MIT.
