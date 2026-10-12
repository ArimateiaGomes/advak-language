import os

BASE = os.path.dirname(os.path.abspath(__file__))
interp_file = os.path.join(BASE, 'advak_interpreter.py')
content = open(interp_file, encoding='utf-8').read()

# The fix: in eval(), handle getter BEFORE calling _get_member
# Line 656-658:
#   if t == 'member':
#       obj = await self.eval(node['obj'], scope)
#       return self._get_member(obj, node['prop'])
#
# Change to: check getters first (await is fine here since we're in async eval)

old = """        if t == 'member':
            obj  = await self.eval(node['obj'], scope)
            return self._get_member(obj, node['prop'])

        if t == 'optional_member':
            obj = await self.eval(node['obj'], scope)
            if obj is None: return None
            return self._get_member(obj, node['prop'])"""

new = """        if t == 'member':
            obj  = await self.eval(node['obj'], scope)
            prop = node['prop']
            if isinstance(obj, AdvakInstance):
                k = obj.klass
                while k:
                    if prop in k.getters:
                        return await self._call_fn(k.getters[prop], [], scope, this=obj)
                    k = k.superclass
            return self._get_member(obj, prop)

        if t == 'optional_member':
            obj = await self.eval(node['obj'], scope)
            if obj is None: return None
            prop = node['prop']
            if isinstance(obj, AdvakInstance):
                k = obj.klass
                while k:
                    if prop in k.getters:
                        return await self._call_fn(k.getters[prop], [], scope, this=obj)
                    k = k.superclass
            return self._get_member(obj, prop)"""

if old in content:
    content = content.replace(old, new)
    print("Fix OK: getter handled in async eval before _get_member")
else:
    print("ERRO: padrao nao encontrado")
    # Show what's there
    for i, line in enumerate(content.splitlines(), 1):
        if "t == 'member'" in line:
            lines = content.splitlines()
            for j in range(i-1, min(len(lines), i+5)):
                print(f"  {j+1}: {lines[j]}")

# Also clean up the _PendingGetter mess in _get_member
old_pending = """        if isinstance(obj, AdvakInstance):
            # Check getters first ù return a special coroutine marker
            k = obj.klass
            while k:
                if prop in k.getters:
                    getter_fn = k.getters[prop]
                    getter_inst = obj
                    # Return a special object that eval will await
                    class _PendingGetter:
                        def __init__(self2): self2.fn = getter_fn; self2.inst = getter_inst
                    return _PendingGetter()
                k = k.superclass
            return obj.get(prop)"""

new_clean = """        if isinstance(obj, AdvakInstance):
            return obj.get(prop)"""

if old_pending in content:
    content = content.replace(old_pending, new_clean)
    print("Cleaned _PendingGetter from _get_member")

open(interp_file, 'w', encoding='utf-8').write(content)

# Verify syntax
try:
    compile(open(interp_file, encoding='utf-8').read(), interp_file, 'exec')
    print("Syntax OK!")
except SyntaxError as e:
    print(f"ERRO linha {e.lineno}: {e.msg}")

# Delete cache
cache_dir = os.path.join(BASE, '__pycache__')
if os.path.exists(cache_dir):
    for f in os.listdir(cache_dir):
        if 'advak_interpreter' in f:
            os.remove(os.path.join(cache_dir, f))
            print(f"Cache deletado: {f}")

print("Pronto! Rode: python advak.py projetos run classes_demo.dk")
