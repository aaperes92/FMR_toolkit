"""Conversión entre el texto de los campos de la GUI y los valores de las funciones.

- texto  -> valor en unidades de la GUI      : leer_texto()
- valor GUI <-> valor de la función           : a_funcion(), a_gui()   (GHz<->Hz, nm<->cm)
- valor de la función -> texto del campo      : texto_por_defecto()
- validación de todos los campos de una variante: validar()

Los errores se informan con ErrorValidacion(clave, **datos); la clave corresponde a un
texto de "errores" en los JSON de idioma. Este módulo no importa tkinter.
"""

import math
import re


class ErrorValidacion(ValueError):
    def __init__(self, clave, **datos):
        super().__init__(clave)
        self.clave = clave
        self.datos = datos


# ==================================================
# NÚMEROS Y LISTAS
# ==================================================

def _real(texto):
    """Acepta coma o punto decimal: '9,76' o '9.76'. Un número sin decimales ('1155')
    se devuelve como int, igual que el valor por defecto de la firma: así los nombres de
    archivo que arman las funciones (p. ej. 'magn1155') quedan iguales que desde un script."""
    t = str(texto).strip().replace(',', '.')
    if not t:
        raise ErrorValidacion('vacio')
    if re.fullmatch(r'[+-]?\d+', t):
        return int(t)
    try:
        valor = float(t)
    except ValueError:
        raise ErrorValidacion('no_numero', texto=texto) from None
    if not math.isfinite(valor):
        raise ErrorValidacion('no_numero', texto=texto)
    return valor


def _entero(texto):
    t = str(texto).strip()
    if not t:
        raise ErrorValidacion('vacio')
    try:
        return int(t)
    except ValueError:
        raise ErrorValidacion('no_entero', texto=texto) from None


def _partes(texto):
    """'1, 3' / '(1, 3)' / '[1; 3]' / '1 3' -> ['1', '3']"""
    t = str(texto).strip().strip('()[]')
    for sep in (';', ','):
        t = t.replace(sep, ' ')
    return [p for p in t.split() if p]


def leer_texto(texto, parametro):
    """Convierte el texto de un campo en el valor en unidades de la GUI. Para 'bool' y
    'opcion' el formulario ya entrega el valor (no texto)."""
    tipo = parametro.tipo
    if tipo == 'real':
        return _real(texto)
    if tipo == 'entero':
        return _entero(texto)
    if tipo == 'bool':
        return bool(texto)
    if tipo == 'opcion':
        valor = int(texto) if str(texto).strip().lstrip('-').isdigit() else texto
        if valor not in parametro.opciones:
            raise ErrorValidacion('opcion_invalida', opciones=', '.join(map(str, parametro.opciones)))
        return valor
    if tipo == 'columnas':                       # entero o lista de enteros: "1" o "1, 3"
        partes = _partes(texto)
        if not partes:
            raise ErrorValidacion('vacio')
        columnas = [_entero(p) for p in partes]
        return columnas[0] if len(columnas) == 1 else columnas
    if tipo == 'par':                            # dos reales, el primero menor
        partes = _partes(texto)
        if len(partes) != 2:
            raise ErrorValidacion('par_invalido')
        a, b = _real(partes[0]), _real(partes[1])
        if not a < b:
            raise ErrorValidacion('par_orden')
        return (a, b)
    if tipo == 'extensiones':                    # ".dat, .txt" -> ('.dat', '.txt')
        partes = _partes(texto)
        if not partes:
            raise ErrorValidacion('vacio')
        return tuple(p if p.startswith('.') else '.' + p for p in partes)
    raise ValueError(f'tipo de parámetro desconocido: {tipo}')


# ==================================================
# UNIDADES
# ==================================================

def a_funcion(valor_gui, parametro):
    """Valor en unidades de la GUI -> unidades de la función (GHz -> Hz, nm -> cm)."""
    if parametro.factor == 1.0 or parametro.tipo != 'real':
        return valor_gui
    return valor_gui * parametro.factor


def a_gui(valor_funcion, parametro):
    """Valor en unidades de la función -> unidades de la GUI (Hz -> GHz, cm -> nm)."""
    if parametro.factor == 1.0 or parametro.tipo != 'real':
        return valor_funcion
    return valor_funcion / parametro.factor


def formatear(valor):
    """Texto para mostrar un valor en un campo, sin ruido de punto flotante (10.000000000000002 -> 10)."""
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, float):
        return format(valor, '.12g')
    if isinstance(valor, (list, tuple)):
        return ', '.join(str(formatear(v)) for v in valor)
    return str(valor)


def texto_por_defecto(parametro, valor_funcion):
    """Lo que se escribe en el campo para el valor por defecto de la firma."""
    if parametro.tipo in ('bool', 'opcion'):
        return valor_funcion
    return formatear(a_gui(valor_funcion, parametro))


# ==================================================
# VALIDACIÓN DE UNA VARIANTE COMPLETA
# ==================================================

def _limites(valor, p):
    if p.tipo not in ('real', 'entero'):
        return
    if p.positivo and not valor > 0:
        raise ErrorValidacion('debe_ser_positivo')
    if p.minimo is not None and valor < p.minimo:
        raise ErrorValidacion('menor_que_minimo', minimo=formatear(p.minimo))
    if p.maximo is not None and valor > p.maximo:
        raise ErrorValidacion('mayor_que_maximo', maximo=formatear(p.maximo))


def validar(variante, textos):
    """Convierte y valida todos los campos de una variante.

    textos : {nombre: texto (o bool/valor para 'bool'/'opcion')}
    Devuelve (valores, errores):
        valores : {nombre: valor en unidades de la FUNCIÓN} (solo los que se pudieron leer)
        errores : lista de (nombre_parametro o None, ErrorValidacion)
    """
    valores, errores = {}, []
    for p in variante.parametros:
        try:
            valor_gui = leer_texto(textos[p.nombre], p)
            _limites(valor_gui, p)
            valores[p.nombre] = a_funcion(valor_gui, p)
        except ErrorValidacion as error:
            errores.append((p.nombre, error))
    if not errores:                              # reglas entre campos, solo si todos se leyeron
        for regla in variante.validaciones:
            for clave, datos in regla(valores):
                errores.append((None, ErrorValidacion(clave, **datos)))
    return valores, errores


def advertencias_activas(variante, tecnica, valores):
    """Claves de las advertencias que aplican a estos valores."""
    claves = []
    for adv in tuple(tecnica.advertencias) + tuple(variante.advertencias):
        try:
            if adv.condicion(valores):
                claves.append(adv.clave)
        except (KeyError, TypeError):            # todavía faltan valores válidos
            pass
    return claves


def texto_plano(texto):
    """Saca el formato matemático de matplotlib: 'erg/cm$^2$, H$_r$' -> 'erg/cm2, Hr'."""
    for caracter in ('$', '^', '_', '{', '}', '\\'):
        texto = texto.replace(caracter, '')
    return texto.replace('\n', ' · ').strip()
