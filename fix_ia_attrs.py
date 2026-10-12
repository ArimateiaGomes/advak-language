import os

BASE = os.path.dirname(os.path.abspath(__file__))
f = os.path.join(BASE, 'advak_interpreter.py')
content = open(f, encoding='utf-8').read()

fixes = 0

# Fix: add AI attributes to __init__
old = "        self.ai_api_key = ai_api_key"
new = """        self.ai_api_key    = ai_api_key
        self._ai_modelo    = 'llama-3.3-70b-versatile'
        self._ai_contexto  = []
        self._ai_sistema   = None
        self._ai_provedor  = 'groq'
        self._ai_providers = {
            'groq':      {'env': 'GROQ_API_KEY',      'modelos': ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768', 'gemma2-9b-it']},
            'openrouter':{'env': 'OPENROUTER_API_KEY', 'modelos': ['meta-llama/llama-3.3-70b-instruct:free', 'qwen/qwen3-235b-a22b:free', 'deepseek/deepseek-r1-0528:free']},
            'deepseek':  {'env': 'DEEPSEEK_API_KEY',   'modelos': ['deepseek-chat', 'deepseek-reasoner']},
            'gemini':    {'env': 'GEMINI_API_KEY',     'modelos': ['gemini-2.0-flash', 'gemini-1.5-flash']},
        }
        self._loaded_modules = {}"""

if old in content and '_ai_provedor' not in content:
    content = content.replace(old, new, 1)
    print("Fix attrs OK")
    fixes += 1
elif '_ai_provedor' in content:
    print("Attrs already present")
else:
    print("ERRO: init pattern not found")

# Fix: replace _ai_call with multi-model version
if '_ai_call_provider' not in content:
    old_call = """    async def _ai_call(self, prompt, system=None):
        try:
            key = self.ai_api_key or os.environ.get('GROQ_API_KEY', '')
            if not key:
                return '[IA] Defina GROQ_API_KEY no arquivo .env'
            from groq import Groq
            messages = []
            if system:
                messages.append({'role': 'system', 'content': system})
            messages.append({'role': 'user', 'content': str(prompt)})
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=messages,
                max_tokens=2048
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"[Erro IA] {e}" """

    new_call = """    def _ai_set_modelo(self, modelo):
        if modelo: self._ai_modelo = modelo; return f"Modelo: {modelo}"
        return self._ai_modelo

    def _ai_set_provedor(self, provedor):
        if provedor:
            if provedor not in self._ai_providers:
                return f"[IA] Provedor desconhecido: {provedor}"
            self._ai_provedor = provedor
            mods = self._ai_providers[provedor]['modelos']
            if mods: self._ai_modelo = mods[0]
            return f"Provedor: {provedor}, Modelo: {self._ai_modelo}"
        return self._ai_provedor

    def _ai_set_sistema(self, sistema):
        self._ai_sistema = sistema
        return f"Sistema definido"

    def _ai_call_sync(self, prompt, system=None, usar_contexto=True):
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(lambda: __import__('asyncio').run(self._ai_call(prompt, system, usar_contexto)))
            return future.result()

    async def _ai_call(self, prompt, system=None, usar_contexto=True):
        try:
            prov = self._ai_provedor
            pinfo = self._ai_providers.get(prov, {})
            key = self.ai_api_key or os.environ.get(pinfo.get('env','GROQ_API_KEY'), '')
            if not key:
                return f"[IA] Defina {pinfo.get('env','GROQ_API_KEY')} no arquivo .env"
            messages = []
            sys_p = system or self._ai_sistema
            if sys_p: messages.append({'role':'system','content':sys_p})
            if usar_contexto: messages.extend(self._ai_contexto[-10:])
            messages.append({'role':'user','content':str(prompt)})
            resposta = await self._ai_call_provider(prov, key, messages)
            if usar_contexto:
                self._ai_contexto.append({'role':'user','content':str(prompt)})
                self._ai_contexto.append({'role':'assistant','content':resposta})
            return resposta
        except Exception as e:
            return f"[Erro IA] {e}"

    async def _ai_call_provider(self, prov, key, messages):
        modelo = self._ai_modelo
        if prov == 'groq':
            from groq import Groq
            client = Groq(api_key=key)
            resp = client.chat.completions.create(model=modelo, messages=messages, max_tokens=2048)
            return resp.choices[0].message.content
        elif prov in ('openrouter', 'deepseek', 'gemini'):
            import urllib.request
            if prov == 'openrouter':
                url = 'https://openrouter.ai/api/v1/chat/completions'
                hdrs = {'Content-Type':'application/json','Authorization':f'Bearer {key}','HTTP-Referer':'https://advak.dev','X-Title':'Advak'}
            elif prov == 'deepseek':
                url = 'https://api.deepseek.com/chat/completions'
                hdrs = {'Content-Type':'application/json','Authorization':f'Bearer {key}'}
            else:
                url = f'https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={key}'
                parts = '\\n'.join(f"{m['role'].upper()}: {m['content']}" for m in messages)
                payload = {'contents':[{'parts':[{'text':parts}]}],'generationConfig':{'maxOutputTokens':2048}}
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=data, method='POST', headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.loads(r.read())['candidates'][0]['content']['parts'][0]['text']
            payload = {'model':modelo,'messages':messages,'max_tokens':2048}
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST', headers=hdrs)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())['choices'][0]['message']['content']
        raise Exception(f"Provedor desconhecido: {prov}") """

    # Find and replace
    if old_call.strip() in content:
        content = content.replace(old_call.strip(), new_call.strip(), 1)
        print("Fix _ai_call OK")
        fixes += 1
    else:
        # Find _ai_call and replace whole method
        idx = content.find('    async def _ai_call(self, prompt, system=None):')
        if idx != -1:
            end = content.find('\n    async def ', idx+10)
            if end == -1: end = content.find('\n    def ', idx+10)
            old_block = content[idx:end]
            content = content.replace(old_block, new_call.strip() + '\n\n', 1)
            print("Fix _ai_call OK (block replace)")
            fixes += 1
        else:
            print("ERRO: _ai_call not found")
