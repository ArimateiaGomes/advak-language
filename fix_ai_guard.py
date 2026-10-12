import os
BASE = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(BASE, 'advak_interpreter.py')
content = open(f, encoding='utf-8').read()

old = "    async def _ai_call(self, prompt, system=None, usar_contexto=True):\n        try:\n            prov = self._ai_provedor"
new = """    async def _ai_call(self, prompt, system=None, usar_contexto=True):
        # Garante atributos mesmo em instâncias legadas
        if not hasattr(self, '_ai_provedor'):
            self._ai_provedor  = 'groq'
            self._ai_modelo    = 'llama-3.3-70b-versatile'
            self._ai_contexto  = []
            self._ai_sistema   = None
            self._ai_providers = {'groq':{'env':'GROQ_API_KEY','modelos':['llama-3.3-70b-versatile']}}
        try:
            prov = self._ai_provedor"""

if old in content:
    content = content.replace(old, new, 1)
    open(f, 'w', encoding='utf-8').write(content)
    print("Fix OK")
else:
    print("ERRO - not found")

cache = os.path.join(BASE, '__pycache__', 'advak_interpreter.cpython-313.pyc')
if os.path.exists(cache): os.remove(cache); print("Cache deleted")
print("Done!")
