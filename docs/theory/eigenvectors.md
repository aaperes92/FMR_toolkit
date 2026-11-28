# `theory.eigenvectors`

**How the magnetisation precesses at resonance.** For a single layer or a coupled
bilayer it finds the resonance field at the measurement frequency, computes the
equilibrium **exactly at Hr**, and solves the **forced response** (with damping) to a
microwave field `h_rf`. The result is the dynamic magnetisation of each layer as a
function of time over one period: its components, the precession ellipse and an
animated GIF.

```python
from fmrtoolkit.theory.eigenvectors import autovectores_1capa, autovectores_bicapa

r1 = autovectores_1capa(magn=1700, Hc=0, Hu=0, frecuencia=9.76e9, carpeta="results")
r2 = autovectores_bicapa(A=0.4, frecuencia=15e9, campo_max=3000, carpeta="results")
```

## Method

1. Dispersion relation on the field grid with the **undamped** matrix
   ([`matriz_*(..., damp=0)`](smit_beljers.md)).
2. Hr of each mode with [`campo_resonancia`](bilayer.md#campo_resonanciacampos-omega-bx).
3. Equilibrium recomputed at Hr (Nelder–Mead starting from the nearest grid field).
4. Forced response with the **damped** matrix at ω = 2π·frecuencia: m(ω)·v = −d,
   with d = M·h_rf in the δφ rows. Solved with `numpy.linalg.solve`.
5. Time evolution: m(t) = Re(v·e^{iωt}), for t/T from 0 to 1.

The dynamic components are normalised by the magnetisation of each layer:
**m_θ/M_s** (out of plane) and **m_φ/M_s** (in plane).

## `autovectores_1capa(magn=1700, Hc=250, Hu=250, ang_u=45, g=2.088, damp=0.0026, frecuencia=9.76e9, ang_campo=0, h_rf=1, campo_min=10, campo_max=1400, paso_campo=10, paso_phi_M=0.5, n_tiempos=51, carpeta='.', guardar_gif=True, graficar=True, figuras=None)`

Energy: [`e_libre_IP_1L`](free_energy.md).

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `magn` | `1700` | emu/cm³ | Magnetisation |
| `Hc`, `Hu` | `250`, `250` | Oe | Cubic and uniaxial anisotropy fields |
| `ang_u` | `45` | deg | Uniaxial easy axis |
| `g` | `2.088` | — | g factor |
| `damp` | `0.0026` | — | Damping (used only in the forced response) |
| `frecuencia` | `9.76e9` | **Hz** | Measurement frequency |
| `ang_campo` | `0` | deg | In-plane field angle |
| `h_rf` | `1` | Oe | Microwave field amplitude (the response is linear in it) |
| `campo_min`, `campo_max`, `paso_campo` | `10`, `1400`, `10` | Oe | Field grid of the dispersion relation |
| `paso_phi_M` | `0.5` | deg | Grid step of the equilibrium angle (refined afterwards) |
| `n_tiempos` | `51` | — | Time points in one period, including t = 0 and t = T |
| `carpeta` | `'.'` | — | Output folder (must exist) |
| `guardar_gif` | `True` | — | Save the animation |
| `graficar` | `True` | — | Show the figures (files are saved anyway) |
| `figuras` | `None` | — | Optional list. If given, every figure except the GIF is appended to it and not closed. `None` keeps the previous behaviour |

**Returns** a dictionary:

| Key | Content |
|---|---|
| `'campos'`, `'f'` | Dispersion relation: fields (Oe), frequency (GHz) |
| `'modo'` | `None` if the mode does not cross the frequency in the field range; otherwise a dictionary with `'Hr'` (Oe), `'ang_M'` (deg), `'amplitudes'` (complex `[m_θ, m_φ]`/M_s), `'t_T'` and `'serie'` (real part vs time, shape `(n_tiempos, 2)`) |

**Files** (in `carpeta`, `<M>` = `magn`):

| File | Content |
|---|---|
| `autovectores_1capa_M<M>.txt` | Columns `t/T, m_theta_re, m_theta_im, m_phi_re, m_phi_im, area, elipt, m_theta_modulus, m_phi_modulus, Hr` |
| `componentes_1capa_M<M>.png` | m_φ and m_θ vs t/T |
| `elipse_1capa_M<M>.png` | m_φ vs m_θ (precession ellipse), with the start point and the sense of rotation |
| `precesion_1capa_M<M>.gif` | Animation of the ellipse |
| `dispersion_1capa_M<M>.png` | f vs H, the measurement frequency and the resonance point |

If the mode is not found: *"El modo no se encuentra visible para esa frecuencia …"* is
printed and only the dispersion plot is saved.

## `autovectores_bicapa(magn_a=1700, magn_b=770, espesor_a=10e-7, espesor_b=5e-7, Hc_a=250, Hc_b=0, Hu_a=250, Hu_b=0, ang_u=45, g_a=2.088, g_b=2.091, damp_a=0.0026, damp_b=0.006, A=0.4, frecuencia=9.76e9, ang_campo=0, h_rf=1, campo_min=10, campo_max=1400, paso_campo=10, paso_phi_M=2, n_tiempos=51, carpeta='.', guardar_gif=True, graficar=True, figuras=None)`

Energy: [`e_libre_IP_2L`](free_energy.md). Same procedure, for each of the two modes.

| Parameter | Default | Unit | Description |
|---|---|---|---|
| `magn_a`, `magn_b` | `1700`, `770` | emu/cm³ | Magnetisations |
| `espesor_a`, `espesor_b` | `10e-7`, `5e-7` | cm | Thicknesses (10 nm and 5 nm) |
| `Hc_a`, `Hc_b`, `Hu_a`, `Hu_b` | `250`, `0`, `250`, `0` | Oe | Anisotropy fields |
| `ang_u` | `45` | deg | Uniaxial easy axis |
| `g_a`, `g_b` | `2.088`, `2.091` | — | g factors |
| `damp_a`, `damp_b` | `0.0026`, `0.006` | — | Damping of each layer |
| `A` | `0.4` | erg/cm² | Interlayer coupling |
| `frecuencia` | `9.76e9` | **Hz** | Measurement frequency |
| `ang_campo` | `0` | deg | In-plane field angle |
| `h_rf` | `1` | Oe | Microwave field amplitude |
| `campo_min`, `campo_max`, `paso_campo` | `10`, `1400`, `10` | Oe | Field grid |
| `paso_phi_M` | `2` | deg | Step of the 2D equilibrium grid (refined afterwards) |
| `n_tiempos` | `51` | — | Time points in one period |
| `carpeta`, `guardar_gif`, `graficar`, `figuras` | `'.'`, `True`, `True`, `None` | — | As above |

**Returns** a dictionary:

| Key | Content |
|---|---|
| `'campos'`, `'f_acustico'`, `'f_optico'` | Dispersion relation: fields (Oe), low and high mode frequency (GHz) |
| `'acustico'`, `'optico'` | `None` if the mode is not found; otherwise `'Hr'` (Oe), `'ang_a'`, `'ang_b'` (deg), `'amplitudes'` (complex `[m_θa, m_φa, m_θb, m_φb]`/M_s), `'t_T'`, `'serie'` (shape `(n_tiempos, 4)`) |

**Files** (in `carpeta`, `<modo>` = `acustico` or `optico`):

| File | Content |
|---|---|
| `autovectores_<modo>_A<A>.txt` | Columns `t/T, m_theta1_re, m_theta1_im, m_phi1_re, m_phi1_im, m_theta2_re, m_theta2_im, m_phi2_re, m_phi2_im, area1, area2, elipt1, elipt2, m_theta1_modulus, m_phi1_modulus, m_theta2_modulus, m_phi2_modulus, Hr` (1 = layer a, 2 = layer b) |
| `componentes_<modo>_A<A>.png` | m_φ and m_θ of both layers vs t/T |
| `elipses_<modo>_A<A>.png` | Precession ellipses of both layers |
| `precesion_<modo>_A<A>.gif` | Animation of the ellipses |
| `dispersion_A<A>.png` | Both modes, the measurement frequency and the resonance points |

For a mode that does not cross the measurement frequency in the field range,
*"El modo óptico no se encuentra visible para esa frecuencia …"* (or *acústico*) is printed
and the other mode is still computed.

## Reading the results

- **Phase between layers:** the angle of `amplitudes[3] / amplitudes[1]` (m_φ of b over
  m_φ of a). Close to 0° → layers precess in phase (acoustic); close to 180° → out of
  phase (optical).
- **Ellipticity check:** for a single layer magnetised in plane without anisotropy,
  |m_θ|/|m_φ| = √(H/(H + 4πM)).

## Known issues

- Bilayer modes are named by frequency order ("acústico" = lower). For A < 0 this is
  inverted (see the [overview](overview.md)); check the phase between layers.
- `area` = π|m_θ||m_φ| and `elipt` = |m_θ|/|m_φ| assume m_θ and m_φ are 90° out of phase.
  With damping and coupling this is only approximate.
- File names contain only `A` (bilayer) or `magn` (single layer): runs with other
  parameters but the same `A` / `magn` overwrite the previous files.
