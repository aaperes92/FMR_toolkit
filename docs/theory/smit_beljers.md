# `theory.smit_beljers`

Matrices of the linearised Landau–Lifshitz–Gilbert equations (Smit–Beljers), built
from the second derivatives of a [free energy](free_energy.md). They are the common
core of `single_layer`, `bilayer`, `dispersion` and `eigenvectors`.

## `matriz_1capa(Elibre, angazimut, angmagn, frec, magn, g, damp=0)`

2 × 2 matrix of a single layer.

| Parameter | Unit | Description |
|---|---|---|
| `Elibre` | erg/cm³ | Free energy **per volume** (SymPy expression) |
| `angazimut`, `angmagn` | symbols | θ and φ of M, the symbols used in `Elibre` |
| `frec` | symbol | Angular frequency ω (rad/s) |
| `magn` | emu/cm³ | Magnetisation |
| `g` | — | g factor (γ = 8.794×10⁶·g) |
| `damp` | — | Damping α. `0` gives the undamped matrix |

Variables of the linear system: **(M·δθ, M·sinθ·δφ)**.

## `matriz_2capas(Elibre, angazimut_a, angmagn_a, angazimut_b, angmagn_b, frec, magn_a, magn_b, espesor_a, espesor_b, g_a, g_b, damp_a=0, damp_b=0)`

4 × 4 matrix of two coupled layers.

| Parameter | Unit | Description |
|---|---|---|
| `Elibre` | erg/cm² | Free energy **per area** (SymPy expression, e.g. `e_libre_IP_2L`) |
| `angazimut_a`, `angmagn_a`, `angazimut_b`, `angmagn_b` | symbols | θ and φ of each layer |
| `frec` | symbol | Angular frequency ω (rad/s) |
| `magn_a`, `magn_b` | emu/cm³ | Magnetisations |
| `espesor_a`, `espesor_b` | cm | Thicknesses |
| `g_a`, `g_b` | — | g factors |
| `damp_a`, `damp_b` | — | Damping of each layer. `0` gives the undamped matrix |

Variables: **(M_a·δθ_a, M_a·sinθ_a·δφ_a, M_b·δθ_b, M_b·sinθ_b·δφ_b)**. The rows of
layer i are divided by t_i·M_i.

## Return value

A SymPy `Matrix` `m` that is **linear in `frec`**: m = frec·C + K.

## How it is used

**Mode frequencies** (undamped matrix): det(m) = 0 is equivalent to frec being an
eigenvalue of −C⁻¹K, which is much faster than solving the determinant.

```python
m = matriz_1capa(Elibre, angazimut, angmagn, frec, magn, g, damp=0)
C_inv = np.linalg.inv(np.array(m.diff(frec).evalf(), dtype=complex))
K_num = lambdify((angmagn, angazimut, h), m.subs(frec, 0), 'numpy')

raices = np.linalg.eigvals(-C_inv @ np.array(K_num(phi_eq, np.pi/2, H), dtype=complex))
omega = raices.real[raices.real > 0]          # rad/s; f = omega / 2π
```

**Forced response** (damped matrix, see [`eigenvectors`](eigenvectors.md)): solve
m(ω)·v = −d, where d is the microwave-field term (M·h_rf in the δφ rows).

## Notes

- Damping enters in Landau–Lifshitz form. It shifts the frequencies by a term of order
  α² (negligible for α ~ 10⁻³), and the imaginary part of the eigenvalue gives the
  linewidth.
- Checks: with no anisotropy the single-layer matrix gives the Kittel frequency; with
  A = 0 the bilayer matrix gives the two layers separately.
