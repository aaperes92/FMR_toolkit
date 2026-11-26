"""Variación angular de Hr en el plano para una bicapa acoplada, por Smit-Beljers.

Lee el output de los ajustes de la variación angular experimental (por ejemplo
output_2peak.txt de fit_positive), calcula para cada ángulo del campo los campos
de resonancia de los dos modos (acústico y óptico) y grafica teoría y experimento.
"""

import os
import time

import matplotlib.pyplot as plt
from fmrtoolkit.theory.smit_beljers import matriz_2capas
import numpy as np
from scipy.optimize import minimize
from sympy import lambdify, symbols

from fmrtoolkit.theory.free_energy import e_libre_IP_2L


def campo_resonancia(campos, omega, BX):
    """Primer campo donde omega pasa BX, por interpolación lineal.

    Devuelve (Hr, i), con i el índice del campo justo antes del cruce,
    o (nan, None) si en el rango de campos no hay cruce.
    """
    if omega[0] >= BX:                 # la resonancia está por debajo del rango
        return np.nan, None
    k = np.flatnonzero((omega[:-1] < BX) & (omega[1:] >= BX))
    if len(k) == 0:                    # por encima del rango
        return np.nan, None
    i = k[0]
    return campos[i] + (BX - omega[i]) * (campos[i+1] - campos[i]) / (omega[i+1] - omega[i]), i


# ==================================================
# VARIACIÓN ANGULAR EN EL PLANO (IP) DE UNA BICAPA
# ==================================================

