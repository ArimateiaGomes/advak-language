"""
Advak — Conectores de banco de dados (API única em português)

    seja db = banco.conectar("mysql://usuario:senha@localhost:3306/loja")
    seja db = banco.conectar("mysql", host="localhost", usuario="root", senha="x", banco="loja")
    seja db = banco.conectar("mysql")          # lê ADVAK_MYSQL_URL do .env

    db.tabela("produtos", {"id": "autonum", "nome": "texto obrigatorio", "preco": "decimal"})
    db.inserir("produtos", {"nome": "Caneta", "preco": 2.5})
    db.buscar("produtos").onde("preco > %s", 1).ordenar("nome").executar()
    db.atualizar("produtos", {"preco": 3}).onde("id = %s", 1).executar()
    db.deletar("produtos").onde("id = %s", 1).executar()
    db.sql("SELECT * FROM produtos WHERE id = %s", [1])
    db.fechar()

Regras:
  * Os drivers são opcionais: só são importados quando o banco é usado.
    Se faltar, a mensagem diz qual `pip install` rodar.
  * Marcadores aceitos nas consultas: %s e $1 (convertidos para o formato do banco).
  * Senhas ficam no .env (ADVAK_<BANCO>_URL), nunca no código.
  * atualizar().executar(), deletar().executar() e sql() de escrita retornam o
    número de linhas afetadas.
"""

import os
import re
import sys
import json
import importlib
import importlib.util
from decimal import Decimal
from urllib.parse import urlparse, unquote, parse_qsl


class ErroBanco(RuntimeError):
    """Erro de banco de dados com mensagem em português."""


# ══════════════════════════════════════════════════════════════════════════════
#  Registro dos bancos suportados
# ══════════════════════════════════════════════════════════════════════════════
# 'testado': 'real' = testado contra o banco de verdade neste repositório;
#            'mock'  = testado só com driver simulado (veja docs/BANCOS_DE_DADOS.md)

BANCOS = {}


def _registrar(tipo, nome, grupo, modulo, pip, esquemas, porta, classe, testado, apelidos=()):
    BANCOS[tipo] = dict(tipo=tipo, nome=nome, grupo=grupo, modulo=modulo, pip=pip,
                        esquemas=tuple(esquemas), porta=porta, classe=classe,
                        testado=testado, apelidos=tuple(apelidos))


# ── Registro (um banco por linha; novos grupos entram aqui) ──────────────────
_registrar('sqlite',   'SQLite',     'Relacional', 'sqlite3',  '(já vem com o Python)',
           ['sqlite', 'sqlite3'], None, 'ConectorSQLite', 'real')
_registrar('duckdb',   'DuckDB',     'Analítico',  'duckdb',   'duckdb',
           ['duckdb'], None, 'ConectorDuckDB', 'instavel')
_registrar('postgres', 'PostgreSQL', 'Relacional', 'psycopg2', 'psycopg2-binary',
           ['postgresql', 'postgres', 'pg'], 5432, 'ConectorPostgres', 'mock', ('postgresql', 'pg'))
_registrar('mysql',    'MySQL',      'Relacional', 'pymysql',  'pymysql',
           ['mysql'], 3306, 'ConectorMySQL', 'mock')
_registrar('mariadb',  'MariaDB',    'Relacional', 'pymysql',  'pymysql',
           ['mariadb'], 3306, 'ConectorMariaDB', 'mock')
_registrar('mssql',    'SQL Server', 'Relacional', 'pymssql',  'pymssql',
           ['mssql', 'sqlserver'], 1433, 'ConectorMSSQL', 'mock', ('sqlserver', 'sql_server'))
_registrar('mongodb',  'MongoDB',    'Documentos (NoSQL)', 'pymongo', 'pymongo',
           ['mongodb', 'mongodb+srv', 'mongo'], 27017, 'ConectorMongoDB', 'mock', ('mongo',))
_registrar('redis',    'Redis',      'Chave-valor e cache', 'redis', 'redis',
           ['redis', 'rediss'], 6379, 'ConectorRedis', 'mock')
# ── Grupo 2, lote A ──
_registrar('cockroachdb', 'CockroachDB', 'Relacional', 'psycopg2', 'psycopg2-binary',
           ['cockroachdb', 'cockroach'], 26257, 'ConectorCockroach', 'mock', ('cockroach',))
_registrar('timescaledb', 'TimescaleDB', 'Séries temporais', 'psycopg2', 'psycopg2-binary',
           ['timescaledb', 'timescale'], 5432, 'ConectorTimescale', 'mock', ('timescale',))
_registrar('oracle',   'Oracle',     'Relacional', 'oracledb', 'oracledb',
           ['oracle', 'oracledb'], 1521, 'ConectorOracle', 'mock')
_registrar('firebird', 'Firebird',   'Relacional', 'firebird.driver', 'firebird-driver',
           ['firebird'], 3050, 'ConectorFirebird', 'mock')
_registrar('db2',      'IBM Db2',    'Relacional', 'ibm_db_dbi', 'ibm_db',
           ['db2', 'ibmdb2'], 50000, 'ConectorDb2', 'mock', ('ibmdb2', 'ibm_db2'))
# ── Grupo 2, lote B ──
_registrar('clickhouse', 'ClickHouse', 'Analítico', 'clickhouse_connect', 'clickhouse-connect',
           ['clickhouse', 'clickhouses'], 8123, 'ConectorClickHouse', 'mock')
_registrar('snowflake', 'Snowflake', 'Analítico', 'snowflake.connector', 'snowflake-connector-python',
           ['snowflake'], None, 'ConectorSnowflake', 'mock')
_registrar('bigquery', 'Google BigQuery', 'Analítico', 'google.cloud.bigquery', 'google-cloud-bigquery',
           ['bigquery', 'bq'], None, 'ConectorBigQuery', 'mock', ('bq', 'google_bigquery'))
_registrar('couchdb',  'CouchDB',    'Documentos (NoSQL)', 'couchdb', 'couchdb',
           ['couchdb', 'couchdbs'], 5984, 'ConectorCouchDB', 'mock')
_registrar('firestore', 'Google Firestore', 'Documentos (NoSQL)', 'google.cloud.firestore',
           'google-cloud-firestore', ['firestore'], None, 'ConectorFirestore', 'mock')
_registrar('dynamodb', 'Amazon DynamoDB', 'Documentos (NoSQL)', 'boto3', 'boto3',
           ['dynamodb', 'dynamo'], None, 'ConectorDynamoDB', 'mock', ('dynamo',))
_registrar('elasticsearch', 'Elasticsearch', 'Busca', 'elasticsearch', 'elasticsearch',
           ['elasticsearch', 'elastic', 'es'], 9200, 'ConectorElasticsearch', 'mock', ('elastic',))
_registrar('neo4j',    'Neo4j',      'Grafos', 'neo4j', 'neo4j',
           ['neo4j', 'bolt', 'neo4j+s', 'bolt+s', 'neo4j+ssc', 'bolt+ssc'], 7687, 'ConectorNeo4j', 'mock')
_registrar('influxdb', 'InfluxDB',   'Séries temporais', 'influxdb_client', 'influxdb-client',
           ['influxdb', 'influx'], 8086, 'ConectorInfluxDB', 'mock', ('influx',))
_registrar('cassandra', 'Cassandra', 'Colunar distribuído', 'cassandra', 'cassandra-driver',
           ['cassandra'], 9042, 'ConectorCassandra', 'mock')


def _tipo_por_nome(nome):
    n = str(nome).strip().lower()
    if n in BANCOS:
        return n
    for tipo, info in BANCOS.items():
        if n in info['apelidos'] or n in info['esquemas']:
            return tipo
    return None


def driver_instalado(tipo):
    info = BANCOS[tipo]
    try:
        return importlib.util.find_spec(info['modulo']) is not None
    except (ImportError, ValueError):
        return False


def listar_bancos():
    """Lista de dicts com os bancos suportados e se o driver está instalado."""
    return [dict(info, instalado=driver_instalado(t)) for t, info in BANCOS.items()]


def tabela_bancos():
    """Texto para o comando `advak bancos`."""
    linhas = ["", "  Bancos de dados suportados pela Advak", "  " + "─" * 100,
              f"  {'Banco':<18}{'Tipo':<22}{'Driver (pip install ...)':<29}{'Instalado':<11}{'Testes'}",
              "  " + "─" * 100]
    for b in listar_bancos():
        inst = "sim" if b['instalado'] else "não"
        teste = {'real': 'real', 'instavel': 'em teste / instável no Windows'}.get(b['testado'], 'simulado')
        linhas.append(f"  {b['nome']:<18}{b['grupo']:<22}{b['pip']:<29}{inst:<11}{teste}")
    linhas += ["  " + "─" * 100,
               "  Conexão: banco.conectar(\"mysql://usuario:senha@host:3306/nome\")",
               "  Senhas no .env: ADVAK_MYSQL_URL=mysql://usuario:senha@host:3306/nome",
               "  Guia completo: docs/BANCOS_DE_DADOS.md", ""]
    return "\n".join(linhas)


# ══════════════════════════════════════════════════════════════════════════════
#  .env e resolução da conexão
# ══════════════════════════════════════════════════════════════════════════════

def carregar_env():
    """Carrega .env / env_config.env da pasta atual e das pastas acima (sem sobrescrever)."""
    pasta = os.getcwd()
    for _ in range(6):
        for nome in ('.env', 'env_config.env'):
            caminho = os.path.join(pasta, nome)
            if os.path.isfile(caminho):
                try:
                    with open(caminho, encoding='utf-8-sig') as f:
                        for linha in f:
                            linha = linha.strip()
                            if not linha or linha.startswith('#') or '=' not in linha:
                                continue
                            chave, _, valor = linha.partition('=')
                            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))
                except OSError:
                    pass
        pai = os.path.dirname(pasta)
        if pai == pasta:
            break
        pasta = pai


def _params_de_url(url):
    esquema = url.split('://', 1)[0].lower()
    tipo = _tipo_por_nome(esquema)
    if tipo is None:
        raise ErroBanco(f"Banco desconhecido: '{esquema}://'. Use `advak bancos` para ver a lista.")
    if tipo in ('sqlite', 'duckdb'):
        # sqlite:///arquivo.db  |  sqlite:///:memory:  |  sqlite:///C:/pasta/arq.db
        resto = url.split('://', 1)[1]
        arquivo = unquote(resto[1:] if resto.startswith('/') else resto) or ':memory:'
        return tipo, dict(arquivo=arquivo, esquema=esquema)
    u = urlparse(url)
    banco = unquote(u.path.lstrip('/')) if u.path else ''
    params = dict(host=u.hostname or 'localhost', porta=u.port or BANCOS[tipo]['porta'],
                  usuario=unquote(u.username) if u.username else None,
                  senha=unquote(u.password) if u.password else None,
                  banco=banco or None, esquema=esquema, url=url,
                  opcoes=dict(parse_qsl(u.query)))
    return tipo, params


def resolver_conexao(destino, **kw):
    """Aceita URL ('mysql://...') ou tipo ('mysql') + dados separados. Retorna (tipo, params)."""
    carregar_env()
    destino = str(destino).strip()
    if '://' in destino:
        return _params_de_url(destino)
    tipo = _tipo_por_nome(destino)
    if tipo is None:
        nomes = ', '.join(sorted(BANCOS))
        raise ErroBanco(f"Banco desconhecido: '{destino}'. Bancos suportados: {nomes}. "
                        "Use `advak bancos` para ver a lista.")
    if tipo in ('sqlite', 'duckdb'):
        arquivo = kw.get('arquivo') or kw.get('banco') or kw.get('caminho')
        if not arquivo:
            url = os.environ.get(f'ADVAK_{tipo.upper()}_URL')
            if url:
                return _params_de_url(url)
            arquivo = ':memory:'
        return tipo, dict(arquivo=str(arquivo), esquema=tipo)
    if not kw:
        url = os.environ.get(f'ADVAK_{tipo.upper()}_URL')
        if not url and tipo == 'mssql':
            url = os.environ.get('ADVAK_SQLSERVER_URL')
        if not url and tipo == 'postgres':
            url = os.environ.get('ADVAK_POSTGRESQL_URL')
        if url:
            return _params_de_url(url)
    padrao_usuario = {'postgres': 'postgres', 'timescaledb': 'postgres', 'cockroachdb': 'root',
                      'mysql': 'root', 'mariadb': 'root', 'mssql': 'sa', 'oracle': 'system',
                      'firebird': 'SYSDBA', 'db2': 'db2inst1', 'clickhouse': 'default',
                      'neo4j': 'neo4j'}.get(tipo)
    conhecidos = {'host', 'hospedeiro', 'porta', 'port', 'usuario', 'user', 'senha', 'password',
                  'banco', 'nome', 'database'}
    extras = {k: v for k, v in kw.items() if k not in conhecidos}
    return tipo, dict(
        host=str(kw.get('host') or kw.get('hospedeiro') or 'localhost'),
        porta=int(kw.get('porta') or kw.get('port') or BANCOS[tipo]['porta'] or 0) or None,
        usuario=kw.get('usuario') or kw.get('user') or padrao_usuario,
        senha=kw.get('senha') or kw.get('password') or '',
        banco=kw.get('banco') or kw.get('nome') or kw.get('database'),
        esquema=tipo, opcoes=extras)


def eh_conexao_nova(args, kwargs):
    """Decide se banco.conectar(...) é o conector novo (True) ou o PostgreSQL legado (False)."""
    if not args or not isinstance(args[0], str):
        return False
    a = args[0].strip()
    if '://' in a:
        return True
    tipo = _tipo_por_nome(a)
    if tipo is None:
        return False
    # "postgres" sozinho continua sendo o nome do banco no modo legado
    if a.lower() == 'postgres' and not kwargs:
        return False
    return True


MODOS_BANCO = ('manual', 'automatico', 'perguntar')


def _resolver_modo(modo):
    """modo= da conexão, senão ADVAK_BANCO_MODO do .env, senão 'manual'."""
    carregar_env()
    escolhido = str(modo or os.environ.get('ADVAK_BANCO_MODO') or 'manual').strip().lower()
    if escolhido not in MODOS_BANCO:
        raise ErroBanco(f"Modo de banco desconhecido: '{escolhido}'. Use um destes: {', '.join(MODOS_BANCO)}.")
    return escolhido


def conectar(destino, **kw):
    """Cria o conector certo para a URL/tipo informado.
    modo= ('manual' padrão, 'automatico', 'perguntar') e tabelas= (mapa de tabelas do projeto) são opcionais."""
    modo = kw.pop('modo', None)
    mapa = kw.pop('tabelas', None)
    tipo, params = resolver_conexao(destino, **kw)
    classe = globals()[BANCOS[tipo]['classe']]
    c = classe(params)
    c.modo = _resolver_modo(modo)
    c.mapa = mapa
    c._abrir()
    c._ao_conectar()
    return c


def _avisar(texto):
    """Imprime um aviso. Se o terminal não codifica algum caractere (emoji no cp1252/ascii), imprime sem ele;
    nunca lança exceção por causa de um aviso."""
    try:
        print(texto, flush=True)
    except UnicodeEncodeError:
        try:
            cod = getattr(sys.stdout, 'encoding', None) or 'ascii'
            print(texto.encode(cod, 'ignore').decode(cod).lstrip(), flush=True)
        except Exception:
            pass
    except Exception:
        pass


def _perguntar_sim_nao(texto):
    """Mostra o texto e pergunta [s/N]. True/False pela resposta; None se não há entrada (não trava)."""
    _avisar(texto)
    try:
        resposta = input("Confirma? [s/N] ")
    except (EOFError, OSError):
        return None
    return resposta.strip().lower() in ('s', 'sim', 'y', 'yes')


AVISO_SEM_ENTRADA = ("⚠️  Modo 'perguntar' sem entrada para ler a resposta: tratando como 'manual' "
                     "(nada foi criado sozinho). O 'perguntar' é para programas de console.")


