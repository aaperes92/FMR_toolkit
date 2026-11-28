# `theory.free_energy`

Free energy densities as **SymPy expressions**. They are the input of the
[Smit–Beljers matrices](smit_beljers.md) and of the equilibrium search. The angles
of M and the field are passed as SymPy symbols; material parameters are numbers.

See [Conventions](../conventions.md) for angle definitions and anisotropy fields.

## `e_libre_IP_1L(angazimut, angmagn, h, angcamp, magn, Kc, Ku, beta)`

Single layer, field in the plane. **Energy per unit volume** (erg/cm³):

```
E = − h·M·cos(φ − φ_H)·sinθ                          Zeeman
    + 2πM²·cos²θ                                      demagnetising (shape)
    − (Kc/4)·[sin²2θ + sin²2φ·sin⁴θ]                  cubic, easy axes at 45°
    − Ku·sin²θ·cos²(φ − β)                            uniaxial, easy axis at β
```

| Parameter | Unit | Description |
|---|---|---|
| `angazimut` | rad (symbol) | θ, polar angle of M from the normal |
| `angmagn` | rad (symbol) | φ, in-plane angle of M |
| `h` | Oe (symbol or number) | Field magnitude |
| `angcamp` | rad | φ_H, in-plane angle of the field |
| `magn` | emu/cm³ | Magnetisation M |
| `Kc` | erg/cm³ | Cubic constant (= M·Hc/2) |
| `Ku` | erg/cm³ | Uniaxial constant (= M·Hu/2) |
| `beta` | rad | Direction of the uniaxial easy axis |

## `e_libre_OP_1L(angazimut, angmagn, h, angcamp, magn)`

Single layer, field rotating **out of plane**. The film normal is the **y** axis and the
field and M rotate in the x–y plane (θ = 90°), so there is no singularity at the normal.
Only Zeeman and shape anisotropy; `magn` acts as the effective magnetisation M_eff.

```
E = − h·M·cos(φ − φ_H)·sinθ + 2πM²·sin²φ·sin²θ
```

`angcamp` is the field angle from the film plane (0 = in plane, π/2 = along the normal).

## `e_libre_IP_2L(angazimut_a, angmagn_a, angazimut_b, angmagn_b, h, angcamp, magn_a, magn_b, Kc_a, Kc_b, Ku_a, Ku_b, beta, A, espesor_a, espesor_b)`

Two coupled layers a and b, field in the plane. **Energy per unit area** (erg/cm²):
each single-layer term is multiplied by the thickness of its layer, plus the
bilinear interlayer coupling

```
E_coupling = − A·(cosθ_a cosθ_b + sinθ_a sinθ_b cos(φ_a − φ_b))   = − A·(m_a · m_b)
```

| Parameter | Unit | Description |
|---|---|---|
| `angazimut_a`, `angmagn_a` | rad (symbols) | θ and φ of layer a |
| `angazimut_b`, `angmagn_b` | rad (symbols) | θ and φ of layer b |
| `h`, `angcamp` | Oe, rad | Field magnitude and in-plane angle |
| `magn_a`, `magn_b` | emu/cm³ | Magnetisations |
| `Kc_a`, `Kc_b`, `Ku_a`, `Ku_b` | erg/cm³ | Anisotropy constants of each layer |
| `beta` | rad | Uniaxial easy axis (same for both layers) |
| `A` | erg/cm² | Interlayer coupling. **A > 0 ferromagnetic, A < 0 antiferromagnetic** |
| `espesor_a`, `espesor_b` | cm | Thicknesses |

## Return value

A SymPy expression. Typical use:

```python
from sympy import symbols, lambdify
from fmrtoolkit.theory.free_energy import e_libre_IP_1L

h, phi, theta = symbols('h, angmagn, angazimut')
E = e_libre_IP_1L(theta, phi, h, 0.0, 1155, 1155*175/2, 1155*20/2, 0.785)
E_num = lambdify((phi, theta, h), E, 'numpy')     # numerical function for the minimisation
```

## Notes

- The single-layer energy is per volume and the bilayer energy per area. The
  [Smit–Beljers matrices](smit_beljers.md) are normalised accordingly (by M, or by t·M).
- There is no out-of-plane energy for bilayers and no biquadratic coupling yet.
