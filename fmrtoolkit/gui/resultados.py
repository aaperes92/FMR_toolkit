"""Panel inferior: tabla con el contenido de los archivos de resultados (.txt).

Los archivos de salida del toolkit tienen una línea de encabezado y valores separados
por comas. Si hay varios, un selector permite elegir cuál ver.
"""

import os
import tkinter as tk
from tkinter import ttk

MAXIMO_FILAS = 5000


def leer_tabla(ruta):
    """(encabezados, filas) de un .txt separado por comas con una línea de encabezado."""
    with open(ruta, encoding='utf-8', errors='replace') as f:
        lineas = [l.rstrip('\n') for l in f if l.strip()]
    if not lineas:
        raise ValueError('archivo vacío')
    encabezados = [c.strip() for c in lineas[0].split(',')]
    filas = []
    for linea in lineas[1:MAXIMO_FILAS + 1]:
        celdas = [c.strip() for c in linea.split(',')]
        filas.append([_formatear_celda(c) for c in celdas])
    if len(encabezados) < max((len(f) for f in filas), default=0):
        encabezados += [f'col{i}' for i in range(len(encabezados), max(len(f) for f in filas))]
    return encabezados, filas


def _formatear_celda(texto):
    try:
        valor = float(texto)
    except ValueError:
        return texto
    return format(valor, '.6g')


class PanelResultados(ttk.Frame):

    def __init__(self, padre, textos, al_abrir_carpeta, al_ver_graficos, al_abrir_gif):
        super().__init__(padre, padding=(8, 4, 8, 4))
        self.textos = textos
        self.carpeta = None
        self.archivos = []
        t = textos.t

        barra = ttk.Frame(self)
        barra.pack(fill='x')
        ttk.Label(barra, text=t('resultados.titulo'), style='Titulo.TLabel').pack(side='left')
        ttk.Label(barra, text='   ' + t('resultados.archivo')).pack(side='left')
        self.var_archivo = tk.StringVar()
        self.selector = ttk.Combobox(barra, textvariable=self.var_archivo, state='readonly', width=42)
        self.selector.pack(side='left', padx=6)
        self.selector.bind('<<ComboboxSelected>>', lambda e: self._mostrar(self.var_archivo.get()))
        ttk.Button(barra, text=t('resultados.abrir_carpeta'), command=al_abrir_carpeta).pack(side='right')
        self.boton_gif = ttk.Button(barra, text=t('resultados.abrir_gif'), command=al_abrir_gif)
        self.boton_graficos = ttk.Button(barra, text=t('resultados.ver_graficos'), command=al_ver_graficos)

        marco = ttk.Frame(self)
        marco.pack(fill='both', expand=True, pady=(4, 0))
        self.tabla = ttk.Treeview(marco, show='headings', height=6)
        barra_y = ttk.Scrollbar(marco, orient='vertical', command=self.tabla.yview)
        barra_x = ttk.Scrollbar(marco, orient='horizontal', command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=barra_y.set, xscrollcommand=barra_x.set)
        self.tabla.grid(row=0, column=0, sticky='nsew')
        barra_y.grid(row=0, column=1, sticky='ns')
        barra_x.grid(row=1, column=0, sticky='ew')
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        self.mensaje = tk.Label(marco, text=t('resultados.sin_resultados'), foreground='#777777',
                                background='white')
        self.mensaje.place(relx=0.5, rely=0.45, anchor='center')

    def mostrar_botones(self, graficos, gif):
        for boton, visible in ((self.boton_gif, gif), (self.boton_graficos, graficos)):
            if visible:
                boton.pack(side='right', padx=(0, 6))
            else:
                boton.pack_forget()

    def cargar(self, carpeta, archivos):
        """Muestra los archivos .txt de `archivos` (nombres dentro de `carpeta`)."""
        self.carpeta = carpeta
        self.archivos = [a for a in archivos if a.lower().endswith('.txt')]
        self.selector.configure(values=self.archivos)
        if not self.archivos:
            self.var_archivo.set('')
            self._limpiar(self.textos.t('resultados.sin_tablas'))
            return
        # Primero el resumen (output_*) si existe
        preferido = next((a for a in self.archivos if a.startswith('output_')), self.archivos[0])
        self.var_archivo.set(preferido)
        self._mostrar(preferido)

    def _limpiar(self, mensaje=None):
        self.tabla.delete(*self.tabla.get_children())
        self.tabla.configure(columns=())
        if mensaje:
            self.mensaje.configure(text=mensaje)
            self.mensaje.place(relx=0.5, rely=0.45, anchor='center')
        else:
            self.mensaje.place_forget()

    def _mostrar(self, nombre):
        if not nombre or self.carpeta is None:
            return
        try:
            encabezados, filas = leer_tabla(os.path.join(self.carpeta, nombre))
        except (OSError, ValueError):
            self._limpiar(self.textos.t('resultados.no_se_pudo_leer', archivo=nombre))
            return
        self._limpiar()
        ids = [f'c{i}' for i in range(len(encabezados))]
        self.tabla.configure(columns=ids)
        for n, (i, titulo) in enumerate(zip(ids, encabezados)):
            largo = max([len(titulo)] + [len(str(f[n])) for f in filas[:200] if n < len(f)])
            self.tabla.heading(i, text=titulo, anchor='w')
            self.tabla.column(i, width=max(70, min(300, 8 * largo + 16)), stretch=False, anchor='w')
        for fila in filas:
            self.tabla.insert('', 'end', values=fila)