def _carregar_driver(tipo):
    info = BANCOS[tipo]
    try:
        return importlib.import_module(info['modulo'])
    except ImportError:
        raise ErroBanco(f"O driver do {info['nome']} não está instalado. "
                        f"Instale com:  pip install {info['pip']}")


# ══════════════════════════════════════════════════════════════════════════════
#  Base comum
# ══════════════════════════════════════════════════════════════════════════════

class ConectorBase:
    tipo = None
    sql_suportado = False
    modo = 'manual'                     # 'manual' | 'automatico' | 'perguntar'
    mapa = None                         # mapa de tabelas do projeto (tabelas=...)

    def _ao_conectar(self):             # só os conectores SQL fazem algo aqui
        pass

    def __init__(self, params):
        self.params = params
        self._conn = None

    @property
    def nome_banco(self):
        return BANCOS[self.tipo]['nome']

    def __repr__(self):
        p = self.params
        destino = p.get('arquivo') or f"{p.get('host')}:{p.get('porta')}/{p.get('banco') or ''}"
        return f"<Conexão {self.nome_banco} {destino}>"      # nunca mostra a senha

    def info(self):
        return dict(tipo=self.tipo, nome=self.nome_banco)

    def fechar(self):
        try:
            if self._conn is not None:
                self._conn.close()
        finally:
            self._conn = None
        return True

    desconectar = fechar

    def _nao_suportado(self, operacao):
        raise ErroBanco(f"'{operacao}' não se aplica ao {self.nome_banco}. "
                        "Veja os comandos disponíveis em docs/BANCOS_DE_DADOS.md")

    def listar_tabelas(self, *a, **k):   self._nao_suportado('listar_tabelas')
    def apagar_tabela(self, *a, **k):    self._nao_suportado('apagar_tabela')
    def descrever_tabela(self, *a, **k): self._nao_suportado('descrever_tabela')
    def contar(self, *a, **k):           self._nao_suportado('contar')
    def inserir_varios(self, *a, **k):   self._nao_suportado('inserir_varios')
    def buscar_por_id(self, *a, **k):    self._nao_suportado('buscar_por_id')
    def iniciar(self, *a, **k):          self._nao_suportado('iniciar (transações)')
    def confirmar(self, *a, **k):        self._nao_suportado('confirmar (transações)')
    def reverter(self, *a, **k):         self._nao_suportado('reverter (transações)')
    def sql(self, *a, **k):          self._nao_suportado('sql')
    def tabela(self, *a, **k):       self._nao_suportado('tabela')
    def criar_tabela(self, *a, **k): self._nao_suportado('criar_tabela')
    def inserir(self, *a, **k):      self._nao_suportado('inserir')
    def buscar(self, *a, **k):       self._nao_suportado('buscar')
    def atualizar(self, *a, **k):    self._nao_suportado('atualizar')
    def deletar(self, *a, **k):      self._nao_suportado('deletar')


# ══════════════════════════════════════════════════════════════════════════════
#  Bancos SQL (DB-API)
# ══════════════════════════════════════════════════════════════════════════════

_RE_ID = re.compile(r'^[^\W\d]\w*(\.[^\W\d]\w*)?$', re.UNICODE)


def _converter_valor(v):
    return float(v) if isinstance(v, Decimal) else v


class ConectorSQL(ConectorBase):
    sql_suportado = True
    marcador = '%s'
    aspas = ('"', '"')
    # tipos Advak → SQL do banco
    tipos = {
        'inteiro': 'INTEGER', 'numero': 'NUMERIC', 'decimal': 'NUMERIC(15,2)',
        'flutuante': 'FLOAT', 'grande': 'BIGINT', 'texto': 'TEXT', 'varchar': 'VARCHAR(255)',
        'char': 'CHAR(1)', 'data': 'DATE', 'hora': 'TIME',
        'datahora': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'timestamp': 'TIMESTAMP',
        'booleano': 'BOOLEAN', 'bool': 'BOOLEAN', 'json': 'TEXT', 'bytes': 'BLOB', 'ref': 'INTEGER',
    }
    autonum = 'INTEGER PRIMARY KEY'
    verdadeiro, falso = 'TRUE', 'FALSE'
    texto_indexavel = 'VARCHAR(255)'    # texto com UNIQUE/índice (MySQL/SQL Server exigem tamanho)
    suporta_notnull = True              # alguns bancos não têm NOT NULL / UNIQUE / DEFAULT
    suporta_unico = True
    suporta_padrao = True
    suporta_fk = True
    add_notnull_exige_padrao = False    # SQLite: ADD COLUMN ... NOT NULL só com DEFAULT (até em tabela vazia)
    add_unico_proibido = False          # SQLite: ADD COLUMN não aceita UNIQUE
    sem_if_not_exists = False          # Oracle, Firebird e Db2 não têm CREATE TABLE IF NOT EXISTS
    sem_if_exists = False               # ... nem DROP TABLE IF EXISTS
    minusculas = False                  # o banco devolve nomes em MAIÚSCULAS (Oracle, Firebird, Db2, Snowflake)

    def __init__(self, params):
        super().__init__(params)
        self._em_transacao = False
        self._ultimo_id = None

    # ── conexão ──────────────────────────────────────────────────────────────
    def _abrir(self):
        self._conn = self._conectar_driver()

    def _conectar_driver(self):                 # implementado por cada banco
        raise NotImplementedError

    def _garantir(self):
        if self._conn is None:
            raise ErroBanco("Conexão fechada. Use banco.conectar(...) novamente.")
        return self._conn

    # ── identificadores e marcadores ─────────────────────────────────────────
    def _id(self, nome):
        nome = str(nome)
        if not _RE_ID.match(nome):
            raise ErroBanco(f"Nome inválido para tabela/campo: '{nome}'. "
                            "Use letras, números e _ (sem espaços ou símbolos).")
        a, f = self.aspas
        return '.'.join(f'{a}{p}{f}' for p in nome.split('.'))

    def _preparar(self, consulta, params):
        """Converte %s / $1 para o marcador do banco e normaliza os parâmetros."""
        if params is None:
            params = []
        elif not isinstance(params, (list, tuple)):
            params = [params]
        params = list(params)
        if re.search(r'\$\d+', consulta):
            ordem = [int(n) for n in re.findall(r'\$(\d+)', consulta)]
            try:
                params = [params[n - 1] for n in ordem]
            except IndexError:
                raise ErroBanco("Faltam valores para os marcadores $n da consulta")
            consulta = re.sub(r'\$\d+', '%s', consulta)
        consulta = self._trocar_marcadores(consulta)
        return consulta, (tuple(_converter_param(p) for p in params) if params else None)

    def _trocar_marcadores(self, consulta):
        if self.marcador != '%s':
            consulta = consulta.replace('%s', self.marcador)
        return consulta

    def _nome_col(self, nome):
        return str(nome).lower() if self.minusculas else nome

    def _cursor(self, conn):
        return conn.cursor()

    def _confirmar_conn(self, conn):
        conn.commit()

    # ── execução ─────────────────────────────────────────────────────────────
    def _executar(self, consulta, params=None, buscar=False):
        conn = self._garantir()
        consulta, params = self._preparar(consulta, params)
        cur = self._cursor(conn)
        try:
            if params is None:
                cur.execute(consulta)
            else:
                cur.execute(consulta, params)
            if buscar:
                cols = [self._nome_col(d[0]) for d in cur.description] if cur.description else []
                return [dict(zip(cols, (_converter_valor(v) for v in row))) for row in cur.fetchall()]
            n = cur.rowcount
            self._ultimo_id = getattr(cur, 'lastrowid', None)
            if not self._em_transacao:
                self._confirmar_conn(conn)
            return n
        except ErroBanco:
            raise
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}" + self._dica_erro(str(e))) from e
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def _dica_erro(self, msg):
        """Dica em português ACRESCENTADA depois da mensagem original (SQLite/PostgreSQL); '' se não se aplica."""
        if self.tipo not in ('sqlite', 'postgres'):
            return ''
        m = msg.lower()
        if 'no such table' in m or ('relation' in m and 'does not exist' in m and 'column' not in m):
            return ('\nDica: essa tabela não existe neste banco. Confira o nome (db.listar_tabelas()) e crie com '
                    'db.tabela("nome", {...}) ou db.preparar(mapa).')
        if 'no column named' in m or 'has no column' in m or 'no such column' in m or \
                ('column' in m and 'does not exist' in m):
            return ('\nDica: essa coluna não existe nesta tabela. Adicione com '
                    'db.adicionar_coluna(tabela, campo, definicao) ou db.preparar(mapa).')
        return ''

    _SELECTS = ('SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC ', 'EXPLAIN', 'PRAGMA', 'VALUES')

    def sql(self, consulta, params=None):
        """SELECT → lista de dicts; demais comandos → linhas afetadas."""
        inicio = str(consulta).lstrip().upper()
        if inicio.startswith(self._SELECTS):
            return self._executar(consulta, params, buscar=True)
        return self._executar(consulta, params)

    # ── tabelas ──────────────────────────────────────────────────────────────
    def _coluna_auto(self, tabela, campo):
        """Retorna (sql_da_coluna, [comandos_antes])."""
        return f'{self._id(campo)} {self.autonum}', []

    def _coluna(self, tabela, campo, definicao):
        partes = str(definicao).split()
        if not partes:
            return f'{self._id(campo)} TEXT', [], None
        t = partes[0].lower()
        mods = [p.lower() for p in partes[1:]]
        antes, fk = [], None
        if t == 'autonum':
            col, antes = self._coluna_auto(tabela, campo)
            return col, antes, None
        base = self.tipos.get(t, self.tipos['texto'])
        if t == 'ref' and len(partes) > 1:
            if self.suporta_fk:
                fk = f'FOREIGN KEY ({self._id(campo)}) REFERENCES {self._id(partes[1])}(id)'
            mods = [p.lower() for p in partes[2:]]
        if base == self.tipos['texto'] and (
                (('unico' in mods or 'unique' in mods) and self.suporta_unico) or 'indice' in mods):
            base = self.texto_indexavel
        sql = [self._id(campo), base]
        # ordem aceita por todos os bancos: tipo, DEFAULT, NOT NULL, UNIQUE
        if 'padrao' in mods and self.suporta_padrao:
            i = mods.index('padrao')
            if i + 1 < len(mods):
                v = mods[i + 1]
                if v == 'verdadeiro': v = self.verdadeiro
                elif v == 'falso':    v = self.falso
                elif v == 'nulo':     v = 'NULL'
                elif not re.fullmatch(r'-?\d+(\.\d+)?', v):
                    v = "'" + v.replace("'", "''") + "'"
                if 'DEFAULT' in base:      # tipo já tem DEFAULT (ex.: datahora)
                    pass
                else:
                    sql.append(f'DEFAULT {v}')
        if ('obrigatorio' in mods or 'notnull' in mods) and self.suporta_notnull:
            sql.append('NOT NULL')
        if ('unico' in mods or 'unique' in mods) and self.suporta_unico:
            sql.append('UNIQUE')
        return ' '.join(sql), antes, fk

    def _criar_se_nao_existe(self, tabela, corpo):
        return f'CREATE TABLE IF NOT EXISTS {self._id(tabela)} (\n    {corpo}\n)'

    def tabela(self, nome, campos, sobrescrever=False):
        """db.tabela("produtos", {"id": "autonum", "nome": "texto obrigatorio"})"""
        cols, antes, fks = [], [], []
        for campo, definicao in dict(campos).items():
            col, pre, fk = self._coluna(nome, campo, definicao)
            cols.append(col)
            antes += pre
            if fk:
                fks.append(fk)
        self._cols_nomes = [str(c) for c in dict(campos)]
        if sobrescrever:
            self.apagar_tabela(nome)
        try:
            existe = self.existe_tabela(nome)
        except Exception:
            existe = False                      # não deu para olhar: segue como antes
        if existe:
            dif = self._colunas_diferentes(nome)
            if dif:
                return dif
        if self.sem_if_not_exists and existe:
            return f"ℹ️  Tabela '{nome}' já existe"
        for cmd in antes:
            self._executar(cmd)
        self._executar(self._criar_se_nao_existe(nome, ',\n    '.join(cols + fks)))
        return f"✅ Tabela '{nome}' criada"

    criar_tabela = tabela

    def _colunas_diferentes(self, nome):
        """Texto de aviso se a tabela existente tem colunas diferentes das pedidas (self._cols_nomes); senão None."""
        try:
            atuais = [str(c['coluna']) for c in self.descrever_tabela(nome)]
        except Exception:
            return None
        pedidas = {c.lower(): c for c in self._cols_nomes}
        tem = {c.lower(): c for c in atuais}
        faltam = [c for k, c in pedidas.items() if k not in tem]
        sobram = [c for k, c in tem.items() if k not in pedidas]
        if not faltam and not sobram:
            return None
        partes = []
        if faltam:
            partes.append("faltam na tabela: " + ", ".join(faltam))
        if sobram:
            partes.append("a mais na tabela: " + ", ".join(sobram))
        return (f"ℹ️  Tabela '{nome}' já existe com colunas diferentes das pedidas ({'; '.join(partes)}). "
                "Nada foi alterado.")

    # ── banco automático/manual: preparar, diferencas, adicionar_coluna ───────────────────────────
    def _so_sqlite_postgres(self):
        if self.tipo not in ('sqlite', 'postgres'):
            raise ErroBanco(f"preparar/diferencas/adicionar_coluna ainda só estão disponíveis para SQLite e "
                            f"PostgreSQL (este é {self.nome_banco}).")

    def _mapa_de(self, mapa):
        mapa = self.mapa if mapa is None else mapa
        if not mapa:
            raise ErroBanco("Nenhum mapa de tabelas informado. Use db.preparar({\"clientes\": {\"id\": \"autonum\", "
                            "\"nome\": \"texto\"}}) ou passe tabelas=mapa em banco.conectar(...).")
        return dict(mapa)

    def _nomes_colunas(self, tabela):
        return {str(r['coluna']).lower() for r in self.descrever_tabela(tabela)}

    def _recusa_coluna(self, tabela, definicao, tem_dados):
        """Motivo (texto) pelo qual a coluna NÃO pode ser adicionada a uma tabela existente; None se pode."""
        t = str(definicao).lower().split()
        if t and t[0] == 'autonum':
            return "coluna 'autonum' (chave primária) não pode ser adicionada a uma tabela que já existe."
        if ('obrigatorio' in t or 'notnull' in t) and 'padrao' not in t and (tem_dados or self.add_notnull_exige_padrao):
            quando = "a tabela já tem dados" if tem_dados else f"o {self.nome_banco} exige isso ao adicionar coluna"
            return (f"coluna obrigatória sem 'padrao' ({quando}). Acrescente um valor padrão "
                    f"(ex.: \"inteiro obrigatorio padrao 0\") ou adicione a coluna sem 'obrigatorio'.")
        if ('unico' in t or 'unique' in t) and self.add_unico_proibido:
            return f"o {self.nome_banco} não aceita 'unico' ao adicionar coluna a uma tabela que já existe."
        return None

    def _plano(self, mapa):
        """Lista do que falta: ('tabela', nome, campos) ou ('coluna', tabela, campo, definicao, motivo_recusa)."""
        plano = []
        for tabela, campos in self._mapa_de(mapa).items():
            campos = dict(campos)
            if not self.existe_tabela(tabela):
                plano.append(('tabela', tabela, campos))
                continue
            tem = self._nomes_colunas(tabela)
            tem_dados = None
            for campo, definicao in campos.items():
                if str(campo).lower() in tem:
                    continue
                if tem_dados is None:
                    tem_dados = self.contar(tabela) > 0
                plano.append(('coluna', tabela, campo, definicao, self._recusa_coluna(tabela, definicao, tem_dados)))
        return plano

    @staticmethod
    def _texto_item(item):
        if item[0] == 'tabela':
            return f"Falta a tabela '{item[1]}'"
        quase = f" (não poderá ser adicionada: {item[4]})" if item[4] else ""
        return f"Falta a coluna '{item[1]}.{item[2]}'{quase}"

    def diferencas(self, mapa=None):
        """Lista de textos com o que o mapa pede e o banco não tem ([] = em dia). Não altera nada."""
        self._so_sqlite_postgres()
        return [self._texto_item(i) for i in self._plano(mapa)]

    def adicionar_coluna(self, tabela, campo, definicao):
        self._so_sqlite_postgres()
        if not self.existe_tabela(tabela):
            raise ErroBanco(f"A tabela '{tabela}' não existe. Crie com db.tabela(\"{tabela}\", {{...}}) "
                            f"ou db.preparar(mapa).")
        if str(campo).lower() in self._nomes_colunas(tabela):
            return f"ℹ️  Coluna '{tabela}.{campo}' já existe. Nada foi alterado."
        motivo = self._recusa_coluna(tabela, definicao, self.contar(tabela) > 0)
        if motivo:
            return f"⚠️  Coluna '{tabela}.{campo}' NÃO adicionada: {motivo}"
        col, antes, fk = self._coluna(tabela, campo, definicao)
        if fk:
            col += ' ' + fk[fk.index('REFERENCES'):]
        for cmd in antes:
            self._executar(cmd)
        self._executar(f'ALTER TABLE {self._id(tabela)} ADD COLUMN {col}')
        return f"✅ Coluna '{tabela}.{campo}' adicionada"

    def preparar(self, mapa=None):
        """Cria o que o mapa pede e o banco não tem (tabelas e colunas novas). Nunca apaga nem altera tipos.
        No modo 'perguntar' mostra o que falta e pergunta antes."""
        self._so_sqlite_postgres()
        plano = self._plano(mapa)
        if not plano:
            return "ℹ️  Nada a fazer: o banco já tem tudo o que o mapa pede."
        if self.modo == 'perguntar':
            resp = _perguntar_sim_nao("O mapa pede o que ainda não existe no banco:\n  " +
                                      "\n  ".join(self._texto_item(i) for i in plano))
            if resp is None:
                _avisar(AVISO_SEM_ENTRADA)        # sem entrada: age como 'manual' (o pedido foi explícito)
            elif not resp:
                return "ℹ️  Nada foi criado (você respondeu não)."
        return self._aplicar_plano(plano)

    def _aplicar_plano(self, plano):
        linhas = []
        for item in plano:
            if item[0] == 'tabela':
                linhas.append(self.tabela(item[1], item[2]))
            else:
                linhas.append(self.adicionar_coluna(item[1], item[2], item[3]))
        return "\n".join(linhas)

    def _ao_conectar(self):
        if self.modo == 'manual' or not self.mapa:
            return
        plano = self._plano(self.mapa)
        if not plano:
            return
        if self.modo == 'perguntar':
            resp = _perguntar_sim_nao("O mapa de tabelas pede o que ainda não existe no banco:\n  " +
                                      "\n  ".join(self._texto_item(i) for i in plano))
            if resp is None:
                _avisar(AVISO_SEM_ENTRADA)
                return                                      # sem entrada: 'manual' não cria nada ao conectar
            if not resp:
                _avisar("ℹ️  Nada foi criado (você respondeu não).")
                return
        _avisar(self._aplicar_plano(plano))               # já confirmado (ou automático): sem perguntar de novo

    def apagar_tabela(self, nome, cascata=False):
        if self.sem_if_exists:
            if not self.existe_tabela(nome):
                return f"ℹ️  Tabela '{nome}' não existe"
            self._executar(f'DROP TABLE {self._id(nome)}')
        else:
            self._executar(f'DROP TABLE IF EXISTS {self._id(nome)}')
        return f"✅ Tabela '{nome}' removida"

    def _sql_listar_tabelas(self):
        return ("SELECT table_name AS nome FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name")

    def listar_tabelas(self):
        nomes = [str(r['nome']).strip() for r in self._executar(self._sql_listar_tabelas(), buscar=True)]
        return [n.lower() for n in nomes] if self.minusculas else nomes

    def existe_tabela(self, nome):
        return (str(nome).lower() if self.minusculas else str(nome)) in self.listar_tabelas()

    def _sql_colunas(self):
        return ("SELECT column_name AS coluna, data_type AS tipo, is_nullable AS aceita_nulo "
                "FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position")

    def descrever_tabela(self, nome):
        return self._executar(self._sql_colunas(), [str(nome)], buscar=True)

    # ── CRUD ─────────────────────────────────────────────────────────────────
    def inserir(self, tabela, dados):
        """Insere um registro e devolve o registro inserido (com o id, quando houver)."""
        if not dados:
            raise ErroBanco("inserir: nenhum dado informado")
        dados = dict(dados)
        cols = ', '.join(self._id(c) for c in dados)
        marc = ', '.join(['%s'] * len(dados))
        self._executar(f'INSERT INTO {self._id(tabela)} ({cols}) VALUES ({marc})', list(dados.values()))
        novo = dict(dados)
        if 'id' not in novo and getattr(self, '_ultimo_id', None):
            novo['id'] = self._ultimo_id
        return novo

    def inserir_varios(self, tabela, lista):
        if not lista:
            raise ErroBanco("inserir_varios: lista vazia")
        iniciou = not self._em_transacao
        if iniciou:
            self.iniciar()
        try:
            for item in lista:
                self.inserir(tabela, item)
        except Exception:
            if iniciou:
                self.reverter()
            raise
        if iniciou:
            self.confirmar()
        return f"✅ {len(lista)} registros inseridos"

    def buscar(self, tabela):
        return ConsultaSQL(self, tabela)

    def buscar_por_id(self, tabela, id_val):
        r = self.buscar(tabela).onde('id = %s', id_val).primeiro()
        return r or {}

    buscar_id = buscar_por_id

    def atualizar(self, tabela, dados):
        return AtualizacaoSQL(self, tabela, dados)

    def deletar(self, tabela):
        return RemocaoSQL(self, tabela)

    def contar(self, tabela, onde=None, params=None):
        q = f'SELECT COUNT(*) AS total FROM {self._id(tabela)}'
        if onde:
            q += f' WHERE {onde}'
        r = self._executar(q, params, buscar=True)
        return int(r[0]['total']) if r else 0

    def _montar_update(self, tabela, colunas, where):
        sets = ', '.join(f'{self._id(k)} = %s' for k in colunas)
        q = f'UPDATE {self._id(tabela)} SET {sets}'
        if where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in where)
        return q

    def _montar_delete(self, tabela, where):
        q = f'DELETE FROM {self._id(tabela)}'
        if where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in where)
        return q

    # ── paginação (cada dialeto pode sobrescrever) ───────────────────────────
    def _montar_select(self, cols, tabela, where, ordem, limite, offset):
        q = f'SELECT {cols} FROM {self._id(tabela)}'
        if where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in where)
        if ordem:
            q += f' ORDER BY {ordem}'
        if limite is not None:
            q += f' LIMIT {int(limite)}'
        if offset:
            q += f' OFFSET {int(offset)}'
        return q

    # ── transações ───────────────────────────────────────────────────────────
    def iniciar(self):
        self._em_transacao = True
        return "🔄 Transação iniciada"

    iniciar_transacao = iniciar

    def confirmar(self):
        try:
            self._garantir().commit()
        finally:
            self._em_transacao = False
        return "✅ Transação confirmada"

    def reverter(self):
        try:
            self._garantir().rollback()
        finally:
            self._em_transacao = False
        return "↩️  Transação revertida"


