# fmr-toolkit documentation

Reference documentation for every public function of the toolkit: what it does, its
parameters (with units), its return value and the files it writes.

Start with **[Conventions](conventions.md)**: units, angle definitions, linewidth
conventions and file formats are described once there and used by every module.

## Experiment — analysis of measured data

| Module | Main function | What it does |
|---|---|---|
| [`experiment.fit_positive`](experiment/fit_positive.md) | `ajustar_carpeta` | Fits spectra measured from 0 to +H with 1 or 2 Lorentzian-derivative lines |
| [`experiment.fit_bipolar`](experiment/fit_bipolar.md) | `ajustar_carpeta` | Fits spectra measured from −H to +H, one line per field branch |
| [`experiment.broadband`](experiment/broadband.md) | `ajustar_banda_ancha` | Kittel fit (g, M_eff, H_u) and linewidth vs frequency (α, ΔH₀) |

## Theory — calculations from the free energy

Read the **[theory overview](theory/overview.md)** first: it explains the common
calculation chain (free energy → equilibrium → Smit–Beljers matrix → frequencies → Hr).

| Module | Main functions | What it does |
|---|---|---|
| [`theory.free_energy`](theory/free_energy.md) | `e_libre_IP_1L`, `e_libre_OP_1L`, `e_libre_IP_2L` | Symbolic free energies (single layer and coupled bilayer) |
| [`theory.smit_beljers`](theory/smit_beljers.md) | `matriz_1capa`, `matriz_2capas` | Smit–Beljers (linearised LLG) matrices, with optional damping |
| [`theory.single_layer`](theory/single_layer.md) | `variacion_angular_ip`, `variacion_angular_op` | Angular dependence of Hr for a single layer, in plane and out of plane |
| [`theory.bilayer`](theory/bilayer.md) | `variacion_angular_ip_bicapa`, `campo_resonancia` | In-plane angular dependence of Hr for the two modes of a coupled bilayer |
| [`theory.dispersion`](theory/dispersion.md) | `dispersion_1capa`, `dispersion_2capas` | Frequency vs field (dispersion relations) |
| [`theory.eigenvectors`](theory/eigenvectors.md) | `autovectores_1capa`, `autovectores_bicapa` | Precession of M at resonance: dynamic components, ellipses, GIF |

## Graphical interface

**[`gui`](gui.md)** — launching the GUI (`python -m fmrtoolkit.gui`), what each part of the
window does, and how to add a technique to it.

## Keeping the documentation up to date

When you change the parameters, return values or output files of a function, update
its page in the same commit (or pull request).
