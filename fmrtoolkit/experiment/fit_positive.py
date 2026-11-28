"""Ajuste de espectros FMR con 1 o 2 lorentzianas (barrido 0 -> +H): Hr, ancho de línea, fase."""

import os

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from fmrtoolkit.core import models as lz
from fmrtoolkit.core.fitting import estimar_p0   # o donde tengas definida estimar_p0

MODELOS = {1: lz.una_lorentziana, 2: lz.dos_lorentzianas}

# El ajuste da el FWHM de la lorentziana. Se guarda el pico-pico: FWHM / sqrt(3)
FWHM_A_PP = 1 / np.sqrt(3)


def ajustar_carpeta(carpeta, n_lineas=2, ventana=300, graficar=True, extensiones=('.dat', '.txt')):
    modelo = MODELOS[n_lineas]
    filas = []

    for archivo in os.listdir(carpeta):
        if not archivo.lower().endswith(extensiones):
            continue
        if archivo.startswith(('fit_', 'output_')):   # resultados de corridas anteriores, no son datos
            continue
        ruta = os.path.join(carpeta, archivo)
        nombre_sin_extension = os.path.splitext(archivo)[0]

        columna = np.loadtxt(ruta, delimiter=None, skiprows=4, encoding='latin1')
        campo = columna[:, 0]
        intensidad = columna[:, 1]

        p0 = estimar_p0(campo, intensidad, ventana, n_lineas)

        # Límites: fondo libre; por línea A > 0, Hr dentro del rango medido,
        # 0 < ancho < rango, -pi < phi < pi
        rango = campo.max() - campo.min()
        inf = [-np.inf, -np.inf] + [0,      campo.min(), 0,     -np.pi] * n_lineas
        sup = [ np.inf,  np.inf] + [np.inf, campo.max(), rango,  np.pi] * n_lineas

        try:
            popt, pcov = curve_fit(modelo, campo, intensidad, p0=p0,
                                   bounds=(inf, sup), x_scale='jac', maxfev=100000)
        except (RuntimeError, ValueError) as error:
            print(f'{archivo}: el ajuste no convergió ({error}). Se saltea.')
            continue
        errores = np.sqrt(np.diag(pcov))

        y0_fit, m_fit = popt[:2]
        lineas = popt[2:].reshape(n_lineas, 4)         # una fila por línea: A, Hr, ancho, phi
        err_lineas = errores[2:].reshape(n_lineas, 4)

        # Línea 1 = la de campo más alto
        orden = np.argsort(lineas[:, 1])[::-1]
        lineas, err_lineas = lineas[orden], err_lineas[orden]
                
        texto = '   '.join(f'Hr{i} = {l[1]:.1f} ± {e[1]:.1f}   ancho{i} = {l[2]:.1f} ± {e[2]:.1f}'
                           for i, (l, e) in enumerate(zip(lineas, err_lineas), start=1))
        print(f'{archivo}: {texto}')
        if lineas[:, 2].max() > 0.3 * rango:
            print('   AVISO: una línea salió muy ancha; probablemente está ajustando el fondo. Revisá el gráfico.')

        # Curva ajustada (la suma), el fondo y cada línea sobre el fondo
        campo_fit = np.linspace(campo.min(), campo.max(), 1000)
        intensidad_fit = modelo(campo_fit, *popt)
        fondo_fit = y0_fit + m_fit * campo_fit
        curvas_lineas = [fondo_fit + lz.lorentziana(campo_fit, 0, *linea) for linea in lineas]

        if graficar:
            plt.figure(figsize=(7, 5))
            plt.plot(campo, intensidad, 'o', label='Datos', markersize=3)
            plt.plot(campo_fit, intensidad_fit, '-', label='Ajuste (suma)')
            for i, (curva, linea) in enumerate(zip(curvas_lineas, lineas), start=1):
                plt.plot(campo_fit, curva, '--', label=f'Línea {i}: Hr = {linea[1]:.0f}')
            plt.plot(campo_fit, fondo_fit, ':', color='gray', label='Fondo')
            plt.xlabel('Campo')
            plt.ylabel('Intensidad')
            plt.title(f'Ajuste para {archivo}')
            plt.legend()
            plt.grid(True)
            plt.show()

        # Curva ajustada de este archivo
        output_fit = os.path.join(carpeta, f'fit_{nombre_sin_extension}.txt')
        encabezado = 'H, Voltage, ' + ', '.join(f'Linea{i}' for i in range(1, n_lineas + 1)) + ', Fondo'
        np.savetxt(output_fit, np.column_stack((campo_fit, intensidad_fit, *curvas_lineas, fondo_fit)),
                   delimiter=',', header=encabezado, comments='')

        # Fila del resumen: Frecuencia, (Hr, ancho) por línea, (err_Hr, err_ancho) por línea, phi por línea
        angulo = float(nombre_sin_extension.split('_')[-1].replace('GHz', '').replace('p', '.'))
        hr_ancho = np.column_stack((lineas[:, 1], lineas[:, 2] * FWHM_A_PP)).ravel()
        err_hr_ancho = np.column_stack((err_lineas[:, 1], err_lineas[:, 2] * FWHM_A_PP)).ravel()
        filas.append([angulo, *hr_ancho, *err_hr_ancho, *lineas[:, 3]])

    if not filas:
        print('No se ajustó ningún archivo.')
        return None

    datos = np.array(filas)
    datos = datos[datos[:, 0].argsort()]

    nums = range(1, n_lineas + 1)
    columnas = (['Frecuencia']
                + [c for i in nums for c in (f'Hr{i}', f'Ancho de linea{i} pico-pico')]
                + [c for i in nums for c in (f'err_Hr{i}', f'err_Ancho{i}')]
                + [f'phi{i}' for i in nums])
    output_file = os.path.join(carpeta, f'output_{n_lineas}peak.txt')
    np.savetxt(output_file, datos, delimiter=',', header=', '.join(columnas), comments='')

    return datos


if __name__ == '__main__':
    # se ejecuta solo si corrés el archivo directamente, no cuando se importa
    ajustar_carpeta(os.path.dirname(os.path.realpath(__file__)), n_lineas=2)
