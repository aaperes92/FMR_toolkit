"""Configuración entre sesiones, reporte de problemas y ejecución (sin pantalla)."""

import json
import os
import tempfile
import unittest
import warnings
from pathlib import Path
from urllib.parse import unquote

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from fmrtoolkit.gui import configuracion, reporte
from fmrtoolkit.gui.ejecucion import ejecutar
from fmrtoolkit.gui.idioma import Textos


class TestConfiguracion(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ruta = Path(self.tmp.name) / 'sub' / 'gui_config.json'

    def tearDown(self):
        self.tmp.cleanup()

    def test_sin_archivo_da_valores_por_defecto(self):
        self.assertEqual(configuracion.cargar(self.ruta), configuracion.POR_DEFECTO)

    def test_guardar_y_cargar(self):
        config = configuracion.cargar(self.ruta)
        config['idioma'] = 'en'
        config['carpeta_salida'] = '/datos/salida'
        config['parametros']['broadband/unica'] = {'col_Hr': '5'}
        self.assertTrue(configuracion.guardar(config, self.ruta))
        leida = configuracion.cargar(self.ruta)
        self.assertEqual(leida['idioma'], 'en')
        self.assertEqual(leida['carpeta_salida'], '/datos/salida')
        self.assertEqual(leida['parametros']['broadband/unica'], {'col_Hr': '5'})

    def test_archivo_corrupto(self):
        self.ruta.parent.mkdir(parents=True)
        self.ruta.write_text('{esto no es json', encoding='utf-8')
        self.assertEqual(configuracion.cargar(self.ruta), configuracion.POR_DEFECTO)

    def test_version_vieja(self):
        self.ruta.parent.mkdir(parents=True)
        self.ruta.write_text(json.dumps({'version': 0, 'idioma': 'en'}), encoding='utf-8')
        self.assertEqual(configuracion.cargar(self.ruta)['idioma'], 'es')

    def test_tipos_incorrectos_e_idioma_invalido(self):
        self.ruta.parent.mkdir(parents=True)
        datos = {'version': configuracion.VERSION_CONFIG, 'idioma': 'fr', 'parametros': 'roto',
                 'carpeta_salida': '/ok'}
        self.ruta.write_text(json.dumps(datos), encoding='utf-8')
        config = configuracion.cargar(self.ruta)
        self.assertEqual(config['idioma'], 'es')
        self.assertEqual(config['parametros'], {})
        self.assertEqual(config['carpeta_salida'], '/ok')

    def test_variable_de_entorno(self):
        os.environ['FMRTOOLKIT_GUI_CONFIG'] = str(self.ruta)
        try:
            self.assertEqual(configuracion.ruta_config(), self.ruta)
        finally:
            del os.environ['FMRTOOLKIT_GUI_CONFIG']


class TestReporte(unittest.TestCase):

    ENTORNO = {'fmrtoolkit': '0.1.0', 'commit': 'abc123', 'python': '3.12', 'os': 'Test'}

    def setUp(self):
        self.textos = Textos('es')
        self.tmp = tempfile.TemporaryDirectory()
        self.contexto = {'tecnica': 'Banda ancha', 'funcion': 'fmrtoolkit.experiment.broadband.ajustar_banda_ancha',
                         'parametros': {'col_Hr': 1, 'g_limites': (2.0, 2.2)},
                         'entrada': '/datos/output_1peak.txt', 'salida': '/datos/salida',
                         'traceback': 'Traceback...\nValueError: algo & raro',
                         'consola': 'AVISO: g quedó pegado al límite'}

    def tearDown(self):
        self.tmp.cleanup()

    def test_reporte_contiene_todo(self):
        texto = reporte.armar_reporte(self.textos, 'error', 'No anda', self.contexto, self.ENTORNO)
        for esperado in ('No anda', 'Banda ancha', 'ajustar_banda_ancha', "g_limites = (2.0, 2.2)",
                         '/datos/output_1peak.txt', '/datos/salida', 'ValueError: algo & raro',
                         'AVISO: g quedó pegado', 'abc123', self.textos.t('reporte.tipo_error')):
            self.assertIn(esperado, texto)

    def test_info_entorno_tiene_versiones(self):
        info = reporte.info_entorno()
        for clave in ('fmrtoolkit', 'commit', 'python', 'os', 'numpy', 'scipy', 'sympy', 'matplotlib'):
            self.assertIn(clave, info)

    def test_mailto_codificado(self):
        url = reporte.enlace_mailto('a@b.com', 'Asunto & más', 'línea 1\nlínea 2 & ?=')
        self.assertTrue(url.startswith('mailto:a@b.com?subject='))
        self.assertNotIn(' ', url)
        self.assertNotIn('\n', url)
        cuerpo = url.split('&body=')[1]
        self.assertEqual(unquote(cuerpo), 'línea 1\nlínea 2 & ?=')

    def test_reporte_corto_va_entero(self):
        texto = 'reporte corto'
        url, ruta = reporte.preparar_envio(self.textos, 'a@b.com', 'resultado', 'x', self.contexto,
                                           texto, self.tmp.name)
        self.assertIsNone(ruta)
        self.assertIn('reporte%20corto', url)

    def test_reporte_largo_se_guarda_y_resume(self):
        texto = reporte.armar_reporte(self.textos, 'resultado', 'x' * 100,
                                      {**self.contexto, 'consola': 'línea de consola\n' * 500}, self.ENTORNO)
        url, ruta = reporte.preparar_envio(self.textos, 'a@b.com', 'resultado', 'x' * 100, self.contexto,
                                           texto, self.tmp.name)
        self.assertIsNotNone(ruta)
        self.assertTrue(ruta.exists())
        self.assertEqual(ruta.read_text(encoding='utf-8'), texto)
        self.assertLessEqual(len(url), reporte.LARGO_MAXIMO_MAILTO)
        self.assertIn(ruta.name, unquote(url))


class TestEjecucion(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()
        plt.close('all')

    def test_captura_salida_avisos_figuras_y_archivos(self):
        carpeta = Path(self.tmp.name)
        (carpeta / 'viejo.txt').write_text('a')

        def funcion(x, figuras=None, carpeta_salida=None):
            print('hola', x)
            print('   AVISO: algo raro')
            warnings.warn('cuidado', RuntimeWarning)
            fig, _ = plt.subplots()
            figuras.append(fig)
            plt.subplots()                                   # figura que nadie pidió
            (carpeta / 'nuevo.txt').write_text('b')
            (carpeta / 'viejo.txt').write_text('cambiado')
            return 42

        r = ejecutar(funcion, {'x': 1}, str(carpeta))
        self.assertTrue(r.ok)
        self.assertEqual(r.valor, 42)
        self.assertIn('hola 1', r.consola)
        self.assertIn('AVISO: algo raro', r.avisos)
        self.assertTrue(any('cuidado' in a for a in r.avisos))
        self.assertEqual(len(r.figuras), 1)
        self.assertEqual(plt.get_fignums(), [r.figuras[0].number])   # la otra se cerró
        self.assertEqual(r.archivos_nuevos, ['nuevo.txt'])
        self.assertEqual(r.archivos_modificados, ['viejo.txt'])

    def test_excepcion_no_se_propaga(self):
        def funcion():
            print('antes del error')
            raise ValueError('falló')

        r = ejecutar(funcion, {}, None)
        self.assertFalse(r.ok)
        self.assertIsInstance(r.excepcion, ValueError)
        self.assertIn('ValueError: falló', r.traceback)
        self.assertIn('antes del error', r.consola)


if __name__ == '__main__':
    unittest.main()
