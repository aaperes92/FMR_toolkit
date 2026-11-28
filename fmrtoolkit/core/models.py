"""Definición de las funciones: derivada de 1 lorentziana y de 2 lorentzianas."""

import numpy as np

def lorentziana(var, y0, Amplitude, var0, ancho, phi):
    x = var - var0
    den = (4*x**2 + ancho**2)**2
    d_abs = (2*Amplitude*ancho/np.pi) * 8*x / den
    d_disp = (2*Amplitude/np.pi) * (8*x**2 - 2*ancho**2) / den
    return y0 - np.cos(phi)*d_abs + np.sin(phi)*d_disp

def una_lorentziana(var, y0, m, A, var0, ancho, phi):
    """Una derivada de lorentziana sobre un fondo lineal y0 + m*var."""
    return y0 + m*var + lorentziana(var, 0, A, var0, ancho, phi)

def dos_lorentzianas(var, y0, m, A1, var0_1, ancho1, phi1, A2, var0_2, ancho2, phi2):
    """Dos derivadas de lorentziana sobre un fondo lineal y0 + m*var."""
    return (y0 + m*var
            + lorentziana(var, 0, A1, var0_1, ancho1, phi1)
            + lorentziana(var, 0, A2, var0_2, ancho2, phi2))

# CORREGIR ESTO NUEVAMENTE
def kittel(H_ext, g, M_eff, H_uniaxial, H_cubico, eje_facil = True):
    if eje_facil:
        return (g/714.5)*np.sqrt((H_ext + H_uniaxial + H_cubico)*(H_ext + H_uniaxial + H_cubico + 4*np.pi*M_eff))
    else:
        return (g/714.5)*np.sqrt((H_ext -H_uniaxial - H_cubico)*(H_ext + H_cubico/2 + 4*np.pi*M_eff))

def ancho_de_linea(frecuency_GHz, delta_H0, damping, g):
    gamma = 8794000 * g 
    return delta_H0 + (4/np.sqrt(3))*np.pi*damping*frecuency_GHz*1e9/gamma

