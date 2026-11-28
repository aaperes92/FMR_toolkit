"""Configuración de la GUI que se recuerda entre sesiones.

Se guarda en ~/.fmrtoolkit/gui_config.json (o en la ruta de la variable de entorno
FMRTOOLKIT_GUI_CONFIG). Si el archivo no existe, está corrupto o es de una versión
vieja, se usan los valores por defecto sin romper nada.

Este módulo no importa tkinter.
"""

import copy
import json
import os
from pathlib import Path

# Dirección a la que se envían los reportes de problemas (cambiar por la real)
CORREO_REPORTES = "REEMPLAZAR@ejemplo.com"

# Subir este número si cambia la estructura del archivo de configuración
VERSION_CONFIG = 1

POR_DEFECTO = {
    'version': VERSION_CONFIG,
    'idioma': 'es',
    'carpeta_salida': '',
    'ultima_tecnica': 'fit_positive',
    'variantes': {},       # {id_tecnica: id_variante elegida}
    'entradas': {},        # {id_tecnica: última carpeta/archivo de entrada}
    'parametros': {},      # {"id_tecnica/id_variante": {nombre: texto}}
}


def ruta_config():
    ruta = os.environ.get('FMRTOOLKIT_GUI_CONFIG')
    return Path(ruta) if ruta else Path.home() / '.fmrtoolkit' / 'gui_config.json'


def cargar(ruta=None):
    """Devuelve la configuración. Nunca lanza excepciones: ante cualquier problema
    devuelve los valores por defecto."""
    ruta = Path(ruta) if ruta else ruta_config()
    config = copy.deepcopy(POR_DEFECTO)
    try:
        with open(ruta, encoding='utf-8') as f:
            leida = json.load(f)
    except (OSError, ValueError):
        return config
    if not isinstance(leida, dict) or leida.get('version') != VERSION_CONFIG:
        return config                         # versión vieja o formato desconocido
    for clave, defecto in POR_DEFECTO.items():
        valor = leida.get(clave, defecto)
        if isinstance(valor, type(defecto)):  # se ignoran valores con tipo incorrecto
            config[clave] = valor
    if config['idioma'] not in ('es', 'en'):
        config['idioma'] = 'es'
    return config


def guardar(config, ruta=None):
    """Guarda la configuración. Devuelve True si pudo. Escribe en un archivo temporal y
    lo renombra, para no dejar un JSON a medio escribir si algo falla."""
    ruta = Path(ruta) if ruta else ruta_config()
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = ruta.with_suffix('.tmp')
        with open(temporal, 'w', encoding='utf-8') as f:
            json.dump({**config, 'version': VERSION_CONFIG}, f, ensure_ascii=False, indent=2)
        os.replace(temporal, ruta)
        return True
    except OSError:
        return False
