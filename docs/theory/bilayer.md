# `theory.bilayer`

In-plane **angular dependence of the resonance fields** of a coupled bilayer
(layers a and b). For every field angle it computes the resonance field of the two
modes (acoustic and optical) and plots them with an experimental angular series.

```python
from fmrtoolkit.theory.bilayer import variacion_angular_ip_bicapa

ang, Hr_ac, Hr_op, ang_a, ang_b = variacion_angular_ip_bicapa(
    "path/to/output_2peak.txt", A=0.8, frecuencia=24.9e9, col_Hr=[1, 3])
```

## `variacion_angular_ip_bicapa(archivo, magn_a=1682, magn_b=770, espesor_a=2.5e-6, espesor_b=5e-7, Hc_a=150, Hc_b=150, Hu_a=50, Hu_b=50, ang_u=45, g_a=2.088, g_b=2.091, A=0.8, frecuencia=24.9e9, col_angulo=0, col_Hr=1, defasaje_deg=-3, margen_campo=1000, paso_campo=20, ang_inicio=0, ang_fin=180, paso_ang=5, paso_phi_M=2, graficar=True)`

Energy: [`e_libre_IP_2L`](free_energy.md). Matrix: [`matriz_2capas`](smit_beljers.md)
without damping.

### Parameters

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `archivo` | — | — | Experimental angular file (`output_*.txt`) |
| `magn_a`, `magn_b` | `1682`, `770` | emu/cm³ | Magnetisations |
| `espesor_a`, `espesor_b` | `2.5e-6`, `5e-7` | cm | Thicknesses (25 nm and 5 nm) |
| `Hc_a`, `Hc_b` | `150`, `150` | Oe | Cubic anisotropy fields |
| `Hu_a`, `Hu_b` | `50`, `50` | Oe | Uniaxial anisotropy fields |
| `ang_u` | `45` | deg | Uniaxial easy axis (both layers) |
| `g_a`, `g_b` | `2.088`, `2.091` | — | g factors |
| `A` | `0.8` | erg/cm² | Interlayer coupling (A > 0 ferro, A < 0 antiferro) |
| `frecuencia` | `24.9e9` | **Hz** | Measurement frequency |
| `col_angulo` | `0` | — | Column of the angle in `archivo` |
| `col_Hr` | `1` | — | Column, **or list of columns**, of experimental Hr to plot. For `output_2peak.txt` use `[1, 3]` |
| `defasaje_deg` | `-3` | deg | Shift of the experimental angles |
| `margen_campo` | `1000` | Oe | Added below and above the experimental Hr range (the lower limit is never below `paso_campo`) |
| `paso_campo` | `20` | Oe | Field step of the simulation |
| `ang_inicio`, `ang_fin`, `paso_ang` | `0`, `180`, `5` | deg | Field angles that are simulated |
| `paso_phi_M` | `2` | deg | Step of the 2D equilibrium grid (refined afterwards with Nelder–Mead) |
| `graficar` | `True` | — | Show the figure (the PDF is saved anyway) |

### Return value

`(angulos, Hr_ac, Hr_op, ang_eqa, ang_eqb)`

| Output | Unit | Description |
|---|---|---|
| `angulos` | deg | Simulated field angles |
| `Hr_ac` | Oe | Resonance field of the lower-frequency ("acoustic") mode; `nan` if outside the field range |
| `Hr_op` | Oe | Resonance field of the higher-frequency ("optical") mode; `nan` if outside the range |
| `ang_eqa`, `ang_eqb` | deg | Equilibrium angles of each layer at the acoustic resonance (between −90° and 270°) |

A message is printed if no mode resonates in the whole field range.

### Output files (in the folder of `archivo`)

| File | Content |
|---|---|
| `output_angular_IP_bicapa_A<A>_eje<ang_u>.txt` | Columns `anguloH (deg), Hr acustico (Oe), Hr optico (Oe), ang M_a (deg), ang M_b (deg)` |
| `output_angular_IP_bicapa_A<A>_eje<ang_u>.pdf` | Both modes and the experimental points |

## `campo_resonancia(campos, omega, BX)`

Helper shared with [`eigenvectors`](eigenvectors.md): first field where a mode frequency
crosses the measurement frequency, by linear interpolation.

| Parameter | Unit | Description |
|---|---|---|
| `campos` | Oe | Field grid (increasing) |
| `omega` | rad/s | Mode frequency at each field (`nan` allowed) |
| `BX` | rad/s | Measurement angular frequency, 2π·f |

Returns `(Hr, i)`, where `i` is the index of the grid field just below the crossing,
or `(nan, None)` if the frequency is already above `BX` at the first field or never
reaches it.

## Known issues

- Modes are named by frequency order. This is correct for A > 0; for A < 0 the
  lower-frequency mode is the optical one (see the [overview](overview.md)).
- The equilibrium angles are those of the grid field just below the crossing, not
  exactly at Hr.
- The symbolic derivatives are recomputed for every field angle (slow with a fine `paso_ang`).
