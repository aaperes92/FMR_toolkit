"""Prueba de humo: cada técnica de la GUI corre de punta a punta con datos sintéticos.

Llama a las funciones igual que la GUI (valores por defecto de la firma + algunos
cambios para que sea rápido, graficar=False, figuras y carpeta de salida), a través de
gui.ejecucion.ejecutar. Tarda alrededor de un minuto, así que solo corre si se pide:

    FMR_TESTS_LENTOS=1 python -m unittest tests.test_humo_tecnicas        (Linux / macOS)
    set FMR_TESTS_LENTOS=1 && python -m unittest tests.test_humo_tecnicas  (Windows)
"""

import os
import tempfile
import unittest
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from fmrtoolkit.core.models import lorentziana
from fmrtoolkit.gui.ejecucion import ejecutar
from fmrtoolkit.gui.especificaciones import tecnica

LENTOS = os.environ.get('FMR_TESTS_LENTOS') == '1'


def _kittel_ip(M, g, f_hz):
    w = 2 * np.pi * f_hz / (8794000 * g)
    return -2 * np.pi * M + np.sqrt((2 * np.pi * M) ** 2 + w ** 2)


@unittest.skipUnless(LENTOS, 'prueba lenta: correr con FMR_TESTS_LENTOS=1')
class TestHumoTecnicas(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        cls.base = base
        H = np.linspace(0, 3000, 600)
        Hb = np.linspace(-3000, 3000, 1200)
        (base / 'positivo').mkdir()
        (base / 'bipolar').mkdir()
        for f, Hr in ((5.0, 600), (9.4, 1200), (12.0, 1700), (15.5, 2300)):
            y = 0.01 + 1e-6 * H + lorentziana(H, 0, 5e4, Hr, 60, 0.1)
            np.savetxt(base / 'positivo' / f'm_{str(f).replace(".", "p")}GHz.dat', np.column_stack((H, y)),
                       header='a\nb\nc\nd', comments='')
            yb = lorentziana(Hb, 0, 5e4, Hr, 60, 0) + lorentziana(Hb, 0, -5e4, -Hr, 60, 0)
            np.savetxt(base / 'bipolar' / f'm_{f}.dat', np.column_stack((Hb, yb)), header='a', comments='')
        # Banda ancha: Kittel con g = 2.1 y M_eff = 1000; ancho lineal en f (pico a pico)
        f = np.array([5, 8, 11, 14, 17, 20.0])
        Hr = np.array([_kittel_ip(1000, 2.1, fi * 1e9) for fi in f])
        dH = 5 + 4 * np.pi / np.sqrt(3) * 0.008 * f * 1e9 / (8794000 * 2.1)
        np.savetxt(base / 'output_1peak.txt', np.column_stack((f, Hr, dH, 0 * f, 0 * f, 0 * f)), delimiter=',',
                   header='Frecuencia,Hr1,Ancho,err_Hr1,err_Ancho1,phi1', comments='')
        np.savetxt(base / 'ip.txt', [[0, 3600], [90, 3700]], delimiter=',', header='a,b', comments='')
        np.savetxt(base / 'op.txt', [[0, 1000], [90, 13000]], delimiter=',', header='a,b', comments='')
        np.savetxt(base / 'bi.txt', [[0, 2400, 1, 3600, 1], [90, 2400, 1, 3600, 1]], delimiter=',',
                   header='a,b,c,d,e', comments='')

    @classmethod
    def tearDownClass(cls):
        plt.close('all')
        cls.tmp.cleanup()

    def correr(self, id_tecnica, id_variante=None, entrada=None, **cambios):
        """Igual que la GUI: defaults de la firma + cambios + entrada + salida + graficar=False."""
        variante = tecnica(id_tecnica).variante(id_variante)
        salida = self.base / f'salida_{id_tecnica}_{variante.id}'
        salida.mkdir(exist_ok=True)
        kwargs = {**variante.valores_por_defecto(), **cambios,
                  variante.param_salida: str(salida), 'graficar': False}
        if variante.entrada:
            kwargs[variante.param_entrada] = str(self.base / entrada)
        resultado = ejecutar(variante.funcion, kwargs, str(salida))
        self.assertTrue(resultado.ok, resultado.traceback)
        self.assertGreater(len(resultado.figuras), 0)
        self.assertGreater(len(resultado.archivos_nuevos), 0)
        for fig in resultado.figuras:
            plt.close(fig)
        return resultado

    def test_fit_positive(self):
        for n in (1, 2):
            with self.subTest(n_lineas=n):
                r = self.correr('fit_positive', entrada='positivo', n_lineas=n)
                self.assertIn(f'output_{n}peak.txt', r.archivos_nuevos)
                self.assertEqual(len(r.figuras), 4)

    def test_fit_bipolar(self):
        r = self.correr('fit_bipolar', entrada='bipolar')
        self.assertIn('output_bipolar.txt', r.archivos_nuevos)

    def test_broadband(self):
        r = self.correr('broadband', entrada='output_1peak.txt')
        g, M = r.valor['g'][0], r.valor['M_eff'][0]
        self.assertAlmostEqual(g, 2.1, places=3)
        self.assertAlmostEqual(M, 1000, delta=1)
        self.assertAlmostEqual(r.valor['damping'][0], 0.008, places=5)

    def test_angular_ip(self):
        self.correr('angular_ip', entrada='ip.txt', ang_fin=90, paso_ang=90)

    def test_angular_op(self):
        self.correr('angular_op', entrada='op.txt', ang_fin=90, paso_ang=90, margen_campo=300,
                    paso_campo=20, paso_phi_M=0.5)

    def test_angular_op_fuera_de_rango_da_error_controlado(self):
        variante = tecnica('angular_op').variante()
        kwargs = {**variante.valores_por_defecto(), 'archivo': str(self.base / 'op.txt'),
                  'carpeta_salida': str(self.base), 'graficar': False, 'ang_fin': 90, 'paso_ang': 90}
        r = ejecutar(variante.funcion, kwargs, str(self.base))
        self.assertFalse(r.ok)
        self.assertIsInstance(r.excepcion, ValueError)

    def test_angular_bicapa(self):
        self.correr('angular_bicapa', entrada='bi.txt', ang_fin=90, paso_ang=90, paso_campo=50, col_Hr=[1, 3])

    def test_dispersion(self):
        self.correr('dispersion', '1capa', campo_max=1000, paso_campo=100, paso_phi_M=1)
        self.correr('dispersion', '2capas', campo_max=1000, paso_campo=100, paso_phi_M=10)

    def test_autovectores_1capa_kittel(self):
        r = self.correr('autovectores', '1capa', Hc=0, Hu=0, guardar_gif=False)
        self.assertAlmostEqual(r.valor['modo']['Hr'], _kittel_ip(1700, 2.088, 9.76e9), delta=0.5)

    def test_autovectores_bicapa_con_gif(self):
        r = self.correr('autovectores', 'bicapa', frecuencia=15e9, campo_max=3000, guardar_gif=True)
        self.assertTrue(any(a.endswith('.gif') for a in r.archivos_nuevos))
        self.assertIsNotNone(r.valor['acustico'])
        self.assertIsNotNone(r.valor['optico'])


if __name__ == '__main__':
    unittest.main()
