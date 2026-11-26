"""Términos de energía libre: Zeeman, demagnetizante, anisotropías."""
from sympy import cos, pi, sin

def e_libre_IP_1L(angazimut, angmagn, h, angcamp, magn, Kc, Ku, beta):
    Elibre = (-h*magn*(cos(angmagn-angcamp))*(sin(angazimut))
                      + 2*pi.evalf(10)*(magn**2)*(cos(angazimut))**2
                      - 0.25*Kc*((sin(2*angazimut))**2 + ((sin(2*angmagn))**2)*(sin(angazimut))**4)
                      - Ku*((sin(angazimut))**2)*((cos(angmagn-beta))**2))
    return Elibre

def e_libre_OP_1L(angazimut, angmagn, h, angcamp, magn):
    Elibre = (-h*magn*cos(angmagn-angcamp)*sin(angazimut)
           +2*pi.evalf(10)*(magn**2)*(sin(angmagn)**2)*sin(angazimut)**2)    
    return Elibre

def e_libre_IP_2L(angazimut_a, angmagn_a, angazimut_b, angmagn_b, h, angcamp, magn_a, magn_b, Kc_a, Kc_b, Ku_a, Ku_b, beta, A, espesor_a, espesor_b):
    Elibre = (-h*espesor_a*magn_a*(cos(angmagn_a-angcamp))*(sin(angazimut_a)) - h*espesor_b*magn_b*(cos(angmagn_b-angcamp))*(sin(angazimut_b))
    +(espesor_a)*2*pi.evalf(10)*(magn_a**2)*(cos(angazimut_a))**2 + (espesor_b)*2*pi.evalf(10)*(magn_b**2)*(cos(angazimut_b))**2
    -0.25*espesor_a*Kc_a*((sin(2*angazimut_a))**2 + ((sin(2*angmagn_a))**2)*(sin(angazimut_a))**4)
    -0.25*espesor_b*Kc_b*((sin(2*angazimut_b))**2 + ((sin(2*angmagn_b))**2)*(sin(angazimut_b))**4)
    -Ku_a*espesor_a*((sin(angazimut_a))**2)*((cos(angmagn_a-beta))**2)-Ku_b*espesor_b*((sin(angazimut_b))**2)*((cos(angmagn_b-beta))**2)
    -A*(cos(angazimut_a)*cos(angazimut_b)+sin(angazimut_a)*sin(angazimut_b)*cos(angmagn_a-angmagn_b)))   
    return Elibre
