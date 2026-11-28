# `theory.single_layer`

Theoretical **angular dependence of the resonance field** Hr of a single layer, by
Smit–Beljers, compared with an experimental angular series (for example
`output_2peak.txt` from [`fit_positive`](../experiment/fit_positive.md)).

The experimental file is used to set the field range of the simulation and is
plotted with the theory. The parameters are **not fitted**: they are chosen by hand.

```python
from fmrtoolkit.theory.single_layer import variacion_angular_ip

angulos, Hr = variacion_angular_ip("path/to/output_2peak.txt",
                                   Hu=20, Hc=175, magn=1155, ang_u=45,
                                   g=2.09, frecuencia=23.9e9, defasaje_deg=12)
```

## `variacion_angular_ip(archivo, Hu=20, Hc=175, magn=1155, ang_u=45, g=2.09, frecuencia=23.9e9, col_angulo=0, col_Hr=1, defasaje_deg=12, margen_campo=400, paso_campo=20, ang_inicio=0, ang_fin=185, paso_ang=5, paso_phi_M=0.5, graficar=True, carpeta_salida=None, figuras=None)`

Field rotating **in the plane**. Energy: [`e_libre_IP_1L`](free_energy.md)
(Zeeman, shape, uniaxial and cubic).

### Parameters

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `archivo` | — | — | Experimental angular file (`output_*.txt`) |
| `Hu`, `Hc` | `20`, `175` | Oe | Uniaxial and cubic anisotropy fields |
| `magn` | `1155` | emu/cm³ | Magnetisation |
| `ang_u` | `45` | deg | Direction of the uniaxial easy axis |
| `g` | `2.09` | — | g factor |
| `frecuencia` | `23.9e9` | **Hz** | Measurement frequency |
| `col_angulo` | `0` | — | Column of the angle in `archivo` |
| `col_Hr` | `1` | — | Column of the experimental Hr that is plotted |
| `defasaje_deg` | `12` | deg | Shift of the experimental angles (plotted at `angle − defasaje_deg`) |
| `margen_campo` | `400` | Oe | Added below and above the experimental Hr range |
| `paso_campo` | `20` | Oe | Field step of the simulation (accuracy of the interpolated Hr) |
| `ang_inicio`, `ang_fin`, `paso_ang` | `0`, `185`, `5` | deg | Field angles that are simulated (`ang_fin` included) |
| `paso_phi_M` | `0.5` | deg | Grid step for the equilibrium angle of M (full turn, no refinement) |
| `graficar` | `True` | — | Show the figure (the PDF is saved anyway) |
| `carpeta_salida` | `None` | — | Folder for the output files. `None` writes them into the folder of `archivo`, as before |
| `figuras` | `None` | — | Optional list. If given, every figure the function creates is appended to it and **not closed**, even with `graficar=False` (used by the GUI to show the plots). `None` keeps the previous behaviour |

The function also prints the experimental spread of Hr (max − min), as a hint for `Hc`.

### Return value

`(angulo_IP, Hr)`: field angles (deg) and theoretical resonance fields (Oe), as arrays.

### Output files (in the folder of `archivo`, or in `carpeta_salida` if given)

| File | Content |
|---|---|
| `output_angular_IP_teoria_magn<magn>_eje<ang_u>.txt` | Columns `Angulo,Hr` |
| `output_angular_IP_teoria_magn<magn>_eje<ang_u>.pdf` | Theory and experiment |

## `variacion_angular_op(archivo, magn=785, g=2.11, frecuencia=9.78e9, col_angulo=0, col_Hr=1, defasaje_deg=-3, margen_campo=90, paso_campo=80, ang_inicio=0, ang_fin=180, paso_ang=5, paso_phi_M=0.05, graficar=True, carpeta_salida=None, figuras=None)`

Field rotating **out of plane**, for a single layer without in-plane anisotropy
(for example permalloy). Energy: [`e_libre_OP_1L`](free_energy.md).
Angle of the field: **0° = in the film plane, 90° = along the normal**.

### Parameters

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `archivo` | — | — | Experimental OP angular file |
| `magn` | `785` | emu/cm³ | **Effective** magnetisation M_eff |
| `g` | `2.11` | — | g factor |
| `frecuencia` | `9.78e9` | **Hz** | Measurement frequency |
| `col_angulo`, `col_Hr` | `0`, `1` | — | Columns of angle and Hr in `archivo` |
| `defasaje_deg` | `-3` | deg | Shift of the experimental angles |
| `margen_campo` | `90` | Oe | Added below and above the experimental Hr range. **Must be larger than `paso_campo`** |
| `paso_campo` | `80` | Oe | Field step of the simulation |
| `ang_inicio`, `ang_fin`, `paso_ang` | `0`, `180`, `5` | deg | Field angles that are simulated |
| `paso_phi_M` | `0.05` | deg | Grid step for the angle of M (grid from 0 to 185°) |
| `graficar` | `True` | — | Show the figure |
| `carpeta_salida`, `figuras` | `None` | — | As in `variacion_angular_ip` |

The function prints a suggested M_eff from the perpendicular resonance,
M = (Hr_max − ω/γ)/4π, useful as a starting value.

### Return value

`(angulo_OP, ang_eq, Hr)`: field angle (deg), equilibrium angle of M from the plane
(deg), resonance field (Oe).

### Output files (in the folder of `archivo`, or in `carpeta_salida` if given)

| File | Content |
|---|---|
| `output_angular_OP_teoria_magn<magn>.txt` | Columns `anguloH,anguloM,Hr` |
| `output_angular_OP_teoria_magn<magn>.pdf` | Theory and experiment |

## Errors

Both functions raise `ValueError` and stop if, at some field angle, the resonance is
below the first simulated field or above the last one. The message says which angle
and suggests increasing `margen_campo`.

## Known issues

- Hr comes from linear interpolation on the field grid: its accuracy depends on
  `paso_campo`.
- The symbolic derivatives are recomputed for every field angle, which makes the
  functions slow with a fine `paso_ang`.