else:
    print("_ai_call_provider already present")

# Add IA object to global scope if missing
if "'IA'" not in content and 'declare(\'IA\'' not in content:
    old_fs = "        # ── Sistema de arquivos"
    new_ia = """        # ── IA Multi-modelo
        _interp_ia = self
        g.declare('IA', {
            'provedor':     lambda p=None: _interp_ia._ai_set_provedor(p),
            'modelo':       lambda m=None: _interp_ia._ai_set_modelo(m),
            'sistema':      lambda s=None: _interp_ia._ai_set_sistema(s),
            'chat':         lambda p: _interp_ia._ai_call_sync(p, usar_contexto=True),
            'sem_contexto': lambda p: _interp_ia._ai_call_sync(p, usar_contexto=False),
            'memoria':      lambda: list(_interp_ia._ai_contexto),
            'limpar':       lambda: _interp_ia._ai_contexto.clear() or 'Contexto limpo',
            'provedores':   lambda: list(_interp_ia._ai_providers.keys()),
            'modelos':      lambda: _interp_ia._ai_providers.get(_interp_ia._ai_provedor, {}).get('modelos', []),
            'info':         lambda: {'provedor':_interp_ia._ai_provedor,'modelo':_interp_ia._ai_modelo,'mensagens':len(_interp_ia._ai_contexto),'sistema':_interp_ia._ai_sistema or '(nenhum)'},
        })

        # ── Sistema de arquivos"""
    if old_fs in content:
        content = content.replace(old_fs, new_ia, 1)
        print("IA scope OK")
        fixes += 1

open(f, 'w', encoding='utf-8').write(content)

try:
    compile(content, f, 'exec')
    print("Syntax OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR linha {e.lineno}: {e.msg}")

cache = os.path.join(BASE, '__pycache__', 'advak_interpreter.cpython-313.pyc')
if os.path.exists(cache): os.remove(cache); print("Cache deleted")

print(f"{fixes} fixes applied.")
