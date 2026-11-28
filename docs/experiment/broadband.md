# `experiment.broadband`

Broadband FMR analysis. From the resonance fields and linewidths measured at several
frequencies (the output of [`fit_positive`](fit_positive.md) or
[`fit_bipolar`](fit_bipolar.md)) it obtains:

1. **g, M_eff** (and optionally H_u) from a Kittel fit of f(Hr);
2. **damping α and ΔH₀** from a linear fit of ΔH(f), with g fixed to the Kittel value.

```python
from fmrtoolkit.experiment.broadband import ajustar_banda_ancha

res = ajustar_banda_ancha("path/to/spectra/output_1peak.txt",
                          g_limites=(2.0, 2.2), H_uniaxial=0.0, eje_facil=True)
print(res["g"], res["M_eff"], res["damping"])     # each entry is (value, error)
```

## `ajustar_banda_ancha(archivo, col_Hr=1, col_ancho=2, eje_facil=True, ajustar_Hu=False, H_uniaxial=0.0, H_cubico=0.0, g_limites=(2.0, 2.2), graficar=True, carpeta_salida=None, figuras=None)`

### Parameters

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `archivo` | — | — | `output_*.txt` from `fit_positive` or `fit_bipolar`. Column 0 must be the frequency in **GHz** |
| `col_Hr` | `1` | — | Column with Hr. For `output_bipolar.txt` use `5` (`Hr_medio`) |
| `col_ancho` | `2` | — | Column with the **peak-to-peak** linewidth |
| `eje_facil` | `True` | — | Field along an easy axis (`True`) or a hard axis (`False`); selects the Kittel formula |
| `ajustar_Hu` | `False` | — | `True`: fit H_uniaxial. `False`: keep it fixed at `H_uniaxial` |
| `H_uniaxial` | `0.0` | Oe | Uniaxial anisotropy field (fixed value, or ignored if `ajustar_Hu=True`) |
| `H_cubico` | `0.0` | Oe | Cubic anisotropy field, always fixed |
| `g_limites` | `(2.0, 2.2)` | — | Allowed range for g |
| `graficar` | `True` | — | Show the figures (the PDFs are saved anyway) |
| `carpeta_salida` | `None` | — | Folder for the output files. `None` writes them into the folder of `archivo`, as before |
| `figuras` | `None` | — | Optional list. If given, every figure the function creates is appended to it and **not closed**, even with `graficar=False` (used by the GUI to show the plots). `None` keeps the previous behaviour |

Rows with `nan` in the frequency, Hr or linewidth are discarded.

### Models

Kittel, field in plane (`core.models.kittel`, f in GHz):

- easy axis: f = (g/714.5) √[(H + Hu + Hc)(H + Hu + Hc + 4πM_eff)]
- hard axis: f = (g/714.5) √[(H − Hu − Hc)(H + Hc/2 + 4πM_eff)]

Along an easy axis only the sum Hu + Hc can be determined, so `H_cubico` is fixed.

Linewidth (`core.models.ancho_de_linea`, peak-to-peak):

ΔH_pp(f) = ΔH₀ + (4π/√3) · α f / γ,   γ = 8.794×10⁶ g

Initial guesses come from `core.fitting.estimar_p0_kittel` (a quadratic fit of f² vs H)
and `core.fitting.estimar_p0_ancho` (a straight line).

### Return value

A dictionary; each entry is a tuple `(value, error)`:

| Key | Unit |
|---|---|
| `'g'` | — |
| `'M_eff'` | emu/cm³ |
| `'H_uniaxial'` | Oe (error 0 if fixed) |
| `'H_cubico'` | Oe (always fixed, error 0) |
| `'delta_H0'` | Oe |
| `'damping'` | — |

A warning is printed if g ends at one of the limits of `g_limites` (the fit is forced
and its error is not reliable).

### Output files (in the folder of `archivo`, or in `carpeta_salida` if given)

| File | Content |
|---|---|
| `output_broadband.txt` | Columns `parametro,valor,error`, one row per key of the dictionary |
| `kittel_fit.pdf` | f vs Hr, data and Kittel fit |
| `damping_fit.pdf` | ΔH vs f, data and linear fit |

### Known issues

- The hard-axis Kittel formula in `core.models.kittel` is marked in the code as
  pending revision (`# CORREGIR ESTO NUEVAMENTE`). Check it before using `eje_facil=False`.
- The file names are fixed: a second analysis in the same folder overwrites the first.
