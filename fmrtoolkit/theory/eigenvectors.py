"""Autovectores de una bicapa acoplada: precesión de M de cada capa en la resonancia.

Para cada modo (acústico y óptico) busca el campo de resonancia a la frecuencia de
medición, calcula el equilibrio de las dos capas en ese campo y resuelve la respuesta
forzada (con amortiguamiento) a un campo de microondas h_rf. Grafica y guarda las
componentes dinámicas en función del tiempo, las elipses de precesión y un GIF.
"""

import os
import time

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from scipy.optimize import minimize
from sympy import lambdify, symbols

from fmrtoolkit.theory.bilayer import campo_resonancia
from fmrtoolkit.theory.free_energy import e_libre_IP_2L
from fmrtoolkit.theory.smit_beljers import matriz_2capas

NOMBRES_MODO = {'acustico': 'acústico', 'optico': 'óptico'}


def autovectores_bicapa(magn_a=1700, magn_b=770, espesor_a=10e-7, espesor_b=5e-7,
                        Hc_a=250, Hc_b=0, Hu_a=250, Hu_b=0, ang_u=45,
                        g_a=2.088, g_b=2.091, damp_a=0.0026, damp_b=0.006,
                        A=0.4, frecuencia=9.76e9, ang_campo=0, h_rf=1,
                        campo_min=10, campo_max=1400, paso_campo=10,
                        paso_phi_M=2, n_tiempos=51,
                        carpeta='.', guardar_gif=True, graficar=True):
    """
    magn_a, magn_b       : magnetización de cada capa (emu/cm³)
    espesor_a, espesor_b : espesor de cada capa (cm)
    Hc_a, Hc_b           : campos de anisotropía cúbica (Oe)
    Hu_a, Hu_b           : campos de anisotropía uniaxial (Oe)
    ang_u                : dirección del eje fácil uniaxial (grados)
    g_a, g_b             : factor g de cada capa
    damp_a, damp_b       : amortiguamiento de Gilbert de cada capa
    A                    : acople entre capas (erg/cm²)
    frecuencia           : frecuencia de medición (Hz)
    ang_campo            : ángulo del campo en el plano (grados)
    h_rf                 : amplitud del campo de microondas (Oe)
    campo_min, campo_max, paso_campo : campos de la relación de dispersión (Oe)
    paso_phi_M           : paso en grados de la grilla inicial del equilibrio (después se refina)
    n_tiempos            : instantes en un período de precesión (incluye t = 0 y t = T)
    carpeta              : dónde se guardan los .txt, .png y .gif
    guardar_gif          : si es False, no genera la animación
    graficar             : si es False, guarda todo pero no abre ventanas

    Devuelve un diccionario con:
        'campos', 'f_acustico', 'f_optico' : relación de dispersión (Oe, GHz)
        'acustico', 'optico' : diccionario del modo, o None si no resuena en el rango.
            Cada uno tiene 'Hr' (Oe), 'ang_a', 'ang_b' (equilibrio en Hr, grados),
            'amplitudes' (complejas, normalizadas por Ms: m_theta_a, m_phi_a, m_theta_b, m_phi_b),
            't_T' y 'serie' (parte real de cada componente en el tiempo, shape (n_tiempos, 4)).
    """
    inicio = time.time()

    # ==================================================
    # PARÁMETROS
    # ==================================================

    h, frec, angmagn_a, angazimut_a, angmagn_b, angazimut_b = symbols(
        'h, frec, angmagn_a, angazimut_a, angmagn_b, angazimut_b')

    angcamp = np.deg2rad(ang_campo)
    beta = np.deg2rad(ang_u)
    Ku_a, Kc_a = magn_a*Hu_a/2, magn_a*Hc_a/2
    Ku_b, Kc_b = magn_b*Hu_b/2, magn_b*Hc_b/2
    BX = 2*np.pi*frecuencia

    campos = np.arange(campo_min, campo_max, paso_campo)

    ang_M_rad = np.deg2rad(np.arange(0, 360, paso_phi_M))
    phi_a_grid, phi_b_grid = np.meshgrid(ang_M_rad, ang_M_rad, indexing='ij')

    # ==================================================
    # ENERGÍA Y MATRICES (sin damping: frecuencias; con damping: respuesta forzada)
    # ==================================================

    Elibre = e_libre_IP_2L(angazimut_a, angmagn_a, angazimut_b, angmagn_b, h, angcamp,
                           magn_a, magn_b, Kc_a, Kc_b, Ku_a, Ku_b, beta, A,
                           espesor_a, espesor_b)

    angulos = (angmagn_a, angmagn_b, angazimut_a, angazimut_b, h)
    m_sin = matriz_2capas(Elibre, angazimut_a, angmagn_a, angazimut_b, angmagn_b, frec,
                          magn_a, magn_b, espesor_a, espesor_b, g_a, g_b)
    m_con = matriz_2capas(Elibre, angazimut_a, angmagn_a, angazimut_b, angmagn_b, frec,
                          magn_a, magn_b, espesor_a, espesor_b, g_a, g_b,
                          damp_a=damp_a, damp_b=damp_b)

    # m = frec*C + K: las frecuencias son los autovalores de -C^-1 K
    C_inv = np.linalg.inv(np.array(m_sin.diff(frec).evalf(), dtype=complex))
    K_num = lambdify(angulos, m_sin.subs(frec, 0), 'numpy')
    M_con_num = lambdify(angulos + (frec,), m_con, 'numpy')
    energia_num = lambdify(angulos, Elibre, 'numpy')

    def equilibrio(campo, x0=None):
        """Ángulos de equilibrio (rad) de las dos capas, con M en el plano."""
        if x0 is None:                                     # grilla en toda la vuelta
            E = energia_num(phi_a_grid, phi_b_grid, np.pi/2, np.pi/2, campo)
            idx = np.unravel_index(np.argmin(E), E.shape)
            x0 = [phi_a_grid[idx], phi_b_grid[idx]]
        E0 = energia_num(x0[0], x0[1], np.pi/2, np.pi/2, campo)
        escala = abs(E0) if E0 != 0 else 1.0
        res = minimize(lambda x: (energia_num(x[0], x[1], np.pi/2, np.pi/2, campo) - E0) / escala,
                       x0, method='Nelder-Mead',
                       options={'xatol': 1e-10, 'fatol': 1e-14, 'maxiter': 5000})
        return res.x

    # ==================================================
    # RELACIÓN DE DISPERSIÓN
    # ==================================================

    lista_min = []
    for campo in campos:
        ang_a, ang_b = equilibrio(campo)
        raices = np.linalg.eigvals(
            -C_inv @ np.array(K_num(ang_a, ang_b, np.pi/2, np.pi/2, campo), dtype=complex))
        positivas = list(np.sort(raices.real[raices.real > 0]))   # rad/s, de menor a mayor
        positivas += [np.nan] * (2 - len(positivas))              # si falta un modo, queda nan
        lista_min.append([campo, positivas[0], positivas[1], ang_a, ang_b])
    matriz = np.array(lista_min)

    resultado = {'campos': campos,
                 'f_acustico': matriz[:, 1]/(2*np.pi*1e9),
                 'f_optico': matriz[:, 2]/(2*np.pi*1e9)}

    # ==================================================
    # CADA MODO: Hr, equilibrio en Hr y respuesta forzada
    # ==================================================

    t_T = np.linspace(0, 1, n_tiempos)                    # tiempo en períodos
    for modo, col in (('acustico', 1), ('optico', 2)):
        Hr, i = campo_resonancia(matriz[:, 0], matriz[:, col], BX)
        if i is None:
            print(f'El modo {NOMBRES_MODO[modo]} no se encuentra visible para esa frecuencia '
                  f'({frecuencia/1e9:g} GHz) entre {campos[0]:g} y {campos[-1]:g} Oe.')
            resultado[modo] = None
            continue

        # Equilibrio exactamente en Hr, partiendo del campo de la grilla más cercano
        ang_a, ang_b = equilibrio(Hr, x0=[matriz[i, 3], matriz[i, 4]])

        # Respuesta forzada: m(BX)·v = -d, con d el término de microondas de cada capa.
        # Variables: v = (Ma·dθa, Ma·sinθa·dφa, Mb·dθb, Mb·sinθb·dφb)
        M = np.array(M_con_num(ang_a, ang_b, np.pi/2, np.pi/2, Hr, BX), dtype=complex)
        d = np.array([0, magn_a*h_rf, 0, magn_b*h_rf], dtype=complex)
        v = np.linalg.solve(M, -d)
        amp = v / np.array([magn_a, magn_a, magn_b, magn_b])       # normalizado por Ms

        # Evolución temporal: m(t) = Re(amp·e^{iωt}), con ωt = 2π·t/T
        fase = np.exp(1j*2*np.pi*t_T)[:, None]
        serie_compleja = amp[None, :] * fase
        serie = serie_compleja.real

        resultado[modo] = {'Hr': Hr,
                           'ang_a': (np.rad2deg(ang_a) + 180) % 360 - 180,
                           'ang_b': (np.rad2deg(ang_b) + 180) % 360 - 180,
                           'amplitudes': amp, 't_T': t_T, 'serie': serie}
        print(f'Modo {NOMBRES_MODO[modo]}: Hr = {Hr:.1f} Oe, '
              f'M_a a {resultado[modo]["ang_a"]:.1f}°, M_b a {resultado[modo]["ang_b"]:.1f}°')

        _guardar_txt(carpeta, modo, A, Hr, t_T, serie_compleja)
        _graficar_componentes(carpeta, modo, A, Hr, t_T, serie, graficar)
        _graficar_elipses(carpeta, modo, A, Hr, serie, graficar)
        if guardar_gif:
            _animar_elipses(carpeta, modo, A, t_T, serie, graficar)

    _graficar_dispersion(carpeta, A, frecuencia, resultado, graficar)

    if graficar:
        plt.show()

    print(f'Tiempo: {time.time() - inicio:.1f} s')
    return resultado


