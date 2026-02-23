"""engine.thermo.antoine

Antoine vapor pressure correlations.

All coefficients and compound metadata are fetched from the JSON database
(engine.database.db.ChemicalDatabase). No thermodynamic constants are stored
in this module.

Equation form stored in DB:
    log10(P_mmHg) = A - B / (T_C + C)

Internal API used by the engine/UI keeps the legacy behavior:
    - get_antoine_coefficients(name) -> (A,B,C,TminC,TmaxC)
    - get_critical_properties(name) -> (Tc_C, Pc_bar) | None
    - get_all_compound_details() -> dict for UI
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

from engine.database.db import ChemicalDatabase

# mmHg -> Pa conversion factor
MMHG_TO_PA = 133.322


def antoine_pressure(T_celsius: float, A: float, B: float, C: float) -> float:
    """Return saturation pressure [Pa] at temperature [°C]."""
    # log10(P_mmHg) = A - B/(T + C)
    P_mmhg = 10 ** (A - B / (T_celsius + C))
    return P_mmhg * MMHG_TO_PA


def antoine_temperature(P_pa: float, A: float, B: float, C: float) -> float:
    """Invert Antoine: return temperature [°C] for a given saturation pressure [Pa]."""
    if P_pa <= 0:
        raise ValueError("Pressure must be positive")
    P_mmhg = P_pa / MMHG_TO_PA
    return B / (A - math.log10(P_mmhg)) - C


def get_antoine_coefficients(component: str, T_celsius: float = None) -> Optional[Tuple[float, float, float, float, float]]:
    """Fetch Antoine coefficients for a component.

    If T_celsius is given, select a coefficient set valid at that temperature.
    """
    with ChemicalDatabase() as db:
        rec = db.get_antoine(component, T_celsius=T_celsius)
    if not rec:
        return None
    return (rec["A"], rec["B"], rec["C"], rec["T_min"], rec["T_max"])


def get_critical_properties(component: str) -> Optional[Tuple[float, float]]:
    """Return (Tc_celsius, Pc_bar) if available."""
    with ChemicalDatabase() as db:
        c = db.get_compound(component)
    if not c:
        return None
    tc = c.get("tc")
    pc = c.get("pc")
    if tc is None or pc is None:
        return None
    return (float(tc) - 273.15, float(pc) / 1e5)


def validate_conditions(component: str, temperature_c: float, pressure_bar: float) -> Optional[str]:
    """Basic validation:

    - Warn when Antoine is used outside validity range.
    - Hard error if supercritical (if critical props are available).
    """
    crit = get_critical_properties(component)
    if crit:
        Tc_c, Pc_bar = crit
        if temperature_c > Tc_c and pressure_bar > Pc_bar:
            return f"Requested point is supercritical (Tc={Tc_c:.2f}°C, Pc={Pc_bar:.2f} bar)"

    coeffs = get_antoine_coefficients(component, T_celsius=temperature_c)
    if not coeffs:
        return None
    _, _, _, Tmin, Tmax = coeffs
    if not (Tmin <= temperature_c <= Tmax):
        return f"Temperature {temperature_c:.2f}°C is outside Antoine validity range ({Tmin:.2f} to {Tmax:.2f} °C); results may be inaccurate."
    return None


# UI grouping metadata (non-thermodynamic).
CATEGORIES: Dict[str, Dict[str, Any]] = {
    "acid_gas": {"label": "Acid / Reactive Gases", "order": 1},
    "amine_solvent": {"label": "Amine Solvents", "order": 2},
    "physical_solvent": {"label": "Physical Solvents", "order": 3},
    "carrier_gas": {"label": "Carrier / Inert Gases", "order": 4},
    "organic": {"label": "Common Organics", "order": 5},
    "": {"label": "Other", "order": 99},
}


def get_all_compound_details() -> Dict[str, Dict[str, Any]]:
    """Return a dict keyed by a stable UI key.

    The UI key is normalized from the compound name to match previous behavior.
    """

    def _key(name: str) -> str:
        return name.strip().lower().replace(" ", "_").replace("-", "_")

    out: Dict[str, Dict[str, Any]] = {}
    with ChemicalDatabase() as db:
        compounds = db.list_compounds()
        for c in compounds:
            key = _key(c["name"])
            antoine = db.get_antoine(c["name"])  # any set
            crit = None
            if c.get("tc") is not None and c.get("pc") is not None:
                crit = {
                    "Tc_celsius": float(c["tc"]) - 273.15,
                    "Pc_bar": float(c["pc"]) / 1e5,
                }
            out[key] = {
                "key": key,
                "name": c["name"],
                "formula": c.get("formula") or "",
                "cas": c.get("cas_number") or "",
                "mw": c.get("mw"),
                "category": c.get("category") or "",
                "description": c.get("description") or "",
                "boiling_point_c": (float(c["tb"]) - 273.15) if c.get("tb") is not None else None,
                "antoine": (
                    {
                        "A": antoine["A"],
                        "B": antoine["B"],
                        "C": antoine["C"],
                        "T_min": antoine["T_min"],
                        "T_max": antoine["T_max"],
                    }
                    if antoine
                    else None
                ),
                "critical": crit,
            }
    return out
