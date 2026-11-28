"""Las especificaciones de la GUI están sincronizadas con las funciones y con los textos.

Correr desde la raíz del repo:  python -m unittest discover tests
"""

import inspect
import unittest

import matplotlib
matplotlib.use('Agg')

from fmrtoolkit.gui import conversion
from fmrtoolkit.gui.especificaciones import GRUPOS, PARAMETROS_INTERNOS, SECCIONES, TECNICAS
from fmrtoolkit.gui.idioma import IDIOMAS, Textos, _cargar_json


def _variantes():
    for t in TECNICAS:
        for v in t.variantes:
            yield t, v


def _claves(arbol, prefijo=''):
    claves = set()
    for k, v in arbol.items():
        clave = f'{prefijo}.{k}' if prefijo else k
        if isinstance(v, dict):
            claves |= _claves(v, clave)
        else:
            claves.add(clave)
    return claves


class TestEspecificaciones(unittest.TestCase):

    def test_cada_parametro_existe_en_la_firma(self):
        for t, v in _variantes():
            firma = inspect.signature(v.funcion).parameters
            for p in v.parametros:
                with self.subTest(tecnica=t.id, variante=v.id, parametro=p.nombre):
                    self.assertIn(p.nombre, firma)
                    self.assertIsNot(firma[p.nombre].default, inspect.Parameter.empty,
                                     'la GUI necesita un valor por defecto en la firma')

    def test_todo_parametro_de_la_firma_esta_en_la_gui(self):
        """Si a una función se le agrega un parámetro, este test avisa que falta en la GUI."""
        for t, v in _variantes():
            nombres = {p.nombre for p in v.parametros}
            for nombre in inspect.signature(v.funcion).parameters:
                with self.subTest(tecnica=t.id, variante=v.id, parametro=nombre):
                    self.assertTrue(nombre in nombres or nombre in PARAMETROS_INTERNOS,
                                    f'{nombre} no está en la especificación de la GUI')

    def test_entrada_salida_y_figuras_en_la_firma(self):
        for t, v in _variantes():
            firma = inspect.signature(v.funcion).parameters
            with self.subTest(tecnica=t.id, variante=v.id):
                self.assertIn(v.param_salida, firma)
                self.assertIn('figuras', firma)
                self.assertIn('graficar', firma)
                if v.entrada:
                    self.assertIn(v.param_entrada, firma)

    def test_grupos_secciones_y_tipos_validos(self):
        tipos = {'real', 'entero', 'bool', 'opcion', 'columnas', 'par', 'extensiones'}
        for t, v in _variantes():
            self.assertIn(t.seccion, SECCIONES)
            for p in v.parametros:
                with self.subTest(tecnica=t.id, parametro=p.nombre):
                    self.assertIn(p.grupo, GRUPOS)
                    self.assertIn(p.tipo, tipos)

    def test_ids_unicos(self):
        ids = [t.id for t in TECNICAS]
        self.assertEqual(len(ids), len(set(ids)))
        for t in TECNICAS:
            ids_v = [v.id for v in t.variantes]
            self.assertEqual(len(ids_v), len(set(ids_v)))

    def test_valores_por_defecto_validos_y_reversibles(self):
        """Los valores por defecto de la firma, mostrados en la GUI y vueltos a leer,
        tienen que dar los mismos valores y pasar la validación."""
        for t, v in _variantes():
            defectos = v.valores_por_defecto()
            textos = {p.nombre: conversion.texto_por_defecto(p, defectos[p.nombre])
                      for p in v.parametros}
            valores, errores = conversion.validar(v, textos)
            with self.subTest(tecnica=t.id, variante=v.id):
                self.assertEqual(errores, [])
                for p in v.parametros:
                    esperado = defectos[p.nombre]
                    if isinstance(esperado, float):
                        self.assertAlmostEqual(valores[p.nombre], esperado,
                                               delta=1e-12 * max(1, abs(esperado)))
                    else:
                        self.assertEqual(valores[p.nombre], esperado)


try:
    import tkinter  # noqa: F401
    HAY_TKINTER = True
except ImportError:
    HAY_TKINTER = False


@unittest.skipUnless(HAY_TKINTER, 'tkinter no está instalado en este Python')
class TestImportarInterfaz(unittest.TestCase):

    def test_modulos_de_la_interfaz_importan(self):
        import importlib
        for modulo in ('app', 'formulario', 'widgets', 'resultados', 'graficos', 'dialogos'):
            with self.subTest(modulo=modulo):
                importlib.import_module(f'fmrtoolkit.gui.{modulo}')


class TestGraficos(unittest.TestCase):

    def test_texto_plano_de_titulos(self):
        from fmrtoolkit.gui.conversion import texto_plano
        self.assertEqual(texto_plano('A = 0.4 erg/cm$^2$, H$_r$ = 705 Oe'), 'A = 0.4 erg/cm2, Hr = 705 Oe')


class TestTextos(unittest.TestCase):

    def test_es_y_en_tienen_las_mismas_claves(self):
        es, en = _claves(_cargar_json('es')), _claves(_cargar_json('en'))
        self.assertEqual(sorted(es - en), [], 'faltan en en.json')
        self.assertEqual(sorted(en - es), [], 'faltan en es.json')

    def test_cada_parametro_tiene_etiqueta_y_ayuda(self):
        for codigo in IDIOMAS:
            textos = Textos(codigo)
            for t, v in _variantes():
                for p in v.parametros:
                    with self.subTest(idioma=codigo, tecnica=t.id, parametro=p.nombre):
                        self.assertTrue(textos.parametro(t.id, p.nombre, 'etiqueta'))
                        self.assertTrue(textos.parametro(t.id, p.nombre, 'ayuda'))

    def test_tecnicas_variantes_grupos_y_advertencias_traducidas(self):
        for codigo in IDIOMAS:
            textos = Textos(codigo)
            for t, v in _variantes():
                with self.subTest(idioma=codigo, tecnica=t.id):
                    self.assertTrue(textos.existe(f'tecnicas.{t.id}.nombre'))
                    self.assertTrue(textos.existe(f'tecnicas.{t.id}.descripcion'))
                    self.assertTrue(textos.existe(f'variantes.{v.id}'))
                    for adv in tuple(t.advertencias) + tuple(v.advertencias):
                        self.assertTrue(textos.existe(f'advertencias.{adv.clave}'))
                    for p in v.parametros:
                        self.assertTrue(textos.existe(f'grupos.{p.grupo}'))

    def test_tooltip_contiene_unidad_y_nombre_python(self):
        textos = Textos('es')
        t = next(t for t in TECNICAS if t.id == 'angular_ip')
        p = next(p for p in t.variante().parametros if p.nombre == 'Hu')
        tip = textos.tooltip_parametro(t.id, p)
        self.assertIn('Oe', tip)
        self.assertIn('Hu', tip)
        self.assertIn('2K_u/M_s', tip)

    def test_texto_faltante_devuelve_la_clave(self):
        self.assertEqual(Textos('en').t('no.existe'), 'no.existe')

    def test_formato_con_datos(self):
        self.assertIn('abc', Textos('es').t('errores.no_numero', texto='abc'))


if __name__ == '__main__':
    unittest.main()