def _converter_param(v):
    """Tipos do Advak que o driver não entende (listas/dicts viram JSON)."""
    if isinstance(v, (list, dict, tuple)):
        return json.dumps(v, ensure_ascii=False)
    return v


class ConsultaSQL:
    def __init__(self, db, tabela):
        self._db, self._tabela = db, tabela
        self._where, self._params = [], []
        self._ordem, self._limite, self._offset = None, None, None
        self._cols = '*'

    def campos(self, *cols):
        self._cols = ', '.join(self._db._id(c) for c in cols)
        return self

    def onde(self, condicao, *params):
        self._where.append(str(condicao))
        for p in params:
            if isinstance(p, (list, tuple)) and len(params) == 1:
                self._params.extend(p)
            else:
                self._params.append(p)
        return self

    def ordenar(self, campo, direcao='ASC'):
        d = str(direcao).upper()
        if d not in ('ASC', 'DESC'):
            raise ErroBanco("ordenar: a direção deve ser ASC ou DESC")
        self._ordem = f'{self._db._id(campo)} {d}'
        return self

    def limite(self, n):
        self._limite = int(n)
        return self

    def pagina(self, numero, tamanho=10):
        self._limite = int(tamanho)
        self._offset = (int(numero) - 1) * int(tamanho)
        return self

    def executar(self):
        q = self._db._montar_select(self._cols, self._tabela, self._where,
                                    self._ordem, self._limite, self._offset)
        return self._db._executar(q, self._params or None, buscar=True)

    def __iter__(self):
        return iter(self.executar())

    def __len__(self):
        return len(self.executar())

    def primeiro(self):
        self._limite = 1
        r = self.executar()
        return r[0] if r else None

    def existe(self):
        return self.primeiro() is not None

    def contar(self):
        cond = ' AND '.join(f'({w})' for w in self._where) or None
        return self._db.contar(self._tabela, cond, self._params or None)


class AtualizacaoSQL:
    def __init__(self, db, tabela, dados):
        self._db, self._tabela, self._dados = db, tabela, dict(dados)
        self._where, self._params = [], []

    def onde(self, condicao, *params):
        self._where.append(str(condicao))
        self._params.extend(params)
        return self

    def executar(self):
        if not self._dados:
            raise ErroBanco("atualizar: nenhum dado informado")
        q = self._db._montar_update(self._tabela, list(self._dados), self._where)
        valores = list(self._dados.values()) + (self._params if self._where else [])
        return self._db._executar(q, valores)


class RemocaoSQL:
    def __init__(self, db, tabela):
        self._db, self._tabela = db, tabela
        self._where, self._params = [], []

    def onde(self, condicao, *params):
        self._where.append(str(condicao))
        self._params.extend(params)
        return self

    def executar(self):
        q = self._db._montar_delete(self._tabela, self._where)
        return self._db._executar(q, self._params or None)


# ── SQLite ───────────────────────────────────────────────────────────────────

class ConectorSQLite(ConectorSQL):
    tipo = 'sqlite'
    marcador = '?'
    autonum = 'INTEGER PRIMARY KEY AUTOINCREMENT'
    verdadeiro, falso = '1', '0'
    tipos = dict(ConectorSQL.tipos, json='TEXT')
    add_notnull_exige_padrao = True
    add_unico_proibido = True

    def _conectar_driver(self):
        sqlite3 = _carregar_driver('sqlite')
        arquivo = self.params['arquivo']
        if arquivo != ':memory:':
            pasta = os.path.dirname(os.path.abspath(arquivo))
            os.makedirs(pasta, exist_ok=True)
        conn = sqlite3.connect(arquivo, check_same_thread=False)
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _sql_listar_tabelas(self):
        return ("SELECT name AS nome FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name")

    def descrever_tabela(self, nome):
        r = self._executar(f'PRAGMA table_info({self._id(nome)})', buscar=True)
        return [dict(coluna=c['name'], tipo=c['type'],
                     aceita_nulo='NO' if c['notnull'] else 'YES') for c in r]

    def iniciar(self):
        self._garantir().execute('BEGIN')
        return super().iniciar()


# ── DuckDB ───────────────────────────────────────────────────────────────────
# ATENÇÃO — EM TESTE / INSTÁVEL NO WINDOWS: com o duckdb 1.5.6 (Python 3.13, Windows) um
# INSERT com parâmetro de texto executado dentro de uma thread travou, e o python.exe chegou
# a fechar com erro de memória. Como o `testar` e o servidor web do Advak rodam em threads,
# use o DuckDB só em scripts simples (thread principal) até isso ser resolvido.
# O teste automático foi desativado: testes/_desativados/bancos_duckdb.dk.desativado

class ConectorDuckDB(ConectorSQL):
    tipo = 'duckdb'
    marcador = '?'
    tipos = dict(ConectorSQL.tipos, datahora='TIMESTAMP DEFAULT now()', json='JSON', bytes='BLOB')

    def _conectar_driver(self):
        duckdb = _carregar_driver('duckdb')
        arquivo = self.params['arquivo']
        if arquivo != ':memory:':
            os.makedirs(os.path.dirname(os.path.abspath(arquivo)), exist_ok=True)
        return duckdb.connect(arquivo)

    def _coluna_auto(self, tabela, campo):
        seq = f'seq_{tabela}_{campo}'
        return (f"{self._id(campo)} INTEGER PRIMARY KEY DEFAULT nextval('{seq}')",
                [f'CREATE SEQUENCE IF NOT EXISTS {self._id(seq)} START 1'])

    def _sql_listar_tabelas(self):
        return ("SELECT table_name AS nome FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_type = 'BASE TABLE' ORDER BY table_name")

    def _sql_colunas(self):
        return ("SELECT column_name AS coluna, data_type AS tipo, is_nullable AS aceita_nulo "
                "FROM information_schema.columns WHERE table_schema = 'main' AND table_name = %s "
                "ORDER BY ordinal_position")

    def inserir(self, tabela, dados):
        if not dados:
            raise ErroBanco("inserir: nenhum dado informado")
        dados = dict(dados)
        cols = ', '.join(self._id(c) for c in dados)
        marc = ', '.join(['%s'] * len(dados))
        r = self._executar(f'INSERT INTO {self._id(tabela)} ({cols}) VALUES ({marc}) RETURNING *',
                           list(dados.values()), buscar=True)
        return r[0] if r else dict(dados)

    def _conn_thread(self):
        """Uma conexão (cursor) por thread: o DuckDB não aceita a mesma conexão em várias threads
        (o `testar` e o servidor web do Advak executam em threads separadas)."""
        import threading
        self._garantir()
        if not hasattr(self, '_local'):
            self._local = threading.local()
        if getattr(self._local, 'cur', None) is None:
            self._local.cur = self._conn.cursor()
        return self._local.cur

    def _executar(self, consulta, params=None, buscar=False):
        # DuckDB: usa o cursor da thread atual direto e está em autocommit fora de transação
        conn = self._conn_thread()
        consulta, params = self._preparar(consulta, params)
        try:
            if params is None:
                conn.execute(consulta)
            else:
                conn.execute(consulta, params)
            if buscar:
                cols = [d[0] for d in conn.description] if conn.description else []
                return [dict(zip(cols, (_converter_valor(v) for v in row))) for row in conn.fetchall()]
            try:
                linhas = conn.fetchall()
                return int(linhas[0][0]) if linhas and len(linhas[0]) == 1 \
                    and isinstance(linhas[0][0], int) else 0
            except Exception:
                return 0
        except ErroBanco:
            raise
        except Exception as e:
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}") from e

    def iniciar(self):
        self._conn_thread().execute('BEGIN TRANSACTION')
        return super().iniciar()

    def confirmar(self):
        try:
            self._conn_thread().execute('COMMIT')
        finally:
            self._em_transacao = False
        return "✅ Transação confirmada"

    def reverter(self):
        try:
            self._conn_thread().execute('ROLLBACK')
        finally:
            self._em_transacao = False
        return "↩️  Transação revertida"


# ── PostgreSQL ───────────────────────────────────────────────────────────────

