"""Ventana principal de la GUI de fmrtoolkit.

Barra superior (carpeta de salida, idioma, reportar), barra lateral con las técnicas
(Experimento / Teoría), formulario de la técnica elegida, panel de resultados y barra de
estado. Las técnicas salen de especificaciones.TECNICAS: para agregar una no hay que
tocar este archivo.

Se lanza con:  python -m fmrtoolkit.gui
"""

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib

matplotlib.use('Agg')            # antes de pyplot y del toolkit: los cálculos no abren ventanas
import matplotlib.pyplot as plt  # noqa: E402

from fmrtoolkit.gui import configuracion
from fmrtoolkit.gui.dialogos import DialogoError, DialogoReporte, VentanaRegistro, carpeta_para_reportes
from fmrtoolkit.gui.ejecucion import EjecutorEnHilo
from fmrtoolkit.gui.especificaciones import SECCIONES, TECNICAS, tecnica as buscar_tecnica
from fmrtoolkit.gui.formulario import Formulario
from fmrtoolkit.gui.graficos import VisorFiguras
from fmrtoolkit.gui.idioma import Textos
from fmrtoolkit.gui.resultados import PanelResultados
from fmrtoolkit.gui.widgets import (COLOR_EXPERIMENTO, COLOR_TEORIA, Tooltip, abrir_con_sistema,
                                    configurar_estilos)

URL_DOCS = 'https://github.com/aaperes92/FMR_toolkit/blob/main/docs/'
COLORES_SECCION = {'experimento': COLOR_EXPERIMENTO, 'teoria': COLOR_TEORIA}
FONDO_LATERAL = '#f4f5f7'
FONDO_ELEGIDO = {'experimento': '#dde9ff', 'teoria': '#ffe8d9'}


