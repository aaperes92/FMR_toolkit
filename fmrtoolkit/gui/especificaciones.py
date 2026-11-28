"""Especificación declarativa de las técnicas que muestra la GUI.

Cada técnica dice qué función pública llama, qué entrada necesita (carpeta, archivo o
nada), dónde se le indica la carpeta de salida y qué parámetros se muestran en el
formulario. Los valores por defecto NO se escriben acá: se leen de la firma de cada
función con inspect.signature, así nunca se desincronizan.

Los textos (etiquetas, tooltips, nombres) están en gui/i18n/es.json y en.json.

Para agregar una técnica nueva: importar su función, agregar una Variante/Tecnica a
TECNICAS y sus textos a los dos JSON. No hace falta tocar la ventana.

Este módulo no importa tkinter (se puede testear sin pantalla).
"""

import inspect
from dataclasses import dataclass, field
from typing import Callable

from fmrtoolkit.experiment import broadband, fit_bipolar, fit_positive
from fmrtoolkit.theory import bilayer, dispersion, eigenvectors, single_layer

# Orden de los grupos de campos en el formulario
GRUPOS = ('datos', 'ajuste', 'material', 'anisotropia', 'campo', 'simulacion')

# Parámetros de las funciones que la GUI maneja sola (no se muestran como campos)
PARAMETROS_INTERNOS = ('graficar', 'figuras', 'carpeta', 'carpeta_salida', 'archivo')


@dataclass(frozen=True)
class Parametro:
    """Un campo del formulario.

    nombre    : nombre del parámetro en la firma de la función
    grupo     : uno de GRUPOS
    tipo      : 'real', 'entero', 'bool', 'opcion', 'columnas' (entero o lista "1, 3"),
                'par' (dos reales "2.0, 2.2"), 'extensiones' (".dat, .txt")
    unidad    : unidad que ve el usuario (puede diferir de la de la función)
    factor    : valor_funcion = valor_gui * factor  (GHz -> Hz: 1e9 ; nm -> cm: 1e-7)
    avanzado  : True -> va en el bloque plegable "Avanzado"
    opciones  : valores posibles si tipo == 'opcion'
    minimo, maximo : límites inclusivos en unidades de la GUI (None = sin límite)
    positivo  : True -> tiene que ser > 0
    """
    nombre: str
    grupo: str
    tipo: str = 'real'
    unidad: str = ''
    factor: float = 1.0
    avanzado: bool = False
    opciones: tuple = ()
    minimo: float = None
    maximo: float = None
    positivo: bool = False


@dataclass(frozen=True)
class Advertencia:
    """Aviso que se muestra en el formulario cuando se cumple `condicion(valores)`.

    `valores` es el diccionario de valores ya convertidos a las unidades de la función.
    `clave` es la clave del texto en los JSON (dentro de "advertencias").
    """
    clave: str
    condicion: Callable[[dict], bool] = lambda valores: True


@dataclass(frozen=True)
class Variante:
    """Una función concreta. Una técnica tiene una o más variantes (p. ej. 1 capa / 2 capas).

    entrada        : None, 'carpeta' o 'archivo'
    param_entrada  : nombre del parámetro de la función que recibe la entrada
    filtro_archivo : patrón para el diálogo de archivos
    param_salida   : 'carpeta_salida' o 'carpeta'
    validaciones   : funciones extra valores -> lista de (clave_error, dict_formato)
    """
    id: str
    funcion: Callable
    parametros: tuple
    entrada: str = None
    param_entrada: str = None
    filtro_archivo: str = 'output_*.txt'
    param_salida: str = 'carpeta_salida'
    advertencias: tuple = ()
    validaciones: tuple = ()

    @property
    def nombre_funcion(self):
        return f'{self.funcion.__module__}.{self.funcion.__name__}'

    def valores_por_defecto(self):
        """{nombre: valor por defecto en unidades de la FUNCIÓN}, leídos de la firma."""
        firma = inspect.signature(self.funcion)
        return {p.nombre: firma.parameters[p.nombre].default for p in self.parametros}


@dataclass(frozen=True)
class Tecnica:
    id: str
    seccion: str                # 'experimento' o 'teoria'
    variantes: tuple
    doc: str = ''               # página de la documentación, relativa a docs/
    advertencias: tuple = field(default=())

    def variante(self, id_variante=None):
        if id_variante is None:
            return self.variantes[0]
        for v in self.variantes:
            if v.id == id_variante:
                return v
        return self.variantes[0]


# ==================================================
# VALIDACIONES Y ADVERTENCIAS COMPARTIDAS
# ==================================================

def _rango_campos(v):
    errores = []
    if 'campo_min' in v and 'campo_max' in v and not v['campo_min'] < v['campo_max']:
        errores.append(('campo_min_max', {}))
    return errores


def _rango_angulos(v):
    errores = []
    if 'ang_inicio' in v and 'ang_fin' in v and v['ang_fin'] < v['ang_inicio']:
        errores.append(('ang_inicio_fin', {}))
    return errores


