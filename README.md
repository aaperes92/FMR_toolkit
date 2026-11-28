# fmr-toolkit

Python tools for analysing and modelling **ferromagnetic resonance (FMR)** data: lineshape fitting of individual spectra, broadband analysis (Kittel and Gilbert damping), and theoretical calculations for single layers and coupled bilayers (angular dependence of the resonance field, dispersion relations and precession of the magnetisation).

The toolkit grew out of the analysis codes written during a PhD on magnetic thin films. It is shared so that others can reuse it, check it and extend it.

---

## Features

| Module | What it does | Status | Docs |
|---|---|---|---|
| `experiment.fit_positive` | Fits spectra measured from 0 to +H with 1 or 2 Lorentzian-derivative lines → Hr, linewidth, phase | Available | [docs](docs/experiment/fit_positive.md) |
| `experiment.fit_bipolar` | Fits spectra measured from −H to +H, one line per branch → Hr, linewidth, field offset | Available | [docs](docs/experiment/fit_bipolar.md) |
| `experiment.broadband` | Kittel fit → g, M_eff (and anisotropy fields); ΔH vs f → damping α and ΔH₀ | Available | [docs](docs/experiment/broadband.md) |
| `theory.free_energy` | Free energies: single layer (in plane, out of plane) and coupled bilayer | Available | [docs](docs/theory/free_energy.md) |
| `theory.smit_beljers` | Smit–Beljers matrices (1 and 2 layers), with optional damping | Available | [docs](docs/theory/smit_beljers.md) |
| `theory.single_layer` | Angular dependence Hr(φ_H) of a single layer, in plane (uniaxial + cubic) and out of plane | Available | [docs](docs/theory/single_layer.md) |
| `theory.bilayer` | In-plane angular dependence of Hr for the acoustic and optical modes of a coupled bilayer | Available | [docs](docs/theory/bilayer.md) |
| `theory.dispersion` | Dispersion relations f(H), single layer and bilayer | Available | [docs](docs/theory/dispersion.md) |
| `theory.eigenvectors` | Precession of M at resonance (dynamic components, ellipses, GIF), single layer and bilayer | Available | [docs](docs/theory/eigenvectors.md) |
| `theory.linewidth` | Angular dependence of the linewidth and its contributions | In progress | — |
| `gui` | Tkinter graphical interface: every technique above without writing code | Available | [docs](docs/gui.md) |

Function and variable names are in Spanish. The documentation is in English.

---

## Documentation

The **[documentation](docs/README.md)** describes every public function: what it does,
its parameters (with units), its return value and the files it writes.

- **[Conventions](docs/conventions.md)** — units, angles, linewidth definitions and file formats used by every module. Read this first.
- **[Graphical interface](docs/gui.md)** — how to launch the GUI and what each part does.
- **Experiment:** [`fit_positive`](docs/experiment/fit_positive.md) · [`fit_bipolar`](docs/experiment/fit_bipolar.md) · [`broadband`](docs/experiment/broadband.md)
- **Theory:** [overview](docs/theory/overview.md) · [`free_energy`](docs/theory/free_energy.md) · [`smit_beljers`](docs/theory/smit_beljers.md) · [`single_layer`](docs/theory/single_layer.md) · [`bilayer`](docs/theory/bilayer.md) · [`dispersion`](docs/theory/dispersion.md) · [`eigenvectors`](docs/theory/eigenvectors.md)

---

## Installation

Clone the repository and install it in **editable mode** inside a virtual environment:

```bash
git clone https://github.com/<user>/fmr-toolkit.git
cd fmr-toolkit

# with conda
conda create -n fmr_env python=3.11
conda activate fmr_env

# or with venv
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

pip install -e .
```

`pip install -e .` installs all dependencies (numpy, scipy, matplotlib, sympy) and makes `fmrtoolkit` importable from anywhere. With `-e`, changes to the code take effect without reinstalling.

Check the installation:

```bash
python -c "import fmrtoolkit.experiment.broadband, fmrtoolkit.theory.single_layer"
```

The graphical interface uses tkinter, which comes with Python on Windows and macOS. On
Linux it may need the system package (for example `sudo apt install python3-tk`).

---

## Quick start

### Graphical interface

```bash
python -m fmrtoolkit.gui
```

Choose a technique on the left, fill in the form (every field has an ⓘ with its
description) and press *Run*. See the [GUI documentation](docs/gui.md).

### From Python

Each module can be imported from a script or notebook, or run directly (`python -m fmrtoolkit.experiment.fit_positive`).

### 1. Fit individual spectra

