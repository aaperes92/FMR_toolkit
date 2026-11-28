"""Ejecución de una técnica: captura de la salida, de los avisos y de las figuras.

ejecutar()        corre la función en el hilo actual y devuelve un Resultado. No usa
                  tkinter, así que se puede testear sin pantalla.
EjecutorEnHilo    corre ejecutar() en un hilo aparte. El hilo NO toca la interfaz: deja
                  el resultado en una cola, y el hilo principal la revisa con root.after
                  (tkinter no es thread-safe).

Matplotlib: la GUI fija el backend 'Agg' antes de importar el toolkit (ver __main__.py).
Con Agg, las funciones pueden crear figuras con pyplot en el hilo de cálculo sin abrir
ventanas ni tocar Tk; las figuras se incrustan después en el hilo principal.
"""

import contextlib
import io
import os
import queue
import sys
import threading
import time
import traceback
import warnings
from dataclasses import dataclass, field

PALABRAS_AVISO = ('AVISO', 'WARNING', 'ADVERTENCIA')


@dataclass
class Resultado:
    ok: bool
    valor: object = None
    excepcion: BaseException = None
    traceback: str = ''
    consola: str = ''
    avisos: list = field(default_factory=list)
    figuras: list = field(default_factory=list)
    archivos_nuevos: list = field(default_factory=list)
    archivos_modificados: list = field(default_factory=list)
    duracion: float = 0.0


class _Duplicador(io.TextIOBase):
    """Escribe en un buffer y además en la consola original (útil para depurar)."""

    def __init__(self, buffer, original):
        self.buffer_texto, self.original = buffer, original

    def write(self, texto):
        self.buffer_texto.write(texto)
        if self.original is not None:
            try:
                self.original.write(texto)
            except Exception:                  # noqa: BLE001 - la consola puede no existir
                pass
        return len(texto)

    def flush(self):
        if self.original is not None:
            try:
                self.original.flush()
            except Exception:                  # noqa: BLE001
                pass


def foto_carpeta(carpeta):
    """{nombre: (fecha de modificación, tamaño)} de los archivos de una carpeta."""
    try:
        return {e.name: (e.stat().st_mtime_ns, e.stat().st_size)
                for e in os.scandir(carpeta) if e.is_file()}
    except OSError:
        return {}


def avisos_de_consola(texto):
    return [linea.strip() for linea in texto.splitlines()
            if any(p in linea for p in PALABRAS_AVISO)]


def ejecutar(funcion, kwargs, carpeta_salida=None):
    """Corre funcion(**kwargs) capturando stdout, stderr, warnings y figuras.

    Si `funcion` acepta `figuras`, se le pasa una lista para recibirlas. Nunca lanza
    excepciones: los errores quedan en Resultado.excepcion y Resultado.traceback.
    """
    import matplotlib.pyplot as plt            # import diferido: el backend ya está fijado

    buffer = io.StringIO()
    figuras = []
    kwargs = dict(kwargs)
    if 'figuras' in kwargs or _acepta(funcion, 'figuras'):
        kwargs['figuras'] = figuras
    antes = foto_carpeta(carpeta_salida) if carpeta_salida else {}
    inicio = time.time()
    resultado = Resultado(ok=False)

    with warnings.catch_warnings(record=True) as capturados:
        warnings.simplefilter('always')
        with contextlib.redirect_stdout(_Duplicador(buffer, sys.__stdout__)), \
                contextlib.redirect_stderr(_Duplicador(buffer, sys.__stderr__)):
            try:
                resultado.valor = funcion(**kwargs)
                resultado.ok = True
            except BaseException as error:     # noqa: BLE001 - se informa en la GUI
                resultado.excepcion = error
                resultado.traceback = traceback.format_exc()

    resultado.duracion = time.time() - inicio
    for w in capturados:
        buffer.write(f'{w.category.__name__}: {w.message}\n')
    resultado.consola = buffer.getvalue()
    resultado.avisos = avisos_de_consola(resultado.consola) + \
        [f'{w.category.__name__}: {w.message}' for w in capturados]
    resultado.figuras = figuras

    # Figuras que quedaron registradas en pyplot pero que no pidió nadie: se cierran
    for numero in plt.get_fignums():
        fig = plt.figure(numero)
        if fig not in figuras:
            plt.close(fig)

    if carpeta_salida:
        despues = foto_carpeta(carpeta_salida)
        resultado.archivos_nuevos = sorted(n for n in despues if n not in antes)
        resultado.archivos_modificados = sorted(n for n in despues
                                                if n in antes and despues[n] != antes[n])
    return resultado


def _acepta(funcion, nombre):
    import inspect
    try:
        return nombre in inspect.signature(funcion).parameters
    except (TypeError, ValueError):
        return False


class EjecutorEnHilo:
    """Corre ejecutar() en un hilo y avisa en el hilo principal cuando termina.

    programar(ms, callback) es root.after. Al terminar se llama a al_terminar(resultado)
    desde el hilo principal.
    """

    INTERVALO_MS = 100

    def __init__(self, programar):
        self.programar = programar
        self.cola = queue.Queue()
        self.ocupado = False

    def lanzar(self, funcion, kwargs, carpeta_salida, al_terminar):
        if self.ocupado:
            return False
        self.ocupado = True
        hilo = threading.Thread(target=lambda: self.cola.put(ejecutar(funcion, kwargs, carpeta_salida)),
                                daemon=True)
        hilo.start()
        self.programar(self.INTERVALO_MS, lambda: self._revisar(al_terminar))
        return True

    def _revisar(self, al_terminar):
        try:
            resultado = self.cola.get_nowait()
        except queue.Empty:
            self.programar(self.INTERVALO_MS, lambda: self._revisar(al_terminar))
            return
        self.ocupado = False
        al_terminar(resultado)
