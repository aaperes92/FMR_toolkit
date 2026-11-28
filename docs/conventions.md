# Conventions

Everything here applies to all modules unless a module page says otherwise.

## Language

Function, parameter and variable names are in **Spanish** (`campo` = field,
`frecuencia` = frequency, `ancho` = linewidth, `capa` = layer, `ajustar` = fit,
`graficar` = plot, `carpeta` = folder). The documentation is in English.

## Units

CGS throughout.

| Quantity | Unit | Typical parameter names |
|---|---|---|
| Magnetic field, anisotropy fields, linewidths | Oe | `campo`, `Hr`, `Hu`, `Hc`, `dH`, `h_rf` |
| Magnetisation | emu/cm³ | `magn`, `magn_a`, `magn_b`, `M_eff` |
| Anisotropy constants | erg/cm³ | `Ku`, `Kc` (computed internally) |
| Interlayer coupling | erg/cm² | `A` |
| Thickness | cm | `espesor_a`, `espesor_b` (e.g. 10 nm = `10e-7`) |
| Frequency, **experiment** modules | GHz | first column of the `output_*.txt` files |
| Frequency, **theory** modules | **Hz** | `frecuencia` (e.g. `9.76e9`) |
| Angular frequency (internal) | rad/s | eigenvalues, `BX = 2π·frecuencia` |

Gyromagnetic ratio: γ = 8.794 × 10⁶ · g rad s⁻¹ Oe⁻¹ (written `8794000*g` in the code).
In GHz/Oe: γ/2π = g/714.5.

### Anisotropy fields

The theory functions take **anisotropy fields** and convert them to constants:

| Field | Constant | Energy term (per volume, in-plane) |
|---|---|---|
| `Hu` (uniaxial) | Ku = M·Hu/2 | −Ku sin²θ cos²(φ − φ_u) |
| `Hc` (cubic, 4-fold) | Kc = M·Hc/2 | −(Kc/4) [sin²2θ + sin²2φ sin⁴θ] |

With Kc > 0 the cubic easy axes are at **45°** from the reference direction (φ = 0).
The uniaxial easy axis is at `ang_u`.

The uniaxial term is written as −Ku sin²θ cos²(φ − φ_u). Papers that use
Ku sin²θ sin²φ give values of M_eff that differ by Hu/4π.

## Angles

All angles are given and returned in **degrees** and converted to radians internally.

**Magnetisation** (spherical coordinates):

- `angazimut` = θ, polar angle measured from the film normal (z). θ = 90° means M in the plane.
- `angmagn` = φ, azimuthal angle in the plane.

**Field, in-plane (IP) functions:** `ang_campo` (or the swept field angle) is the
in-plane angle φ_H, measured from the **same reference as `ang_u`** (for example the
substrate MgO[100] direction).

**Field, out-of-plane (OP) functions:** 0° = field in the film plane, 90° = field along
the normal. Internally the film normal is the y axis and the field rotates in the x–y
plane, so the calculation has no singularity when M is perpendicular.

**`defasaje_deg`:** shift applied to the **experimental** angles before plotting them
with the theory: the experimental points are plotted at `angulo_exp − defasaje_deg`.
Use it when the sample was mounted rotated with respect to the reference axis.

## Linewidth

Spectra are fitted with the derivative of a Lorentzian. The fitted width parameter is
the **FWHM** of the absorption line. The **peak-to-peak** width of the derivative is

ΔH_pp = ΔH_FWHM / √3

**Every `output_*.txt` file stores peak-to-peak widths**, and the damping model in
`broadband` assumes peak-to-peak:

ΔH_pp(f) = ΔH₀ + (4π/√3) · α f / γ

## Input spectra

Plain text, whitespace separated, two columns: field (Oe) and signal.

| Module | Header lines skipped | Value read from the file name |
|---|---|---|
| `fit_positive` | 4 (fixed) | Last `_`-separated token, with `GHz` removed and `p` → `.`: `sample_9p4GHz.dat` → 9.4 |
| `fit_bipolar` | `skiprows` (default 1) | Trailing number: `sample_9.4.dat` → 9.4 |

For angular measurements name the files by angle (`sample_000.dat`, `sample_010.dat`, …).
The number is stored in the first column of the output (which is then called
`Frecuencia` but contains the angle).

Files whose names start with `fit_` or `output_` are skipped, so results of a previous
run are never fitted as data.

## Output files

- Plain text, **comma separated**, **one header line** (no `#`). Read them with
  `np.loadtxt(archivo, delimiter=',', skiprows=1)`.
- Experiment modules write into the folder of the input data, and theory functions that
  read an experimental file write into the folder of that file. All of them accept an
  optional `carpeta_salida` to write somewhere else.
- Theory functions that do not read a file write into `carpeta` (the folder must exist).
- File names include some parameters (for example `_A0.4` or `_magn1155`). Running again
  with the same values in the name **overwrites** the previous files.

## Plots

- `graficar=True` opens the figure windows (`plt.show()`).
- `graficar=False` saves the PDF/PNG files without opening windows. Use it in loops and
  from the GUI.
- `figuras=[]` (an empty list): every figure the function creates is appended to that list
  and left open, so it can be shown elsewhere (this is what the GUI does).