class ConectorPostgres(ConectorSQL):
    tipo = 'postgres'
    autonum = 'SERIAL PRIMARY KEY'
    tipos = dict(ConectorSQL.tipos, datahora='TIMESTAMP DEFAULT NOW()', json='JSONB', bytes='BYTEA')

    def _conectar_driver(self):
        pg = _carregar_driver(self.tipo)
        p = self.params
        extra = {}
        if (p.get('opcoes') or {}).get('sslmode'):
            extra['sslmode'] = p['opcoes']['sslmode']
        banco = p['banco'] or 'postgres'
        try:
            return self._conectar_em(pg, banco, extra)
        except UnicodeDecodeError as e:
            # PostgreSQL em português (cp1252): o texto do erro não é UTF-8 e não dá para classificá-lo.
            # Banco inexistente e senha errada geram o mesmo UnicodeDecodeError; pergunta ao banco 'postgres'.
            detalhe = self._detalhe_cp1252(e)
            if self._banco_existe(pg, banco, extra) is not False:
                from advak_db import MSG_SENHA_ERRADA
                raise ErroBanco(MSG_SENHA_ERRADA + (f" Detalhe do driver: {detalhe}" if detalhe else '')) from None
            if not self._pode_criar_banco(banco):
                raise ErroBanco(self._mensagem_falha('banco_inexistente', detalhe)) from None
        except getattr(pg, 'OperationalError', ()) as e:
            tipo_falha = self._classificar_falha(str(e))
            if tipo_falha == 'outro':
                raise                                   # erro desconhecido: passa sem conversão, como antes
            if tipo_falha != 'banco_inexistente':
                raise ErroBanco(self._mensagem_falha(tipo_falha, str(e))) from None
            if not self._pode_criar_banco(banco):
                raise ErroBanco(self._mensagem_falha(tipo_falha, str(e))) from None
        # o banco não existe e o modo (ou a resposta) autoriza criar: cria pelo banco 'postgres' e reconecta
        self._criar_banco_pelo_postgres(pg, banco, extra)
        _avisar(f"✅ Banco '{banco}' criado")
        return self._conectar_em(pg, banco, extra)

    @staticmethod
    def _detalhe_cp1252(erro):
        """1ª linha do texto do servidor lida como cp1252 (só para exibir); '' se não houver."""
        bruto = erro.object if isinstance(erro.object, (bytes, bytearray)) else b''
        linhas = bytes(bruto).decode('cp1252', errors='replace').strip().splitlines()
        return linhas[0].strip() if linhas else ''

    def _banco_existe(self, pg, banco, extra):
        """True/False consultando pg_database pelo banco 'postgres'; None se não der para saber."""
        if banco == 'postgres':
            return True
        try:
            conn = self._conectar_em(pg, 'postgres', extra)
        except Exception:                               # inclui um 2º UnicodeDecodeError: não dá para distinguir
            return None
        try:
            cur = conn.cursor()
            cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (banco,))
            achou = bool(cur.fetchall())
            cur.close()
            return achou
        except Exception:
            return None
        finally:
            conn.close()

    def _conectar_em(self, pg, banco, extra):
        p = self.params
        return pg.connect(host=p['host'], port=p['porta'], user=p['usuario'],
                          password=p['senha'] or '', dbname=banco, **extra)

    @staticmethod
    def _classificar_falha(msg):
        m = msg.lower()
        if 'password authentication failed' in m or 'no password supplied' in m or 'authentication failed' in m:
            return 'senha'
        if 'does not exist' in m and 'database' in m:
            return 'banco_inexistente'
        if 'connection refused' in m or 'could not connect' in m or 'timeout' in m or 'timed out' in m \
                or 'could not translate host' in m or 'getaddrinfo' in m or 'name or service not known' in m \
                or 'is the server running' in m:
            return 'rede'
        return 'outro'

    def _mensagem_falha(self, tipo_falha, original):
        p = self.params
        host, porta, banco = p['host'], p['porta'], p['banco'] or 'postgres'
        # 1ª linha do texto original do driver, no final de toda mensagem (a do driver repete IPv6 e IPv4)
        primeira = original.strip().splitlines()[0].strip() if original.strip() else ''
        primeira = primeira.encode('utf-8', 'replace').decode('utf-8')
        detalhe = f" Detalhe do driver: {primeira}" if primeira else ""
        if tipo_falha == 'senha':
            return (f"Senha ou usuário incorretos para o PostgreSQL em {host}:{porta} (usuário '{p['usuario']}'). "
                    "Confira o usuário e a senha (ADVAK_DB_USER e ADVAK_DB_PASS no .env) e teste os mesmos dados "
                    f"no pgAdmin.{detalhe}")
        if tipo_falha == 'banco_inexistente':
            return (f"O banco '{banco}' não existe neste servidor. Crie-o com db.criar_banco('{banco}') depois de "
                    f"conectar ao banco 'postgres', ou conecte com modo=\"automatico\" para criá-lo sozinho.{detalhe}")
        if tipo_falha == 'rede':
            if porta != BANCOS['postgres']['porta']:
                return (f"Nada respondeu em {host}:{porta}. A porta está certa? O PostgreSQL costuma usar a "
                        f"{BANCOS['postgres']['porta']}. Se a porta estiver certa, o servidor pode estar "
                        f"desligado.{detalhe}")
            return (f"Não consegui falar com o PostgreSQL em {host}:{porta}. Ele está instalado e ligado? "
                    "No Windows, procure o serviço 'postgresql-x64-NN' em Serviços (services.msc). Se o servidor "
                    f"está em outro computador, confira o endereço ({host}) e o firewall.{detalhe}")
        return f"Não foi possível conectar ao PostgreSQL em {host}:{porta}.{detalhe}"

    def _pode_criar_banco(self, banco):
        if self.modo == 'automatico':
            return True
        if self.modo == 'perguntar':
            resp = _perguntar_sim_nao(f"O banco '{banco}' não existe neste servidor e o mapa de tabelas precisa dele.")
            if resp is None:
                _avisar(AVISO_SEM_ENTRADA)
            return bool(resp)
        return False

    def _criar_banco_pelo_postgres(self, pg, banco, extra):
        try:
            conn = self._conectar_em(pg, 'postgres', extra)
            try:
                conn.autocommit = True
                cur = conn.cursor()
                cur.execute(f'CREATE DATABASE {self._id(banco)}')
                cur.close()
            finally:
                conn.close()
        except Exception as e:
            raise ErroBanco(f"Não consegui criar o banco '{banco}': {str(e).strip().splitlines()[0] if str(e).strip() else e}") from None

    def criar_banco(self, nome):
        """db.criar_banco("loja"): cria o banco no servidor se ainda não existir (nunca apaga)."""
        if not nome or not str(nome).strip():
            raise ErroBanco("criar_banco: informe o nome do banco.")
        if self._executar('SELECT 1 AS x FROM pg_database WHERE datname = %s', [str(nome)], buscar=True):
            return f"ℹ️  Banco '{nome}' já existe"
        conn = self._garantir()
        conn.autocommit = True
        try:
            self._executar(f'CREATE DATABASE {self._id(nome)}')
        finally:
            conn.autocommit = False
        return f"✅ Banco '{nome}' criado"

    def inserir(self, tabela, dados):
        if not dados:
            raise ErroBanco("inserir: nenhum dado informado")
        dados = dict(dados)
        cols = ', '.join(self._id(c) for c in dados)
        marc = ', '.join(['%s'] * len(dados))
        r = self._executar(f'INSERT INTO {self._id(tabela)} ({cols}) VALUES ({marc}) RETURNING *',
                           list(dados.values()), buscar=True)
        if not self._em_transacao:
            self._garantir().commit()
        return r[0] if r else dict(dados)

    def apagar_tabela(self, nome, cascata=False):
        self._executar(f'DROP TABLE IF EXISTS {self._id(nome)}' + (' CASCADE' if cascata else ''))
        return f"✅ Tabela '{nome}' removida"

    def _sql_colunas(self):
        return ("SELECT column_name AS coluna, data_type AS tipo, is_nullable AS aceita_nulo "
                "FROM information_schema.columns WHERE table_schema = 'public' AND table_name = %s "
                "ORDER BY ordinal_position")


# ── MySQL / MariaDB ──────────────────────────────────────────────────────────

class ConectorMySQL(ConectorSQL):
    tipo = 'mysql'
    aspas = ('`', '`')
    autonum = 'INT AUTO_INCREMENT PRIMARY KEY'
    tipos = dict(ConectorSQL.tipos, texto='TEXT', numero='DECIMAL(20,6)', decimal='DECIMAL(15,2)',
                 datahora='DATETIME DEFAULT CURRENT_TIMESTAMP', json='JSON', bytes='BLOB',
                 booleano='TINYINT(1)', bool='TINYINT(1)', flutuante='DOUBLE')
    verdadeiro, falso = '1', '0'

    def _conectar_driver(self):
        pymysql = _carregar_driver(self.tipo)
        p = self.params
        return pymysql.connect(host=p['host'], port=p['porta'], user=p['usuario'],
                               password=p['senha'] or '', database=p['banco'],
                               charset='utf8mb4', autocommit=False)

    def _sql_listar_tabelas(self):
        return ("SELECT table_name AS nome FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE' ORDER BY table_name")

    def _sql_colunas(self):
        return ("SELECT column_name AS coluna, data_type AS tipo, is_nullable AS aceita_nulo "
                "FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = %s "
                "ORDER BY ordinal_position")


class ConectorMariaDB(ConectorMySQL):
    tipo = 'mariadb'


# ── SQL Server ───────────────────────────────────────────────────────────────

class ConectorMSSQL(ConectorSQL):
    tipo = 'mssql'
    aspas = ('[', ']')
    autonum = 'INT IDENTITY(1,1) PRIMARY KEY'
    verdadeiro, falso = '1', '0'
    texto_indexavel = 'NVARCHAR(255)'
    tipos = dict(ConectorSQL.tipos, texto='NVARCHAR(MAX)', varchar='NVARCHAR(255)', char='NCHAR(1)',
                 datahora='DATETIME2 DEFAULT SYSDATETIME()', timestamp='DATETIME2',
                 booleano='BIT', bool='BIT', json='NVARCHAR(MAX)', bytes='VARBINARY(MAX)',
                 flutuante='FLOAT', numero='DECIMAL(20,6)', decimal='DECIMAL(15,2)')

    def _conectar_driver(self):
        pymssql = _carregar_driver('mssql')
        p = self.params
        return pymssql.connect(server=p['host'], port=str(p['porta']), user=p['usuario'],
                               password=p['senha'] or '', database=p['banco'] or 'master',
                               charset='UTF-8')

    def _criar_se_nao_existe(self, tabela, corpo):
        nome = str(tabela).replace("'", "''")
        return (f"IF OBJECT_ID(N'{nome}', N'U') IS NULL\n"
                f"CREATE TABLE {self._id(tabela)} (\n    {corpo}\n)")

    def apagar_tabela(self, nome, cascata=False):
        n = str(nome).replace("'", "''")
        self._executar(f"IF OBJECT_ID(N'{n}', N'U') IS NOT NULL DROP TABLE {self._id(nome)}")
        return f"✅ Tabela '{nome}' removida"

    def _sql_listar_tabelas(self):
        return ("SELECT table_name AS nome FROM information_schema.tables "
                "WHERE table_type = 'BASE TABLE' ORDER BY table_name")

    def inserir(self, tabela, dados):
        if not dados:
            raise ErroBanco("inserir: nenhum dado informado")
        dados = dict(dados)
        cols = ', '.join(self._id(c) for c in dados)
        marc = ', '.join(['%s'] * len(dados))
        r = self._executar(f'INSERT INTO {self._id(tabela)} ({cols}) OUTPUT INSERTED.* VALUES ({marc})',
                           list(dados.values()), buscar=True)
        if not self._em_transacao:
            self._garantir().commit()
        return r[0] if r else dict(dados)

    def _montar_select(self, cols, tabela, where, ordem, limite, offset):
        base = f'FROM {self._id(tabela)}'
        if where:
            base += ' WHERE ' + ' AND '.join(f'({w})' for w in where)
        if offset:
            # OFFSET/FETCH exige ORDER BY
            q = f'SELECT {cols} {base} ORDER BY {ordem or "(SELECT NULL)"} OFFSET {int(offset)} ROWS'
            if limite is not None:
                q += f' FETCH NEXT {int(limite)} ROWS ONLY'
            return q
        topo = f'TOP {int(limite)} ' if limite is not None else ''
        q = f'SELECT {topo}{cols} {base}'
        if ordem:
            q += f' ORDER BY {ordem}'
        return q


# ── CockroachDB / TimescaleDB (falam o protocolo do PostgreSQL) ──────────────

class ConectorCockroach(ConectorPostgres):
    """CockroachDB: mesmo protocolo do PostgreSQL (porta 26257). Use ?sslmode=require na URL."""
    tipo = 'cockroachdb'


class ConectorTimescale(ConectorPostgres):
    """TimescaleDB: PostgreSQL com extensão de séries temporais."""
    tipo = 'timescaledb'

    def criar_hipertabela(self, tabela, coluna_tempo='tempo', intervalo=None):
        """db.criar_hipertabela("sensores", "tempo")  — transforma a tabela em hypertable."""
        self._executar('CREATE EXTENSION IF NOT EXISTS timescaledb')
        q = f"SELECT create_hypertable('{self._id(tabela).replace(chr(34), '')}', '{self._id(coluna_tempo).replace(chr(34), '')}', if_not_exists => TRUE)"
        self._executar(q, buscar=True)
        return f"✅ Tabela '{tabela}' agora é uma hipertabela (coluna de tempo: {coluna_tempo})"


# ── Bancos que guardam nomes em MAIÚSCULAS: Oracle, Firebird, Db2 ────────────

class ConectorMaiusculas(ConectorSQL):
    """Nomes sem aspas (o banco os guarda em MAIÚSCULAS) e resultados devolvidos em minúsculas."""
    aspas = ('', '')
    minusculas = True
    sem_if_not_exists = True
    sem_if_exists = True

    def inserir(self, tabela, dados):
        # sem RETURNING portátil: devolve os dados enviados (use buscar para ler o id gerado)
        if not dados:
            raise ErroBanco("inserir: nenhum dado informado")
        dados = dict(dados)
        cols = ', '.join(self._id(c) for c in dados)
        marc = ', '.join(['%s'] * len(dados))
        self._executar(f'INSERT INTO {self._id(tabela)} ({cols}) VALUES ({marc})', list(dados.values()))
        return dict(dados)


class ConectorOracle(ConectorMaiusculas):
    tipo = 'oracle'
    marcador = ':n'
    autonum = 'NUMBER GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY'
    verdadeiro, falso = '1', '0'
    texto_indexavel = 'VARCHAR2(255)'
    tipos = dict(ConectorSQL.tipos, inteiro='NUMBER(10)', numero='NUMBER', decimal='NUMBER(15,2)',
                 flutuante='BINARY_DOUBLE', grande='NUMBER(19)', texto='CLOB', varchar='VARCHAR2(255)',
                 hora='VARCHAR2(8)', datahora='TIMESTAMP DEFAULT SYSTIMESTAMP',
                 booleano='NUMBER(1)', bool='NUMBER(1)', json='CLOB', bytes='BLOB', ref='NUMBER(10)')

    def _conectar_driver(self):
        oracledb = _carregar_driver('oracle')
        p = self.params
        try:
            oracledb.defaults.fetch_lobs = False          # CLOB/BLOB vêm como texto/bytes
        except Exception:
            pass
        servico = p.get('banco') or (p.get('opcoes') or {}).get('servico') or 'XEPDB1'
        return oracledb.connect(user=p['usuario'], password=p['senha'] or '',
                                dsn=f"{p['host']}:{p['porta']}/{servico}")

    def _trocar_marcadores(self, consulta):
        n = [0]

        def num(_):
            n[0] += 1
            return f':{n[0]}'
        return re.sub(r'%s', num, consulta)

    def _sql_listar_tabelas(self):
        return "SELECT table_name AS nome FROM user_tables ORDER BY table_name"

    def _sql_colunas(self):
        return ("SELECT column_name AS coluna, data_type AS tipo, "
                "CASE nullable WHEN 'Y' THEN 'YES' ELSE 'NO' END AS aceita_nulo "
                "FROM user_tab_columns WHERE table_name = UPPER(%s) ORDER BY column_id")

    def apagar_tabela(self, nome, cascata=False):
        if not self.existe_tabela(nome):
            return f"ℹ️  Tabela '{nome}' não existe"
        self._executar(f'DROP TABLE {self._id(nome)}' + (' CASCADE CONSTRAINTS' if cascata else ''))
        return f"✅ Tabela '{nome}' removida"

    def _montar_select(self, cols, tabela, where, ordem, limite, offset):
        q = f'SELECT {cols} FROM {self._id(tabela)}'
        if where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in where)
        if ordem:
            q += f' ORDER BY {ordem}'
        if offset:
            q += f' OFFSET {int(offset)} ROWS'
        if limite is not None:
            q += f' FETCH NEXT {int(limite)} ROWS ONLY'
        return q


