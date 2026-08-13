"""
Module B - Heat Transfer Calculator.

Streamlit page for (1) steady-state conduction through a flat wall
(Fourier's Law) and (2) Newton's Law of Cooling, including a live
temperature-vs-time cooling curve. Uses HeatExchangerWall and the
newton_cooling_* functions from engineering.py.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from engineering import HeatExchangerWall, newton_cooling_time, newton_cooling_curve

st.set_page_config(page_title="Heat Transfer Calculator", page_icon="🔥", layout="wide")

st.title("🔥 Module B — Heat Transfer Calculator")
st.markdown(
    """
Two calculations in one page: **steady-state conduction** through a single
flat wall layer, and **Newton's Law of Cooling** for an object cooling
toward its surroundings. Set inputs in the sidebar — both sections update
live.
"""
)

# ==================================================================
# Part 1 — Steady-state conduction (Fourier's Law)
# ==================================================================
st.sidebar.header("Part 1: Wall Conduction")
k = st.sidebar.number_input(
    "Thermal conductivity, k (W/m·K)", min_value=0.0, value=0.8, step=0.05,
    help="Material property describing how easily heat conducts through it "
         "(e.g. brick ≈ 0.8, glass wool ≈ 0.04, steel ≈ 45).",
)
thickness_mm = st.sidebar.slider(
    "Wall thickness, L (mm)", min_value=1.0, max_value=1000.0, value=200.0, step=1.0,
    help="Thickness of the wall in the direction of heat flow.",
)
area_m2 = st.sidebar.number_input(
    "Wall area, A (m²)", min_value=0.0, value=10.0, step=0.5,
    help="Cross-sectional area of the wall, perpendicular to heat flow.",
)
t_hot = st.sidebar.number_input(
    "Hot-face temperature, T_hot (°C)", value=25.0, step=1.0,
    help="Temperature on the warmer side of the wall.",
)
t_cold = st.sidebar.number_input(
    "Cold-face temperature, T_cold (°C)", value=5.0, step=1.0,
    help="Temperature on the cooler side of the wall.",
)

st.markdown("## Part 1 — Steady-State Conduction (Fourier's Law)")

try:
    wall = HeatExchangerWall(k, thickness_mm / 1000.0, area_m2)
    Q = wall.heat_transfer_rate(t_hot, t_cold)
    q_flux = wall.heat_flux(t_hot, t_cold)

    col1, col2 = st.columns(2)
    col1.metric("Heat Transfer Rate, Q", f"{Q:,.1f} W")
    col2.metric("Heat Flux, q", f"{q_flux:,.1f} W/m²")

    if Q < 0:
        st.info(
            "Q is negative because T_cold is warmer than T_hot — heat is actually "
            "flowing from the 'cold' face to the 'hot' face as labelled. Swap the "
            "two temperatures if that wasn't intended."
        )

    conduction_df = pd.DataFrame({
        "Quantity": ["Thermal conductivity k (W/m·K)", "Thickness L (mm)", "Area A (m²)",
                     "T_hot (°C)", "T_cold (°C)", "Heat transfer rate Q (W)", "Heat flux q (W/m²)"],
        "Value": [k, thickness_mm, area_m2, t_hot, t_cold, round(Q, 2), round(q_flux, 2)],
    })
    st.table(conduction_df)

except ValueError as e:
    st.warning(f"⚠️ Invalid input: {e}")
except Exception as e:
    st.warning(f"⚠️ Something went wrong with these inputs — please adjust them. ({e})")

st.markdown("---")

# ==================================================================
# Part 2 — Newton's Law of Cooling
# ==================================================================
st.sidebar.header("Part 2: Newton's Law of Cooling")
t0 = st.sidebar.number_input(
    "Initial temperature, T₀ (°C)", value=90.0, step=1.0,
    help="Starting temperature of the object (e.g. a cup of coffee).",
)
t_target = st.sidebar.number_input(
    "Target temperature, T_target (°C)", value=40.0, step=1.0,
    help="Temperature you want the object to reach.",
)
t_inf = st.sidebar.number_input(
    "Ambient temperature, T∞ (°C)", value=20.0, step=1.0,
    help="Temperature of the surrounding environment the object cools toward.",
)
cooling_k = st.sidebar.slider(
    "Cooling constant, k (1/s)", min_value=0.0001, max_value=0.05, value=0.005, step=0.0001,
    format="%.4f",
    help="Rate constant controlling how fast the object cools — larger k means "
         "faster cooling. Depends on the object's material, surface area, and "
         "the surrounding airflow.",
)

st.markdown("## Part 2 — Newton's Law of Cooling")
st.markdown(
    "Model: **T(t) = T∞ + (T₀ − T∞) · e^(−k·t)** — the object's temperature "
    "decays exponentially toward the ambient temperature."
)

try:
    time_to_target_s = newton_cooling_time(t0, t_target, t_inf, cooling_k)

    col1, col2 = st.columns(2)
    col1.metric("Time to reach target", f"{time_to_target_s:,.1f} s")
    col2.metric("Time to reach target", f"{time_to_target_s/60:,.2f} min")

    # Plot a bit beyond the target time so the curve's shape is visible
    t_max = time_to_target_s * 1.5
    times, temps = newton_cooling_curve(t0, t_inf, cooling_k, t_max)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=temps, mode="lines", name="Temperature",
                              line=dict(color="#ff7f0e", width=3)))
    fig.add_hline(y=t_inf, line_dash="dot", line_color="gray",
                   annotation_text="Ambient T∞", annotation_position="bottom right")
    fig.add_trace(go.Scatter(x=[time_to_target_s], y=[t_target], mode="markers",
                              name="Target reached", marker=dict(color="#d62728", size=13, symbol="star")))
    fig.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Temperature (°C)",
        template="plotly_white",
        height=430,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    cooling_df = pd.DataFrame({
        "Time (s)": times,
        "Temperature (°C)": temps,
    })
    with st.expander("View full cooling curve data"):
        st.dataframe(cooling_df, use_container_width=True)

    csv_bytes = cooling_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download cooling curve as CSV",
        data=csv_bytes,
        file_name="cooling_curve_results.csv",
        mime="text/csv",
    )

except ValueError as e:
    st.warning(f"⚠️ Invalid input: {e}")
except Exception as e:
    st.warning(f"⚠️ Something went wrong with these inputs — please adjust them. ({e})")
