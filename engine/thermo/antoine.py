"""
Antoine Equation for pure-component vapor pressure.

    log10(P) = A - B / (C + T)

where P is in mmHg and T is in °C (standard convention).
Results are converted to Pa for internal consistency.

References:
    - NIST Chemistry WebBook
    - Perry's Chemical Engineers' Handbook, 9th Ed.
"""

import math
from typing import Optional

# Conversion: 1 mmHg = 133.322 Pa
MMHG_TO_PA = 133.322


def antoine_pressure(T_celsius: float, A: float, B: float, C: float) -> float:
    """
    Calculate vapor pressure using the Antoine equation.

    Parameters
    ----------
    T_celsius : float
        Temperature in degrees Celsius.
    A, B, C : float
        Antoine coefficients (log10, mmHg, °C convention).

    Returns
    -------
    float
        Vapor pressure in Pa.

    Raises
    ------
    ValueError
        If (C + T) == 0 (singularity) or result is non-physical.
    """
    denom = C + T_celsius
    if abs(denom) < 1e-10:
        raise ValueError(f"Singularity: C + T = {denom:.6e} (T={T_celsius}, C={C})")

    log10_p_mmhg = A - B / denom
    p_mmhg = 10.0 ** log10_p_mmhg

    if p_mmhg < 0:
        raise ValueError(f"Non-physical negative pressure: {p_mmhg} mmHg")

    return p_mmhg * MMHG_TO_PA


def antoine_temperature(P_pa: float, A: float, B: float, C: float) -> float:
    """
    Calculate temperature from vapor pressure using inverted Antoine equation.

    Parameters
    ----------
    P_pa : float
        Vapor pressure in Pa.
    A, B, C : float
        Antoine coefficients (log10, mmHg, °C convention).

    Returns
    -------
    float
        Temperature in degrees Celsius.

    Raises
    ------
    ValueError
        If pressure is non-positive.
    """
    if P_pa <= 0:
        raise ValueError(f"Pressure must be positive, got {P_pa} Pa")

    p_mmhg = P_pa / MMHG_TO_PA
    log10_p = math.log10(p_mmhg)

    T_celsius = B / (A - log10_p) - C
    return T_celsius


# --- Built-in Antoine coefficient sets (NIST) ---
# Format: (A, B, C, T_min_C, T_max_C)

ANTOINE_COEFFICIENTS = {
    "water": (8.07131, 1730.63, 233.426, 1.0, 100.0),
    "water_high": (8.14019, 1810.94, 244.485, 99.0, 374.0),
    "methanol": (8.08097, 1582.27, 239.726, 15.0, 84.0),
    "ethanol": (8.20417, 1642.89, 230.300, 20.0, 93.0),
    "benzene": (6.90565, 1211.033, 220.790, 8.0, 80.0),
    "toluene": (6.95464, 1344.800, 219.482, 6.0, 137.0),
    "acetone": (7.02447, 1161.0, 224.0, -20.0, 77.0),
    "n_hexane": (6.87776, 1171.530, 224.366, -25.0, 92.0),
    "n_heptane": (6.89385, 1264.370, 216.636, -2.0, 127.0),
    "chloroform": (6.95465, 1170.966, 226.232, -10.0, 60.0),
}


def get_antoine_coefficients(compound: str) -> Optional[tuple]:
    """
    Retrieve built-in Antoine coefficients for a compound.

    Returns (A, B, C, T_min, T_max) or None if not found.
    """
    key = compound.lower().replace(" ", "_").replace("-", "_")
    return ANTOINE_COEFFICIENTS.get(key)
