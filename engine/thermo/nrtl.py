"""
NRTL (Non-Random Two-Liquid) Activity Coefficient Model.

Calculates activity coefficients for binary mixtures using the NRTL equation:

    ln(γ₁) = x₂² [τ₂₁(G₂₁/(x₁+x₂G₂₁))² + τ₁₂G₁₂/(x₂+x₁G₁₂)²]

where:
    Gᵢⱼ = exp(-αᵢⱼ · τᵢⱼ)
    τᵢⱼ = (gᵢⱼ - gⱼⱼ) / RT = Δgᵢⱼ / RT

References:
    - Renon, H.; Prausnitz, J.M. (1968). AIChE J., 14(1), 135-144.
    - Smith, Van Ness, Abbott — Introduction to Chemical Engineering Thermodynamics
"""

import math
from typing import Tuple

# Universal gas constant [J/(mol·K)]
R = 8.314


def nrtl_gamma(
    x1: float,
    T_kelvin: float,
    dg12: float,
    dg21: float,
    alpha12: float = 0.3,
) -> Tuple[float, float]:
    """
    Calculate NRTL activity coefficients for a binary mixture.

    Parameters
    ----------
    x1 : float
        Mole fraction of component 1 (0 < x1 < 1).
    T_kelvin : float
        Temperature in Kelvin.
    dg12 : float
        Δg₁₂ = g₁₂ - g₂₂ interaction parameter [J/mol].
    dg21 : float
        Δg₂₁ = g₂₁ - g₁₁ interaction parameter [J/mol].
    alpha12 : float
        Non-randomness parameter (default 0.3, typical range 0.2–0.47).

    Returns
    -------
    (gamma1, gamma2) : Tuple[float, float]
        Activity coefficients for components 1 and 2.

    Raises
    ------
    ValueError
        If inputs are non-physical.
    """
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

    # Dimensionless interaction parameters
    tau12 = dg12 / (R * T_kelvin)
    tau21 = dg21 / (R * T_kelvin)

    # Non-randomness factors
    G12 = math.exp(-alpha12 * tau12)
    G21 = math.exp(-alpha12 * tau21)

    # Activity coefficient for component 1
    term1_num = tau21 * G21
    term1_den = x1 + x2 * G21
    term2_num = tau12 * G12
    term2_den = (x2 + x1 * G12) ** 2

    ln_gamma1 = x2 * x2 * (
        tau21 * (G21 / term1_den) ** 2
        + term2_num / term2_den
    )

    # Activity coefficient for component 2
    term3_num = tau12 * G12
    term3_den = x2 + x1 * G12
    term4_num = tau21 * G21
    term4_den = (x1 + x2 * G21) ** 2

    ln_gamma2 = x1 * x1 * (
        tau12 * (G12 / term3_den) ** 2
        + term4_num / term4_den
    )

    return (math.exp(ln_gamma1), math.exp(ln_gamma2))


def _infinite_dilution_gamma1(T_kelvin, dg12, dg21, alpha12):
    """Activity coefficient of component 1 at infinite dilution (x1→0)."""
    tau12 = dg12 / (R * T_kelvin)
    tau21 = dg21 / (R * T_kelvin)
    G12 = math.exp(-alpha12 * tau12)
    G21 = math.exp(-alpha12 * tau21)
    ln_gamma1_inf = tau21 + tau12 * G12
    return math.exp(ln_gamma1_inf)


def _infinite_dilution_gamma2(T_kelvin, dg12, dg21, alpha12):
    """Activity coefficient of component 2 at infinite dilution (x2→0)."""
    tau12 = dg12 / (R * T_kelvin)
    tau21 = dg21 / (R * T_kelvin)
    G12 = math.exp(-alpha12 * tau12)
    G21 = math.exp(-alpha12 * tau21)
    ln_gamma2_inf = tau12 + tau21 * G21
    return math.exp(ln_gamma2_inf)


# --- Built-in NRTL binary parameter sets ---
# Format: (dg12 [J/mol], dg21 [J/mol], alpha12)
# Source: DECHEMA, Gmehling et al.

NRTL_BINARY_PARAMS = {
    # Classic organic pairs (DECHEMA)
    ("benzene", "toluene"): (228.46, -228.46, 0.30),
    ("methanol", "water"): (-253.88, 845.21, 0.30),
    ("ethanol", "water"): (1300.52, 975.49, 0.30),
    ("acetone", "water"): (631.05, 1197.41, 0.30),
    ("acetone", "methanol"): (184.70, 222.64, 0.30),
    ("methanol", "benzene"): (4148.36, 2377.51, 0.47),
    ("ethanol", "benzene"): (4104.44, 2386.41, 0.47),
    ("chloroform", "methanol"): (-1579.59, 4824.98, 0.30),
    # Amine scrubbing solvents (Hilliard 2005, Kim et al. 2008, Posey 1996)
    ("mea", "water"): (-936.0, 4017.0, 0.20),
    ("mdea", "water"): (-1541.0, 5849.0, 0.20),
}


def get_nrtl_params(comp1: str, comp2: str) -> tuple:
    """
    Retrieve built-in NRTL binary parameters.

    Handles order automatically (checks both (1,2) and (2,1)).
    Returns (dg12, dg21, alpha12) or None.
    """
    key1 = comp1.lower().replace(" ", "_").replace("-", "_")
    key2 = comp2.lower().replace(" ", "_").replace("-", "_")

    if (key1, key2) in NRTL_BINARY_PARAMS:
        return NRTL_BINARY_PARAMS[(key1, key2)]
    elif (key2, key1) in NRTL_BINARY_PARAMS:
        dg12, dg21, alpha = NRTL_BINARY_PARAMS[(key2, key1)]
        return (dg21, dg12, alpha)  # Swap interaction params
    return None