# ==================================================
# FUNCIONES AUXILIARES (guardar y graficar)
# ==================================================

def _guardar_txt(carpeta, modo, A, Hr, t_T, serie_compleja):
    """Mismas columnas que el programa original, para que lo lean los mismos scripts."""
    th1, ph1, th2, ph2 = serie_compleja.T
    mod = np.abs(serie_compleja)                       # módulos (constantes en el tiempo)
    area1 = np.pi*mod[:, 0]*mod[:, 1]
    area2 = np.pi*mod[:, 2]*mod[:, 3]
    datos = np.column_stack((t_T, th1.real, th1.imag, ph1.real, ph1.imag,
                             th2.real, th2.imag, ph2.real, ph2.imag,
                             area1, area2, mod[:, 0]/mod[:, 1], mod[:, 2]/mod[:, 3],
                             mod, np.full_like(t_T, Hr)))
    np.savetxt(os.path.join(carpeta, f'autovectores_{modo}_A{A:g}.txt'), datos, delimiter=',',
               header='t/T, m_theta1_re, m_theta1_im, m_phi1_re, m_phi1_im, m_theta2_re, '
                      'm_theta2_im, m_phi2_re, m_phi2_im, area1, area2, elipt1, elipt2, '
                      'm_theta1_modulus, m_phi1_modulus, m_theta2_modulus, m_phi2_modulus, Hr',
               comments='')


