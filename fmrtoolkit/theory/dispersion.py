"""Relaciones de dispersión teóricas (frecuencia vs campo), campo en el plano.

Dos funciones independientes, una para cada caso:
    dispersion_1capa(...)   monocapa
    dispersion_2capas(...)  bicapa acoplada (A = acople entre capas)

Cada una calcula, guarda el .txt y el .pdf en `carpeta`, grafica y devuelve los
resultados. Los parámetros que comparten tienen el mismo nombre.
"""

import os
import time

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize
from sympy import I, Matrix, diff, lambdify, rad, sin, symbols

from fmrtoolkit.theory.free_energy import e_libre_IP_1L, e_libre_IP_2L


# ==================================================
# MONOCAPA
# ==================================================

def dispersion_1capa(magn=1300, g=2.015, damp=0.0026,
                     Hc=250, Hu=0, ang_u=45, espesor=1e-7,
                     ang_campo=0, campo_min=5, campo_max=4000, paso_campo=50,
                     paso_phi_M=0.01, carpeta='.', graficar=True):
    """
    magn          : magnetización (emu/cm³)
    g, damp       : factor g y amortiguamiento de Gilbert
    Hc, Hu        : campos de anisotropía cúbica y uniaxial (Oe)
    ang_u         : dirección del eje fácil uniaxial (grados)
    espesor       : espesor (cm). En una monocapa se cancela
    ang_campo     : ángulo del campo en el plano (grados)
    campo_min, campo_max, paso_campo : campos que se calculan (Oe)
    paso_phi_M    : paso en grados para buscar el ángulo de equilibrio de M
    carpeta       : dónde se guardan el .txt y el .pdf
    graficar      : si es False, guarda el .pdf pero no abre la ventana

    Devuelve campos (Oe), frecuencia (GHz) y ángulo de equilibrio de M (grados).
    """
    inicio = time.time()

    # ==================================================
    # PARÁMETROS
    # ==================================================

    h, frec, angmagn, angazimut = symbols('h, frec, angmagn, angazimut')

    angcamp = float(rad(ang_campo))   # ángulo del campo en radianes
    beta = float(rad(ang_u))          # eje fácil uniaxial en radianes
    Ku = magn*Hu/2
    Kc = magn*Hc/2
    gamma = 8794000*g

    campos = np.arange(campo_min, campo_max, paso_campo)

    # Ángulo de M: toda la vuelta, así funciona con cualquier ángulo del campo
    ang_M_rad = np.deg2rad(np.arange(0, 360, paso_phi_M))

    # ==================================================
    # ENERGÍA, DERIVADAS Y MATRIZ
    # ==================================================

    Elibre = e_libre_IP_1L(angazimut, angmagn, h, angcamp, espesor, magn, Kc, Ku, beta)

    E_theta_phi = diff(Elibre, angazimut, angmagn)
    E_theta_theta = diff(Elibre, angazimut, angazimut)
    E_phi_phi = diff(Elibre, angmagn, angmagn)

    tM, s = espesor*magn, sin(angazimut)
    m = Matrix([[I*frec/gamma + E_theta_phi/(tM*s) + damp*E_theta_theta/tM,
                 E_phi_phi/(tM*s**2) + damp*E_theta_phi/(tM*s)],
                [-E_theta_theta/tM + damp*E_theta_phi/(tM*s),
                 I*frec/gamma - E_theta_phi/(tM*s) + damp*E_phi_phi/(tM*s**2)]])

    # La matriz es m = frec*C + K, así que det(m) = 0 equivale a que frec sea
    # autovalor de -C^-1 K. Da las mismas raíces que resolver el determinante,
    # pero es mucho más rápido.
    C_inv = np.linalg.inv(np.array(m.diff(frec).evalf(), dtype=complex))
    K_num = lambdify((angmagn, angazimut, h), m.subs(frec, 0), 'numpy')

    energia_num = lambdify((angmagn, angazimut, h), Elibre, 'numpy')

    # ==================================================
    # ÁNGULO DE EQUILIBRIO Y FRECUENCIA PARA CADA CAMPO
    # ==================================================

    freq = []
    ang_eq = []

    for campo in campos:
        Elibre_campo = energia_num(ang_M_rad, np.pi/2, campo)   # M en el plano, todos los ángulos
        ang = ang_M_rad[np.argmin(Elibre_campo)]                # en radianes

        raices = np.linalg.eigvals(-C_inv @ np.array(K_num(ang, np.pi/2, campo), dtype=complex))
        positivas = np.sort(raices.real[raices.real > 0]) / (2*np.pi*1e9)   # GHz

        freq.append(positivas[0] if len(positivas) > 0 else np.nan)
        ang_eq.append(np.rad2deg(ang))

    freq = np.array(freq)
    ang_eq = np.array(ang_eq)

    # ==================================================
    # GUARDAR Y GRAFICAR
    # ==================================================

    nombre = f'Dispersion_1capa_magn{magn}_{ang_campo}deg'
    np.savetxt(os.path.join(carpeta, nombre + '.txt'), np.column_stack((campos, freq, ang_eq)),
               delimiter=',', header='Field (Oe), Frequency (GHz), angulo magnetizacion (deg)',
               comments='')

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(campos, freq, 'o--', label='mode', markersize=3)
    ax.set_xlabel('Resonance Field (Oe)')
    ax.set_ylabel('Frequency (GHz)')
    ax.set_title(f'Dispersion relation, single layer, {ang_campo} degree')
    ax.legend()
    ax.grid(True)
    fig.savefig(os.path.join(carpeta, nombre + '.pdf'), bbox_inches='tight')

    if graficar:
        plt.show()
    else:
        plt.close(fig)

    print(f'Tiempo: {time.time() - inicio:.1f} s')

    return campos, freq, ang_eq


