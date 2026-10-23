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
- **Teclado e mouse em português:** `gui.ao_tecla(tratador)` chama o tratador a cada tecla pressionada na janela
  principal, com `{tecla, caractere}`. `area.ao_clicar(tratador)` e `area.ao_soltar(tratador)` chamam o tratador com
  `{x, y}` (as coordenadas do desenho) quando o botão esquerdo do mouse é pressionado ou solto sobre a tela. Chamar de
  novo troca o tratador. Teste: `testes/test_gui_teclado.py`, 17 testes.
  - `tecla` vem em português para sete teclas (`esquerda`, `direita`, `cima`, `baixo`, `espaco`, `enter`, `esc`); as
    outras seguem o nome do Tk (`a`, `A`, `F1`...). `caractere` é o texto digitado: vazio para setas, Esc e F1, e
    `"\r"` para enter. O `ç` chega como `ccedilla` em `tecla` e como `ç` em `caractere`.
  - Uma tecla digitada num campo com foco também chega ao `gui.ao_tecla`; o campo recebe o texto normalmente.
  - Só o botão esquerdo do mouse. Não há `ao_mover` nem tratador de tecla solta.
  - `area.ao_clicar` e `area.ao_soltar` não apagam um `bind` que o programa já tenha feito em `area.widget`.
  - **`ao_soltar` tem outro sentido em `habilitar_drop` e `kanban`:** lá é o tratador de um item arrastado e solto
    numa área; em `area.ao_soltar` é soltar o botão do mouse sobre a tela.
  - Não foi medido se o Windows repete a tecla segurada; o tratador é chamado uma vez por tecla que o Tk entregar, um
    de cada vez, sem juntar eventos.
  - **Janela secundária:** `gui.ao_tecla` só foi testado na janela principal; o bindtags de uma janela secundária
    inclui all, mas o event_generate não permitiu medir.
  - **`gui.ao_tecla` não existe em programas compilados** (`advak_compiler.py`, que também não lista `gui.canvas`).
- **Mudado:** erros dentro de tratadores (botão, `gui.apos`, `gui.repetir`) agora aparecem no terminal (stderr), com a
  mensagem e a linha; antes eram engolidos em silêncio. O mesmo erro repetido aparece uma vez, e ao fechar a janela
  sai um resumo (`⚠ 3 erros em tratadores (1 diferente).`). Um erro causado só por a janela já ter fechado não é mostrado.
  Os tratadores passam a rodar **um por vez**, na ordem em que chegam. Testes: `testes/test_gui_eventos.py`.

### Linguagem e ferramentas

- **Comentário alinhado depois de uma divisão inteira** (`advak_lexer.py`). Antes, `seja y = 7 // 2   // metade`
  dava erro de sintaxe, e `seja z = (10 // 3)   // 3` e `seja b = (20 // 3) + 1   // 201 = criado` rodavam em
  silêncio com valor errado (1 em vez de 3; 6 em vez de 7), porque o segundo `//` da linha era lido como outra
  divisão. Agora o segundo `//` com 2 ou mais espaços (ou um tab) antes, fora de parênteses abertos, é comentário.
  - Continua divisão: `a // b // c` com um espaço, e o que está dentro de parênteses abertos (medido com
    `testar(...)` e com uma chamada aberta em várias linhas). Comentário de frase normal não é afetado em nenhum
    dos dois lugares (0 tokens `//` na medição).
  - Testes: `testes/test_comentarios.py`, classe `TestComentarioAposDivisao`, 8 testes novos. Antes da correção:
    `Ran 22 tests`, `FAILED (failures=7)`; depois: `Ran 22 tests`, `OK`.
  - Comparação de tokens dos 439 `.dk` do repositório, lexer anterior contra o novo: 438 iguais; o
    `testes/comentario_barras.dk` atual difere por ter ganhado linhas novas, e a versão dele no HEAD é igual.
- **`advak formatar` preserva os 2 ou mais espaços antes de um comentário `//` no fim da linha**
  (`advak_formatador.py`). Antes, `seja x = 1   // 3` virava `seja x = 1 // 3` (a divisão `1 // 3`) e
  `imprimir(5)   // 2` virava um programa que nem analisa.
  - Testes: `testes/test_formatador.py`, classe `TesteComentarioAlinhado`, 6 testes novos. Antes da correção:
    `Ran 6 tests`, `FAILED (failures=16, errors=1)`; depois, a suíte do formatador: `Ran 19 tests`, `OK`.
