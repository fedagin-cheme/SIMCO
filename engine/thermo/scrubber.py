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
    absorption_factor,
    onda_kG_a,
    onda_kL_a,
    overall_HTU,
    operating_equilibrium_lines,
)

R_GAS = 8.314  # J/(mol·K)


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
) -> Dict[str, Any]:
    """Design a multi-component gas scrubber.

    Parameters
    ----------
    gas_mixture : list of dict
        Each dict has: {name: str, mol_percent: float}
        e.g. [{"name": "Nitrogen", "mol_percent": 73},
              {"name": "Carbon dioxide", "mol_percent": 12}, ...]
    solvent_name : str
        Solvent name (e.g. "Monoethanolamine", "Water").
    packing_name : str
        Packing name from database.
    removal_target_pct : float
        Target removal percentage for the dominant acid gas.
    G_mass_kgs, L_mass_kgs : float
        Gas and liquid mass flow rates [kg/s].
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

    Returns
    -------
    dict
        Complete scrubber design with per-component results.
    """
    db = get_db()
    T_K = T_celsius + 273.15
    P_Pa = P_bar * 1e5

    # ── Resolve packing
    packing = db.get_packing(packing_name)
    if packing is None:
        raise ValueError(f"Packing '{packing_name}' not found in database")

    # ── Compute gas mixture properties
    total_mol = sum(g["mol_percent"] for g in gas_mixture)
    if abs(total_mol - 100.0) > 1.0:
        raise ValueError(f"Gas mixture mol% sum = {total_mol:.1f}, must be ~100%")

    # Resolve each component
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

    # ── Hydraulic design (column diameter)
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

    # ── Per-component mass transfer analysis
    solv_id = _solvent_id(solvent_name)

    # Approximate molar flows from mass flows
    G_mol = G_mass_kgs / (mixture_MW / 1000.0)  # mol/s
    L_mol = L_mass_kgs / (rho_L_kgm3 / 55500.0 * rho_L_kgm3 / 1000.0)  # rough estimate
    # Better: L_mol from MW of solvent
    solvent_comp = db.get_compound(solvent_name)
    if solvent_comp:
        L_mol = L_mass_kgs / (solvent_comp["mw"] / 1000.0)

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
            # No Henry data → skip (carrier gas behavior)
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

        # Enhancement factor
        kinetics = db.get_kinetics(comp["id"], solv_id)
        E = kinetics["enhancement_factor_E"] if kinetics else 1.0
        D_G_val = kinetics["D_G_m2s"] if kinetics else 1.5e-5
        D_L_val = kinetics["D_L_m2s"] if kinetics else 1.5e-9

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
        # For A < 1 as NTU→∞: y_out_min ≈ y_in × (1 - A) (dilute limit)
        removal_capped = False
        if A < 1.0:
            max_removal = A  # approximate max removal fraction when A < 1
            if removal_frac > max_removal * 0.95:  # leave 5% margin
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
        })

        if Z_comp > max_NTU * max_HOG if max_HOG > 0 else 0:
            pass
        # Track the dominant (controlling) component
        if NTU > 0 and H_OG > 0 and Z_comp > (max_NTU * max_HOG if dominant_component else 0):
            max_NTU = NTU
            max_HOG = H_OG
            dominant_component = comp["name"]

    # ── Design height = max Z across all acid gases
    Z_design = max((r["Z_required_m"] for r in acid_gas_results if r.get("Z_required_m")), default=0.0)
    Z_hetp = max_NTU * packing["hetp"] if max_NTU > 0 else 0.0

    # ── Back-calculate actual removal at Z_design for each component
    exit_gas = []
    total_absorbed_mol_s = 0.0

    for comp in components:
        ag = next((r for r in acid_gas_results if r["name"] == comp["name"] and r.get("status") == "calculated"), None)

        if ag and ag["H_OG_m"] > 0 and Z_design > 0:
            # Actual NTU at design height
            actual_NTU = Z_design / ag["H_OG_m"]
            A = ag["A_factor"]
            m = ag["m_eq"]

            # Back-calculate y_out from Kremser: y_out = y_in / [(A^NTU)(1 - 1/A) + 1/A]
            # when A ≠ 1
            y_in_val = comp["mol_fraction"]
            if abs(A - 1.0) < 1e-6:
                y_out_actual = y_in_val / (1.0 + actual_NTU)
            else:
                denominator = (A ** actual_NTU) * (1.0 - 1.0 / A) + 1.0 / A
                y_out_actual = y_in_val / denominator if denominator > 0 else y_in_val

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
        else:
            # Carrier gas or no data — passes through
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

    # Total pressure drop
    dP_total = hyd_result["pressure_drop_Pa_m"] * Z_design if Z_design > 0 else 0.0

    # Operating lines for the dominant component
    dom_ag = next((r for r in acid_gas_results if r["name"] == dominant_component and r.get("status") == "calculated"), None)
    lines = None
    if dom_ag and dom_ag["m_eq"] and dom_ag["A_factor"]:
        dom_comp = next((c for c in components if c["name"] == dominant_component), None)
        if dom_comp:
            lines = operating_equilibrium_lines(
                y_in=dom_comp["mol_fraction"],
                y_out=dom_comp["mol_fraction"] * (1 - removal_target_pct / 100),
                m=dom_ag["m_eq"],
                A=dom_ag["A_factor"],
            )

    return {
        # System
        "solvent": solvent_name,
        "packing": packing_name,
        "T_celsius": T_celsius,
        "P_bar": P_bar,
        "removal_target_pct": removal_target_pct,

        # Gas properties
        "mixture_MW": round(mixture_MW, 3),
        "rho_G_kgm3": round(rho_G, 4),
        "rho_L_kgm3": rho_L_kgm3,
        "G_mol_per_s": round(G_mol, 2),
        "L_mol_per_s": round(L_mol, 2),

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
    }
