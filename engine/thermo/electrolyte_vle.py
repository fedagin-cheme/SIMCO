"""
Electrolyte VLE — Boiling Point Elevation & Vapor Pressure Depression.

For non-volatile electrolyte + water systems (NaOH, K₂CO₃, etc.), the VLE
reduces to water activity depression:

    P_water = a_w × P°_water(T)

which manifests as boiling point elevation (BPE):

    T_boil(w, P) = T_sat_water(P) + BPE(w, P)

Approach:
    1. BPE at 1 atm is stored as polynomial fit to handbook data
    2. Pressure correction via Dühring rule scaling
    3. Vapor pressure from modified Raoult's law with water activity

Data Sources:
    - NaOH: OxyChem Caustic Soda Handbook, JSIA Safe Handling of Caustic Soda
    - K₂CO₃: Armand Products Potassium Carbonate Handbook
    - Steam tables: Antoine equation for water
"""

import math
import numpy as np
from typing import Dict, List, Optional, Tuple

from engine.thermo.antoine import (
    antoine_pressure,
    antoine_temperature,
    ANTOINE_COEFFICIENTS,
)


# ── BPE data at 1 atm (760 mmHg = 101325 Pa) ───────────────────────────────
# Format: (w_percent, T_boil_celsius) from handbook curves
# These are engineering-grade data points read from published graphs/tables.

_BPE_DATA = {
    "NaOH": {
        "name": "Sodium Hydroxide",
        "formula": "NaOH",
        "mw": 40.00,
        "max_wt_pct": 50.0,
        # (wt%, boiling point °C at 1 atm)
        "data": [
            (0.0, 100.0),
            (5.0, 102.2),
            (10.0, 104.6),
            (15.0, 107.5),
            (20.0, 111.1),
            (25.0, 115.5),
            (30.0, 120.8),
            (35.0, 127.1),
            (40.0, 134.6),
            (45.0, 143.5),
            (50.0, 153.9),
        ],
    },
    "K2CO3": {
        "name": "Potassium Carbonate",
        "formula": "K₂CO₃",
        "mw": 138.21,
        "max_wt_pct": 50.0,
        # (wt%, boiling point °C at 1 atm)
        "data": [
            (0.0, 100.0),
            (5.0, 100.5),
            (10.0, 101.2),
            (15.0, 102.2),
            (20.0, 103.5),
            (25.0, 105.2),
            (30.0, 107.5),
            (35.0, 110.3),
            (40.0, 114.0),
            (45.0, 118.5),
            (50.0, 124.0),
        ],
    },
}


# ── Polynomial fits ──────────────────────────────────────────────────────────
# Fit once on import: BPE(w) = T_boil(w) - 100 = a₀ + a₁w + a₂w² + a₃w³

_BPE_POLY: Dict[str, np.poly1d] = {}
_TBOIL_POLY: Dict[str, np.poly1d] = {}


def _fit_polynomials():
    """Fit BPE polynomials to handbook data at 1 atm."""
    for solute, info in _BPE_DATA.items():
        ws = np.array([pt[0] for pt in info["data"]])
        ts = np.array([pt[1] for pt in info["data"]])
        bpe = ts - 100.0  # boiling point elevation above pure water

        # 3rd order polynomial gives excellent fit for these smooth curves
        coeffs = np.polyfit(ws, bpe, 3)
        _BPE_POLY[solute] = np.poly1d(coeffs)

        # Also store T_boil directly
        coeffs_t = np.polyfit(ws, ts, 3)
        _TBOIL_POLY[solute] = np.poly1d(coeffs_t)


_fit_polynomials()


# ── Helper: water saturation temperature ─────────────────────────────────────

def _water_tsat(P_pa: float) -> float:
    """
    Saturation temperature of pure water at pressure P (Pa).
    Uses Antoine equation (water_high coefficients for broader range).
    """
    A, B, C = ANTOINE_COEFFICIENTS["water_high"][:3]
    return antoine_temperature(P_pa, A, B, C)


def _water_psat(T_celsius: float) -> float:
    """Saturation pressure of pure water at T (°C) in Pa."""
    A, B, C = ANTOINE_COEFFICIENTS["water_high"][:3]
    return antoine_pressure(T_celsius, A, B, C)


# ── Public API ───────────────────────────────────────────────────────────────