- Com as duas mudanças, as 18 suítes de `testes/` passam e o curso completo (`python testes/curso.py`), rodando
  sozinho, termina com `pronto.` e `exit=0`.
- **Ideia para uma versão futura, não implementada:** palavra própria para a divisão inteira (por exemplo `div`),
  com o `//` sempre como comentário. Veja "Ideia para uma versão futura" no README. Sem versão prevista.
- **Nomes de exceção inexistentes em `advak.py`** (8 pontos: `ImportErro` nas linhas 97, 110, 115, 120, 125, 134 e 149;
  `AttributeErro` na 181; agora `ImportError` e `AttributeError`). Antes, simulando a falta do `colorama` (import
  falhando), `advak.py versao` terminava com `NameError: name 'ImportErro' is not defined` e exit 1; agora termina com
  `Advak 5.2.0` e exit 0.
  - Testes: `testes/test_advak_excecoes.py`, 2 testes novos. Antes da correção: `Ran 2 tests`, `FAILED (failures=2)`;
    depois: `Ran 2 tests`, `OK`. As 20 suítes que já existiam em `testes/` somam 426 testes e passaram (uma rodada
    cada).
  - Limites: só a linha 97 foi reproduzida (simulando a falta do `colorama`); para as outras sete a prova é a varredura
    por AST, que só olha nomes simples em `except` de `advak.py` (não vê `except modulo.Erro` nem outros arquivos).
- **`Arquivo.pasta_do_programa()` e `Arquivo.do_programa(caminho)`** (`advak.py`, `advak_interpreter.py`). A primeira devolve
  a pasta do `.dk` em execução; a segunda junta um caminho relativo a essa pasta (um caminho absoluto fica como está; só
  aceita texto). `advak programa.dk` e `advak run programa.dk` guardam o caminho do programa numa variável do módulo,
  e a pasta não muda se o programa faz `OS.cd(...)`.
  - **O resto não mudou:** `Arquivo.ler`, `escrever` etc. e `importar` continuam procurando pelo **diretório atual**, não pela
    pasta do `.dk`. Os testes fixam isso, inclusive a limitação conhecida: rodando de outra pasta, um módulo homônimo do
    diretório atual é carregado sem aviso.
  - Testes: `testes/test_pasta_programa.py`, 17 testes (6 fixam o comportamento anterior e passavam antes). Antes da
    mudança, os 11 testes das funções novas falhavam (`FAILED (failures=10, errors=1)`); depois, `Ran 17 tests`, `OK`.
    As outras 21 suítes de `testes/` e `python testes/curso.py` passaram (nesta máquina, uma rodada cada).
  - Limites: no REPL e quando o interpretador é usado direto (testados), as duas funções caem no diretório atual, sem
    erro. Não verificados: programa compilado (pela leitura do código, o wrapper gerado não define o caminho, então deve
    cair no diretório atual, mas não foi testado), `advak_nativo.py`, `debug_gui.py`, `debug_studio_executar.py` e
    `_studio_executar`. Não testados também: caminho com "/" sem letra de unidade, "C:foo", UNC, `advak.bat` e
    `advak --live`.