# ==================================================
# BICAPA
# ==================================================

def dispersion_2capas(magn_a=1300, magn_b=770, g_a=2.015, g_b=2.011,
                      damp_a=0.0026, damp_b=0.006,
                      Hc_a=250, Hc_b=250, Hu_a=0, Hu_b=0, ang_u=45,
                      espesor_a=1e-6, espesor_b=1e-6, A=80,
                      ang_campo=0, campo_min=5, campo_max=4000, paso_campo=50,
                      paso_phi_M=2, carpeta='.', graficar=True):
    """
    magn_a, magn_b     : magnetización de cada capa (emu/cm³)
    g_a, g_b           : factor g de cada capa
    damp_a, damp_b     : amortiguamiento de Gilbert de cada capa
    Hc_a, Hc_b         : campos de anisotropía cúbica (Oe)
    Hu_a, Hu_b         : campos de anisotropía uniaxial (Oe)
    ang_u              : dirección del eje fácil uniaxial (grados)
    espesor_a, espesor_b : espesores (cm)
    A                  : acople entre capas, como en e_libre_IP_2L
    ang_campo          : ángulo del campo en el plano (grados)
    campo_min, campo_max, paso_campo : campos que se calculan (Oe)
    paso_phi_M         : paso en grados de la grilla inicial para el equilibrio
                         (después se refina, así que no hace falta que sea chico)
    carpeta            : dónde se guardan el .txt y el .pdf
    graficar           : si es False, guarda el .pdf pero no abre la ventana

    Devuelve campos (Oe), las dos frecuencias (GHz, f1 < f2) y los ángulos de
    equilibrio de cada capa (grados).
    """
    inicio = time.time()

    # ==================================================
    # PARÁMETROS
    # ==================================================

    h, frec, angmagn_a, angazimut_a, angmagn_b, angazimut_b = symbols(
        'h, frec, angmagn_a, angazimut_a, angmagn_b, angazimut_b')

    angcamp = float(rad(ang_campo))   # ángulo del campo en radianes
    beta = float(rad(ang_u))          # eje fácil uniaxial en radianes
    Ku_a = magn_a*Hu_a/2
    Kc_a = magn_a*Hc_a/2
    Ku_b = magn_b*Hu_b/2
    Kc_b = magn_b*Hc_b/2
    gamma1 = 8794000*g_a
    gamma2 = 8794000*g_b

    campos = np.arange(campo_min, campo_max, paso_campo)

    # Grilla de ángulos de M para las dos capas: toda la vuelta
    ang_M_rad = np.deg2rad(np.arange(0, 360, paso_phi_M))
    AA, BB = np.meshgrid(ang_M_rad, ang_M_rad, indexing='ij')

    # ==================================================
    # ENERGÍA, DERIVADAS Y MATRIZ
    # ==================================================

    Elibre = e_libre_IP_2L(angazimut_a, angmagn_a, angazimut_b, angmagn_b, h, angcamp,
                           magn_a, magn_b, Kc_a, Kc_b, Ku_a, Ku_b, beta, A, espesor_a, espesor_b)

    E_theta1_phi1 = diff(Elibre, angazimut_a, angmagn_a)
    E_theta1_phi2 = diff(Elibre, angazimut_a, angmagn_b)
    E_theta1_theta1 = diff(Elibre, angazimut_a, angazimut_a)
    E_phi1_phi1 = diff(Elibre, angmagn_a, angmagn_a)
    E_theta2_phi2 = diff(Elibre, angazimut_b, angmagn_b)
    E_theta2_phi1 = diff(Elibre, angazimut_b, angmagn_a)
    E_theta2_theta1 = diff(Elibre, angazimut_b, angazimut_a)
    E_theta2_theta2 = diff(Elibre, angazimut_b, angazimut_b)
    E_phi2_phi2 = diff(Elibre, angmagn_b, angmagn_b)
    E_phi1_phi2 = diff(Elibre, angmagn_a, angmagn_b)

    Ma, ta, d1, sa = magn_a, espesor_a, damp_a, sin(angazimut_a)
    Mb, tb, d2, sb = magn_b, espesor_b, damp_b, sin(angazimut_b)
    m = Matrix([
        [I*frec/gamma1 + E_theta1_phi1/(ta*Ma*sa) + d1*E_theta1_theta1/(ta*Ma),
         E_phi1_phi1/(ta*Ma*sa**2) + d1*E_theta1_phi1/(ta*Ma*sa),
         E_theta2_phi1/(ta*Mb*sa) + d1*E_theta2_theta1/(ta*Mb),
         E_phi1_phi2/(ta*Mb*sa*sb) + d1*E_theta1_phi2/(ta*Mb*sb)],
        [-E_theta1_theta1/(ta*Ma) + d1*E_theta1_phi1/(ta*Ma*sa),
         I*frec/gamma1 - E_theta1_phi1/(ta*Ma*sa) + d1*E_phi1_phi1/(ta*Ma*sa**2),
         -E_theta2_theta1/(ta*Mb) + d1*E_theta2_phi1/(ta*Mb*sa),
         -E_theta1_phi2/(ta*Mb*sb) + d1*E_phi1_phi2/(ta*Mb*sb*sa)],
        [E_theta1_phi2/(tb*Ma*sb) + d2*E_theta2_theta1/(tb*Ma),
         E_phi1_phi2/(tb*Ma*sa*sb) + d2*E_theta2_phi1/(tb*Ma*sa),
         I*frec/gamma2 + E_theta2_phi2/(tb*Mb*sb) + d2*E_theta2_theta2/(tb*Mb),
         E_phi2_phi2/(tb*Mb*sb**2) + d2*E_theta2_phi2/(tb*Mb*sb)],
        [-E_theta2_theta1/(tb*Ma) + d2*E_theta1_phi2/(tb*Ma*sb),
         -E_theta2_phi1/(tb*Ma*sa) + d2*E_phi1_phi2/(tb*Ma*sa*sb),
         -E_theta2_theta2/(tb*Mb) + d2*E_theta2_phi2/(tb*Mb*sb),
         I*frec/gamma2 - E_theta2_phi2/(tb*Mb*sb) + d2*E_phi2_phi2/(tb*Mb*sb**2)]])

    # m = frec*C + K: las frecuencias son los autovalores de -C^-1 K
    C_inv = np.linalg.inv(np.array(m.diff(frec).evalf(), dtype=complex))
    K_num = lambdify((angmagn_a, angmagn_b, angazimut_a, angazimut_b, h), m.subs(frec, 0), 'numpy')

    energia_num = lambdify((angmagn_a, angmagn_b, angazimut_a, angazimut_b, h), Elibre, 'numpy')

    # ==================================================
    # ÁNGULOS DE EQUILIBRIO Y FRECUENCIAS PARA CADA CAMPO
    # ==================================================

    freq1 = []
    freq2 = []
    ang_a_eq = []
    ang_b_eq = []

    for campo in campos:
        # 1) Grilla en toda la vuelta para las dos capas
        Elibre_campo = energia_num(AA, BB, np.pi/2, np.pi/2, campo)   # M en el plano
        idx = np.unravel_index(np.argmin(Elibre_campo), Elibre_campo.shape)

        # 2) Se refina desde el mejor punto de la grilla
        E0 = Elibre_campo[idx]
        escala = abs(E0) if E0 != 0 else 1.0
        res = minimize(lambda x: (energia_num(x[0], x[1], np.pi/2, np.pi/2, campo) - E0) / escala,
                       [AA[idx], BB[idx]], method='Nelder-Mead',
                       options={'xatol': 1e-10, 'fatol': 1e-14, 'maxiter': 5000})
        ang_a, ang_b = res.x                                           # en radianes

        raices = np.linalg.eigvals(
            -C_inv @ np.array(K_num(ang_a, ang_b, np.pi/2, np.pi/2, campo), dtype=complex))
        positivas = list(np.sort(raices.real[raices.real > 0]) / (2*np.pi*1e9))   # GHz
        positivas += [np.nan] * (2 - len(positivas))                 # si falta un modo, queda nan

        freq1.append(positivas[0])   # modo de menor frecuencia
        freq2.append(positivas[1])   # modo de mayor frecuencia
        ang_a_eq.append(np.rad2deg(ang_a) % 360)
        ang_b_eq.append(np.rad2deg(ang_b) % 360)

    freq1 = np.array(freq1)
    freq2 = np.array(freq2)
    ang_a_eq = np.array(ang_a_eq)
    ang_b_eq = np.array(ang_b_eq)

    # ==================================================
    # GUARDAR Y GRAFICAR
    # ==================================================

    nombre = f'Dispersion_2capas_A{A}_{ang_campo}deg'
    np.savetxt(os.path.join(carpeta, nombre + '.txt'),
               np.column_stack((campos, freq1, freq2, ang_a_eq, ang_b_eq)), delimiter=',',
               header='Field (Oe), Frequency1 (GHz), Frequency2 (GHz), '
                      'angulo magnetizacion capa A (deg), angulo magnetizacion capa B (deg)',
               comments='')

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(campos, freq1, 'o--', label='low frequency mode', markersize=3)
    ax.plot(campos, freq2, 's--', label='high frequency mode', markersize=3)
    ax.set_xlabel('Resonance Field (Oe)')
    ax.set_ylabel('Frequency (GHz)')
    ax.set_title(f'Dispersion relation, bilayer A = {A}, {ang_campo} degree')
    ax.legend()
    ax.grid(True)
    fig.savefig(os.path.join(carpeta, nombre + '.pdf'), bbox_inches='tight')

    if graficar:
        plt.show()
    else:
        plt.close(fig)

    print(f'Tiempo: {time.time() - inicio:.1f} s')

    return campos, freq1, freq2, ang_a_eq, ang_b_eq


if __name__ == '__main__':
    # se ejecuta solo si corrés el archivo directamente, no cuando se importa
    carpeta = r'C:\Disco D\Study\Phd Bariloche\FMR'

    dispersion_2capas(A=80, carpeta=carpeta)
    # dispersion_1capa(magn=1300, carpeta=carpeta)
