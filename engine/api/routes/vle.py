"""
VLE (Vapor-Liquid Equilibrium) API routes.

Handles requests for:
    - Bubble point calculations
    - Dew point calculations
    - Full Txy / Pxy diagram generation
    - Flash calculations
"""

from typing import Dict, Any, List
import numpy as np

from ...thermo.antoine import antoine_pressure, get_antoine_coefficients
from ...thermo.nrtl import nrtl_gamma, get_nrtl_params


def bubble_point_temperature(
    x1: float,
    P_pa: float,
    comp1: str,
    comp2: str,
    tol: float = 0.01,
    max_iter: int = 100,
) -> Dict[str, Any]:
    """
    Calculate bubble point temperature for a binary mixture at given pressure.

    Uses modified Raoult's law: P = x₁γ₁P₁ˢᵃᵗ + x₂γ₂P₂ˢᵃᵗ

    Returns dict with T_celsius, y1, gamma1, gamma2.
    """
    antoine1 = get_antoine_coefficients(comp1)
    antoine2 = get_antoine_coefficients(comp2)
    nrtl = get_nrtl_params(comp1, comp2)

    if not antoine1 or not antoine2:
        raise ValueError(f"Antoine coefficients not found for {comp1} and/or {comp2}")

    A1, B1, C1, _, _ = antoine1
    A2, B2, C2, _, _ = antoine2

    dg12, dg21, alpha12 = nrtl if nrtl else (0.0, 0.0, 0.3)

    x2 = 1.0 - x1

    # Initial guess: ideal Raoult's law (average of pure boiling points)
    from ...thermo.antoine import antoine_temperature
    T_guess = x1 * antoine_temperature(P_pa, A1, B1, C1) + x2 * antoine_temperature(P_pa, A2, B2, C2)

    T = T_guess
    for _ in range(max_iter):
        T_K = T + 273.15
        gamma1, gamma2 = nrtl_gamma(x1, T_K, dg12, dg21, alpha12)

        P1sat = antoine_pressure(T, A1, B1, C1)
        P2sat = antoine_pressure(T, A2, B2, C2)

        P_calc = x1 * gamma1 * P1sat + x2 * gamma2 * P2sat

        if abs(P_calc - P_pa) < tol:
            y1 = x1 * gamma1 * P1sat / P_pa
            return {
                "T_celsius": round(T, 4),
                "y1": round(y1, 6),
                "gamma1": round(gamma1, 6),
                "gamma2": round(gamma2, 6),
                "converged": True,
            }

        # Newton-like update (numerical derivative)
        dT = 0.01
        T_K2 = (T + dT) + 273.15
        g1_2, g2_2 = nrtl_gamma(x1, T_K2, dg12, dg21, alpha12)
        P1sat_2 = antoine_pressure(T + dT, A1, B1, C1)
        P2sat_2 = antoine_pressure(T + dT, A2, B2, C2)
        P_calc_2 = x1 * g1_2 * P1sat_2 + x2 * g2_2 * P2sat_2

        dP_dT = (P_calc_2 - P_calc) / dT
        if abs(dP_dT) < 1e-15:
            break

        T = T - (P_calc - P_pa) / dP_dT

    return {"T_celsius": round(T, 4), "converged": False}


def bubble_point_pressure(
    x1: float,
    T_celsius: float,
    comp1: str,
    comp2: str,
) -> Dict[str, Any]:
    """
    Calculate bubble point pressure for a binary mixture at given temperature.

    Uses modified Raoult's law: P = x₁γ₁P₁ˢᵃᵗ + x₂γ₂P₂ˢᵃᵗ

    At constant T this is direct (no iteration needed).
    Returns dict with P_pa, P_bar, y1, gamma1, gamma2.
    """
    antoine1 = get_antoine_coefficients(comp1)
    antoine2 = get_antoine_coefficients(comp2)
    nrtl = get_nrtl_params(comp1, comp2)

    if not antoine1 or not antoine2:
        raise ValueError(f"Antoine coefficients not found for {comp1} and/or {comp2}")

    A1, B1, C1, _, _ = antoine1
    A2, B2, C2, _, _ = antoine2

    dg12, dg21, alpha12 = nrtl if nrtl else (0.0, 0.0, 0.3)

    x2 = 1.0 - x1
    T_K = T_celsius + 273.15

    gamma1, gamma2 = nrtl_gamma(x1, T_K, dg12, dg21, alpha12)

    P1sat = antoine_pressure(T_celsius, A1, B1, C1)
    P2sat = antoine_pressure(T_celsius, A2, B2, C2)

    P_bubble = x1 * gamma1 * P1sat + x2 * gamma2 * P2sat
    y1 = x1 * gamma1 * P1sat / P_bubble if P_bubble > 0 else 0.0

    return {
        "P_pa": round(P_bubble, 2),
        "P_bar": round(P_bubble / 1e5, 6),
        "y1": round(y1, 6),
        "gamma1": round(gamma1, 6),
        "gamma2": round(gamma2, 6),
    }


def generate_pxy_diagram(
    T_celsius: float,
    comp1: str,
    comp2: str,
    n_points: int = 51,
) -> Dict[str, Any]:
    """
    Generate Pxy diagram data for a binary mixture at constant temperature.

    Returns dict with x1, y1, P_bar arrays.
    """
    x1_values = np.linspace(0.0, 1.0, n_points)
    P_values = []
    y1_values = []

    for x1 in x1_values:
        result = bubble_point_pressure(float(x1), T_celsius, comp1, comp2)
        P_values.append(result["P_bar"])
        y1_values.append(result["y1"])

    return {
        "x1": x1_values.tolist(),
        "y1": y1_values,
        "P_bar": P_values,
        "T_celsius": T_celsius,
        "comp1": comp1,
        "comp2": comp2,
    }


def generate_txy_diagram(
    P_pa: float,
    comp1: str,
    comp2: str,
    n_points: int = 51,
) -> Dict[str, Any]:
    """
    Generate Txy diagram data for a binary mixture at constant pressure.

    Returns dict with x1, y1, T arrays.
    """
    x1_values = np.linspace(0.0, 1.0, n_points)
    T_values = []
    y1_values = []

    for x1 in x1_values:
        result = bubble_point_temperature(float(x1), P_pa, comp1, comp2)
        T_values.append(result["T_celsius"])
        y1_values.append(result.get("y1", float(x1)))

    return {
        "x1": x1_values.tolist(),
        "y1": y1_values,
        "T_celsius": T_values,
        "P_pa": P_pa,
        "comp1": comp1,
        "comp2": comp2,
    }