def _normalize_solute(solute: str) -> str:
    """Normalize solute identifier to match _BPE_DATA keys."""
    s = solute.strip().replace("₂", "2").replace("₃", "3")
    # Try exact match first
    if s in _BPE_DATA:
        return s
    # Try case-insensitive match
    for key in _BPE_DATA:
        if s.lower() == key.lower():
            return key
    raise ValueError(f"Unknown electrolyte: {solute}. Available: {list(_BPE_DATA.keys())}")


def get_available_electrolytes() -> List[Dict]:
    """Return list of available electrolyte solutes."""
    result = []
    for key, info in _BPE_DATA.items():
        result.append({
            "id": key,
            "name": info["name"],
            "formula": info["formula"],
            "mw": info["mw"],
            "max_wt_pct": info["max_wt_pct"],
        })
    return result


def boiling_point(solute: str, w_percent: float, P_pa: float = 101325.0) -> float:
    """
    Boiling point of aqueous electrolyte solution.

    Parameters
    ----------
    solute : str
        Electrolyte identifier ('NaOH' or 'K2CO3').
    w_percent : float
        Mass fraction of solute in percent (0-50 typical).
    P_pa : float
        Total pressure in Pascals (default: 1 atm = 101325 Pa).

    Returns
    -------
    float
        Boiling point in °C.
    """
    solute = _normalize_solute(solute)
    if solute not in _BPE_POLY:
        raise ValueError(f"Unknown electrolyte: {solute}. Available: {list(_BPE_POLY.keys())}")

    w_percent = max(0.0, min(w_percent, _BPE_DATA[solute]["max_wt_pct"]))

    # BPE at 1 atm from polynomial
    bpe_1atm = float(_BPE_POLY[solute](w_percent))
    bpe_1atm = max(0.0, bpe_1atm)

    # Pure water saturation temperature at the given pressure
    T_sat_water = _water_tsat(P_pa)

    # Dühring rule: BPE scales approximately with T_sat ratio
    # BPE(P) ≈ BPE(1atm) × (T_sat(P) + 273.15) / (100 + 273.15)
    duhring_factor = (T_sat_water + 273.15) / 373.15
    bpe_at_P = bpe_1atm * duhring_factor

    return T_sat_water + bpe_at_P


def vapor_pressure(solute: str, w_percent: float, T_celsius: float) -> float:
    """
    Vapor pressure of water above an aqueous electrolyte solution.

    Uses modified Raoult's law: P_water = a_w × P°_water(T)
    where a_w is the water activity derived from the BPE correlation.

    Parameters
    ----------
    solute : str
        Electrolyte identifier.
    w_percent : float
        Mass fraction of solute in percent.
    T_celsius : float
        Temperature in °C.

    Returns
    -------
    float
        Vapor pressure in Pa (only water vapor — solute is non-volatile).
    """
    solute = _normalize_solute(solute)
    if solute not in _BPE_POLY:
        raise ValueError(f"Unknown electrolyte: {solute}")

    w_percent = max(0.0, min(w_percent, _BPE_DATA[solute]["max_wt_pct"]))

    # Pure water saturation pressure
    P_water_pure = _water_psat(T_celsius)

    if w_percent < 0.01:
        return P_water_pure

    # Water activity from BPE: at the boiling point, P_water = P_total
    # So a_w = P_total / P°_water(T_boil)
    # For general T: a_w ≈ exp(-ΔH_vap × BPE / (R × T² ))
    # Simpler approach: a_w from Clausius-Clapeyron approximation
    bpe_1atm = max(0.0, float(_BPE_POLY[solute](w_percent)))
    T_boil_1atm = 100.0 + bpe_1atm  # °C

    # Water activity: a_w = P°_water(100°C) / P°_water(T_boil)
    P_water_100 = _water_psat(100.0)
    P_water_tboil = _water_psat(T_boil_1atm)
    a_w = P_water_100 / P_water_tboil if P_water_tboil > 0 else 1.0
    a_w = min(1.0, max(0.0, a_w))

    return a_w * P_water_pure


