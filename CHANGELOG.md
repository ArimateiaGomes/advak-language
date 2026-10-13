# Histórico de versões

Todas as mudanças importantes da Advak Language. Datas no formato ano-mês-dia.

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