def _graficar_componentes(carpeta, modo, A, Hr, t_T, serie, graficar):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 8), sharex=True)
    ax1.plot(t_T, serie[:, 1], 'o--', color='r', label=r'm$_{\varphi_1}$', markersize=3)
    ax1.plot(t_T, serie[:, 3], 's', color='b', label=r'm$_{\varphi_2}$', markersize=3)
    ax1.set_ylabel(r'm$_{\varphi}$/M$_s$')
    ax1.set_title(f'Modo {NOMBRES_MODO[modo]}, A = {A:g} erg/cm$^2$, H$_r$ = {Hr:.0f} Oe\n'
                  'Componente dinámica en el plano')
    ax2.plot(t_T, serie[:, 0], 'o--', color='r', label=r'm$_{\theta_1}$', markersize=3)
    ax2.plot(t_T, serie[:, 2], 's', color='b', label=r'm$_{\theta_2}$', markersize=3)
    ax2.set_ylabel(r'm$_{\theta}$/M$_s$')
    ax2.set_title('Componente dinámica fuera del plano')
    ax2.set_xlabel('t/T')
    for ax in (ax1, ax2):
        ax.axhline(0, color='k', lw=0.8)
        ax.legend()
        ax.grid(True)
    fig.savefig(os.path.join(carpeta, f'componentes_{modo}_A{A:g}.png'), dpi=300,
                bbox_inches='tight')
    if not graficar:
        plt.close(fig)


