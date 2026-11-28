"""Conversión de unidades, lectura de los campos y validación de la GUI."""

import unittest

import matplotlib
matplotlib.use('Agg')

from fmrtoolkit.gui import conversion as cv
from fmrtoolkit.gui.conversion import ErrorValidacion
from fmrtoolkit.gui.especificaciones import Parametro, tecnica

FREC = Parametro('frecuencia', 'campo', unidad='GHz', factor=1e9)
ESPESOR = Parametro('espesor_a', 'material', unidad='nm', factor=1e-7)


class TestUnidades(unittest.TestCase):

    def test_ghz_a_hz_y_vuelta(self):
        self.assertAlmostEqual(cv.a_funcion(9.76, FREC), 9.76e9)
        self.assertAlmostEqual(cv.a_gui(23.9e9, FREC), 23.9)

    def test_nm_a_cm_y_vuelta(self):
        self.assertAlmostEqual(cv.a_funcion(10, ESPESOR), 1e-6)
        self.assertAlmostEqual(cv.a_gui(2.5e-6, ESPESOR), 25)

    def test_texto_por_defecto_sin_ruido_de_punto_flotante(self):
        self.assertEqual(cv.texto_por_defecto(ESPESOR, 10e-7), '10')
        self.assertEqual(cv.texto_por_defecto(FREC, 9.76e9), '9.76')
        self.assertEqual(cv.texto_por_defecto(Parametro('g_limites', 'material', tipo='par'), (2.0, 2.2)), '2, 2.2')

    def test_sin_factor_no_cambia(self):
        p = Parametro('Hu', 'anisotropia', unidad='Oe')
        self.assertEqual(cv.a_funcion(250.0, p), 250.0)


class TestLectura(unittest.TestCase):

    def test_real_con_coma_o_punto(self):
        p = Parametro('g', 'material')
        self.assertEqual(cv.leer_texto('2,09', p), 2.09)
        self.assertEqual(cv.leer_texto(' 2.09 ', p), 2.09)
        self.assertEqual(cv.leer_texto('1e3', p), 1000.0)

    def test_entero_escrito_en_campo_real_queda_entero(self):
        """Así los nombres de archivo (p. ej. 'magn1155_eje45') son los mismos que desde un script."""
        p = Parametro('magn', 'material')
        self.assertIsInstance(cv.leer_texto('1155', p), int)
        self.assertIsInstance(cv.leer_texto('1155.0', p), float)
        self.assertEqual(f"magn{cv.leer_texto('1155', p)}", 'magn1155')
        self.assertAlmostEqual(cv.a_funcion(cv.leer_texto('10', FREC), FREC), 1e10)

    def test_real_invalido(self):
        p = Parametro('g', 'material')
        for texto, clave in (('', 'vacio'), ('abc', 'no_numero'), ('nan', 'no_numero'), ('inf', 'no_numero')):
            with self.subTest(texto=texto):
                with self.assertRaises(ErrorValidacion) as e:
                    cv.leer_texto(texto, p)
                self.assertEqual(e.exception.clave, clave)

    def test_entero(self):
        p = Parametro('skiprows', 'datos', tipo='entero')
        self.assertEqual(cv.leer_texto('4', p), 4)
        with self.assertRaises(ErrorValidacion):
            cv.leer_texto('4.5', p)

    def test_columnas_entero_o_lista(self):
        p = Parametro('col_Hr', 'datos', tipo='columnas')
        self.assertEqual(cv.leer_texto('1', p), 1)
        self.assertEqual(cv.leer_texto('1, 3', p), [1, 3])
        self.assertEqual(cv.leer_texto('[1;3]', p), [1, 3])
        with self.assertRaises(ErrorValidacion):
            cv.leer_texto('1, x', p)

    def test_par(self):
        p = Parametro('g_limites', 'material', tipo='par')
        self.assertEqual(cv.leer_texto('(2.0, 2.2)', p), (2.0, 2.2))
        self.assertEqual(cv.leer_texto('2 2.2', p), (2.0, 2.2))
        for texto, clave in (('2.0', 'par_invalido'), ('2.2, 2.0', 'par_orden'), ('1, 2, 3', 'par_invalido')):
            with self.subTest(texto=texto):
                with self.assertRaises(ErrorValidacion) as e:
                    cv.leer_texto(texto, p)
                self.assertEqual(e.exception.clave, clave)

    def test_opcion_n_lineas(self):
        p = Parametro('n_lineas', 'ajuste', tipo='opcion', opciones=(1, 2))
        self.assertEqual(cv.leer_texto('2', p), 2)
        self.assertEqual(cv.leer_texto(1, p), 1)
        with self.assertRaises(ErrorValidacion) as e:
            cv.leer_texto('3', p)
        self.assertEqual(e.exception.clave, 'opcion_invalida')

    def test_extensiones(self):
        p = Parametro('extensiones', 'datos', tipo='extensiones')
        self.assertEqual(cv.leer_texto('.dat, txt', p), ('.dat', '.txt'))


class TestValidacion(unittest.TestCase):

    def _textos_por_defecto(self, variante):
        d = variante.valores_por_defecto()
        return {p.nombre: cv.texto_por_defecto(p, d[p.nombre]) for p in variante.parametros}

    def test_margen_mayor_que_paso_en_op(self):
        v = tecnica('angular_op').variante()
        textos = self._textos_por_defecto(v)
        textos['margen_campo'], textos['paso_campo'] = '50', '80'
        _, errores = cv.validar(v, textos)
        self.assertIn('margen_paso', [e.clave for _, e in errores])

    def test_positivo_y_rangos(self):
        v = tecnica('dispersion').variante('1capa')
        textos = self._textos_por_defecto(v)
        textos['magn'] = '-5'
        textos['campo_min'], textos['campo_max'] = '100', '50'
        _, errores = cv.validar(v, textos)
        self.assertEqual([(n, e.clave) for n, e in errores], [('magn', 'debe_ser_positivo')])
        textos['magn'] = '1300'                     # con todo legible aparecen las reglas cruzadas
        _, errores = cv.validar(v, textos)
        self.assertEqual([e.clave for _, e in errores], ['campo_min_max'])

    def test_frecuencia_y_espesores_llegan_en_hz_y_cm(self):
        v = tecnica('autovectores').variante('bicapa')
        textos = self._textos_por_defecto(v)
        textos['frecuencia'], textos['espesor_a'] = '24', '25'
        valores, errores = cv.validar(v, textos)
        self.assertEqual(errores, [])
        self.assertAlmostEqual(valores['frecuencia'], 24e9)
        self.assertAlmostEqual(valores['espesor_a'], 2.5e-6)

    def test_advertencias(self):
        t = tecnica('broadband')
        v = t.variante()
        textos = self._textos_por_defecto(v)
        textos['eje_facil'] = False
        valores, _ = cv.validar(v, textos)
        self.assertIn('eje_dificil', cv.advertencias_activas(v, t, valores))
        t2 = tecnica('dispersion')
        v2 = t2.variante('2capas')
        valores2, _ = cv.validar(v2, {**self._textos_por_defecto(v2), 'A': '-0.3'})
        self.assertIn('acople_negativo', cv.advertencias_activas(v2, t2, valores2))


if __name__ == '__main__':
    unittest.main()
