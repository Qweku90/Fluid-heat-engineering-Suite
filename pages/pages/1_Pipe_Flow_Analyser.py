"""
Module A - Pipe Flow Analyser.

Streamlit page for calculating flow velocity, Reynolds number, friction
factor, flow regime, and Darcy-Weisbach pressure drop for a fluid flowing
through a circular pipe. Uses the Fluid and Pipe classes from engineering.py.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from engineering import Fluid, Pipe

st.set_page_config(page_title="Pipe Flow Analyser", page_icon="📐", layout="wide")

st.title("📐 Module A — Pipe Flow Analyser")
st.markdown(
    """
Calculates flow velocity, Reynolds number, Darcy friction factor, flow
regime, and pressure drop for a fluid flowing through a circular pipe, using
the Darcy-Weisbach equation. Set the fluid and pipe geometry in the sidebar,
then enter a flow rate.
"""
)

# ------------------------------------------------------------------
# Sidebar inputs
# ------------------------------------------------------------------
st.sidebar.header("Fluid & Pipe Inputs")

fluid_choice = st.sidebar.selectbox(
    "Fluid",
    options=list(Fluid.PRESETS.keys()) + ["User-defined"],
    help="Choose a preset fluid or define your own properties.",
)

if fluid_choice == "User-defined":
    density = st.sidebar.number_input(
        "Fluid density (kg/m³)", min_value=0.0, value=1000.0, step=10.0,
        help="Mass per unit volume of the fluid.",
    )
    viscosity = st.sidebar.number_input(
        "Dynamic viscosity (Pa·s)", min_value=0.0, value=1.0e-3, step=1.0e-4, format="%.5f",
        help="Resistance of the fluid to shear/flow.",
    )
    fluid_name = "User-defined fluid"
else:
    preset = Fluid.PRESETS[fluid_choice]
    density = preset["density"]
    viscosity = preset["viscosity"]
    fluid_name = fluid_choice
    st.sidebar.caption(f"ρ = {density} kg/m³, μ = {viscosity:.2e} Pa·s (auto-populated)")

diameter_mm = st.sidebar.slider(
    "Pipe internal diameter, D (mm)", min_value=1.0, max_value=500.0, value=50.0, step=1.0,
    help="Internal diameter of the pipe.",
)
length_m = st.sidebar.number_input(
    "Pipe length, L (m)", min_value=0.0, value=100.0, step=1.0,
    help="Total length of pipe the fluid travels through.",
)
roughness_mm = st.sidebar.slider(
    "Pipe roughness, ε (mm)", min_value=0.0, max_value=2.0, value=0.045, step=0.005,
    help="Absolute internal roughness (commercial steel ≈ 0.045 mm, PVC ≈ 0.0015 mm).",
)
flow_rate_lps = st.sidebar.slider(
    "Flow rate, Q (L/s)", min_value=0.01, max_value=200.0, value=3.0, step=0.01,
    help="Volumetric flow rate through the pipe.",
)

st.sidebar.markdown("---")
st.sidebar.caption("All results update automatically as you change inputs.")

# ------------------------------------------------------------------
# Calculation with error handling
# ------------------------------------------------------------------
try:
    fluid = Fluid(fluid_name, density, viscosity)
    pipe = Pipe(diameter_mm / 1000.0, length_m, roughness_mm / 1000.0, fluid)
    flow_rate_m3s = flow_rate_lps / 1000.0

    result = pipe.analyse(flow_rate_m3s)

    # ------------------------------------------------------------------
    # Metric displays
    # ------------------------------------------------------------------
    st.markdown("### 📊 Results")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Velocity", f"{result['velocity']:.3f} m/s")
    col2.metric("Reynolds Number", f"{result['reynolds']:,.0f}", result["regime"])
    col3.metric("Friction Factor", f"{result['friction_factor']:.5f}")
    col4.metric("Pressure Drop", f"{result['pressure_drop_pa']/1000:.3f} kPa")

    # ------------------------------------------------------------------
    # Interactive plot: pressure drop vs flow rate
    # ------------------------------------------------------------------
    st.markdown("### 📈 Pressure Drop vs. Flow Rate")

    q_range_lps = np.linspace(0.05, max(200.0, flow_rate_lps * 1.2), 150)
    dp_curve_kpa = []
    v_curve = []
    for q_lps in q_range_lps:
        r = pipe.analyse(q_lps / 1000.0)
        dp_curve_kpa.append(r["pressure_drop_pa"] / 1000.0)
        v_curve.append(r["velocity"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=q_range_lps, y=dp_curve_kpa, mode="lines",
                              name="Pressure drop", line=dict(color="#1f77b4", width=3)))
    fig.add_trace(go.Scatter(x=[flow_rate_lps], y=[result["pressure_drop_pa"] / 1000.0],
                              mode="markers", name="Current operating point",
                              marker=dict(color="#d62728", size=13, symbol="star")))
    fig.update_layout(
        xaxis_title="Flow rate (L/s)",
        yaxis_title="Pressure drop (kPa)",
        template="plotly_white",
        height=430,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # Results table + CSV export
    # ------------------------------------------------------------------
    st.markdown("### 📋 Results Table & Export")

    sweep_df = pd.DataFrame({
        "Flow rate (L/s)": q_range_lps,
        "Velocity (m/s)": v_curve,
        "Pressure drop (kPa)": dp_curve_kpa,
    })

    summary_df = pd.DataFrame({
        "Quantity": ["Fluid", "Diameter (mm)", "Length (m)", "Roughness (mm)",
                     "Flow rate (L/s)", "Velocity (m/s)", "Reynolds number",
                     "Flow regime", "Friction factor", "Pressure drop (kPa)"],
        "Value": [fluid_name, diameter_mm, length_m, roughness_mm, flow_rate_lps,
                  round(result["velocity"], 4), f"{result['reynolds']:,.0f}",
                  result["regime"], round(result["friction_factor"], 5),
                  round(result["pressure_drop_pa"] / 1000.0, 4)],
    })
    st.table(summary_df)

    with st.expander("View full pressure-drop-vs-flow-rate sweep data"):
        st.dataframe(sweep_df, use_container_width=True)

    csv_bytes = sweep_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download sweep results as CSV",
        data=csv_bytes,
        file_name="pipe_flow_results.csv",
        mime="text/csv",
    )

except ValueError as e:
    st.warning(f"⚠️ Invalid input: {e}")
except ZeroDivisionError:
    st.warning("⚠️ A division-by-zero occurred — check that diameter and viscosity are nonzero.")
except Exception as e:
    st.warning(f"⚠️ Something went wrong with these inputs — please adjust them. ({e})")