def _graficar_elipses(carpeta, modo, A, Hr, serie, graficar):
    fig, ax = plt.subplots(figsize=(6, 6))
    for th, ph, color, nombre in ((serie[:, 0], serie[:, 1], 'r', 'Capa a'),
                                  (serie[:, 2], serie[:, 3], 'b', 'Capa b')):
        ax.plot(th, ph, '-', color=color, label=nombre)
        ax.plot(th[0], ph[0], 'o', color=color)                          # t = 0
        ax.annotate('', xy=(th[3], ph[3]), xytext=(th[0], ph[0]),        # sentido de giro
                    arrowprops=dict(arrowstyle='->', color=color, lw=2))
    ax.axhline(0, color='k', lw=0.5)
    ax.axvline(0, color='k', lw=0.5)
    ax.set_aspect('equal')
    ax.set_xlabel(r'$m_{\theta}/M_s$ (fuera del plano)')
    ax.set_ylabel(r'$m_{\varphi}/M_s$ (en el plano)')
    ax.set_title(f'Modo {NOMBRES_MODO[modo]}, A = {A:g} erg/cm$^2$, H$_r$ = {Hr:.0f} Oe')
    ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
    ax.grid(True)
    fig.savefig(os.path.join(carpeta, f'elipses_{modo}_A{A:g}.png'), dpi=300,
                bbox_inches='tight')
    if not graficar:
        plt.close(fig)


def _animar_elipses(carpeta, modo, A, t_T, serie, graficar):
    th1, ph1, th2, ph2 = serie.T
    fig, ax = plt.subplots(figsize=(6, 6))
    lim = 1.15*np.abs(serie).max()
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect('equal')
    ax.set_xlabel(r'$m_{\theta}/M_s$')
    ax.set_ylabel(r'$m_{\varphi}/M_s$')
    ax.grid(True)
    ax.plot(th1, ph1, ':', color='r', alpha=0.4)                 # elipse completa de fondo
    ax.plot(th2, ph2, ':', color='b', alpha=0.4)
    tray1, = ax.plot([], [], '-', color='r', lw=2, label='Capa a')
    tray2, = ax.plot([], [], '-', color='b', lw=2, label='Capa b')
    punto1, = ax.plot([], [], 'o', color='r')
    punto2, = ax.plot([], [], 'o', color='b')
    ax.legend(loc='upper right')

    def update(k):
        tray1.set_data(th1[:k+1], ph1[:k+1])
        tray2.set_data(th2[:k+1], ph2[:k+1])
        punto1.set_data([th1[k]], [ph1[k]])
        punto2.set_data([th2[k]], [ph2[k]])
        ax.set_title(f'Modo {NOMBRES_MODO[modo]}, t/T = {t_T[k]:.2f}')
        return tray1, tray2, punto1, punto2

    ani = FuncAnimation(fig, update, frames=len(t_T), interval=100, blit=False)
    ani.save(os.path.join(carpeta, f'precesion_{modo}_A{A:g}.gif'), writer='pillow', fps=10)
    plt.close(fig)                                    # el GIF ya quedó guardado


def _graficar_dispersion(carpeta, A, frecuencia, resultado, graficar):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(resultado['campos'], resultado['f_acustico'], 'o--', label='Modo acústico',
            markersize=3)
    ax.plot(resultado['campos'], resultado['f_optico'], 's', label='Modo óptico', markersize=3)
    ax.axhline(frecuencia/1e9, color='red', linestyle='--', linewidth=2,
               label=f'{frecuencia/1e9:g} GHz')
    for modo, marca in (('acustico', 'o'), ('optico', 's')):
        if resultado[modo] is not None:
            ax.plot(resultado[modo]['Hr'], frecuencia/1e9, marca, color='k', markersize=8,
                    mfc='none', mew=2)
    ax.set_xlabel('Campo (Oe)')
    ax.set_ylabel('Frecuencia (GHz)')
    ax.set_title(f'Relación de dispersión, A = {A:g} erg/cm$^2$')
    ax.legend()
    ax.grid(True)
    fig.savefig(os.path.join(carpeta, f'dispersion_A{A:g}.png'), dpi=300, bbox_inches='tight')
    if not graficar:
        plt.close(fig)


if __name__ == '__main__':
    # se ejecuta solo si corrés el archivo directamente, no cuando se importa
    carpeta = r'C:\Disco D\Study\Phd Bariloche\FMR'
    autovectores_bicapa(A=0.4, carpeta=carpeta)