def _margen_mayor_que_paso(v):
    if v['margen_campo'] <= v['paso_campo']:
        return [('margen_paso', {})]
    return []


def _acople_negativo(v):
    return v.get('A', 0) < 0


SOBRESCRIBE = Advertencia('sobrescribe')
ACOPLE_NEGATIVO = Advertencia('acople_negativo', _acople_negativo)


# ==================================================
# PARÁMETROS QUE SE REPITEN
# ==================================================

def _P(nombre, grupo, **kw):
    return Parametro(nombre, grupo, **kw)


FRECUENCIA = _P('frecuencia', 'campo', unidad='GHz', factor=1e9, positivo=True)
G = _P('g', 'material', positivo=True)
MAGN = _P('magn', 'material', unidad='emu/cm³', positivo=True)
HU = _P('Hu', 'anisotropia', unidad='Oe')
HC = _P('Hc', 'anisotropia', unidad='Oe')
ANG_U = _P('ang_u', 'anisotropia', unidad='°')
COL_ANGULO = _P('col_angulo', 'datos', tipo='entero', minimo=0)
DEFASAJE = _P('defasaje_deg', 'datos', unidad='°')
ANGULOS_BARRIDO = (_P('ang_inicio', 'campo', unidad='°'),
                   _P('ang_fin', 'campo', unidad='°'),
                   _P('paso_ang', 'campo', unidad='°', positivo=True))
MARGEN_Y_PASO = (_P('margen_campo', 'simulacion', unidad='Oe', positivo=True, avanzado=True),
                 _P('paso_campo', 'simulacion', unidad='Oe', positivo=True, avanzado=True))
PASO_PHI_M = _P('paso_phi_M', 'simulacion', unidad='°', positivo=True, avanzado=True)
RANGO_CAMPOS = (_P('campo_min', 'campo', unidad='Oe', minimo=0),
                _P('campo_max', 'campo', unidad='Oe', positivo=True),
                _P('paso_campo', 'simulacion', unidad='Oe', positivo=True, avanzado=True))

BICAPA_MATERIAL = (_P('magn_a', 'material', unidad='emu/cm³', positivo=True),
                   _P('magn_b', 'material', unidad='emu/cm³', positivo=True),
                   _P('espesor_a', 'material', unidad='nm', factor=1e-7, positivo=True),
                   _P('espesor_b', 'material', unidad='nm', factor=1e-7, positivo=True),
                   _P('g_a', 'material', positivo=True),
                   _P('g_b', 'material', positivo=True),
                   _P('A', 'material', unidad='erg/cm²'))
BICAPA_ANISOTROPIA = (_P('Hc_a', 'anisotropia', unidad='Oe'), _P('Hc_b', 'anisotropia', unidad='Oe'),
                      _P('Hu_a', 'anisotropia', unidad='Oe'), _P('Hu_b', 'anisotropia', unidad='Oe'),
                      ANG_U)


# ==================================================
# TÉCNICAS
# ==================================================