- **Gerador das imagens do jogo 2D do curso** (`docs/curso/ferramentas/gerar_imagens.py`) e as 7 imagens PNG que ele
  produz em `docs/curso/codigos/imagens/` (`fundo` 480×320; `heroi` e `parede` 32×32; `moeda1` a `moeda4` 16×16;
  3.536 bytes no total). Só biblioteca padrão (`zlib`, `struct`); os pixels saem de fórmulas escritas no gerador, sem
  arte de terceiros. `python docs/curso/ferramentas/gerar_imagens.py` escreve; com `--conferir` não escreve e compara
  os bytes (sai com 0 se iguais, 1 se diferirem). O destino vem da localização do script, não do diretório atual.
  - Nada na linguagem usa essas imagens ainda (não há `quadro.imagem`), e nenhuma aula as referencia.
  - Testes: `testes/test_gerador_imagens.py`, 10 testes, `OK`: três processos separados (diretório atual e
    `PYTHONHASHSEED` diferentes) dão o mesmo SHA-256; os pixels dos arquivos versionados são os do gerador; o Tk lê
    cada PNG com o tamanho esperado e o canto (0, 0) transparente só no herói e nas moedas; um PNG cortado
    (40 bytes do herói, criado numa pasta temporária) é recusado pelo Tk. Se os pixels forem iguais e os bytes
    diferirem, o teste imprime um AVISO e passa; quem reprova é o teste de pixels.
  - `.gitattributes` (novo): `*.png binary`, só como declaração explícita; o Git já os detectava como binários nesta
    máquina com `core.autocrlf=true`.
  - As 22 suítes que já existiam em `testes/` e `python testes/curso.py` passaram (nesta máquina, uma rodada cada).
  - Não medidos: bytes idênticos em outra máquina, outro Python ou outro `zlib`. O AVISO de `zlib` foi medido só
    SIMULANDO bytes diferentes (`heroi.png` recomprimido), não com outro `zlib`. A linha `assertNotIn("Traceback")` do
    teste de `--conferir` não foi rodada sobre bytes diferentes (o AVISO e o pixel diferente foram medidos antes
    dela). `core.autocrlf` diferente de `true` não foi testado. A aparência da transparência na tela não foi vista
    (só `transparency_get`). Sem display, o teste do Tk falha em vez de pular. A arte pode mudar antes da aula.
