# Theory overview

All theory functions follow the same calculation chain. Knowing it makes every module
page easier to read.

```
free energy  ──►  equilibrium of M  ──►  Smit–Beljers matrix  ──►  eigenvalues = mode frequencies
(free_energy)     (grid + Nelder–Mead)    (smit_beljers)              │
                                                                       ├──► dispersion f(H)          (dispersion)
                                                                       ├──► Hr where f(H) = f_meas    (single_layer, bilayer)
                                                                       └──► forced response at Hr     (eigenvectors)
```

## 1. Free energy

[`free_energy`](free_energy.md) builds the free energy as a **SymPy expression** of the
angles of M (θ, φ for each layer) and the field `h`: Zeeman, demagnetising (shape),
uniaxial and cubic in-plane anisotropy and, for bilayers, the interlayer coupling `A`.

- Single layer: energy per unit **volume** (erg/cm³).
- Bilayer: energy per unit **area** (erg/cm²), each layer weighted by its thickness.

## 2. Equilibrium

For each field value, the direction of M that **minimises** the energy (with M in the
plane, θ = 90°):

1. evaluate the energy on a grid of in-plane angles covering the full turn
   (a 2D grid for bilayers);
2. refine from the best grid point with `scipy.optimize.minimize` (Nelder–Mead),
   in `bilayer`, `dispersion_2capas` and `eigenvectors`. `single_layer` and
   `dispersion_1capa` use only a fine grid.

## 3. Smit–Beljers matrix and frequencies

[`smit_beljers`](smit_beljers.md) builds the matrix of the linearised
Landau–Lifshitz–Gilbert equations from the second derivatives of the energy. It is
linear in the frequency, **m = frec·C + K**, so the mode frequencies are the
eigenvalues of **−C⁻¹K**. They come in ± pairs; the positive real parts are kept
(1 for a single layer, 2 for a bilayer), sorted from low to high.

## 4. What each module does with the frequencies

| Goal | Function | Result |
|---|---|---|
| f vs H at a fixed field angle | [`dispersion_1capa`, `dispersion_2capas`](dispersion.md) | Dispersion curve(s) |
| Hr vs field angle, single layer | [`variacion_angular_ip`, `variacion_angular_op`](single_layer.md) | Hr(angle), compared with the experiment |
| Hr vs field angle, bilayer | [`variacion_angular_ip_bicapa`](bilayer.md) | Hr of both modes vs angle |
| How M precesses at resonance | [`autovectores_1capa`, `autovectores_bicapa`](eigenvectors.md) | Dynamic components, ellipses, GIF |

**Resonance field.** Hr is the field where the mode frequency crosses the measured
frequency `2π·frecuencia`, found by **linear interpolation** between the two grid
fields around the crossing (`paso_campo` controls the accuracy). Only the **first**
crossing is taken.

**Mode names in bilayers.** "Acoustic" is the **lower** frequency mode and "optical"
the higher one. This is correct for ferromagnetic coupling (A > 0). For
antiferromagnetic coupling (A < 0) the order is inverted: the lower mode is the
optical one (layers precessing out of phase).

## Choosing the field range

The theory functions that read an experimental file simulate fields between the
experimental minimum and maximum of Hr, extended by `margen_campo`. The others use
`campo_min`, `campo_max`, `paso_campo`. If a mode does not cross the measured
frequency inside that range, its Hr is reported as `nan` (or an error is raised in
`single_layer`): widen the range or check the parameters.

## Performance tips

- The symbolic derivatives are computed once per call (`dispersion`, `eigenvectors`)
  or once per field angle (`single_layer`, `bilayer`). Angular calculations are
  therefore slower; use a coarser `paso_ang` for exploration.
- For bilayers the equilibrium grid is 2D: `paso_phi_M=2` (180 × 180 points) is enough
  because the result is refined afterwards.
