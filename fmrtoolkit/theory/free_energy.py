"""Términos de energía libre: Zeeman, demagnetizante, anisotropías."""
from sympy import I, Matrix, cos, diff, pi, rad, re, sin

def e_libre_IP_1L(angazimut, angmagn, h, angcamp, espesor, magn, Kc, Ku, beta):
    Elibre = (-h*espesor*magn*(cos(angmagn-angcamp))*(sin(angazimut))
                      + espesor*2*pi.evalf(10)*(magn**2)*(cos(angazimut))**2
                      - 0.25*espesor*Kc*((sin(2*angazimut))**2 + ((sin(2*angmagn))**2)*(sin(angazimut))**4)
                      - Ku*espesor*((sin(angazimut))**2)*((cos(angmagn-beta))**2))
    return Elibre

def e_libre_OP_1L(angazimut, angmagn, h, angcamp, espesor, magn, Kc, Ku, beta):
    Elibre = (-h*espesor*magn*(cos(angmagn-angcamp))*(sin(angazimut))
                      + espesor*2*pi.evalf(10)*(magn**2)*(cos(angazimut))**2
                      - 0.25*espesor*Kc*((sin(2*angazimut))**2 + ((sin(2*angmagn))**2)*(sin(angazimut))**4)
                      - Ku*espesor*((sin(angazimut))**2)*((cos(angmagn-beta))**2))
    return Elibre
