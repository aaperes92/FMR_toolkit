# `experiment.fit_positive`

Fits every spectrum in a folder measured **from 0 to +H** with the derivative of one
or two Lorentzian lines on a linear background, and collects Hr, linewidth and phase
of each line in a summary table.

Typical use: a frequency series (broadband) or an angular series, one file per
frequency or angle.

```python
from fmrtoolkit.experiment import fit_positive

tabla = fit_positive.ajustar_carpeta("path/to/spectra", n_lineas=2, ventana=300)
```

## `ajustar_carpeta(carpeta, n_lineas=2, ventana=300, graficar=True, extensiones=('.dat', '.txt'))`

### Parameters

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `carpeta` | — | — | Folder with the spectra |
| `n_lineas` | `2` | — | Number of lines per spectrum: `1` or `2` |
| `ventana` | `300` | Oe | Half-width of the field region that belongs to one line. Used to find the initial guess of each line and to hide it while looking for the next one. It should be larger than a linewidth and smaller than the separation between the two lines |
| `graficar` | `True` | — | Show one figure per spectrum (data, total fit, each line, background) |
| `extensiones` | `('.dat', '.txt')` | — | File extensions that are read |

### Model

```
signal(H) = y0 + m·H + Σ_i L'(H; A_i, Hr_i, ΔH_i, φ_i)
```

L' is the field derivative of a Lorentzian mixing absorption and dispersion with the
phase φ (`core.models.lorentziana`). ΔH_i is the FWHM.

- Initial guess: `core.fitting.estimar_p0` (background from the 10 % at each end of the
  spectrum, then the strongest remaining line inside `ventana`).
- Bounds: A > 0, Hr inside the measured range, 0 < ΔH < field range, −π < φ < π.
- **Line 1 is always the line at the highest field.**
- A warning is printed when a line is wider than 30 % of the field range (it is
  probably fitting the background).
- Files where the fit does not converge are skipped with a message.

### Input

See [Conventions → Input spectra](../conventions.md#input-spectra): 4 header lines,
two columns, frequency or angle read from the file name (`sample_9p4GHz.dat` → 9.4).

### Return value

A NumPy array with one row per spectrum, sorted by the first column, with the same
columns as `output_<n>peak.txt`. Returns `None` if no file was fitted.

### Output files (in `carpeta`)

**`output_1peak.txt` / `output_2peak.txt`** — summary table. Columns for `n_lineas=2`:

| Col | Name | Content |
|---|---|---|
| 0 | `Frecuencia` | Frequency (GHz) or angle (deg), from the file name |
| 1 | `Hr1` | Resonance field of line 1 (Oe) |
| 2 | `Ancho de linea1 pico-pico` | Peak-to-peak linewidth of line 1 (Oe) |
| 3 | `Hr2` | Resonance field of line 2 (Oe) |
| 4 | `Ancho de linea2 pico-pico` | Peak-to-peak linewidth of line 2 (Oe) |
| 5–8 | `err_Hr1, err_Ancho1, err_Hr2, err_Ancho2` | Fit uncertainties (1σ) |
| 9–10 | `phi1, phi2` | Phases (rad) |

For `n_lineas=1`: `Frecuencia, Hr1, Ancho de linea1 pico-pico, err_Hr1, err_Ancho1, phi1`.

**`fit_<file>.txt`** — fitted curves of each spectrum on 1000 points:
`H, Voltage` (total fit), `Linea1`, `Linea2` (each line plus background), `Fondo`.

### Next steps

- `output_1peak.txt` of a frequency series → [`broadband.ajustar_banda_ancha`](broadband.md)
- `output_2peak.txt` of an angular series → [`theory.single_layer`](../theory/single_layer.md)
  or [`theory.bilayer`](../theory/bilayer.md)

### Known issues

- In the current version **the function fails with `TypeError`** for both `n_lineas=1`
  and `n_lineas=2`: it was written for a `core.models.lorentziana` with a background
  slope (`y0, m, A, Hr, ΔH, φ`), but `lorentziana` has no slope (`y0, A, Hr, ΔH, φ`).
  `n_lineas=1` fails in the fit and `n_lineas=2` when building the curve of each line.
- The number of header lines (4) is fixed.
- No PDF is saved; figures are only shown when `graficar=True`.
