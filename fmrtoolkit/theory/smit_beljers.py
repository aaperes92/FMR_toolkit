from sympy import I, Matrix, diff, sin


def matriz_1capa(Elibre, angazimut, angmagn, frec, magn, g, damp=0):
    """Matriz de Smit-Beljers (2x2) de una capa. damp=0 → sin amortiguamiento."""
    gamma = 8794000*g

    E_theta_theta = diff(Elibre, angazimut, angazimut)
    E_phi_phi = diff(Elibre, angmagn, angmagn)
    E_theta_phi = diff(Elibre, angazimut, angmagn)

    sen = sin(angazimut)
    m = Matrix([
        [I*frec/gamma + E_theta_phi/(magn*sen) + damp*E_theta_theta/magn,
         E_phi_phi/(magn*sen**2) + damp*E_theta_phi/(magn*sen)],
        [-E_theta_theta/magn + damp*E_theta_phi/(magn*sen),
         I*frec/gamma - E_theta_phi/(magn*sen) + damp*E_phi_phi/(magn*sen**2)]])
    return m


def matriz_2capas(Elibre, angazimut_a, angmagn_a, angazimut_b, angmagn_b, frec,
                  magn_a, magn_b, espesor_a, espesor_b, g_a, g_b, damp_a=0, damp_b=0):
    """Matriz de Smit-Beljers (4x4) de dos capas acopladas. damp=0 → sin amortiguamiento."""
    gamma_a = 8794000*g_a
    gamma_b = 8794000*g_b

    E_theta_a_theta_a = diff(Elibre, angazimut_a, angazimut_a)
    E_phi_a_phi_a = diff(Elibre, angmagn_a, angmagn_a)
    E_theta_a_phi_a = diff(Elibre, angazimut_a, angmagn_a)
    E_theta_b_theta_b = diff(Elibre, angazimut_b, angazimut_b)
    E_phi_b_phi_b = diff(Elibre, angmagn_b, angmagn_b)
    E_theta_b_phi_b = diff(Elibre, angazimut_b, angmagn_b)
    E_theta_a_theta_b = diff(Elibre, angazimut_a, angazimut_b)
    E_theta_a_phi_b = diff(Elibre, angazimut_a, angmagn_b)
    E_theta_b_phi_a = diff(Elibre, angazimut_b, angmagn_a)
    E_phi_a_phi_b = diff(Elibre, angmagn_a, angmagn_b)

    sen_a = sin(angazimut_a)
    sen_b = sin(angazimut_b)
    tMa = espesor_a*magn_a
    tMb = espesor_b*magn_b
    taMb = espesor_a*magn_b
    tbMa = espesor_b*magn_a

    m = Matrix([
        [I*frec/gamma_a + E_theta_a_phi_a/(tMa*sen_a) + damp_a*E_theta_a_theta_a/tMa,
         E_phi_a_phi_a/(tMa*sen_a**2) + damp_a*E_theta_a_phi_a/(tMa*sen_a),
         E_theta_b_phi_a/(taMb*sen_a) + damp_a*E_theta_a_theta_b/taMb,
         E_phi_a_phi_b/(taMb*sen_a*sen_b) + damp_a*E_theta_a_phi_b/(taMb*sen_b)],

        [-E_theta_a_theta_a/tMa + damp_a*E_theta_a_phi_a/(tMa*sen_a),
         I*frec/gamma_a - E_theta_a_phi_a/(tMa*sen_a) + damp_a*E_phi_a_phi_a/(tMa*sen_a**2),
         -E_theta_a_theta_b/taMb + damp_a*E_theta_b_phi_a/(taMb*sen_a),
         -E_theta_a_phi_b/(taMb*sen_b) + damp_a*E_phi_a_phi_b/(taMb*sen_a*sen_b)],

        [E_theta_a_phi_b/(tbMa*sen_b) + damp_b*E_theta_a_theta_b/tbMa,
         E_phi_a_phi_b/(tbMa*sen_a*sen_b) + damp_b*E_theta_b_phi_a/(tbMa*sen_a),
         I*frec/gamma_b + E_theta_b_phi_b/(tMb*sen_b) + damp_b*E_theta_b_theta_b/tMb,
         E_phi_b_phi_b/(tMb*sen_b**2) + damp_b*E_theta_b_phi_b/(tMb*sen_b)],

        [-E_theta_a_theta_b/tbMa + damp_b*E_theta_a_phi_b/(tbMa*sen_b),
         -E_theta_b_phi_a/(tbMa*sen_a) + damp_b*E_phi_a_phi_b/(tbMa*sen_a*sen_b),
         -E_theta_b_theta_b/tMb + damp_b*E_theta_b_phi_b/(tMb*sen_b),
         I*frec/gamma_b - E_theta_b_phi_b/(tMb*sen_b) + damp_b*E_phi_b_phi_b/(tMb*sen_b**2)]])
    return m