```python
from fmrtoolkit.experiment import fit_positive, fit_bipolar

# Spectra from 0 to +H, two resonance lines per spectrum
tabla = fit_positive.ajustar_carpeta("path/to/spectra", n_lineas=2, ventana=300)

# Spectra from -H to +H
tabla = fit_bipolar.ajustar_carpeta("path/to/spectra")
```

Main options: `n_lineas` (1 or 2), `ventana` (half-width in Oe of the region assigned to one line), `extensiones` (`'.dat'`, `'.txt'` or both) and `graficar` (show plots; PDFs are saved anyway).

### 2. Broadband analysis

```python
from fmrtoolkit.experiment.broadband import ajustar_banda_ancha

res = ajustar_banda_ancha("path/to/spectra/output_1peak.txt",
                          g_limites=(2.0, 2.2),     # allowed range for g
                          H_uniaxial=0.0,           # fixed, or ajustar_Hu=True to fit it
                          eje_facil=True)

print(res["g"], res["M_eff"], res["damping"])     # each entry is (value, error)
```

### 3. Theoretical in-plane angular dependence

```python
from fmrtoolkit.theory.single_layer import variacion_angular_ip

angulos, Hr = variacion_angular_ip("path/to/angular/output_2peak.txt",
                                   Hu=20, Hc=175, magn=1155, ang_u=45,
                                   g=2.09, frecuencia=23.9e9,
                                   defasaje_deg=12)
```

The experimental file sets the field range of the simulation, and the experimental Hr is plotted with the theory for comparison.

### 4. Coupled bilayers

```python
from fmrtoolkit.theory.dispersion import dispersion_2capas
from fmrtoolkit.theory.eigenvectors import autovectores_bicapa

# Frequency vs field of the two modes (A = interlayer coupling, erg/cm²)
campos, f1, f2, ang_a, ang_b = dispersion_2capas(A=0.4, carpeta="path/to/results")

# Precession of each layer at resonance (ellipses, components vs time, GIF)
res = autovectores_bicapa(A=0.4, frecuencia=9.76e9, carpeta="path/to/results")
```

In the theory modules the frequency is given in **Hz** (`9.76e9`), not GHz. See the [documentation](docs/README.md) for all parameters.

---

## Input data

Spectra are plain-text files with **two columns**: field (Oe) and signal.

| Module | Header lines skipped | Value read from the file name |
|---|---|---|
| `fit_positive` | 4 | Frequency, e.g. `sample_9p4GHz.dat` → 9.4 |
| `fit_bipolar` | 1 (option `skiprows`) | Trailing number, e.g. `sample_9.4.dat` → 9.4 |

For angular measurements, name the files by angle (`000.dat`, `010.dat`, ...). The number is read in the same way and stored in the first column of the output.

Files whose names start with `fit_` or `output_` are ignored, so the results of a previous run are never fitted as data.

---

## Output files

Experiment modules write their outputs to the same folder as the input data.

| Module | Files |
|---|---|
| `fit_positive` | `output_1peak.txt` / `output_2peak.txt` (summary table), `fit_<file>.txt` (fitted curves) |
| `fit_bipolar` | `output_bipolar.txt`, `<file>_fit.pdf` |
| `broadband` | `output_broadband.txt`, `kittel_fit.pdf`, `damping_fit.pdf` |
| `single_layer` | `output_angular_IP_teoria_magn<Ms>_eje<angle>.txt` / `output_angular_OP_teoria_magn<Ms>.txt` and `.pdf` |
| `bilayer` | `output_angular_IP_bicapa_A<A>_eje<angle>.txt` and `.pdf` |
| `dispersion` | `Dispersion_1capa_magn<Ms>_<angle>deg.txt` / `Dispersion_2capas_A<A>_<angle>deg.txt` and `.pdf` (in `carpeta`) |
| `eigenvectors` | `autovectores_*.txt`, `componentes_*.png`, `elipse(s)_*.png`, `precesion_*.gif`, `dispersion_*.png` (in `carpeta`) |

The theory modules that do not read an experimental file write into the folder given by `carpeta`. The exact columns of every file are listed in the [documentation](docs/README.md).

---

## Models and conventions

**Units:** CGS throughout. Fields in Oe, magnetisation in emu/cm³, interlayer coupling in erg/cm², thickness in cm. Frequency in GHz in the experiment modules and in **Hz** in the theory modules. Details in [Conventions](docs/conventions.md).

**Lineshape:** the derivative of a Lorentzian, mixing absorption and dispersion through a phase φ. The fitted width is the **FWHM** of the absorption line. The peak-to-peak width of the derivative is

$$\Delta H_{pp} = \frac{\Delta H_{\text{FWHM}}}{\sqrt{3}}$$

