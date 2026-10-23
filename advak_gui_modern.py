"""
Advak GUI Modern — Componentes Avançados de Interface

Usa ttkbootstrap (se disponível) para tema moderno,
com fallback inteligente para tkinter puro.

Recursos adicionados:
  - gui.tema("escuro"|"claro"|"azul"|"verde"|"roxo")
  - gui.toast(msg, tipo)          — notificação flutuante
  - gui.modal(titulo, conteudo)   — dialog customizado
  - gui.grafico(pai, dados, tipo) — gráfico matplotlib embutido
  - gui.calendario(pai)           — seletor de data
  - gui.slider(pai, min, max)     — controle deslizante
  - gui.switch(pai, texto)        — toggle moderno
  - gui.badge(pai, texto, cor)    — badge/tag colorida
  - gui.card(pai, titulo, corpo)  — card elevado
  - gui.busca(pai, lista, fn)     — campo com autocomplete
  - gui.tabela_editavel(pai, cols)— tabela com edição inline
  - gui.arvore(pai, dados)        — tree view hierárquico
  - gui.barra_status(jan, msg)    — barra de status inferior
  - gui.splitter(pai)             — divisor redimensionável
  - gui.icone(nome)               — emoji como ícone
  - gui.cor_hex(nome)             — resolve nome para hex
"""

import os, sys, threading, time, json, queue
from datetime import datetime, date

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, colorchooser
    TKINTER_OK = True
except ImportError:
    TKINTER_OK = False

# Tenta ttkbootstrap para temas modernos
try:
    import ttkbootstrap as tbs
    from ttkbootstrap.constants import *
    BOOTSTRAP_OK = True
except ImportError:
    BOOTSTRAP_OK = False

# Matplotlib — importado sob demanda (lazy) para evitar 1s+ de startup
MATPLOTLIB_OK = None  # None = não testado ainda, True/False = testado

def _get_matplotlib():
    global MATPLOTLIB_OK
    if MATPLOTLIB_OK is None:
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            MATPLOTLIB_OK = True
        except ImportError:
            MATPLOTLIB_OK = False
    return MATPLOTLIB_OK

def _sanitizar_cor(cor, padrao='#000000'):
    """Garante que cor é uma string de cor válida para tkinter."""
    if cor is None: return padrao
    if not isinstance(cor, str): return padrao
    if cor.startswith('#'): return cor
    # Cores nomeadas comuns aceitas pelo tkinter
    cores_validas = {'white','black','red','green','blue','yellow','orange',
                     'purple','pink','gray','grey','cyan','magenta','brown'}
    if cor.lower() in cores_validas: return cor
    return padrao

def _check():
    if not TKINTER_OK:
        raise RuntimeError("tkinter não instalado. Linux: sudo apt install python3-tk")

# ── Paleta de cores moderna ─────────────────────────────────────────────────
PALETA = {
    # Primárias
    'azul':      '#2563EB', 'azul_claro': '#3B82F6', 'azul_escuro': '#1D4ED8',
    'verde':     '#16A34A', 'verde_claro':'#22C55E', 'verde_escuro':'#15803D',
    'vermelho':  '#DC2626', 'vermelho_claro':'#EF4444',
    'amarelo':   '#CA8A04', 'amarelo_claro': '#EAB308',
    'roxo':      '#7C3AED', 'roxo_claro':  '#8B5CF6',
    'rosa':      '#DB2777', 'laranja':     '#EA580C',
    'ciano':     '#0891B2', 'cinza':       '#6B7280',
    # Neutros
    'branco':    '#FFFFFF', 'preto':       '#111827',
    'cinza_100': '#F3F4F6', 'cinza_200':   '#E5E7EB',
    'cinza_700': '#374151', 'cinza_800':   '#1F2937',
    'cinza_900': '#111827',
    # Semânticas
    'sucesso':   '#16A34A', 'erro':        '#DC2626',
    'aviso':     '#CA8A04', 'info':        '#2563EB',
}

TEMAS = {
    'claro': {
        'bg':         '#F8FAFC', 'bg2':        '#FFFFFF',
        'fg':         '#1E293B', 'fg2':        '#64748B',
        'border':     '#E2E8F0', 'accent':     '#2563EB',
        'btn_bg':     '#2563EB', 'btn_fg':     '#FFFFFF',
        'input_bg':   '#FFFFFF', 'input_fg':   '#1E293B',
        'table_head': '#F1F5F9', 'table_row':  '#FFFFFF',
        'table_alt':  '#F8FAFC', 'select':     '#DBEAFE',
        'sidebar':    '#1E293B', 'sidebar_fg': '#94A3B8',
        'campo_bg':   '#FFFFFF', 'selecao':    '#DBEAFE',
        'borda':      '#E2E8F0',
    },
    'escuro': {
        'bg':         '#0F172A', 'bg2':        '#1E293B',
        'fg':         '#F1F5F9', 'fg2':        '#94A3B8',
        'border':     '#334155', 'accent':     '#3B82F6',
        'btn_bg':     '#3B82F6', 'btn_fg':     '#FFFFFF',
        'input_bg':   '#1E293B', 'input_fg':   '#F1F5F9',
        'table_head': '#1E293B', 'table_row':  '#0F172A',
        'table_alt':  '#1E293B', 'select':     '#1D4ED8',
        'sidebar':    '#0F172A', 'sidebar_fg': '#64748B',
        'campo_bg':   '#1E293B', 'selecao':    '#1D4ED8',
        'borda':      '#334155',
    },
    'roxo': {
        'bg':         '#FAF5FF', 'bg2':        '#FFFFFF',
        'fg':         '#3B0764', 'fg2':        '#7C3AED',
        'border':     '#E9D5FF', 'accent':     '#7C3AED',
        'btn_bg':     '#7C3AED', 'btn_fg':     '#FFFFFF',
        'input_bg':   '#FFFFFF', 'input_fg':   '#3B0764',
        'table_head': '#F3E8FF', 'table_row':  '#FFFFFF',
        'table_alt':  '#FAF5FF', 'select':     '#EDE9FE',
        'sidebar':    '#3B0764', 'sidebar_fg': '#C4B5FD',
    },
    'verde': {
        'bg':         '#F0FDF4', 'bg2':        '#FFFFFF',
        'fg':         '#14532D', 'fg2':        '#16A34A',
        'border':     '#BBF7D0', 'accent':     '#16A34A',
        'btn_bg':     '#16A34A', 'btn_fg':     '#FFFFFF',
        'input_bg':   '#FFFFFF', 'input_fg':   '#14532D',
        'table_head': '#DCFCE7', 'table_row':  '#FFFFFF',
        'table_alt':  '#F0FDF4', 'select':     '#BBF7D0',
        'sidebar':    '#14532D', 'sidebar_fg': '#86EFAC',
    },
}

_tema_atual = 'claro'
_root_ref   = None

# Fila de tarefas GUI — permite que threads secundárias executem código tkinter
# na main thread de forma segura
import queue as _queue_module
_gui_task_queue = _queue_module.Queue()

def _t(chave):
    return TEMAS.get(_tema_atual, TEMAS['claro']).get(chave, '#000000')


_gui_instance = None  # Module-level singleton for _get_member access

# ── Canvas 2D em português (gui.canvas) ─────────────────────────────────────
# Origem (0, 0) no canto superior esquerdo; x cresce para a direita e y para BAIXO.
CORES_CANVAS = {
    'preto': '#000000', 'branco': '#ffffff', 'vermelho': '#e53935', 'azul': '#1e66f5',
    'verde': '#2e9e44', 'amarelo': '#f9d71c', 'laranja': '#fb8c00', 'roxo': '#8e44ad',
    'cinza': '#808080', 'rosa': '#ff69b4', 'marrom': '#8b5a2b',
}


def _erro_canvas(msg):
    from advak_interpreter import AdvakError     # import tardio: a GUI só é carregada pelo interpretador
    return AdvakError(msg)


def _cor_canvas(cor):
    if isinstance(cor, str):
        c = cor.strip().lower()
        if c in CORES_CANVAS:
            return CORES_CANVAS[c]
        if len(c) == 7 and c[0] == '#' and all(h in '0123456789abcdef' for h in c[1:]):
            return c
    raise _erro_canvas(f"Cor desconhecida: {cor!r}. Use um destes nomes: {', '.join(CORES_CANVAS)} "
                       f"ou um valor hexadecimal como \"#ff8800\".")


def _num_canvas(valor, nome):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise _erro_canvas(f"'{nome}' deve ser um número, mas recebeu {valor!r}.")
    return valor


def _positivo_canvas(valor, nome, minimo=0):
    _num_canvas(valor, nome)
    if valor < minimo:
        raise _erro_canvas(f"'{nome}' não pode ser menor que {minimo} (recebeu {valor}).")
    return valor


# ── Tratadores (callbacks) ───────────────────────────────────────────────────
# Cada tratador .dk roda fora da thread da janela. Antes: uma thread por chamada e `except: pass`, então dois
# tratadores corriam juntos e o erro de um sumia. Agora há uma fila (um por vez, na ordem de chegada) e o erro
# aparece uma vez no stderr. Chave de segurança: False volta a uma thread por chamada (o erro continua visível).
_SERIALIZAR_CALLBACKS = True


def _janela_ja_fechou(e):
    """Chamar o Tk depois do destroy levanta RuntimeError/TclError: é a janela que fechou, não erro do programa."""
    visto = set()
    while e is not None and id(e) not in visto:
        visto.add(id(e))
        t = str(e)
        if ('main thread is not in main loop' in t or 'application has been destroyed' in t
                or 'invalid command name' in t):
            return True
        e = e.__cause__ or e.__context__
    return False


class _Despachante:
    """Roda os tratadores .dk (um por vez) e mostra o erro de cada um uma única vez."""

    def __init__(self):
        self._fila = queue.Queue()
        self._cond = threading.Condition()
        self._pendentes = 0
        self._trabalhador = None
        self._vistos = set()
        self._total = 0

    def enviar(self, fn, args, origem=None):
        with self._cond:
            self._pendentes += 1
            if _SERIALIZAR_CALLBACKS:
                self._fila.put((fn, args, origem))
                if self._trabalhador is None:
                    self._trabalhador = threading.Thread(target=self._trabalhar, daemon=True)
                    self._trabalhador.start()
                return
        threading.Thread(target=self._rodar, args=(fn, args, origem), daemon=True).start()

    def _trabalhar(self):
        while True:
            self._rodar(*self._fila.get())

    def _rodar(self, fn, args, origem):
        import asyncio, warnings
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='coroutine.*never awaited')
        interp = None
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            from advak_interpreter import AdvakInterpreter
            interp = AdvakInterpreter.__new__(AdvakInterpreter)
            interp.ast = []
            interp.global_scope = fn.closure
            interp.ai_api_key   = getattr(fn.closure, '_ai_key', None)
            interp.db           = getattr(fn.closure, '_db', None)
            loop.run_until_complete(interp._call_fn(fn, args, fn.closure))
        except Exception as e:
            if not _janela_ja_fechou(e):
                self._relatar(e, fn, origem, getattr(interp, '_current_line', None))
        finally:
            loop.close()
            with self._cond:
                self._pendentes -= 1
                self._cond.notify_all()

    def _relatar(self, e, fn, origem, linha):
        import re
        msg = re.sub(r'\s*\(linha \d+\)\s*$', '', str(e) or type(e).__name__).strip()
        origem = origem or (f"tratador '{fn.name}'" if getattr(fn, 'name', None) else 'tratador')
        with self._cond:
            self._total += 1
            chave = (origem, msg, linha)
            if chave in self._vistos:
                return
            self._vistos.add(chave)
        texto = f"❌ Erro em {origem}: {msg}" + (f" (linha {linha})" if linha else "") + "\n"
        try:
            sys.stderr.write(texto)
        except UnicodeEncodeError:
            sys.stderr.write(texto.encode('ascii', 'replace').decode('ascii'))
        except Exception:
            pass

    def esperar(self, limite):
        with self._cond:
            return self._cond.wait_for(lambda: self._pendentes == 0, limite)

    def resumo(self):
        """(erros no total, erros diferentes)"""
        with self._cond:
            return self._total, len(self._vistos)


