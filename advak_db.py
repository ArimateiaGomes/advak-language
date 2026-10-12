"""
Advak 3.0 — Motor de Banco de Dados
Abstração completa do PostgreSQL usando sintaxe Advak nativa.

Comandos suportados:
  banco.criar("nome")
  banco.usar("nome")
  banco.tabela("usuarios") { id: autonum, nome: texto, idade: numero }
  banco.inserir("tabela", {campo: valor, ...})
  banco.buscar("tabela")
  banco.buscar("tabela").onde(campo == valor)
  banco.buscar("tabela").limite(10)
  banco.atualizar("tabela", {campo: valor}).onde(campo == valor)
  banco.deletar("tabela").onde(campo == valor)
  banco.sql("SELECT ...")       -- SQL puro quando precisar
"""

import re
import json


# ── Mapeamento de tipos Advak → PostgreSQL ────────────────────────────────────

TIPOS = {
    # Numéricos
    'autonum':    'SERIAL PRIMARY KEY',
    'inteiro':    'INTEGER',
    'numero':     'NUMERIC',
    'decimal':    'NUMERIC(15,2)',
    'flutuante':  'FLOAT',
    'grande':     'BIGINT',
    # Texto
    'texto':      'TEXT',
    'varchar':    'VARCHAR(255)',
    'char':       'CHAR(1)',
    # Datas / tempo
    'data':       'DATE',
    'hora':       'TIME',
    'datahora':   'TIMESTAMP DEFAULT NOW()',
    'timestamp':  'TIMESTAMP',
    # Booleano
    'booleano':   'BOOLEAN',
    'bool':       'BOOLEAN',
    # Binário / JSON
    'json':       'JSONB',
    'bytes':      'BYTEA',
    # Chave estrangeira (será processado separadamente)
    'ref':        'INTEGER',
}

MODIFICADORES = {
    'unico':      'UNIQUE',
    'obrigatorio':'NOT NULL',
    'padrao':     'DEFAULT',
    'indice':     'INDEX',
}


