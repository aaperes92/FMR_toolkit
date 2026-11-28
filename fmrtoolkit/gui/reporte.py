"""Reporte de problemas: arma el texto, el enlace mailto: y guarda el reporte completo.

No se envía nada automáticamente ni se guardan contraseñas: se abre el cliente de correo
del usuario con el mensaje ya escrito, y el usuario decide si lo manda.

Este módulo no importa tkinter.
"""

import datetime
import importlib.metadata
import platform
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

# Largo máximo seguro de un enlace mailto: (algunos clientes cortan alrededor de 2000)
LARGO_MAXIMO_MAILTO = 1800


def version_fmrtoolkit():
    try:
        return importlib.metadata.version('fmrtoolkit')
    except importlib.metadata.PackageNotFoundError:
        return 'desconocida (no instalado con pip)'


def commit_git():
    """Commit actual del repositorio donde está el paquete, si se puede obtener."""
    carpeta = Path(__file__).resolve().parents[2]
    try:
        commit = subprocess.run(['git', '-C', str(carpeta), 'rev-parse', '--short', 'HEAD'],
                                capture_output=True, text=True, timeout=3)
        if commit.returncode != 0:
            return 'desconocido'
        cambios = subprocess.run(['git', '-C', str(carpeta), 'status', '--porcelain', '--untracked-files=no'],
                                 capture_output=True, text=True, timeout=3)
        sucio = ' (+ cambios locales)' if cambios.stdout.strip() else ''
        return commit.stdout.strip() + sucio
    except (OSError, subprocess.SubprocessError):
        return 'desconocido'


def info_entorno():
    """Versiones del programa y del sistema, para adjuntar a los reportes."""
    info = {'fmrtoolkit': version_fmrtoolkit(),
            'commit': commit_git(),
            'python': sys.version.split()[0],
            'sistema': platform.platform()}
    for modulo in ('numpy', 'scipy', 'sympy', 'matplotlib'):
        try:
            info[modulo] = __import__(modulo).__version__
        except Exception:                      # noqa: BLE001 - solo es informativo
            info[modulo] = 'no disponible'
    return info


def encabezado_reporte(textos, tipo, descripcion):
    """Primera parte del reporte: tipo de problema, fecha y descripción del usuario."""
    t = textos.t
    return '\n'.join([f"{t('reporte.titulo_tipo')}: {t('reporte.tipo_' + tipo)}",
                      f"{t('reporte.fecha')}: {datetime.datetime.now():%Y-%m-%d %H:%M}",
                      '',
                      f"== {t('reporte.descripcion')} ==",
                      (descripcion or '').strip() or '-',
                      '']) + '\n'


def contexto_reporte(textos, contexto, entorno=None):
    """Segunda parte del reporte: técnica, parámetros, entorno, traceback y consola.
    Es la parte que el usuario puede revisar y editar en el diálogo."""
    t = textos.t
    entorno = info_entorno() if entorno is None else entorno
    ctx = contexto or {}
    lineas = [f"== {t('reporte.tecnica')} ==",
              f"{ctx.get('tecnica', '-')}  ({ctx.get('funcion', '-')})",
              f"{t('reporte.entrada')}: {ctx.get('entrada') or '-'}",
              f"{t('reporte.salida')}: {ctx.get('salida') or '-'}",
              '',
              f"== {t('reporte.parametros')} =="]
    parametros = ctx.get('parametros') or {}
    lineas += [f'{k} = {v!r}' for k, v in parametros.items()] or ['-']
    lineas += ['', f"== {t('reporte.entorno')} =="]
    lineas += [f'{k}: {v}' for k, v in entorno.items()]
    if ctx.get('traceback'):
        lineas += ['', f"== {t('reporte.traceback')} ==", ctx['traceback'].rstrip()]
    if ctx.get('consola'):
        lineas += ['', f"== {t('reporte.consola')} ==", ctx['consola'].rstrip()]
    return '\n'.join(lineas) + '\n'


def armar_reporte(textos, tipo, descripcion, contexto, entorno=None):
    """Texto completo del reporte.

    textos   : objeto Textos (idioma.py)
    tipo     : 'error' o 'resultado'
    contexto : dict con 'tecnica', 'funcion', 'parametros' (dict), 'entrada', 'salida',
               'traceback' y 'consola' (todos opcionales)
    """
    return encabezado_reporte(textos, tipo, descripcion) + contexto_reporte(textos, contexto, entorno)


def resumen_reporte(textos, tipo, descripcion, contexto, ruta_archivo):
    """Versión corta para el cuerpo del email cuando el reporte completo no entra."""
    t = textos.t
    ctx = contexto or {}
    ultima_linea_error = ''
    if ctx.get('traceback'):
        ultima_linea_error = ctx['traceback'].strip().splitlines()[-1]
    lineas = [f"{t('reporte.titulo_tipo')}: {t('reporte.tipo_' + tipo)}",
              f"{t('reporte.tecnica')}: {ctx.get('tecnica', '-')}  ({ctx.get('funcion', '-')})",
              '',
              (descripcion or '').strip()[:500] or '-']
    if ultima_linea_error:
        lineas += ['', f"{t('reporte.error')}: {ultima_linea_error[:300]}"]
    lineas += ['', t('reporte.adjuntar', archivo=Path(ruta_archivo).name)]
    return '\n'.join(lineas)


def enlace_mailto(destino, asunto, cuerpo):
    return f'mailto:{destino}?subject={quote(asunto)}&body={quote(cuerpo)}'


def guardar_reporte(texto, carpeta):
    """Guarda el reporte completo como .txt y devuelve la ruta."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f'reporte_fmrtoolkit_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt'
    ruta.write_text(texto, encoding='utf-8')
    return ruta


def preparar_envio(textos, destino, tipo, descripcion, contexto, texto_reporte, carpeta):
    """Decide qué se manda por email.

    Devuelve (url_mailto, ruta_reporte_o_None). Si el reporte completo entra en el enlace
    se manda entero; si no, se guarda como .txt en `carpeta` y el email lleva un resumen
    que pide adjuntar el archivo.
    """
    asunto = textos.t('reporte.asunto', tecnica=(contexto or {}).get('tecnica', '-'))
    url = enlace_mailto(destino, asunto, texto_reporte)
    if len(url) <= LARGO_MAXIMO_MAILTO:
        return url, None
    ruta = guardar_reporte(texto_reporte, carpeta)
    cuerpo = resumen_reporte(textos, tipo, descripcion, contexto, ruta)
    url = enlace_mailto(destino, asunto, cuerpo)
    if len(url) > LARGO_MAXIMO_MAILTO:         # resumen todavía largo: se corta la descripción
        url = url[:LARGO_MAXIMO_MAILTO]
        while '%' in url[-3:]:                 # no cortar en medio de un %XX
            url = url[:-1]
    return url, ruta
