"""
Module C - Rock & Fluid Data Dashboard.

Streamlit page for uploading a CSV of rock or fluid sample data, viewing
summary statistics, filtering by porosity, and exploring a porosity
histogram and porosity-permeability crossplot. Filtered data can be
downloaded as CSV. This module works on plain pandas DataFrames rather
than the engineering.py classes, since it is a general data-exploration
tool rather than a fixed physical model.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Rock & Fluid Data Dashboard", page_icon="🪨", layout="wide")

st.title("🪨 Module C — Rock & Fluid Data Dashboard")
st.markdown(
    """
Upload a CSV of rock or fluid sample data. This page expects at least a
**`porosity`** column (fraction or %) and a **`permeability`** column
(any unit, e.g. mD) — any other columns (sample ID, depth, lithology, etc.)
are shown but not required. Use the sidebar to upload a file and filter by
porosity.

Don't have your own data handy? A sample file is included in the repository
at `sample_data/rock_data_sample.csv` — download it locally and upload it
here to try the dashboard out.
"""
)

st.sidebar.header("Data Upload & Filter")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is None:
    st.info("⬆️ Upload a CSV file using the sidebar to get started.")
    st.stop()

# ------------------------------------------------------------------
# Load & validate
# ------------------------------------------------------------------
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.warning(f"⚠️ Could not read this file as a CSV: {e}")
    st.stop()

if df.empty:
    st.warning("⚠️ The uploaded file has no rows.")
    st.stop()

required_cols = {"porosity", "permeability"}
missing = required_cols - set(c.lower() for c in df.columns)
# Build a case-insensitive lookup so "Porosity" / "POROSITY" etc. also work
col_lookup = {c.lower(): c for c in df.columns}

if missing:
    st.warning(
        f"⚠️ This file is missing required column(s): {', '.join(sorted(missing))}. "
        f"Expected at least 'porosity' and 'permeability' columns (case-insensitive)."
    )
    st.stop()

porosity_col = col_lookup["porosity"]
permeability_col = col_lookup["permeability"]

# Coerce to numeric, warn (not crash) on bad rows
df[porosity_col] = pd.to_numeric(df[porosity_col], errors="coerce")
df[permeability_col] = pd.to_numeric(df[permeability_col], errors="coerce")
n_bad = df[porosity_col].isna().sum() + df[permeability_col].isna().sum()
if n_bad > 0:
    st.warning(
        f"⚠️ {n_bad} value(s) in the porosity/permeability columns could not be "
        f"read as numbers and were treated as missing. They're excluded from "
        f"the statistics and charts below."
    )
df = df.dropna(subset=[porosity_col, permeability_col])

if df.empty:
    st.warning("⚠️ No valid numeric rows remain after cleaning — please check your file.")
    st.stop()

st.success(f"Loaded {len(df):,} valid sample(s) from **{uploaded_file.name}**.")

# ------------------------------------------------------------------
# Display raw data + summary statistics
# ------------------------------------------------------------------
st.markdown("### 📄 Data Preview")
st.dataframe(df.head(20), use_container_width=True)

st.markdown("### 📊 Summary Statistics")
st.dataframe(df.describe(), use_container_width=True)

# ------------------------------------------------------------------
# Filtering
# ------------------------------------------------------------------
st.sidebar.markdown("---")
por_min = float(df[porosity_col].min())
por_max = float(df[porosity_col].max())

if por_min == por_max:
    st.sidebar.caption("All samples have the same porosity — filter disabled.")
    threshold = por_min
else:
    threshold = st.sidebar.slider(
        "Minimum porosity to include",
        min_value=por_min,
        max_value=por_max,
        value=por_min,
        step=(por_max - por_min) / 100 if por_max > por_min else 0.01,
        help="Only samples with porosity greater than or equal to this value are shown.",
    )

filtered_df = df[df[porosity_col] >= threshold]

st.markdown(f"### 🔎 Filtered Data (porosity ≥ {threshold:.4f}) — {len(filtered_df):,} of {len(df):,} samples")

if filtered_df.empty:
    st.warning("⚠️ No samples match this filter — try lowering the minimum porosity.")
else:
    st.dataframe(filtered_df, use_container_width=True)

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Porosity Histogram")
        fig_hist = px.histogram(
            filtered_df, x=porosity_col, nbins=25,
            labels={porosity_col: "Porosity"},
            template="plotly_white",
        )
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.markdown("#### Porosity–Permeability Crossplot")
        color_col = None
        for candidate in ["lithology", "Lithology", "rock_type", "type"]:
            if candidate in filtered_df.columns:
                color_col = candidate
                break
        fig_scatter = px.scatter(
            filtered_df, x=porosity_col, y=permeability_col, color=color_col,
            labels={porosity_col: "Porosity", permeability_col: "Permeability"},
            template="plotly_white",
            log_y=True,
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ------------------------------------------------------------------
    # Download filtered data
    # ------------------------------------------------------------------
    st.markdown("### ⬇️ Export")
    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered data as CSV",
        data=csv_bytes,
        file_name="filtered_rock_fluid_data.csv",
        mime="text/csv",
    )
