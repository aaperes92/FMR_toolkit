"""Formulario de una técnica, armado a partir de su especificación (especificaciones.py).

No sabe nada de física: muestra los campos agrupados, lee y valida los valores, y le
devuelve a la ventana principal los argumentos listos para llamar a la función.
"""

import os
import tkinter as tk
from tkinter import filedialog, ttk

from fmrtoolkit.gui import conversion
from fmrtoolkit.gui.especificaciones import GRUPOS
from fmrtoolkit.gui.widgets import (COLOR_EXPERIMENTO, COLOR_TEORIA, CampoParametro,
                                    MarcoConScroll, SeccionPlegable, Tooltip)


class Formulario(ttk.Frame):
    """Formulario de una técnica.

    padre        : contenedor
    tecnica      : Tecnica (especificaciones.py)
    textos       : Textos (idioma.py)
    guardado     : {"id_variante": {nombre: texto}} con los últimos valores usados
    variante_ini : id de la variante elegida la última vez
    entrada_ini  : última carpeta/archivo de entrada
    al_ejecutar  : callback sin argumentos del botón Ejecutar
    al_documentar: callback(ruta_doc) del botón de documentación
    """

    def __init__(self, padre, tecnica, textos, guardado, variante_ini, entrada_ini,
                 al_ejecutar, al_documentar):
        super().__init__(padre)
        self.tecnica, self.textos = tecnica, textos
        self.guardado = {k: dict(v) for k, v in (guardado or {}).items()}
        self.al_ejecutar, self.al_documentar = al_ejecutar, al_documentar
        self.variante = tecnica.variante(variante_ini)
        self.var_variante = tk.StringVar(value=self.variante.id)
        self.var_entrada = tk.StringVar(value=entrada_ini or '')
        self.campos = {}
        self._construir()

    # ==================================================
    # CONSTRUCCIÓN
    # ==================================================

    def _construir(self):
        t = self.textos.t
        color = COLOR_EXPERIMENTO if self.tecnica.seccion == 'experimento' else COLOR_TEORIA

        # ----- Encabezado -----
        cabecera = ttk.Frame(self, padding=(12, 10, 12, 4))
        cabecera.pack(fill='x')
        tk.Frame(cabecera, background=color, width=5).pack(side='left', fill='y', padx=(0, 10))
        textos_cab = ttk.Frame(cabecera)
        textos_cab.pack(side='left', fill='x', expand=True)
        ttk.Label(textos_cab, text=t(f'tecnicas.{self.tecnica.id}.nombre'),
                  style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(textos_cab, text=t(f'tecnicas.{self.tecnica.id}.descripcion'),
                  wraplength=620, justify='left').pack(anchor='w', pady=(2, 0))
        self.lbl_funcion = ttk.Label(textos_cab, style='Funcion.TLabel')
        self.lbl_funcion.pack(anchor='w', pady=(2, 0))
        botones = ttk.Frame(cabecera)
        botones.pack(side='right', anchor='n')
        ttk.Button(botones, text=t('formulario.restaurar'), command=self.restaurar).pack(fill='x')
        if self.tecnica.doc:
            ttk.Button(botones, text=t('app.documentacion'),
                       command=lambda: self.al_documentar(self.tecnica.doc)).pack(fill='x', pady=(4, 0))

        # ----- Selector de variante (1 capa / 2 capas) -----
        if len(self.tecnica.variantes) > 1:
            fila = ttk.Frame(self, padding=(12, 2))
            fila.pack(fill='x')
            ttk.Label(fila, text=t('variantes.titulo')).pack(side='left', padx=(0, 8))
            for v in self.tecnica.variantes:
                ttk.Radiobutton(fila, text=t(f'variantes.{v.id}'), value=v.id, variable=self.var_variante,
                                command=self._cambiar_variante).pack(side='left', padx=(0, 12))

        # ----- Entrada -----
        marco_entrada = ttk.LabelFrame(self, text=t('entrada.titulo'), padding=(8, 4))
        marco_entrada.pack(fill='x', padx=12, pady=(6, 2))
        self.marco_entrada = marco_entrada

        # ----- Avisos, errores y botón Ejecutar (fijo abajo, siempre visible) -----
        pie = ttk.Frame(self, padding=(12, 4, 12, 8))
        pie.pack(side='bottom', fill='x')
        self.lbl_avisos = ttk.Label(pie, style='Aviso.TLabel', wraplength=640, justify='left')
        self.lbl_avisos.pack(fill='x', anchor='w')
        self.lbl_errores = ttk.Label(pie, style='Error.TLabel', wraplength=640, justify='left')
        self.lbl_errores.pack(fill='x', anchor='w')
        fila_boton = ttk.Frame(pie)
        fila_boton.pack(fill='x', pady=(4, 0))
        self.progreso = ttk.Progressbar(fila_boton, mode='indeterminate', length=160)
        self.lbl_calculando = ttk.Label(fila_boton, text=t('formulario.calculando'))
        self.boton_ejecutar = ttk.Button(fila_boton, text=t('formulario.ejecutar'), style='Ejecutar.TButton',
                                         command=self.al_ejecutar)
        self.boton_ejecutar.pack(side='right')

        # ----- Campos (con scroll): ocupan el espacio que queda -----
        self.scroll = MarcoConScroll(self)
        self.scroll.pack(fill='both', expand=True, padx=6, pady=2)

        self._construir_variante()

    def _construir_variante(self):
        """Entrada y campos de la variante actual (se rehace al cambiar de variante)."""
        t = self.textos.t
        v = self.variante
        self.lbl_funcion.configure(text=f"{t('formulario.funcion')} {v.nombre_funcion}")

        for hijo in self.marco_entrada.winfo_children():
            hijo.destroy()
        if v.entrada is None:
            ttk.Label(self.marco_entrada, text=t('entrada.sin_entrada')).pack(anchor='w')
        else:
            ttk.Label(self.marco_entrada, text=t(f'entrada.{v.entrada}')).pack(side='left')
            entrada = ttk.Entry(self.marco_entrada, textvariable=self.var_entrada, state='readonly')
            entrada.pack(side='left', fill='x', expand=True, padx=6)
            Tooltip(entrada, lambda: self.var_entrada.get())
            ttk.Button(self.marco_entrada, text=t('entrada.elegir'), command=self._elegir_entrada).pack(side='left')

        for hijo in self.scroll.interior.winfo_children():
            hijo.destroy()
        self.campos = {}
        comunes = [p for p in v.parametros if not p.avanzado]
        avanzados = [p for p in v.parametros if p.avanzado]

        grilla = ttk.Frame(self.scroll.interior)
        grilla.pack(fill='x', padx=6)
        columnas = 2
        for i, grupo in enumerate(g for g in GRUPOS if any(p.grupo == g for p in comunes)):
            marco = ttk.LabelFrame(grilla, text=t(f'grupos.{grupo}'), padding=(6, 2, 6, 6))
            marco.grid(row=i // columnas, column=i % columnas, sticky='nwe', padx=4, pady=4)
            marco.columnconfigure(1, weight=1)
            self._agregar_campos(marco, [p for p in comunes if p.grupo == grupo])
        for c in range(columnas):
            grilla.columnconfigure(c, weight=1, uniform='grupos')

        if avanzados:
            plegable = SeccionPlegable(self.scroll.interior, t('formulario.avanzado_mostrar'),
                                       t('formulario.avanzado_ocultar'))
            plegable.pack(fill='x', padx=10, pady=(2, 8))
            marco = ttk.Frame(plegable.contenido)
            marco.pack(fill='x', anchor='w')
            marco.columnconfigure(1, weight=1)
            self._agregar_campos(marco, avanzados)

        self._cargar_valores()
        self.scroll.al_inicio()
        self.actualizar_avisos()

    def _agregar_campos(self, marco, parametros):
        tx = self.textos
        for fila, p in enumerate(parametros):
            self.campos[p.nombre] = CampoParametro(
                marco, fila, p,
                etiqueta=tx.parametro(self.tecnica.id, p.nombre, 'etiqueta'),
                tooltip=lambda p=p: tx.tooltip_parametro(self.tecnica.id, p),
                al_cambiar=self.actualizar_avisos, textos=tx)

    # ==================================================
    # VALORES
    # ==================================================

    def _cargar_valores(self):
        """Pone los últimos valores usados, o los de la firma si no hay guardados."""
        defectos = self.variante.valores_por_defecto()
        guardados = self.guardado.get(self.variante.id, {})
        for p in self.variante.parametros:
            valor = guardados.get(p.nombre, conversion.texto_por_defecto(p, defectos[p.nombre]))
            self.campos[p.nombre].poner(valor)

    def restaurar(self):
        """Valores por defecto de la firma de la función."""
        defectos = self.variante.valores_por_defecto()
        for p in self.variante.parametros:
            self.campos[p.nombre].poner(conversion.texto_por_defecto(p, defectos[p.nombre]))
            self.campos[p.nombre].marcar_error(None)
        self.lbl_errores.configure(text='')
        self.actualizar_avisos()

    def textos_actuales(self):
        return {nombre: campo.obtener() for nombre, campo in self.campos.items()}

    def estado_para_guardar(self):
        """{"id_variante": {nombre: texto}} incluyendo la variante actual."""
        self.guardado[self.variante.id] = self.textos_actuales()
        return self.guardado

    def _cambiar_variante(self):
        nueva = self.tecnica.variante(self.var_variante.get())
        if nueva is self.variante:
            return
        self.guardado[self.variante.id] = self.textos_actuales()
        self.variante = nueva
        self.lbl_errores.configure(text='')
        self._construir_variante()

    def _elegir_entrada(self):
        t = self.textos.t
        inicial = self.var_entrada.get()
        carpeta_inicial = inicial if os.path.isdir(inicial) else os.path.dirname(inicial) or os.path.expanduser('~')
        if self.variante.entrada == 'carpeta':
            ruta = filedialog.askdirectory(parent=self, title=t('entrada.elegir_carpeta'),
                                           initialdir=carpeta_inicial, mustexist=True)
        else:
            ruta = filedialog.askopenfilename(
                parent=self, title=t('entrada.elegir_archivo'), initialdir=carpeta_inicial,
                filetypes=[(t('entrada.filtro_output'), self.variante.filtro_archivo),
                           (t('entrada.filtro_todos'), '*.*')])
        if ruta:
            self.var_entrada.set(os.path.normpath(ruta))

    def entrada(self):
        return self.var_entrada.get().strip()

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    def actualizar_avisos(self):
        """Advertencias de la documentación que aplican a los valores actuales."""
        valores, _ = conversion.validar(self.variante, self.textos_actuales())
        claves = conversion.advertencias_activas(self.variante, self.tecnica, valores)
        self.lbl_avisos.configure(text='\n'.join('⚠ ' + self.textos.t(f'advertencias.{c}') for c in claves))

    def leer(self):
        """Valida todo. Devuelve (valores, mensajes_de_error). Los valores ya están en las
        unidades de la función. Marca en rojo los campos con error."""
        t = self.textos.t
        valores, errores = conversion.validar(self.variante, self.textos_actuales())
        for campo in self.campos.values():
            campo.marcar_error(None)
        mensajes = []
        for nombre, error in errores:
            texto = t(f'errores.{error.clave}', **error.datos)
            if nombre is not None:
                self.campos[nombre].marcar_error(texto)
                etiqueta = self.textos.parametro(self.tecnica.id, nombre, 'etiqueta')
                mensajes.append(f'{etiqueta}: {texto}')
            else:
                mensajes.append(texto)
        if self.variante.entrada:
            ruta = self.entrada()
            if not ruta:
                mensajes.insert(0, t(f'formulario.falta_entrada_{self.variante.entrada}'))
            elif not os.path.exists(ruta):
                mensajes.insert(0, t('formulario.entrada_no_existe', ruta=ruta))
        self.lbl_errores.configure(
            text=(t('formulario.errores_texto') + '\n• ' + '\n• '.join(mensajes)) if mensajes else '')
        return valores, mensajes

    # ==================================================
    # ESTADO "CALCULANDO"
    # ==================================================

    def calculando(self, activo):
        if activo:
            self.boton_ejecutar.state(['disabled'])
            self.progreso.pack(side='right', padx=8)
            self.lbl_calculando.pack(side='right')
            self.progreso.start(12)
        else:
            self.progreso.stop()
            self.progreso.pack_forget()
            self.lbl_calculando.pack_forget()
            self.boton_ejecutar.state(['!disabled'])
