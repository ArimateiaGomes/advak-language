import os

f = open('advak_interpreter.py', encoding='utf-8').read()

f = f.replace(
    'async def _call_fn(self, fn, args, caller_scope, this=None, kwargs=None):',
    'async def _call_fn(self, fn, args, caller_scope, this=None, kwargs=None, owner_class=None):',
    1
)

marker_start = 'if isinstance(this, AdvakInstance) and this.klass.superclass:'
marker_end = "inner.declare('Super', _super_call)"
si = f.find(marker_start)
ei = f.find(marker_end, si) + len(marker_end)

if si == -1:
    print("BLOCO NAO ENCONTRADO")
    idx = f.find('async def _call_fn')
    print(f[idx:idx+600])
else:
    old_block = f[si:ei]
    new_block = (
        "if isinstance(this, AdvakInstance):\n"
        "                oc = owner_class\n"
        "                if oc is None:\n"
        "                    _k = this.klass\n"
        "                    while _k:\n"
        "                        if any(m is fn for m in _k.methods.values()):\n"
        "                            oc = _k\n"
        "                            break\n"
        "                        _k = _k.superclass\n"
        "                _sup = oc.superclass if (oc and oc.superclass) else None\n"
        "                if _sup:\n"
        "                    _ir = self\n"
        "                    _sc = _sup\n"
        "                    async def _super_call(*_a, **_kw):\n"
        "                        for _cn in ('construtor', 'constructor'):\n"
        "                            if _cn in _sc.methods:\n"
        "                                return await _ir._call_fn(_sc.methods[_cn], list(_a), inner, this=this, owner_class=_sc)\n"
        "                        return None\n"
        "                    inner.declare('super', _super_call)\n"
        "                    inner.declare('Super', _super_call)"
    )
    f = f.replace(old_block, new_block, 1)
    print("Fix 2 OK")

f = f.replace(
    'await self._call_fn(klass.methods[cname], args, scope, this=inst)',
    'await self._call_fn(klass.methods[cname], args, scope, this=inst, owner_class=klass)',
    1
)
print("Fix 3 OK")

open('advak_interpreter.py', 'w', encoding='utf-8').write(f)

try:
    compile(open('advak_interpreter.py', encoding='utf-8').read(), 'f', 'exec')
    print("Syntax OK!")
except SyntaxError as e:
    print("SYNTAX ERROR linha", e.lineno, ":", e.msg)

cache = '__pycache__/advak_interpreter.cpython-313.pyc'
if os.path.exists(cache):
    os.remove(cache)
    print("Cache deletado")

print("Done!")