class ConectorFirebird(ConectorMaiusculas):
    tipo = 'firebird'
    marcador = '?'
    autonum = 'INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY'
    tipos = dict(ConectorSQL.tipos, numero='NUMERIC(18,6)', decimal='DECIMAL(15,2)',
                 flutuante='DOUBLE PRECISION', texto='BLOB SUB_TYPE TEXT', json='BLOB SUB_TYPE TEXT',
                 bytes='BLOB')

    def _conectar_driver(self):
        fb = _carregar_driver('firebird')
        p = self.params
        banco = p.get('banco') or ''
        if p.get('host') and p['host'] not in ('', 'embedded'):
            banco = f"{p['host']}/{p['porta']}:{banco}"
        return fb.connect(banco, user=p['usuario'], password=p['senha'] or '', charset='UTF8')

    def _sql_listar_tabelas(self):
        return ("SELECT TRIM(rdb$relation_name) AS nome FROM rdb$relations "
                "WHERE COALESCE(rdb$system_flag, 0) = 0 AND rdb$view_blr IS NULL ORDER BY 1")

    def _sql_colunas(self):
        return ("SELECT TRIM(rf.rdb$field_name) AS coluna, CAST(f.rdb$field_type AS VARCHAR(10)) AS tipo, "
                "CASE WHEN rf.rdb$null_flag = 1 THEN 'NO' ELSE 'YES' END AS aceita_nulo "
                "FROM rdb$relation_fields rf JOIN rdb$fields f ON f.rdb$field_name = rf.rdb$field_source "
                "WHERE rf.rdb$relation_name = UPPER(%s) ORDER BY rf.rdb$field_position")

    def _montar_select(self, cols, tabela, where, ordem, limite, offset):
        topo = ''
        if limite is not None:
            topo += f'FIRST {int(limite)} '
        if offset:
            topo += f'SKIP {int(offset)} '
        q = f'SELECT {topo}{cols} FROM {self._id(tabela)}'
        if where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in where)
        if ordem:
            q += f' ORDER BY {ordem}'
        return q


class ConectorDb2(ConectorMaiusculas):
    tipo = 'db2'
    marcador = '?'
    autonum = 'INTEGER NOT NULL GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY'
    verdadeiro, falso = 'TRUE', 'FALSE'
    tipos = dict(ConectorSQL.tipos, numero='DECIMAL(20,6)', decimal='DECIMAL(15,2)', flutuante='DOUBLE',
                 texto='VARCHAR(2000)', datahora='TIMESTAMP DEFAULT CURRENT TIMESTAMP',
                 json='CLOB', bytes='BLOB')

    def _conectar_driver(self):
        dbi = _carregar_driver('db2')
        p = self.params
        dsn = (f"DATABASE={p.get('banco') or ''};HOSTNAME={p['host']};PORT={p['porta']};"
               f"PROTOCOL=TCPIP;UID={p['usuario']};PWD={p['senha'] or ''};")
        return dbi.connect(dsn, '', '')

    def _sql_listar_tabelas(self):
        return ("SELECT tabname AS nome FROM syscat.tables "
                "WHERE tabschema = CURRENT SCHEMA AND type = 'T' ORDER BY tabname")

    def _sql_colunas(self):
        return ("SELECT colname AS coluna, typename AS tipo, "
                "CASE nulls WHEN 'Y' THEN 'YES' ELSE 'NO' END AS aceita_nulo "
                "FROM syscat.columns WHERE tabschema = CURRENT SCHEMA AND tabname = UPPER(%s) "
                "ORDER BY colno")

    def _montar_select(self, cols, tabela, where, ordem, limite, offset):
        q = f'SELECT {cols} FROM {self._id(tabela)}'
        if where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in where)
        if ordem:
            q += f' ORDER BY {ordem}'
        if offset:
            q += f' OFFSET {int(offset)} ROWS'
        if limite is not None:
            q += f' FETCH FIRST {int(limite)} ROWS ONLY'
        return q


# ══════════════════════════════════════════════════════════════════════════════
#  MongoDB (documentos)
# ══════════════════════════════════════════════════════════════════════════════

_OPS_MONGO = {'=': None, '==': None, '!=': '$ne', '<>': '$ne', '>': '$gt', '>=': '$gte',
              '<': '$lt', '<=': '$lte'}
_RE_COND = re.compile(r'^\s*([\w\.]+)\s*(==|=|!=|<>|>=|<=|>|<)\s*(%s|\$\d+)\s*$')


def cond_para_filtro(condicao, params):
    """Converte 'preco > %s AND ativo = %s' (+ valores) em filtro MongoDB."""
    if isinstance(condicao, dict):
        return dict(condicao)
    params = list(params)
    filtro, seq = {}, 0
    for parte in re.split(r'\s+AND\s+', str(condicao), flags=re.IGNORECASE):
        m = _RE_COND.match(parte)
        if not m:
            raise ErroBanco(f"MongoDB: condição não suportada: '{parte.strip()}'. Use campo = %s, "
                            "campo > %s, ... ligados por AND, ou passe um dicionário de filtro.")
        campo, op, marc = m.groups()
        try:
            if marc.startswith('$'):
                valor = params[int(marc[1:]) - 1]
            else:
                valor = params[seq]
                seq += 1
        except IndexError:
            raise ErroBanco("MongoDB: faltam valores para os marcadores da condição")
        mongo_op = _OPS_MONGO[op]
        if mongo_op is None:
            filtro[campo] = valor
        else:
            filtro.setdefault(campo, {})
            if not isinstance(filtro[campo], dict):
                filtro[campo] = {'$eq': filtro[campo]}
            filtro[campo][mongo_op] = valor
    return filtro


class ConectorMongoDB(ConectorBase):
    tipo = 'mongodb'

    def _abrir(self):
        pymongo = _carregar_driver('mongodb')
        p = self.params
        url = p.get('url') or f"mongodb://{p['host']}:{p['porta']}"
        if not p.get('url') and p.get('usuario'):
            from urllib.parse import quote_plus
            url = (f"mongodb://{quote_plus(p['usuario'])}:{quote_plus(p['senha'] or '')}"
                   f"@{p['host']}:{p['porta']}")
        self._client = pymongo.MongoClient(url, serverSelectionTimeoutMS=5000)
        self._conn = self._client
        self._db = self._client[p.get('banco') or 'advak']
        self._pymongo = pymongo

    def fechar(self):
        try:
            self._client.close()
        finally:
            self._conn = None
        return True

    desconectar = fechar

    # ids ↔ texto
    def _oid(self, v):
        try:
            from bson import ObjectId
            if isinstance(v, str) and re.fullmatch(r'[0-9a-fA-F]{24}', v):
                return ObjectId(v)
        except ImportError:
            pass
        return v

    def _filtro(self, filtro):
        f = dict(filtro)
        if 'id' in f:
            f['_id'] = self._oid(f.pop('id'))
        elif '_id' in f:
            f['_id'] = self._oid(f['_id'])
        return f

    @staticmethod
    def _doc_saida(doc):
        d = dict(doc)
        if '_id' in d:
            d['id'] = str(d.pop('_id'))
        return d

    # coleções
    def tabela(self, nome, campos=None, sobrescrever=False):
        """No MongoDB a coleção é criada sozinha; os campos são apenas ignorados."""
        if sobrescrever:
            self._db.drop_collection(nome)
        if nome not in self._db.list_collection_names():
            self._db.create_collection(nome)
        return f"✅ Coleção '{nome}' pronta"

    criar_tabela = tabela

    def apagar_tabela(self, nome, cascata=False):
        self._db.drop_collection(nome)
        return f"✅ Coleção '{nome}' removida"

    def listar_tabelas(self):
        return sorted(self._db.list_collection_names())

    listar_colecoes = listar_tabelas

    def inserir(self, colecao, dados):
        doc = dict(dados)
        r = self._db[colecao].insert_one(doc)
        doc['id'] = str(r.inserted_id)
        doc.pop('_id', None)
        return doc

    def inserir_varios(self, colecao, lista):
        docs = [dict(d) for d in lista]
        if not docs:
            raise ErroBanco("inserir_varios: lista vazia")
        self._db[colecao].insert_many(docs)
        return f"✅ {len(docs)} registros inseridos"

    def buscar(self, colecao):
        return ConsultaMongo(self, colecao)

    def buscar_por_id(self, colecao, id_val):
        d = self._db[colecao].find_one({'_id': self._oid(id_val)})
        return self._doc_saida(d) if d else {}

    buscar_id = buscar_por_id

    def atualizar(self, colecao, dados):
        return AtualizacaoMongo(self, colecao, dados)

    def deletar(self, colecao):
        return RemocaoMongo(self, colecao)

    def contar(self, colecao, onde=None, params=None):
        filtro = self._filtro(cond_para_filtro(onde, params or [])) if onde else {}
        return self._db[colecao].count_documents(filtro)

    def comando(self, comando):
        """Executa um comando nativo do MongoDB: db.comando({"ping": 1})"""
        return self._db.command(comando)

    def sql(self, *a, **k):
        raise ErroBanco("O MongoDB não usa SQL. Use inserir, buscar, atualizar, deletar "
                        "ou db.comando({...}).")


class ConsultaMongo:
    def __init__(self, db, colecao):
        self._db, self._col = db, colecao
        self._filtro, self._campos = {}, None
        self._ordem, self._limite, self._pular = None, None, 0

    def campos(self, *cols):
        self._campos = {c: 1 for c in cols}
        return self

    def onde(self, condicao, *params):
        if len(params) == 1 and isinstance(params[0], (list, tuple)):
            params = tuple(params[0])
        self._filtro.update(self._db._filtro(cond_para_filtro(condicao, params)))
        return self

    def ordenar(self, campo, direcao='ASC'):
        self._ordem = [(campo, -1 if str(direcao).upper() == 'DESC' else 1)]
        return self

    def limite(self, n):
        self._limite = int(n)
        return self

    def pagina(self, numero, tamanho=10):
        self._limite = int(tamanho)
        self._pular = (int(numero) - 1) * int(tamanho)
        return self

    def executar(self):
        cur = self._db._db[self._col].find(self._filtro, self._campos)
        if self._ordem:
            cur = cur.sort(self._ordem)
        if self._pular:
            cur = cur.skip(self._pular)
        if self._limite is not None:
            cur = cur.limit(self._limite)
        return [self._db._doc_saida(d) for d in cur]

    def __iter__(self):
        return iter(self.executar())

    def __len__(self):
        return len(self.executar())

    def primeiro(self):
        self._limite = 1
        r = self.executar()
        return r[0] if r else None

    def existe(self):
        return self.primeiro() is not None

    def contar(self):
        return self._db._db[self._col].count_documents(self._filtro)


class AtualizacaoMongo:
    def __init__(self, db, colecao, dados):
        self._db, self._col, self._dados = db, colecao, dict(dados)
        self._filtro = {}

    def onde(self, condicao, *params):
        if len(params) == 1 and isinstance(params[0], (list, tuple)):
            params = tuple(params[0])
        self._filtro.update(self._db._filtro(cond_para_filtro(condicao, params)))
        return self

    def executar(self):
        r = self._db._db[self._col].update_many(self._filtro, {'$set': self._dados})
        return r.modified_count


class RemocaoMongo:
    def __init__(self, db, colecao):
        self._db, self._col, self._filtro = db, colecao, {}

    def onde(self, condicao, *params):
        if len(params) == 1 and isinstance(params[0], (list, tuple)):
            params = tuple(params[0])
        self._filtro.update(self._db._filtro(cond_para_filtro(condicao, params)))
        return self

    def executar(self):
        return self._db._db[self._col].delete_many(self._filtro).deleted_count


# ══════════════════════════════════════════════════════════════════════════════
#  Redis (chave-valor)
# ══════════════════════════════════════════════════════════════════════════════

class ConectorRedis(ConectorBase):
    tipo = 'redis'

    def _abrir(self):
        redis = _carregar_driver('redis')
        p = self.params
        if p.get('url'):
            self._r = redis.Redis.from_url(p['url'], decode_responses=True)
        else:
            self._r = redis.Redis(host=p['host'], port=p['porta'], password=p['senha'] or None,
                                  db=int(p['banco'] or 0), decode_responses=True)
        self._conn = self._r

    def fechar(self):
        try:
            self._r.close()
        finally:
            self._conn = None
        return True

    desconectar = fechar

    @staticmethod
    def _serializar(v):
        if isinstance(v, (dict, list, tuple)):
            return json.dumps(v, ensure_ascii=False)
        if isinstance(v, bool):
            return 'verdadeiro' if v else 'falso'
        return v

    def testar(self):
        return bool(self._r.ping())

    def definir(self, chave, valor, expira=None):
        """db.definir("sessao:1", {"nome": "Ana"}, expira=60)   # expira em segundos"""
        self._r.set(chave, self._serializar(valor), ex=int(expira) if expira else None)
        return True

    def obter(self, chave, padrao=None):
        v = self._r.get(chave)
        return padrao if v is None else v

    def obter_json(self, chave, padrao=None):
        v = self._r.get(chave)
        return padrao if v is None else json.loads(v)

    def excluir(self, *chaves):
        return self._r.delete(*chaves)

    remover = excluir

    def existe(self, chave):
        return bool(self._r.exists(chave))

    def chaves(self, padrao='*'):
        return sorted(self._r.keys(padrao))

    def expirar(self, chave, segundos):
        return bool(self._r.expire(chave, int(segundos)))

    def ttl(self, chave):
        return self._r.ttl(chave)

    def incrementar(self, chave, quantidade=1):
        return self._r.incrby(chave, int(quantidade))

    def decrementar(self, chave, quantidade=1):
        return self._r.decrby(chave, int(quantidade))

    def lista_adicionar(self, chave, *valores):
        return self._r.rpush(chave, *[self._serializar(v) for v in valores])

    def lista_ler(self, chave, inicio=0, fim=-1):
        return self._r.lrange(chave, int(inicio), int(fim))

    def conjunto_adicionar(self, chave, *valores):
        return self._r.sadd(chave, *[self._serializar(v) for v in valores])

    def conjunto_ler(self, chave):
        return sorted(self._r.smembers(chave))

    def hash_definir(self, chave, mapa):
        return self._r.hset(chave, mapping={k: self._serializar(v) for k, v in dict(mapa).items()})

    def hash_ler(self, chave):
        return self._r.hgetall(chave)

    def publicar(self, canal, mensagem):
        return self._r.publish(canal, self._serializar(mensagem))

    def limpar(self):
        """Apaga TODAS as chaves do banco Redis atual."""
        self._r.flushdb()
        return True


# ══════════════════════════════════════════════════════════════════════════════
#  Grupo 2, lote B — analíticos e colunar (SQL)
# ══════════════════════════════════════════════════════════════════════════════

