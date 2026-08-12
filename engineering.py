"""
engineering.py

Core engineering classes and calculation functions for the
Fluid Flow & Heat Transfer Engineering Suite.

This module intentionally contains ONLY calculation logic (no Streamlit
imports), so it can be tested and verified independently of the UI layer —
good separation of concerns between the "engineering model" and the "view".
"""

import numpy as np


class Fluid:
    """
    Represents a fluid with the properties needed for flow and heat
    transfer calculations.

    Attributes:
        name (str): Descriptive name of the fluid.
        density (float): Density in kg/m^3.
        viscosity (float): Dynamic viscosity in Pa.s.
        thermal_conductivity (float or None): Thermal conductivity in
            W/(m.K), if known.
    """

    #: Built-in fluid presets with properties at approximately 20 degC.
    PRESETS = {
        "Water (20°C)": {
            "density": 998.0,
            "viscosity": 1.002e-3,
            "thermal_conductivity": 0.6,
        },
        "Air (20°C)": {
            "density": 1.204,
            "viscosity": 1.825e-5,
            "thermal_conductivity": 0.0257,
        },
        "Crude Oil (20°C)": {
            "density": 870.0,
            "viscosity": 8.0e-3,
            "thermal_conductivity": 0.14,
        },
    }

    def __init__(self, name, density, viscosity, thermal_conductivity=None):
        """
        Create a Fluid.

        Args:
            name (str): Descriptive name shown in the UI.
            density (float): Density in kg/m^3. Must be strictly positive.
            viscosity (float): Dynamic viscosity in Pa.s. Must be strictly
                positive.
            thermal_conductivity (float, optional): W/(m.K).

        Raises:
            ValueError: if density or viscosity are not positive numbers.
        """
        if density is None or density <= 0:
            raise ValueError("Fluid density must be a positive number.")
        if viscosity is None or viscosity <= 0:
            raise ValueError("Fluid viscosity must be a positive number.")
        self.name = name
        self.density = float(density)
        self.viscosity = float(viscosity)
        self.thermal_conductivity = thermal_conductivity

    @classmethod
    def from_preset(cls, preset_name):
        """
        Build a Fluid from one of the built-in PRESETS.

        Args:
            preset_name (str): A key in Fluid.PRESETS.

        Returns:
            Fluid: a new instance with the preset's properties.

        Raises:
            KeyError: if preset_name is not a recognised preset.
        """
        props = cls.PRESETS[preset_name]
        return cls(
            preset_name,
            props["density"],
            props["viscosity"],
            props.get("thermal_conductivity"),
        )

    def __repr__(self):
        return f"Fluid(name={self.name!r}, density={self.density}, viscosity={self.viscosity})"