class Tela:
    """Área de desenho 2D. Cada desenho devolve um número de item para mover ou apagar."""

    def __init__(self, canvas, gui=None):
        self.widget = canvas      # atalho avançado e provisório: expõe o tkinter (bind etc.)
        self._gui = gui           # quem roda os tratadores (ao_clicar, ao_soltar)
        self._ligados = {}        # sequência do Tk -> id da ligação, para trocar o tratador
        self._imagens = {}        # caminho absoluto -> PhotoImage (o Tk apaga a imagem se ninguém a guardar)

    def _item(self, item):
        if isinstance(item, bool) or not isinstance(item, int) or not self.widget.find_withtag(item):
            raise _erro_canvas(f"O item {item!r} não existe nesta tela (já foi apagado ou nunca foi criado).")
        return item

    def retangulo(self, x, y, largura, altura, cor, preenchido=True):
        _num_canvas(x, 'x'); _num_canvas(y, 'y')
        _positivo_canvas(largura, 'largura'); _positivo_canvas(altura, 'altura')
        c = _cor_canvas(cor)
        return self.widget.create_rectangle(x, y, x + largura, y + altura, outline=c, fill=c if preenchido else '')

    def circulo(self, x, y, raio, cor, preenchido=True):
        _num_canvas(x, 'x'); _num_canvas(y, 'y'); _positivo_canvas(raio, 'raio')
        c = _cor_canvas(cor)
        return self.widget.create_oval(x - raio, y - raio, x + raio, y + raio, outline=c, fill=c if preenchido else '')

    def linha(self, x1, y1, x2, y2, cor, espessura=1):
        for v, n in ((x1, 'x1'), (y1, 'y1'), (x2, 'x2'), (y2, 'y2')):
            _num_canvas(v, n)
        _positivo_canvas(espessura, 'espessura', 1)
        return self.widget.create_line(x1, y1, x2, y2, fill=_cor_canvas(cor), width=espessura)

    def texto(self, x, y, texto, cor, tamanho=12):
        _num_canvas(x, 'x'); _num_canvas(y, 'y'); _positivo_canvas(tamanho, 'tamanho', 1)
        return self.widget.create_text(x, y, text=str(texto), fill=_cor_canvas(cor),
                                       font=('Segoe UI', int(tamanho)), anchor='nw')

    def _carregar(self, caminho):
        """Valida o caminho de um PNG e devolve o PhotoImage (do cache, se o arquivo já foi lido)."""
        from advak_interpreter import pasta_do_programa     # import tardio, como _erro_canvas
        if not isinstance(caminho, str):
            raise _erro_canvas(f"'caminho' deve ser um texto, mas recebeu {caminho!r}.")
        if not caminho.lower().endswith('.png'):
            raise _erro_canvas(f"Formato de imagem não suportado: '{caminho}'. Só PNG (.png) é aceito.")
        absoluto = caminho if os.path.isabs(caminho) else os.path.normpath(os.path.join(pasta_do_programa(), caminho))
        if os.path.isdir(absoluto):
            raise _erro_canvas(f"'{caminho}' é uma pasta, não um arquivo de imagem.")
        if not os.path.isfile(absoluto):
            raise _erro_canvas(f"Imagem não encontrada: '{caminho}' (procurei em {absoluto}).")
        img = self._imagens.get(absoluto)
        if img is None:
            try:
                img = tk.PhotoImage(master=self.widget, file=absoluto)
            except tk.TclError:
                raise _erro_canvas(f"Não consegui ler a imagem '{caminho}': o arquivo está corrompido ou não é um PNG válido.")
            self._imagens[absoluto] = img
        return img

    def imagem(self, x, y, caminho):
        _num_canvas(x, 'x'); _num_canvas(y, 'y')
        return self.widget.create_image(x, y, image=self._carregar(caminho), anchor='nw')

    _NOME_TIPO = {'rectangle': 'um retângulo', 'oval': 'um círculo', 'line': 'uma linha', 'text': 'um texto'}

    def trocar_imagem(self, item, caminho):
        self._item(item)
        tipo = self.widget.type(item)
        if tipo != 'image':
            raise _erro_canvas(f"O item {item} não é uma imagem (é {self._NOME_TIPO.get(tipo, f'do tipo {tipo!r}')}).")
        self.widget.itemconfigure(item, image=self._carregar(caminho))     # se o caminho falhar, o item não muda

    def _caixa(self, item):
        if self.widget.type(item) in ('rectangle', 'oval'):     # o bbox do Tk soma 1 px de contorno por lado
            x1, y1, x2, y2 = self.widget.coords(item)
            return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
        return self.widget.bbox(item)

    def colide(self, a, b):
        """Colisão por retângulo; encostar não conta. Para linha e texto vale o bbox do Tk, um pouco maior que o desenho."""
        self._item(a); self._item(b)
        if a == b:
            return True
        ax1, ay1, ax2, ay2 = self._caixa(a)
        bx1, by1, bx2, by2 = self._caixa(b)
        return ax1 < bx2 and bx1 < ax2 and ay1 < by2 and by1 < ay2

    def para_frente(self, item):
        self.widget.tag_raise(self._item(item))

    def para_tras(self, item):
        self.widget.tag_lower(self._item(item))

    def mover(self, item, dx, dy):
        self._item(item); _num_canvas(dx, 'dx'); _num_canvas(dy, 'dy')
        self.widget.move(item, dx, dy)

    def apagar(self, item):
        self.widget.delete(self._item(item))

    def limpar(self):
        self.widget.delete('all')

    def quantidade(self):
        return len(self.widget.find_all())

    def _ponto(self, evento):
        # canvasx/canvasy: a coordenada do desenho (a mesma dos itens), mesmo que o canvas tenha rolagem
        return {"x": int(round(self.widget.canvasx(evento.x))), "y": int(round(self.widget.canvasy(evento.y)))}

    def _ligar(self, sequencia, tratador, origem):
        if self._gui is None:
            raise _erro_canvas("Esta tela não foi criada por gui.canvas, então não tem tratadores de mouse.")
        if sequencia in self._ligados:
            self.widget.unbind(sequencia, self._ligados[sequencia])      # o tratador novo substitui o anterior
        # add='+': não apaga um bind que o programa tenha feito em area.widget para a mesma sequência
        self._ligados[sequencia] = self.widget.bind(
            sequencia, lambda e: self._gui._chamar(tratador, self._ponto(e), origem=origem), add='+')

    def ao_clicar(self, tratador):
        """Chama `tratador` com {x, y} quando o botão esquerdo do mouse é pressionado sobre a tela."""
        self._ligar('<ButtonPress-1>', tratador, 'tratador de clique na tela')

    def ao_soltar(self, tratador):
        """Chama `tratador` com {x, y} quando o botão esquerdo do mouse é solto sobre a tela."""
        self._ligar('<ButtonRelease-1>', tratador, 'tratador de soltar na tela')


# Nomes das teclas que o programa recebe em português; as outras seguem o nome do Tk (a, A, F1, ccedilla...).
_NOMES_TECLA = {'Left': 'esquerda', 'Right': 'direita', 'Up': 'cima', 'Down': 'baixo',
                'space': 'espaco', 'Return': 'enter', 'Escape': 'esc'}