class ConectorClickHouse(ConectorSQL):
    """ClickHouse (clickhouse-connect, porta HTTP 8123). Sem transações; UPDATE/DELETE são
    'mutações' assíncronas (ALTER TABLE ... UPDATE/DELETE) e não informam linhas afetadas."""
    tipo = 'clickhouse'
    suporta_notnull = False        # colunas já são NOT NULL por padrão
    suporta_unico = False
    suporta_fk = False
    autonum = 'UUID DEFAULT generateUUIDv4()'
    verdadeiro, falso = 'true', 'false'
    tipos = dict(ConectorSQL.tipos, inteiro='Int32', numero='Float64', decimal='Decimal(15,2)',
                 flutuante='Float64', grande='Int64', texto='String', varchar='String',
                 char='FixedString(1)', hora='String', datahora='DateTime DEFAULT now()',
                 timestamp='DateTime', booleano='Bool', bool='Bool', json='String', bytes='String',
                 ref='Int32')

    def _conectar_driver(self):
        cc = _carregar_driver('clickhouse')
        p = self.params
        op = p.get('opcoes') or {}
        seguro = str(op.get('secure', op.get('seguro', ''))).lower() in ('1', 'true', 'sim')
        return cc.get_client(host=p['host'], port=p['porta'], username=p['usuario'] or 'default',
                             password=p['senha'] or '', database=p.get('banco') or 'default',
                             secure=seguro)

    def fechar(self):
        try:
            if self._conn is not None:
                self._conn.close()
        finally:
            self._conn = None
        return True

    def _executar(self, consulta, params=None, buscar=False):
        cli = self._garantir()
        consulta, params = self._preparar(consulta, params)
        parametros = list(params) if params else None
        try:
            if buscar:
                r = cli.query(consulta, parameters=parametros)
                cols = [self._nome_col(c) for c in r.column_names]
                return [dict(zip(cols, (_converter_valor(v) for v in row))) for row in r.result_rows]
            cli.command(consulta, parameters=parametros)
            return 0
        except Exception as e:
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}") from e

    def inserir(self, tabela, dados):
        if not dados:
            raise ErroBanco("inserir: nenhum dado informado")
        dados = dict(dados)
        try:
            self._garantir().insert(str(tabela), [list(dados.values())],
                                    column_names=[self._id(c).strip('"') for c in dados])
        except Exception as e:
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}") from e
        return dict(dados)

    def _criar_se_nao_existe(self, tabela, corpo):
        chave = self._id(self._cols_nomes[0]) if getattr(self, '_cols_nomes', None) else 'tuple()'
        return (f'CREATE TABLE IF NOT EXISTS {self._id(tabela)} (\n    {corpo}\n) '
                f'ENGINE = MergeTree ORDER BY {chave}')

    def _montar_update(self, tabela, colunas, where):
        sets = ', '.join(f'{self._id(k)} = %s' for k in colunas)
        cond = ' AND '.join(f'({w})' for w in where) if where else '1'
        return f'ALTER TABLE {self._id(tabela)} UPDATE {sets} WHERE {cond}'

    def _montar_delete(self, tabela, where):
        cond = ' AND '.join(f'({w})' for w in where) if where else '1'
        return f'ALTER TABLE {self._id(tabela)} DELETE WHERE {cond}'

    def _sql_listar_tabelas(self):
        return "SELECT name AS nome FROM system.tables WHERE database = currentDatabase() ORDER BY name"

    def _sql_colunas(self):
        return ("SELECT name AS coluna, type AS tipo, if(startsWith(type, 'Nullable'), 'YES', 'NO') "
                "AS aceita_nulo FROM system.columns WHERE database = currentDatabase() AND table = %s "
                "ORDER BY position")

    def iniciar(self):
        raise ErroBanco("O ClickHouse não tem transações.")

    confirmar = reverter = iniciar_transacao = iniciar


class ConectorSnowflake(ConectorMaiusculas):
    """Snowflake: URL snowflake://usuario:senha@CONTA/BANCO/ESQUEMA?warehouse=WH&role=PAPEL"""
    tipo = 'snowflake'
    sem_if_not_exists = False
    sem_if_exists = False
    suporta_fk = False
    autonum = 'INTEGER AUTOINCREMENT PRIMARY KEY'
    tipos = dict(ConectorSQL.tipos, numero='NUMBER(20,6)', decimal='NUMBER(15,2)', flutuante='FLOAT',
                 texto='VARCHAR', datahora='TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()',
                 timestamp='TIMESTAMP_NTZ', json='VARCHAR', bytes='BINARY')

    def _conectar_driver(self):
        sf = _carregar_driver('snowflake')
        p = self.params
        op = p.get('opcoes') or {}
        banco, _, esquema = str(p.get('banco') or '').partition('/')
        kw = dict(account=op.get('conta') or p['host'], user=p['usuario'], password=p['senha'] or '')
        if banco:
            kw['database'] = banco
        if esquema or op.get('esquema_nome'):
            kw['schema'] = esquema or op['esquema_nome']
        for chave in ('warehouse', 'role'):
            if op.get(chave):
                kw[chave] = op[chave]
        return sf.connect(**kw)

    def _sql_listar_tabelas(self):
        return ("SELECT table_name AS nome FROM information_schema.tables "
                "WHERE table_schema = CURRENT_SCHEMA() AND table_type = 'BASE TABLE' ORDER BY table_name")

    def _sql_colunas(self):
        return ("SELECT column_name AS coluna, data_type AS tipo, is_nullable AS aceita_nulo "
                "FROM information_schema.columns WHERE table_schema = CURRENT_SCHEMA() "
                "AND table_name = UPPER(%s) ORDER BY ordinal_position")

    def _comando(self, texto):
        cur = self._garantir().cursor()
        try:
            cur.execute(texto)
        finally:
            cur.close()

    def iniciar(self):
        self._comando('BEGIN')
        return super().iniciar()

    def confirmar(self):
        try:
            self._comando('COMMIT')
        finally:
            self._em_transacao = False
        return "✅ Transação confirmada"

    def reverter(self):
        try:
            self._comando('ROLLBACK')
        finally:
            self._em_transacao = False
        return "↩️  Transação revertida"


class ConectorBigQuery(ConectorSQL):
    """Google BigQuery: bigquery://PROJETO/DATASET?credenciais=chave.json
    (sem credenciais, usa GOOGLE_APPLICATION_CREDENTIALS). DML exige faturamento ativo."""
    tipo = 'bigquery'
    aspas = ('`', '`')
    suporta_unico = False
    suporta_fk = False
    autonum = 'STRING DEFAULT GENERATE_UUID()'
    tipos = dict(ConectorSQL.tipos, inteiro='INT64', numero='NUMERIC', decimal='NUMERIC',
                 flutuante='FLOAT64', grande='INT64', texto='STRING', varchar='STRING', char='STRING',
                 datahora='TIMESTAMP DEFAULT CURRENT_TIMESTAMP()', booleano='BOOL', bool='BOOL',
                 json='JSON', bytes='BYTES', ref='INT64')

    def _conectar_driver(self):
        bq = _carregar_driver('bigquery')
        p = self.params
        self._bq = bq
        self._projeto = p.get('host')
        self._dataset = p.get('banco')
        cred = (p.get('opcoes') or {}).get('credenciais')
        if cred:
            return bq.Client.from_service_account_json(cred, project=self._projeto)
        return bq.Client(project=self._projeto)

    def fechar(self):
        try:
            if self._conn is not None:
                self._conn.close()
        finally:
            self._conn = None
        return True

    def _param(self, v):
        import datetime
        bq = self._bq
        if isinstance(v, bool):
            return bq.ScalarQueryParameter(None, 'BOOL', v)
        if isinstance(v, int):
            return bq.ScalarQueryParameter(None, 'INT64', v)
        if isinstance(v, float):
            return bq.ScalarQueryParameter(None, 'FLOAT64', v)
        if isinstance(v, Decimal):
            return bq.ScalarQueryParameter(None, 'NUMERIC', v)
        if isinstance(v, datetime.datetime):
            return bq.ScalarQueryParameter(None, 'TIMESTAMP' if v.tzinfo else 'DATETIME', v)
        if isinstance(v, datetime.date):
            return bq.ScalarQueryParameter(None, 'DATE', v)
        if isinstance(v, bytes):
            return bq.ScalarQueryParameter(None, 'BYTES', v)
        return bq.ScalarQueryParameter(None, 'STRING', None if v is None else str(v))

    def _trocar_marcadores(self, consulta):
        return consulta.replace('%s', '?')

    def _executar(self, consulta, params=None, buscar=False):
        cli = self._garantir()
        consulta, params = self._preparar(consulta, params)
        kw = {'query_parameters': [self._param(v) for v in (params or ())]}
        if self._dataset:
            kw['default_dataset'] = f'{self._projeto}.{self._dataset}'
        try:
            job = cli.query(consulta, job_config=self._bq.QueryJobConfig(**kw))
            res = job.result()
            if buscar:
                return [{self._nome_col(k): _converter_valor(v) for k, v in dict(row.items()).items()}
                        for row in res]
            return int(getattr(job, 'num_dml_affected_rows', 0) or 0)
        except Exception as e:
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}") from e

    def listar_tabelas(self):
        try:
            return sorted(t.table_id for t in self._garantir().list_tables(self._dataset))
        except Exception as e:
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}") from e

    def descrever_tabela(self, nome):
        t = self._garantir().get_table(f'{self._projeto}.{self._dataset}.{nome}')
        return [dict(coluna=c.name, tipo=c.field_type,
                     aceita_nulo='NO' if c.mode == 'REQUIRED' else 'YES') for c in t.schema]

    def iniciar(self):
        raise ErroBanco("O BigQuery não oferece transações por este conector.")

    confirmar = reverter = iniciar_transacao = iniciar


class ConectorCassandra(ConectorSQL):
    """Cassandra (CQL): cassandra://usuario:senha@host:9042/keyspace. Sem transações nem OFFSET;
    filtros fora da chave usam ALLOW FILTERING (lento em tabelas grandes)."""
    tipo = 'cassandra'
    suporta_notnull = False
    suporta_unico = False
    suporta_padrao = False
    suporta_fk = False
    autonum = 'uuid'
    verdadeiro, falso = 'true', 'false'
    tipos = dict(ConectorSQL.tipos, inteiro='int', numero='decimal', decimal='decimal', flutuante='double',
                 grande='bigint', texto='text', varchar='text', char='text', data='date', hora='time',
                 datahora='timestamp', timestamp='timestamp', booleano='boolean', bool='boolean',
                 json='text', bytes='blob', ref='int')

    def __init__(self, params):
        super().__init__(params)
        self._tabelas_uuid = set()

    def _conectar_driver(self):
        _carregar_driver('cassandra')
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
        from cassandra.query import dict_factory
        p = self.params
        auth = PlainTextAuthProvider(p['usuario'], p['senha'] or '') if p.get('usuario') else None
        self._cluster = Cluster([p['host']], port=p['porta'], auth_provider=auth)
        sessao = self._cluster.connect(p['banco']) if p.get('banco') else self._cluster.connect()
        sessao.row_factory = dict_factory
        return sessao

    def fechar(self):
        try:
            self._cluster.shutdown()
        finally:
            self._conn = None
        return True

    def _executar(self, consulta, params=None, buscar=False):
        sessao = self._garantir()
        consulta, params = self._preparar(consulta, params)
        try:
            linhas = sessao.execute(consulta, params) if params else sessao.execute(consulta)
            if buscar:
                return [{self._nome_col(k): _converter_valor(v) for k, v in dict(r).items()}
                        for r in linhas]
            return 0
        except Exception as e:
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}") from e

    def _keyspace(self):
        ks = str(self.params.get('banco') or '')
        if not re.fullmatch(r'\w+', ks):
            raise ErroBanco("Informe o keyspace na URL: cassandra://host:9042/meu_keyspace")
        return ks

    def _coluna_auto(self, tabela, campo):
        self._tabelas_uuid.add(str(tabela))
        return f'{self._id(campo)} uuid', []

    def _criar_se_nao_existe(self, tabela, corpo):
        cols = getattr(self, '_cols_nomes', [])
        chave = 'id' if 'id' in cols else (cols[0] if cols else 'id')
        return (f'CREATE TABLE IF NOT EXISTS {self._id(tabela)} (\n    {corpo},\n'
                f'    PRIMARY KEY ({self._id(chave)})\n)')

    def inserir(self, tabela, dados):
        dados = dict(dados or {})
        if 'id' not in dados and str(tabela) in self._tabelas_uuid:
            import uuid
            dados['id'] = uuid.uuid4()
        novo = super().inserir(tabela, dados)
        return {k: (str(v) if k == 'id' else v) for k, v in novo.items()}

    def _montar_select(self, cols, tabela, where, ordem, limite, offset):
        if offset:
            raise ErroBanco("O Cassandra não tem OFFSET (paginação por número de página).")
        q = f'SELECT {cols} FROM {self._id(tabela)}'
        if where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in where)
        if ordem:
            q += f' ORDER BY {ordem}'
        if limite is not None:
            q += f' LIMIT {int(limite)}'
        if where:
            q += ' ALLOW FILTERING'
        return q

    def contar(self, tabela, onde=None, params=None):
        q = f'SELECT COUNT(*) AS total FROM {self._id(tabela)}'
        if onde:
            q += f' WHERE {onde} ALLOW FILTERING'
        r = self._executar(q, params, buscar=True)
        return int(r[0]['total']) if r else 0

    def _sql_listar_tabelas(self):
        return ("SELECT table_name AS nome FROM system_schema.tables "
                f"WHERE keyspace_name = '{self._keyspace()}'")

    def _sql_colunas(self):
        return ("SELECT column_name AS coluna, type AS tipo, kind AS aceita_nulo "
                f"FROM system_schema.columns WHERE keyspace_name = '{self._keyspace()}' "
                "AND table_name = %s")

    def iniciar(self):
        raise ErroBanco("O Cassandra não tem transações.")

    confirmar = reverter = iniciar_transacao = iniciar


# ══════════════════════════════════════════════════════════════════════════════
#  Grupo 2, lote B — documentos (CouchDB, Firestore, DynamoDB, Elasticsearch)
# ══════════════════════════════════════════════════════════════════════════════

def _valor_campo(doc, campo):
    atual = doc
    for parte in str(campo).split('.'):
        if isinstance(atual, dict) and parte in atual:
            atual = atual[parte]
        else:
            return None
    return atual


def casa_filtro(doc, filtro):
    """Aplica um filtro estilo MongoDB ({campo: valor} ou {campo: {"$gt": 1}}) a um documento."""
    for campo, cond in filtro.items():
        valor = doc.get('id') if campo in ('id', '_id') else _valor_campo(doc, campo)
        if campo in ('id', '_id'):
            valor = None if valor is None else str(valor)
            cond = {k: (str(v) if not isinstance(v, (list, dict)) else v) for k, v in cond.items()} \
                if isinstance(cond, dict) else str(cond)
        ops = cond if isinstance(cond, dict) and any(str(k).startswith('$') for k in cond) else {'$eq': cond}
        for op, alvo in ops.items():
            try:
                if op == '$eq' and not valor == alvo: return False
                if op == '$ne' and not valor != alvo: return False
                if op == '$gt' and not valor > alvo: return False
                if op == '$gte' and not valor >= alvo: return False
                if op == '$lt' and not valor < alvo: return False
                if op == '$lte' and not valor <= alvo: return False
            except TypeError:
                return False
    return True