- **`quadro.imagem(x, y, caminho)`** (`gui.canvas`): desenha um PNG com o canto superior esquerdo em (x, y) e devolve o
  número do item, que `mover`, `apagar`, `limpar` e `quantidade` já aceitam. Só PNG, checado pelo nome (`.png`, também
  `.PNG`); sem zoom nem redução. Mudança só em `advak_gui_modern.py` (22 linhas); o interpretador e o `advak.py` não mudaram.
  - **Duas regras, lado a lado:** `quadro.imagem` resolve o caminho **relativo pela pasta do programa** (a do `.dk` em
    execução; sem programa em arquivo, como no REPL, o diretório atual). **`Arquivo.ler`, `escrever` e `importar`
    continuam pelo diretório atual.** Caminho absoluto fica como está. Não depende de `Arquivo.do_programa`.
  - Erros em português (capturáveis): caminho que não é texto, extensão que não é `.png`, arquivo inexistente (com o
    caminho absoluto procurado), pasta, arquivo corrompido ou vazio; `x` e `y` pelas mesmas mensagens dos outros desenhos.
  - A `Tela` guarda cada imagem lida (`caminho absoluto` → `PhotoImage`), porque o Tk apaga a imagem quando ninguém a
    guarda; o mesmo arquivo duas vezes dá dois itens com a mesma imagem. `apagar` e `limpar` não esvaziam esse cache.
  - Testes: `testes/test_gui_imagem.py`, 15 testes. Antes da mudança, `Ran 14 tests`, `FAILED (failures=12, errors=2)`
    (o caso do REPL ainda não existia); depois, `Ran 15 tests`, `OK`. As 24 suítes de `testes/` e `python testes/curso.py`
    (`exit=0`) passaram (nesta máquina, uma rodada cada). Cobrem: rodar de outra pasta, `advak programa.dk` e `advak run`,
    um `imagens/heroi.png` homônimo de 16×16 no diretório atual que **não** é lido, caminho absoluto, tratador de
    `gui.apos`, os erros acima com o texto exato, `.jpg`, `.bmp` e `.gif` recusados, e a imagem sobrevivendo a `gc.collect()`.
  - REPL com `quadro.imagem` (rodado, entrada pela stdin): `ITEM 1 (0, 0, 32, 32)` e `FIM`, e a janela fechou sozinha. O
    código de saída do `advak.py` no REPL não foi medido (o `exit=0` visto era do `tail`).
  - Medido uma vez nesta máquina, em Tk puro: carregar `fundo.png` (480×320) levou 21,5 e 34,9 ms; um quadro com o fundo
    em cache e o herói, mediana de 2,66 ms; o fundo recarregado do disco a cada quadro, mediana de cerca de 30 ms.
  - Limitação conhecida (com teste): um GIF renomeado para `.png` é lido pelo Tk, porque só o nome é checado. Não há
    suporte a GIF.
  - **Medido depois.** Cada item: uma vez, nesta máquina (Windows 10 Home 10.0.19045, Python 3.13.8, Tk 8.6), sem outra
    máquina nem outra versão.
    - Custo por quadro pelo interpretador (**PC parado, confirmado pelo usuário**): `gui.repetir(16, ...)`, 5000 ms por
      execução, 2 execuções por cenário. Mediana do intervalo entre quadros cerca de 16,8 ms (a previsão de cerca de
      31 ms **não bateu**). Mediana do tratador: 1 `mover` 0,42 a 0,48 ms; 10 `mover` 8,45 a 9,06 ms; fundo + herói +
      4 moedas movendo os 5, 4,98 a 5,12 ms; com 4 `colide`, 8,20 a 8,22 ms; com `trocar_imagem` por quadro, 7,57 a 7,71
      ms (inclui `k = k + 1` e a indexação; a parte da `trocar_imagem` não foi separada). Os 4 primeiros quadros com
      `trocar_imagem` levaram 14,6 a 29,9 ms. Numa execução do cenário vazio houve uma parada de cerca de 5 s, causa não
      investigada. `ao_tecla` ficou fora desta medição.
    - Memória do cache de imagens (**PC em uso**): fundo 480×320 com 200 caminhos distintos. Logo depois de criar as
      imagens, antes de desenhar: 1.100.411 B de `PrivateUsage` por imagem (previsão de 614.400 B: **não bateu**,
      1,79×). Depois de `limpar()` com as imagens ainda no cache: 631.747 a 687.718 B por imagem (1,03× a 1,12× a
      previsão de 614.400 B; fundo ×10, ×100 e ×200, uma vez, nesta máquina, PC em uso; no ×1 não houve queda). Herói
      32×32 com 200, 14.643 B por imagem
      (previsão de 4.096 B: **não bateu**, 3,58×); 200 itens do mesmo caminho, cerca de 870 B por item. Esvaziar o cache à
      mão devolveu a memória do fundo; `apagar` e `limpar` não esvaziam o cache. A sobra por imagem não foi explicada.
    - Outros tipos de PNG (**PC em uso**, sem previsão escrita antes): em 14 casos de 4×4 (RGB, cinza 8 e 16 bits, cinza
      + alfa, paleta com e sem `tRNS`, paleta de 2 bits, RGB e RGBA de 16 bits, os 4 filtros de linha, entrelaçado
      Adam7, `gAMA` 45455 e 100000) o Tk e o `quadro.imagem` leram os pixels esperados; transparência conferida só no
      cinza + alfa e na paleta com `tRNS`.
    - Caminho relativo dentro de módulo importado (**PC em uso**): 7 casos. O caminho de `quadro.imagem` vale a partir da
      **pasta do programa principal** (imagem 32×32), não da do módulo (16×16) nem do diretório atual (480×320).
      `importar` com caminho relativo não acha o módulo quando o diretório atual é outra pasta (`Módulo não encontrado`).
      O `advak` saiu com código 0 nesse erro.
    - Repetição de tecla segurada (Windows com `KeyboardDelay = 1` e `KeyboardSpeed = 31`; estado do PC não registrado).
      Tk puro: atraso até a 1ª repetição 615 a 627 ms (previsto 440 a 560 ms: **não bateu**), mediana do intervalo
      37,2 a 37,7 ms (previsto 30 a 40 ms: bateu), um `KeyRelease` por aperto. Duas teclas: com a 2ª entrando, a 1ª
      deixou de gerar `KeyPress` nas duas fases, e a 2ª repetiu com atraso de 627 e 621 ms. `gui.ao_tecla`: atraso 609 a
      632 ms e mediana 37,3 a 37,9 ms, com dispersão maior (intervalos de 13,8 a 59,4 ms; causa não investigada); esta
      parte não recebe `KeyRelease`.
  - **Lido do código, não medido:** `gui.repetir` não espera o tratador (enfileira e reagenda o próximo `after` na hora);
    não foi medido com um tratador lento nem com a fila crescendo.
  - **Não medido / a decidir:** a retomada das teclas (a 1ª voltar a repetir ao soltar a 2ª); aparência na tela e
    transparência real; alfa parcial; PNG de editor real, cinza de 1, 2 e 4 bits, paleta de 1 e 4 bits e imagens
    grandes; JPEG real; `_SERIALIZAR_CALLBACKS = False` com várias threads; sem display (o teste falha em vez de
    pular); `advak.bat`, `advak --live` e programa compilado; importações em cadeia. Possível necessidade de evento de
    soltura, a decidir em etapa própria.
