"""FMR de banda ancha: Kittel -> Meff, g ; ΔH(f) -> damping, ΔH0.
De los datos fitteados de los espectros de FMR broadband se calcula mediante Kittel
el parámetro g y se ajusta el ancho de línea para determinar el damping y Delta H0."""

import os
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from fmrtoolkit.core import models
from fmrtoolkit.core.fitting import estimar_p0_ancho, estimar_p0_kittel


def ajustar_banda_ancha(archivo, col_Hr=1, col_ancho=2, eje_facil=True,
                        ajustar_Hu=False, H_uniaxial=0.0, H_cubico=0.0,
                        g_limites=(2.0, 2.2), graficar=True,
                        carpeta_salida=None, figuras=None):
    """
    archivo     : output_*.txt generado por fit_positive o fit_bipolar
    col_Hr      : columna de Hr (la 0 es la frecuencia)
    col_ancho   : columna del ancho de línea
    ajustar_Hu  : True -> ajusta H_uniaxial ; False -> lo deja fijo en el valor dado
    H_cubico    : siempre fijo (en el eje fácil no se distingue de H_uniaxial)
    g_limites   : (g_min, g_max) rango permitido para g; por defecto (2.0, 2.2)
    graficar    : True -> muestra las figuras (los PDF se guardan siempre)
    carpeta_salida : dónde se guardan los PDF y output_broadband.txt.
                     None -> en la carpeta de `archivo`
    figuras     : lista opcional; si se pasa, se le agregan las dos figuras y no se cierran
    """

    # ==================================================
    # LEER LOS RESULTADOS DE LOS ESPECTROS
    # ==================================================

    datos = np.loadtxt(archivo, delimiter=',', skiprows=1)
    f, Hr, dH = datos[:, 0], datos[:, col_Hr], datos[:, col_ancho]

    validas = ~np.isnan(f) & ~np.isnan(Hr) & ~np.isnan(dH)     # descarta filas sin frecuencia
    f, Hr, dH = f[validas], Hr[validas], dH[validas]

    # ==================================================
    # 1) KITTEL: de acá salen g y M_eff
    # ==================================================

    g_min, g_max = g_limites
    g0, M0, Hu0 = estimar_p0_kittel(Hr, f)
    if not g_min < g0 < g_max:              # el valor inicial tiene que estar dentro de los límites
        g0 = (g_min + g_max) / 2

    if ajustar_Hu:
        modelo_kittel = partial(models.kittel, H_cubico=H_cubico, eje_facil=eje_facil)
        p0_kittel = [g0, M0, Hu0]                                   # g, M_eff, H_uniaxial
    else:
        modelo_kittel = partial(models.kittel, H_uniaxial=H_uniaxial,
                                H_cubico=H_cubico, eje_facil=eje_facil)
        p0_kittel = [g0, M0]                                        # g, M_eff

    # Límites: solo g está acotado; el resto queda libre (-inf, inf)
    inf = [g_min] + [-np.inf] * (len(p0_kittel) - 1)
    sup = [g_max] + [ np.inf] * (len(p0_kittel) - 1)

    popt_k, pcov_k = curve_fit(modelo_kittel, Hr, f, p0=p0_kittel,
                               bounds=(inf, sup), maxfev=100000)
    err_k = np.sqrt(np.diag(pcov_k))

    g_fit, M_eff_fit = popt_k[0], popt_k[1]
    Hu_fit = popt_k[2] if ajustar_Hu else H_uniaxial
    err_Hu = err_k[2] if ajustar_Hu else 0.0

    if np.isclose(g_fit, g_min) or np.isclose(g_fit, g_max):
        print(f'   AVISO: g quedó pegado al límite ({g_fit:.3f}); el ajuste está forzado '
              f'y su error no es confiable.')

    # ==================================================
    # 2) ANCHO DE LÍNEA con g fijo: de acá salen damping y ΔH0
    # ==================================================

    modelo_ancho = partial(models.ancho_de_linea, g=g_fit)
    p0_ancho = estimar_p0_ancho(f, dH, g_fit)                       # delta_H0, damping
    popt_a, pcov_a = curve_fit(modelo_ancho, f, dH, p0=p0_ancho)
    err_a = np.sqrt(np.diag(pcov_a))

    delta_H0, damping = popt_a

    resultados = {
        'g':          (g_fit, err_k[0]),
        'M_eff':      (M_eff_fit, err_k[1]),     # emu/cm³
        'H_uniaxial': (Hu_fit, err_Hu),          # Oe
        'H_cubico':   (H_cubico, 0.0),           # Oe (fijo)
        'delta_H0':   (delta_H0, err_a[0]),      # Oe
        'damping':    (damping, err_a[1]),
    }

    print('\nRESULTADOS BANDA ANCHA')
    for nombre, (valor, error) in resultados.items():
        print(f'{nombre:>11} = {valor:.5g} ± {error:.2g}')

    # ==================================================
    # GRAFICA (los PDF se guardan siempre; la ventana solo si graficar=True)
    # ==================================================

    carpeta = os.path.dirname(os.path.abspath(archivo)) if carpeta_salida is None else carpeta_salida
    os.makedirs(carpeta, exist_ok=True)

    H_plot = np.linspace(Hr.min(), Hr.max(), 300)
    f_plot = np.linspace(f.min(), f.max(), 300)

    # Kittel
    fig1, ax1 = plt.subplots(figsize=(6, 4.5))
    ax1.plot(Hr, f, 'o', label='Datos')
    ax1.plot(H_plot, modelo_kittel(H_plot, *popt_k), '-', label=f'Kittel: g = {g_fit:.3f}')
    ax1.set_xlabel(r'$H_r$ (Oe)')
    ax1.set_ylabel('f (GHz)')
    ax1.legend()
    ax1.grid(True)
    fig1.savefig(os.path.join(carpeta, 'kittel_fit.pdf'), bbox_inches='tight')

    # Ancho de línea
    fig2, ax2 = plt.subplots(figsize=(6, 4.5))
    ax2.plot(f, dH, 'o', label='Datos')
    ax2.plot(f_plot, modelo_ancho(f_plot, *popt_a), '-', label=fr'$\alpha$ = {damping:.2e}')
    ax2.set_xlabel('f (GHz)')
    ax2.set_ylabel(r'$\Delta H$ (Oe)')
    ax2.legend()
    ax2.grid(True)
    fig2.savefig(os.path.join(carpeta, 'damping_fit.pdf'), bbox_inches='tight')

    if figuras is not None:
        figuras.extend([fig1, fig2])
    if graficar:
        plt.show()
    elif figuras is None:
        plt.close(fig1)
        plt.close(fig2)

    # ==================================================
    # GUARDAR RESULTADOS
    # ==================================================

    with open(os.path.join(carpeta, 'output_broadband.txt'), 'w') as salida:
        salida.write('parametro,valor,error\n')
        for nombre, (valor, error) in resultados.items():
            salida.write(f'{nombre},{valor:.6g},{error:.3g}\n')

    return resultados


if __name__ == '__main__':
    # se ejecuta solo si corrés el archivo directamente, no cuando se importa
    carpeta = os.path.dirname(os.path.realpath(__file__))
    ajustar_banda_ancha(os.path.join(carpeta, 'output_1peak.txt'))
