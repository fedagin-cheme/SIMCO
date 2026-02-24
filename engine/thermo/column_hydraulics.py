"""engine.thermo.column_hydraulics

Packed column hydraulic design calculations.

Covers:
    - Flooding velocity via Generalized Pressure Drop Correlation (GPDC)
    - Column diameter sizing at a given flooding fraction
    - Irrigated pressure drop (Robbins-type correlation)
    - Minimum wetting rate check

Reference:
    Perry's Chemical Engineers' Handbook, 8th ed., Section 14
    Strigle, R.F., "Packed Tower Design and Applications", 2nd ed.
    Robbins, L.A., Chem. Eng. Prog., 87(5), 87-91, 1991

Units convention:
    SI throughout — Pa, m, kg, s, mol
    Packing factor F_p in m⁻¹  (note: some references use ft⁻¹; we store m⁻¹)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

# Gravitational acceleration [m/s²]
g_ACCEL = 9.81


# ── GPDC Flooding Correlation ───────────────────────────────────────────────

def flow_parameter(L_mass: float, G_mass: float, rho_G: float, rho_L: float) -> float:
    """Dimensionless flow parameter X for GPDC chart.

    X = (L/G) × (ρ_G / ρ_L)^0.5

    Parameters
    ----------
    L_mass : float
        Liquid mass flow rate [kg/s].
    G_mass : float
        Gas mass flow rate [kg/s].
    rho_G : float
        Gas density [kg/m³].
    rho_L : float
        Liquid density [kg/m³].

    Returns
    -------
    float
        Flow parameter X (dimensionless).
    """
    if G_mass <= 0:
        raise ValueError(f"Gas mass flow rate must be positive, got {G_mass}")
    if rho_L <= 0:
        raise ValueError(f"Liquid density must be positive, got {rho_L}")
    return (L_mass / G_mass) * math.sqrt(rho_G / rho_L)


def _gpdc_flooding_capacity(X: float) -> float:
    """Capacity parameter Y_flood at the flooding line.

    Uses a polynomial fit to the Eckert/Strigle GPDC flooding curve:
        ln(Y_flood) = a₀ + a₁·ln(X) + a₂·[ln(X)]²

    where Y is defined as:
        Y = u_G² · F_p · ρ_G / (g · (ρ_L - ρ_G))

    Fitted to Perry's 8th ed., Fig 14-55 flooding line data.
    Valid for X in [0.01, 5.0].

    Returns
    -------
    float
        Y_flood (dimensionless capacity parameter at flooding).
    """
    X_clamped = max(0.01, min(X, 5.0))
    ln_X = math.log(X_clamped)

    # Coefficients fitted to Perry's GPDC flooding line
    # (Eckert, 1970; verified against Norton/Koch-Glitsch data)
    a0 = -4.7674
    a1 = -0.9638
    a2 = -0.0847

    ln_Y = a0 + a1 * ln_X + a2 * ln_X ** 2
    return math.exp(ln_Y)


def flooding_velocity(
    F_p: float,
    rho_G: float,
    rho_L: float,
    L_mass: float,
    G_mass: float,
    mu_L: float = 1.0e-3,
) -> float:
    """Flooding gas velocity from the GPDC correlation.

    Parameters
    ----------
    F_p : float
        Packing factor [m⁻¹].
    rho_G : float
        Gas density [kg/m³].
    rho_L : float
        Liquid density [kg/m³].
    L_mass : float
        Liquid mass flow rate [kg/s].
    G_mass : float
        Gas mass flow rate [kg/s].
    mu_L : float
        Liquid dynamic viscosity [Pa·s]. Default: 1e-3 (water at ~20°C).

    Returns
    -------
    float
        Flooding gas superficial velocity u_flood [m/s].
    """
    if F_p <= 0:
        raise ValueError(f"Packing factor must be positive, got {F_p}")
    if rho_G <= 0 or rho_L <= 0:
        raise ValueError("Densities must be positive")
    if rho_L <= rho_G:
        raise ValueError("Liquid density must exceed gas density")

    X = flow_parameter(L_mass, G_mass, rho_G, rho_L)
    Y_flood = _gpdc_flooding_capacity(X)

    # Viscosity correction: Y includes (μ_L / μ_ref)^0.1
    # μ_ref = 1e-3 Pa·s (water reference)
    mu_ref = 1.0e-3
    mu_correction = (mu_L / mu_ref) ** 0.1

    # Solve for u_G from Y = (u_G² · F_p · ρ_G · mu_correction) / (g · (ρ_L - ρ_G))
    u_flood_sq = Y_flood * g_ACCEL * (rho_L - rho_G) / (F_p * rho_G * mu_correction)

    if u_flood_sq <= 0:
        raise ValueError("Negative flooding velocity — check input parameters")

    return math.sqrt(u_flood_sq)


# ── Column Diameter ─────────────────────────────────────────────────────────

def column_diameter(
    Q_gas_m3s: float,
    u_flood: float,
    flooding_fraction: float = 0.70,
) -> Dict[str, float]:
    """Size the column diameter from volumetric gas flow and flooding velocity.

    Parameters
    ----------
    Q_gas_m3s : float
        Actual volumetric gas flow rate [m³/s] at column conditions.
    u_flood : float
        Flooding gas superficial velocity [m/s].
    flooding_fraction : float
        Design fraction of flooding (0.5–0.85 typical). Default: 0.70.

    Returns
    -------
    dict
        u_design [m/s], A_column [m²], D_column [m].
    """
    if Q_gas_m3s <= 0:
        raise ValueError(f"Gas volumetric flow must be positive, got {Q_gas_m3s}")
    if u_flood <= 0:
        raise ValueError(f"Flooding velocity must be positive, got {u_flood}")
    if not (0.1 <= flooding_fraction <= 0.95):
        raise ValueError(f"Flooding fraction should be 0.1–0.95, got {flooding_fraction}")

    u_design = flooding_fraction * u_flood
    A_column = Q_gas_m3s / u_design
    D_column = math.sqrt(4.0 * A_column / math.pi)

    return {
        "u_design_ms": round(u_design, 4),
        "A_column_m2": round(A_column, 4),
        "D_column_m": round(D_column, 4),
    }


# ── Pressure Drop ──────────────────────────────────────────────────────────

def pressure_drop_irrigated(
    u_G: float,
    F_p: float,
    rho_G: float,
    rho_L: float,
    L_mass: float,
    G_mass: float,
    mu_L: float = 1.0e-3,
) -> float:
    """Irrigated pressure drop per unit height [Pa/m].

    Uses a simplified Robbins-type correlation:
        ΔP/Z_dry = C₁ · F_p · ρ_G · u_G²
        ΔP/Z_wet = ΔP/Z_dry × (1 + C₂ · (L_mass/G_mass)^0.5)

    This gives engineering-grade estimates (±30%) suitable for preliminary design.

    Parameters
    ----------
    u_G : float
        Gas superficial velocity [m/s].
    F_p : float
        Packing factor [m⁻¹].
    rho_G : float
        Gas density [kg/m³].
    rho_L : float
        Liquid density [kg/m³].
    L_mass : float
        Liquid mass flow rate [kg/s].
    G_mass : float
        Gas mass flow rate [kg/s].
    mu_L : float
        Liquid dynamic viscosity [Pa·s].

    Returns
    -------
    float
        Pressure drop [Pa/m of packed height].
    """
    if u_G <= 0 or F_p <= 0 or rho_G <= 0:
        raise ValueError("u_G, F_p, rho_G must all be positive")

    # Dry bed pressure drop (Ergun-like simplified)
    # Empirical constant tuned to match GPDC chart ΔP lines
    C1 = 0.04
    dP_dry = C1 * F_p * rho_G * u_G ** 2

    # Irrigation correction
    L_over_G = L_mass / G_mass if G_mass > 0 else 0.0
    C2 = 0.40  # irrigation multiplier
    dP_wet = dP_dry * (1.0 + C2 * math.sqrt(L_over_G))

    # Viscosity correction for liquids thicker than water
    mu_ref = 1.0e-3
    dP_wet *= (mu_L / mu_ref) ** 0.1

    return dP_wet


# ── Minimum Wetting Rate ───────────────────────────────────────────────────

def minimum_wetting_rate(
    a_p: float,
    sigma: float = 0.072,
    mu_L: float = 1.0e-3,
    rho_L: float = 998.0,
) -> float:
    """Minimum liquid rate to fully wet the packing [m³/(m²·s)].

    Schmidt correlation:
        MWR = 0.08 × (μ_L / (ρ_L × a_p × σ))^(1/3) × a_p

    Parameters
    ----------
    a_p : float
        Packing specific surface area [m²/m³].
    sigma : float
        Liquid surface tension [N/m]. Default: 0.072 (water at 25°C).
    mu_L : float
        Liquid dynamic viscosity [Pa·s].
    rho_L : float
        Liquid density [kg/m³].

    Returns
    -------
    float
        Minimum wetting rate [m³/(m²·s)].
    """
    if a_p <= 0:
        raise ValueError(f"Specific area must be positive, got {a_p}")

    # Simplified minimum wetting rate from Schmidt (1979)
    # MWR ≈ 0.08 × (μ_L / (ρ_L × σ))^(1/3) × a_p^(-2/3)
    term = (mu_L / (rho_L * sigma)) ** (1.0 / 3.0)
    MWR = 0.08 * term * a_p ** (-2.0 / 3.0)
    return MWR


# ── Orchestrator ───────────────────────────────────────────────────────────

def design_column(
    G_mass: float,
    L_mass: float,
    rho_G: float,
    rho_L: float,
    T_celsius: float,
    P_bar: float,
    packing: Dict[str, Any],
    flooding_fraction: float = 0.70,
    mu_L: float = 1.0e-3,
    mu_G: float = 1.8e-5,
    sigma: float = 0.072,
) -> Dict[str, Any]:
    """Full hydraulic design of a packed column.

    Parameters
    ----------
    G_mass : float
        Gas mass flow rate [kg/s].
    L_mass : float
        Liquid mass flow rate [kg/s].
    rho_G : float
        Gas density [kg/m³].
    rho_L : float
        Liquid density [kg/m³].
    T_celsius : float
        Operating temperature [°C].
    P_bar : float
        Operating pressure [bar].
    packing : dict
        Packing record from DB (must have 'packing_factor', 'specific_area',
        'void_fraction', 'name', 'type').
    flooding_fraction : float
        Design fraction of flooding. Default 0.70.
    mu_L : float
        Liquid viscosity [Pa·s]. Default: water at ~20°C.
    mu_G : float
        Gas viscosity [Pa·s]. Default: air at ~20°C.
    sigma : float
        Liquid surface tension [N/m]. Default: water at 25°C.

    Returns
    -------
    dict
        Complete hydraulic design summary.
    """
    F_p = packing["packing_factor"]
    a_p = packing["specific_area"]
    eps = packing["void_fraction"]

    # Flow parameter
    X = flow_parameter(L_mass, G_mass, rho_G, rho_L)

    # Flooding
    u_flood = flooding_velocity(F_p, rho_G, rho_L, L_mass, G_mass, mu_L)

    # Gas volumetric flow rate at operating conditions
    Q_gas = G_mass / rho_G

    # Column sizing
    sizing = column_diameter(Q_gas, u_flood, flooding_fraction)
    u_design = sizing["u_design_ms"]
    D_col = sizing["D_column_m"]
    A_col = sizing["A_column_m2"]

    # Pressure drop at design conditions
    dP_dZ = pressure_drop_irrigated(u_design, F_p, rho_G, rho_L, L_mass, G_mass, mu_L)

    # Minimum wetting rate
    MWR = minimum_wetting_rate(a_p, sigma, mu_L, rho_L)
    # Actual liquid superficial velocity
    L_vol = L_mass / rho_L  # m³/s
    u_L = L_vol / A_col if A_col > 0 else 0.0
    wetting_ok = u_L >= MWR

    return {
        "packing_name": packing.get("name", ""),
        "packing_type": packing.get("type", ""),
        "packing_factor": F_p,
        "specific_area": a_p,
        "void_fraction": eps,
        "T_celsius": T_celsius,
        "P_bar": P_bar,
        "G_mass_kgs": round(G_mass, 4),
        "L_mass_kgs": round(L_mass, 4),
        "rho_G_kgm3": round(rho_G, 3),
        "rho_L_kgm3": round(rho_L, 1),
        "flow_parameter_X": round(X, 4),
        "u_flood_ms": round(u_flood, 4),
        "flooding_fraction": flooding_fraction,
        "u_design_ms": round(u_design, 4),
        "A_column_m2": round(A_col, 4),
        "D_column_m": round(D_col, 4),
        "D_column_mm": round(D_col * 1000, 0),
        "pressure_drop_Pa_m": round(dP_dZ, 1),
        "pressure_drop_mbar_m": round(dP_dZ / 100.0, 2),
        "min_wetting_rate_m3m2s": round(MWR, 6),
        "actual_liquid_vel_m3m2s": round(u_L, 6),
        "wetting_adequate": wetting_ok,
    }