class AdvakDB:
    """
    Interface principal do banco de dados para o interpretador Advak.
    Exposta como objeto global 'banco' nos programas .dk
    """

    # ─── Tipos mapeados para SQL ──────────────────────────────────────────────
    _AUTO_SETUP_DONE = set()  # bancos já configurados nesta sessão

    def __init__(self, host='localhost', port=5432,
                 user='postgres', password='', dbname='postgres'):
        self.host     = host
        self.port     = port
        self.user     = user
        self.password = password
        self.dbname   = dbname
        self._conn    = None
        self._cur_db  = dbname

    # ── Auto-setup: cria banco e tabelas automaticamente ─────────────────────

    def auto_setup(self, dbname, tabelas: dict):
        """
        Framework auto-cria banco e tabelas se não existirem.

        banco.auto_setup("meu_app", {
            "usuarios": {
                "id":    "autonum",
                "nome":  "texto obrigatorio",
                "email": "texto unico",
                "ativo": "booleano padrao verdadeiro",
            },
            "produtos": {
                "id":      "autonum",
                "nome":    "texto obrigatorio",
                "preco":   "decimal",
                "estoque": "inteiro padrao 0",
            }
        })
        Retorna True se criou algo novo, False se já existia tudo.
        """
        cache_key = f"{self.host}:{self.port}/{dbname}"
        novidades = []

        # 1. Conectar ao postgres (banco padrão) para criar o banco se necessário
        try:
            import psycopg2
            conn_pg = psycopg2.connect(
                host=self.host, port=self.port,
                user=self.user, password=self.password,
                dbname='postgres'
            )
            conn_pg.autocommit = True
            cur = conn_pg.cursor()

            # Verifica se o banco existe
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)
            )
            existe = cur.fetchone()
            if not existe:
                cur.execute(f'CREATE DATABASE "{dbname}"')
                novidades.append(f"Banco '{dbname}' criado")
                print(f"  🗄️  Banco '{dbname}' criado automaticamente")
            cur.close()
            conn_pg.close()
        except Exception as e:
            raise RuntimeError(
                f"\n❌ Não foi possível conectar ao PostgreSQL.\n"
                f"   Erro: {e}\n\n"
                f"   Verifique:\n"
                f"   1. PostgreSQL está instalado e rodando\n"
                f"   2. Configure a senha em env_config.env:\n"
                f"      ADVAK_DB_PASS=sua_senha_aqui\n"
                f"   3. Ou instale: https://www.postgresql.org/download/"
            )

        # 2. Conectar ao banco destino
        if self._conn:
            try: self._conn.close()
            except: pass
        self._cur_db = dbname
        self.conectar(dbname)

        # 3. Criar tabelas que não existem
        for tabela_nome, campos in tabelas.items():
            try:
                import psycopg2
                cur2 = self._conn.cursor()
                cur2.execute(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name=%s",
                    (tabela_nome,)
                )
                tabela_existe = cur2.fetchone()
                cur2.close()

                if not tabela_existe:
                    self.criar_tabela(tabela_nome, campos)
                    novidades.append(f"Tabela '{tabela_nome}' criada")
                    print(f"  📋 Tabela '{tabela_nome}' criada automaticamente")
                else:
                    # Verifica se há campos novos para adicionar (migração suave)
                    self._migrar_suave(tabela_nome, campos)
            except Exception as e:
                print(f"  ⚠️  Tabela '{tabela_nome}': {e}")

        if novidades:
            print(f"  ✅ Auto-setup concluído: {', '.join(novidades)}")
        else:
            print(f"  ✅ Banco '{dbname}' pronto (já configurado)")

        AdvakDB._AUTO_SETUP_DONE.add(cache_key)
        return len(novidades) > 0

    def _migrar_suave(self, tabela, campos):
        """Adiciona colunas novas sem apagar dados existentes."""
        try:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s",
                (tabela,)
            )
            existentes = {row[0] for row in cur.fetchall()}
            cur.close()

            type_map = self._build_type_map()
            for campo, defn in campos.items():
                if campo == 'id' or campo in existentes:
                    continue
                sql_type = type_map.get(defn.split()[0].lower(), 'TEXT')
                try:
                    self._exec(f'ALTER TABLE "{tabela}" ADD COLUMN "{campo}" {sql_type}')
                    print(f"  ➕ Coluna '{campo}' adicionada a '{tabela}'")
                except Exception:
                    pass  # já existe ou erro de tipo — ignora
        except Exception:
            pass

    def _build_type_map(self):
        return {
            'autonum': 'SERIAL PRIMARY KEY',
            'texto': 'TEXT',
            'inteiro': 'INTEGER',
            'numero': 'NUMERIC',
            'decimal': 'NUMERIC(15,2)',
            'booleano': 'BOOLEAN',
            'data': 'TIMESTAMP DEFAULT NOW()',
            'json': 'JSONB',
            'varchar': 'VARCHAR(255)',
            'float': 'FLOAT',
        }

    # ── Conexão ───────────────────────────────────────────────────────────────

    def conectar(self, dbname=None):
        import psycopg2
        db = dbname or self._cur_db
        self._conn = psycopg2.connect(
            host=self.host, port=self.port,
            user=self.user, password=self.password,
            dbname=db
        )
        self._conn.autocommit = True
        self._cur_db = db
        return f"✅ Conectado ao banco '{db}' em {self.host}:{self.port}"

    def desconectar(self):
        if self._conn:
            self._conn.close()
            self._conn = None
        return "✅ Desconectado"

    def _garantir_conexao(self):
        if self._conn is None or self._conn.closed:
            self.conectar()

    def _exec(self, sql, params=None, fetch=False):
        self._garantir_conexao()
        cur = self._conn.cursor()
        try:
            cur.execute(sql, params)
            if fetch:
                cols = [d[0] for d in cur.description] if cur.description else []
                rows = cur.fetchall()
                # Convert None values to safe defaults in each row
                result = []
                for row in rows:
                    d = {}
                    for col, val in zip(cols, row):
                        d[col] = val if val is not None else ''
                    result.append(d)
                return result
            return cur.rowcount
        except Exception as e:
            if fetch:
                return []
            return 0
        finally:
            try: cur.close()
            except: pass

    # ── Gerenciamento de bancos ───────────────────────────────────────────────

    def criar_banco(self, nome):
        """banco.criar_banco("meu_app")"""
        try:
            self._garantir_conexao()
            cur = self._conn.cursor()
            cur.execute(f'CREATE DATABASE "{nome}"')
            cur.close()
            return f"✅ Banco '{nome}' criado com sucesso"
        except Exception as e:
            if 'already exists' in str(e):
                return f"ℹ️  Banco '{nome}' já existe"
            return f"❌ Erro: {e}"

    def usar(self, nome):
        """banco.usar("meu_app")  — conecta a um banco específico"""
        if self._conn:
            self._conn.close()
        self._cur_db = nome
        return self.conectar(nome)

    def listar_bancos(self):
        """banco.listar_bancos()"""
        self._garantir_conexao()
        rows = self._exec(
            "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname",
            fetch=True
        )
        return [r['datname'] for r in rows]

    def apagar_banco(self, nome):
        """banco.apagar_banco("nome")"""
        try:
            old = self._cur_db
            if self._conn: self._conn.close()
            self.conectar('postgres')
            self._exec(f'DROP DATABASE IF EXISTS "{nome}"')
            if old != nome:
                self.conectar(old)
            return f"✅ Banco '{nome}' removido"
        except Exception as e:
            return f"❌ {e}"

    # ── Tabelas ───────────────────────────────────────────────────────────────

    def criar_tabela(self, nome, campos: dict, sobrescrever=False):
        """
        banco.criar_tabela("usuarios", {
            "id":    "autonum",
            "nome":  "texto obrigatorio",
            "email": "texto unico obrigatorio",
            "idade": "inteiro",
            "ativo": "booleano padrao verdadeiro",
            "criado":"datahora",
        })
        """
        colunas = []
        indices = []
        foreign_keys = []

        for campo, definicao in campos.items():
            col_sql, idx, fk = self._parse_campo(campo, str(definicao))
            colunas.append(col_sql)
            if idx: indices.append(idx)
            if fk:  foreign_keys.append(fk)

        colunas.extend(foreign_keys)
        cols_str = ',\n    '.join(colunas)

        if sobrescrever:
            self._exec(f'DROP TABLE IF EXISTS "{nome}" CASCADE')

        sql = f'CREATE TABLE IF NOT EXISTS "{nome}" (\n    {cols_str}\n)'
        try:
            self._exec(sql)
            for idx_sql in indices:
                self._exec(idx_sql.replace('__TABLE__', nome))
            return f"✅ Tabela '{nome}' criada"
        except Exception as e:
            return f"❌ Erro ao criar tabela: {e}\nSQL: {sql}"

    def _parse_campo(self, nome, definicao):
        """
        Converte 'texto unico obrigatorio' em SQL de coluna.
        Suporta: tipo [unico] [obrigatorio] [padrao valor] [ref outra_tabela]
        """
        partes = definicao.strip().split()
        if not partes:
            return f'"{nome}" TEXT', None, None

        tipo_str = partes[0].lower()
        modificadores = [p.lower() for p in partes[1:]]

        # Tipo base
        pg_tipo = TIPOS.get(tipo_str, 'TEXT')

        # Referência (chave estrangeira)
        fk = None
        if tipo_str == 'ref' and len(partes) > 1:
            tabela_ref = partes[1]
            pg_tipo = 'INTEGER'
            fk = f'FOREIGN KEY ("{nome}") REFERENCES "{tabela_ref}"(id)'
            modificadores = [p.lower() for p in partes[2:]]

        # Monta coluna
        parts_sql = [f'"{nome}"', pg_tipo]

        if 'obrigatorio' in modificadores or 'notnull' in modificadores:
            parts_sql.append('NOT NULL')
        if 'unico' in modificadores or 'unique' in modificadores:
            parts_sql.append('UNIQUE')
        if 'padrao' in modificadores:
            idx_pad = modificadores.index('padrao')
            if idx_pad + 1 < len(modificadores):
                val = modificadores[idx_pad + 1]
                # Traduz valores PT
                val = val.replace('verdadeiro', 'TRUE').replace('falso', 'FALSE').replace('nulo', 'NULL')
                if val not in ('TRUE', 'FALSE', 'NULL') and not val.replace('.','').isdigit():
                    val = f"'{val}'"
                parts_sql.append(f'DEFAULT {val}')

        col_sql = ' '.join(parts_sql)

        # Índice separado
        idx_sql = None
        if 'indice' in modificadores:
            idx_sql = f'CREATE INDEX IF NOT EXISTS idx___TABLE__{nome} ON "__TABLE__"("{nome}")'

        return col_sql, idx_sql, fk

    def apagar_tabela(self, nome, cascata=False):
        cas = 'CASCADE' if cascata else ''
        self._exec(f'DROP TABLE IF EXISTS "{nome}" {cas}')
        return f"✅ Tabela '{nome}' removida"

    def listar_tabelas(self):
        rows = self._exec(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename",
            fetch=True
        )
        return [r['tablename'] for r in rows]

    def descrever_tabela(self, nome):
        rows = self._exec("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (nome,), fetch=True)
        return rows

    def renomear_tabela(self, nome, novo_nome):
        self._exec(f'ALTER TABLE "{nome}" RENAME TO "{novo_nome}"')
        return f"✅ Tabela '{nome}' renomeada para '{novo_nome}'"

    def adicionar_coluna(self, tabela, campo, definicao):
        col_sql, _, _ = self._parse_campo(campo, definicao)
        self._exec(f'ALTER TABLE "{tabela}" ADD COLUMN IF NOT EXISTS {col_sql}')
        return f"✅ Coluna '{campo}' adicionada em '{tabela}'"

    def remover_coluna(self, tabela, campo):
        self._exec(f'ALTER TABLE "{tabela}" DROP COLUMN IF EXISTS "{campo}"')
        return f"✅ Coluna '{campo}' removida de '{tabela}'"

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def inserir(self, tabela, dados: dict):
        """
        banco.inserir("usuarios", {"nome": "Ana", "idade": 25})
        """
        if not dados:
            return "❌ Nenhum dado fornecido"
        cols   = [f'"{k}"' for k in dados.keys()]
        vals   = list(dados.values())
        placeholders = ', '.join(['%s'] * len(vals))
        sql = f'INSERT INTO "{tabela}" ({", ".join(cols)}) VALUES ({placeholders}) RETURNING *'
        try:
            rows = self._exec(sql, vals, fetch=True)
            return rows[0] if rows else {}
        except Exception as e:
            return f"❌ {e}"

    def inserir_varios(self, tabela, lista: list):
        """
        banco.inserir_varios("produtos", [
            {"nome": "A", "preco": 10},
            {"nome": "B", "preco": 20},
        ])
        """
        if not lista:
            return "❌ Lista vazia"
        results = []
        for item in lista:
            r = self.inserir(tabela, item)
            results.append(r)
        return f"✅ {len(results)} registros inseridos"

    def buscar(self, tabela):
        """Inicia uma consulta. Retorna QueryBuilder."""
        return QueryBuilder(self, tabela)

    def buscar_por_id(self, tabela, id_val):
        try:
            rows = self._exec(
                f'SELECT * FROM "{tabela}" WHERE id = %s', (id_val,), fetch=True
            )
            return rows[0] if rows else {}
        except Exception as e:
            return {}

    def atualizar(self, tabela, dados: dict):
        """Inicia atualização. Retorna UpdateBuilder."""
        return UpdateBuilder(self, tabela, dados)

    def deletar(self, tabela):
        """Inicia deleção. Retorna DeleteBuilder."""
        return DeleteBuilder(self, tabela)

    def contar(self, tabela, where=None, params=None):
        sql = f'SELECT COUNT(*) as total FROM "{tabela}"'
        if where: sql += f' WHERE {where}'
        rows = self._exec(sql, params, fetch=True)
        return rows[0]['total'] if rows else 0

    # ── SQL puro ─────────────────────────────────────────────────────────────

    def sql(self, query, params=None):
        """
        banco.sql("SELECT * FROM usuarios WHERE ativo = true")
        banco.sql("UPDATE usuarios SET nome=%s WHERE id=%s", ["Ana", 1])
        """
        try:
            q = query.strip().upper()
            if q.startswith('SELECT') or q.startswith('WITH'):
                return self._exec(query, params, fetch=True)
            else:
                n = self._exec(query, params)
                return f"✅ {n} linha(s) afetada(s)"
        except Exception as e:
            return f"❌ {e}"

    # ── Transações ───────────────────────────────────────────────────────────

    def iniciar_transacao(self):
        self._garantir_conexao()
        self._conn.autocommit = False
        return "🔄 Transação iniciada"

    def confirmar(self):
        self._conn.commit()
        self._conn.autocommit = True
        return "✅ Transação confirmada"

    def reverter(self):
        self._conn.rollback()
        self._conn.autocommit = True
        return "↩️  Transação revertida"

    # ── Migrations ───────────────────────────────────────────────────────────

    def migrar(self, nome, campos: dict):
        """
        Cria ou atualiza tabela de forma segura (adiciona colunas novas).
        banco.migrar("usuarios", {"novo_campo": "texto"})
        """
        tabelas = self.listar_tabelas()
        if nome not in tabelas:
            return self.criar_tabela(nome, campos)

        existentes = {r['column_name'] for r in self.descrever_tabela(nome)}
        adicionadas = []
        for campo, definicao in campos.items():
            if campo not in existentes:
                self.adicionar_coluna(nome, campo, definicao)
                adicionadas.append(campo)

        if adicionadas:
            return f"✅ Migração: colunas adicionadas → {adicionadas}"
        return f"ℹ️  Nenhuma coluna nova em '{nome}'"


# ── Query Builders ────────────────────────────────────────────────────────────

class QueryBuilder:
    def __init__(self, db, tabela):
        self._db      = db
        self._tabela  = tabela
        self._where   = []
        self._params  = []
        self._order   = None
        self._limit   = None
        self._offset  = None
        self._cols    = '*'

    def campos(self, *cols):
        self._cols = ', '.join(f'"{c}"' for c in cols)
        return self

    def onde(self, condicao, *params):
        """
        .onde("nome = %s", "Ana")
        .onde("idade > %s AND ativo = %s", 18, True)
        """
        self._where.append(condicao)
        self._params.extend(params)
        return self

    def ordenar(self, campo, direcao='ASC'):
        self._order = f'"{campo}" {direcao.upper()}'
        return self

    def limite(self, n):
        self._limit = n
        return self

    def pagina(self, num, tamanho=10):
        self._limit  = tamanho
        self._offset = (num - 1) * tamanho
        return self

    def executar(self):
        sql = f'SELECT {self._cols} FROM "{self._tabela}"'
        if self._where:
            sql += ' WHERE ' + ' AND '.join(self._where)
        if self._order:
            sql += f' ORDER BY {self._order}'
        if self._limit is not None:
            sql += f' LIMIT {self._limit}'
        if self._offset is not None:
            sql += f' OFFSET {self._offset}'
        return self._db._exec(sql, self._params or None, fetch=True)

    # Atalho — permite usar sem .executar()
    def __iter__(self):
        return iter(self.executar())

    def __len__(self):
        return len(self.executar())

    def primeiro(self):
        self._limit = 1
        r = self.executar()
        return r[0] if r else None

    def existe(self):
        return self.primeiro() is not None

    def contar(self):
        self._cols = 'COUNT(*) as total'
        r = self.executar()
        return r[0]['total'] if r else 0


class UpdateBuilder:
    def __init__(self, db, tabela, dados):
        self._db     = db
        self._tabela = tabela
        self._dados  = dados
        self._where  = []
        self._params = []

    def onde(self, condicao, *params):
        self._where.append(condicao)
        self._params.extend(params)
        return self

    def executar(self):
        sets    = ', '.join(f'"{k}" = %s' for k in self._dados.keys())
        vals    = list(self._dados.values())
        sql     = f'UPDATE "{self._tabela}" SET {sets}'
        if self._where:
            sql += ' WHERE ' + ' AND '.join(self._where)
            vals.extend(self._params)
        sql += ' RETURNING *'
        try:
            return self._db._exec(sql, vals, fetch=True)
        except Exception as e:
            return f"❌ {e}"


class DeleteBuilder:
    def __init__(self, db, tabela):
        self._db     = db
        self._tabela = tabela
        self._where  = []
        self._params = []

    def onde(self, condicao, *params):
        self._where.append(condicao)
        self._params.extend(params)
        return self

    def executar(self):
        sql = f'DELETE FROM "{self._tabela}"'
        if self._where:
            sql += ' WHERE ' + ' AND '.join(self._where)
        try:
            n = self._db._exec(sql, self._params or None)
            return f"✅ {n} registro(s) removido(s)"
        except Exception as e:
            return f"❌ {e}"
