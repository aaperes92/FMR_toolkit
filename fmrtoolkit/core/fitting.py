"""Utilidades de ajuste comunes: valores iniciales (p0) para cada modelo."""

import numpy as np

from fmrtoolkit.core import models


# ==================================================
# ESPECTROS: 1 o 2 lorentzianas
# ==================================================

def estimar_p0(campo, intensidad, ventana, n_lineas=2):
    """Valores iniciales: fondo lineal y una estimación para cada línea por separado.

    Devuelve [y0, m, A1, H1, G1, phi1, (A2, H2, G2, phi2)] -> 2 + 4·n_lineas valores.
    ventana: semiancho (Oe) de la zona que se considera parte de una misma línea.
    """
    # Fondo: recta ajustada a los extremos del espectro (10 % de cada lado)
    n = max(len(campo) // 10, 5)
    bordes = np.r_[0:n, len(campo) - n:len(campo)]
    m, y0 = np.polyfit(campo[bordes], intensidad[bordes], 1)
    senal = intensidad - (y0 + m*campo)

    p0 = [y0, m]
    libre = np.ones(campo.size, dtype=bool)
    paso = np.median(np.abs(np.diff(campo)))
    for _ in range(n_lineas):
        # La línea más intensa que queda: el punto más alejado de cero...
        i = np.argmax(np.where(libre, np.abs(senal), -np.inf))
        # ...y el máximo y el mínimo de ESA línea, dentro de la ventana
        cerca = np.flatnonzero(libre & (np.abs(campo - campo[i]) < ventana))
        imax = cerca[np.argmax(senal[cerca])]
        imin = cerca[np.argmin(senal[cerca])]
        H = (campo[imax] + campo[imin]) / 2
        G = max(abs(campo[imax] - campo[imin]) * np.sqrt(3), 2*paso)  # pico a pico -> FWHM
        A = 1.209199 * (senal[imax] - senal[imin]) / 2 * G**2
        p0 += [A, H, G, 0]
        libre &= np.abs(campo - H) > ventana   # se tapa esta línea para buscar la otra
    return p0


# ==================================================
# BANDA ANCHA: Kittel y ancho de línea
# ==================================================

def estimar_p0_kittel(Hr, f):
    """Valores iniciales para Kittel en el plano (eje fácil): [g, M_eff, H_uniaxial].

    Kittel elevado al cuadrado es un polinomio de grado 2 en H:
        f² = a·H² + b·H + c
    con  a = (g/714.5)² ,  b/a = 2·Hu + 4πM_eff ,  c/a = Hu·(Hu + 4πM_eff)
    De a sale g; de b/a y c/a salen Hu y M_eff (resolviendo una cuadrática).
    """
    Hr = np.asarray(Hr, dtype=float)
    f = np.asarray(f, dtype=float)

    if len(Hr) >= 4:
        a, b, c = np.polyfit(Hr, f**2, 2)
    else:
        a = 0.0                                   # muy pocos puntos: se usa el plan B

    if a > 0:
        g0 = 714.5 * np.sqrt(a)
        S, P = b / a, c / a                       # S = 2Hu + 4πM ; P = Hu·(Hu + 4πM)
        disc = S**2 - 4*P
        Hu0 = (S - np.sqrt(disc)) / 2 if disc >= 0 else 0.0
        M0 = (S - 2*Hu0) / (4*np.pi)
    else:
        # Plan B (pocos puntos o mucho ruido): g típico y M_eff despejado punto a punto
        g0, Hu0 = 2.1, 0.0
        M0 = np.median((f * 714.5 / g0)**2 / Hr - Hr) / (4*np.pi)

    return [g0, M0, Hu0]


def estimar_p0_ancho(f, dH, g):
    """Valores iniciales para el ancho de línea: [delta_H0, damping].

    El modelo es una recta en f, así que se ajusta con polyfit:
        ordenada  -> delta_H0
        pendiente -> damping (dividiendo por la pendiente que da damping = 1)
    Se usa models.ancho_de_linea para no repetir la fórmula: si la cambiás
    (FWHM o pico-pico), esta función se adapta sola.
    """
    pendiente, ordenada = np.polyfit(f, dH, 1)
    pendiente_por_unidad = models.ancho_de_linea(1.0, 0.0, 1.0, g)   # ΔH a 1 GHz con damping = 1
    return [ordenada, pendiente / pendiente_por_unidad]