class AdvakGUIModern:
    """
    GUI Moderno para Advak Language.
    Substitui advak_gui.py com componentes avançados.
    """

    def __init__(self):
        global _root_ref, _gui_instance
        _gui_instance = self
        self._root      = None
        self._tema_nome = 'claro'
        self._toasts    = []
        self._style     = None
        self._despachante = _Despachante()
        self._tratador_tecla = None
        self._tecla_ligada = False

    # ── Janela principal ──────────────────────────────────────────────────────

    def _processar_fila_gui(self):
        """Processa tarefas GUI pendentes da fila. Chamado periodicamente."""
        try:
            while True:
                task = _gui_task_queue.get_nowait()
                try:
                    task()
                except Exception as e:
                    pass  # não interrompe o loop por erro em tarefa
        except:
            pass  # fila vazia
        if self._root:
            try:
                self._root.after(50, self._processar_fila_gui)
            except Exception:
                pass

    def janela(self, titulo='Advak App', largura=900, altura=650,
               tema='claro', redimensionavel=True):
        _check()
        global _root_ref, _tema_atual
        _tema_atual = tema
        self._tema_nome = tema

        if self._root is None:
            self._root = tk.Tk()
            _root_ref  = self._root
        else:
            # Secondary window — save main root, create Toplevel
            _main = self._root
            top   = tk.Toplevel(_main)
            top.title(titulo)
            top.geometry(f'{largura}x{altura}')
            if not redimensionavel:
                top.resizable(False, False)
            self._aplicar_tema_global(top)
            # Restore main root so subsequent gui calls still work
            self._root = _main
            return top

        self._root.title(titulo)
        self._root.geometry(f'{largura}x{altura}')
        if not redimensionavel:
            self._root.resizable(False, False)

        self._aplicar_tema_global(self._root)
        self._style = ttk.Style(self._root)
        self._configurar_estilo()

        # Atalho de teclado para tema escuro/claro
        self._root.bind('<F11>', lambda e: self._toggle_tema())
        # Inicia o processador de tarefas GUI (para advak_executar thread-safe)
        self._root.after(50, self._processar_fila_gui)

        win = self._root
        win.titulo      = lambda t: win.title(t)
        win.fechar      = win.destroy
        win.centralizar = lambda: self._centralizar(win)
        win.ao_fechar   = lambda fn: win.protocol("WM_DELETE_WINDOW", fn)
        win.tema        = lambda t: self.tema(t)
        win.maximizar   = lambda: win.state('zoomed')
        win._frame      = win
        win.clipboard_clear  = self._root.clipboard_clear
        win.clipboard_append = self._root.clipboard_append

        frame = tk.Frame(win, bg=_t('bg'))
        frame.pack(fill='both', expand=True)
        win._frame = frame
        return win

    def _centralizar(self, win):
        win.update_idletasks()
        w  = win.winfo_width()
        h  = win.winfo_height()
        if w <= 1: w = 900
        if h <= 1: h = 650
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')

    def _aplicar_tema_global(self, root):
        root.configure(bg=_t('bg'))

    def _configurar_estilo(self):
        s = self._style
        s.theme_use('clam')
        bg  = _t('bg');  bg2 = _t('bg2'); fg  = _t('fg')
        fg2 = _t('fg2'); acc = _t('accent'); brd = _t('border')

        s.configure('.', background=bg, foreground=fg,
                    font=('Segoe UI', 10), bordercolor=brd)
        s.configure('TFrame',    background=bg)
        s.configure('TLabel',    background=bg, foreground=fg)
        s.configure('TButton',
            background=acc, foreground='white',
            padding=(12, 6), relief='flat', borderwidth=0,
            font=('Segoe UI', 10, 'bold'))
        s.map('TButton',
            background=[('active', '#1D4ED8' if 'azul' in _t('accent') else acc),
                        ('disabled', '#E2E8F0')],
            foreground=[('disabled', '#334155')])
        s.configure('Secondary.TButton',
            background='#E2E8F0', foreground='#334155')
        s.configure('Danger.TButton',
            background=PALETA['vermelho'], foreground='white')
        s.configure('Success.TButton',
            background=PALETA['verde'], foreground='white')
        s.configure('TEntry',
            fieldbackground=_t('input_bg'), foreground=_t('input_fg'),
            bordercolor=brd, padding=6, relief='flat')
        s.configure('TCombobox',
            fieldbackground=_t('input_bg'), foreground=_t('input_fg'),
            selectbackground=acc)
        s.configure('TNotebook',    background=bg, borderwidth=0)
        s.configure('TNotebook.Tab',
            background='#E2E8F0' if self._tema_nome == 'claro' else _t('bg2'),
            foreground=fg2, padding=(16, 8), font=('Segoe UI', 10))
        s.map('TNotebook.Tab',
            background=[('selected', bg2)],
            foreground=[('selected', acc)])
        s.configure('Treeview',
            background=_t('table_row'), foreground=fg,
            fieldbackground=_t('table_row'), rowheight=32,
            font=('Segoe UI', 10))
        s.configure('Treeview.Heading',
            background=_t('table_head'), foreground=fg,
            font=('Segoe UI', 10, 'bold'), relief='flat')
        s.map('Treeview',
            background=[('selected', acc)],
            foreground=[('selected', 'white')])
        s.configure('TProgressbar',
            background=acc, troughcolor=_t('border'),
            thickness=8)
        s.configure('Horizontal.TScale',
            background=bg, troughcolor=brd)
        s.configure('TCheckbutton', background=bg, foreground=fg)
        s.configure('TScrollbar',
            background=brd, troughcolor=bg, arrowcolor=fg2)

    def _toggle_tema(self):
        global _tema_atual
        if _tema_atual == 'claro': self.tema('escuro')
        else: self.tema('claro')

    # ── Tema ──────────────────────────────────────────────────────────────────

    def tema(self, nome):
        global _tema_atual
        if nome not in TEMAS: nome = 'claro'
        _tema_atual = nome
        self._tema_nome = nome
        if self._root:
            self._aplicar_tema_global(self._root)
            self._configurar_estilo()
            self._recolorir_widgets(self._root)

    def _recolorir_widgets(self, widget):
        try:
            cls = widget.winfo_class()
            if cls in ('Frame', 'Toplevel', 'Tk'):
                widget.configure(bg=_t('bg'))
            elif cls == 'Label':
                widget.configure(bg=_t('bg'), fg=_t('fg'))
        except: pass
        for child in widget.winfo_children():
            self._recolorir_widgets(child)

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _get_frame(self, pai):
        if hasattr(pai, '_frame'): return pai._frame
        return pai

    def _esperar_tratadores(self, limite=5.0):
        """True quando não há mais tratador rodando nem na fila; False se estourar o limite (segundos)."""
        return self._despachante.esperar(limite)

    def _linha_resumo_erros(self):
        total, diferentes = self._despachante.resumo()
        if not total:
            return ""
        return (f"⚠ {total} {'erro' if total == 1 else 'erros'} em tratadores "
                f"({diferentes} {'diferente' if diferentes == 1 else 'diferentes'}).")

    def _chamar(self, fn, arg=None, origem=None):
        import asyncio, concurrent.futures
        if not fn: return
        if callable(fn) and not hasattr(fn, 'params'):
            r = fn(arg) if arg is not None else fn()
            if asyncio.iscoroutine(r):
                threading.Thread(target=lambda: asyncio.run(r), daemon=True).start()
            return
        if hasattr(fn, 'params'):
            # Se todos os params têm default, não passa o widget como arg
            params = getattr(fn, 'params', [])
            all_have_defaults = all(
                (p.get('default') is not None if isinstance(p, dict) else False)
                for p in params
            ) if params else True
            if all_have_defaults and params:
                args = []  # usa defaults, não passa widget
            else:
                args = [arg] if arg is not None else []
            self._despachante.enviar(fn, args, origem)

    # ── Widgets básicos (compatíveis com advak_gui.py) ────────────────────────

    def label(self, pai, texto='', fonte=None, cor=None, negrito=False, tamanho=10):
        _check()
        p   = self._get_frame(pai)
        # Garante que tamanho é inteiro e cor é string de cor válida
        try: tamanho = int(tamanho)
        except: tamanho = 10
        # Cor inválida (número passado por engano) → usa cor padrão
        cor_final = _t('fg')
        if cor and isinstance(cor, str) and (cor.startswith('#') or cor.isalpha()):
            cor_final = cor
        fnt = (fonte or 'Segoe UI', tamanho, 'bold' if negrito else 'normal')
        w   = tk.Label(p, text=texto, font=fnt,
                       bg=_t('bg'), fg=cor_final)
        w.pack(anchor='w', pady=2, padx=4)
        w.texto = lambda t: w.config(text=t)
        w.cor   = lambda c: w.config(fg=c)
        w.posicionar = lambda **kw: self._posicionar(w, **kw)
        return w

    def canvas(self, pai, largura=400, altura=300, fundo='preto'):
        """Área de desenho 2D: devolve uma Tela (retangulo, circulo, linha, texto, mover, apagar...)."""
        _check()
        _positivo_canvas(largura, 'largura', 1); _positivo_canvas(altura, 'altura', 1)
        cv = tk.Canvas(self._get_frame(pai), width=int(largura), height=int(altura),
                       bg=_cor_canvas(fundo), highlightthickness=0)
        cv.pack(pady=4, padx=4, anchor='w')
        return Tela(cv, self)

    def botao(self, pai, texto='', ao_clicar=None, cor=None,
              largura=None, estilo='primario'):
        _check()
        p = self._get_frame(pai)
        estilos = {
            'primario':   {'bg': _t('btn_bg'),        'fg': '#FFFFFF'},
            'secundario': {'bg': '#E2E8F0' if self._tema_nome == 'claro' else _t('bg2'),
                           'fg': _t('fg')},
            'perigo':     {'bg': PALETA['vermelho'],   'fg': '#FFFFFF'},
            'sucesso':    {'bg': PALETA['verde'],       'fg': '#FFFFFF'},
            'aviso':      {'bg': PALETA['amarelo'],     'fg': '#FFFFFF'},
            'roxo':       {'bg': PALETA['roxo'],        'fg': '#FFFFFF'},
        }
        cfg = estilos.get(str(estilo).lower(), estilos['primario'])
        if cor: cfg['bg'] = cor
        w = tk.Button(p, text=texto,
                      bg=cfg['bg'], fg=cfg['fg'],
                      activebackground=cfg['bg'], activeforeground=cfg['fg'],
                      relief='flat', bd=0, padx=14, pady=7,
                      cursor='hand2', font=('Segoe UI', 10, 'bold'),
                      disabledforeground='#9CA3AF')
        if largura: w.config(width=largura)
        if ao_clicar:
            w.config(command=lambda: self._chamar(ao_clicar, w))
        w.pack(pady=4, padx=4, anchor='w')
        w.texto      = lambda t: w.config(text=t)
        w.habilitar  = lambda: w.config(state='normal')
        w.desabilitar= lambda: w.config(state='disabled')
        w.ao_clicar  = lambda fn: w.config(command=lambda: self._chamar(fn, w))
        w.posicionar = lambda **kw: self._posicionar(w, **kw)
        return w

    def campo(self, pai, placeholder='', valor_inicial='', senha=False,
              largura=35, ao_mudar=None):
        _check()
        p   = self._get_frame(pai)
        var = tk.StringVar(value=valor_inicial)
        w   = tk.Entry(p, textvariable=var, width=largura,
                       show='*' if senha else '',
                       bg=_t('input_bg'), fg=_t('input_fg'),
                       insertbackground=_t('input_fg'),
                       relief='solid', bd=1,
                       highlightthickness=1,
                       highlightcolor=_t('accent'),
                       highlightbackground=_t('border'),
                       font=('Segoe UI', 10))
        if placeholder and not valor_inicial:
            w.insert(0, placeholder)
            w.config(fg=_t('fg2'))
            def fi(e):
                if w.get() == placeholder: w.delete(0,'end'); w.config(fg=_t('input_fg'))
            def fo(e):
                if not w.get(): w.insert(0,placeholder); w.config(fg=_t('fg2'))
            w.bind('<FocusIn>', fi); w.bind('<FocusOut>', fo)
        if ao_mudar:
            var.trace_add('write', lambda *_: self._chamar(ao_mudar, var.get()))
        w.pack(pady=4, padx=4, anchor='w')
        w._ph  = placeholder
        w._var = var
        w.valor   = lambda: ('' if w.get()==placeholder else w.get())
        w.definir = lambda v: (var.set(v), w.config(fg=_t('input_fg')))
        w.limpar  = lambda: w.definir('')
        w.focar   = w.focus_set
        w.posicionar = lambda **kw: self._posicionar(w, **kw)
        return w

    def area_texto(self, pai, largura=50, altura=10, valor_inicial=''):
        _check()
        p  = self._get_frame(pai)
        fr = tk.Frame(p, bg=_t('bg'))
        sb = tk.Scrollbar(fr, bg=_t('border'))
        w  = tk.Text(fr, width=largura, height=altura,
                     bg=_t('input_bg'), fg=_t('input_fg'),
                     insertbackground=_t('input_fg'),
                     font=('Consolas', 10),
                     relief='solid', bd=1, wrap='word',
                     yscrollcommand=sb.set,
                     selectbackground=_t('accent'),
                     selectforeground='white')
        sb.config(command=w.yview)
        sb.pack(side='right', fill='y'); w.pack(side='left', fill='both', expand=True)
        fr.pack(pady=4, fill='both', expand=True)
        if valor_inicial: w.insert('1.0', valor_inicial)
        w.valor    = lambda: w.get('1.0','end-1c')
        w.definir  = lambda v: (w.delete('1.0','end'), w.insert('1.0',v))
        w.adicionar= lambda v: w.insert('end', v+'\n')
        w.limpar   = lambda: w.delete('1.0','end')
        # ── Métodos para syntax highlighting ─────────────────────────────
        # tag_configure: define cor/estilo de uma tag
        # Uso: editor.tag_configure("keyword", fg="#color", bold=True)
        def _tag_configure(nome, fg=None, bg=None, negrito=False, italico=False, sublinhado=False, **kw):
            opts = dict(kw)
            if fg:          opts['foreground'] = fg
            if bg:          opts['background'] = bg
            if negrito:     opts['font'] = ('Consolas', 11, 'bold')
            if italico:     opts['font'] = ('Consolas', 11, 'italic')
            if sublinhado:  opts['underline'] = True
            w.tag_configure(nome, **opts)
        # tag_add: aplica tag num intervalo de texto
        # Uso: editor.tag_add("keyword", "1.0", "1.5")
        def _tag_add(nome, inicio, fim):
            w.tag_add(nome, inicio, fim)
        # tag_remove: remove tag de um intervalo
        def _tag_remove(nome, inicio, fim):
            w.tag_remove(nome, inicio, fim)
        # tag_remover_todas: remove todas as ocorrências de uma tag
        def _tag_remover_todas(nome):
            w.tag_remove(nome, '1.0', 'end')
        # search: busca texto e retorna posição
        def _search(padrao, inicio='1.0', fim='end', regexp=False, nocase=False):
            resultado = w.search(padrao, inicio, stopindex=fim,
                                 regexp=regexp, nocase=nocase)
            return resultado if resultado else ''
        # count: conta caracteres entre dois índices
        def _count(inicio, fim):
            return int(w.count(inicio, fim, 'chars')[0])
        # index: converte índice para "linha.coluna"
        def _index(idx):
            return w.index(idx)
        w.tag_configurar   = _tag_configure
        w.tag_adicionar    = _tag_add
        w.tag_remover      = _tag_remove
        w.tag_limpar       = _tag_remover_todas
        w.buscar           = _search
        w.contar           = _count
        # Expor o widget tkinter bruto para acesso avançado
        w._widget_tk       = w
        return w

    def tabela(self, pai, colunas, altura=10, ao_selecionar=None):
        _check()
        p  = self._get_frame(pai)
        fr = tk.Frame(p, bg=_t('bg'))
        tree = ttk.Treeview(fr, columns=colunas, show='headings', height=altura)
        sby  = ttk.Scrollbar(fr, orient='vertical',   command=tree.yview)
        sbx  = ttk.Scrollbar(fr, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=sby.set, xscrollcommand=sbx.set)
        for col in colunas:
            tree.heading(col, text=col,
                         command=lambda c=col: self._ordenar(tree, c))
            tree.column(col, width=120, anchor='w')
        sby.pack(side='right', fill='y')
        sbx.pack(side='bottom', fill='x')
        tree.pack(fill='both', expand=True)
        fr.pack(fill='both', expand=True, pady=4)
        # Linhas alternadas
        tree.tag_configure('par',   background=_t('table_row'))
        tree.tag_configure('impar', background=_t('table_alt'))
        if ao_selecionar:
            def _on_sel(e, _t=tree, _c=colunas, _fn=ao_selecionar):
                sel = _t.selection()
                if not sel: return
                vals = _t.item(sel[0])['values']
                self._chamar(_fn, dict(zip(_c, vals)) if vals else None)
            tree.bind('<<TreeviewSelect>>', _on_sel)
        tree._colunas     = colunas
        tree._sort_reverse= {}
        tree._row_count   = 0
        def adicionar(dados):
            tree._row_count += 1
            tag = 'par' if tree._row_count % 2 == 0 else 'impar'
            if isinstance(dados, dict):
                vals = [dados.get(c,'') for c in colunas]
            elif isinstance(dados, (list, tuple)):
                vals = list(dados)
            else:
                vals = [str(dados)]
            tree.insert('', 'end', values=vals, tags=(tag,))
        def preencher(lst):
            tree.delete(*tree.get_children())
            tree._row_count = 0
            for item in (lst or []): adicionar(item)
        def selecionado():
            sel = tree.selection()
            if not sel: return None
            return dict(zip(colunas, tree.item(sel[0])['values']))
        def limpar():
            tree.delete(*tree.get_children())
            tree._row_count = 0
        tree.adicionar  = adicionar
        tree.preencher  = preencher
        tree.selecionado= selecionado
        tree.limpar     = limpar
        tree.posicionar = lambda **kw: self._posicionar(fr, **kw)
        return tree

    def separador(self, pai, horizontal=True):
        _check()
        p = self._get_frame(pai)
        w = ttk.Separator(p, orient='horizontal' if horizontal else 'vertical')
        w.pack(fill='x' if horizontal else 'y', pady=8, padx=4)
        return w

    def caixa_selecao(self, pai, opcoes, valor_inicial=None, ao_mudar=None):
        _check()
        p   = self._get_frame(pai)
        var = tk.StringVar(value=valor_inicial or (opcoes[0] if opcoes else ''))
        w   = ttk.Combobox(p, textvariable=var, values=opcoes,
                           font=('Segoe UI',10), state='readonly')
        w.pack(pady=4, padx=4, anchor='w')
        if ao_mudar:
            w.bind('<<ComboboxSelected>>', lambda e: self._chamar(ao_mudar, var.get()))
        w.valor   = var.get
        w.definir = var.set
        return w

    def checkbox(self, pai, texto='', valor_inicial=False, ao_mudar=None):
        _check()
        p   = self._get_frame(pai)
        var = tk.BooleanVar(value=valor_inicial)
        w   = ttk.Checkbutton(p, text=texto, variable=var,
            command=lambda: self._chamar(ao_mudar, var.get()) if ao_mudar else None)
        w.pack(pady=2, padx=4, anchor='w')
        w.valor     = var.get
        w.definir   = var.set
        w.marcar    = lambda: var.set(True)
        w.desmarcar = lambda: var.set(False)
        return w

    def barra_progresso(self, pai, valor=0, maximo=100):
        _check()
        p = self._get_frame(pai)
        w = ttk.Progressbar(p, length=300, maximum=maximo,
                            value=valor, mode='determinate')
        w.pack(pady=4, padx=4, anchor='w')
        w.definir      = lambda v: w.configure(value=v)
        w.incrementar  = lambda v=1: w.step(v)
        w.indeterminado= lambda: (w.configure(mode='indeterminate'), w.start(10))
        w.parar        = lambda: (w.stop(), w.configure(mode='determinate'))
        return w

    def lista(self, pai, itens=None, ao_selecionar=None, altura=8):
        _check()
        p  = self._get_frame(pai)
        fr = tk.Frame(p, bg=_t('bg'))
        sb = tk.Scrollbar(fr)
        w  = tk.Listbox(fr, font=('Segoe UI',10), height=altura,
                        yscrollcommand=sb.set, relief='solid', bd=1,
                        bg=_t('input_bg'), fg=_t('input_fg'),
                        selectbackground=_t('accent'), selectforeground='white',
                        selectmode='single')
        sb.config(command=w.yview)
        sb.pack(side='right', fill='y'); w.pack(side='left', fill='both', expand=True)
        fr.pack(pady=4, fill='both')
        for item in (itens or []): w.insert('end', str(item))
        if ao_selecionar:
            w.bind('<<ListboxSelect>>', lambda e:
                self._chamar(ao_selecionar, w.get(w.curselection()[0])) if w.curselection() else None)
        w.adicionar   = lambda v: w.insert('end', str(v))
        w.preencher   = lambda lst: (w.delete(0,'end'), [w.insert('end',str(i)) for i in lst])
        w.selecionado = lambda: w.get(w.curselection()[0]) if w.curselection() else None
        w.limpar      = lambda: w.delete(0,'end')
        return w

    def abas(self, pai):
        _check()
        p  = self._get_frame(pai)
        nb = ttk.Notebook(p)
        nb.pack(fill='both', expand=True, pady=4)
        def adicionar(titulo):
            fr = ttk.Frame(nb)
            nb.add(fr, text=f'  {titulo}  ')
            fr._frame = fr
            return fr
        nb.adicionar = adicionar
        # Métodos PT-BR para ttk.Notebook
        nb.selecionar = lambda idx: nb.select(idx)
        nb.aba_atual  = lambda: nb.index(nb.select())
        nb.total_abas = lambda: nb.index('end')
        return nb

    def menu_bar(self, janela):
        _check()
        mb = tk.Menu(janela, bg=_t('bg'), fg=_t('fg'),
                     activebackground=_t('accent'), activeforeground='white',
                     relief='flat', bd=0)
        janela.config(menu=mb)
        def adicionar(nome, itens):
            m = tk.Menu(mb, tearoff=0,
                        bg=_t('bg2'), fg=_t('fg'),
                        activebackground=_t('accent'), activeforeground='white',
                        relief='flat', bd=1)
            mb.add_cascade(label=nome, menu=m)
            for item in itens:
                if item == '---': m.add_separator()
                elif isinstance(item, (list,tuple)):
                    m.add_command(label=item[0],
                                  command=lambda fn=item[1]: self._chamar(fn, None))
                else:
                    m.add_command(label=str(item))
            return m
        mb.adicionar = adicionar
        return mb

    def frame(self, pai, cor=None, borda=False):
        _check()
        p  = self._get_frame(pai)
        kw = {'bg': cor or _t('bg')}
        if borda: kw.update(relief='solid', bd=1, highlightthickness=1,
                            highlightbackground=_t('border'))
        w = tk.Frame(p, **kw)
        w.pack(fill='both', expand=True, pady=2)
        w._frame = w
        def _pos(lado=None, preencher=None, expandir=False,
                 x=None, y=None, largura=None, altura=None,
                 pady=2, padx=4, ancora=None,
                 espaco_y=None, espaco_x=None):
            if espaco_y is not None: pady = espaco_y
            if espaco_x is not None: padx = espaco_x
            w.pack_forget()
            if lado:
                w.pack(side=lado, fill=preencher or 'both',
                       expand=expandir, padx=padx, pady=pady)
            else:
                w.pack(fill=preencher or 'both', expand=expandir,
                       padx=padx, pady=pady)
        w.posicionar = _pos
        return w

    def frame_horizontal(self, pai, cor=None):
        _check()
        p = self._get_frame(pai)
        bg = cor if cor else _t('bg')
        w = tk.Frame(p, bg=bg)
        w.pack(fill='x', pady=2, padx=4)
        w._frame = w; w._lado = 'left'
        def _pos(lado=None, preencher=None, expandir=False,
                 x=None, y=None, largura=None, altura=None,
                 pady=2, padx=4, ancora=None,
                 espaco_y=None, espaco_x=None):
            # espaco_y/espaco_x são aliases de pady/padx
            if espaco_y is not None: pady = espaco_y
            if espaco_x is not None: padx = espaco_x
            w.pack_forget()
            w.pack(side=lado or 'left', fill=preencher or 'x',
                   expand=expandir, padx=padx, pady=pady)
        w.posicionar = _pos
        return w

    # ── Diálogos ──────────────────────────────────────────────────────────────

    def alerta(self, msg, titulo='Advak'):
        _check(); self._garantir_root()
        messagebox.showinfo(titulo, msg)
    def erro(self, msg, titulo='Erro'):
        _check(); self._garantir_root()
        messagebox.showerror(titulo, msg)
    def aviso(self, msg, titulo='Aviso'):
        _check(); self._garantir_root()
        messagebox.showwarning(titulo, msg)
    def confirmar(self, msg, titulo='Confirmar'):
        _check(); self._garantir_root()
        return messagebox.askyesno(titulo, msg)
    def pedir(self, msg, titulo='Entrada', valor_inicial=''):
        _check(); self._garantir_root()
        from tkinter import simpledialog
        return simpledialog.askstring(titulo, msg, initialvalue=valor_inicial)
    def pedir_numero(self, msg, titulo='Número'):
        _check(); self._garantir_root()
        from tkinter import simpledialog
        return simpledialog.askfloat(titulo, msg)
    def escolher_arquivo(self, titulo='Abrir', tipos=None):
        _check(); self._garantir_root()
        from tkinter import filedialog
        return filedialog.askopenfilename(title=titulo,
                filetypes=tipos or [('Todos','*.*')]) or None
    def salvar_arquivo(self, titulo='Salvar', tipos=None):
        _check(); self._garantir_root()
        from tkinter import filedialog
        return filedialog.asksaveasfilename(title=titulo,
                filetypes=tipos or [('Todos','*.*')]) or None
    def escolher_cor(self, cor_inicial='#ffffff'):
        _check(); self._garantir_root()
        r = colorchooser.askcolor(color=cor_inicial)
        return r[1] if r[1] else None
    def escolher_pasta(self):
        _check(); self._garantir_root()
        from tkinter import filedialog
        return filedialog.askdirectory() or None

    # ── NOVOS COMPONENTES MODERNOS ────────────────────────────────────────────

    def toast(self, mensagem, tipo='info', duracao=3000):
        """
        Notificação flutuante no canto da tela.
        gui.toast("Salvo!", tipo="sucesso")
        tipos: info | sucesso | erro | aviso
        """
        _check()
        if not self._root: return
        cores = {
            'info':    (_t('accent'),      'white'),
            'sucesso': (PALETA['verde'],    'white'),
            'erro':    (PALETA['vermelho'], 'white'),
            'aviso':   (PALETA['amarelo'],  'white'),
        }
        bg, fg = cores.get(tipo, cores['info'])
        icones = {'info':'ℹ', 'sucesso':'✓', 'erro':'✗', 'aviso':'⚠'}
        icone  = icones.get(tipo, 'ℹ')

        toast = tk.Toplevel(self._root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        toast.configure(bg=bg)

        # Posiciona no canto inferior direito
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        tw, th = 320, 56
        offset = len(self._toasts) * (th + 8)
        toast.geometry(f'{tw}x{th}+{sw-tw-20}+{sh-th-60-offset}')

        tk.Label(toast, text=f' {icone}  {mensagem}',
                 bg=bg, fg=fg, font=('Segoe UI', 10, 'bold'),
                 anchor='w', padx=12).pack(fill='both', expand=True)

        self._toasts.append(toast)

        def fechar():
            try:
                self._toasts.remove(toast)
                toast.destroy()
            except: pass

        toast.after(duracao, fechar)

    def card(self, pai, titulo='', corpo='', cor_borda=None):
        """
        Card elevado com título e corpo.
        seja c = gui.card(aba, "Total", "R$ 1.500,00")
        """
        _check()
        p  = self._get_frame(pai)
        brd= cor_borda or _t('accent')
        fr = tk.Frame(p, bg=_t('bg2'),
                      highlightthickness=1,
                      highlightbackground=brd,
                      relief='flat', bd=0)
        fr.pack(padx=6, pady=6, fill='x')

        # Barra colorida no topo
        tk.Frame(fr, bg=brd, height=3).pack(fill='x')

        tk.Label(fr, text=titulo, bg=_t('bg2'), fg=_t('fg2'),
                 font=('Segoe UI', 9)).pack(anchor='w', padx=12, pady=(8,0))
        lbl_val = tk.Label(fr, text=corpo, bg=_t('bg2'), fg=_t('fg'),
                           font=('Segoe UI', 18, 'bold'))
        lbl_val.pack(anchor='w', padx=12, pady=(0,10))

        fr._frame = fr
        fr.titulo = lambda t: None  # título fixo
        fr.valor  = lambda v: lbl_val.config(text=v)
        fr.posicionar = lambda **kw: self._posicionar(fr, **kw)
        return fr

    def slider(self, pai, minimo=0, maximo=100, valor=50, ao_mudar=None, label=True):
        """
        Controle deslizante moderno.
        seja vol = gui.slider(aba, 0, 100, 50)
        """
        _check()
        p   = self._get_frame(pai)
        var = tk.DoubleVar(value=valor)
        fr  = tk.Frame(p, bg=_t('bg'))
        fr.pack(fill='x', padx=4, pady=4)
        lbl = None
        if label:
            lbl = tk.Label(fr, text=str(int(valor)), bg=_t('bg'), fg=_t('accent'),
                           font=('Segoe UI', 10, 'bold'), width=4)
            lbl.pack(side='right', padx=4)
        scale = ttk.Scale(fr, from_=minimo, to=maximo, variable=var,
                          orient='horizontal',
                          command=lambda v: (
                              lbl.config(text=str(int(float(v)))) if lbl else None,
                              self._chamar(ao_mudar, int(float(v))) if ao_mudar else None
                          ))
        scale.pack(side='left', fill='x', expand=True)
        scale.valor   = lambda: int(var.get())
        scale.definir = lambda v: var.set(v)
        scale.posicionar = lambda **kw: self._posicionar(fr, **kw)
        return scale

    def switch(self, pai, texto='', valor_inicial=False, ao_mudar=None):
        """
        Toggle switch moderno (como iOS/Android).
        seja sw = gui.switch(aba, "Ativar notificações")
        """
        _check()
        p   = self._get_frame(pai)
        var = tk.BooleanVar(value=valor_inicial)
        fr  = tk.Frame(p, bg=_t('bg'), cursor='hand2')
        fr.pack(fill='x', padx=4, pady=4, anchor='w')

        # Canvas para desenhar o switch
        cvs = tk.Canvas(fr, width=44, height=22,
                        bg=_t('bg'), highlightthickness=0)
        cvs.pack(side='left', padx=(0,8))
        tk.Label(fr, text=texto, bg=_t('bg'), fg=_t('fg'),
                 font=('Segoe UI',10)).pack(side='left')

        def desenhar():
            cvs.delete('all')
            bg_sw = _t('accent') if var.get() else _t('border')
            cvs.create_rounded_rect = lambda x1,y1,x2,y2,r,**kw: cvs.create_polygon(
                x1+r,y1, x2-r,y1, x2,y1+r, x2,y2-r, x2-r,y2, x1+r,y2, x1,y2-r, x1,y1+r,
                smooth=True, **kw)
            cvs.create_rounded_rect(0, 0, 44, 22, 11, fill=bg_sw, outline='')
            x = 33 if var.get() else 11
            cvs.create_oval(x-9, 2, x+9, 20, fill='white', outline='')

        def toggle(e=None):
            var.set(not var.get())
            desenhar()
            if ao_mudar: self._chamar(ao_mudar, var.get())

        cvs.bind('<Button-1>', toggle)
        fr.bind('<Button-1>', toggle)
        desenhar()

        fr.valor     = var.get
        fr.definir   = lambda v: (var.set(v), desenhar())
        fr.marcar    = lambda: (var.set(True), desenhar())
        fr.desmarcar = lambda: (var.set(False), desenhar())
        fr.posicionar= lambda **kw: self._posicionar(fr, **kw)
        return fr

    def badge(self, pai, texto, cor='azul'):
        """
        Badge/tag colorida.
        gui.badge(aba, "NOVO", cor="verde")
        """
        _check()
        p  = self._get_frame(pai)
        bg = PALETA.get(cor, cor)
        w  = tk.Label(p, text=f'  {texto}  ',
                      bg=bg, fg='white',
                      font=('Segoe UI', 9, 'bold'),
                      relief='flat', bd=0, pady=3)
        w.pack(side='left', padx=2, pady=2)
        w.texto = lambda t: w.config(text=f'  {t}  ')
        w.cor   = lambda c: w.config(bg=PALETA.get(c, c))
        return w

    def barra_status(self, janela, mensagem='Pronto'):
        """
        Barra de status na parte inferior da janela.
        seja st = gui.barra_status(jan, "Conectado ao banco")
        """
        _check()
        fr = tk.Frame(janela, bg=_t('bg2'),
                      highlightthickness=1,
                      highlightbackground=_t('border'), height=28)
        fr.pack(side='bottom', fill='x')
        fr.pack_propagate(False)
        lbl = tk.Label(fr, text=f'  {mensagem}',
                       bg=_t('bg2'), fg=_t('fg2'),
                       font=('Segoe UI', 9), anchor='w')
        lbl.pack(side='left', fill='y')
        # Indicador de status (bolinha colorida)
        dot = tk.Label(fr, text='●', bg=_t('bg2'),
                       fg=PALETA['verde'], font=('Segoe UI', 9))
        dot.pack(side='right', padx=8)

        fr.mensagem = lambda m: lbl.config(text=f'  {m}')
        fr.ok       = lambda m='OK': (lbl.config(text=f'  {m}'), dot.config(fg=PALETA['verde']))
        fr.erro_st  = lambda m='Erro': (lbl.config(text=f'  {m}'), dot.config(fg=PALETA['vermelho']))
        fr.aviso_st = lambda m='Aviso': (lbl.config(text=f'  {m}'), dot.config(fg=PALETA['amarelo']))
        return fr

    def grafico(self, pai, dados, tipo='barras', titulo='', largura=6, altura=3):
        """
        Gráfico embutido na janela (usa matplotlib).
        gui.grafico(aba, {labels:["Jan","Fev"], valores:[100,200]}, tipo="barras")
        tipos: barras | linha | pizza | area
        """
        _check()
        if not MATPLOTLIB_OK:
            lbl = tk.Label(self._get_frame(pai),
                           text='matplotlib não instalado.\npip install matplotlib',
                           bg=_t('bg'), fg=_t('fg2'), font=('Segoe UI',10))
            lbl.pack(pady=20)
            return lbl

        p   = self._get_frame(pai)
        fig = Figure(figsize=(largura, altura), dpi=90,
                     facecolor=_t('bg2'))
        ax  = fig.add_subplot(111, facecolor=_t('bg2'))
        ax.tick_params(colors=_t('fg2'))
        for spine in ax.spines.values():
            spine.set_color(_t('border'))
        ax.xaxis.label.set_color(_t('fg2'))
        ax.yaxis.label.set_color(_t('fg2'))

        labels  = dados.get('labels', []) if isinstance(dados, dict) else []
        valores = dados.get('valores', []) if isinstance(dados, dict) else dados
        cores_g = [_t('accent'), PALETA['verde'], PALETA['roxo'],
                   PALETA['laranja'], PALETA['ciano'], PALETA['rosa']]

        if tipo == 'barras':
            bars = ax.bar(labels or range(len(valores)), valores,
                         color=cores_g[:len(valores)])
            for bar, val in zip(bars, valores):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                        str(val), ha='center', va='bottom',
                        color=_t('fg'), fontsize=8)
        elif tipo == 'linha':
            ax.plot(labels or range(len(valores)), valores,
                    color=_t('accent'), linewidth=2, marker='o',
                    markerfacecolor=_t('accent'))
            ax.fill_between(labels or range(len(valores)), valores,
                           alpha=0.1, color=_t('accent'))
        elif tipo == 'pizza':
            ax.pie(valores, labels=labels, colors=cores_g[:len(valores)],
                   autopct='%1.1f%%', textprops={'color': _t('fg')})
        elif tipo == 'area':
            ax.fill_between(labels or range(len(valores)), valores,
                           alpha=0.4, color=_t('accent'))
            ax.plot(labels or range(len(valores)), valores,
                    color=_t('accent'), linewidth=2)

        if titulo: ax.set_title(titulo, color=_t('fg'), fontsize=11)
        fig.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(fig, master=p)
        canvas.draw()
        w = canvas.get_tk_widget()
        w.pack(fill='both', expand=True, pady=4)

        def atualizar(novos_dados):
            ax.clear()
            ax.set_facecolor(_t('bg2'))
            ax.tick_params(colors=_t('fg2'))
            nv = novos_dados.get('valores', []) if isinstance(novos_dados, dict) else novos_dados
            nl = novos_dados.get('labels', []) if isinstance(novos_dados, dict) else []
            if tipo == 'barras':
                ax.bar(nl or range(len(nv)), nv, color=cores_g[:len(nv)])
            elif tipo == 'linha':
                ax.plot(nl or range(len(nv)), nv, color=_t('accent'),
                        linewidth=2, marker='o')
            canvas.draw()

        w.atualizar = atualizar
        return w

    def arvore(self, pai, dados=None, colunas=None, altura=12, ao_selecionar=None):
        """
        Tree view hierárquico.
        gui.arvore(aba, [{"texto":"Pasta", "filhos":[{"texto":"Arquivo"}]}])
        """
        _check()
        p  = self._get_frame(pai)
        fr = tk.Frame(p, bg=_t('bg'))
        cols = colunas or ('#0',)
        tree = ttk.Treeview(fr, columns=[c for c in cols if c != '#0'],
                            show='tree headings', height=altura)
        sb = ttk.Scrollbar(fr, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.heading('#0', text='Item')
        for col in (colunas or []):
            if col != '#0':
                tree.heading(col, text=col)
                tree.column(col, width=100)
        sb.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)
        fr.pack(fill='both', expand=True, pady=4)

        def inserir_node(pai_id, item):
            texto = item.get('texto', str(item))
            vals  = [item.get(c,'') for c in (colunas or []) if c != '#0']
            node_id = tree.insert(pai_id, 'end', text=texto, values=vals, open=True)
            for filho in item.get('filhos', []):
                inserir_node(node_id, filho)
            return node_id

        if dados:
            for item in dados: inserir_node('', item)

        if ao_selecionar:
            tree.bind('<<TreeviewSelect>>', lambda e:
                self._chamar(ao_selecionar,
                    tree.item(tree.selection()[0]) if tree.selection() else None))

        tree.adicionar = lambda pai_id, item: inserir_node(pai_id or '', item)
        tree.limpar    = lambda: tree.delete(*tree.get_children())
        tree.preencher = lambda lst: (tree.limpar(), [inserir_node('', i) for i in lst])
        return tree

    def busca(self, pai, lista_itens=None, ao_selecionar=None, placeholder='Buscar...'):
        """
        Campo com autocomplete/busca.
        seja b = gui.busca(aba, ["Ana","Bob","Carla"], ao_selecionar=fn)
        """
        _check()
        p     = self._get_frame(pai)
        itens = list(lista_itens or [])
        fr    = tk.Frame(p, bg=_t('bg'))
        fr.pack(fill='x', padx=4, pady=4)
        var   = tk.StringVar()
        campo = tk.Entry(fr, textvariable=var, font=('Segoe UI',10),
                         bg=_t('input_bg'), fg=_t('input_fg'),
                         insertbackground=_t('input_fg'),
                         relief='solid', bd=1)
        campo.pack(fill='x')
        campo.insert(0, placeholder)
        campo.config(fg=_t('fg2'))
        # Listbox para sugestões
        lb_fr = tk.Frame(p, bg=_t('bg2'),
                         highlightthickness=1,
                         highlightbackground=_t('border'))
        lb    = tk.Listbox(lb_fr, font=('Segoe UI',10),
                           bg=_t('bg2'), fg=_t('fg'),
                           selectbackground=_t('accent'),
                           selectforeground='white',
                           relief='flat', bd=0, height=5)
        lb.pack(fill='both')

        def mostrar_sugestoes(filtro):
            lb.delete(0,'end')
            filtro = filtro.lower()
            matches = [i for i in itens if filtro in str(i).lower()] if filtro else []
            if matches:
                for m in matches[:8]: lb.insert('end', m)
                lb_fr.place(in_=campo, x=0, rely=1.0, relwidth=1.0)
                lb_fr.lift()
            else:
                lb_fr.place_forget()

        def on_key(e):
            val = var.get()
            if val != placeholder: mostrar_sugestoes(val)

        def on_select(e):
            if lb.curselection():
                val = lb.get(lb.curselection()[0])
                var.set(val); campo.config(fg=_t('input_fg'))
                lb_fr.place_forget()
                if ao_selecionar: self._chamar(ao_selecionar, val)

        def fi(e):
            if campo.get() == placeholder:
                campo.delete(0,'end'); campo.config(fg=_t('input_fg'))
        def fo(e):
            if not campo.get():
                campo.insert(0, placeholder); campo.config(fg=_t('fg2'))
            p.after(200, lb_fr.place_forget)

        campo.bind('<KeyRelease>', on_key)
        lb.bind('<<ListboxSelect>>', on_select)
        campo.bind('<FocusIn>', fi); campo.bind('<FocusOut>', fo)

        campo.valor    = lambda: ('' if var.get()==placeholder else var.get())
        campo.definir  = lambda v: (var.set(v), campo.config(fg=_t('input_fg')))
        campo.limpar   = lambda: campo.definir('')
        campo.atualizar_lista = lambda lst: itens.__class__ and itens.clear() or itens.extend(lst)
        campo.posicionar = lambda **kw: self._posicionar(fr, **kw)
        return campo

    def calendario(self, pai, ao_selecionar=None):
        """
        Seletor de data compacto.
        seja cal = gui.calendario(aba)
        data = cal.valor()  # retorna "2026-03-22"
        """
        _check()
        p = self._get_frame(pai)
        try:
            from tkcalendar import DateEntry
            w = DateEntry(p, font=('Segoe UI',10),
                         background=_t('accent'), foreground='white',
                         date_pattern='yyyy-mm-dd')
            w.pack(pady=4, padx=4, anchor='w')
            w.valor   = lambda: w.get_date().strftime('%Y-%m-%d')
            w.definir = lambda d: w.set_date(d)
            return w
        except ImportError:
            # Fallback simples sem tkcalendar
            var = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))
            w   = tk.Entry(p, textvariable=var, font=('Segoe UI',10),
                          bg=_t('input_bg'), fg=_t('input_fg'),
                          relief='solid', bd=1, width=12)
            w.pack(pady=4, padx=4, anchor='w')
            lbl = tk.Label(p, text='(AAAA-MM-DD)',
                          bg=_t('bg'), fg=_t('fg2'), font=('Segoe UI',8))
            lbl.pack(anchor='w', padx=4)
            w.valor   = var.get
            w.definir = var.set
            return w

    def modal(self, titulo, conteudo_fn, largura=500, altura=400):
        """
        Abre um modal/dialog customizável.
        gui.modal("Detalhes", (win) => { gui.label(win, "Conteúdo"); })
        """
        _check()
        if not self._root: return
        m = tk.Toplevel(self._root)
        m.title(titulo)
        m.geometry(f'{largura}x{altura}')
        m.configure(bg=_t('bg'))
        m.transient(self._root)
        m.grab_set()
        # Centraliza sobre a janela pai
        self._root.update_idletasks()
        x = self._root.winfo_x() + (self._root.winfo_width() - largura) // 2
        y = self._root.winfo_y() + (self._root.winfo_height() - altura) // 2
        m.geometry(f'{largura}x{altura}+{x}+{y}')
        # Barra de título customizada
        tk.Frame(m, bg=_t('accent'), height=40).pack(fill='x')
        m._frame = m
        m.fechar = m.destroy
        if conteudo_fn: self._chamar(conteudo_fn, m)
        return m

    def splitter(self, pai, orientacao='horizontal'):
        """
        Divisor redimensionável entre dois painéis.
        seja sp = gui.splitter(aba)
        """
        _check()
        p   = self._get_frame(pai)
        pw  = tk.PanedWindow(p,
            orient='horizontal' if orientacao=='horizontal' else 'vertical',
            bg=_t('bg'), sashwidth=6,
            sashrelief='flat', sashpad=2,
            handlesize=0)
        pw.pack(fill='both', expand=True)

        def adicionar_painel(peso=1):
            fr = tk.Frame(pw, bg=_t('bg'))
            pw.add(fr, stretch='always', minsize=100)
            fr._frame = fr
            fr.posicionar = lambda **kw: None
            return fr

        pw.adicionar = adicionar_painel
        pw.posicionar= lambda **kw: self._posicionar(pw, **kw)
        return pw

    # ── Helpers ───────────────────────────────────────────────────────────────

    def escolher(self, titulo, opcoes):
        """
        Abre um diálogo de seleção com lista de opções.
        Retorna o índice escolhido (int) ou -1 se cancelado.
        gui.escolher("Selecione:", ["Opção A", "Opção B"])
        """
        _check()
        if not self._root or not opcoes: return -1
        import tkinter as tk
        result = [-1]
        d = tk.Toplevel(self._root)
        d.title(titulo)
        d.configure(bg=_t('bg'))
        d.resizable(False, False)
        d.grab_set()

        # Centralizar
        d.update_idletasks()
        w, h = 380, min(400, 80 + len(opcoes) * 28)
        x = self._root.winfo_x() + (self._root.winfo_width()  - w) // 2
        y = self._root.winfo_y() + (self._root.winfo_height() - h) // 2
        d.geometry(f'{w}x{h}+{x}+{y}')

        tk.Label(d, text=titulo, bg=_t('bg'), fg=_t('fg'),
                 font=('Segoe UI', 11, 'bold'), pady=8).pack()

        lb_var = tk.StringVar()
        lb = tk.Listbox(d, listvariable=lb_var,
                        bg=_t('input_bg'), fg=_t('input_fg'),
                        selectbackground=_t('accent'), selectforeground='white',
                        font=('Segoe UI', 10), relief='flat', bd=1,
                        activestyle='none', height=min(12, len(opcoes)))
        for op in opcoes:
            lb.insert('end', op)
        lb.pack(fill='both', expand=True, padx=12, pady=4)
        if opcoes:
            lb.selection_set(0)

        def confirmar(e=None):
            sel = lb.curselection()
            result[0] = sel[0] if sel else -1
            d.destroy()

        lb.bind('<Double-1>', confirmar)
        tk.Button(d, text='Confirmar',
                  command=confirmar,
                  bg=_t('accent'), fg='white',
                  font=('Segoe UI', 10), relief='flat',
                  padx=20, pady=6, cursor='hand2').pack(pady=8)
        d.bind('<Return>', confirmar)
        d.bind('<Escape>', lambda e: d.destroy())
        self._root.wait_window(d)
        return result[0]

    def cor_hex(self, nome):
        """gui.cor_hex("azul") → "#2563EB" """
        return PALETA.get(nome, nome)

    def icone(self, nome):
        """
        Retorna emoji como ícone.
        gui.icone("salvar") → "💾"
        """
        icones = {
            'salvar':'💾','abrir':'📂','novo':'➕','excluir':'🗑',
            'editar':'✏','buscar':'🔍','atualizar':'🔄','fechar':'✕',
            'ok':'✓','erro':'✗','aviso':'⚠','info':'ℹ',
            'usuario':'👤','config':'⚙','home':'🏠','lista':'☰',
            'grafico':'📊','banco':'🗄','exportar':'📤','importar':'📥',
            'imprimir':'🖨','email':'📧','telefone':'📞',
            'calendario':'📅','relogio':'🕐','pasta':'📁','arquivo':'📄',
        }
        return icones.get(nome, nome)

    # ── Loop principal ────────────────────────────────────────────────────────

    def iniciar(self):
        _check()
        if self._root: self._root.mainloop()
        resumo = self._linha_resumo_erros()
        if resumo:
            print(resumo, file=sys.stderr)

    def parar(self):
        if self._root:
            try: self._root.quit(); self._root.destroy()
            except: pass

    def apos(self, ms, fn):
        if self._root: self._root.after(ms, lambda: self._chamar(fn, None))

    def repetir(self, ms, fn):
        def loop():
            self._chamar(fn, None)
            if self._root: self._root.after(ms, loop)
        if self._root: self._root.after(ms, loop)

    def ao_tecla(self, tratador):
        """Chama `tratador` com {tecla, caractere} a cada tecla pressionada na janela principal."""
        _check()
        if self._root is None:
            raise _erro_canvas("Crie a janela antes, com gui.janela(...), para usar gui.ao_tecla.")
        self._tratador_tecla = tratador                                  # o tratador novo substitui o anterior
        if not self._tecla_ligada:
            # bind_all e não bind na janela: o Tk só roda a ligação mais específica de cada tag, e a janela já
            # tem <F11> (tema), que esconderia o <KeyPress> da janela. A tag 'all' é separada e está em todos os widgets.
            self._root.bind_all('<KeyPress>', self._evento_tecla, add='+')
            self._tecla_ligada = True

    def _evento_tecla(self, evento):
        if self._tratador_tecla is not None:
            self._chamar(self._tratador_tecla, self._dados_tecla(evento), origem='tratador de tecla')

    @staticmethod
    def _dados_tecla(evento):
        return {"tecla": _NOMES_TECLA.get(evento.keysym, evento.keysym), "caractere": evento.char}

    def atualizar(self):
        if self._root:
            try: self._root.update()
            except: pass

    def _garantir_root(self):
        if self._root is None:
            self._root = tk.Tk()
            self._root.withdraw()
            global _root_ref
            _root_ref = self._root

    def _posicionar(self, widget, lado=None, preencher=None, expandir=False,
                    x=None, y=None, largura=None, altura=None,
                    pady=4, padx=4, ancora=None):
        if x is not None and y is not None:
            widget.place(x=x, y=y)
        elif lado:
            widget.pack(side=lado, fill=preencher or 'none',
                       expand=expandir, padx=padx, pady=pady)
        elif ancora:
            widget.pack(anchor=ancora, padx=padx, pady=pady)

    def _ordenar(self, tree, col):
        rev = tree._sort_reverse.get(col, False)
        dados = [(tree.set(k, col), k) for k in tree.get_children('')]
        try:    dados.sort(key=lambda t: float(t[0]), reverse=rev)
        except: dados.sort(key=lambda t: str(t[0]).lower(), reverse=rev)
        for i, (_, k) in enumerate(dados): tree.move(k, '', i)

    # ══════════════════════════════════════════════════════════════════════
    #  C# GUI — DataGrid vinculado
    # ══════════════════════════════════════════════════════════════════════

    def datagrid(self, pai, colunas, dados=None, editavel=True,
                 ao_mudar=None, ao_selecionar=None, filtro=True, altura=15):
        """
        DataGrid estilo C#/WPF — tabela com:
          • Binding bidirecional (editar célula atualiza fonte de dados)
          • Ordenação por coluna (clique no header)
          • Filtro em tempo real
          • Adição/remoção de linhas via interface
          • Callback ao_mudar(linha, coluna, novo_valor)

        Retorna objeto com API:
          .dados        — lista atual
          .adicionar(d) — adiciona linha
          .remover()    — remove linha selecionada
          .atualizar()  — rebind completo
          .selecionar() — linha selecionada como dict
          .filtrar(txt) — filtra por texto
        """
        _check()
        frame_pai = self._get_frame(pai)
        container = tk.Frame(frame_pai, bg=_t('bg'))
        container.pack(fill='both', expand=True, padx=4, pady=4)

        _source = list(dados or [])
        _filtro_texto = ['']
        _sort_col = [None]
        _sort_rev = [False]

        # ── Barra de filtro e botões ──────────────────────────────────────
        barra = tk.Frame(container, bg=_t('bg'))
        barra.pack(fill='x', pady=(0, 4))

        if filtro:
            var_filtro = tk.StringVar()
            ent_filtro = tk.Entry(barra, textvariable=var_filtro,
                                  bg=_t('input_bg'),
                                  fg=_t('fg'),
                                  insertbackground=_t('fg'),
                                  relief='flat', font=('Segoe UI', 10))
            ent_filtro.pack(side='left', fill='x', expand=True, padx=(0, 8))
            ent_filtro.insert(0, '🔍  Filtrar...')
            ent_filtro.config(fg='#888')

            def _fi_f(e):
                if ent_filtro.get().startswith('🔍'):
                    ent_filtro.delete(0, 'end')
                    ent_filtro.config(fg=_t('fg'))
            def _fo_f(e):
                if not ent_filtro.get():
                    ent_filtro.insert(0, '🔍  Filtrar...')
                    ent_filtro.config(fg='#888')
            ent_filtro.bind('<FocusIn>', _fi_f)
            ent_filtro.bind('<FocusOut>', _fo_f)

            def _on_filtro(*a):
                txt = var_filtro.get()
                if txt.startswith('🔍'): txt = ''
                _filtro_texto[0] = txt.lower()
                _rebind()
            var_filtro.trace('w', _on_filtro)

        if editavel:
            btn_add = tk.Button(barra, text='＋ Adicionar',
                                bg=_t('btn_bg'), fg=_t('fg'),
                                relief='flat', font=('Segoe UI', 9),
                                command=lambda: _adicionar_linha())
            btn_add.pack(side='right', padx=2)
            btn_del = tk.Button(barra, text='✕ Remover',
                                bg='#7f1d1d', fg='white',
                                relief='flat', font=('Segoe UI', 9),
                                command=lambda: _remover_linha())
            btn_del.pack(side='right', padx=2)

        # ── Treeview (tabela) ─────────────────────────────────────────────
        style_id = f'DG{id(container)}.Treeview'
        s = ttk.Style()
        bg = _t('bg')
        fg = _t('fg')
        sel = _t('select')
        s.theme_use('default')
        s.configure(style_id, background=bg, foreground=fg,
                    fieldbackground=bg, rowheight=28,
                    font=('Segoe UI', 10))
        s.configure(f'{style_id}.Heading',
                    background=_t('bg2'),
                    foreground=fg, font=('Segoe UI', 10, 'bold'),
                    relief='flat')
        s.map(style_id, background=[('selected', sel)],
              foreground=[('selected', 'white')])

        frame_tree = tk.Frame(container, bg=bg)
        frame_tree.pack(fill='both', expand=True)

        cols = [c if isinstance(c, str) else c.get('nome', str(c)) for c in colunas]
        widths = []
        for c in colunas:
            if isinstance(c, dict): widths.append(c.get('largura', 140))
            else: widths.append(140)

        tree = ttk.Treeview(frame_tree, columns=cols, show='headings',
                            height=altura, style=style_id)

        # Headers clicáveis para ordenar
        for i, col in enumerate(cols):
            w = widths[i] if i < len(widths) else 140
            tree.heading(col, text=col,
                         command=lambda c=col: _sort(c))
            tree.column(col, width=w, minwidth=60, anchor='w')

        vsb = ttk.Scrollbar(frame_tree, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(container, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        hsb.pack(fill='x')

        # Zebra striping
        tree.tag_configure('impar',  background=bg)
        tree.tag_configure('par',    background=_t('bg2'))
        tree.tag_configure('editando', background='#1d4ed8')

        def _rebind():
            tree.delete(*tree.get_children())
            filtro = _filtro_texto[0]
            src = _source
            if _sort_col[0]:
                col_idx = cols.index(_sort_col[0]) if _sort_col[0] in cols else 0
                try:
                    src = sorted(src, key=lambda r: float(list(r.values())[col_idx])
                                 if isinstance(list(r.values())[col_idx], (int, float))
                                 else str(list(r.values())[col_idx]).lower(),
                                 reverse=_sort_rev[0])
                except: pass
            for i, linha in enumerate(src):
                vals = [str(linha.get(c, '')) for c in cols]
                if filtro and not any(filtro in v.lower() for v in vals):
                    continue
                tag = 'par' if i % 2 == 0 else 'impar'
                tree.insert('', 'end', values=vals,
                            tags=(tag,), iid=str(id(linha)) + str(i))

        def _sort(col):
            if _sort_col[0] == col:
                _sort_rev[0] = not _sort_rev[0]
            else:
                _sort_col[0] = col
                _sort_rev[0] = False
            _rebind()

        # Edição inline ao dar duplo-clique
        if editavel:
            def _on_double_click(event):
                region = tree.identify('region', event.x, event.y)
                if region != 'cell': return
                row_id = tree.identify_row(event.y)
                col_id = tree.identify_column(event.x)
                if not row_id or not col_id: return
                col_num = int(col_id.replace('#', '')) - 1
                if col_num < 0 or col_num >= len(cols): return
                col_name = cols[col_num]
                bbox = tree.bbox(row_id, col_id)
                if not bbox: return
                x, y, w, h = bbox
                valor_atual = tree.set(row_id, col_name)
                _editar_celula(row_id, col_name, col_num, x, y, w, h, valor_atual)
            tree.bind('<Double-1>', _on_double_click)

        def _editar_celula(row_id, col_name, col_num, x, y, w, h, valor_atual):
            entry = tk.Entry(tree, bg='#1d4ed8', fg='white',
                             insertbackground='white',
                             relief='flat', font=('Segoe UI', 10),
                             justify='left')
            entry.place(x=x, y=y, width=w, height=h)
            entry.insert(0, valor_atual)
            entry.select_range(0, 'end')
            entry.focus_set()

            def _confirmar(event=None):
                novo_val = entry.get()
                entry.destroy()
                # Atualiza árvore
                tree.set(row_id, col_name, novo_val)
                # Atualiza fonte de dados
                iid_str = row_id
                for i, linha in enumerate(_source):
                    if str(id(linha)) + str(i) == iid_str:
                        _source[i][col_name] = novo_val
                        if ao_mudar:
                            self._chamar_com_args(ao_mudar, [_source[i], col_name, novo_val])
                        break

            def _cancelar(event=None):
                entry.destroy()

            entry.bind('<Return>', _confirmar)
            entry.bind('<Escape>', _cancelar)
            entry.bind('<FocusOut>', _confirmar)

        def _adicionar_linha():
            nova = {c: '' for c in cols}
            _source.append(nova)
            _rebind()

        def _remover_linha():
            sel = tree.selection()
            if not sel: return
            row_id = sel[0]
            for i, linha in enumerate(_source):
                if str(id(linha)) + str(i) == row_id:
                    _source.pop(i)
                    break
            _rebind()

        if ao_selecionar:
            def _on_sel(e):
                sel = tree.selection()
                if sel:
                    vals = tree.item(sel[0], 'values')
                    d = dict(zip(cols, vals))
                    self._chamar_com_args(ao_selecionar, [d])
            tree.bind('<<TreeviewSelect>>', _on_sel)

        _rebind()

        # ── API pública ───────────────────────────────────────────────────
        class DataGridAPI:
            pass
        api = DataGridAPI()
        api.__dict__['dados']     = _source
        api.__dict__['adicionar'] = lambda d: (_source.append(d), _rebind())
        api.__dict__['remover']   = _remover_linha
        api.__dict__['atualizar'] = _rebind
        api.__dict__['filtrar']   = lambda txt: setattr(_filtro_texto, 0, txt.lower()) or _rebind()
        api.__dict__['selecionar'] = lambda: (
            dict(zip(cols, tree.item(tree.selection()[0], 'values')))
            if tree.selection() else None
        )
        api.__dict__['limpar'] = lambda: (_source.clear(), _rebind())
        api.__dict__['widget'] = tree
        return api

    # ══════════════════════════════════════════════════════════════════════
    #  C# GUI — MVVM / Binding reativo
    # ══════════════════════════════════════════════════════════════════════

    def criar_viewmodel(self, dados_iniciais=None):
        """
        Cria um ViewModel estilo C#/WPF com propriedades reativas.

        Uso:
          vm = gui.criar_viewmodel({nome: "Ana", pontos: 0})
          vm.vincular(campo_entry, "nome")       // bidirecional
          vm.vincular_label(label, "pontos")     // unidirecional
          vm.definir("pontos", vm.obter("pontos") + 1)
          vm.ao_mudar("pontos", fn)             // observer
        """
        _check()
        dados = dict(dados_iniciais or {})
        _observers = {}      # prop -> [callbacks]
        _bindings_to  = {}   # prop -> [tk.Variable]
        _bindings_from = {}  # prop -> [tk.Variable]

        def _notificar(prop, val):
            # Atualiza todos os widgets vinculados
            for var in _bindings_to.get(prop, []):
                try:
                    cur = var.get()
                    if str(cur) != str(val):
                        var.set(val)
                except: pass
            # Chama observers (suporta AdvakFunction e funções Python)
            for fn in _observers.get(prop, []):
                try:
                    if hasattr(fn, 'params'):
                        self._chamar(fn, val)
                    else:
                        fn(val)
                except: pass

        def _definir(prop, val):
            dados[prop] = val
            _notificar(prop, val)

        def _obter(prop, default=None):
            return dados.get(prop, default)

        def _vincular(widget, prop, bidirecional=True):
            """Vincula um widget Entry/Spinbox a uma propriedade."""
            if hasattr(widget, 'configure'):
                var = tk.StringVar(value=str(dados.get(prop, '')))
                try: widget.configure(textvariable=var)
                except: pass
                _bindings_to.setdefault(prop, []).append(var)

                if bidirecional:
                    def _on_var_change(*a):
                        v = var.get()
                        # Tenta converter para número se o dado original era número
                        orig = dados.get(prop)
                        if isinstance(orig, (int, float)):
                            try: v = type(orig)(v)
                            except: pass
                        if dados.get(prop) != v:
                            dados[prop] = v
                            for fn in _observers.get(prop, []):
                                try:
                                    if hasattr(fn, 'params'):
                                        self._chamar(fn, v)
                                    else:
                                        fn(v)
                                except: pass
                    var.trace('w', _on_var_change)

        def _vincular_label(widget, prop, formatar=None):
            """Vincula um Label a uma propriedade (leitura)."""
            var = tk.StringVar(value=str(dados.get(prop, '')))
            try: widget.configure(textvariable=var)
            except: pass
            _bindings_to.setdefault(prop, []).append(var)
            if formatar:
                # Wrap: formatar é uma função string -> string
                orig_app = _bindings_to[prop]
                class _FmtVar:
                    def set(self, v):
                        try: var.set(formatar(v))
                        except: var.set(str(v))
                    def get(self): return var.get()
                _bindings_to[prop][-1] = _FmtVar()

        def _vincular_checkbox(widget, prop):
            """Vincula um Checkbutton a uma propriedade bool."""
            var = tk.BooleanVar(value=bool(dados.get(prop, False)))
            try: widget.configure(variable=var)
            except: pass
            _bindings_to.setdefault(prop, []).append(var)

            def _on_check(*a):
                dados[prop] = var.get()
                for fn in _observers.get(prop, []):
                    try:
                        if hasattr(fn, 'params'):
                            self._chamar(fn, var.get())
                        else:
                            fn(var.get())
                    except: pass
            var.trace('w', _on_check)

        def _vincular_lista(widget, prop):
            """Vincula Listbox/Combobox a propriedade lista."""
            _observers.setdefault(prop, []).append(lambda v: _atualizar_lista(widget, v))

        def _atualizar_lista(widget, vals):
            try:
                widget['values'] = vals  # Combobox
            except:
                try:
                    widget.delete(0, 'end')
                    for v in (vals or []):
                        widget.insert('end', str(v))
                except: pass

        def _ao_mudar(prop, fn):
            _observers.setdefault(prop, []).append(fn)

        def _remover_observer(prop, fn):
            if prop in _observers and fn in _observers[prop]:
                _observers[prop].remove(fn)

        def _calcular(prop, fn, *deps):
            """Propriedade computada — recalcula quando deps mudam."""
            def _recalc(_v=None):
                try:
                    if hasattr(fn, 'params'):
                        # AdvakFunction não suportada como calculada
                        val = None
                    else:
                        val = fn(*[dados.get(d) for d in deps])
                except Exception:
                    val = None
                dados[prop] = val
                _notificar(prop, val)
            for dep in deps:
                _observers.setdefault(dep, []).append(_recalc)
            _recalc()  # Calcula inicial

        class ViewModel:
            pass
        vm = ViewModel()
        vm.__dict__['dados']            = dados
        vm.__dict__['definir']          = _definir
        vm.__dict__['obter']            = _obter
        vm.__dict__['vincular']         = _vincular
        vm.__dict__['vincular_label']   = _vincular_label
        vm.__dict__['vincular_checkbox']= _vincular_checkbox
        vm.__dict__['vincular_lista']   = _vincular_lista
        vm.__dict__['ao_mudar']         = _ao_mudar
        vm.__dict__['remover_observer'] = _remover_observer
        vm.__dict__['calcular']         = _calcular
        vm.__dict__['notificar']        = _notificar
        return vm

    # ══════════════════════════════════════════════════════════════════════
    #  C# GUI — Animações CSS (tkinter transitions)
    # ══════════════════════════════════════════════════════════════════════

    def animar(self, widget, propriedade, valor_final, duracao=300,
               easing='ease_out', ao_terminar=None):
        """
        Anima uma propriedade de widget — estilo CSS transitions.

        propriedade: 'largura' | 'altura' | 'x' | 'y' | 'opacidade' | 'cor_fundo'
        easing: 'linear' | 'ease_in' | 'ease_out' | 'ease_in_out' | 'bounce'
        duracao: milissegundos

        Exemplo:
          gui.animar(botao, 'largura', 300, duracao=500, easing='ease_out')
          gui.animar(frame, 'cor_fundo', '#ff0000', duracao=800)
        """
        _check()
        if not self._root: return

        FPS = 60
        frames = max(1, int(duracao / 1000 * FPS))
        intervalo = int(1000 / FPS)

        def _ease(t, modo):
            if modo == 'linear':     return t
            if modo == 'ease_in':    return t * t
            if modo == 'ease_out':   return 1 - (1 - t) ** 2
            if modo == 'ease_in_out':
                return 2*t*t if t < 0.5 else 1 - (-2*t+2)**2/2
            if modo == 'bounce':
                if t < 1/2.75:     return 7.5625*t*t
                elif t < 2/2.75:   t -= 1.5/2.75;   return 7.5625*t*t + 0.75
                elif t < 2.5/2.75: t -= 2.25/2.75;  return 7.5625*t*t + 0.9375
                else:              t -= 2.625/2.75; return 7.5625*t*t + 0.984375
            return t

        def _hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        def _rgb_to_hex(r, g, b):
            return f'#{int(r):02x}{int(g):02x}{int(b):02x}'

        # Descobre valor inicial
        try:
            if propriedade == 'largura':
                v0 = widget.winfo_width() or 40
                v1 = int(valor_final)
                import tkinter as _tk
                if isinstance(widget, _tk.Label):
                    # Labels: use place geometry to resize (safe on Windows)
                    def _aplicar(v):
                        try: widget.place(width=int(v))
                        except Exception: pass
                else:
                    def _aplicar(v):
                        try: widget.configure(width=int(v))
                        except Exception: pass
            elif propriedade == 'altura':
                v0 = widget.winfo_height() or 30
                v1 = int(valor_final)
                import tkinter as _tk
                if isinstance(widget, _tk.Label):
                    def _aplicar(v):
                        try: widget.place(height=int(v))
                        except Exception: pass
                else:
                    def _aplicar(v):
                        try: widget.configure(height=int(v))
                        except Exception: pass
            elif propriedade == 'x':
                info = widget.place_info()
                v0 = int(info.get('x', 0))
                v1 = int(valor_final)
                def _aplicar(v): widget.place(x=int(v))
            elif propriedade == 'y':
                info = widget.place_info()
                v0 = int(info.get('y', 0))
                v1 = int(valor_final)
                def _aplicar(v): widget.place(y=int(v))
            elif propriedade in ('cor_fundo', 'background', 'bg'):
                try: cur = widget.cget('bg')
                except: cur = '#000000'
                if not cur.startswith('#'):
                    try: cur = widget.winfo_rgb(cur)
                    except: cur = '#000000'
                r0, g0, b0 = _hex_to_rgb(cur)
                r1, g1, b1 = _hex_to_rgb(str(valor_final))
                v0, v1 = 0, 1
                def _aplicar(v):
                    r = r0 + (r1-r0)*v
                    g = g0 + (g1-g0)*v
                    b = b0 + (b1-b0)*v
                    try: widget.configure(bg=_rgb_to_hex(r, g, b))
                    except: pass
            elif propriedade == 'opacidade':
                # Tkinter não suporta opacidade diretamente — usa attr custom
                v0 = float(getattr(widget, '_opacidade', 1.0))
                v1 = float(valor_final)
                def _aplicar(v):
                    widget._opacidade = v
                    # Simula via cor de fundo misturada com parent
                    try:
                        pbg = widget.master.cget('bg')
                        wbg = getattr(widget, '_bg_original',
                                      widget.cget('bg') or '#ffffff')
                        if not hasattr(widget, '_bg_original'):
                            widget._bg_original = widget.cget('bg') or '#ffffff'
                        r0c, g0c, b0c = _hex_to_rgb(wbg)
                        rp, gp, bp   = _hex_to_rgb(pbg if pbg.startswith('#') else '#1e293b')
                        r = r0c*v + rp*(1-v)
                        g = g0c*v + gp*(1-v)
                        b = b0c*v + bp*(1-v)
                        widget.configure(bg=_rgb_to_hex(r, g, b))
                    except: pass
            else:
                return  # propriedade desconhecida
        except Exception as e:
            return

        frame_atual = [0]

        def _tick():
            if frame_atual[0] > frames:
                _aplicar(v1)
                if ao_terminar:
                    try: ao_terminar()
                    except: pass
                return
            t = frame_atual[0] / frames
            t_eased = _ease(t, easing)
            v = v0 + (v1 - v0) * t_eased
            try: _aplicar(v)
            except: pass
            frame_atual[0] += 1
            if self._root:
                self._root.after(intervalo, _tick)

        if self._root:
            self._root.after(0, _tick)

    def animar_sequencia(self, animacoes):
        """
        Executa animações em sequência (como CSS animation keyframes).
        animacoes = lista de dicts: {widget, prop, valor, duracao, easing}
        """
        if not animacoes: return
        def _next(idx):
            if idx >= len(animacoes): return
            a = animacoes[idx]
            self.animar(
                a['widget'], a.get('prop', a.get('propriedade', '')),
                a['valor'],
                duracao=a.get('duracao', 300),
                easing=a.get('easing', 'ease_out'),
                ao_terminar=lambda: _next(idx + 1)
            )
        _next(0)

    def animar_loop(self, widget, propriedade, v_inicio, v_fim,
                    duracao=600, easing='ease_in_out'):
        """
        Anima em loop ping-pong (ida e volta) — como CSS animation infinite alternate.
        """
        _going = [True]

        def _ida():
            if not _going[0]: return
            self.animar(widget, propriedade, v_fim, duracao, easing,
                        ao_terminar=_volta)
        def _volta():
            if not _going[0]: return
            self.animar(widget, propriedade, v_inicio, duracao, easing,
                        ao_terminar=_ida)

        widget._anim_loop_stop = lambda: _going.__setitem__(0, False)
        _ida()

    # ══════════════════════════════════════════════════════════════════════
    #  C# GUI — Drag and Drop
    # ══════════════════════════════════════════════════════════════════════

    def habilitar_drag(self, widget, dados=None, ao_iniciar=None, cursor='hand2'):
        """
        Torna um widget arrastável.
        dados: valor associado ao widget (qualquer coisa)
        ao_iniciar: callback chamado quando drag começa
        """
        _check()
        widget._drag_dados = dados
        widget._drag_ativo = False
        widget._drag_x = 0
        widget._drag_y = 0
        widget._drag_fantasma = None

        def _on_press(e):
            widget._drag_ativo = True
            widget._drag_x = e.x_root
            widget._drag_y = e.y_root
            widget.configure(cursor=cursor)
            if ao_iniciar:
                try: ao_iniciar(dados)
                except: pass
            # Cria widget fantasma (cópia visual seguindo o mouse)
            try:
                texto = widget.cget('text') if hasattr(widget, 'cget') else ''
                cor = widget.cget('bg') if hasattr(widget, 'cget') else '#334155'
                fantasma = tk.Label(self._root, text=texto,
                                    bg=cor, fg=_t('fg'),
                                    relief='raised', padx=8, pady=4,
                                    font=('Segoe UI', 10))
                fantasma.place(x=e.x_root - self._root.winfo_rootx(),
                               y=e.y_root - self._root.winfo_rooty())
                widget._drag_fantasma = fantasma
            except: pass

        def _on_motion(e):
            if not widget._drag_ativo: return
            if widget._drag_fantasma:
                try:
                    x = e.x_root - self._root.winfo_rootx()
                    y = e.y_root - self._root.winfo_rooty()
                    widget._drag_fantasma.place(x=x, y=y)
                except: pass

        def _on_release(e):
            widget._drag_ativo = False
            widget.configure(cursor='')
            if widget._drag_fantasma:
                try: widget._drag_fantasma.destroy()
                except: pass
                widget._drag_fantasma = None
            # Verifica se soltou sobre um alvo de drop
            try:
                w_abaixo = self._root.winfo_containing(e.x_root, e.y_root)
                while w_abaixo:
                    if hasattr(w_abaixo, '_drop_handler'):
                        w_abaixo._drop_handler(widget._drag_dados, e)
                        break
                    try: w_abaixo = w_abaixo.master
                    except: break
            except: pass

        widget.bind('<ButtonPress-1>',  _on_press)
        widget.bind('<B1-Motion>',      _on_motion)
        widget.bind('<ButtonRelease-1>',_on_release)

    def habilitar_drop(self, widget, ao_soltar, realce=True):
        """
        Torna um widget alvo de drop.
        ao_soltar: callback(dados, evento) — chamado quando item é solto aqui
        """
        _check()
        _cor_original = [None]

        widget._drop_handler = lambda d, e: ao_soltar(d, e)

        if realce:
            def _on_enter(e):
                try:
                    _cor_original[0] = widget.cget('bg')
                    widget.configure(bg='#1d4ed8')
                except: pass
            def _on_leave(e):
                try:
                    if _cor_original[0]:
                        widget.configure(bg=_cor_original[0])
                except: pass
            widget.bind('<Enter>', _on_enter)
            widget.bind('<Leave>', _on_leave)

    def kanban(self, pai, colunas_config, ao_mover=None):
        """
        Painel Kanban com drag-and-drop entre colunas — estilo C# WPF.

        colunas_config = [
          {titulo: "A Fazer",  itens: ["Task 1", "Task 2"], cor: "#1e293b"},
          {titulo: "Fazendo",  itens: [],                   cor: "#1e3a5f"},
          {titulo: "Concluído",itens: ["Task 0"],           cor: "#14532d"},
        ]

        Retorna objeto com:
          .adicionar(coluna_idx, item)
          .obter_colunas()  → [[itens], ...]
        """
        _check()
        frame_pai = self._get_frame(pai)
        frame_main = tk.Frame(frame_pai, bg=_t('bg'))
        frame_main.pack(fill='both', expand=True)

        _colunas_data = [list(c.get('itens', [])) for c in colunas_config]
        _col_frames = []
        _col_listas = []

        def _rebuild():
            for w in frame_main.winfo_children():
                w.destroy()
            _col_frames.clear()
            _col_listas.clear()
            for ci, conf in enumerate(colunas_config):
                col_bg = conf.get('cor', '#1e293b')
                col_frame = tk.Frame(frame_main, bg=col_bg,
                                     relief='flat', bd=0)
                col_frame.pack(side='left', fill='both', expand=True,
                               padx=6, pady=6)
                _col_frames.append(col_frame)

                # Header
                header = tk.Frame(col_frame, bg=col_bg)
                header.pack(fill='x', pady=(8, 4))
                tk.Label(header, text=conf['titulo'],
                         bg=col_bg, fg=_t('fg'),
                         font=('Segoe UI', 11, 'bold')).pack(side='left', padx=12)
                count_lbl = tk.Label(header,
                                     text=str(len(_colunas_data[ci])),
                                     bg='#334155', fg='white',
                                     font=('Segoe UI', 9),
                                     padx=6, pady=1, relief='flat')
                count_lbl.pack(side='right', padx=8)

                # Área de cards
                cards_frame = tk.Frame(col_frame, bg=col_bg)
                cards_frame.pack(fill='both', expand=True, padx=6, pady=4)
                _col_listas.append(cards_frame)

                # Habilita drop na coluna
                self.habilitar_drop(col_frame,
                    ao_soltar=lambda dados, e, ci=ci: _on_drop(dados, ci),
                    realce=True)
                self.habilitar_drop(cards_frame,
                    ao_soltar=lambda dados, e, ci=ci: _on_drop(dados, ci),
                    realce=False)

                # Renderiza cards
                for item in _colunas_data[ci]:
                    _criar_card(cards_frame, item, ci)

        def _criar_card(parent, item, col_idx):
            card = tk.Frame(parent, bg='#334155', relief='flat',
                            cursor='hand2')
            card.pack(fill='x', pady=3, padx=2)
            lbl = tk.Label(card, text=str(item), bg='#334155',
                           fg=_t('fg'),
                           font=('Segoe UI', 10),
                           wraplength=160, justify='left',
                           padx=10, pady=8)
            lbl.pack(fill='x')
            # Drag
            self.habilitar_drag(card, dados={'item': item, 'col': col_idx})
            self.habilitar_drag(lbl,  dados={'item': item, 'col': col_idx})
            return card

        def _on_drop(dados, col_destino):
            if dados is None: return
            item = dados.get('item')
            col_origem = dados.get('col')
            if col_origem == col_destino: return
            if item in _colunas_data[col_origem]:
                _colunas_data[col_origem].remove(item)
            _colunas_data[col_destino].append(item)
            if ao_mover:
                try: ao_mover(item, col_origem, col_destino)
                except: pass
            _rebuild()

        _rebuild()

        class KanbanAPI:
            pass
        api = KanbanAPI()
        api.__dict__['adicionar'] = lambda ci, item: (
            _colunas_data[ci].append(item), _rebuild()
        )
        api.__dict__['obter_colunas'] = lambda: [list(c) for c in _colunas_data]
        api.__dict__['remover'] = lambda ci, item: (
            _colunas_data[ci].remove(item) if item in _colunas_data[ci] else None,
            _rebuild()
        )
        return api

    def _chamar_com_args(self, fn, args, origem=None):
        """Chama função Advak com lista de argumentos, em thread segura."""
        if fn is None: return
        import asyncio
        if callable(fn) and not hasattr(fn, 'params'):
            # Função Python nativa
            if self._root:
                self._root.after(0, lambda: fn(*args))
            else:
                try:
                    if hasattr(fn, 'params'):
                        self._chamar(fn, args[0] if len(args)==1 else args)
                    else:
                        fn(*args)
                except Exception:
                    pass
            return
        if hasattr(fn, 'params'):
            # AdvakFunction — executa via interpretador
            self._despachante.enviar(fn, args, origem)