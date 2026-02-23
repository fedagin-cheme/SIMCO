"""engine.thermo.nrtl

NRTL (Non-Random Two-Liquid) Activity Coefficient Model.

Thermodynamic parameters are fetched from the JSON database.
"""

import math
from typing import Optional, Tuple

from engine.database.db import ChemicalDatabase

# Universal gas constant [J/(mol·K)]
R = 8.314


def nrtl_gamma(
    x1: float,
    T_kelvin: float,
    dg12: float,
    dg21: float,
    alpha12: float = 0.3,
) -> Tuple[float, float]:
    """Calculate NRTL activity coefficients for a binary mixture."""
    if not (0.0 <= x1 <= 1.0):
        raise ValueError(f"x1 must be in [0, 1], got {x1}")
    if T_kelvin <= 0:
        raise ValueError(f"Temperature must be positive, got {T_kelvin} K")

    x2 = 1.0 - x1

    # Handle pure-component limits
    if x1 < 1e-12:
        return (_infinite_dilution_gamma1(T_kelvin, dg12, dg21, alpha12), 1.0)
    if x2 < 1e-12:
        return (1.0, _infinite_dilution_gamma2(T_kelvin, dg12, dg21, alpha12))

    tau12 = dg12 / (R * T_kelvin)
    tau21 = dg21 / (R * T_kelvin)

    G12 = math.exp(-alpha12 * tau12)
    G21 = math.exp(-alpha12 * tau21)

    term1_den = x1 + x2 * G21
    term2_den = (x2 + x1 * G12) ** 2

    ln_gamma1 = x2 * x2 * (
        tau21 * (G21 / term1_den) ** 2 + (tau12 * G12) / term2_den
    )

    term3_den = x2 + x1 * G12
    term4_den = (x1 + x2 * G21) ** 2

    ln_gamma2 = x1 * x1 * (
        tau12 * (G12 / term3_den) ** 2 + (tau21 * G21) / term4_den
    )

    return (math.exp(ln_gamma1), math.exp(ln_gamma2))


def _infinite_dilution_gamma1(T_kelvin, dg12, dg21, alpha12):
    tau12 = dg12 / (R * T_kelvin)
    tau21 = dg21 / (R * T_kelvin)
    G12 = math.exp(-alpha12 * tau12)
    G21 = math.exp(-alpha12 * tau21)
    ln_gamma1_inf = tau21 + tau12 * G12
    return math.exp(ln_gamma1_inf)


def _infinite_dilution_gamma2(T_kelvin, dg12, dg21, alpha12):
    tau12 = dg12 / (R * T_kelvin)
    tau21 = dg21 / (R * T_kelvin)
    G12 = math.exp(-alpha12 * tau12)
    G21 = math.exp(-alpha12 * tau21)
    ln_gamma2_inf = tau12 + tau21 * G21
    return math.exp(ln_gamma2_inf)


def get_nrtl_params(comp1: str, comp2: str, T_kelvin: float = 298.15) -> Optional[tuple]:
    """Retrieve NRTL parameters from the DB.

    Returns (dg12, dg21, alpha12) or None.
    """
    with ChemicalDatabase() as db:
        rec = db.get_nrtl(comp1, comp2, T_kelvin=T_kelvin)
    if not rec:
        return None
    return (rec["dg12"], rec["dg21"], rec["alpha12"])