- **`quadro.trocar_imagem(item, caminho)`, `quadro.colide(a, b)`, `quadro.para_frente(item)` e `quadro.para_tras(item)`**
  (`gui.canvas`). Só `advak_gui_modern.py`; `imagem` passou a usar um auxiliar interno `_carregar` (mesmas mensagens, os 15
  testes de `quadro.imagem` passaram sem alteração).
  - `trocar_imagem` troca o desenho de um item que já é imagem, mantendo número, posição e `quantidade`. Reaproveita o cache
    de `quadro.imagem` (o mesmo arquivo dá a mesma imagem). Se o caminho falhar, o item não muda. Item que não é imagem:
    `O item N não é uma imagem (é um retângulo).` (também `um círculo`, `uma linha`, `um texto`; outro tipo do Tk aparece
    como `do tipo 'polygon'`). Os erros de caminho são os de `quadro.imagem`.
  - `colide` devolve `verdadeiro` ou `falso`, **por retângulo; encostar não conta**; `colide(a, a)` é `verdadeiro`. Aceita
    qualquer tipo de item. Retângulo e círculo usam as coordenadas exatas; imagem, linha e texto usam o `bbox` do Tk. **O
    retângulo de uma imagem inclui os pixels transparentes**, e o de um círculo é o quadrado que o contém: a colisão fica
    um pouco maior que o desenho. Linha e texto ficam ainda um pouco maiores (ver o medido abaixo).
  - `para_frente` e `para_tras` mudam a ordem de desenho (quem fica por cima); `quantidade` não muda.
  - Item que não existe: a mensagem de sempre (`O item N não existe nesta tela (já foi apagado ou nunca foi criado).`).
  - **Medido (Tk, uma vez, esta máquina):** o `bbox` do Tk é exato para imagem (32×32 em (10, 10) → (10, 10, 42, 42)) e
    maior que o desenho nos outros tipos: retângulo (100, 10, 140, 40) → (99, 9, 141, 41), com e sem preenchimento; círculo
    (40, 80, 80, 120) → (39, 79, 81, 121) (1 px por lado); linha de espessura 1 na diagonal (100, 100)-(160, 140) → (98, 98,
    162, 142) (2 px); linha horizontal de espessura 3 → 4 px por lado; texto "Olá" tamanho 12 em (200, 100) → (199, 100, 225,
    121). Por isso retângulo e círculo usam `coords` (com o `bbox`, dois retângulos encostando colidiriam). `tag_raise` e
    `tag_lower` com o número do item mexeram só nesse item (ordem de `find_all()` conferida).
  - Testes: `testes/test_gui_itens.py`, 18 testes. Antes da mudança, `Ran 18 tests`, `FAILED (failures=7, errors=11)`;
    depois, `Ran 18 tests`, `OK`. As 25 suítes de `testes/` (as 24 de antes mais esta) e `python testes/curso.py`
    (`exit=0`) passaram (nesta máquina, uma rodada cada).
  - **Medido depois** (uma vez, nesta máquina): `trocar_imagem` a cada quadro em `gui.repetir(16, ...)` (**PC parado,
    confirmado pelo usuário**) deu mediana de tratador de 7,57 a 7,71 ms contra 4,98 a 5,12 ms do mesmo cenário sem ela
    (o excesso inclui `k = k + 1` e a indexação; a `trocar_imagem` isolada não foi separada); 4 `colide` por quadro somaram
    cerca de +3,1 a +3,2 ms. Memória (**PC em uso**): as imagens trocadas continuam no cache, que só é esvaziado à mão; com 200
    imagens de 32×32 no cache foram 14.643 B por imagem (previsão de 4.096 B: **não bateu**).
  - **Não medido / a decidir:** `colide` com polígono e outros tipos (usariam o `bbox`, sem teste); linha e texto em
    outras fontes, tamanhos ou escalas de tela; várias threads chamando estes métodos ao mesmo tempo; custo da
    `trocar_imagem` isolado e com muitos arquivos distintos (só 4); o custo de `para_frente` e `para_tras`; a retomada das teclas e a aparência da transparência.