def variacion_angular_ip_bicapa(archivo,
                                magn_a=1682, magn_b=770,
                                espesor_a=2.5e-6, espesor_b=5e-7,
                                Hc_a=150, Hc_b=150, Hu_a=50, Hu_b=50, ang_u=45,
                                g_a=2.088, g_b=2.091,
                                A=0.8, frecuencia=24.9e9,
                                col_angulo=0, col_Hr=1, defasaje_deg=-3,
                                margen_campo=1000, paso_campo=20,
                                ang_inicio=0, ang_fin=180, paso_ang=5,
                                paso_phi_M=2, graficar=True):
    """
    archivo              : output_*.txt de los ajustes de la variación angular experimental
    magn_a, magn_b       : magnetización de cada capa (emu/cm³)
    espesor_a, espesor_b : espesor de cada capa (cm)
    Hc_a, Hc_b           : campos de anisotropía cúbica (Oe)
    Hu_a, Hu_b           : campos de anisotropía uniaxial (Oe)
    ang_u                : dirección del eje fácil uniaxial (grados)
    g_a, g_b             : factor g de cada capa
    A                    : acople entre capas (erg/cm²). Con A > 0 (ferro) el modo
                           acústico es el de menor frecuencia
    frecuencia           : frecuencia de medición (Hz)
    col_angulo           : columna del ángulo en el archivo (la 0)
    col_Hr               : columna (o lista de columnas) del Hr experimental que se grafica;
                           con output_2peak.txt, [1, 3] grafica los dos picos
    defasaje_deg         : corrimiento de los ángulos experimentales para que coincidan con la teoría
    margen_campo         : Oe que se agregan por debajo y por encima del rango experimental
    paso_campo           : paso de campo de la simulación (Oe)
    ang_inicio, ang_fin, paso_ang : ángulos del campo que se simulan (grados, ang_fin incluido)
    paso_phi_M           : paso en grados de la grilla inicial del equilibrio de M
                           (después se refina, así que puede ser grueso)
    graficar             : si es False, guarda el PDF pero no abre la ventana

    Devuelve: ángulos del campo, Hr acústico, Hr óptico (Oe; nan si no cae en el
    rango de campos) y los ángulos de equilibrio de cada capa en la resonancia
    acústica (grados, entre -90° y 270°).
    """

    inicio = time.time()

    # ==================================================
    # DATOS EXPERIMENTALES
    # ==================================================

    columnas = [col_Hr] if isinstance(col_Hr, int) else list(col_Hr)

    data = np.loadtxt(archivo, skiprows=1, delimiter=',')
    angulo_exp = data[:, col_angulo]
    Hr_exp = data[:, columnas]

    # Rango de campos de la simulación: el experimental más un margen de seguridad
    campos = np.arange(max(np.nanmin(Hr_exp) - margen_campo, paso_campo),
                       np.nanmax(Hr_exp) + margen_campo, paso_campo)

    # ==================================================
    # PARÁMETROS
    # ==================================================

    h, frec, angmagn_a, angazimut_a, angmagn_b, angazimut_b = symbols(
        'h, frec, angmagn_a, angazimut_a, angmagn_b, angazimut_b')

    beta = np.deg2rad(ang_u)          # dirección del eje fácil uniaxial en radianes
    Ku_a = magn_a*Hu_a/2
    Kc_a = magn_a*Hc_a/2
    Ku_b = magn_b*Hu_b/2
    Kc_b = magn_b*Hc_b/2

    BX = np.float64(2*np.pi*frecuencia)

    # Grilla del ángulo de M de las dos capas: toda la vuelta, en RADIANES
    ang_M_rad = np.deg2rad(np.arange(0, 360, paso_phi_M))
    phi_a_grid, phi_b_grid = np.meshgrid(ang_M_rad, ang_M_rad, indexing='ij')

    angulos = np.arange(ang_inicio, ang_fin + paso_ang/2, paso_ang)
    Hr_ac = []
    Hr_op = []
    ang_eqa = []
    ang_eqb = []

    for valor in angulos:
        angcamp = np.deg2rad(valor)   # ángulo del campo en radianes

        Elibre = e_libre_IP_2L(angazimut_a, angmagn_a, angazimut_b, angmagn_b, h, angcamp,
                               magn_a, magn_b, Kc_a, Kc_b, Ku_a, Ku_b, beta, A,
                               espesor_a, espesor_b)

        m = matriz_2capas(Elibre, angazimut_a, angmagn_a, angazimut_b, angmagn_b, frec,
                  magn_a, magn_b, espesor_a, espesor_b, g_a, g_b, damp_a=0, damp_b=0)

        # m = frec*C + K: las frecuencias son los autovalores de -C^-1 K
        C_inv = np.linalg.inv(np.array(m.diff(frec).evalf(), dtype=complex))
        K_num = lambdify((angmagn_a, angmagn_b, angazimut_a, angazimut_b, h), m.subs(frec, 0), 'numpy')
        energia_num = lambdify((angmagn_a, angmagn_b, angazimut_a, angazimut_b, h), Elibre, 'numpy')

        # ==================================================
        # ÁNGULOS DE EQUILIBRIO Y FRECUENCIAS PARA CADA CAMPO
        # ==================================================

        lista_min = []

        for campo in campos:
            # 1) Grilla en toda la vuelta para las dos capas
            Elibre_campo = energia_num(phi_a_grid, phi_b_grid, np.pi/2, np.pi/2, campo)   # M en el plano
            idx = np.unravel_index(np.argmin(Elibre_campo), Elibre_campo.shape)

            # 2) Se refina desde el mejor punto de la grilla
            E0 = Elibre_campo[idx]
            escala = abs(E0) if E0 != 0 else 1.0
            res = minimize(lambda x: (energia_num(x[0], x[1], np.pi/2, np.pi/2, campo) - E0) / escala,
                           [phi_a_grid[idx], phi_b_grid[idx]], method='Nelder-Mead',
                           options={'xatol': 1e-10, 'fatol': 1e-14, 'maxiter': 5000})
            ang_a, ang_b = res.x                                     # RADIANES

            raices = np.linalg.eigvals(
                -C_inv @ np.array(K_num(ang_a, ang_b, np.pi/2, np.pi/2, campo), dtype=complex))
            positivas = list(np.sort(raices.real[raices.real > 0]))   # rad/s, de menor a mayor
            positivas += [np.nan] * (2 - len(positivas))
            f_acustico, f_optico = positivas

            lista_min.append([campo, f_acustico, f_optico,
                              (np.rad2deg(ang_a) + 90) % 360 - 90,     # GRADOS, entre -90 y 270
                              (np.rad2deg(ang_b) + 90) % 360 - 90])

        matriz = np.array(lista_min)

        # ==================================================
        # CAMPOS DE RESONANCIA DE LOS DOS MODOS
        # ==================================================

        hr_ac, i_ac = campo_resonancia(matriz[:, 0], matriz[:, 1], BX)
        hr_op, i_op = campo_resonancia(matriz[:, 0], matriz[:, 2], BX)

        Hr_ac.append(hr_ac)
        Hr_op.append(hr_op)
        ang_eqa.append(matriz[i_ac, 3] if i_ac is not None else np.nan)
        ang_eqb.append(matriz[i_ac, 4] if i_ac is not None else np.nan)
        print(f'{valor:5.1f}°  Hr acústico = {hr_ac:.1f} Oe   Hr óptico = {hr_op:.1f} Oe')

    Hr_ac = np.array(Hr_ac)
    Hr_op = np.array(Hr_op)
    ang_eqa = np.array(ang_eqa)
    ang_eqb = np.array(ang_eqb)

    if np.all(np.isnan(Hr_ac)) and np.all(np.isnan(Hr_op)):
        print(f'Ningún modo resuena entre {campos[0]:.0f} y {campos[-1]:.0f} Oe: '
              f'aumentá margen_campo o revisá los parámetros.')

    # ==================================================
    # GUARDAR (en la misma carpeta que el archivo experimental)
    # ==================================================

    carpeta = os.path.dirname(os.path.abspath(archivo))
    nombre = f'output_angular_IP_bicapa_A{A}_eje{ang_u}'

    np.savetxt(os.path.join(carpeta, nombre + '.txt'),
               np.column_stack((angulos, Hr_ac, Hr_op, ang_eqa, ang_eqb)), delimiter=',',
               header='anguloH (deg), Hr acustico (Oe), Hr optico (Oe), ang M_a (deg), ang M_b (deg)',
               comments='')

    # ==================================================
    # GRÁFICA (el PDF se guarda siempre; la ventana solo si graficar=True)
    # ==================================================

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(angulos, Hr_ac, 'o--', label='Modo acústico', markersize=3)
    ax.plot(angulos, Hr_op, 's--', label='Modo óptico', markersize=3)
    for j, col in enumerate(columnas):
        ax.plot(angulo_exp - defasaje_deg, Hr_exp[:, j], 's', markersize=4,
                label='Experimento' if len(columnas) == 1 else f'Experimento (columna {col})')
    ax.set_xlabel('Ángulo en el plano (deg)')
    ax.set_ylabel('H$_r$ (Oe)')
    ax.set_title(f'IP angular variation, $A$ = {A} erg/cm$^2$')
    ax.legend()
    ax.grid(True)
    fig.savefig(os.path.join(carpeta, nombre + '.pdf'), bbox_inches='tight')

    if graficar:
        plt.show()
    else:
        plt.close(fig)

    print(f'Tiempo: {time.time() - inicio:.1f} s')

    return angulos, Hr_ac, Hr_op, ang_eqa, ang_eqb


if __name__ == '__main__':
    # se ejecuta solo si corrés el archivo directamente, no cuando se importa
    archivo = r"C:\Disco D\Study\Phd Bariloche\FeCoB\datos\output_2peak.txt"
    variacion_angular_ip_bicapa(archivo, col_Hr=[1, 3])
