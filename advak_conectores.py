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
           ['duckdb'], None, 'ConectorDuckDB', 'real')
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
    linhas = ["", "  Bancos de dados suportados pela Advak", "  " + "─" * 86,
              f"  {'Banco':<12}{'Tipo':<22}{'Driver (pip install ...)':<28}{'Instalado':<11}{'Testes'}",
              "  " + "─" * 86]
    for b in listar_bancos():
        inst = "sim" if b['instalado'] else "não"
        teste = "real" if b['testado'] == 'real' else "simulado"
        linhas.append(f"  {b['nome']:<12}{b['grupo']:<22}{b['pip']:<28}{inst:<11}{teste}")
    linhas += ["  " + "─" * 86,
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
    padrao_usuario = {'postgres': 'postgres', 'mysql': 'root', 'mariadb': 'root', 'mssql': 'sa'}.get(tipo)
    return tipo, dict(
        host=str(kw.get('host') or kw.get('hospedeiro') or 'localhost'),
        porta=int(kw.get('porta') or kw.get('port') or BANCOS[tipo]['porta'] or 0) or None,
        usuario=kw.get('usuario') or kw.get('user') or padrao_usuario,
        senha=kw.get('senha') or kw.get('password') or '',
        banco=kw.get('banco') or kw.get('nome') or kw.get('database'),
        esquema=tipo, opcoes={})


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


def conectar(destino, **kw):
    """Cria o conector certo para a URL/tipo informado."""
    tipo, params = resolver_conexao(destino, **kw)
    classe = globals()[BANCOS[tipo]['classe']]
    c = classe(params)
    c._abrir()
    return c


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
        if self.marcador != '%s':
            consulta = consulta.replace('%s', self.marcador)
        return consulta, (tuple(_converter_param(p) for p in params) if params else None)

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
                cols = [d[0] for d in cur.description] if cur.description else []
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
            raise ErroBanco(f"Erro no {self.nome_banco}: {e}") from e
        finally:
            try:
                cur.close()
            except Exception:
                pass

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
            fk = f'FOREIGN KEY ({self._id(campo)}) REFERENCES {self._id(partes[1])}(id)'
            mods = [p.lower() for p in partes[2:]]
        if base == self.tipos['texto'] and ('unico' in mods or 'unique' in mods or 'indice' in mods):
            base = self.texto_indexavel
        sql = [self._id(campo), base]
        if 'obrigatorio' in mods or 'notnull' in mods:
            sql.append('NOT NULL')
        if 'unico' in mods or 'unique' in mods:
            sql.append('UNIQUE')
        if 'padrao' in mods:
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
        if sobrescrever:
            self.apagar_tabela(nome)
        for cmd in antes:
            self._executar(cmd)
        self._executar(self._criar_se_nao_existe(nome, ',\n    '.join(cols + fks)))
        return f"✅ Tabela '{nome}' criada"

    criar_tabela = tabela

    def apagar_tabela(self, nome, cascata=False):
        self._executar(f'DROP TABLE IF EXISTS {self._id(nome)}')
        return f"✅ Tabela '{nome}' removida"

    def _sql_listar_tabelas(self):
        return ("SELECT table_name AS nome FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name")

    def listar_tabelas(self):
        return [r['nome'] for r in self._executar(self._sql_listar_tabelas(), buscar=True)]

    def existe_tabela(self, nome):
        return nome in self.listar_tabelas()

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
        sets = ', '.join(f'{self._db._id(k)} = %s' for k in self._dados)
        q = f'UPDATE {self._db._id(self._tabela)} SET {sets}'
        valores = list(self._dados.values())
        if self._where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in self._where)
            valores += self._params
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
        q = f'DELETE FROM {self._db._id(self._tabela)}'
        if self._where:
            q += ' WHERE ' + ' AND '.join(f'({w})' for w in self._where)
        return self._db._executar(q, self._params or None)


# ── SQLite ───────────────────────────────────────────────────────────────────

class ConectorSQLite(ConectorSQL):
    tipo = 'sqlite'
    marcador = '?'
    autonum = 'INTEGER PRIMARY KEY AUTOINCREMENT'
    verdadeiro, falso = '1', '0'
    tipos = dict(ConectorSQL.tipos, json='TEXT')

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
        pg = _carregar_driver('postgres')
        p = self.params
        return pg.connect(host=p['host'], port=p['porta'], user=p['usuario'],
                          password=p['senha'] or '', dbname=p['banco'] or 'postgres')

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
    filtro = {}
    for parte in re.split(r'\s+AND\s+', str(condicao), flags=re.IGNORECASE):
        m = _RE_COND.match(parte)
        if not m:
            raise ErroBanco(f"MongoDB: condição não suportada: '{parte.strip()}'. Use campo = %s, "
                            "campo > %s, ... ligados por AND, ou passe um dicionário de filtro.")
        campo, op, marc = m.groups()
        if marc.startswith('$'):
            valor = params[int(marc[1:]) - 1]
        else:
            valor = params.pop(0)
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