class Pipe:
    """
    Represents a circular pipe carrying a given Fluid, and provides
    flow calculations (Reynolds number, friction factor, pressure drop).
    """

    def __init__(self, diameter_m, length_m, roughness_m, fluid):
        """
        Create a Pipe.

        Args:
            diameter_m (float): Internal diameter in metres. Must be > 0.
            length_m (float): Pipe length in metres. Must be > 0.
            roughness_m (float): Absolute internal roughness in metres.
                Must be >= 0.
            fluid (Fluid): The Fluid instance flowing through the pipe.

        Raises:
            ValueError: if any geometric input is non-physical, or if
                `fluid` is not a Fluid instance.
        """
        if diameter_m is None or diameter_m <= 0:
            raise ValueError("Pipe diameter must be a positive number.")
        if length_m is None or length_m <= 0:
            raise ValueError("Pipe length must be a positive number.")
        if roughness_m is None or roughness_m < 0:
            raise ValueError("Pipe roughness cannot be negative.")
        if not isinstance(fluid, Fluid):
            raise ValueError("fluid must be a Fluid instance.")

        self.diameter = float(diameter_m)
        self.length = float(length_m)
        self.roughness = float(roughness_m)
        self.fluid = fluid

    @property
    def area(self):
        """float: Cross-sectional flow area of the pipe, in m^2."""
        return np.pi * (self.diameter ** 2) / 4.0

    def velocity_from_flow_rate(self, flow_rate_m3s):
        """
        Convert a volumetric flow rate into a mean flow velocity.

        Args:
            flow_rate_m3s (float): Volumetric flow rate in m^3/s. Must be > 0.

        Returns:
            float: mean velocity in m/s.

        Raises:
            ValueError: if flow_rate_m3s is not positive.
        """
        if flow_rate_m3s is None or flow_rate_m3s <= 0:
            raise ValueError("Flow rate must be a positive number.")
        return flow_rate_m3s / self.area

    def reynolds_number(self, velocity):
        """
        Compute the Reynolds number: Re = rho * v * D / mu.

        Args:
            velocity (float): Mean flow velocity in m/s. Must be > 0.

        Returns:
            float: dimensionless Reynolds number.

        Raises:
            ValueError: if velocity is not positive.
        """
        if velocity is None or velocity <= 0:
            raise ValueError("Velocity must be a positive number.")
        return (self.fluid.density * velocity * self.diameter) / self.fluid.viscosity

    def friction_factor(self, reynolds):
        """
        Compute the Darcy friction factor and identify the flow regime.

        Uses f = 64/Re for laminar flow (Re < 2300), a linear blend across
        the transitional region (2300-4000), and the Swamee-Jain explicit
        approximation to the Colebrook-White equation for turbulent flow
        (Re >= 4000).

        Args:
            reynolds (float): Reynolds number. Must be > 0.

        Returns:
            tuple[float, str]: (Darcy friction factor, regime name)

        Raises:
            ValueError: if reynolds is not positive.
        """
        if reynolds is None or reynolds <= 0:
            raise ValueError("Reynolds number must be a positive number.")

        relative_roughness = self.roughness / self.diameter

        def swamee_jain(re_val):
            return 0.25 / (
                np.log10((relative_roughness / 3.7) + (5.74 / (re_val ** 0.9)))
            ) ** 2

        if reynolds < 2300:
            return 64.0 / reynolds, "Laminar"

        if reynolds < 4000:
            f_lam = 64.0 / 2300.0
            f_turb = swamee_jain(4000.0)
            blend = (reynolds - 2300.0) / (4000.0 - 2300.0)
            return f_lam + blend * (f_turb - f_lam), "Transitional"

        return swamee_jain(reynolds), "Turbulent"

    def analyse(self, flow_rate_m3s):
        """
        Run a full flow analysis for a given volumetric flow rate.

        Args:
            flow_rate_m3s (float): Volumetric flow rate in m^3/s. Must be > 0.

        Returns:
            dict: keys "flow_rate_m3s", "velocity", "reynolds",
                "friction_factor", "regime", "pressure_drop_pa".

        Raises:
            ValueError: propagated from velocity_from_flow_rate /
                reynolds_number / friction_factor for non-physical inputs.
        """
        velocity = self.velocity_from_flow_rate(flow_rate_m3s)
        re = self.reynolds_number(velocity)
        f, regime = self.friction_factor(re)
        dp = f * (self.length / self.diameter) * (self.fluid.density * velocity ** 2) / 2.0
        return {
            "flow_rate_m3s": flow_rate_m3s,
            "velocity": velocity,
            "reynolds": re,
            "friction_factor": f,
            "regime": regime,
            "pressure_drop_pa": dp,
        }


