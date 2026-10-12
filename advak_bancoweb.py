# -*- coding: utf-8 -*-
"""
advak_bancoweb.py — Banco de Dados Automático para Advak 5.0
PostgreSQL como padrão, SQLite como fallback.

Uso:
    seja db = banco_auto("minha_app")         # PostgreSQL via .env
    seja db = banco_auto("app.db")            # SQLite (fallback)
    seja db = banco_auto("minha_app",
        host="localhost", porta=5432,
        usuario="postgres", senha="123",
        banco="meu_banco")                    # PostgreSQL explícito
"""

import os, json, threading, re, sys
from datetime import datetime

def _carregar_env():
    """Carrega variáveis do arquivo .env se existir."""
    # Procura .env na pasta atual e nas pastas pai
    pasta = os.getcwd()
    for _ in range(3):  # sobe até 3 níveis
        env_path = os.path.join(pasta, '.env')
        if os.path.isfile(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if linha and not linha.startswith('#') and '=' in linha:
                            chave, _, valor = linha.partition('=')
                            chave  = chave.strip()
                            valor  = valor.strip().strip('"').strip("'")
                            os.environ.setdefault(chave, valor)
                return env_path
            except Exception:
                pass
        pasta = os.path.dirname(pasta)
    return None

# Carrega .env automaticamente
_env_file = _carregar_env()

# ── Cores ─────────────────────────────────────────────────────────────────────
def _cor(c, txt):
    if sys.is_finalizing(): return txt
    cores = {"verde":"\033[92m","azul":"\033[94m","amarelo":"\033[93m",
             "verm":"\033[91m","cinza":"\033[90m","neg":"\033[1m","r":"\033[0m"}
    return f"{cores.get(c,'')}{txt}{cores['r']}"

def _log(msg, cor="verde"):
    try:
        if not sys.is_finalizing():
            print(f"  {_cor(cor, msg)}", flush=True)
    except: pass

# ── Tipos de campos ────────────────────────────────────────────────────────────
TIPOS_PG = {
    'texto':     'TEXT',       'text':      'TEXT',
    'numero':    'DECIMAL(12,4)', 'float':  'DECIMAL(12,4)',
    'inteiro':   'INTEGER',    'int':       'INTEGER',
    'bigint':    'BIGINT',     'serial':    'SERIAL',
    'booleano':  'BOOLEAN',    'bool':      'BOOLEAN',
    'data':      'DATE',       'hora':      'TIME',
    'timestamp': 'TIMESTAMP DEFAULT NOW()',
    'json':      'JSONB',      'lista':     'JSONB',
    'uuid':      'UUID DEFAULT gen_random_uuid()',
    'email':     'TEXT',       'url':       'TEXT',
    'senha':     'TEXT',       'cpf':       'TEXT',
    'dinheiro':  'DECIMAL(10,2)',
    'arquivo':   'TEXT',       'imagem':    'TEXT',
}

TIPOS_SQ = {
    'texto':     'TEXT',       'text':      'TEXT',
    'numero':    'REAL',       'float':     'REAL',
    'inteiro':   'INTEGER',    'int':       'INTEGER',
    'bigint':    'INTEGER',    'serial':    'INTEGER',
    'booleano':  'INTEGER',    'bool':      'INTEGER',
    'data':      'TEXT',       'hora':      'TEXT',
    'timestamp': 'TEXT',       'json':      'TEXT',
    'lista':     'TEXT',       'uuid':      'TEXT',
    'email':     'TEXT',       'url':       'TEXT',
    'senha':     'TEXT',       'cpf':       'TEXT',
    'dinheiro':  'REAL',       'arquivo':   'TEXT',
    'imagem':    'TEXT',
}

# ── Banco Principal ────────────────────────────────────────────────────────────
class BancoWeb:
    """
    Banco de dados para aplicações web Advak.
    Usa PostgreSQL por padrão (via .env), SQLite como fallback.
    """

    def __init__(self, nome="app", **kwargs):
        self._nome    = nome
        self._lock    = threading.Lock()
        self._pg      = None   # psycopg2 connection
        self._sq      = None   # sqlite3 connection
        self._modo    = None   # 'pg' ou 'sq'
        self._tabelas = {}     # esquemas registrados
        self._conectar(kwargs)

    # ── Conexão ──────────────────────────────────────────────────────────────
    def _conectar(self, kw):
        # Tenta PostgreSQL primeiro
        if self._tentar_pg(kw): return
        # Fallback para SQLite
        self._usar_sqlite()

    def _tentar_pg(self, kw, silencioso=False):
        try:
            import psycopg2
            import psycopg2.extras

            # Prioridade: kwargs explícitos → variáveis de ambiente → padrões
            host   = kw.get('host')   or os.getenv('ADVAK_DB_HOST', 'localhost')
            porta  = int(kw.get('porta', kw.get('port', 0)) or os.getenv('ADVAK_DB_PORT', 5432))
            user   = kw.get('usuario', kw.get('user', '')) or os.getenv('ADVAK_DB_USER', 'postgres')
            pwd    = kw.get('senha',   kw.get('password', '')) or os.getenv('ADVAK_DB_PASS', '')
            # Priority: explicit kwarg → project name (banco_auto arg)
            # ADVAK_DB_NAME is ONLY used when banco_auto() is called with no name
            explicit = kw.get('banco', kw.get('database', ''))
            if explicit:
                dbname = explicit.rstrip('.db') if explicit.endswith('.db') else explicit
            elif self._nome and self._nome not in ('app', ''):
                # Use the project name passed to banco_auto("biblioteca")
                dbname = self._nome.replace('.db', '')
            else:
                # Last resort: use ADVAK_DB_NAME env var
                dbname = os.getenv('ADVAK_DB_NAME', self._nome).replace('.db', '')

            try:
                conn = psycopg2.connect(
                    host=host, port=porta, user=user,
                    password=pwd, dbname=dbname,
                    connect_timeout=5
                )
            except psycopg2.OperationalError as e:
                # If database doesn't exist, auto-create it!
                if 'does not exist' in str(e) or 'database' in str(e).lower():
                    if not silencioso:
                        _log(f"🔧 Criando banco '{dbname}' no PostgreSQL...", "amarelo")
                    # Connect to default 'postgres' admin database to create
                    admin = psycopg2.connect(
                        host=host, port=porta, user=user,
                        password=pwd, dbname='postgres',
                        connect_timeout=5
                    )
                    admin.autocommit = True
                    admin.cursor().execute(f'CREATE DATABASE "{dbname}"')
                    admin.close()
                    if not silencioso:
                        _log(f"✅ Banco '{dbname}' criado!", "verde")
                    # Now connect to the new database
                    conn = psycopg2.connect(
                        host=host, port=porta, user=user,
                        password=pwd, dbname=dbname,
                        connect_timeout=5
                    )
                else:
                    raise

            # Usa connection pool para PostgreSQL
            try:
                from psycopg2 import pool as _pg_pool
                self._pool = _pg_pool.ThreadedConnectionPool(
                    minconn=2, maxconn=10,
                    host=host, port=porta, user=user,
                    password=pwd, dbname=dbname
                )
                self._pg = None  # connections obtained from pool
                self._pool_ativo = True
            except Exception:
                # Fallback: single connection
                self._pg = conn
                self._pg.autocommit = True
                self._pool = None
                self._pool_ativo = False

            self._modo   = 'pg'
            self._pg_kw  = {
                'host': host, 'porta': porta,
                'user': user, 'pwd': pwd, 'dbname': dbname
            }

            if not silencioso:
                pool_info = " (pool 2-10)" if getattr(self, '_pool_ativo', False) else ""
                _log(f"🐘 PostgreSQL → {host}:{porta}/{dbname}{pool_info}", "verde")
            return True

        except Exception as e:
            if not silencioso:
                import sys as _sys
                # BUG 13 FIX: send PG warnings to stderr to avoid polluting stdout
                _amarel = "\033[93m"; _R = "\033[0m"; _cinza = "\033[90m"
                print(f"  {_amarel}⚠️  PostgreSQL indisponível: {e}{_R}", file=_sys.stderr)
                print(f"  {_cinza}   Configure o arquivo .env:{_R}", file=_sys.stderr)
                print(f"  {_cinza}   ADVAK_DB_HOST=localhost{_R}", file=_sys.stderr)
                print(f"  {_cinza}   ADVAK_DB_PORT=5432{_R}", file=_sys.stderr)
                print(f"  {_cinza}   ADVAK_DB_USER=postgres{_R}", file=_sys.stderr)
                print(f"  {_cinza}   ADVAK_DB_PASS=sua_senha{_R}", file=_sys.stderr)
                print(f"  {_cinza}   ADVAK_DB_NAME={self._nome}{_R}", file=_sys.stderr)
                print(f"  {_amarel}   → Usando SQLite como fallback...{_R}", file=_sys.stderr)
            return False

    def _usar_sqlite(self):
        import sqlite3
        arquivo = self._nome if self._nome.endswith('.db') else f"{self._nome}.db"
        self._sq = sqlite3.connect(arquivo, check_same_thread=False)
        self._sq.row_factory = sqlite3.Row
        self._sq.execute("PRAGMA journal_mode=WAL")
        self._sq.execute("PRAGMA foreign_keys=ON")
        self._modo = 'sq'
        import sys as _sys
        print(f"  \033[94m🗄️  SQLite → {arquivo} (fallback)\033[0m", file=_sys.stderr)

    @property
    def modo(self): return self._modo
    @property
    def eh_postgres(self): return self._modo == 'pg'
    @property
    def eh_sqlite(self): return self._modo == 'sq'

    # ── Execução SQL ──────────────────────────────────────────────────────────
    def _exec(self, sql, params=None, fetch=True):
        with self._lock:
            if self._modo == 'pg':
                return self._exec_pg(sql, params, fetch)
            else:
                return self._exec_sq(sql, params, fetch)

    def _exec_pg(self, sql, params, fetch):
        """Executa SQL no PostgreSQL usando pool de conexões quando disponível."""
        import psycopg2.extras
        pool_ativo = getattr(self, '_pool_ativo', False)
        pool       = getattr(self, '_pool', None)
        conn = None
        try:
            if pool_ativo and pool:
                conn = pool.getconn()
                conn.autocommit = True
            else:
                conn = self._pg
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params or [])
            if fetch:
                try:    return [dict(r) for r in cur.fetchall()]
                except: return []
            return []
        except Exception as e:
            try:
                kw = getattr(self, '_pg_kw', {})
                if kw and not pool_ativo:
                    if self._tentar_pg(kw, silencioso=True):
                        return self._exec_pg(sql, params, fetch)
            except: pass
            raise
        finally:
            if pool_ativo and pool and conn:
                try: pool.putconn(conn)
                except: pass


    def _exec_sq(self, sql, params, fetch):
        import sqlite3
        # Translate PostgreSQL syntax to SQLite
        sql_sq = self._pg2sq(sql)
        try:
            cur = self._sq.execute(sql_sq, params or [])
            if not sql_sq.strip().upper().startswith('SELECT'):
                self._sq.commit()
            if fetch:
                try:
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
                except: return []
            return []
        except Exception as e:
            try: self._sq.rollback()
            except: pass
            raise

    def _pg2sq(self, sql):
        """Translate common PostgreSQL syntax to SQLite."""
        # $1, $2 → ?, ?
        sql = re.sub(r'\$\d+', '?', sql)
        # SERIAL/BIGSERIAL → INTEGER
        sql = re.sub(r'\bSERIAL\b', 'INTEGER', sql, flags=re.I)
        sql = re.sub(r'\bBIGSERIAL\b', 'INTEGER', sql, flags=re.I)
        # BOOLEAN defaults
        sql = re.sub(r'\bTRUE\b', '1', sql)
        sql = re.sub(r'\bFALSE\b', '0', sql)
        # NOW() → datetime('now')
        sql = re.sub(r'\bNOW\(\)', "datetime('now')", sql, flags=re.I)
        # CURRENT_TIMESTAMP
        sql = re.sub(r'\bCURRENT_TIMESTAMP\b', "datetime('now')", sql, flags=re.I)
        # DEFAULT gen_random_uuid() → remove (SQLite doesn't have UUIDs natively)
        sql = re.sub(r'DEFAULT gen_random_uuid\(\)', '', sql, flags=re.I)
        # JSONB → TEXT
        sql = re.sub(r'\bJSONB\b', 'TEXT', sql, flags=re.I)
        # DECIMAL/NUMERIC → REAL
        sql = re.sub(r'\bDECIMAL\(\d+,\d+\)', 'REAL', sql)
        sql = re.sub(r'\bNUMERIC\(\d+,\d+\)', 'REAL', sql)
        # IF NOT EXISTS (already supported by SQLite)
        # ON CONFLICT DO NOTHING → OR IGNORE
        sql = re.sub(r'ON CONFLICT DO NOTHING', 'OR IGNORE', sql, flags=re.I)
        sql = re.sub(r'ON CONFLICT \([^)]+\) DO NOTHING', 'OR IGNORE', sql, flags=re.I)
        # RETURNING → remove (SQLite handles via lastrowid)
        sql = re.sub(r'\bRETURNING\b.*$', '', sql, flags=re.I|re.MULTILINE)
        # ::text, ::integer casts → remove
        sql = re.sub(r'::\w+', '', sql)
        # ILIKE → LIKE (SQLite is case-insensitive by default for ASCII)
        sql = re.sub(r'\bILIKE\b', 'LIKE', sql, flags=re.I)
        return sql.strip()

    # ── Serialização ──────────────────────────────────────────────────────────
    def _ser(self, v):
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False, default=str)
        if isinstance(v, bool):
            return True if self._modo == 'pg' else (1 if v else 0)
        return v

    def _sanitizar_html(self, v):
        """Remove tags HTML perigosas de strings (prevenção XSS)."""
        if not isinstance(v, str): return v
        import html
        return html.escape(v) if v else v

    def _deser(self, row):
        if not isinstance(row, dict): return row
        d = dict(row)
        for k, v in d.items():
            if isinstance(v, str) and v and v[0] in ('{', '['):
                try: d[k] = json.loads(v)
                except: pass
        return d

    # ── Criar Tabela ──────────────────────────────────────────────────────────
    def criar_tabela(self, nome, campos, chave="id"):
        """
        Cria tabela automaticamente se não existir.
        campos = { 'nome': 'texto', 'preco': 'dinheiro', 'ativo': 'booleano' }
        """
        self._tabelas[nome] = campos
        tipos = TIPOS_PG if self._modo == 'pg' else TIPOS_SQ

        if self._modo == 'pg':
            cols = [f"{chave} SERIAL PRIMARY KEY"]
        else:
            cols = [f"{chave} INTEGER PRIMARY KEY AUTOINCREMENT"]

        for campo, tipo in campos.items():
            sql_tipo = tipos.get(tipo.lower(), 'TEXT')
            # Handle timestamp with default
            if tipo.lower() == 'timestamp':
                if self._modo == 'pg':
                    cols.append(f"{campo} TIMESTAMP DEFAULT NOW()")
                else:
                    cols.append(f"{campo} TEXT DEFAULT (datetime('now'))")
            else:
                cols.append(f"{campo} {sql_tipo}")

        # Auto timestamps
        if self._modo == 'pg':
            cols.append("criado_em TIMESTAMP DEFAULT NOW()")
            cols.append("atualizado_em TIMESTAMP DEFAULT NOW()")
        else:
            cols.append("criado_em TEXT DEFAULT (datetime('now'))")
            cols.append("atualizado_em TEXT DEFAULT (datetime('now'))")

        sql = f"CREATE TABLE IF NOT EXISTS {nome} ({', '.join(cols)})"
        self._exec(sql, fetch=False)

        # Auto-update trigger for atualizado_em (PostgreSQL only)
        if self._modo == 'pg':
            try:
                # Create function once (OR REPLACE = idempotent)
                self._exec("""
                    CREATE OR REPLACE FUNCTION _advak_atualizar_ts()
                    RETURNS TRIGGER AS $$
                    BEGIN NEW.atualizado_em = NOW(); RETURN NEW; END;
                    $$ LANGUAGE plpgsql
                """, fetch=False)
                self._exec(f"""
                    DROP TRIGGER IF EXISTS _trg_{nome}_ts ON {nome}
                """, fetch=False)
                self._exec(f"""
                    CREATE TRIGGER _trg_{nome}_ts
                    BEFORE UPDATE ON {nome}
                    FOR EACH ROW EXECUTE FUNCTION _advak_atualizar_ts()
                """, fetch=False)
            except Exception:
                pass  # Triggers are optional

        _log(f"  ✅ {nome} ({len(campos)+3} campos)", "verde")
        return self._tabela_obj(nome)

    def _tabela_obj(self, nome):
        """Retorna objeto com métodos CRUD para a tabela."""
        db = self
        return {
            'nome':       nome,
            'inserir':    lambda d: db.inserir(nome, d),
            'buscar':     lambda condicao=None, params=None, ordenar=None, limite=None, pagina=None:
                             db.buscar(nome, condicao, params, ordenar, limite, pagina),
            'buscar_um':  lambda condicao, params=None: db.buscar_um(nome, condicao, params),
            'buscar_id':  lambda id: db.buscar_um(nome, f"{self._modo=='pg' and 'id=$1' or 'id=?'}", [id]),
            'atualizar':  lambda dados, condicao, params=None: db.atualizar(nome, dados, condicao, params),
            'atualizar_id': lambda id, dados: db.atualizar(nome, dados, 
                               f"{'id=$' + str(len(dados)+1) if db._modo=='pg' else 'id=?'}", 
                               list(dados.values()) + [id]),
            'excluir':    lambda condicao, params=None: db.excluir(nome, condicao, params),
            'excluir_id': lambda id: db.excluir(nome, f"{'id=$1' if db._modo=='pg' else 'id=?'}", [id]),
            'contar':     lambda condicao=None, params=None: db.contar(nome, condicao, params),
            'existe':     lambda condicao, params=None: db.contar(nome, condicao, params) > 0,
            'sql':        lambda s, p=None: db.sql(s, p),
            'todos':      lambda ordenar='id': db.buscar(nome, ordenar=ordenar),
            'limpar':     lambda: db.excluir(nome),
        }

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def inserir(self, tabela, dados):
        campos = list(dados.keys())
        valores = [self._ser(v) for v in dados.values()]

        if self._modo == 'pg':
            marcadores = ', '.join([f'${i+1}' for i in range(len(campos))])
            sql = f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({marcadores}) RETURNING id"
            resultado = self._exec(sql, valores)
            return resultado[0]['id'] if resultado else None
        else:
            marcadores = ', '.join(['?' * len(campos)])
            marcadores = ', '.join(['?'] * len(campos))
            sql = f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({marcadores})"
            self._exec(sql, valores, fetch=False)
            # Get last inserted id
            resultado = self._exec("SELECT last_insert_rowid() as id")
            return resultado[0]['id'] if resultado else None

    def buscar(self, tabela, condicao=None, params=None, ordenar=None, limite=None, pagina=None):
        sql = f"SELECT * FROM {tabela}"
        if condicao: sql += f" WHERE {condicao}"
        if ordenar:  sql += f" ORDER BY {ordenar}"
        if limite:
            sql += f" LIMIT {int(limite)}"
            if pagina and pagina > 1:
                sql += f" OFFSET {(int(pagina)-1) * int(limite)}"
        rows = self._exec(sql, params)
        return [self._deser(r) for r in rows]

    def buscar_um(self, tabela, condicao, params=None):
        resultados = self.buscar(tabela, condicao, params, limite=1)
        return resultados[0] if resultados else None

    def atualizar(self, tabela, dados, condicao, params=None):
        if self._modo == 'pg':
            sets = ', '.join([f"{k}=${i+1}" for i, k in enumerate(dados.keys())])
            valores = [self._ser(v) for v in dados.values()]
            if params: valores += params
            idx_where = len(dados) + 1
            cond_pg = re.sub(r'\$(\d+)', lambda m: f'${int(m.group(1)) + len(dados)}', condicao)
            sql = f"UPDATE {tabela} SET {sets} WHERE {cond_pg}"
        else:
            sets = ', '.join([f"{k}=?" for k in dados.keys()])
            valores = [self._ser(v) for v in dados.values()]
            if params: valores += params
            sql = f"UPDATE {tabela} SET {sets} WHERE {self._pg2sq(condicao)}"
        cur_result = self._exec(sql, valores, fetch=False)
        return True

    def atualizar_id(self, tabela, id, dados):
        if self._modo == 'pg':
            sets = ', '.join([f"{k}=${i+1}" for i, k in enumerate(dados.keys())])
            valores = list(dados.values()) + [id]
            sql = f"UPDATE {tabela} SET {sets} WHERE id=${len(dados)+1}"
        else:
            sets = ', '.join([f"{k}=?" for k in dados.keys()])
            valores = list(dados.values()) + [id]
            sql = f"UPDATE {tabela} SET {sets} WHERE id=?"
        self._exec(sql, valores, fetch=False)
        return True

    def excluir(self, tabela, condicao=None, params=None):
        if condicao:
            if self._modo == 'pg':
                sql = f"DELETE FROM {tabela} WHERE {condicao}"
            else:
                sql = f"DELETE FROM {tabela} WHERE {self._pg2sq(condicao)}"
        else:
            sql = f"DELETE FROM {tabela}"
        self._exec(sql, params, fetch=False)
        return True

    def contar(self, tabela, condicao=None, params=None):
        sql = f"SELECT COUNT(*) AS n FROM {tabela}"
        if condicao:
            sql += f" WHERE {condicao}"
        resultado = self._exec(sql, params)
        if resultado:
            val = resultado[0].get('n', resultado[0].get('count', 0))
            return int(val)
        return 0

    def sql(self, query, params=None):
        """Executa SQL direto (com tradução automática PG→SQLite se necessário)."""
        if isinstance(params, (list, tuple)) and len(params) == 1 and isinstance(params[0], (list, tuple)):
            params = list(params[0])     # banco.sql(q, [a, b]) chega como [[a, b]]
        elif params is not None and not isinstance(params, (list, tuple)):
            params = [params]            # banco.sql(q, valor)
        return self._exec(query, params)

    def transacao(self, fn):
        """Executa função dentro de uma transação explícita."""
        with self._lock:
            try:
                if self._modo == 'pg':
                    self._pg.autocommit = False
                    resultado = fn()
                    self._pg.commit()
                    self._pg.autocommit = True
                else:
                    resultado = fn()
                    self._sq.commit()
                return resultado
            except Exception as e:
                if self._modo == 'pg':
                    try: self._pg.rollback()
                    except: pass
                    try: self._pg.autocommit = True
                    except: pass
                else:
                    try: self._sq.rollback()
                    except: pass
                raise

    def info(self):
        """Retorna informações sobre o banco."""
        if self._modo == 'pg':
            rows = self._exec("""
                SELECT table_name, 
                    (SELECT COUNT(*) FROM information_schema.columns 
                     WHERE table_name=t.table_name AND table_schema='public') as colunas
                FROM information_schema.tables t
                WHERE table_schema='public' AND table_type='BASE TABLE'
                ORDER BY table_name
            """)
        else:
            rows = self._exec("""
                SELECT name as table_name,
                    (SELECT COUNT(*) FROM pragma_table_info(name)) as colunas
                FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
        return {
            'modo': self._modo,
            'eh_postgres': self._modo == 'pg',
            'tabelas': rows or []
        }

    def fechar(self):
        try:
            pool = getattr(self, '_pool', None)
            if pool: pool.closeall()
            elif self._pg: self._pg.close()
        except: pass
        try:
            if self._sq: self._sq.close()
        except: pass
        _log("🔒 Banco fechado.", "cinza") if not __import__('sys').is_finalizing() else None

