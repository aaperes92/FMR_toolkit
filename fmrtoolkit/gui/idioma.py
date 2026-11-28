"""Textos de la interfaz en español e inglés.

Todos los textos están en gui/i18n/<idioma>.json, anidados por secciones. Se piden con
claves con puntos:  textos.t('app.titulo'),  textos.t('errores.no_numero', texto='abc').

Si una clave falta en el idioma elegido, se usa la del español; si tampoco está, se
devuelve la clave (así un texto faltante se ve, pero no rompe la ventana).

Este módulo no importa tkinter.
"""

import json
from pathlib import Path

CARPETA_I18N = Path(__file__).resolve().parent / 'i18n'
IDIOMAS = ('es', 'en')


def _cargar_json(codigo):
    with open(CARPETA_I18N / f'{codigo}.json', encoding='utf-8') as f:
        return json.load(f)


def _buscar(arbol, clave):
    nodo = arbol
    for parte in clave.split('.'):
        if not isinstance(nodo, dict) or parte not in nodo:
            return None
        nodo = nodo[parte]
    return nodo


class Textos:
    def __init__(self, codigo='es'):
        self._base = _cargar_json('es')
        self.cambiar(codigo)

    def cambiar(self, codigo):
        self.codigo = codigo if codigo in IDIOMAS else 'es'
        self._arbol = self._base if self.codigo == 'es' else _cargar_json(self.codigo)

    def existe(self, clave):
        return _buscar(self._arbol, clave) is not None or _buscar(self._base, clave) is not None

    def t(self, clave, **datos):
        texto = _buscar(self._arbol, clave)
        if texto is None:
            texto = _buscar(self._base, clave)
        if texto is None:
            return clave
        if isinstance(texto, str) and datos:
            try:
                return texto.format(**datos)
            except (KeyError, IndexError, ValueError):
                return texto
        return texto

    # ---------- atajos para parámetros y técnicas ----------

    def parametro(self, id_tecnica, nombre, campo):
        """Texto de un parámetro ('etiqueta', 'ayuda', 'formula' o 'aviso'). Primero busca
        un texto específico de la técnica y si no, el general."""
        especifico = f'parametros_tecnica.{id_tecnica}.{nombre}.{campo}'
        if self.existe(especifico):
            return self.t(especifico)
        general = f'parametros.{nombre}.{campo}'
        return self.t(general) if self.existe(general) else ''

    def tooltip_parametro(self, id_tecnica, parametro):
        """Texto completo del tooltip de un campo."""
        partes = [self.parametro(id_tecnica, parametro.nombre, 'ayuda')]
        if parametro.unidad:
            partes.append(f"{self.t('tooltip.unidad')}: {parametro.unidad}")
        formula = self.parametro(id_tecnica, parametro.nombre, 'formula')
        if formula:
            partes.append(f"{self.t('tooltip.formula')}: {formula}")
        partes.append(f"{self.t('tooltip.python')}: {parametro.nombre}")
        aviso = self.parametro(id_tecnica, parametro.nombre, 'aviso')
        if aviso:
            partes.append(f"⚠ {aviso}")
        return '\n'.join(p for p in partes if p)