def generate_bpe_curve(
    solute: str,
    P_pa: float = 101325.0,
    n_points: int = 51,
) -> Dict:
    """
    Generate boiling point elevation curve.

    Returns
    -------
    dict with:
        - w_percent: list of concentration values
        - T_boil: list of boiling temperatures (°C)
        - bpe: list of BPE values (°C above pure water)
        - T_water: pure water boiling point at this pressure
    """
    solute_key = _normalize_solute(solute)
    if solute_key not in _BPE_DATA:
        raise ValueError(f"Unknown electrolyte: {solute_key}")

    info = _BPE_DATA[solute_key]
    w_max = info["max_wt_pct"]
    ws = np.linspace(0, w_max, n_points).tolist()
    T_water = _water_tsat(P_pa)
    ts = [boiling_point(solute_key, w, P_pa) for w in ws]
    bpes = [t - T_water for t in ts]

    return {
        "solute": solute_key,
        "solute_name": info["name"],
        "formula": info["formula"],
        "P_pa": P_pa,
        "T_water": round(T_water, 2),
        "w_percent": [round(w, 2) for w in ws],
        "T_boil": [round(t, 2) for t in ts],
        "bpe": [round(b, 2) for b in bpes],
    }


def generate_vp_curve(
    solute: str,
    T_celsius: float = 100.0,
    n_points: int = 51,
) -> Dict:
    """
    Generate vapor pressure depression curve at fixed temperature.

    Returns
    -------
    dict with:
        - w_percent: list of concentration values
        - P_water: list of water vapor pressures (Pa)
        - P_pure: pure water vapor pressure at this temperature
        - vpd: list of vapor pressure depression values (Pa)
    """
    solute_key = _normalize_solute(solute)
    if solute_key not in _BPE_DATA:
        raise ValueError(f"Unknown electrolyte: {solute_key}")

    info = _BPE_DATA[solute_key]
    w_max = info["max_wt_pct"]
    ws = np.linspace(0, w_max, n_points).tolist()
    P_pure = _water_psat(T_celsius)
    ps = [vapor_pressure(solute_key, w, T_celsius) for w in ws]
    vpds = [P_pure - p for p in ps]

    return {
        "solute": solute_key,
        "solute_name": info["name"],
        "formula": info["formula"],
        "T_celsius": T_celsius,
        "P_pure_water": round(P_pure, 1),
        "w_percent": [round(w, 2) for w in ws],
        "P_water": [round(p, 1) for p in ps],
        "vpd": [round(d, 1) for d in vpds],
    }


def calculate_operating_point(
    solute: str,
    w_percent: float,
    T_celsius: float = None,
    P_pa: float = None,
) -> Dict:
    """
    Calculate a single operating point for an electrolyte solution.

    Provide either T or P (not both). The other is calculated.

    Returns
    -------
    dict with T_boil, P_water, bpe, a_w, etc.
    """
    solute_key = _normalize_solute(solute)
    if solute_key not in _BPE_DATA:
        raise ValueError(f"Unknown electrolyte: {solute_key}")

    info = _BPE_DATA[solute_key]
    w_percent = max(0.0, min(w_percent, info["max_wt_pct"]))

    if P_pa is not None:
        # Given P → find T_boil
        T_boil = boiling_point(solute_key, w_percent, P_pa)
        P_water = vapor_pressure(solute_key, w_percent, T_boil)
        T_water = _water_tsat(P_pa)
    elif T_celsius is not None:
        # Given T → find P_water
        P_water = vapor_pressure(solute_key, w_percent, T_celsius)
        T_boil = T_celsius  # this IS the temperature
        T_water = T_celsius  # for reference
        P_pa = _water_psat(T_celsius)  # pure water pressure at this T
    else:
        # Default: 1 atm
        P_pa = 101325.0
        T_boil = boiling_point(solute_key, w_percent, P_pa)
        P_water = vapor_pressure(solute_key, w_percent, T_boil)
        T_water = _water_tsat(P_pa)

    P_pure_at_Tboil = _water_psat(T_boil)
    a_w = P_water / P_pure_at_Tboil if P_pure_at_Tboil > 0 else 1.0
    bpe = T_boil - _water_tsat(P_pa) if P_pa else 0

    return {
        "solute": solute_key,
        "solute_name": info["name"],
        "formula": info["formula"],
        "w_percent": round(w_percent, 2),
        "T_boil_celsius": round(T_boil, 2),
        "P_water_pa": round(P_water, 1),
        "P_water_kpa": round(P_water / 1000, 3),
        "bpe_celsius": round(bpe, 2),
        "water_activity": round(a_w, 4),
        "P_total_pa": round(P_pa, 1) if P_pa else None,
    }
