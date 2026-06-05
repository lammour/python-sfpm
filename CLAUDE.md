# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Educational demo application for a video conference talk: **"Python pour les physiciens médicaux"**. The app measures the **NPS (Noise Power Spectrum / Spectre de Puissance du Bruit)** from CT scanner DICOM images, following the ANSM standard (décision du 18/12/2025). It is designed to be coded live during the presentation.

The NPS algorithm is adapted from [cq-tdm](https://github.com/lammour/cq-tdm/).

## Running the app

```bash
# Create and activate the virtual environment (first time)
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # Linux/macOS
.venv\Scripts\pip install -r requirements.txt  # Windows

# Run
.venv/bin/python main.py   # Linux/macOS
.venv\Scripts\python main.py  # Windows
```

## Test images

The archive `20251229-controle-scanographie-banque-images-reference.zip` contains 5 CT series of a water phantom, extracted to `images/`:

| Série | Chemin | kV | mA | Noyau |
|-------|--------|----|----|-------|
| Serie_1 | `images/Serie_1/S1/` | 120 | 350 | STANDARD |
| Serie_2 | `images/Serie_2/S2/` | 120 | 275 | B |
| Serie_3a | `images/Serie_3a/S3a/` | 120 | 182 | Hr38s |
| Serie_3b | `images/Serie_3b/S3b/` | 100 | 288 | Br38f |
| Serie_4 | `images/Serie_4/S4/` | 100 | 250 | BODY_SHARP |

## Architecture

```
main.py           # Entry point
app.py            # CustomTkinter GUI (ApplicationNPS, VueCT, VueNPS, VueMetriques)
nps_calculator.py # NPS computation: DICOM → ROIs → FFT → radial avg → polynomial fit
dicom_loader.py   # DICOM I/O: SliceDicom, SerieDicom, charger_dossier_dicom()
requirements.txt
images/           # Extracted DICOM test data
```

**Data flow:**
1. `charger_dossier_dicom(path)` → `SerieDicom` (sorted by slice location)
2. `analyser_nps(serie)` → `ResultatNPS`
   - Detect phantom center (threshold -100 to +100 HU → centroid)
   - Place 8 ROIs in octagonal pattern (4 cardinal at 42% radius, 4 diagonal at 34%)
   - For each of 10 central slices × 8 ROIs: detrend (2nd-order 2D polynomial) → FFT 2D
   - Accumulate 2D NPS, radially average (37 angles, bilinear interpolation, up to 1.375×Nyquist)
   - Fit 11th-degree polynomial → smooth NPS curve
   - Compute centroid frequency: `f̄ = ∫f·NPS(f)df / ∫NPS(f)df`
3. GUI displays CT slice + ROI overlay (left) and NPS curve (right)

## Key implementation notes

- **No FFT windowing** — this matches the ANSM/iQMetrix reference (NPWE3 method)
- **NPS normalization**: `NPS_2D = |FFT|² × pixel_size² / (rows × cols)`
- **Frequency range**: extended to 1.375 × Nyquist to cover diagonal corners of 2D frequency space
- The app uses background threads for loading and analysis to keep the GUI responsive
- Requires `numpy>=2.0` — uses `np.trapezoid` (renamed from `np.trapz` in NumPy 2.0)
