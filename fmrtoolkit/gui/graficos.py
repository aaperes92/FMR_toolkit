"""Visor de gráficos: una ventana aparte con todas las figuras de una ejecución.

Las figuras se crean en el hilo de cálculo con el backend Agg (sin ventanas). Acá, en el
hilo principal, se incrustan con FigureCanvasTkAgg y NavigationToolbar2Tk (zoom,
desplazamiento, guardar). Si hay muchas (por ejemplo un ajuste de carpeta), se recorren
con una lista y los botones anterior/siguiente, en una sola ventana.
"""

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def nombre_figura(figura, numero, textos):
    """Título de la figura (el del eje o el suptitle) para la lista."""
    suptitulo = getattr(figura, '_suptitle', None)
    if suptitulo is not None and suptitulo.get_text():
        return suptitulo.get_text()
    for eje in figura.axes:
        titulo = eje.get_title()
        if titulo:
            return titulo.replace('\n', ' · ')
    return textos.t('graficos.figura', n=numero)


class VisorFiguras(tk.Toplevel):

    def __init__(self, padre, figuras, titulo, textos):
        super().__init__(padre)
        self.figuras = figuras
        self.textos = textos
        self.indice = 0
        self.canvas = None
        self.barra = None
        t = textos.t
        self.title(t('graficos.titulo', tecnica=titulo, n=len(figuras)))
        self.geometry('1050x640')
        self.minsize(640, 420)

        lateral = ttk.Frame(self, padding=4)
        lateral.pack(side='left', fill='y')
        self.lista = tk.Listbox(lateral, width=34, activestyle='dotbox', exportselection=False)
        barra_lista = ttk.Scrollbar(lateral, orient='vertical', command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra_lista.set)
        self.lista.pack(side='left', fill='y')
        barra_lista.pack(side='left', fill='y')
        for i, fig in enumerate(figuras, start=1):
            self.lista.insert('end', f'{i}. {nombre_figura(fig, i, textos)}')
        self.lista.bind('<<ListboxSelect>>', self._seleccion)
        if len(figuras) <= 1:
            lateral.pack_forget()

        derecha = ttk.Frame(self)
        derecha.pack(side='left', fill='both', expand=True)
        abajo = ttk.Frame(derecha, padding=(4, 2))          # fijo abajo: siempre visible
        abajo.pack(side='bottom', fill='x')
        self.zona = ttk.Frame(derecha)
        self.zona.pack(fill='both', expand=True)
        # Los botones se ubican antes que la barra de herramientas, para que no queden tapados
        self.boton_siguiente = ttk.Button(abajo, text=t('graficos.siguiente'), command=lambda: self.ir(self.indice + 1))
        self.boton_anterior = ttk.Button(abajo, text=t('graficos.anterior'), command=lambda: self.ir(self.indice - 1))
        if len(figuras) > 1:
            self.boton_siguiente.pack(side='right')
            self.boton_anterior.pack(side='right', padx=4)
        self.zona_barra = ttk.Frame(abajo)
        self.zona_barra.pack(side='left', fill='x', expand=True)
        self.bind('<Left>', lambda e: self.ir(self.indice - 1))
        self.bind('<Right>', lambda e: self.ir(self.indice + 1))
        self.ir(0)

    def _seleccion(self, _evento):
        seleccion = self.lista.curselection()
        if seleccion:
            self.ir(seleccion[0])

    def ir(self, indice):
        if not self.figuras:
            return
        self.indice = indice % len(self.figuras)
        for widget in (self.canvas.get_tk_widget() if self.canvas else None, self.barra):
            if widget is not None:
                widget.destroy()
        figura = self.figuras[self.indice]
        self.canvas = FigureCanvasTkAgg(figura, master=self.zona)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.barra = NavigationToolbar2Tk(self.canvas, self.zona_barra, pack_toolbar=False)
        self.barra.update()
        self.barra.pack(side='left')
        self.lista.selection_clear(0, 'end')
        self.lista.selection_set(self.indice)
        self.lista.see(self.indice)