> **Note:** both `fit_positive` and `fit_bipolar` store the **peak-to-peak** width in their `output_*.txt` files, which is what the damping model in `broadband` assumes.

**Kittel (field in plane, along an easy or hard axis):**

$$f = \frac{g}{714.5}\sqrt{(H + H_u + H_c)(H + H_u + H_c + 4\pi M_{\text{eff}})} \qquad \text{(easy axis)}$$

$$f = \frac{g}{714.5}\sqrt{(H - H_u - H_c)\left(H + \tfrac{H_c}{2} + 4\pi M_{\text{eff}}\right)} \qquad \text{(hard axis)}$$

with $H_u = 2K_u/M_s$ and $H_c = 2K_1/M_s$. In the easy-axis case only the sum $H_u + H_c$ can be determined from a single direction.

**Linewidth vs frequency (peak-to-peak):**

$$\Delta H_{pp} = \Delta H_0 + \frac{4\pi}{\sqrt{3}}\,\frac{\alpha f}{\gamma}, \qquad \gamma = 8.794\times10^{6}\, g \ \ \text{rad s}^{-1}\,\text{Oe}^{-1}$$

**Angular dependence, dispersion and eigenvectors:** the equilibrium direction of M is found by minimising the free energy (Zeeman, shape, uniaxial and cubic in-plane anisotropy and, for bilayers, the interlayer coupling −A·m_a·m_b). The mode frequencies come from the Smit–Beljers matrices. The common calculation chain is described in the [theory overview](docs/theory/overview.md). Uniaxial anisotropy is written as $-K_u \sin^2\theta\cos^2(\varphi-\varphi_u)$, so values of $M_{\text{eff}}$ may differ by $H_u/4\pi$ from papers that use $K_u\sin^2\theta\sin^2\varphi$.

---

## Project structure

```
fmr-toolkit/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml            # metadata and dependencies
├── main.py                   # launches the GUI (same as python -m fmrtoolkit.gui)
├── fmrtoolkit/
│   ├── core/
│   │   ├── constants.py      # physical constants and unit conversions
│   │   ├── io.py             # reading spectra and writing results
│   │   ├── models.py         # Lorentzians, Kittel, linewidth vs frequency
│   │   └── fitting.py        # initial-guess (p0) estimators
│   ├── experiment/           # analysis of measured data
│   │   ├── fit_positive.py
│   │   ├── fit_bipolar.py
│   │   └── broadband.py
│   ├── theory/               # theoretical calculations
│   │   ├── free_energy.py    # free energies (1 and 2 layers)
│   │   ├── smit_beljers.py   # Smit–Beljers matrices
│   │   ├── equilibrium.py    # (planned) common equilibrium search
│   │   ├── single_layer.py   # angular dependence, single layer
│   │   ├── bilayer.py        # angular dependence, bilayer
│   │   ├── dispersion.py     # dispersion relations
│   │   └── eigenvectors.py   # precession at resonance
│   ├── plotting.py
│   └── gui/                  # Tkinter interface (python -m fmrtoolkit.gui)
├── examples/
│   ├── data/                 # example spectra
│   └── notebooks/            # usage without the GUI
├── tests/
└── docs/                     # documentation of every module (start at docs/README.md)
    ├── conventions.md
    ├── experiment/
    └── theory/
```

Physics and analysis live in `core/`, `experiment/` and `theory/`, and never depend on the GUI. Everything can be used from scripts or notebooks, and the GUI only collects parameters and calls these functions.

---

## Contributing

1. Create a branch for your work: `git switch -c my-feature`
2. Make small commits with descriptive messages.
3. Before pushing, run the tests: `python -m unittest discover tests` (they also check that the GUI is in sync with the function signatures).
4. If you change the parameters, return values or output files of a function, update its page in [`docs/`](docs/README.md). A new module gets a new page and a row in the *Features* table. To show a new function in the GUI, add it to `fmrtoolkit/gui/especificaciones.py` and its texts to `gui/i18n/` (see [GUI → For developers](docs/gui.md#for-developers)).
5. Open a Pull Request to `main` and ask for a review.

Measurement data and generated outputs (`*.dat`, `output_*.txt`, `*.pdf`) are excluded via `.gitignore`. Only small example files go in `examples/data/`.

---

## Citation

If this toolkit helps your research, please cite it using the information in [`CITATION.cff`](CITATION.cff).

## License

See [`LICENSE`](LICENSE).

## Authors

- *Angel A. Perez Martinez* — Instituto Balseiro / Centro Atómico Bariloche
- *Daniel Romero Rosales* — Instituto Balseiro / Centro Atómico Bariloche
