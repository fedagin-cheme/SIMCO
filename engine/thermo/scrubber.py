"""engine.thermo.scrubber

Multi-component gas scrubber design engine.

Given a gas mixture, solvent, packing, and operating conditions, this module:
    1. Identifies which components are acid gases (absorbable)
    2. Looks up Henry's law constants and absorption kinetics per component
    3. Computes equilibrium slope m, absorption factor A, and NTU per component
    4. Determines packed height from the most demanding component
    5. Back-calculates actual removal for each component at that height
    6. Returns exit gas and rich solvent compositions

Physical solvent (water):    m = H_pa(T) / P_total
Amine solvent (MEA/MDEA):   m_eff = H_pa(T) / (E × P_total)
    where E = enhancement factor from kinetics database.

Solve modes (DOF = 2, pick 2 of {L, η, Z}):
    solve_for="Z"   — specify L + η, compute Z  (forward design, default)
    solve_for="eta"  — specify L + Z, compute η  (rating / verification)
    solve_for="L"    — specify η + Z, compute L  (solvent optimization, bisection)

References:
    Perry's Chemical Engineers' Handbook, 8th ed., Section 14
    Kohl, A.L. & Nielsen, R.B., "Gas Purification", 5th ed., Gulf, 1997
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from engine.database.db import get_db
from engine.thermo.column_hydraulics import design_column
from engine.thermo.mass_transfer import (
    kremser_NTU,
    kremser_y_out,
    absorption_factor,
    onda_kG_a,
    onda_kL_a,
    overall_HTU,
    operating_equilibrium_lines,
)

R_GAS = 8.314  # J/(mol·K)

# Reference wt% concentrations assumed in the kinetics DB E values
_SOLVENT_REF_WT = {"MEA": 30.0, "MDEA": 50.0}
_MW_WATER = 18.015


def henry_at_T(H_pa_ref: float, dH_sol: float, T_ref_K: float, T_K: float) -> float:
    """Henry's constant at temperature T using van't Hoff equation.

    H(T) = H_ref × exp(-ΔH_sol/R × (1/T - 1/T_ref))

    Parameters
    ----------
    H_pa_ref : float
        Henry's constant at T_ref [Pa].
    dH_sol : float
        Enthalpy of dissolution [J/mol] (negative = exothermic).
    T_ref_K : float
        Reference temperature [K].
    T_K : float
        Target temperature [K].

    Returns
    -------
    float
        Henry's constant at T [Pa].
    """
    return H_pa_ref * math.exp(-dH_sol / R_GAS * (1.0 / T_K - 1.0 / T_ref_K))


def _solvent_id(solvent_name: str) -> str:
    """Map solvent names to DB kinetics keys."""
    name = solvent_name.lower()
    if "monoethanolamine" in name or name == "mea":
        return "MEA"
    elif "methyldiethanolamine" in name or name == "mdea":
        return "MDEA"
    elif "water" in name:
        return "H2O"
    elif "methanol" in name:
        return "H2O"  # treat as physical solvent
    return "H2O"


# ── Internal helpers ──────────────────────────────────────────────────────────


def _prepare_system(
    gas_mixture: List[Dict[str, Any]],
    solvent_name: str,
    packing_name: str,
    G_mass_kgs: float,
    L_mass_kgs: float,
    T_celsius: float,
    P_bar: float,
    flooding_fraction: float,
    mu_L_Pas: float,
    sigma_Nm: float,
    rho_L_kgm3: float,
    solvent_wt_pct: float = 100.0,
) -> Dict[str, Any]:
    """Resolve DB lookups, compute gas properties, and run hydraulic design.

    Returns a context dict used by downstream analysis helpers.
    """
    db = get_db()
    T_K = T_celsius + 273.15
    P_Pa = P_bar * 1e5

    # Resolve packing
    packing = db.get_packing(packing_name)
    if packing is None:
        raise ValueError(f"Packing '{packing_name}' not found in database")

    # Compute gas mixture properties
    total_mol = sum(g["mol_percent"] for g in gas_mixture)
    if abs(total_mol - 100.0) > 1.0:
        raise ValueError(f"Gas mixture mol% sum = {total_mol:.1f}, must be ~100%")

    mixture_MW = 0.0
    components = []
    for g in gas_mixture:
        comp = db.get_compound(g["name"])
        if comp is None:
            raise ValueError(f"Compound '{g['name']}' not found in database")
        frac = g["mol_percent"] / 100.0
        mixture_MW += frac * comp["mw"]
        components.append({
            "name": comp["name"],
            "id": comp["id"],
            "formula": comp.get("formula", ""),
            "mw": comp["mw"],
            "category": comp["category"],
            "mol_percent": g["mol_percent"],
            "mol_fraction": frac,
        })

    # Gas density (ideal gas)
    rho_G = (P_Pa * mixture_MW / 1000.0) / (R_GAS * T_K)

    # Hydraulic design (column diameter)
    hyd_result = design_column(
        G_mass=G_mass_kgs,
        L_mass=L_mass_kgs,
        rho_G=rho_G,
        rho_L=rho_L_kgm3,
        T_celsius=T_celsius,
        P_bar=P_bar,
        packing=packing,
        flooding_fraction=flooding_fraction,
        mu_L=mu_L_Pas,
        sigma=sigma_Nm,
    )
    A_column = hyd_result["A_column_m2"]

    # Molar flows — use effective solvent MW for amine solutions
    solv_id = _solvent_id(solvent_name)
    G_mol = G_mass_kgs / (mixture_MW / 1000.0)  # mol/s

    solvent_comp = db.get_compound(solvent_name)
    solvent_mw = solvent_comp["mw"] if solvent_comp else 18.015

    # Effective MW of the solvent solution (amine + water mixture)
    wt_frac = solvent_wt_pct / 100.0
    if solvent_wt_pct < 100.0 and solv_id in ("MEA", "MDEA"):
        MW_eff = 1.0 / (wt_frac / solvent_mw + (1.0 - wt_frac) / _MW_WATER)
    else:
        MW_eff = solvent_mw

    L_mol = L_mass_kgs / (MW_eff / 1000.0)

    return {
        "db": db,
        "T_K": T_K,
        "P_Pa": P_Pa,
        "T_celsius": T_celsius,
        "P_bar": P_bar,
        "packing": packing,
        "components": components,
        "mixture_MW": mixture_MW,
        "rho_G": rho_G,
        "rho_L_kgm3": rho_L_kgm3,
        "hyd_result": hyd_result,
        "A_column": A_column,
        "solv_id": solv_id,
        "G_mol": G_mol,
        "L_mol": L_mol,
        "G_mass_kgs": G_mass_kgs,
        "L_mass_kgs": L_mass_kgs,
        "mu_L_Pas": mu_L_Pas,
        "solvent_name": solvent_name,
        "solvent_comp": solvent_comp,
        "solvent_wt_pct": solvent_wt_pct,
        "MW_eff": MW_eff,
    }


def _compute_acid_gas_analysis(
    ctx: Dict[str, Any],
    removal_target_pct: float,
    target_component: Optional[str] = None,
) -> tuple:
    """Per-component mass transfer analysis for all acid gases.

    Parameters
    ----------
    target_component : str or None
        If set, Z_design is driven by this component only.
        If None, Z_design = max Z across all acid gases (legacy behavior).

    Returns
    -------
    tuple of (acid_gas_results, Z_design, max_NTU, max_HOG, dominant_component)
    """
    db = ctx["db"]
    T_K = ctx["T_K"]
    P_Pa = ctx["P_Pa"]
    packing = ctx["packing"]
    components = ctx["components"]
    rho_G = ctx["rho_G"]
    A_column = ctx["A_column"]
    solv_id = ctx["solv_id"]
    G_mol = ctx["G_mol"]
    L_mol = ctx["L_mol"]
    G_mass_kgs = ctx["G_mass_kgs"]
    L_mass_kgs = ctx["L_mass_kgs"]
    mu_L_Pas = ctx["mu_L_Pas"]
    rho_L_kgm3 = ctx["rho_L_kgm3"]
    solvent_wt_pct = ctx.get("solvent_wt_pct", 100.0)

    acid_gas_results = []
    max_NTU = 0.0
    max_HOG = 0.0
    dominant_component = None

    for comp in components:
        if comp["category"] != "acid_gas":
            continue

        # Henry's law constant
        henry = db.get_henry(comp["id"], solvent="water")
        if henry is None:
            acid_gas_results.append({
                **comp,
                "status": "no_henry_data",
                "m_eq": None,
                "A_factor": None,
                "NTU": None,
                "removal_pct": 0.0,
            })
            continue

        H_pa_T = henry_at_T(henry["H_pa"], henry["dH_sol"], henry["T_ref"], T_K)

        # Enhancement factor — scale by wt% relative to DB reference
        kinetics = db.get_kinetics(comp["id"], solv_id)
        E_db = kinetics["enhancement_factor_E"] if kinetics else 1.0
        D_G_val = kinetics["D_G_m2s"] if kinetics else 1.5e-5
        D_L_val = kinetics["D_L_m2s"] if kinetics else 1.5e-9

        # Scale E by actual wt% vs reference wt% (first-order approximation)
        ref_wt = _SOLVENT_REF_WT.get(solv_id)
        if ref_wt and solvent_wt_pct < 100.0:
            E = E_db * (solvent_wt_pct / ref_wt)
        else:
            E = E_db

        # Effective equilibrium slope
        m_eff = H_pa_T / (E * P_Pa)

        # Absorption factor
        A = absorption_factor(L_mol, G_mol, m_eff) if m_eff > 0 else float('inf')

        # Target removal for this component
        y_in = comp["mol_fraction"]
        removal_frac = removal_target_pct / 100.0
        y_out_target = y_in * (1.0 - removal_frac)

        if y_out_target <= 0:
            y_out_target = y_in * 0.001  # cap at 99.9%

        # When A < 1, max achievable removal is limited
        removal_capped = False
        if A < 1.0:
            max_removal = A
            if removal_frac > max_removal * 0.95:
                removal_frac = max_removal * 0.90
                y_out_target = y_in * (1.0 - removal_frac)
                removal_capped = True

        # NTU (Kremser)
        try:
            NTU = kremser_NTU(y_in, y_out_target, A) if A > 0 and A != float('inf') else 0.0
        except ValueError:
            NTU = 0.0

        # HTU from Onda
        G_mass_flux = G_mass_kgs / A_column
        L_mass_flux = L_mass_kgs / A_column
        G_mol_flux = G_mol / A_column
        L_mol_flux = L_mol / A_column

        # Nominal packing size
        d_nom_mm = packing.get("nominal_size_mm")
        d_nom = (d_nom_mm / 1000.0) if d_nom_mm and d_nom_mm > 0 else 4.0 * packing.get("void_fraction", 0.95) / packing["specific_area"]

        kG_a = onda_kG_a(G_mass_flux, packing["specific_area"], D_G_val, 1.8e-5, rho_G, d_nom)
        kL_a = onda_kL_a(L_mass_flux, packing["specific_area"], D_L_val, mu_L_Pas, rho_L_kgm3, d_nom)

        # Enhanced kL_a (chemical reaction accelerates liquid-side transfer)
        kL_a_eff = kL_a * E

        htu = overall_HTU(G_mol_flux, L_mol_flux, m_eff, kG_a, kL_a_eff, P_total=P_Pa)
        H_OG = htu["H_OG_m"]

        # Packed height for this component
        Z_comp = H_OG * NTU if NTU > 0 else 0.0

        acid_gas_results.append({
            **comp,
            "status": "calculated",
            "H_pa_at_T": round(H_pa_T, 0),
            "enhancement_E": E,
            "m_eq": round(m_eff, 6),
            "A_factor": round(A, 4),
            "NTU": round(NTU, 3),
            "H_OG_m": round(H_OG, 4),
            "Z_required_m": round(Z_comp, 3),
            "target_removal_pct": round(removal_frac * 100, 2),
            "removal_capped": removal_capped,
            "kG_a": round(kG_a, 3),
            "kL_a": round(kL_a, 6),
            "kL_a_effective": round(kL_a_eff, 6),
            "D_G": D_G_val,
            "D_L": D_L_val,
            # Full-precision values for back-calculation (avoids rounding errors)
            "_A_full": A,
            "_H_OG_full": H_OG,
            "_m_eff_full": m_eff,
        })

        # Track the dominant (controlling) component
        if NTU > 0 and H_OG > 0 and Z_comp > (max_NTU * max_HOG if dominant_component else 0):
            max_NTU = NTU
            max_HOG = H_OG
            dominant_component = comp["name"]

    # Design height selection
    if target_component:
        # Use the target component's Z_required
        target_ag = next(
            (r for r in acid_gas_results
             if r["name"] == target_component and r.get("status") == "calculated"),
            None,
        )
        if target_ag and target_ag.get("Z_required_m"):
            Z_design = target_ag["Z_required_m"]
            dominant_component = target_component
        else:
            Z_design = max((r["Z_required_m"] for r in acid_gas_results if r.get("Z_required_m")), default=0.0)
    else:
        Z_design = max((r["Z_required_m"] for r in acid_gas_results if r.get("Z_required_m")), default=0.0)

    return acid_gas_results, Z_design, max_NTU, max_HOG, dominant_component


def _backcalc_at_height(
    ctx: Dict[str, Any],
    acid_gas_results: List[Dict[str, Any]],
    Z_design: float,
    removal_target_pct: Optional[float],
) -> tuple:
    """Back-calculate actual removal at a given packed height for every component.

    Returns
    -------
    tuple of (exit_gas, total_absorbed_mol_s, lines)
    """
    components = ctx["components"]
    G_mol = ctx["G_mol"]
    packing = ctx["packing"]
    hyd_result = ctx["hyd_result"]

    exit_gas = []
    total_absorbed_mol_s = 0.0
    dominant_component = None
    dominant_removal = 0.0

    for comp in components:
        ag = next(
            (r for r in acid_gas_results if r["name"] == comp["name"] and r.get("status") == "calculated"),
            None,
        )

        if ag and ag.get("_H_OG_full", ag["H_OG_m"]) > 0 and Z_design > 0:
            actual_NTU = Z_design / ag.get("_H_OG_full", ag["H_OG_m"])
            A = ag.get("_A_full", ag["A_factor"])

            y_in_val = comp["mol_fraction"]
            y_out_actual = kremser_y_out(y_in_val, A, actual_NTU)

            actual_removal = (1.0 - y_out_actual / y_in_val) * 100.0 if y_in_val > 0 else 0.0
            absorbed_mol_s = (y_in_val - y_out_actual) * G_mol

            exit_gas.append({
                "name": comp["name"],
                "formula": comp.get("formula", ""),
                "inlet_mol_pct": comp["mol_percent"],
                "outlet_mol_frac": round(y_out_actual, 8),
                "removal_pct": round(actual_removal, 2),
                "absorbed_mol_s": round(absorbed_mol_s, 6),
            })
            total_absorbed_mol_s += absorbed_mol_s

            # Track dominant acid gas (highest required Z)
            if ag.get("Z_required_m", 0) > 0:
                z_req = ag["Z_required_m"]
                if dominant_component is None or z_req > dominant_removal:
                    dominant_component = comp["name"]
                    dominant_removal = z_req
        else:
            exit_gas.append({
                "name": comp["name"],
                "formula": comp.get("formula", ""),
                "inlet_mol_pct": comp["mol_percent"],
                "outlet_mol_frac": comp["mol_fraction"],
                "removal_pct": 0.0,
                "absorbed_mol_s": 0.0,
            })

    # Normalize exit gas to mol%
    total_exit_mol_frac = sum(g["outlet_mol_frac"] for g in exit_gas)
    for g in exit_gas:
        g["outlet_mol_pct"] = round(g["outlet_mol_frac"] / total_exit_mol_frac * 100.0, 4) if total_exit_mol_frac > 0 else 0.0

    # Operating lines for the dominant component
    dom_ag = next(
        (r for r in acid_gas_results if r["name"] == dominant_component and r.get("status") == "calculated"),
        None,
    )
    lines = None
    if dom_ag and dom_ag["m_eq"] and dom_ag["A_factor"]:
        dom_comp = next((c for c in components if c["name"] == dominant_component), None)
        if dom_comp:
            # For operating line y_out, use the actual back-calculated value
            dom_exit = next((g for g in exit_gas if g["name"] == dominant_component), None)
            y_out_for_line = dom_exit["outlet_mol_frac"] if dom_exit else dom_comp["mol_fraction"] * 0.1
            lines = operating_equilibrium_lines(
                y_in=dom_comp["mol_fraction"],
                y_out=y_out_for_line,
                m=dom_ag["m_eq"],
                A=dom_ag["A_factor"],
            )

    return exit_gas, total_absorbed_mol_s, lines, dominant_component


def _compute_Z_for_L(
    gas_mixture: List[Dict[str, Any]],
    solvent_name: str,
    packing_name: str,
    G_mass_kgs: float,
    L_mass_kgs: float,
    T_celsius: float,
    P_bar: float,
    flooding_fraction: float,
    mu_L_Pas: float,
    sigma_Nm: float,
    rho_L_kgm3: float,
    removal_target_pct: float,
    solvent_wt_pct: float = 100.0,
    target_component: Optional[str] = None,
) -> float:
    """Compute Z_design for a given L. Lightweight wrapper for bisection."""
    ctx = _prepare_system(
        gas_mixture, solvent_name, packing_name,
        G_mass_kgs, L_mass_kgs,
        T_celsius, P_bar, flooding_fraction,
        mu_L_Pas, sigma_Nm, rho_L_kgm3,
        solvent_wt_pct=solvent_wt_pct,
    )
    _, Z_design, _, _, _ = _compute_acid_gas_analysis(ctx, removal_target_pct, target_component=target_component)
    return Z_design


def _bisect_for_L(
    gas_mixture: List[Dict[str, Any]],
    solvent_name: str,
    packing_name: str,
    G_mass_kgs: float,
    T_celsius: float,
    P_bar: float,
    flooding_fraction: float,
    mu_L_Pas: float,
    sigma_Nm: float,
    rho_L_kgm3: float,
    removal_target_pct: float,
    Z_target: float,
    solvent_wt_pct: float = 100.0,
    target_component: Optional[str] = None,
    tol: float = 0.001,
    max_iter: int = 50,
) -> tuple:
    """Find L_mass_kgs via bisection such that Z(L) ≈ Z_target.

    As L increases, A increases, NTU decreases, Z decreases (monotonic).

    Returns
    -------
    tuple of (L_mass_kgs, converged, iterations)
    """
    # First, find a reasonable L_min where A > 1 for all components.
    # We need to know m_eff for the dominant component. Do a preliminary run
    # at a moderate L to discover m_eff values.
    db = get_db()
    T_K = T_celsius + 273.15
    P_Pa = P_bar * 1e5

    # Compute mixture MW and G_mol
    mixture_MW = 0.0
    for g in gas_mixture:
        comp = db.get_compound(g["name"])
        if comp is None:
            raise ValueError(f"Compound '{g['name']}' not found in database")
        mixture_MW += (g["mol_percent"] / 100.0) * comp["mw"]
    G_mol = G_mass_kgs / (mixture_MW / 1000.0)

    solvent_comp = db.get_compound(solvent_name)
    solvent_MW_kg = (solvent_comp["mw"] / 1000.0) if solvent_comp else 0.018

    # Find max m_eff across acid gas components
    solv_id = _solvent_id(solvent_name)
    max_m_eff = 0.0
    for g in gas_mixture:
        comp = db.get_compound(g["name"])
        if comp is None or comp["category"] != "acid_gas":
            continue
        henry = db.get_henry(comp["id"], solvent="water")
        if henry is None:
            continue
        H_pa_T = henry_at_T(henry["H_pa"], henry["dH_sol"], henry["T_ref"], T_K)
        kinetics = db.get_kinetics(comp["id"], solv_id)
        E = kinetics["enhancement_factor_E"] if kinetics else 1.0
        m_eff = H_pa_T / (E * P_Pa)
        if m_eff > max_m_eff:
            max_m_eff = m_eff

    if max_m_eff <= 0:
        raise ValueError("No acid gas components with valid Henry's law data found")

    # L_min: A = 1.05 for the component with largest m_eff
    L_mol_min = 1.05 * max_m_eff * G_mol
    L_min = L_mol_min * solvent_MW_kg
    L_max = max(L_min * 100.0, 1000.0)

    # Verify bounds: Z(L_min) should be > Z_target, Z(L_max) should be < Z_target
    Z_at_min = _compute_Z_for_L(
        gas_mixture, solvent_name, packing_name,
        G_mass_kgs, L_min, T_celsius, P_bar,
        flooding_fraction, mu_L_Pas, sigma_Nm, rho_L_kgm3,
        removal_target_pct, solvent_wt_pct=solvent_wt_pct,
        target_component=target_component,
    )
    Z_at_max = _compute_Z_for_L(
        gas_mixture, solvent_name, packing_name,
        G_mass_kgs, L_max, T_celsius, P_bar,
        flooding_fraction, mu_L_Pas, sigma_Nm, rho_L_kgm3,
        removal_target_pct, solvent_wt_pct=solvent_wt_pct,
        target_component=target_component,
    )

    if Z_at_max > Z_target:
        raise ValueError(
            f"Target height Z={Z_target:.3f} m is too short even at L={L_max:.1f} kg/s "
            f"(computed Z={Z_at_max:.3f} m). Increase Z_packed_m or reduce removal target."
        )

    if Z_at_min < Z_target:
        # Even minimal L gives Z < Z_target; Z_target is very generous.
        # Use L_min as the answer (column is oversized).
        L_lo = L_min * 0.5
        L_hi = L_min
    else:
        L_lo = L_min
        L_hi = L_max

    converged = False
    n_iter = 0
    L_mid = (L_lo + L_hi) / 2.0

    for n_iter in range(1, max_iter + 1):
        L_mid = (L_lo + L_hi) / 2.0
        Z_mid = _compute_Z_for_L(
            gas_mixture, solvent_name, packing_name,
            G_mass_kgs, L_mid, T_celsius, P_bar,
            flooding_fraction, mu_L_Pas, sigma_Nm, rho_L_kgm3,
            removal_target_pct, solvent_wt_pct=solvent_wt_pct,
            target_component=target_component,
        )

        if abs(Z_mid - Z_target) < tol:
            converged = True
            break

        if Z_mid > Z_target:
            # Need more L to shorten the column
            L_lo = L_mid
        else:
            # Need less L to lengthen the column
            L_hi = L_mid

    return L_mid, converged, n_iter


# ── Public API ────────────────────────────────────────────────────────────────


def design_scrubber(
    gas_mixture: List[Dict[str, Any]],
    solvent_name: str,
    packing_name: str,
    removal_target_pct: float = 90.0,
    G_mass_kgs: float = 1.0,
    L_mass_kgs: float = 3.0,
    T_celsius: float = 40.0,
    P_bar: float = 1.01325,
    flooding_fraction: float = 0.70,
    mu_L_Pas: float = 1.0e-3,
    sigma_Nm: float = 0.072,
    rho_L_kgm3: float = 998.0,
    solve_for: str = "Z",
    Z_packed_m: Optional[float] = None,
    target_component: Optional[str] = None,
    solvent_wt_pct: float = 100.0,
) -> Dict[str, Any]:
    """Design a multi-component gas scrubber.

    Parameters
    ----------
    gas_mixture : list of dict
        Each dict has: {name: str, mol_percent: float}
    solvent_name : str
        Solvent name (e.g. "Monoethanolamine", "Water").
    packing_name : str
        Packing name from database.
    removal_target_pct : float
        Target removal percentage for the dominant acid gas.
        Required for solve_for="Z" and "L". Ignored for "eta".
    G_mass_kgs : float
        Gas mass flow rate [kg/s].
    L_mass_kgs : float
        Liquid mass flow rate [kg/s].
        Required for solve_for="Z" and "eta". Ignored for "L".
    T_celsius : float
        Operating temperature [°C].
    P_bar : float
        Operating pressure [bar].
    flooding_fraction : float
        Design fraction of flooding velocity.
    mu_L_Pas : float
        Liquid viscosity [Pa·s].
    sigma_Nm : float
        Surface tension [N/m].
    rho_L_kgm3 : float
        Liquid density [kg/m³].
    solve_for : str
        Which variable to compute: "Z" (height), "eta" (removal), "L" (solvent flow).
    Z_packed_m : float or None
        Known packed height [m]. Required when solve_for in ("eta", "L").

    Returns
    -------
    dict
        Complete scrubber design with per-component results.
    """
    # ── Validate parameters
    if solve_for not in ("Z", "eta", "L"):
        raise ValueError(f"solve_for must be 'Z', 'eta', or 'L', got '{solve_for}'")
    if solve_for in ("eta", "L") and (Z_packed_m is None or Z_packed_m <= 0):
        raise ValueError(f"Z_packed_m must be a positive number when solve_for='{solve_for}'")

    # ── Mode 3: bisect for L first
    bisection_converged = None
    bisection_iterations = None
    computed_L_kgs = None

    if solve_for == "L":
        L_result, bisection_converged, bisection_iterations = _bisect_for_L(
            gas_mixture=gas_mixture,
            solvent_name=solvent_name,
            packing_name=packing_name,
            G_mass_kgs=G_mass_kgs,
            T_celsius=T_celsius,
            P_bar=P_bar,
            flooding_fraction=flooding_fraction,
            mu_L_Pas=mu_L_Pas,
            sigma_Nm=sigma_Nm,
            rho_L_kgm3=rho_L_kgm3,
            removal_target_pct=removal_target_pct,
            Z_target=Z_packed_m,
            solvent_wt_pct=solvent_wt_pct,
            target_component=target_component,
        )
        L_mass_kgs = L_result
        computed_L_kgs = L_result

    # ── Prepare system (common for all modes)
    ctx = _prepare_system(
        gas_mixture, solvent_name, packing_name,
        G_mass_kgs, L_mass_kgs,
        T_celsius, P_bar, flooding_fraction,
        mu_L_Pas, sigma_Nm, rho_L_kgm3,
        solvent_wt_pct=solvent_wt_pct,
    )

    # ── Acid gas analysis
    if solve_for == "eta":
        # For Mode 2, we still need H_OG per component. Use a high dummy target
        # so that NTU calculations don't cap removal.
        acid_gas_results, _, max_NTU, max_HOG, dominant_component = _compute_acid_gas_analysis(
            ctx, 99.0, target_component=target_component,
        )
        Z_design = Z_packed_m
    else:
        acid_gas_results, Z_design_computed, max_NTU, max_HOG, dominant_component = _compute_acid_gas_analysis(
            ctx, removal_target_pct, target_component=target_component,
        )
        if solve_for == "Z":
            Z_design = Z_design_computed
        else:  # solve_for == "L"
            Z_design = Z_packed_m

    # ── Back-calculate removals at the design height
    exit_gas, total_absorbed_mol_s, lines, dom_comp_name = _backcalc_at_height(
        ctx, acid_gas_results, Z_design, removal_target_pct,
    )
    if dom_comp_name and not target_component:
        dominant_component = dom_comp_name

    # ── Compute actual removal of dominant component (for Mode 2 output)
    computed_removal_pct = None
    if solve_for == "eta" and dominant_component:
        dom_exit = next((g for g in exit_gas if g["name"] == dominant_component), None)
        if dom_exit:
            computed_removal_pct = dom_exit["removal_pct"]

    # ── Total pressure drop
    hyd_result = ctx["hyd_result"]
    packing = ctx["packing"]
    dP_total = hyd_result["pressure_drop_Pa_m"] * Z_design if Z_design > 0 else 0.0

    Z_hetp = max_NTU * packing["hetp"] if max_NTU > 0 else 0.0

    result = {
        # System
        "solvent": solvent_name,
        "packing": packing_name,
        "T_celsius": T_celsius,
        "P_bar": P_bar,
        "removal_target_pct": computed_removal_pct if solve_for == "eta" else removal_target_pct,

        # Gas properties
        "mixture_MW": round(ctx["mixture_MW"], 3),
        "rho_G_kgm3": round(ctx["rho_G"], 4),
        "rho_L_kgm3": rho_L_kgm3,
        "G_mol_per_s": round(ctx["G_mol"], 2),
        "L_mol_per_s": round(ctx["L_mol"], 2),

        # Column
        "D_column_m": hyd_result["D_column_m"],
        "D_column_mm": hyd_result["D_column_mm"],
        "A_column_m2": hyd_result["A_column_m2"],
        "Z_design_m": round(Z_design, 3),
        "Z_hetp_m": round(Z_hetp, 3),
        "dominant_component": dominant_component,

        # Hydraulic
        "u_flood_ms": hyd_result["u_flood_ms"],
        "u_design_ms": hyd_result["u_design_ms"],
        "flooding_fraction": hyd_result["flooding_fraction"],
        "dP_per_m_Pa": hyd_result["pressure_drop_Pa_m"],
        "dP_total_Pa": round(dP_total, 1),
        "dP_total_mbar": round(dP_total / 100.0, 2),
        "wetting_adequate": hyd_result["wetting_adequate"],

        # Per-component results
        "acid_gas_analysis": acid_gas_results,

        # Exit compositions
        "exit_gas": exit_gas,
        "total_absorbed_mol_s": round(total_absorbed_mol_s, 6),

        # Operating lines (dominant component)
        "lines": lines,

        # Solve mode info
        "solve_mode": solve_for,
        "target_component": target_component,
        "solvent_wt_pct": solvent_wt_pct,
    }

    # Mode-specific outputs
    if solve_for == "eta":
        result["computed_removal_pct"] = computed_removal_pct
    if solve_for == "L":
        result["computed_L_kgs"] = computed_L_kgs
        result["L_mass_kgs_input"] = computed_L_kgs
        result["bisection_converged"] = bisection_converged
        result["bisection_iterations"] = bisection_iterations

    return result
