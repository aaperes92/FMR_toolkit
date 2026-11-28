# `experiment.fit_bipolar`

Fits every spectrum in a folder measured **from −H to +H**. Each field branch
(H < 0 and H > 0) is fitted with one Lorentzian-derivative line. From the two
resonance fields it obtains the average Hr and the field offset (for example, from
exchange bias or a remanent field in the magnet).

```python
from fmrtoolkit.experiment import fit_bipolar

tabla = fit_bipolar.ajustar_carpeta("path/to/spectra")
```

## `ajustar_carpeta(carpeta, graficar=True, extensiones=('.dat', '.txt'), skiprows=1, carpeta_salida=None, figuras=None)`

### Parameters

| Parameter | Default | Description |
|---|---|---|
| `carpeta` | — | Folder with the spectra |
| `graficar` | `True` | Show the figure of each spectrum (the PDF is saved anyway) |
| `extensiones` | `('.dat', '.txt')` | File extensions that are read |
| `skiprows` | `1` | Header lines to skip in each spectrum |
| `carpeta_salida` | `None` | Folder for the PDFs and `output_bipolar.txt`. `None` writes them into `carpeta`, as before |
| `figuras` | `None` | Optional list. If given, the figure of each spectrum is appended to it and not closed. `None` keeps the previous behaviour |

### Procedure

1. Split the spectrum into H < 0 and H > 0. Files with fewer than 5 points in either
   branch are skipped (probably a positive-only sweep: use [`fit_positive`](fit_positive.md)).
2. Fit each branch with [`ajustar_rama`](#ajustar_ramacampo-intensidad).
3. Compute, for each file,
   - `Hr_medio = (Hr_pos − Hr_neg)/2`
   - `Desplazamiento = (Hr_pos + Hr_neg)/2` (offset; 0 for a symmetric spectrum)

### Input

Two columns (field in Oe, signal), `skiprows` header lines. The frequency is the
**trailing number** of the file name: `sample_9.4.dat` → 9.4. Names like
`sample_9p4GHz.dat` are **not** recognised (the frequency is stored as `nan` and a
message is printed). See [Conventions](../conventions.md#input-spectra).

### Return value

A NumPy array with the columns of `output_bipolar.txt`, sorted by frequency, or `None`
if no file was fitted.

### Output files (in `carpeta`, or in `carpeta_salida` if given)

**`output_bipolar.txt`**

| Col | Name | Content |
|---|---|---|
| 0 | `Frecuencia` | From the file name (GHz) |
| 1 | `Hr_negativo` | Resonance field of the negative branch (Oe, negative) |
| 2 | `Ancho_negativo peak-peak` | Peak-to-peak linewidth, negative branch (Oe) |
| 3 | `Hr_positivo` | Resonance field of the positive branch (Oe) |
| 4 | `Ancho_positivo peak-peak` | Peak-to-peak linewidth, positive branch (Oe) |
| 5 | `Hr_medio` | (Hr_pos − Hr_neg)/2 (Oe) |
| 6 | `Desplazamiento` | (Hr_pos + Hr_neg)/2 (Oe) |

**`<file>_fit.pdf`** — data and the fit of each branch.

For the broadband analysis use `col_Hr=5` (`Hr_medio`) and `col_ancho=2` or `4`.

## `ajustar_rama(campo, intensidad)`

Fits one branch with one line (constant background, no slope).

| Parameter | Description |
|---|---|
| `campo` | Field values of the branch (Oe) |
| `intensidad` | Signal values |

Initial guess: Hr at the midpoint between the maximum and the minimum of the signal,
width = their distance, phase 0.

Returns `(popt, Hr_inicial, ancho_inicial)`, where `popt = [y0, A, Hr, ΔH_FWHM, φ]`
are the fitted parameters of `core.models.lorentziana`, and the other two values are
the initial estimates.

### Known issues

- No uncertainties are stored in the output (only printed values are available).
- The fit has no bounds; the width is taken as `abs(ΔH)`.