class VentanaPrincipal(tk.Tk):

    def __init__(self, ruta_config=None):
        super().__init__()
        self.ruta_config = ruta_config
        self.config_gui = configuracion.cargar(ruta_config)
        self.textos = Textos(self.config_gui['idioma'])
        self.ejecutor = EjecutorEnHilo(self.after)
        self.formulario = None
        self.id_tecnica = self.config_gui['ultima_tecnica']
        if not any(t.id == self.id_tecnica for t in TECNICAS):
            self.id_tecnica = TECNICAS[0].id
        # Lo que se recuerda de la última ejecución (para resultados y reportes)
        self.ultimo = {'contexto': {}, 'figuras': [], 'gif': None, 'consola': '',
                       'archivos': [], 'carpeta': None, 'tecnica': None, 'fallo': False}

        configurar_estilos(self)
        self.title(self.textos.t('app.titulo'))
        self.geometry('1180x860')
        self.minsize(900, 640)
        self.protocol('WM_DELETE_WINDOW', self.cerrar)
        self._construir()
        self.after(300, self._pedir_carpeta_si_falta)

    # ==================================================
    # CONSTRUCCIÓN (se rehace entera al cambiar de idioma)
    # ==================================================

    def _construir(self):
        t = self.textos.t
        self.title(t('app.titulo'))

        # ----- Barra superior -----
        arriba = ttk.Frame(self, padding=(10, 6))
        arriba.pack(fill='x')
        ttk.Label(arriba, text=t('app.carpeta_salida')).pack(side='left')
        self.lbl_carpeta = ttk.Label(arriba, font=('TkDefaultFont', 10, 'bold'))
        self.lbl_carpeta.pack(side='left', padx=6)
        Tooltip(self.lbl_carpeta, lambda: self.config_gui['carpeta_salida'] or t('app.sin_carpeta'))
        ttk.Button(arriba, text=t('app.cambiar'), command=self.cambiar_carpeta_salida).pack(side='left')
        ttk.Button(arriba, text=t('app.reportar'),
                   command=lambda: self.abrir_reporte(None)).pack(side='right')
        self.var_idioma = tk.StringVar(value=self.textos.codigo.upper())
        selector = ttk.Combobox(arriba, textvariable=self.var_idioma, values=('ES', 'EN'),
                                state='readonly', width=4)
        selector.pack(side='right', padx=(4, 14))
        selector.bind('<<ComboboxSelected>>', lambda e: self.cambiar_idioma(self.var_idioma.get().lower()))
        ttk.Label(arriba, text=t('app.idioma')).pack(side='right')
        self._actualizar_carpeta()
        ttk.Separator(self).pack(fill='x')

        # ----- Barra de estado (abajo de todo) -----
        estado = ttk.Frame(self, padding=(10, 3))
        estado.pack(side='bottom', fill='x')
        self.lbl_estado = ttk.Label(estado, text='', wraplength=1000, justify='left')
        self.lbl_estado.pack(side='left', fill='x', expand=True)
        ttk.Button(estado, text=t('ejecucion.ver_registro'), command=self.ver_registro).pack(side='right')
        ttk.Separator(self).pack(side='bottom', fill='x')

        # ----- Centro: lateral + formulario (arriba) / resultados (abajo) -----
        vertical = ttk.PanedWindow(self, orient='vertical')
        vertical.pack(fill='both', expand=True)
        centro = ttk.Frame(vertical)
        vertical.add(centro, weight=4)

        self._construir_lateral(centro)
        self.zona_formulario = ttk.Frame(centro)
        self.zona_formulario.pack(side='left', fill='both', expand=True)

        self.resultados = PanelResultados(vertical, self.textos, self.abrir_carpeta_salida,
                                          self.ver_graficos, self.abrir_gif)
        vertical.add(self.resultados, weight=1)

        self.elegir_tecnica(self.id_tecnica)
        self._restaurar_resultados()
        # El formulario arranca con ~70 % del alto; la tabla de resultados con el resto
        self.after(80, lambda: vertical.sashpos(0, max(420, int(self.winfo_height() * 0.68))))

    def _construir_lateral(self, padre):
        t = self.textos.t
        lateral = tk.Frame(padre, background=FONDO_LATERAL, width=270)
        lateral.pack(side='left', fill='y')
        lateral.pack_propagate(False)
        self.items_lateral = {}
        for seccion in SECCIONES:
            color = COLORES_SECCION[seccion]
            tk.Label(lateral, text=t(f'secciones.{seccion}'), background=FONDO_LATERAL, foreground=color,
                     font=('TkDefaultFont', 10, 'bold'), anchor='w').pack(fill='x', padx=12, pady=(14, 2))
            tk.Frame(lateral, background=color, height=2).pack(fill='x', padx=12, pady=(0, 6))
            for tec in (x for x in TECNICAS if x.seccion == seccion):
                fila = tk.Frame(lateral, background=FONDO_LATERAL, cursor='hand2')
                fila.pack(fill='x', padx=8, pady=1)
                barra = tk.Frame(fila, background=color, width=4)
                barra.pack(side='left', fill='y')
                etiqueta = tk.Label(fila, text=t(f'tecnicas.{tec.id}.nombre'), background=FONDO_LATERAL,
                                    anchor='w', justify='left', padx=8, pady=5, wraplength=220)
                etiqueta.pack(side='left', fill='x', expand=True)
                for w in (fila, etiqueta, barra):
                    w.bind('<Button-1>', lambda e, i=tec.id: self.elegir_tecnica(i))
                Tooltip(etiqueta, lambda i=tec.id: t(f'tecnicas.{i}.descripcion'))
                self.items_lateral[tec.id] = (fila, etiqueta, seccion)

    def _marcar_lateral(self):
        for id_tec, (fila, etiqueta, seccion) in self.items_lateral.items():
            fondo = FONDO_ELEGIDO[seccion] if id_tec == self.id_tecnica else FONDO_LATERAL
            fuente = ('TkDefaultFont', 10, 'bold') if id_tec == self.id_tecnica else ('TkDefaultFont', 10)
            fila.configure(background=fondo)
            etiqueta.configure(background=fondo, font=fuente)

    # ==================================================
    # TÉCNICAS Y FORMULARIO
    # ==================================================

    def _guardar_formulario(self):
        if self.formulario is None:
            return
        id_tec = self.formulario.tecnica.id
        for id_variante, textos in self.formulario.estado_para_guardar().items():
            self.config_gui['parametros'][f'{id_tec}/{id_variante}'] = textos
        self.config_gui['variantes'][id_tec] = self.formulario.variante.id
        if self.formulario.entrada():
            self.config_gui['entradas'][id_tec] = self.formulario.entrada()

    def elegir_tecnica(self, id_tecnica):
        if self.ejecutor.ocupado:
            return
        self._guardar_formulario()
        self.id_tecnica = id_tecnica
        self.config_gui['ultima_tecnica'] = id_tecnica
        tec = buscar_tecnica(id_tecnica)
        if self.formulario is not None:
            self.formulario.destroy()
        guardado = {v.id: self.config_gui['parametros'].get(f'{tec.id}/{v.id}', {}) for v in tec.variantes}
        self.formulario = Formulario(self.zona_formulario, tec, self.textos, guardado,
                                     self.config_gui['variantes'].get(tec.id),
                                     self.config_gui['entradas'].get(tec.id, ''),
                                     al_ejecutar=self.ejecutar, al_documentar=self.abrir_documentacion)
        self.formulario.pack(fill='both', expand=True)
        self._marcar_lateral()

    # ==================================================
    # CARPETA DE SALIDA, IDIOMA, DOCUMENTACIÓN
    # ==================================================

    def _actualizar_carpeta(self):
        carpeta = self.config_gui['carpeta_salida']
        texto = carpeta if carpeta else self.textos.t('app.sin_carpeta')
        if len(texto) > 70:
            texto = '…' + texto[-68:]
        self.lbl_carpeta.configure(text=texto)

    def cambiar_carpeta_salida(self):
        actual = self.config_gui['carpeta_salida'] or os.path.expanduser('~')
        ruta = filedialog.askdirectory(parent=self, title=self.textos.t('app.elegir_carpeta_salida'),
                                       initialdir=actual)
        if ruta:
            self.config_gui['carpeta_salida'] = os.path.normpath(ruta)
            self._actualizar_carpeta()
            configuracion.guardar(self.config_gui, self.ruta_config)

    def _pedir_carpeta_si_falta(self):
        carpeta = self.config_gui['carpeta_salida']
        if carpeta and os.path.isdir(carpeta):
            return
        t = self.textos.t
        messagebox.showinfo(t('app.pedir_carpeta_titulo'), t('app.pedir_carpeta_texto'), parent=self)
        self.cambiar_carpeta_salida()

    def cambiar_idioma(self, codigo):
        if codigo == self.textos.codigo or self.ejecutor.ocupado:
            return
        self._guardar_formulario()
        self.formulario = None
        self.textos.cambiar(codigo)
        self.config_gui['idioma'] = self.textos.codigo
        for hijo in self.winfo_children():
            hijo.destroy()
        self._construir()
        configuracion.guardar(self.config_gui, self.ruta_config)

    def abrir_documentacion(self, ruta_doc):
        local = Path(__file__).resolve().parents[2] / 'docs' / ruta_doc
        abrir_con_sistema(local if local.exists() else URL_DOCS + ruta_doc)

    # ==================================================
    # EJECUCIÓN
    # ==================================================

    def ejecutar(self):
        t = self.textos.t
        form = self.formulario
        valores, errores = form.leer()
        if errores:
            self._estado(t('formulario.errores_titulo'), 'error')
            return
        carpeta = self.config_gui['carpeta_salida']
        if not carpeta:
            self.cambiar_carpeta_salida()
            carpeta = self.config_gui['carpeta_salida']
            if not carpeta:
                self._estado(t('formulario.falta_salida'), 'error')
                return
        os.makedirs(carpeta, exist_ok=True)

        variante = form.variante
        kwargs = dict(valores)
        if variante.entrada:
            kwargs[variante.param_entrada] = form.entrada()
        kwargs[variante.param_salida] = carpeta
        kwargs['graficar'] = False

        nombre = t(f'tecnicas.{form.tecnica.id}.nombre')
        if len(form.tecnica.variantes) > 1:
            nombre += ' · ' + t(f'variantes.{variante.id}')
        self._guardar_formulario()
        configuracion.guardar(self.config_gui, self.ruta_config)
        self._cerrar_figuras_anteriores()
        self.ultimo.update({'contexto': {'tecnica': nombre, 'funcion': variante.nombre_funcion,
                                         'parametros': {k: v for k, v in kwargs.items() if k != 'graficar'},
                                         'entrada': form.entrada() if variante.entrada else '',
                                         'salida': carpeta},
                            'tecnica': nombre, 'carpeta': carpeta})
        form.calculando(True)
        self._estado(t('formulario.calculando'), 'info')
        self.ejecutor.lanzar(variante.funcion, kwargs, carpeta, self._al_terminar)

    def _al_terminar(self, resultado):
        t = self.textos.t
        if self.formulario is not None:
            self.formulario.calculando(False)
        carpeta = self.ultimo['carpeta']
        archivos = resultado.archivos_nuevos + resultado.archivos_modificados
        gifs = [a for a in archivos if a.lower().endswith('.gif')]
        self.ultimo.update({'figuras': resultado.figuras, 'consola': resultado.consola,
                            'gif': os.path.join(carpeta, gifs[0]) if gifs else None,
                            'archivos': archivos, 'fallo': not resultado.ok})
        self.ultimo['contexto'].update({'consola': resultado.consola, 'traceback': resultado.traceback})

        self.resultados.cargar(carpeta, archivos)
        self.resultados.mostrar_botones(bool(resultado.figuras), bool(gifs))

        if not resultado.ok:
            self._estado(t('ejecucion.error', mensaje=f'{type(resultado.excepcion).__name__}: '
                                                     f'{resultado.excepcion}'), 'error')
            DialogoError(self, self.textos, self.ultimo['tecnica'], resultado.excepcion,
                         resultado.traceback, self.abrir_reporte)
            return

        partes = []
        if resultado.avisos:
            partes.append(t('ejecucion.listo_avisos', segundos=resultado.duracion, n=len(resultado.avisos)))
            partes += ['   ' + a for a in resultado.avisos[:4]]
        else:
            partes.append(t('ejecucion.listo', segundos=resultado.duracion))
        if resultado.archivos_modificados:
            partes.append(t('ejecucion.sobrescritos', n=len(resultado.archivos_modificados)))
        self._estado('\n'.join(partes), 'aviso' if resultado.avisos else 'ok')
        if resultado.figuras:
            self.ver_graficos()

    def _cerrar_figuras_anteriores(self):
        for fig in self.ultimo['figuras']:
            plt.close(fig)
        self.ultimo['figuras'] = []

    def _restaurar_resultados(self):
        """Después de cambiar de idioma: volver a mostrar la última tabla."""
        if self.ultimo['carpeta'] and self.ultimo['archivos']:
            self.resultados.cargar(self.ultimo['carpeta'], self.ultimo['archivos'])
            self.resultados.mostrar_botones(bool(self.ultimo['figuras']), bool(self.ultimo['gif']))

    def _estado(self, texto, tipo='info'):
        colores = {'info': '#333333', 'ok': '#2b8a3e', 'aviso': '#9c6500', 'error': '#c92a2a'}
        self.lbl_estado.configure(text=texto, foreground=colores.get(tipo, '#333333'))

    # ==================================================
    # RESULTADOS, GRÁFICOS, REGISTRO, REPORTE
    # ==================================================

    def ver_graficos(self):
        if self.ultimo['figuras']:
            VisorFiguras(self, self.ultimo['figuras'], self.ultimo['tecnica'], self.textos)
        else:
            self._estado(self.textos.t('ejecucion.sin_figuras'), 'info')

    def abrir_gif(self):
        if self.ultimo['gif'] and os.path.exists(self.ultimo['gif']):
            abrir_con_sistema(self.ultimo['gif'])

    def abrir_carpeta_salida(self):
        carpeta = self.config_gui['carpeta_salida']
        if carpeta and os.path.isdir(carpeta):
            abrir_con_sistema(carpeta)

    def ver_registro(self):
        VentanaRegistro(self, self.textos, self.ultimo['consola'])

    def abrir_reporte(self, tipo=None):
        if tipo is None:
            tipo = 'error' if self.ultimo['fallo'] else 'resultado'
        DialogoReporte(self, self.textos, tipo, self.ultimo['contexto'],
                       carpeta_para_reportes(self.config_gui['carpeta_salida']))

    # ==================================================
    # CIERRE
    # ==================================================

    def cerrar(self):
        self._guardar_formulario()
        configuracion.guardar(self.config_gui, self.ruta_config)
        self._cerrar_figuras_anteriores()
        self.destroy()


def main():
    ventana = VentanaPrincipal()
    ventana.mainloop()
