"""Widgets reutilizables de la GUI: tooltip, ícono ⓘ, campo de parámetro, sección
plegable, marco con scroll y apertura de archivos con el programa del sistema."""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

# Colores de la interfaz
COLOR_EXPERIMENTO = '#1f6feb'
COLOR_TEORIA = '#d9480f'
COLOR_FONDO_TOOLTIP = '#fffbe6'
COLOR_BORDE_TOOLTIP = '#c9b458'
COLOR_ERROR = '#c92a2a'
COLOR_AVISO = '#9c6500'
COLOR_INFO = '#1971c2'


# ==================================================
# TOOLTIP
# ==================================================

class Tooltip:
    """Cartel que aparece al dejar el mouse quieto sobre un widget y desaparece al salir.

    `texto` puede ser un string o una función sin argumentos que lo devuelve (así el
    tooltip se actualiza solo si cambia el idioma).
    """

    DEMORA_MS = 350
    ANCHO_MAXIMO = 420

    def __init__(self, widget, texto):
        self.widget = widget
        self.texto = texto
        self.ventana = None
        self._pendiente = None
        widget.bind('<Enter>', self._programar, add='+')
        widget.bind('<Leave>', self._ocultar, add='+')
        widget.bind('<ButtonPress>', self._ocultar, add='+')
        widget.bind('<Destroy>', self._ocultar, add='+')

    def _texto(self):
        return self.texto() if callable(self.texto) else self.texto

    def _programar(self, _evento=None):
        self._cancelar()
        self._pendiente = self.widget.after(self.DEMORA_MS, self._mostrar)

    def _cancelar(self):
        if self._pendiente is not None:
            try:
                self.widget.after_cancel(self._pendiente)
            except tk.TclError:
                pass
            self._pendiente = None

    def _mostrar(self):
        self._pendiente = None
        texto = self._texto()
        if not texto or self.ventana is not None:
            return
        self.ventana = tk.Toplevel(self.widget)
        self.ventana.wm_overrideredirect(True)
        try:
            self.ventana.wm_attributes('-topmost', True)
        except tk.TclError:
            pass
        marco = tk.Frame(self.ventana, background=COLOR_BORDE_TOOLTIP, padx=1, pady=1)
        marco.pack()
        tk.Label(marco, text=texto, justify='left', background=COLOR_FONDO_TOOLTIP,
                 wraplength=self.ANCHO_MAXIMO, padx=8, pady=6).pack()
        self.ventana.update_idletasks()
        # Cerca del puntero, sin salirse de la pantalla
        x = self.widget.winfo_pointerx() + 14
        y = self.widget.winfo_pointery() + 18
        ancho, alto = self.ventana.winfo_reqwidth(), self.ventana.winfo_reqheight()
        x = min(x, self.widget.winfo_screenwidth() - ancho - 4)
        if y + alto > self.widget.winfo_screenheight() - 4:
            y = self.widget.winfo_pointery() - alto - 10
        self.ventana.wm_geometry(f'+{max(x, 0)}+{max(y, 0)}')

    def _ocultar(self, _evento=None):
        self._cancelar()
        if self.ventana is not None:
            try:
                self.ventana.destroy()
            except tk.TclError:
                pass
            self.ventana = None


class IconoInfo(ttk.Label):
    """Ícono ⓘ que muestra un tooltip al pasar el mouse."""

    def __init__(self, padre, texto, **kw):
        super().__init__(padre, text='ⓘ', foreground=COLOR_INFO, cursor='question_arrow', **kw)
        self.tooltip = Tooltip(self, texto)


# ==================================================
# CAMPO DE UN PARÁMETRO
# ==================================================

class CampoParametro:
    """Etiqueta "nombre (unidad)" + control + ícono ⓘ + mensaje de error, en una fila
    de una grilla. El control depende del tipo: Checkbutton (bool), Combobox (opcion)
    o Entry (el resto)."""

    def __init__(self, padre, fila, parametro, etiqueta, tooltip, al_cambiar, textos):
        self.parametro = parametro
        self.textos = textos
        unidad = f' ({parametro.unidad})' if parametro.unidad else ''
        self.label = ttk.Label(padre, text=etiqueta + unidad)
        self.label.grid(row=2 * fila, column=0, sticky='w', padx=(4, 8), pady=(3, 0))

        if parametro.tipo == 'bool':
            self.variable = tk.BooleanVar()
            self.control = ttk.Checkbutton(padre, variable=self.variable)
        elif parametro.tipo == 'opcion':
            self.variable = tk.StringVar()
            self.control = ttk.Combobox(padre, textvariable=self.variable, width=12, state='readonly',
                                        values=[str(o) for o in parametro.opciones])
        else:
            self.variable = tk.StringVar()
            self.control = ttk.Entry(padre, textvariable=self.variable, width=14)
        self.control.grid(row=2 * fila, column=1, sticky='we', pady=(3, 0))
        self.icono = IconoInfo(padre, tooltip)
        self.icono.grid(row=2 * fila, column=2, sticky='w', padx=(4, 2), pady=(3, 0))
        Tooltip(self.label, tooltip)
        self.error = ttk.Label(padre, text='', foreground=COLOR_ERROR, wraplength=300)
        self.error.grid(row=2 * fila + 1, column=0, columnspan=3, sticky='w', padx=4)
        self.error.grid_remove()
        self.variable.trace_add('write', lambda *_: al_cambiar())

    def obtener(self):
        """Texto del campo (o bool, para tipo 'bool')."""
        if self.parametro.tipo == 'bool':
            return bool(self.variable.get())
        return self.variable.get()

    def poner(self, valor):
        if self.parametro.tipo == 'bool':
            self.variable.set(bool(valor))
        else:
            self.variable.set('' if valor is None else str(valor))

    def marcar_error(self, mensaje=None):
        if mensaje:
            self.error.configure(text='⚠ ' + mensaje)
            self.error.grid()
            if isinstance(self.control, ttk.Entry) and not isinstance(self.control, ttk.Combobox):
                self.control.configure(style='Error.TEntry')
        else:
            self.error.grid_remove()
            if isinstance(self.control, ttk.Entry) and not isinstance(self.control, ttk.Combobox):
                self.control.configure(style='TEntry')