### Conhecido

- **OBSERVADO:** `advak.py:344` faz `args[0].lower()` e passa o caminho do programa já em minúsculas a `cmd_run` ao rodar
  `advak programa.dk` (linha 406). Medido no Windows: o caminho impresso por `quadro.imagem` ("procurei em ...") saiu em
  minúsculas. Em sistema que diferencia maiúsculas o arquivo talvez não fosse achado: só leitura do código, não
  testado. `advak run programa.dk` passa `args[1]` sem o `lower()` (só leitura do código). É anterior à `quadro.imagem`;
  o `advak.py` não foi alterado.
- **`quadro.imagem` chamado de outra thread** só funciona com a janela em `mainloop` (sem ele:
  `RuntimeError: main thread is not in main loop`, medido). É o caso dos tratadores de `gui.apos`, que rodam com a
  janela em `mainloop`; o teste cobre isso.
- A lição 22 do curso pode falhar sob carga forte de CPU: com 4 processos em loop, `python testes/curso.py` deu
  "bloco desatualizado" em blocos da lição 22 (vistos: `aula22_resposta5.dk` no código corrigido; `aula22_resposta7.dk`
  e `aula22_exemplo3.dk` no código de antes das correções acima). O curso completo rodando sozinho passou
  (`exit=0`, cerca de 9 minutos); uma execução completa feita ao mesmo tempo que outras tarefas falhou. A lição usa
  janela gráfica e temporizadores. A causa de `aula22_resposta7` foi investigada em 2026-10-20 e a causa natural
  não foi encontrada (veja o item dele logo abaixo); essa investigação não olhou os outros blocos citados. Não há
  correção prometida.
- **Os tratadores da interface gráfica rodam um por vez; um tratador que espera por outro tratador não termina.** O
  segundo só começa quando o primeiro acaba. Medido: um tratador A esperando um sinal que só o tratador B envia, com B
  chegando depois de A, não recebeu o sinal em 3 s; com `_SERIALIZAR_CALLBACKS = False` (em `advak_gui_modern.py`,
  volta a uma thread por chamada) os dois terminaram em 0,2 s. Uma busca por `esperar`, `aguardar`, `dormir` e `sleep`
  nos `.dk` do curso e de `projetos/` só achou `embarcado.aguardar` em `projetos/mobile_embarcado_demo.dk`, que não
  verifiquei se está dentro de um tratador.
- **`aula22_resposta7` (lição 22) é intermitente em algumas condições; a causa natural não foi encontrada.** O exemplo
  `docs/curso/codigos/aula22_resposta7.dk` às vezes imprime `Tarefas na tabela: 0` ou `1` em vez de `2`, sem mostrar
  erro. Uma vez o curso completo (`python testes/curso.py`, sozinho) deu `exit=1` por causa dele ("bloco
  desatualizado", 7 min 34 s) e `exit=0` na vez seguinte (9 min 22 s).
  - Medido (exemplo isolado, falhas por rodadas): 10 em 60 na primeira medição, com outros comandos rodando em
    paralelo e sem controle; 4 em 80 com carga de CPU aplicada de propósito; 0 em 160 em silêncio (80 com
    `ADVAK_EVENTOS` e 80 sem); em 2026-10-20, 0 em 200 com relógio e eventos e 0 em 200 no código sem instrumentação,
    ambos com a mesma carga.
  - Provado só em condição artificial: parar a janela por cerca de 700 ms ou mais, no início, produz exatamente essas
    saídas (10 rodadas por condição: com 700 ms, 9 deram `1` e 1 deu `0`; com 1000 ms e com 1500 ms, as 10 rodadas de
    cada uma deram `0`). Não foi provado que as falhas naturais tenham essa causa.
  - Não corrigido: não há mudança no interpretador nem no exemplo.

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
