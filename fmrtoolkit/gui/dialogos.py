"""Diálogos: error de ejecución, reporte de problemas y registro de la última ejecución."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

from fmrtoolkit.gui import configuracion, reporte
from fmrtoolkit.gui.widgets import abrir_con_sistema


def _centrar(ventana, padre):
    ventana.update_idletasks()
    x = padre.winfo_rootx() + (padre.winfo_width() - ventana.winfo_width()) // 2
    y = padre.winfo_rooty() + (padre.winfo_height() - ventana.winfo_height()) // 3
    ventana.geometry(f'+{max(x, 0)}+{max(y, 0)}')


class DialogoError(tk.Toplevel):
    """Mensaje entendible + "Ver detalles" (traceback) + "Reportar este error"."""

    def __init__(self, padre, textos, nombre_tecnica, excepcion, traceback_texto, al_reportar):
        super().__init__(padre)
        t = textos.t
        self.textos = textos
        self.title(t('dialogo_error.titulo'))
        self.transient(padre)
        self.resizable(True, True)
        marco = ttk.Frame(self, padding=14)
        marco.pack(fill='both', expand=True)

        ttk.Label(marco, text=t('dialogo_error.texto', tecnica=nombre_tecnica)).pack(anchor='w')
        mensaje = f'{type(excepcion).__name__}: {excepcion}' if excepcion is not None else '-'
        ttk.Label(marco, text=mensaje, style='Error.TLabel', wraplength=560,
                  justify='left').pack(anchor='w', pady=(6, 6))
        ttk.Label(marco, text=t('dialogo_error.consejo'), wraplength=560, justify='left').pack(anchor='w')

        self.detalles = scrolledtext.ScrolledText(marco, height=14, width=90, font=('TkFixedFont', 9))
        self.detalles.insert('1.0', traceback_texto or '')
        self.detalles.configure(state='disabled')

        botones = ttk.Frame(marco)
        botones.pack(fill='x', pady=(10, 0))
        self.boton_detalles = ttk.Button(botones, text=t('dialogo_error.ver_detalles'), command=self._alternar)
        self.boton_detalles.pack(side='left')
        ttk.Button(botones, text=t('dialogo_error.reportar'),
                   command=lambda: (self.destroy(), al_reportar('error'))).pack(side='left', padx=6)
        ttk.Button(botones, text=t('dialogo_error.cerrar'), command=self.destroy).pack(side='right')
        self._mostrando = False
        self._marco = marco
        _centrar(self, padre)
        self.grab_set()

    def _alternar(self):
        t = self.textos.t
        self._mostrando = not self._mostrando
        if self._mostrando:
            self.detalles.pack(fill='both', expand=True, pady=(10, 0), before=self.boton_detalles.master)
            self.boton_detalles.configure(text=t('dialogo_error.ocultar_detalles'))
        else:
            self.detalles.pack_forget()
            self.boton_detalles.configure(text=t('dialogo_error.ver_detalles'))


class DialogoReporte(tk.Toplevel):
    """Reporte de un problema. Se arma con la información de la última ejecución, el
    usuario la puede editar, y se abre el cliente de correo con mailto:."""

    def __init__(self, padre, textos, tipo, contexto, carpeta_reportes):
        super().__init__(padre)
        t = textos.t
        self.textos, self.contexto = textos, contexto or {}
        self.carpeta_reportes = carpeta_reportes
        self.title(t('reporte.titulo_dialogo'))
        self.transient(padre)
        self.geometry('760x640')
        marco = ttk.Frame(self, padding=12)
        marco.pack(fill='both', expand=True)

        ttk.Label(marco, text=t('reporte.tipo_pregunta'), style='Titulo.TLabel').pack(anchor='w')
        self.var_tipo = tk.StringVar(value=tipo)
        for valor in ('error', 'resultado'):
            ttk.Radiobutton(marco, text=t(f'reporte.tipo_{valor}'), value=valor,
                            variable=self.var_tipo).pack(anchor='w', padx=8)

        ttk.Label(marco, text=t('reporte.descripcion_pregunta')).pack(anchor='w', pady=(10, 2))
        self.descripcion = scrolledtext.ScrolledText(marco, height=5, wrap='word')
        self.descripcion.pack(fill='x')

        ttk.Label(marco, text=t('reporte.info_adjunta')).pack(anchor='w', pady=(10, 2))
        self.info = scrolledtext.ScrolledText(marco, height=14, wrap='none', font=('TkFixedFont', 9))
        self.info.insert('1.0', reporte.contexto_reporte(textos, self.contexto))
        self.info.pack(fill='both', expand=True)

        botones = ttk.Frame(marco)
        botones.pack(fill='x', pady=(10, 0))
        ttk.Label(botones, text=configuracion.CORREO_REPORTES, foreground='#777777').pack(side='left')
        ttk.Button(botones, text=t('reporte.cancelar'), command=self.destroy).pack(side='right')
        ttk.Button(botones, text=t('reporte.enviar'), command=self._enviar).pack(side='right', padx=6)
        _centrar(self, padre)
        self.descripcion.focus_set()

    def _enviar(self):
        t = self.textos.t
        tipo = self.var_tipo.get()
        descripcion = self.descripcion.get('1.0', 'end').strip()
        texto = reporte.encabezado_reporte(self.textos, tipo, descripcion) + self.info.get('1.0', 'end')
        url, ruta = reporte.preparar_envio(self.textos, configuracion.CORREO_REPORTES, tipo, descripcion,
                                           self.contexto, texto, self.carpeta_reportes)
        if abrir_con_sistema(url):
            if ruta is None:
                messagebox.showinfo(t('reporte.titulo_dialogo'), t('reporte.enviado'), parent=self)
            else:
                messagebox.showinfo(t('reporte.titulo_dialogo'),
                                    t('reporte.enviado_con_archivo', ruta=ruta), parent=self)
        else:
            ruta = ruta or reporte.guardar_reporte(texto, self.carpeta_reportes)
            messagebox.showwarning(t('reporte.titulo_dialogo'),
                                   t('reporte.sin_cliente', ruta=ruta, correo=configuracion.CORREO_REPORTES),
                                   parent=self)
        self.destroy()


class VentanaRegistro(tk.Toplevel):
    """Salida de consola capturada en la última ejecución."""

    def __init__(self, padre, textos, consola):
        super().__init__(padre)
        self.title(textos.t('ejecucion.registro_titulo'))
        self.geometry('820x420')
        texto = scrolledtext.ScrolledText(self, wrap='none', font=('TkFixedFont', 9))
        texto.pack(fill='both', expand=True)
        texto.insert('1.0', consola or textos.t('ejecucion.registro_vacio'))
        texto.configure(state='disabled')


def carpeta_para_reportes(carpeta_salida):
    """Dónde guardar un reporte largo: la carpeta de salida o ~/.fmrtoolkit."""
    if carpeta_salida and Path(carpeta_salida).is_dir():
        return carpeta_salida
    return str(Path.home() / '.fmrtoolkit')