TECNICAS = (
    # ---------------- EXPERIMENTO ----------------
    Tecnica('fit_positive', 'experimento', doc='experiment/fit_positive.md', variantes=(
        Variante('unica', fit_positive.ajustar_carpeta,
                 entrada='carpeta', param_entrada='carpeta',
                 parametros=(_P('n_lineas', 'ajuste', tipo='opcion', opciones=(1, 2)),
                             _P('ventana', 'ajuste', unidad='Oe', positivo=True),
                             _P('extensiones', 'datos', tipo='extensiones', avanzado=True)),
                 advertencias=(SOBRESCRIBE,)),)),

    Tecnica('fit_bipolar', 'experimento', doc='experiment/fit_bipolar.md', variantes=(
        Variante('unica', fit_bipolar.ajustar_carpeta,
                 entrada='carpeta', param_entrada='carpeta',
                 parametros=(_P('skiprows', 'datos', tipo='entero', minimo=0),
                             _P('extensiones', 'datos', tipo='extensiones', avanzado=True)),
                 advertencias=(SOBRESCRIBE,)),)),

    Tecnica('broadband', 'experimento', doc='experiment/broadband.md', variantes=(
        Variante('unica', broadband.ajustar_banda_ancha,
                 entrada='archivo', param_entrada='archivo',
                 parametros=(_P('col_Hr', 'datos', tipo='entero', minimo=1),
                             _P('col_ancho', 'datos', tipo='entero', minimo=1),
                             _P('g_limites', 'material', tipo='par'),
                             _P('ajustar_Hu', 'anisotropia', tipo='bool'),
                             _P('H_uniaxial', 'anisotropia', unidad='Oe'),
                             _P('H_cubico', 'anisotropia', unidad='Oe'),
                             _P('eje_facil', 'campo', tipo='bool')),
                 advertencias=(Advertencia('eje_dificil', lambda v: not v['eje_facil']),
                               SOBRESCRIBE)),)),

    # ---------------- TEORÍA ----------------
    Tecnica('angular_ip', 'teoria', doc='theory/single_layer.md', variantes=(
        Variante('unica', single_layer.variacion_angular_ip,
                 entrada='archivo', param_entrada='archivo',
                 parametros=(COL_ANGULO, _P('col_Hr', 'datos', tipo='entero', minimo=1), DEFASAJE,
                             MAGN, G, HU, HC, ANG_U, FRECUENCIA, *ANGULOS_BARRIDO,
                             *MARGEN_Y_PASO, PASO_PHI_M),
                 advertencias=(Advertencia('rango_ip'), SOBRESCRIBE),
                 validaciones=(_rango_angulos,)),)),

    Tecnica('angular_op', 'teoria', doc='theory/single_layer.md', variantes=(
        Variante('unica', single_layer.variacion_angular_op,
                 entrada='archivo', param_entrada='archivo',
                 parametros=(COL_ANGULO, _P('col_Hr', 'datos', tipo='entero', minimo=1), DEFASAJE,
                             MAGN, G, FRECUENCIA, *ANGULOS_BARRIDO, *MARGEN_Y_PASO, PASO_PHI_M),
                 advertencias=(Advertencia('rango_ip'), SOBRESCRIBE),
                 validaciones=(_rango_angulos, _margen_mayor_que_paso)),)),

    Tecnica('angular_bicapa', 'teoria', doc='theory/bilayer.md', variantes=(
        Variante('unica', bilayer.variacion_angular_ip_bicapa,
                 entrada='archivo', param_entrada='archivo',
                 parametros=(COL_ANGULO, _P('col_Hr', 'datos', tipo='columnas'), DEFASAJE,
                             *BICAPA_MATERIAL, *BICAPA_ANISOTROPIA, FRECUENCIA, *ANGULOS_BARRIDO,
                             *MARGEN_Y_PASO, PASO_PHI_M),
                 advertencias=(ACOPLE_NEGATIVO, SOBRESCRIBE),
                 validaciones=(_rango_angulos,)),)),

    Tecnica('dispersion', 'teoria', doc='theory/dispersion.md', variantes=(
        Variante('1capa', dispersion.dispersion_1capa, param_salida='carpeta',
                 parametros=(MAGN, G, _P('damp', 'material', minimo=0), HU, HC, ANG_U,
                             _P('ang_campo', 'campo', unidad='°'), *RANGO_CAMPOS, PASO_PHI_M),
                 advertencias=(SOBRESCRIBE,),
                 validaciones=(_rango_campos,)),
        Variante('2capas', dispersion.dispersion_2capas, param_salida='carpeta',
                 parametros=(*BICAPA_MATERIAL,
                             _P('damp_a', 'material', minimo=0), _P('damp_b', 'material', minimo=0),
                             *BICAPA_ANISOTROPIA, _P('ang_campo', 'campo', unidad='°'),
                             *RANGO_CAMPOS, PASO_PHI_M),
                 advertencias=(ACOPLE_NEGATIVO, SOBRESCRIBE),
                 validaciones=(_rango_campos,)),
    )),

    Tecnica('autovectores', 'teoria', doc='theory/eigenvectors.md', variantes=(
        Variante('1capa', eigenvectors.autovectores_1capa, param_salida='carpeta',
                 parametros=(MAGN, G, _P('damp', 'material', minimo=0), HU, HC, ANG_U,
                             FRECUENCIA, _P('ang_campo', 'campo', unidad='°'),
                             _P('h_rf', 'campo', unidad='Oe', positivo=True), *RANGO_CAMPOS,
                             _P('guardar_gif', 'simulacion', tipo='bool'),
                             _P('n_tiempos', 'simulacion', tipo='entero', minimo=3, avanzado=True),
                             PASO_PHI_M),
                 advertencias=(SOBRESCRIBE,),
                 validaciones=(_rango_campos,)),
        Variante('bicapa', eigenvectors.autovectores_bicapa, param_salida='carpeta',
                 parametros=(*BICAPA_MATERIAL,
                             _P('damp_a', 'material', minimo=0), _P('damp_b', 'material', minimo=0),
                             *BICAPA_ANISOTROPIA, FRECUENCIA, _P('ang_campo', 'campo', unidad='°'),
                             _P('h_rf', 'campo', unidad='Oe', positivo=True), *RANGO_CAMPOS,
                             _P('guardar_gif', 'simulacion', tipo='bool'),
                             _P('n_tiempos', 'simulacion', tipo='entero', minimo=3, avanzado=True),
                             PASO_PHI_M),
                 advertencias=(ACOPLE_NEGATIVO, SOBRESCRIBE),
                 validaciones=(_rango_campos,)),
    )),
)

SECCIONES = ('experimento', 'teoria')


def tecnica(id_tecnica):
    for t in TECNICAS:
        if t.id == id_tecnica:
            return t
    raise KeyError(id_tecnica)
