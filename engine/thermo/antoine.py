from typing import Optional

# mmHg → Pa conversion factor
MMHG_TO_PA = 133.322

ANTOINE_COEFFICIENTS = {
    "water":      (8.07131, 1730.630, 233.426,   1.0,  100.0),
    "water_high": (8.14019, 1810.940, 244.485,  60.0,  150.0),
    "methanol":   (8.08097, 1582.271, 239.726, -10.0,   84.0),
    "ethanol":    (8.11220, 1592.864, 226.184,  20.0,   93.0),
    "benzene":    (6.90565, 1211.033, 220.790,   8.0,   80.0),
    "toluene":    (6.95087, 1342.310, 219.187,   6.0,  137.0),
    "acetone":    (7.11714, 1210.595, 229.664, -13.0,   55.0),
    "n_hexane":   (6.87776, 1171.530, 224.366, -25.0,   92.0),
    "n_heptane":  (6.89385, 1264.370, 216.636,  -2.0,  127.0),
    "chloroform": (6.95465, 1170.966, 226.232, -10.0,   60.0),
    "co2":        (6.81228, 1301.679,  -3.494, -56.6,   31.0),
    "h2s":        (7.07354, 1044.849,  -3.994, -85.5,  100.0),
    "mea":        (8.41085, 2492.659,   3.456,  10.0,  170.0),
    "mdea":       (7.97354, 2530.000,   0.000,  20.0,  200.0),
    "nitrogen":   (6.49457,  255.680,  -6.600,-210.0, -147.0),
    "oxygen":     (6.69144,  340.024,  -4.144,-218.0, -119.0),
    "methane":    (6.61184,  389.930,  -7.197,-182.0,  -82.0),
    "so2":        (7.28228, 1301.679,  -3.494, -72.7,  157.5),
}

# Critical properties: (Tc_celsius, Pc_bar)
# Sources: NIST, Perry's Chemical Engineers' Handbook
CRITICAL_PROPERTIES = {
    "water":      (373.95, 220.64),
    "methanol":   (239.45, 80.84),
    "ethanol":    (241.56, 62.68),
    "benzene":    (288.87, 48.98),
    "toluene":    (318.60, 41.06),
    "acetone":    (235.05, 47.01),
    "n_hexane":   (234.67, 30.25),
    "n_heptane":  (267.01, 27.40),
    "chloroform": (263.20, 54.72),
    "co2":        ( 30.98, 73.77),
    "h2s":        (100.05, 89.63),
    "mea":        (405.05, 44.50),
    "mdea":       (404.85, 38.70),
    "nitrogen":   (-146.96, 33.96),
    "oxygen":     (-118.57, 50.43),
    "methane":    (-82.59, 45.99),
    "so2":        (157.49, 78.84),
}


def _normalize_key(compound: str) -> str:
    return compound.lower().replace(" ", "_").replace("-", "_")


def get_antoine_coefficients(compound: str) -> Optional[tuple]:
    return ANTOINE_COEFFICIENTS.get(_normalize_key(compound))


def get_critical_properties(compound: str) -> Optional[tuple]:
    """Return (Tc_celsius, Pc_bar) or None."""
    return CRITICAL_PROPERTIES.get(_normalize_key(compound))


def validate_conditions(compound: str, temperature_c: float = None, pressure_bar: float = None) -> Optional[str]:
    """
    Check whether T/P conditions are physically meaningful for VLE.

    Returns an error message string if invalid, None if OK.
    """
    key = _normalize_key(compound)
    crit = CRITICAL_PROPERTIES.get(key)
    coeffs = ANTOINE_COEFFICIENTS.get(key)

    if not coeffs:
        return f"Component '{compound}' not found in database."

    A, B, C, T_min, T_max = coeffs

    if crit:
        Tc, Pc = crit

        # Supercritical temperature check
        if temperature_c is not None and temperature_c > Tc:
            return (
                f"{compound} is supercritical above {Tc:.1f} °C. "
                f"No liquid phase exists at {temperature_c} °C."
            )

        # Pressure above critical — no VLE
        if pressure_bar is not None and pressure_bar > Pc:
            return (
                f"{compound} critical pressure is {Pc:.1f} bar. "
                f"No VLE exists at {pressure_bar} bar."
            )

        # Subcritical but pressure too high for liquid at this temperature
        # (Antoine inverse would give T > Tc)
        if pressure_bar is not None:
            try:
                bubble_T = antoine_temperature(pressure_bar * 1e5, A, B, C)
                if bubble_T > Tc:
                    return (
                        f"{compound} cannot be boiled at {pressure_bar:.4f} bar — "
                        f"the required temperature ({bubble_T:.1f} °C) exceeds "
                        f"the critical point ({Tc:.1f} °C / {Pc:.1f} bar)."
                    )
            except (ValueError, ZeroDivisionError):
                pass

    # Antoine validity range warning (non-blocking, just for info)
    if temperature_c is not None and (temperature_c < T_min or temperature_c > T_max):
        return (
            f"Temperature {temperature_c} °C is outside the Antoine valid range "
            f"for {compound} ({T_min} to {T_max} °C). Results may be inaccurate."
        )

    return None

def antoine_pressure(T_celsius: float, A: float, B: float, C: float) -> float:
    return MMHG_TO_PA * (10 ** (A - B / (C + T_celsius)))

def antoine_temperature(P_pa: float, A: float, B: float, C: float) -> float:
    import math
    P_mmhg = P_pa / MMHG_TO_PA
    return B / (A - math.log10(P_mmhg)) - C
