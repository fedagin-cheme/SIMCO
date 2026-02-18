"""
Henry's Law for gas solubility.

    P_i = H_i · x_i

where:
    P_i = partial pressure of gas i [Pa]
    H_i = Henry's law constant [Pa]
    x_i = mole fraction of dissolved gas in liquid

Temperature dependence (van't Hoff form):
    H(T) = H_ref · exp[-ΔH_sol/R · (1/T - 1/T_ref)]

References:
    - Sander, R. (2015). Compilation of Henry's law constants, Atmos. Chem. Phys.
    - Perry's Chemical Engineers' Handbook, 9th Ed.
"""

import math

# Universal gas constant [J/(mol·K)]
R = 8.314


def henry_constant_pressure(x_i: float, H_i: float) -> float:
    """
    Calculate partial pressure using Henry's law: P_i = H_i · x_i.

    Parameters
    ----------
    x_i : float
        Mole fraction of dissolved gas in liquid.
    H_i : float
        Henry's law constant [Pa].

    Returns
    -------
    float
        Partial pressure [Pa].
    """
    if not (0.0 <= x_i <= 1.0):
        raise ValueError(f"Mole fraction must be in [0, 1], got {x_i}")
    if H_i <= 0:
        raise ValueError(f"Henry's constant must be positive, got {H_i}")

    return H_i * x_i


def henry_solubility(P_i: float, H_i: float) -> float:
    """
    Calculate dissolved mole fraction from partial pressure: x_i = P_i / H_i.

    Parameters
    ----------
    P_i : float
        Partial pressure of gas [Pa].
    H_i : float
        Henry's law constant [Pa].

    Returns
    -------
    float
        Mole fraction of dissolved gas.
    """
    if P_i < 0:
        raise ValueError(f"Partial pressure must be non-negative, got {P_i}")
    if H_i <= 0:
        raise ValueError(f"Henry's constant must be positive, got {H_i}")

    return P_i / H_i


def henry_temperature_correction(
    H_ref: float,
    T_kelvin: float,
    T_ref: float = 298.15,
    dH_sol: float = 0.0,
) -> float:
    """
    Correct Henry's constant for temperature using van't Hoff equation.

    Parameters
    ----------
    H_ref : float
        Henry's constant at reference temperature [Pa].
    T_kelvin : float
        Target temperature [K].
    T_ref : float
        Reference temperature [K] (default 298.15 K = 25°C).
    dH_sol : float
        Enthalpy of dissolution [J/mol] (negative for exothermic).

    Returns
    -------
    float
        Henry's constant at target temperature [Pa].
    """
    if T_kelvin <= 0 or T_ref <= 0:
        raise ValueError("Temperatures must be positive")
    if H_ref <= 0:
        raise ValueError(f"H_ref must be positive, got {H_ref}")

    return H_ref * math.exp(-dH_sol / R * (1.0 / T_ref - 1.0 / T_kelvin))


# --- Built-in Henry's law constants at 25°C in water [Pa] ---
# Source: Sander (2015), NIST

HENRY_CONSTANTS_WATER_25C = {
    "co2": {
        "H_pa": 1.61e8,
        "dH_sol": -19400.0,  # J/mol
        "name": "Carbon dioxide",
    },
    "o2": {
        "H_pa": 4.26e9,
        "dH_sol": -14200.0,
        "name": "Oxygen",
    },
    "n2": {
        "H_pa": 8.65e9,
        "dH_sol": -10400.0,
        "name": "Nitrogen",
    },
    "h2s": {
        "H_pa": 5.53e7,
        "dH_sol": -18000.0,
        "name": "Hydrogen sulfide",
    },
    "so2": {
        "H_pa": 7.88e5,
        "dH_sol": -24800.0,
        "name": "Sulfur dioxide",
    },
    "nh3": {
        "H_pa": 5.69e4,
        "dH_sol": -34200.0,
        "name": "Ammonia",
    },
    "cl2": {
        "H_pa": 6.25e6,
        "dH_sol": -18900.0,
        "name": "Chlorine",
    },
    "ch4": {
        "H_pa": 4.13e9,
        "dH_sol": -14500.0,
        "name": "Methane",
    },
    "co": {
        "H_pa": 5.80e9,
        "dH_sol": -11000.0,
        "name": "Carbon monoxide",
    },
    "no": {
        "H_pa": 2.69e9,
        "dH_sol": -12000.0,
        "name": "Nitric oxide",
    },
}


def get_henry_data(gas: str) -> dict:
    """
    Retrieve built-in Henry's law data for a gas in water at 25°C.

    Returns dict with keys: H_pa, dH_sol, name — or None.
    """
    key = gas.lower().replace(" ", "_").replace("-", "_")
    return HENRY_CONSTANTS_WATER_25C.get(key)
