"""Variación angular de Hr en el plano (monocapa), por Smit-Beljers.

Lee el output de los ajustes de la variación angular experimental (por ejemplo
output_2peak.txt de fit_positive), calcula la curva teórica Hr(ángulo) con
anisotropía uniaxial + cúbica en el plano y grafica ambas para compararlas.
"""

import os
import time

import matplotlib.pyplot as plt
import numpy as np
from sympy import I, Matrix, cos, diff, lambdify, pi, rad, re, sin, solve, symbols
from fmrtoolkit.theory.free_energy import e_libre_IP_1L, e_libre_OP_1L


def variacion_angular_ip(archivo,
                         Hu=20, Hc=175, magn=1155, ang_u=45, g=2.09,
                         frecuencia=23.9e9, espesor=1e-7,
                         col_angulo=0, col_Hr=1, defasaje_deg=12,
                         margen_campo=400, paso_campo=20,
                         ang_inicio=0, ang_fin=185, paso_ang=5,
                         paso_phi_M=0.5, graficar=True):
    """
    archivo       : output_*.txt de los ajustes de la variación angular experimental
    Hu, Hc        : campos de anisotropía uniaxial y cúbica (Oe)
    magn          : magnetización (emu/cm³)
    ang_u         : dirección del eje fácil uniaxial (grados)
    g, frecuencia : factor g y frecuencia de medición (Hz)
    espesor       : espesor (cm). En una monocapa se cancela; queda para bicapas
    col_angulo    : columna del ángulo en el archivo (la 0)
    col_Hr        : columna del Hr experimental que se compara
    defasaje_deg  : corrimiento de los ángulos experimentales para que coincidan con la teoría
    margen_campo  : Oe que se agregan por debajo y por encima del rango experimental
    paso_campo    : paso de campo de la simulación (Oe)
    ang_inicio, ang_fin, paso_ang : ángulos del campo que se simulan (grados, ang_fin incluido)
    paso_phi_M    : paso en grados para buscar el ángulo de equilibrio de M
    """
    inicio = time.time()

    # ==================================================
    # DATOS EXPERIMENTALES
    # ==================================================

    data = np.loadtxt(archivo, skiprows=1, delimiter=',')
    angulo_exp = data[:, col_angulo]
    Hr_exp = data[:, col_Hr]

    # Rango de campos de la simulación: el experimental más un margen de seguridad
    campos = np.arange(np.nanmin(Hr_exp) - margen_campo,
                       np.nanmax(Hr_exp) + margen_campo, paso_campo)

    Hc_sugerido = np.nanmax(Hr_exp) - np.nanmin(Hr_exp)
    print(f'Variación experimental de Hr: {Hc_sugerido:.0f} Oe (orientativo para elegir Hc)')

    # ==================================================
    # PARÁMETROS
    # ==================================================

    h, frec, angmagn, angazimut = symbols('h, frec, angmagn, angazimut')

    beta = float(rad(ang_u))          # dirección del eje fácil uniaxial en radianes
    Ku = magn*Hu/2
    Kc = magn*Hc/2
    gamma = 8794000*g
    BX = np.float64(2*np.pi*frecuencia)

    # Ángulo de M: se busca en toda la vuelta (0-360°) para que funcione con el campo > 180°
    ang_Ma_deg = np.arange(0, 360, paso_phi_M)
    ang_Ma_rad = np.deg2rad(ang_Ma_deg)

    angulo_IP = []
    Hr = []

    for valor in np.arange(ang_inicio, ang_fin + paso_ang/2, paso_ang):
        angcamp = float(rad(valor))   # ángulo del campo en radianes

        Elibre = e_libre_IP_1L(angazimut, angmagn, h, angcamp, espesor, magn, Kc, Ku, beta)

        # Derivadas segundas
        E_theta1_phi1 = diff(Elibre, angazimut, angmagn)
        E_theta1_theta1 = diff(Elibre, angazimut, angazimut)
        E_phi1_phi1 = diff(Elibre, angmagn, angmagn)

        m = Matrix([[I*(frec/gamma) + E_theta1_phi1/(espesor*magn*sin(angazimut)),
                     E_phi1_phi1/(espesor*magn*(sin(angazimut))**2)],
                    [-E_theta1_theta1/(espesor*magn),
                     I*(frec/gamma) - E_theta1_phi1/(espesor*magn*sin(angazimut))]])

        # ==================================================
        # ÁNGULO DE EQUILIBRIO Y FRECUENCIA PARA CADA CAMPO
        # ==================================================

        lista_min = []
        for campo in campos:

            energia_num = lambdify((angmagn, angazimut, h), Elibre, 'numpy')

            for campo in campos:
                Elibre_campo = energia_num(ang_Ma_rad, np.pi/2, campo)   # M en el plano, todos los ángulos
                ang_a = ang_Ma_deg[np.argmin(Elibre_campo)]

            ang_a = ang_Ma_deg[np.argmin(Elibre_campo)]

            m_eval = m.evalf(20, subs={angmagn: ang_a*np.pi/180, angazimut: np.pi/2, h: campo})
            determinante = m_eval.det(method='berkowitz')
            solucion = list(solve(determinante, frec))

            lista_min.append([campo, valor, solucion[1], ang_a])

        matriz = np.array(lista_min)

        # ==================================================
        # INTERPOLACIÓN LINEAL: campo donde la frecuencia cruza BX
        # ==================================================

        f_primera = float(re(matriz[0][2]))
        f_ultima = float(re(matriz[-1][2]))

        if f_primera >= BX:
            raise ValueError(f'{valor:.0f}°: la resonancia está por DEBAJO de {campos[0]:.0f} Oe. '
                             f'Aumentá margen_campo o revisá Ms y las anisotropías.')

        for i in range(1, len(matriz)):
            if re(matriz[i][2]) >= BX:
                H0, H1 = float(matriz[i-1][0]), float(matriz[i][0])
                f0, f1 = float(re(matriz[i-1][2])), float(re(matriz[i][2]))
                h_res = H0 + (BX - f0) * (H1 - H0) / (f1 - f0)

                angulo_IP.append(valor)
                Hr.append(h_res)
                print(f'{valor:5.1f}°  Hr = {h_res:.1f} Oe')
                break
        else:
            raise ValueError(f'{valor:.0f}°: la resonancia está por ENCIMA de {campos[-1]:.0f} Oe '
                             f'(f máx = {f_ultima/(2*np.pi)/1e9:.2f} GHz). '
                             f'Aumentá margen_campo o revisá Ms y las anisotropías.')

    angulo_IP = np.array(angulo_IP)
    Hr = np.array(Hr)

    # ==================================================
    # GUARDAR (en la misma carpeta que el archivo experimental)
    # ==================================================

    carpeta = os.path.dirname(os.path.abspath(archivo))
    nombre = f'output_angular_IP_teoria_magn{magn}_eje{ang_u}'

    np.savetxt(os.path.join(carpeta, nombre + '.txt'), np.column_stack((angulo_IP, Hr)),
               delimiter=',', header='Angulo,Hr', comments='')

    # ==================================================
    # GRÁFICA (el PDF se guarda siempre; la ventana solo si graficar=True)
    # ==================================================

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(angulo_IP, Hr, 'o--', label='Teoría', markersize=3)
    ax.plot(angulo_exp - defasaje_deg, Hr_exp, 's', label='Experimento', markersize=4)
    ax.set_xlabel('Ángulo (deg)')
    ax.set_ylabel('Hr (Oe)')
    ax.set_title('IP angular variation')
    ax.legend()
    ax.grid(True)
    fig.savefig(os.path.join(carpeta, nombre + '.pdf'), bbox_inches='tight')

    if graficar:
        plt.show()
    else:
        plt.close(fig)

    print(f'Tiempo: {time.time() - inicio:.1f} s')

    return angulo_IP, Hr


if __name__ == '__main__':
    # se ejecuta solo si corrés el archivo directamente, no cuando se importa
    archivo = r"C:\Disco D\Study\Phd Bariloche\FeCoB\datos\output_2peak.txt"
    variacion_angular_ip(archivo)