class HeatExchangerWall:
    """
    Represents a single flat wall layer for steady-state 1D conduction
    calculations (Fourier's Law).
    """

    def __init__(self, thermal_conductivity, thickness_m, area_m2):
        """
        Create a HeatExchangerWall.

        Args:
            thermal_conductivity (float): Wall material thermal
                conductivity, W/(m.K). Must be > 0.
            thickness_m (float): Wall thickness in metres. Must be > 0.
            area_m2 (float): Cross-sectional area normal to heat flow,
                in m^2. Must be > 0.

        Raises:
            ValueError: for any non-positive input.
        """
        if thermal_conductivity is None or thermal_conductivity <= 0:
            raise ValueError("Thermal conductivity must be a positive number.")
        if thickness_m is None or thickness_m <= 0:
            raise ValueError("Wall thickness must be a positive number.")
        if area_m2 is None or area_m2 <= 0:
            raise ValueError("Wall area must be a positive number.")

        self.k = float(thermal_conductivity)
        self.thickness = float(thickness_m)
        self.area = float(area_m2)

    def heat_transfer_rate(self, t_hot, t_cold):
        """
        Compute the steady-state conductive heat transfer rate through
        the wall using Fourier's Law: Q = k * A * (T_hot - T_cold) / L.

        Args:
            t_hot (float): Hot-face temperature (°C or K).
            t_cold (float): Cold-face temperature, same units as t_hot.

        Returns:
            float: heat transfer rate Q, in Watts. Positive when
                t_hot > t_cold (heat flows from hot to cold face).
        """
        return self.k * self.area * (t_hot - t_cold) / self.thickness

    def heat_flux(self, t_hot, t_cold):
        """
        Compute the conductive heat flux (rate per unit area).

        Args:
            t_hot (float): Hot-face temperature.
            t_cold (float): Cold-face temperature.

        Returns:
            float: heat flux q, in W/m^2.
        """
        return self.k * (t_hot - t_cold) / self.thickness


def newton_cooling_time(t0, t_target, t_inf, cooling_constant):
    """
    Compute the time required to cool (or warm) from T0 to T_target in an
    ambient of T_inf, under Newton's Law of Cooling:

        T(t) = T_inf + (T0 - T_inf) * exp(-k * t)

    Args:
        t0 (float): Initial temperature.
        t_target (float): Target temperature to reach.
        t_inf (float): Ambient (surrounding) temperature.
        cooling_constant (float): Cooling constant k, in 1/s. Must be > 0.

    Returns:
        float: time in seconds to reach t_target.

    Raises:
        ValueError: if cooling_constant is not positive, if t0 equals
            t_inf, or if t_target is not strictly between t_inf and t0
            (i.e. physically unreachable by cooling/warming toward
            ambient).
    """
    if cooling_constant is None or cooling_constant <= 0:
        raise ValueError("Cooling constant must be a positive number.")
    if t0 == t_inf:
        raise ValueError("Initial temperature must differ from the ambient temperature.")

    ratio = (t_target - t_inf) / (t0 - t_inf)

    if ratio <= 0 or ratio > 1:
        raise ValueError(
            "Target temperature is not reachable: it must lie strictly "
            "between the ambient temperature and the initial temperature."
        )

    return -np.log(ratio) / cooling_constant


def newton_cooling_curve(t0, t_inf, cooling_constant, t_max_s, n_points=200):
    """
    Generate a temperature-vs-time curve under Newton's Law of Cooling.

    Args:
        t0 (float): Initial temperature.
        t_inf (float): Ambient temperature.
        cooling_constant (float): Cooling constant k, in 1/s. Must be > 0.
        t_max_s (float): Maximum time to compute, in seconds. Must be > 0.
        n_points (int): Number of points along the curve.

    Returns:
        tuple[numpy.ndarray, numpy.ndarray]: (time_seconds, temperature)

    Raises:
        ValueError: if cooling_constant or t_max_s are not positive.
    """
    if cooling_constant is None or cooling_constant <= 0:
        raise ValueError("Cooling constant must be a positive number.")
    if t_max_s is None or t_max_s <= 0:
        raise ValueError("Maximum time must be a positive number.")

    times = np.linspace(0.0, t_max_s, n_points)
    temps = t_inf + (t0 - t_inf) * np.exp(-cooling_constant * times)
    return times, temps