class ConectorDocumentos(ConectorBase):
    """Base para bancos de documentos sem SQL. Cada banco implementa só as primitivas _p_*;
    filtros, ordenação e paginação são aplicados aqui (em Python, sobre o que o banco devolver)."""

    # primitivas — implementadas por cada banco
    def _p_inserir(self, colecao, doc): raise NotImplementedError          # → id
    def _p_listar(self, colecao, filtro): raise NotImplementedError        # → [{'id':..., ...}]
    def _p_atualizar(self, colecao, id_, dados): raise NotImplementedError
    def _p_remover(self, colecao, id_): raise NotImplementedError
    def _p_colecoes(self): raise NotImplementedError
    def _p_criar(self, colecao): raise NotImplementedError
    def _p_apagar(self, colecao): raise NotImplementedError

    def _p_obter(self, colecao, id_):
        achados = [d for d in self._p_listar(colecao, {'id': id_}) if casa_filtro(d, {'id': id_})]
        return achados[0] if achados else None

    def _tratar(self, funcao, *a, **k):
        try:
            return funcao(*a, **k)
        except ErroBanco:
            raise
        except Exception as e:
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}") from e

    @staticmethod
    def _limpar(doc):
        d = dict(doc)
        d.pop('_rev', None)
        if '_id' in d and 'id' not in d:
            d['id'] = d['_id']
        d.pop('_id', None)
        if 'id' in d:
            d['id'] = str(d['id'])
        return d

    def _achar(self, colecao, filtro, ordem=None, limite=None, pular=0, campos=None):
        docs = [self._limpar(d) for d in self._tratar(self._p_listar, colecao, filtro)]
        docs = [d for d in docs if casa_filtro(d, filtro)]
        if ordem:
            campo, desc = ordem

            def chave(d):
                v = _valor_campo(d, campo)
                return (v is None, v if isinstance(v, (int, float)) else str(v) if v is not None else '')
            try:
                docs.sort(key=chave, reverse=desc)
            except TypeError:
                docs.sort(key=lambda d: str(_valor_campo(d, campo)), reverse=desc)
        if pular:
            docs = docs[pular:]
        if limite is not None:
            docs = docs[:limite]
        if campos:
            docs = [{k: v for k, v in d.items() if k in campos or k == 'id'} for d in docs]
        return docs

    def _filtro(self, filtro):
        return dict(filtro)

    # API pública
    def tabela(self, nome, campos=None, sobrescrever=False):
        """Cria a coleção/índice/tabela se não existir (os campos são ignorados)."""
        if sobrescrever:
            self.apagar_tabela(nome)
        if nome not in self.listar_tabelas():
            self._tratar(self._p_criar, nome)
        return f"✅ Coleção '{nome}' pronta"

    criar_tabela = tabela

    def apagar_tabela(self, nome, cascata=False):
        if nome in self.listar_tabelas():
            self._tratar(self._p_apagar, nome)
        return f"✅ Coleção '{nome}' removida"

    def listar_tabelas(self):
        return sorted(self._tratar(self._p_colecoes))

    listar_colecoes = listar_tabelas

    def inserir(self, colecao, dados):
        if not dados:
            raise ErroBanco("inserir: nenhum dado informado")
        doc = dict(dados)
        novo_id = self._tratar(self._p_inserir, colecao, doc)
        doc.pop('id', None)
        return {**doc, 'id': str(novo_id)}

    def inserir_varios(self, colecao, lista):
        if not lista:
            raise ErroBanco("inserir_varios: lista vazia")
        for item in lista:
            self.inserir(colecao, item)
        return f"✅ {len(lista)} registros inseridos"

    def buscar(self, colecao):
        return ConsultaDoc(self, colecao)

    def buscar_por_id(self, colecao, id_val):
        d = self._tratar(self._p_obter, colecao, str(id_val))
        return self._limpar(d) if d else {}

    buscar_id = buscar_por_id

    def atualizar(self, colecao, dados):
        return AtualizacaoDoc(self, colecao, dados)

    def deletar(self, colecao):
        return RemocaoDoc(self, colecao)

    def contar(self, colecao, onde=None, params=None):
        filtro = cond_para_filtro(onde, params or []) if onde else {}
        return len(self._achar(colecao, filtro))

    def sql(self, *a, **k):
        raise ErroBanco(f"O {self.nome_banco} não usa SQL. Use inserir, buscar, atualizar e deletar.")


def _params_planos(params):
    if len(params) == 1 and isinstance(params[0], (list, tuple)):
        return tuple(params[0])
    return params


class ConsultaDoc:
    def __init__(self, db, colecao):
        self._db, self._col = db, colecao
        self._filtro, self._campos = {}, None
        self._ordem, self._limite, self._pular = None, None, 0

    def campos(self, *cols):
        self._campos = set(cols)
        return self

    def onde(self, condicao, *params):
        self._filtro.update(cond_para_filtro(condicao, _params_planos(params)))
        return self

    def ordenar(self, campo, direcao='ASC'):
        self._ordem = (str(campo), str(direcao).upper() == 'DESC')
        return self

    def limite(self, n):
        self._limite = int(n)
        return self

    def pagina(self, numero, tamanho=10):
        self._limite = int(tamanho)
        self._pular = (int(numero) - 1) * int(tamanho)
        return self

    def executar(self):
        return self._db._achar(self._col, self._filtro, self._ordem, self._limite, self._pular, self._campos)

    def __iter__(self):
        return iter(self.executar())

    def __len__(self):
        return len(self.executar())

    def primeiro(self):
        self._limite = 1
        r = self.executar()
        return r[0] if r else None

    def existe(self):
        return self.primeiro() is not None

    def contar(self):
        return len(self._db._achar(self._col, self._filtro))


class AtualizacaoDoc:
    def __init__(self, db, colecao, dados):
        self._db, self._col, self._dados, self._filtro = db, colecao, dict(dados), {}

    def onde(self, condicao, *params):
        self._filtro.update(cond_para_filtro(condicao, _params_planos(params)))
        return self

    def executar(self):
        alvo = self._db._achar(self._col, self._filtro)
        dados = {k: v for k, v in self._dados.items() if k != 'id'}
        for d in alvo:
            self._db._tratar(self._db._p_atualizar, self._col, d['id'], dados)
        return len(alvo)


class RemocaoDoc:
    def __init__(self, db, colecao):
        self._db, self._col, self._filtro = db, colecao, {}

    def onde(self, condicao, *params):
        self._filtro.update(cond_para_filtro(condicao, _params_planos(params)))
        return self

    def executar(self):
        alvo = self._db._achar(self._col, self._filtro)
        for d in alvo:
            self._db._tratar(self._db._p_remover, self._col, d['id'])
        return len(alvo)


class ConectorCouchDB(ConectorDocumentos):
    """CouchDB: couchdb://usuario:senha@host:5984  (cada 'tabela' é um banco do CouchDB;
    nomes em minúsculas). Use ?https=1 para HTTPS."""
    tipo = 'couchdb'

    def _abrir(self):
        from urllib.parse import quote
        couchdb = _carregar_driver('couchdb')
        p = self.params
        op = p.get('opcoes') or {}
        esquema = 'https' if str(op.get('https', '')).lower() in ('1', 'true', 'sim') or \
            p.get('esquema') == 'couchdbs' else 'http'
        cred = f"{quote(p['usuario'])}:{quote(p['senha'] or '')}@" if p.get('usuario') else ''
        self._srv = couchdb.Server(f"{esquema}://{cred}{p['host']}:{p['porta']}/")
        self._conn = self._srv
        try:
            self._srv.version()
        except Exception as e:
            raise ErroBanco(f"Não foi possível conectar ao CouchDB: {e}") from e

    def fechar(self):
        self._conn = None
        return True

    def _db(self, col):
        return self._srv[col]

    def _p_inserir(self, col, doc):
        if 'id' in doc:
            doc['_id'] = str(doc.pop('id'))
        return self._db(col).save(doc)[0]

    def _p_listar(self, col, filtro):
        seletor = {('_id' if k == 'id' else k): v for k, v in filtro.items()} or {'_id': {'$gt': None}}
        return list(self._db(col).find({'selector': seletor, 'limit': 1000000}))

    def _p_obter(self, col, id_):
        try:
            return dict(self._db(col)[id_])
        except Exception:
            return None

    def _p_atualizar(self, col, id_, dados):
        banco = self._db(col)
        doc = banco[id_]
        doc.update(dados)
        banco.save(doc)

    def _p_remover(self, col, id_):
        banco = self._db(col)
        banco.delete(banco[id_])

    def _p_colecoes(self):
        return [n for n in self._srv if not n.startswith('_')]

    def _p_criar(self, col):
        if not re.fullmatch(r'[a-z][a-z0-9_$()+/-]*', col):
            raise ErroBanco("Nome inválido no CouchDB: use minúsculas, números e _ (começando por letra).")
        self._srv.create(col)

    def _p_apagar(self, col):
        self._srv.delete(col)


class ConectorFirestore(ConectorDocumentos):
    """Google Firestore: firestore://PROJETO?credenciais=chave.json
    (sem credenciais, usa GOOGLE_APPLICATION_CREDENTIALS). Filtra no cliente: leia o custo na documentação."""
    tipo = 'firestore'

    def _abrir(self):
        fs = _carregar_driver('firestore')
        p = self.params
        cred = (p.get('opcoes') or {}).get('credenciais')
        projeto = p.get('host')
        self._cli = fs.Client.from_service_account_json(cred, project=projeto) if cred \
            else fs.Client(project=projeto)
        self._conn = self._cli

    def fechar(self):
        try:
            self._cli.close()
        except Exception:
            pass
        self._conn = None
        return True

    def _p_inserir(self, col, doc):
        if 'id' in doc:
            ref = self._cli.collection(col).document(str(doc.pop('id')))
            ref.set(doc)
            return ref.id
        return self._cli.collection(col).add(doc)[1].id

    def _p_listar(self, col, filtro):
        return [{**d.to_dict(), 'id': d.id} for d in self._cli.collection(col).stream()]

    def _p_obter(self, col, id_):
        d = self._cli.collection(col).document(id_).get()
        return {**d.to_dict(), 'id': id_} if d.exists else None

    def _p_atualizar(self, col, id_, dados):
        self._cli.collection(col).document(id_).update(dados)

    def _p_remover(self, col, id_):
        self._cli.collection(col).document(id_).delete()

    def _p_colecoes(self):
        return [c.id for c in self._cli.collections()]

    def _p_criar(self, col):
        pass                                   # o Firestore cria a coleção no primeiro documento

    def _p_apagar(self, col):
        for d in self._cli.collection(col).stream():
            d.reference.delete()


