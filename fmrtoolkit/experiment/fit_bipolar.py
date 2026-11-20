
"""Ajuste de espectros FMR con barrido bipolar (-H -> +H): una lorentziana por rama."""

import os
import re

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from fmrtoolkit.core.models import lorentziana


def ajustar_rama(campo, intensidad):

    minimo_idx = np.argmin(intensidad)
    maximo_idx = np.argmax(intensidad)

    H_min = campo[minimo_idx]
    H_max = campo[maximo_idx]

    V_min = intensidad[minimo_idx]
    V_max = intensidad[maximo_idx]

    Res_field = (H_max + H_min) / 2

    Linewidth = abs(H_max - H_min)

    if Linewidth == 0:
        Linewidth = 10

    Amplit = 1.209199 * abs(V_max - V_min) * Linewidth**2

    popt, pcov = curve_fit(
        lorentziana,
        campo,
        intensidad,
        p0=[
            np.mean(intensidad),
            Amplit,
            Res_field,
            Linewidth,
            0
        ],
        maxfev=100000
    )

    return popt, Res_field, Linewidth


def ajustar_carpeta(carpeta, graficar=True, extensiones=('.dat', '.txt'), skiprows=1):

    Frecuencia = []

    Hr_pos = []
    Ancho_pos = []

    Hr_neg = []
    Ancho_neg = []

    for archivo in os.listdir(carpeta):

        if not archivo.lower().endswith(extensiones):
            continue
        if archivo.startswith(('fit_', 'output_')):   # resultados de corridas anteriores, no son datos
            continue

        ruta = os.path.join(carpeta, archivo)
        nombre_sin_extension = os.path.splitext(archivo)[0]

        columna = np.loadtxt(
            ruta,
            delimiter=None,
            skiprows=skiprows
        )

        if columna.ndim == 1:
            columna = columna.reshape(1, -1)

        campo = columna[:, 0]
        intensidad = columna[:, 1]

        # ==================================================
        # Separar campo negativo y positivo
        # ==================================================

        mascara_neg = campo < 0
        mascara_pos = campo > 0

        if mascara_neg.sum() < 5 or mascara_pos.sum() < 5:
            print(f'{archivo}: no tiene datos suficientes en ambas ramas '
                  f'(¿es un barrido solo positivo?). Se saltea.')
            continue

        campo_neg = campo[mascara_neg]
        intensidad_neg = intensidad[mascara_neg]

        campo_pos = campo[mascara_pos]
        intensidad_pos = intensidad[mascara_pos]

        # ==================================================
        # AJUSTE DE AMBAS RAMAS
        # ==================================================

        try:
            popt_neg, Res_neg, Linewidth_neg = ajustar_rama(campo_neg, intensidad_neg)
            popt_pos, Res_pos, Linewidth_pos = ajustar_rama(campo_pos, intensidad_pos)
        except (RuntimeError, ValueError) as error:
            print(f'{archivo}: el ajuste no convergió ({error}). Se saltea.')
            continue

        y0_neg, Amp_neg, Hr_fit_neg, ancho_fit_neg, phi_fit_neg = popt_neg
        y0_pos, Amp_pos, Hr_fit_pos, ancho_fit_pos, phi_fit_pos = popt_pos

        print("\n----------------------------------")
        print(archivo)

        print("\nCAMPO NEGATIVO")
        print("Hr =", Hr_fit_neg, "Oe")
        print("Ancho =", abs(ancho_fit_neg), "Oe")
        print("phi =", phi_fit_neg)

        print("\nCAMPO POSITIVO")
        print("Hr =", Hr_fit_pos, "Oe")
        print("Ancho =", abs(ancho_fit_pos), "Oe")
        print("phi =", phi_fit_pos)

        # ==================================================
        # Curvas ajustadas
        # ==================================================

        campo_fit_neg = np.linspace(np.min(campo_neg), np.max(campo_neg), 500)
        intensidad_fit_neg = lorentziana(campo_fit_neg, *popt_neg)

        campo_fit_pos = np.linspace(np.min(campo_pos), np.max(campo_pos), 500)
        intensidad_fit_pos = lorentziana(campo_fit_pos, *popt_pos)

        # ==================================================
        # GRAFICA (el PDF se guarda siempre; la ventana solo si graficar=True)
        # ==================================================

        plt.figure(figsize=(7, 5))

        plt.plot(campo, intensidad, 'o', label='Data', markersize=4)
        plt.plot(campo_fit_neg, intensidad_fit_neg, '-', linewidth=2, label='Negative field fit')
        plt.plot(campo_fit_pos, intensidad_fit_pos, '-', linewidth=2, label='Positive field fit')

        plt.xlabel(r'$H_{\mathrm{ext}}$ (Oe)')
        plt.ylabel(r'Intensity ($\mu\mathrm{V}$)')
        plt.title(f'Fit for {nombre_sin_extension}')
        plt.legend()
        plt.grid(True)

        ruta_pdf = os.path.join(carpeta, f'{nombre_sin_extension}_fit.pdf')
        plt.savefig(ruta_pdf, format='pdf', bbox_inches='tight')

        if graficar:
            plt.show()
        else:
            plt.close()

        # ==================================================
        # GUARDAR RESULTADOS
        # ==================================================

        Hr_neg.append(Hr_fit_neg)
        Ancho_neg.append(abs(ancho_fit_neg)/ np.sqrt(3))

        Hr_pos.append(Hr_fit_pos)
        Ancho_pos.append(abs(ancho_fit_pos)/ np.sqrt(3))

        match = re.search(r'(\d+(?:\.\d+)?)$', nombre_sin_extension)

        if match:
            Frecuencia.append(float(match.group(1)))
        else:
            print(f"No se encontró frecuencia en: {archivo}")
            Frecuencia.append(np.nan)

    if not Frecuencia:
        print('No se ajustó ningún archivo.')
        return None

    # ==================================================
    # GUARDAR TODOS LOS PARAMETROS
    # ==================================================

    Hr_neg = np.array(Hr_neg)
    Hr_pos = np.array(Hr_pos)

    Hr_medio = (Hr_pos - Hr_neg) / 2          # Hr_neg es negativo
    Desplazamiento = (Hr_pos + Hr_neg) / 2    # offset del campo o exchange bias

    data = np.column_stack((
        Frecuencia,
        Hr_neg,
        Ancho_neg,
        Hr_pos,
        Ancho_pos,
        Hr_medio,
        Desplazamiento
    ))

    data = data[data[:, 0].argsort()]

    output_file = os.path.join(carpeta, 'output_bipolar.txt')

    np.savetxt(
        output_file,
        data,
        delimiter=',',
        header='Frecuencia,Hr_negativo,Ancho_negativo peak-peak,Hr_positivo,Ancho_positivo peak-peak,Hr_medio,Desplazamiento',
        comments=''
    )

    return data


if __name__ == '__main__':
    # se ejecuta solo si corrés el archivo directamente, no cuando se importa
    ajustar_carpeta(os.path.dirname(os.path.realpath(__file__)))
