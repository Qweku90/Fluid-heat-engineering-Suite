# 🛠️ Fluid Flow & Heat Transfer Engineering Suite

A multi-page Streamlit capstone application combining three engineering
modules on top of a shared, unit-tested, object-oriented calculation core
(`engineering.py`): a **pipe flow analyser** (Reynolds number, Darcy
friction factor, Darcy–Weisbach pressure drop), a **heat transfer
calculator** (steady-state conduction via Fourier's Law, plus Newton's Law
of Cooling with a live cooling-curve plot), and a **rock & fluid data
dashboard** (CSV upload, summary statistics, porosity filtering, a
porosity histogram, and a porosity–permeability crossplot). All three pages
read from the same `Fluid`, `Pipe`, and `HeatExchangerWall` classes rather
than duplicating physics in the UI layer, every input has a plain-language
description, invalid inputs surface as warnings instead of crashes, and
every chart or table has a CSV export/download option.

**Live app:** https://engineering-suite.streamlit.app/

## Modules

| Module | What it does |
|---|---|
| **A — Pipe Flow Analyser** | Fluid + pipe geometry + flow rate → velocity, Re, friction factor, regime, pressure drop; interactive pressure-drop-vs-flow-rate plot; CSV export. |
| **B — Heat Transfer Calculator** | Steady-state flat-wall conduction (Fourier's Law) and Newton's Law of Cooling time-to-target, with a live cooling curve plot. |
| **C — Rock & Fluid Data Dashboard** | Upload a CSV with `porosity`/`permeability` columns, view summary stats, filter by minimum porosity, view a histogram and crossplot, download the filtered set. A sample file is at `sample_data/rock_data_sample.csv`. |

## Architecture

- `engineering.py` — pure-Python OOP calculation core (`Fluid`, `Pipe`,
  `HeatExchangerWall` classes, plus `newton_cooling_time` /
  `newton_cooling_curve` functions). No Streamlit imports, fully
  docstring-documented, validates its own inputs and raises `ValueError`
  on non-physical values.
- `Home.py` — app entry point / landing page (this is the Streamlit "main
  file" for deployment).
- `pages/1_Pipe_Flow_Analyser.py`, `pages/2_Heat_Transfer_Calculator.py`,
  `pages/3_Rock_Fluid_Data_Dashboard.py` — the three UI modules, using
  Streamlit's built-in multi-page app support.

## Run locally
```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Deployment
Deployed on [Streamlit Community Cloud](https://streamlit.io/cloud) from
this repository, with **`Home.py`** as the main file.

## Verification
Core physics was checked against hand calculations before trusting it:
water at 1 m/s through a 25 mm pipe gives Re ≈ 24,900 and a Darcy–Weisbach
pressure drop matching a manual calculation to within 0.1%; steady-state
conduction through a 200 mm brick wall (k = 0.8 W/m·K, ΔT = 20°C, A = 10 m²)
gives exactly Q = 800 W by Fourier's Law; Newton's Law of Cooling
time-to-target was cross-checked against the closed-form analytical
solution.

## Tech stack
Python, Streamlit, NumPy, Pandas, Plotly.
