"""
Teste de ponta a ponta SEM internet e SEM chave: sobe um servidor HTTP falso em localhost que imita
o Ollama e roda testes/ia_local.dk pelo interpretador de verdade (python advak.py ...).

Rodar:  python -I testes/test_ia_local.py
"""
import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OllamaFalso(BaseHTTPRequestHandler):
    corpos = []

    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
        OllamaFalso.corpos.append((self.path, corpo))
        ultima = [m for m in corpo['messages'] if m['role'] == 'user'][-1]['content']
        resposta = json.dumps({'message': {'role': 'assistant', 'content': f'eco: {ultima}'}}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(resposta)))
        self.end_headers()
        self.wfile.write(resposta)

    def log_message(self, *a):
        pass


class TesteIALocal(unittest.TestCase):
    def test_programa_dk_conversa_com_ollama_falso(self):
        srv = HTTPServer(('127.0.0.1', 0), OllamaFalso)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            env = {k: v for k, v in os.environ.items() if not (k.startswith('ADVAK_') and k.endswith('_API_KEY'))}
            env.update({'ADVAK_OLLAMA_URL': f'http://127.0.0.1:{srv.server_port}', 'PYTHONUTF8': '1'})
            p = subprocess.run([sys.executable, 'advak.py', os.path.join('testes', 'ia_local.dk')], cwd=RAIZ,
                               capture_output=True, timeout=60, env=env, stdin=subprocess.DEVNULL)
        finally:
            srv.shutdown()
            srv.server_close()
        saida = p.stdout.decode('utf-8', 'ignore')
        erro = p.stderr.decode('utf-8', 'ignore')
        self.assertIn('RESPOSTA: eco: Diga oi', saida, saida + erro)
        self.assertIn('CONVERSA: eco: segunda', saida)
        self.assertIn('HISTORICO: 4', saida)
        self.assertIn('ERRO-PROVEDOR:', saida)
        self.assertIn('não está conectado', saida)
        # o servidor recebeu o prompt de sistema e o histórico da conversa
        caminhos = {c for c, _ in OllamaFalso.corpos}
        self.assertEqual(caminhos, {'/api/chat'})
        self.assertEqual(OllamaFalso.corpos[0][1]['messages'][0], {'role': 'system', 'content': 'Seja breve'})
        self.assertEqual([m['content'] for m in OllamaFalso.corpos[-1][1]['messages']],
                         ['primeira', 'eco: primeira', 'segunda'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
