# `theory.dispersion`

Theoretical **dispersion relations**: mode frequency vs field magnitude, for a fixed
in-plane field angle. One function for a single layer and one for a coupled bilayer.
No experimental file is needed.

```python
from fmrtoolkit.theory.dispersion import dispersion_1capa, dispersion_2capas

campos, f, ang = dispersion_1capa(magn=1300, Hc=250, carpeta="results")
campos, f1, f2, ang_a, ang_b = dispersion_2capas(A=0.08, carpeta="results")
```

## `dispersion_1capa(magn=1300, g=2.015, damp=0.0026, Hc=250, Hu=0, ang_u=45, ang_campo=0, campo_min=5, campo_max=4000, paso_campo=50, paso_phi_M=0.01, carpeta='.', graficar=True)`

Energy: [`e_libre_IP_1L`](free_energy.md). Matrix: [`matriz_1capa`](smit_beljers.md).

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `magn` | `1300` | emu/cm³ | Magnetisation |
| `g` | `2.015` | — | g factor |
| `damp` | `0.0026` | — | Damping, included in the matrix (shifts f only by ~α²) |
| `Hc`, `Hu` | `250`, `0` | Oe | Cubic and uniaxial anisotropy fields |
| `ang_u` | `45` | deg | Uniaxial easy axis |
| `ang_campo` | `0` | deg | In-plane field angle |
| `campo_min`, `campo_max`, `paso_campo` | `5`, `4000`, `50` | Oe | Fields that are computed (`campo_max` excluded) |
| `paso_phi_M` | `0.01` | deg | Grid step of the equilibrium angle (full turn, no refinement) |
| `carpeta` | `'.'` | — | Output folder |
| `graficar` | `True` | — | Show the figure |

**Returns** `(campos, freq, ang_eq)`: fields (Oe), frequency of the mode (**GHz**, `nan`
if there is no positive eigenvalue) and equilibrium angle of M (deg).

**Files** (in `carpeta`): `Dispersion_1capa_magn<magn>_<ang_campo>deg.txt`, columns
`Field (Oe), Frequency (GHz), angulo magnetizacion (deg)`, and the `.pdf` with the same name.

## `dispersion_2capas(magn_a=1300, magn_b=770, g_a=2.015, g_b=2.011, damp_a=0.0026, damp_b=0.006, Hc_a=250, Hc_b=250, Hu_a=0, Hu_b=0, ang_u=45, espesor_a=1e-6, espesor_b=1e-6, A=0.08, ang_campo=0, campo_min=5, campo_max=4000, paso_campo=50, paso_phi_M=2, carpeta='.', graficar=True)`

Energy: [`e_libre_IP_2L`](free_energy.md). Matrix: [`matriz_2capas`](smit_beljers.md).

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `magn_a`, `magn_b` | `1300`, `770` | emu/cm³ | Magnetisations |
| `g_a`, `g_b` | `2.015`, `2.011` | — | g factors |
| `damp_a`, `damp_b` | `0.0026`, `0.006` | — | Damping of each layer, included in the matrix |
| `Hc_a`, `Hc_b`, `Hu_a`, `Hu_b` | `250`, `250`, `0`, `0` | Oe | Anisotropy fields |
| `ang_u` | `45` | deg | Uniaxial easy axis |
| `espesor_a`, `espesor_b` | `1e-6`, `1e-6` | cm | Thicknesses (10 nm) |
| `A` | `0.08` | erg/cm² | Interlayer coupling |
| `ang_campo` | `0` | deg | In-plane field angle |
| `campo_min`, `campo_max`, `paso_campo` | `5`, `4000`, `50` | Oe | Fields that are computed |
| `paso_phi_M` | `2` | deg | Step of the 2D equilibrium grid (refined with Nelder–Mead) |
| `carpeta` | `'.'` | — | Output folder |
| `graficar` | `True` | — | Show the figure |

**Returns** `(campos, freq1, freq2, ang_a_eq, ang_b_eq)`: fields (Oe), lower and higher
mode frequency (**GHz**, f1 < f2, `nan` if a mode is missing) and equilibrium angles of
each layer (deg, 0–360).

**Files** (in `carpeta`): `Dispersion_2capas_A<A>_<ang_campo>deg.txt`, columns
`Field (Oe), Frequency1 (GHz), Frequency2 (GHz), angulo magnetizacion capa A (deg),
angulo magnetizacion capa B (deg)`, and the `.pdf` with the same name.

## Notes

- `freq1` / `freq2` are the low and high frequency modes. With A > 0 they are the
  acoustic and optical modes; with A < 0 the order is inverted.
- To also get the eigenvectors and the precession at resonance, use
  [`eigenvectors`](eigenvectors.md), which computes the same dispersion internally.
- The example in the `if __name__ == '__main__':` block of `dispersion.py` calls
  `dispersion_2capas(A=80, ...)`, a leftover from the old convention (A/100). With the
  current energy it means 80 erg/cm².