# ==================================================
# SECCIÓN PLEGABLE
# ==================================================

class SeccionPlegable(ttk.Frame):
    """Botón que muestra u oculta un marco interno (`self.contenido`)."""

    def __init__(self, padre, texto_mostrar, texto_ocultar, abierta=False):
        super().__init__(padre)
        self.texto_mostrar, self.texto_ocultar = texto_mostrar, texto_ocultar
        self.abierta = abierta
        self.boton = ttk.Button(self, style='Plegable.TButton', command=self.alternar)
        self.boton.pack(anchor='w')
        self.contenido = ttk.Frame(self, padding=(12, 2, 0, 2))
        self._actualizar()

    def alternar(self):
        self.abierta = not self.abierta
        self._actualizar()

    def _actualizar(self):
        self.boton.configure(text=self.texto_ocultar if self.abierta else self.texto_mostrar)
        if self.abierta:
            self.contenido.pack(fill='x', anchor='w')
        else:
            self.contenido.pack_forget()


# ==================================================
# MARCO CON SCROLL VERTICAL
# ==================================================

class MarcoConScroll(ttk.Frame):
    """Marco con barra de desplazamiento vertical. Los widgets van en `self.interior`."""

    def __init__(self, padre, **kw):
        super().__init__(padre, **kw)
        fondo = ttk.Style(self).lookup('TFrame', 'background') or None
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, background=fondo)
        self.barra = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.barra.set)
        self.barra.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.interior = ttk.Frame(self.canvas)
        self._ventana = self.canvas.create_window((0, 0), window=self.interior, anchor='nw')
        self.interior.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self._ventana, width=e.width))
        # Rueda del mouse solo mientras el puntero está sobre este marco
        self.bind('<Enter>', lambda e: self._rueda(True))
        self.bind('<Leave>', lambda e: self._rueda(False))

    def _rueda(self, activar):
        if activar:
            self.bind_all('<MouseWheel>', self._mover)
            self.bind_all('<Button-4>', lambda e: self.canvas.yview_scroll(-3, 'units'))
            self.bind_all('<Button-5>', lambda e: self.canvas.yview_scroll(3, 'units'))
        else:
            self.unbind_all('<MouseWheel>')
            self.unbind_all('<Button-4>')
            self.unbind_all('<Button-5>')

    def _mover(self, evento):
        if self.interior.winfo_height() <= self.canvas.winfo_height():
            return
        paso = -1 * (evento.delta // 120 if sys.platform.startswith('win') else evento.delta)
        self.canvas.yview_scroll(int(paso) or (1 if evento.delta < 0 else -1), 'units')

    def al_inicio(self):
        self.canvas.yview_moveto(0)


# ==================================================
# ABRIR ARCHIVOS Y CARPETAS CON EL PROGRAMA DEL SISTEMA
# ==================================================

def abrir_con_sistema(ruta):
    """Abre un archivo, carpeta o enlace (mailto:) con el programa predeterminado.
    Devuelve True si pudo lanzarlo."""
    ruta = str(ruta)
    try:
        if sys.platform.startswith('win'):
            os.startfile(ruta)                                      # noqa: S606
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', ruta])
        else:
            subprocess.Popen(['xdg-open', ruta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, AttributeError):
        import webbrowser
        try:
            return webbrowser.open(ruta)
        except Exception:                                            # noqa: BLE001
            return False


def configurar_estilos(raiz):
    """Tema y estilos de la aplicación."""
    estilo = ttk.Style(raiz)
    if 'clam' in estilo.theme_names():
        estilo.theme_use('clam')
    estilo.configure('Error.TEntry', fieldbackground='#ffe3e3')
    estilo.configure('Plegable.TButton', relief='flat', padding=(2, 1))
    estilo.configure('Titulo.TLabel', font=('TkDefaultFont', 13, 'bold'))
    estilo.configure('Funcion.TLabel', foreground='#666666')
    estilo.configure('Aviso.TLabel', foreground=COLOR_AVISO)
    estilo.configure('Error.TLabel', foreground=COLOR_ERROR)
    estilo.configure('Ejecutar.TButton', font=('TkDefaultFont', 11, 'bold'), padding=(14, 6))
    estilo.configure('Treeview', rowheight=22)
    return estilo
