"""engine.thermo.henry

Henry's Law utilities.

All Henry constants are fetched from the JSON database.
"""

import math
from typing import Optional, Dict

from engine.database.db import ChemicalDatabase, get_db

# Universal gas constant [J/(mol·K)]
R = 8.314


def henry_constant_pressure(x_i: float, H_i: float) -> float:
    """P_i = H_i * x_i"""
    if not (0.0 <= x_i <= 1.0):
        raise ValueError(f"Mole fraction must be in [0, 1], got {x_i}")
    if H_i <= 0:
        raise ValueError(f"Henry's constant must be positive, got {H_i}")
    return H_i * x_i


def henry_solubility(P_i: float, H_i: float) -> float:
    """x_i = P_i / H_i"""
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
    """van't Hoff correction."""
    if T_kelvin <= 0 or T_ref <= 0:
        raise ValueError("Temperatures must be positive")
    if H_ref <= 0:
        raise ValueError(f"H_ref must be positive, got {H_ref}")
    return H_ref * math.exp(-dH_sol / R * (1.0 / T_ref - 1.0 / T_kelvin))


def get_henry_data(gas: str, solvent: str = "water") -> Optional[Dict[str, float]]:
    """Return Henry data for a gas in a solvent.

    Shape preserved for tests/UI:
        {H_pa, dH_sol, name?}
    """
    db = get_db()
    h = db.get_henry(gas, solvent=solvent)
    c = db.get_compound(gas)

    if not h:
        return None

    return {
        "H_pa": h["H_pa"],
        "dH_sol": h.get("dH_sol", 0.0),
        "name": (c or {}).get("name", gas),
    }
