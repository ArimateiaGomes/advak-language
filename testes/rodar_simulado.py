"""
Roda exemplos/11_cache_redis.dk ou exemplos/12_catalogo_mongodb.dk com um Redis e um MongoDB de MENTIRA
(guardados só na memória), porque não há servidor desses bancos neste computador.
Serve para conferir a sintaxe e o jeito de chamar a Advak; NÃO prova que o banco real se comporta igual.

Uso:  python testes/rodar_simulado.py exemplos/11_cache_redis.dk
"""
import os, runpy, sys, types

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
os.environ.update(PYTHONUTF8="1", ADVAK_REDIS_URL="redis://localhost:6379/0", ADVAK_MONGODB_URL="mongodb://localhost:27017/catalogo")


class FakeRedis:
    def __init__(self): self.d = {}
    @classmethod
    def from_url(cls, url, **kw): return cls()
    def ping(self): return True
    def set(self, k, v, ex=None): self.d[k] = str(v)
    def get(self, k): return self.d.get(k)
    def delete(self, *ks): return sum(1 for k in ks if self.d.pop(k, None) is not None)
    def incrby(self, k, n): self.d[k] = str(int(self.d.get(k, 0)) + n); return int(self.d[k])
    def close(self): pass


OPS = {"$gt": lambda a, b: a > b, "$gte": lambda a, b: a >= b, "$lt": lambda a, b: a < b,
       "$lte": lambda a, b: a <= b, "$ne": lambda a, b: a != b}


def casa(doc, filtro):
    for k, v in filtro.items():
        if isinstance(v, dict):
            if not all(OPS[o](doc.get(k), x) for o, x in v.items()):
                return False
        elif doc.get(k) != v:
            return False
    return True


class Cursor(list):
    def sort(self, o):
        for campo, sentido in reversed(o if isinstance(o, list) else [o]):
            self[:] = sorted(self, key=lambda d: d.get(campo), reverse=sentido < 0)
        return self
    def skip(self, n): self[:] = self[n:]; return self
    def limit(self, n): self[:] = self[:n] if n else self; return self


class Colecao:
    def __init__(self): self.docs, self.n = [], 0
    def insert_one(self, d):
        self.n += 1; d["_id"] = "id%03d" % self.n; self.docs.append(d)
        return types.SimpleNamespace(inserted_id=d["_id"])
    def find(self, f, campos=None): return Cursor(dict(d) for d in self.docs if casa(d, f))
    def update_many(self, f, u):
        alvo = [d for d in self.docs if casa(d, f)]
        for d in alvo: d.update(u["$set"])
        return types.SimpleNamespace(modified_count=len(alvo))
    def delete_many(self, f):
        antes = len(self.docs); self.docs[:] = [d for d in self.docs if not casa(d, f)]
        return types.SimpleNamespace(deleted_count=antes - len(self.docs))
    def count_documents(self, f): return len(self.find(f))


cols = {}
class BancoMongo:
    def __getitem__(s, nome): return cols.setdefault(nome, Colecao())
    def list_collection_names(s): return list(cols)
    def command(s, d): return {"ok": 1}
class ClienteMongo:
    def __init__(s, url, **kw): pass
    def __getitem__(s, nome): return BancoMongo()
    def close(s): pass

r = types.ModuleType("redis"); r.Redis = FakeRedis; sys.modules["redis"] = r
m = types.ModuleType("pymongo"); m.MongoClient = ClienteMongo; sys.modules["pymongo"] = m

sys.argv = ["advak.py", sys.argv[1]]
runpy.run_path(os.path.join(RAIZ, "advak.py"), run_name="__main__")
