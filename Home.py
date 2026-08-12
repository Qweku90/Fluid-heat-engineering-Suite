"""
================================================================================
AI DOCUMENTATION (Capstone Project requirement)
================================================================================
AI tools used:
    - Claude (Anthropic) - used to scaffold the multi-page Streamlit
      structure, the engineering.py OOP module, and the three calculation
      pages (pipe flow, heat transfer, rock/fluid dashboard).

Key prompts given to the AI:
    1. "Design an engineering.py module with a Fluid class (with preset
       properties), a Pipe class (Reynolds number, Darcy friction factor
       via laminar/transitional/Swamee-Jain turbulent correlations,
       Darcy-Weisbach pressure drop), and a HeatExchangerWall class for
       Fourier's Law conduction, plus standalone Newton's Law of Cooling
       functions - all with docstrings and input validation, no Streamlit
       imports so the logic can be tested independently."
    2. "Build a Streamlit multi-page app: Home page plus three pages
       (Pipe Flow Analyser, Heat Transfer Calculator, Rock & Fluid Data
       Dashboard) that import classes from engineering.py rather than
       reimplementing calculations, each with sidebar inputs, live
       Plotly charts, and CSV export/download."
    3. "Add a Rock & Fluid Data Dashboard page: CSV upload, summary
       statistics table, a porosity threshold filter, a porosity
       histogram, a porosity-vs-permeability crossplot, and a download
       button for the filtered data."

Most important thing manually fixed/verified in the AI-generated code:
    - All physics was independently checked against hand calculations
      before trusting it: (1) water at 1 m/s in a 25 mm pipe gives
      Re ≈ 24,900 and a Darcy-Weisbach pressure drop within 0.1% of a
      manual calculation; (2) steady-state conduction through a 200 mm
      brick wall (k = 0.8 W/m·K, ΔT = 20°C, A = 10 m²) gives exactly
      Q = 800 W matching Fourier's Law by hand; (3) Newton's Law of
      Cooling time-to-target was cross-checked against the closed-form
      solution t = -ln((T_target-T_inf)/(T0-T_inf))/k. The AI's first
      draft of newton_cooling_time() did not validate that T_target lies
      strictly between T_inf and T0, which silently produced negative
      or complex-valued "times" for physically impossible inputs (e.g.
      asking to "cool" toward a target colder than ambient) - this was
      manually caught during testing and fixed by adding an explicit
      reachability check that raises ValueError instead.
================================================================================
"""

import streamlit as st

st.set_page_config(
    page_title="Fluid Flow & Heat Transfer Engineering Suite",
    page_icon="🛠️",
    layout="wide",
)

st.title("🛠️ Fluid Flow & Heat Transfer Engineering Suite")
st.subheader("A multi-module engineering calculation and data-analysis toolkit")

st.markdown(
    """
Welcome! This is a capstone engineering application built with Python, an
object-oriented calculation core (`engineering.py`), and Streamlit for the
interface. Use the **sidebar navigation** (or the links below) to open a
module:

### 📐 Module A — Pipe Flow Analyser
Select a fluid and pipe geometry, enter a flow rate, and get the velocity,
Reynolds number, friction factor, flow regime, and pressure drop — with an
interactive pressure-drop-vs-flow-rate chart and CSV export.

### 🔥 Module B — Heat Transfer Calculator
Compute steady-state conduction through a flat wall (Fourier's Law) and the
time for an object to cool toward ambient temperature (Newton's Law of
Cooling), with a live-updating cooling curve.

### 🪨 Module C — Rock & Fluid Data Dashboard
Upload your own CSV of rock or fluid sample data, view summary statistics,
filter by porosity, and explore a porosity histogram and a
porosity–permeability crossplot. Download the filtered data as CSV.

---

**How to use this app:** open a module from the sidebar on the left. Every
input has a short physical description next to it. Charts and tables update
automatically as you change inputs — there's no "calculate" button to press.
If you enter an invalid value (e.g. a negative diameter), the app will show
a warning instead of crashing.
"""
)

st.info(
    "💡 Tip: Module C needs a CSV with numeric `porosity` and `permeability` "
    "columns. A sample file is included in the repository under "
    "`sample_data/rock_data_sample.csv` if you'd like to try it out."
)