def _para_dynamo(v):
    if isinstance(v, float):
        return Decimal(str(v))
    if isinstance(v, dict):
        return {k: _para_dynamo(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_para_dynamo(x) for x in v]
    return v


def _de_dynamo(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, dict):
        return {k: _de_dynamo(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_de_dynamo(x) for x in v]
    return v


class ConectorDynamoDB(ConectorDocumentos):
    """Amazon DynamoDB: dynamodb://CHAVE:SEGREDO@us-east-1 (ou sem credenciais, usando a configuração
    padrão da AWS). DynamoDB local: ?endpoint=http://localhost:8000. Tabelas com chave 'id' (texto).
    Consultas fazem Scan (leem a tabela inteira = custo)."""
    tipo = 'dynamodb'

    def _abrir(self):
        boto3 = _carregar_driver('dynamodb')
        p = self.params
        op = p.get('opcoes') or {}
        kw = {}
        regiao = op.get('regiao') or p.get('host') or os.environ.get('AWS_DEFAULT_REGION')
        if regiao:
            kw['region_name'] = regiao
        if p.get('usuario'):
            kw['aws_access_key_id'] = p['usuario']
            kw['aws_secret_access_key'] = p['senha'] or ''
        if op.get('endpoint'):
            kw['endpoint_url'] = op['endpoint']
        self._res = boto3.resource('dynamodb', **kw)
        self._conn = self._res

    def fechar(self):
        self._conn = None
        return True

    def _tab(self, col):
        return self._res.Table(col)

    def _p_inserir(self, col, doc):
        import uuid
        id_ = str(doc.pop('id')) if 'id' in doc else str(uuid.uuid4())
        self._tab(col).put_item(Item={**_para_dynamo(doc), 'id': id_})
        return id_

    def _p_listar(self, col, filtro):
        t = self._tab(col)
        r = t.scan()
        itens = list(r.get('Items', []))
        while r.get('LastEvaluatedKey'):
            r = t.scan(ExclusiveStartKey=r['LastEvaluatedKey'])
            itens += r.get('Items', [])
        return [_de_dynamo(i) for i in itens]

    def _p_obter(self, col, id_):
        item = self._tab(col).get_item(Key={'id': id_}).get('Item')
        return _de_dynamo(item) if item else None

    def _p_atualizar(self, col, id_, dados):
        if not dados:
            return
        nomes = {f'#c{i}': k for i, k in enumerate(dados)}
        valores = {f':v{i}': _para_dynamo(v) for i, v in enumerate(dados.values())}
        expr = 'SET ' + ', '.join(f'#c{i} = :v{i}' for i in range(len(dados)))
        self._tab(col).update_item(Key={'id': id_}, UpdateExpression=expr,
                                   ExpressionAttributeNames=nomes, ExpressionAttributeValues=valores)

    def _p_remover(self, col, id_):
        self._tab(col).delete_item(Key={'id': id_})

    def _p_colecoes(self):
        return [t.name for t in self._res.tables.all()]

    def _p_criar(self, col):
        t = self._res.create_table(
            TableName=col, KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST')
        t.wait_until_exists()

    def _p_apagar(self, col):
        t = self._tab(col)
        t.delete()
        t.wait_until_not_exists()


class ConectorElasticsearch(ConectorDocumentos):
    """Elasticsearch: elasticsearch://usuario:senha@host:9200 (?https=1, ?verificar_certificado=0).
    Cada 'tabela' é um índice. Leitura traz até 10.000 documentos por consulta."""
    tipo = 'elasticsearch'

    def _abrir(self):
        es = _carregar_driver('elasticsearch')
        p = self.params
        op = p.get('opcoes') or {}
        https = str(op.get('https', '')).lower() in ('1', 'true', 'sim')
        kw = {}
        if p.get('usuario'):
            kw['basic_auth'] = (p['usuario'], p['senha'] or '')
        if str(op.get('verificar_certificado', '1')).lower() in ('0', 'false', 'nao', 'não'):
            kw['verify_certs'] = False
        self._es = es.Elasticsearch(f"{'https' if https else 'http'}://{p['host']}:{p['porta']}", **kw)
        self._conn = self._es

    def fechar(self):
        try:
            self._es.close()
        except Exception:
            pass
        self._conn = None
        return True

    @staticmethod
    def _consulta(filtro):
        """Traduz só o que é seguro empurrar para o servidor; o resto o Advak filtra depois."""
        must = []
        for campo, cond in filtro.items():
            if campo in ('id', '_id'):
                if not isinstance(cond, dict):
                    must.append({'ids': {'values': [str(cond)]}})
                continue
            if isinstance(cond, dict):
                faixa = {op[1:]: v for op, v in cond.items() if op in ('$gt', '$gte', '$lt', '$lte')}
                if faixa:
                    must.append({'range': {campo: faixa}})
                if '$eq' in cond:
                    must.append({'match_phrase': {campo: cond['$eq']}} if isinstance(cond['$eq'], str)
                                else {'term': {campo: cond['$eq']}})
            elif isinstance(cond, str):
                must.append({'match_phrase': {campo: cond}})
            else:
                must.append({'term': {campo: cond}})
        return {'bool': {'must': must}} if must else {'match_all': {}}

    def _p_inserir(self, col, doc):
        id_ = str(doc.pop('id')) if 'id' in doc else None
        return self._es.index(index=col, id=id_, document=doc, refresh='wait_for')['_id']

    def _p_listar(self, col, filtro):
        r = self._es.search(index=col, query=self._consulta(filtro), size=10000)
        return [{**h['_source'], 'id': h['_id']} for h in r['hits']['hits']]

    def _p_atualizar(self, col, id_, dados):
        self._es.update(index=col, id=id_, doc=dados, refresh='wait_for')

    def _p_remover(self, col, id_):
        self._es.delete(index=col, id=id_, refresh='wait_for')

    def _p_colecoes(self):
        return [n for n in self._es.indices.get_alias(index='*') if not n.startswith('.')]

    def _p_criar(self, col):
        self._es.indices.create(index=col)

    def _p_apagar(self, col):
        self._es.indices.delete(index=col, ignore_unavailable=True)


# ══════════════════════════════════════════════════════════════════════════════
#  Grupo 2, lote B — grafos e séries temporais
# ══════════════════════════════════════════════════════════════════════════════

_RE_NOME_SIMPLES = re.compile(r'^[^\W\d]\w*$', re.UNICODE)


def _nome_simples(nome, o_que='nome'):
    if not _RE_NOME_SIMPLES.match(str(nome)):
        raise ErroBanco(f"{o_que.capitalize()} inválido: '{nome}'. Use letras, números e _ (sem espaços).")
    return str(nome)


_OPS_CYPHER = {'$ne': '<>', '$gt': '>', '$gte': '>=', '$lt': '<', '$lte': '<='}


class ConectorNeo4j(ConectorBase):
    """Neo4j 5+: neo4j://usuario:senha@host:7687/banco. 'Tabela' = rótulo (label) dos nós."""
    tipo = 'neo4j'

    def _abrir(self):
        neo = _carregar_driver('neo4j')
        p = self.params
        esquema = p.get('esquema') if p.get('esquema') in ('neo4j', 'bolt', 'neo4j+s', 'bolt+s',
                                                            'neo4j+ssc', 'bolt+ssc') else 'neo4j'
        auth = (p['usuario'], p['senha'] or '') if p.get('usuario') else None
        self._drv = neo.GraphDatabase.driver(f"{esquema}://{p['host']}:{p['porta']}", auth=auth)
        self._conn = self._drv

    def fechar(self):
        try:
            self._drv.close()
        finally:
            self._conn = None
        return True

    def consulta(self, cypher, params=None):
        """db.consulta("MATCH (p:Pessoa) WHERE p.idade > $i RETURN p.nome AS nome", {i: 18})"""
        self._garantir()
        try:
            with self._drv.session(database=self.params.get('banco') or None) as s:
                return [dict(r.data()) for r in s.run(cypher, dict(params or {}))]
        except Exception as e:
            raise ErroBanco(f"Erro no Neo4j: {e}") from e

    comando = consulta

    def _garantir(self):
        if self._conn is None:
            raise ErroBanco("Conexão fechada. Use banco.conectar(...) novamente.")

    def sql(self, *a, **k):
        raise ErroBanco("O Neo4j usa Cypher: use db.consulta(\"MATCH ...\", {parametros}).")

    def tabela(self, rotulo, campos=None, sobrescrever=False):
        """Cria restrições de unicidade para os campos marcados com 'unico'."""
        rotulo = _nome_simples(rotulo, 'rótulo')
        for campo, definicao in dict(campos or {}).items():
            if 'unico' in str(definicao).lower().split():
                c = _nome_simples(campo, 'campo')
                self.consulta(f'CREATE CONSTRAINT IF NOT EXISTS FOR (n:{rotulo}) REQUIRE n.{c} IS UNIQUE')
        return f"✅ Rótulo '{rotulo}' pronto"

    criar_tabela = tabela

    def listar_tabelas(self):
        return sorted(r['label'] for r in self.consulta('CALL db.labels() YIELD label RETURN label'))

    def apagar_tabela(self, rotulo, cascata=False):
        self.consulta(f'MATCH (n:{_nome_simples(rotulo, "rótulo")}) DETACH DELETE n')
        return f"✅ Nós '{rotulo}' removidos"

    def inserir(self, rotulo, dados):
        rotulo = _nome_simples(rotulo, 'rótulo')
        props = dict(dados or {})
        props.pop('id', None)
        r = self.consulta(f'CREATE (n:{rotulo}) SET n = $props RETURN elementId(n) AS id', {'props': props})
        return {**props, 'id': r[0]['id']}

    def inserir_varios(self, rotulo, lista):
        for item in lista:
            self.inserir(rotulo, item)
        return f"✅ {len(lista)} registros inseridos"

    def relacionar(self, id_origem, tipo, id_destino, dados=None):
        """db.relacionar(ana.id, "AMIGO_DE", bia.id, {desde: 2020})"""
        tipo = _nome_simples(tipo, 'tipo de relação')
        r = self.consulta(
            'MATCH (a), (b) WHERE elementId(a) = $a AND elementId(b) = $b '
            f'CREATE (a)-[r:{tipo}]->(b) SET r = $props RETURN elementId(r) AS id',
            {'a': str(id_origem), 'b': str(id_destino), 'props': dict(dados or {})})
        if not r:
            raise ErroBanco("relacionar: um dos nós não foi encontrado")
        return r[0]['id']

    def buscar(self, rotulo):
        return ConsultaGrafo(self, rotulo)

    def buscar_por_id(self, rotulo, id_val):
        return ConsultaGrafo(self, rotulo).onde({'id': str(id_val)}).primeiro() or {}

    buscar_id = buscar_por_id

    def atualizar(self, rotulo, dados):
        return AtualizacaoGrafo(self, rotulo, dados)

    def deletar(self, rotulo):
        return RemocaoGrafo(self, rotulo)

    def contar(self, rotulo, onde=None, params=None):
        c = ConsultaGrafo(self, rotulo)
        if onde:
            c.onde(onde, *(params or []))
        return c.contar()


class ConsultaGrafo:
    def __init__(self, db, rotulo):
        self._db, self._rotulo = db, _nome_simples(rotulo, 'rótulo')
        self._filtro, self._ordem, self._limite, self._pular = {}, None, None, 0

    def onde(self, condicao, *params):
        self._filtro.update(cond_para_filtro(condicao, _params_planos(params)))
        return self

    def ordenar(self, campo, direcao='ASC'):
        d = 'DESC' if str(direcao).upper() == 'DESC' else 'ASC'
        self._ordem = f'n.{_nome_simples(campo, "campo")} {d}'
        return self

    def limite(self, n):
        self._limite = int(n)
        return self

    def pagina(self, numero, tamanho=10):
        self._limite, self._pular = int(tamanho), (int(numero) - 1) * int(tamanho)
        return self

    def _where(self):
        partes, params = [], {}
        for i, (campo, cond) in enumerate(self._filtro.items()):
            ops = cond if isinstance(cond, dict) else {'$eq': cond}
            for j, (op, valor) in enumerate(ops.items()):
                nome = f'p{i}_{j}'
                alvo = 'elementId(n)' if campo in ('id', '_id') else f'n.{_nome_simples(campo, "campo")}'
                partes.append(f'{alvo} {"=" if op == "$eq" else _OPS_CYPHER[op]} ${nome}')
                params[nome] = str(valor) if campo in ('id', '_id') else valor
        return (' WHERE ' + ' AND '.join(partes) if partes else ''), params

    def executar(self):
        onde, params = self._where()
        q = f'MATCH (n:{self._rotulo}){onde} RETURN n AS no, elementId(n) AS id'
        if self._ordem:
            q += f' ORDER BY {self._ordem}'
        if self._pular:
            q += f' SKIP {self._pular}'
        if self._limite is not None:
            q += f' LIMIT {self._limite}'
        return [{**dict(r['no']), 'id': r['id']} for r in self._db.consulta(q, params)]

    def __iter__(self):
        return iter(self.executar())

    def __len__(self):
        return len(self.executar())

    def primeiro(self):
        self._limite = 1
        r = self.executar()
        return r[0] if r else None

    def existe(self):
        return self.primeiro() is not None

    def contar(self):
        onde, params = self._where()
        r = self._db.consulta(f'MATCH (n:{self._rotulo}){onde} RETURN count(n) AS total', params)
        return int(r[0]['total']) if r else 0


class AtualizacaoGrafo(ConsultaGrafo):
    def __init__(self, db, rotulo, dados):
        super().__init__(db, rotulo)
        self._dados = {k: v for k, v in dict(dados).items() if k != 'id'}

    def executar(self):
        onde, params = self._where()
        params['dados'] = self._dados
        r = self._db.consulta(f'MATCH (n:{self._rotulo}){onde} SET n += $dados RETURN count(n) AS total', params)
        return int(r[0]['total']) if r else 0


class RemocaoGrafo(ConsultaGrafo):
    def executar(self):
        onde, params = self._where()
        r = self._db.consulta(f'MATCH (n:{self._rotulo}){onde} WITH collect(n) AS ns '
                              'FOREACH (x IN ns | DETACH DELETE x) RETURN size(ns) AS total', params)
        return int(r[0]['total']) if r else 0


def _lit_flux(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return repr(v)
    if v is None:
        raise ErroBanco("InfluxDB: valor nulo não pode ser usado em filtros")
    return json.dumps(str(v), ensure_ascii=False).replace('$', '\\$')


_RE_DURACAO = re.compile(r'^-?\d+(ms|s|m|h|d|w|mo|y)$')
_RE_DATA_RFC = re.compile(r'^\d{4}-\d{2}-\d{2}T[\d:.]+Z$')


class ConectorInfluxDB(ConectorBase):
    """InfluxDB 2.x: influxdb://:TOKEN@host:8086/BUCKET?org=MINHA_ORG (?https=1).
    'Tabela' = medição. Pontos de tempo não são atualizáveis: grave um novo ponto."""
    tipo = 'influxdb'

    def _abrir(self):
        influx = _carregar_driver('influxdb')
        p = self.params
        op = p.get('opcoes') or {}
        https = str(op.get('https', '')).lower() in ('1', 'true', 'sim')
        token = p.get('senha') or op.get('token') or os.environ.get('INFLUXDB_TOKEN', '')
        self._org = op.get('org') or p.get('usuario') or ''
        self._bucket = p.get('banco') or op.get('bucket') or ''
        self._cli = influx.InfluxDBClient(url=f"{'https' if https else 'http'}://{p['host']}:{p['porta']}",
                                          token=token, org=self._org)
        self._conn = self._cli

    def fechar(self):
        try:
            self._cli.close()
        finally:
            self._conn = None
        return True

    def _bucket_ok(self):
        if not self._bucket:
            raise ErroBanco("Informe o bucket na URL: influxdb://:TOKEN@host:8086/meu_bucket?org=minha_org")
        return self._bucket

    def inserir(self, medicao, dados, tags=None, tempo=None):
        """db.inserir("temperatura", {valor: 21.5}, tags={sala: "A"})"""
        from influxdb_client import Point
        from influxdb_client.client.write_api import SYNCHRONOUS
        campos = dict(dados or {})
        if not campos:
            raise ErroBanco("inserir: nenhum campo informado")
        ponto = Point(_nome_simples(medicao, 'medição'))
        for k, v in dict(tags or {}).items():
            ponto = ponto.tag(str(k), str(v))
        for k, v in campos.items():
            ponto = ponto.field(str(k), v)
        if tempo is not None:
            ponto = ponto.time(tempo)
        try:
            self._cli.write_api(write_options=SYNCHRONOUS).write(bucket=self._bucket_ok(),
                                                                  org=self._org, record=ponto)
        except Exception as e:
            raise ErroBanco(f"Erro no InfluxDB: {e}") from e
        return {**campos, **dict(tags or {})}

    escrever = inserir

    def inserir_varios(self, medicao, lista):
        for item in lista:
            self.inserir(medicao, item)
        return f"✅ {len(lista)} registros inseridos"

    def consulta(self, flux):
        """db.consulta('from(bucket: "b") |> range(start: -1h)') → lista de dicts"""
        try:
            tabelas = self._cli.query_api().query(flux, org=self._org)
        except Exception as e:
            raise ErroBanco(f"Erro no InfluxDB: {e}") from e
        linhas = []
        for tabela in tabelas:
            for r in tabela.records:
                v = {k: x for k, x in dict(r.values).items() if k not in ('result', 'table')}
                linhas.append(v)
        return linhas

    def buscar(self, medicao):
        return ConsultaInflux(self, medicao)

    def listar_tabelas(self):
        flux = ('import "influxdata/influxdb/schema"\n'
                f'schema.measurements(bucket: {_lit_flux(self._bucket_ok())})')
        return sorted(str(r['_value']) for r in self.consulta(flux))

    def apagar_dados(self, medicao, inicio='1970-01-01T00:00:00Z', fim='2100-01-01T00:00:00Z'):
        """Apaga os pontos de uma medição entre duas datas (formato 2024-01-31T00:00:00Z)."""
        for d in (inicio, fim):
            if not _RE_DATA_RFC.match(str(d)):
                raise ErroBanco("Datas no formato 2024-01-31T00:00:00Z")
        pred = f'_measurement="{_nome_simples(medicao, "medição")}"'
        try:
            self._cli.delete_api().delete(inicio, fim, pred, bucket=self._bucket_ok(), org=self._org)
        except Exception as e:
            raise ErroBanco(f"Erro no InfluxDB: {e}") from e
        return f"✅ Dados de '{medicao}' removidos"

    def atualizar(self, *a, **k):
        raise ErroBanco("O InfluxDB não atualiza pontos: grave outro ponto com o mesmo tempo e as mesmas tags.")

    def deletar(self, *a, **k):
        raise ErroBanco("No InfluxDB use db.apagar_dados(medicao, inicio, fim).")

    def sql(self, *a, **k):
        raise ErroBanco("O InfluxDB usa Flux: use db.consulta('from(bucket: \"b\") |> ...').")


class ConsultaInflux:
    def __init__(self, db, medicao):
        self._db, self._med = db, _nome_simples(medicao, 'medição')
        self._desde, self._filtro, self._ordem, self._limite = '-30d', {}, ('_time', True), None

    def desde(self, inicio):
        if not (_RE_DURACAO.match(str(inicio)) or _RE_DATA_RFC.match(str(inicio))):
            raise ErroBanco("desde: use uma duração como -1h, -7d ou uma data 2024-01-31T00:00:00Z")
        self._desde = str(inicio)
        return self

    def onde(self, condicao, *params):
        self._filtro.update(cond_para_filtro(condicao, _params_planos(params)))
        return self

    def ordenar(self, campo='tempo', direcao='ASC'):
        c = '_time' if campo in ('tempo', '_time') else _nome_simples(campo, 'campo')
        self._ordem = (c, str(direcao).upper() == 'DESC')
        return self

    def limite(self, n):
        self._limite = int(n)
        return self

    def _flux(self):
        f = [f'from(bucket: {_lit_flux(self._db._bucket_ok())})',
             f'range(start: {self._desde if _RE_DURACAO.match(self._desde) else self._desde})',
             f'filter(fn: (r) => r._measurement == {_lit_flux(self._med)})',
             'pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")']
        ops = {'$ne': '!=', '$gt': '>', '$gte': '>=', '$lt': '<', '$lte': '<='}
        for campo, cond in self._filtro.items():
            c = _nome_simples(campo, 'campo')
            for op, valor in (cond if isinstance(cond, dict) else {'$eq': cond}).items():
                f.append(f'filter(fn: (r) => r.{c} {"==" if op == "$eq" else ops[op]} {_lit_flux(valor)})')
        campo, desc = self._ordem
        f.append(f'sort(columns: [{_lit_flux(campo)}], desc: {"true" if desc else "false"})')
        if self._limite is not None:
            f.append(f'limit(n: {self._limite})')
        return '\n  |> '.join(f)

    def executar(self):
        linhas = self._db.consulta(self._flux())
        for l in linhas:
            if '_time' in l:
                l['tempo'] = l.pop('_time')
            for k in ('_start', '_stop', '_measurement'):
                l.pop(k, None)
        return linhas

    def __iter__(self):
        return iter(self.executar())

    def __len__(self):
        return len(self.executar())

    def primeiro(self):
        self._limite = 1
        r = self.executar()
        return r[0] if r else None

    def existe(self):
        return self.primeiro() is not None

    def contar(self):
        return len(self.executar())
