"""engine.thermo.mass_transfer

Packed column mass transfer calculations for gas absorption.

Covers:
    - Kremser equation (NTU for dilute gas absorption)
    - HETP-based packed height
    - Onda (1968) correlation for individual mass transfer coefficients
    - Overall HTU (Height of a Transfer Unit)
    - Operating and equilibrium line generation

Reference:
    Perry's Chemical Engineers' Handbook, 8th ed., Section 14
    Onda, K., Takeuchi, H., Okumoto, Y., J. Chem. Eng. Japan 1(1), 56-62, 1968
    Treybal, R.E., "Mass-Transfer Operations", 3rd ed., McGraw-Hill, 1980
    Seader, J.D., Henley, E.J., "Separation Process Principles", Wiley

Units convention:
    SI throughout — Pa, m, kg, s, mol
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

# ── Constants ───────────────────────────────────────────────────────────────

g_ACCEL = 9.81  # m/s²


# ── HETP Method ─────────────────────────────────────────────────────────────

def hetp_height(N_stages: float, HETP: float) -> float:
    """Packed height from number of theoretical stages.

    Z = N × HETP

    Parameters
    ----------
    N_stages : float
        Number of theoretical stages (equilibrium stages).
    HETP : float
        Height equivalent to a theoretical plate [m].

    Returns
    -------
    float
        Packed height Z [m].
    """
    if N_stages <= 0:
        raise ValueError(f"N_stages must be positive, got {N_stages}")
    if HETP <= 0:
        raise ValueError(f"HETP must be positive, got {HETP}")
    return N_stages * HETP


# ── Kremser Equation (NTU for Dilute Absorption) ───────────────────────────

def kremser_NTU(y_in: float, y_out: float, A: float) -> float:
    """Number of overall gas-phase transfer units for dilute absorption.

    Uses the Kremser-Souders-Brown equation:

        N_OG = ln[(y_in/y_out)(1 - 1/A) + 1/A] / ln(A)

    Valid for dilute systems where operating and equilibrium lines are straight.
    Special case A = 1:  N_OG = y_in/y_out - 1  (L'Hôpital limit)

    Parameters
    ----------
    y_in : float
        Inlet gas mole fraction of solute (bottom of column).
    y_out : float
        Outlet gas mole fraction of solute (top of column).
    A : float
        Absorption factor = L_mol / (m · G_mol), where m is the
        equilibrium slope (y* = m·x).

    Returns
    -------
    float
        Number of overall gas-phase transfer units N_OG.
    """
    if y_in <= 0:
        raise ValueError(f"y_in must be positive, got {y_in}")
    if y_out <= 0:
        raise ValueError(f"y_out must be positive, got {y_out}")
    if y_out >= y_in:
        raise ValueError(f"y_out ({y_out}) must be less than y_in ({y_in})")
    if A <= 0:
        raise ValueError(f"Absorption factor must be positive, got {A}")

    ratio = y_in / y_out

    # Special case: A ≈ 1
    if abs(A - 1.0) < 1e-6:
        return ratio - 1.0

    arg = ratio * (1.0 - 1.0 / A) + 1.0 / A
    if arg <= 0:
        raise ValueError("Invalid Kremser argument — check y_in, y_out, A consistency")

    return math.log(arg) / math.log(A)


def kremser_y_out(y_in: float, A: float, NTU: float) -> float:
    """Back-calculate outlet gas mole fraction from Kremser equation.

    Inverse of kremser_NTU: given y_in, absorption factor A, and number
    of transfer units NTU, compute y_out.

    Parameters
    ----------
    y_in : float
        Inlet gas mole fraction of solute.
    A : float
        Absorption factor L_mol / (m * G_mol).
    NTU : float
        Number of overall gas-phase transfer units N_OG.

    Returns
    -------
    float
        Outlet gas mole fraction y_out.
    """
    if y_in <= 0:
        raise ValueError(f"y_in must be positive, got {y_in}")
    if A <= 0:
        raise ValueError(f"Absorption factor must be positive, got {A}")
    if NTU < 0:
        raise ValueError(f"NTU must be non-negative, got {NTU}")

    if abs(A - 1.0) < 1e-6:
        return y_in / (1.0 + NTU)

    return y_in * (A - 1.0) / (A ** (NTU + 1.0) - 1.0)


def absorption_factor(L_mol: float, G_mol: float, m: float) -> float:
    """Absorption factor A = L / (m · G).

    Parameters
    ----------
    L_mol : float
        Liquid molar flow rate [mol/s].
    G_mol : float
        Gas molar flow rate [mol/s].
    m : float
        Equilibrium line slope: y* = m · x.

    Returns
    -------
    float
        Absorption factor A (dimensionless). A > 1 means absorption is feasible.
    """
    if m <= 0:
        raise ValueError(f"Equilibrium slope m must be positive, got {m}")
    if G_mol <= 0:
        raise ValueError(f"Gas molar flow must be positive, got {G_mol}")
    return L_mol / (m * G_mol)


# ── Onda Correlation (1968) for Mass Transfer Coefficients ─────────────────

def onda_kG_a(
    G_mass_flux: float,
    a_p: float,
    D_G: float,
    mu_G: float,
    rho_G: float,
    d_nom: float = 0.025,
) -> float:
    """Gas-phase volumetric mass transfer coefficient kG·a [1/s].

    Onda (1968) correlation:
        kG / (a_p · D_G) = 5.23 · Re_G^0.7 · Sc_G^(1/3) · (a_p·d_p)^(-2)

    where d_p is the nominal packing diameter.

    Parameters
    ----------
    G_mass_flux : float
        Gas mass flux [kg/(m²·s)].
    a_p : float
        Packing specific surface area [m²/m³].
    D_G : float
        Gas-phase diffusion coefficient [m²/s].
    mu_G : float
        Gas dynamic viscosity [Pa·s].
    rho_G : float
        Gas density [kg/m³].
    d_nom : float
        Nominal packing size [m]. Default 0.025 (25mm).

    Returns
    -------
    float
        kG·a [1/s] (volumetric gas-phase mass transfer coefficient).
    """
    if G_mass_flux <= 0 or a_p <= 0 or D_G <= 0:
        raise ValueError("All inputs must be positive")

    Re_G = G_mass_flux / (a_p * mu_G)
    Sc_G = mu_G / (rho_G * D_G)
    ad_p = a_p * d_nom

    # kG [m/s] from Onda (1968)
    kG = 5.23 * a_p * D_G * Re_G ** 0.7 * Sc_G ** (1.0 / 3.0) * ad_p ** (-2.0)

    # Effective wetted area ≈ 80% of specific area (simplified)
    a_eff = 0.80 * a_p

    return kG * a_eff


def onda_kL_a(
    L_mass_flux: float,
    a_p: float,
    D_L: float,
    mu_L: float,
    rho_L: float,
    d_nom: float = 0.025,
) -> float:
    """Liquid-phase volumetric mass transfer coefficient kL·a [1/s].

    Onda (1968) correlation:
        kL · (ρ_L / (μ_L · g))^(1/3) = 0.0051 · (L/(a_w·μ_L))^(2/3) · Sc_L^(-1/2) · (a_p·d_p)^0.4

    Parameters
    ----------
    L_mass_flux : float
        Liquid mass flux [kg/(m²·s)].
    a_p : float
        Packing specific surface area [m²/m³].
    D_L : float
        Liquid-phase diffusion coefficient [m²/s].
    mu_L : float
        Liquid dynamic viscosity [Pa·s].
    rho_L : float
        Liquid density [kg/m³].
    d_nom : float
        Nominal packing size [m]. Default 0.025 (25mm).

    Returns
    -------
    float
        kL·a [1/s] (volumetric liquid-phase mass transfer coefficient).
    """
    if L_mass_flux <= 0 or a_p <= 0 or D_L <= 0:
        raise ValueError("All inputs must be positive")

    Re_L = L_mass_flux / (a_p * mu_L)
    Sc_L = mu_L / (rho_L * D_L)
    ad_p = a_p * d_nom

    # Gravitational term
    grav_factor = (rho_L / (mu_L * g_ACCEL)) ** (1.0 / 3.0)

    # kL [m/s] from Onda (1968)
    kL = 0.0051 / grav_factor * Re_L ** (2.0 / 3.0) * Sc_L ** (-0.5) * ad_p ** 0.4

    # Effective wetted area
    a_eff = 0.80 * a_p

    return kL * a_eff


# ── Overall HTU ─────────────────────────────────────────────────────────────

def overall_HTU(
    G_mol_flux: float,
    L_mol_flux: float,
    m: float,
    kG_a: float,
    kL_a: float,
    c_total_L: float = 55500.0,
    P_total: float = 101325.0,
) -> Dict[str, float]:
    """Overall height of a gas-phase transfer unit H_OG.

    H_OG = H_G + (m·G_mol / L_mol) · H_L

    where:
        H_G = G_mol_flux / (kG_a · P_total / (R·T))  [simplified]
            ≈ G_mol_flux / kG_a  for practical purposes
        H_L = L_mol_flux / (kL_a · c_total_L)

    Parameters
    ----------
    G_mol_flux : float
        Gas molar flux [mol/(m²·s)].
    L_mol_flux : float
        Liquid molar flux [mol/(m²·s)].
    m : float
        Equilibrium line slope y* = m·x.
    kG_a : float
        Volumetric gas-phase mass transfer coefficient [1/s].
    kL_a : float
        Volumetric liquid-phase mass transfer coefficient [1/s].
    c_total_L : float
        Total molar concentration of liquid [mol/m³].
        Default: 55500 (pure water at 25°C).
    P_total : float
        Total pressure [Pa]. Default: 1 atm.

    Returns
    -------
    dict
        H_G [m], H_L [m], H_OG [m], lambda (stripping factor m*G/L).
    """
    # Individual HTUs
    # H_G = G_mol_flux / (kG_a * c_G) where c_G = P/(RT) ≈ 41 mol/m³ at 25°C, 1atm
    # Simplified: H_G = G_mol_flux / kG_a (when kG_a already accounts for concentration)
    c_G = P_total / (8.314 * 298.15)  # approximate gas concentration [mol/m³]

    H_G = G_mol_flux / (kG_a * c_G) if kG_a > 0 else 0.0
    H_L = L_mol_flux / (kL_a * c_total_L) if kL_a > 0 else 0.0

    # Stripping factor
    lam = m * G_mol_flux / L_mol_flux if L_mol_flux > 0 else 0.0

    # Overall gas-phase HTU
    H_OG = H_G + lam * H_L

    return {
        "H_G_m": H_G,
        "H_L_m": H_L,
        "H_OG_m": H_OG,
        "lambda_stripping": lam,
    }


# ── Operating & Equilibrium Lines ──────────────────────────────────────────

def operating_equilibrium_lines(
    y_in: float,
    y_out: float,
    m: float,
    A: float,
    n_points: int = 51,
) -> Dict[str, List[float]]:
    """Generate operating and equilibrium line data for x-y diagram.

    Operating line (from mass balance):
        y = (L/G)·x + y_out - (L/G)·x_out
        where L/G = m·A and x_out ≈ 0 for clean solvent

    Equilibrium line:
        y* = m · x

    Parameters
    ----------
    y_in : float
        Inlet gas mole fraction.
    y_out : float
        Outlet gas mole fraction.
    m : float
        Equilibrium slope.
    A : float
        Absorption factor L/(m·G).
    n_points : int
        Number of data points.

    Returns
    -------
    dict
        x_eq, y_eq (equilibrium line), x_op, y_op (operating line).
    """
    # Operating line slope = L/G = m * A
    L_over_G = m * A

    # For clean solvent inlet: x_out = 0 (top of column)
    x_out = 0.0

    # x_in from mass balance: y_in - y_out = (L/G)(x_in - x_out)
    x_in = (y_in - y_out) / L_over_G if L_over_G > 0 else 0.0

    # x range for plotting
    x_max = max(x_in * 1.2, y_in / m * 1.2) if m > 0 else x_in * 1.2

    # Equilibrium line: y* = m·x
    x_eq = [i * x_max / (n_points - 1) for i in range(n_points)]
    y_eq = [m * x for x in x_eq]

    # Operating line: y = (L/G)·(x - x_out) + y_out
    x_op = [i * x_in / (n_points - 1) for i in range(n_points)]
    y_op = [L_over_G * (x - x_out) + y_out for x in x_op]

    return {
        "x_eq": x_eq,
        "y_eq": y_eq,
        "x_op": x_op,
        "y_op": y_op,
        "x_in": x_in,
        "x_out": x_out,
    }


# ── Full Design Orchestrator ───────────────────────────────────────────────

def design_packed_height(
    y_in: float,
    y_out: float,
    m: float,
    G_mol: float,
    L_mol: float,
    A_column: float,
    packing: Dict[str, Any],
    rho_G: float = 1.2,
    rho_L: float = 998.0,
    mu_G: float = 1.8e-5,
    mu_L: float = 1.0e-3,
    D_G: float = 1.5e-5,
    D_L: float = 1.5e-9,
    sigma: float = 0.072,
    P_total: float = 101325.0,
    dP_per_m: Optional[float] = None,
) -> Dict[str, Any]:
    """Full mass transfer design: NTU, HTU, packed height, operating lines.

    Parameters
    ----------
    y_in : float
        Inlet gas mole fraction of target solute.
    y_out : float
        Desired outlet gas mole fraction.
    m : float
        Equilibrium line slope (y* = m·x). For Henry's law: m = H / P_total.
    G_mol : float
        Total gas molar flow rate [mol/s].
    L_mol : float
        Total liquid molar flow rate [mol/s].
    A_column : float
        Column cross-section area [m²] (from Phase 3A hydraulic design).
    packing : dict
        Packing record from DB.
    rho_G, rho_L : float
        Gas/liquid densities [kg/m³].
    mu_G, mu_L : float
        Gas/liquid viscosities [Pa·s].
    D_G, D_L : float
        Gas/liquid diffusion coefficients [m²/s].
    sigma : float
        Surface tension [N/m].
    P_total : float
        Total pressure [Pa].
    dP_per_m : float or None
        Pressure drop per meter [Pa/m] from Phase 3A. If provided,
        total ΔP = dP_per_m × Z.

    Returns
    -------
    dict
        Complete mass transfer design summary.
    """
    a_p = packing["specific_area"]
    HETP = packing["hetp"]

    # Nominal packing diameter for Onda correlation
    # For structured packings (no nominal size), estimate from specific area
    d_nom_mm = packing.get("nominal_size_mm")
    if d_nom_mm and d_nom_mm > 0:
        d_nom = d_nom_mm / 1000.0  # mm → m
    else:
        # Estimate: d_p ≈ 4·ε/a_p for structured packings
        eps = packing.get("void_fraction", 0.95)
        d_nom = 4.0 * eps / a_p

    # ── Absorption factor
    A = absorption_factor(L_mol, G_mol, m)

    # ── NTU (Kremser)
    N_OG = kremser_NTU(y_in, y_out, A)

    # ── Mass fluxes
    G_mol_flux = G_mol / A_column  # mol/(m²·s)
    L_mol_flux = L_mol / A_column

    # Mass fluxes for Onda (need kg/(m²·s))
    # Approximate: G_mass_flux = G_mol * MW_gas / A_column
    # Use rho and velocity: G_mass_flux ≈ G_mol * MW_avg / A_column
    # Since we have rho_G and G_mol, approximate MW_avg = rho_G * R * T / P
    MW_G_approx = rho_G * 8.314 * 298.15 / P_total  # kg/mol
    MW_L_approx = rho_L / 55500.0  # approximate for water-like liquids

    G_mass_flux = G_mol * MW_G_approx / A_column  # kg/(m²·s)
    L_mass_flux = L_mol * MW_L_approx / A_column

    # ── Onda mass transfer coefficients
    kG_a = onda_kG_a(G_mass_flux, a_p, D_G, mu_G, rho_G, d_nom)
    kL_a = onda_kL_a(L_mass_flux, a_p, D_L, mu_L, rho_L, d_nom)

    # ── Overall HTU
    htu = overall_HTU(G_mol_flux, L_mol_flux, m, kG_a, kL_a, P_total=P_total)
    H_OG = htu["H_OG_m"]

    # ── Packed height
    Z_htu_ntu = H_OG * N_OG
    Z_hetp = HETP * N_OG  # Using NTU as approximate stage count for comparison

    # ── Operating & equilibrium lines
    lines = operating_equilibrium_lines(y_in, y_out, m, A)

    # ── Total pressure drop
    total_dP = dP_per_m * Z_htu_ntu if dP_per_m is not None else None

    # ── Removal efficiency
    removal_pct = (1.0 - y_out / y_in) * 100.0

    return {
        # Separation specs
        "y_in": y_in,
        "y_out": y_out,
        "removal_percent": round(removal_pct, 2),
        "m_equilibrium": m,
        "absorption_factor_A": round(A, 4),

        # Transfer units
        "N_OG": round(N_OG, 3),
        "H_G_m": round(htu["H_G_m"], 4),
        "H_L_m": round(htu["H_L_m"], 4),
        "H_OG_m": round(H_OG, 4),
        "lambda_stripping": round(htu["lambda_stripping"], 4),

        # Packed height
        "Z_htu_ntu_m": round(Z_htu_ntu, 3),
        "Z_hetp_m": round(Z_hetp, 3),
        "HETP_m": HETP,

        # Mass transfer coefficients
        "kG_a_per_s": round(kG_a, 4),
        "kL_a_per_s": round(kL_a, 6),

        # Fluxes
        "G_mol_flux": round(G_mol_flux, 4),
        "L_mol_flux": round(L_mol_flux, 4),
        "G_mass_flux": round(G_mass_flux, 4),
        "L_mass_flux": round(L_mass_flux, 4),

        # Pressure drop
        "total_dP_Pa": round(total_dP, 1) if total_dP is not None else None,
        "total_dP_mbar": round(total_dP / 100.0, 2) if total_dP is not None else None,

        # Line data for plotting
        "lines": lines,
    }
