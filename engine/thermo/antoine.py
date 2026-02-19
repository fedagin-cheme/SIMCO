from typing import Optional, Dict, Any, List

# mmHg -> Pa conversion factor
MMHG_TO_PA = 133.322

# --- Antoine Coefficients -------------------------------------------------
# Format: log10(P_mmHg) = A - B/(T_C + C)
# Tuple: (A, B, C, T_min_C, T_max_C)
# Sources: NIST WebBook, Coulson & Richardson (converted), Yaws

ANTOINE_COEFFICIENTS = {
    # Physical solvents / diluents
    "water":      (8.07131, 1730.630, 233.426,   1.0,  100.0),
    "water_high": (8.14019, 1810.940, 244.485,  60.0,  150.0),
    "methanol":   (8.08097, 1582.271, 239.726, -10.0,   84.0),
    # Amine solvents
    "mea":        (7.1676, 1408.873, 157.057,  65.5,  171.0),
    "mdea":       (7.1773, 1835.461, 180.000,  60.0,  260.0),
    # Acid gases
    "co2":        (9.6874, 1301.679, 269.656,-118.9,  -77.3),
    "h2s":        (6.9939,  768.132, 247.090, -83.0,  -43.0),
    "so2":        (7.2823,  999.898, 237.180, -78.0,    7.0),
    "ammonia":    (7.3605,  926.133, 240.170, -94.0,  -12.0),
    "hcl":        (7.1676,  744.489, 258.700,-136.0,  -73.0),
    "no":         (8.7430,  682.937, 268.270,-178.0, -133.0),
    "no2":        (8.9171, 1798.539, 276.800, -43.0,   47.0),
    # Carrier / inert gases
    "nitrogen":   (6.4945,  255.678, 266.550,-219.0, -183.0),
    "oxygen":     (6.6914,  319.011, 266.700,-210.0, -173.0),
    "methane":    (6.8646,  443.028, 272.660,-182.5,  -83.2),
    # Validation set (common organics)
    "ethanol":    (8.11220, 1592.864, 226.184,  20.0,   93.0),
    "benzene":    (6.90565, 1211.033, 220.790,   8.0,   80.0),
    "toluene":    (6.95087, 1342.310, 219.187,   6.0,  137.0),
    "acetone":    (7.11714, 1210.595, 229.664, -13.0,   55.0),
    "n_hexane":   (6.87776, 1171.530, 224.366, -25.0,   92.0),
    "n_heptane":  (6.89385, 1264.370, 216.636,  -2.0,  127.0),
    "chloroform": (6.95465, 1170.966, 226.232, -10.0,   60.0),
}

# --- Critical Properties --------------------------------------------------
# (Tc_celsius, Pc_bar)
# Sources: NIST, Perry s, Coulson & Richardson

CRITICAL_PROPERTIES = {
    "water":      (373.95, 220.64),
    "methanol":   (239.45,  80.84),
    "mea":        (405.05,  44.50),
    "mdea":       (404.85,  38.70),
    "co2":        ( 30.98,  73.77),
    "h2s":        (100.05,  89.63),
    "so2":        (157.49,  78.84),
    "ammonia":    (132.45, 112.80),
    "hcl":        ( 51.45,  83.10),
    "no":         (-93.15,  64.80),
    "no2":        (158.25, 101.30),
    "nitrogen":   (-146.96, 33.96),
    "oxygen":     (-118.57, 50.43),
    "methane":    (-82.59,  45.99),
    "ethanol":    (241.56,  62.68),
    "benzene":    (288.87,  48.98),
    "toluene":    (318.60,  41.06),
    "acetone":    (235.05,  47.01),
    "n_hexane":   (234.67,  30.25),
    "n_heptane":  (267.01,  27.40),
    "chloroform": (263.20,  54.72),
}

# --- Compound Registry ----------------------------------------------------
# Full metadata for every compound in SIMCO.

COMPOUND_DATA = {
    # -- Acid Gases / Gases to Remove ------------------------------------
    "co2": {
        "name": "Carbon Dioxide",
        "formula": "CO\u2082",
        "cas": "124-38-9",
        "mw": 44.01,
        "category": "acid_gas",
        "description": "Primary target in post-combustion capture and natural gas sweetening.",
    },
    "h2s": {
        "name": "Hydrogen Sulfide",
        "formula": "H\u2082S",
        "cas": "7783-06-4",
        "mw": 34.08,
        "category": "acid_gas",
        "description": "Toxic acid gas removed in gas sweetening (Claus process feed).",
    },
    "so2": {
        "name": "Sulfur Dioxide",
        "formula": "SO\u2082",
        "cas": "7446-09-5",
        "mw": 64.06,
        "category": "acid_gas",
        "description": "Flue gas desulfurization (FGD) target from power plants and smelters.",
    },
    "ammonia": {
        "name": "Ammonia",
        "formula": "NH\u2083",
        "cas": "7664-41-7",
        "mw": 17.03,
        "category": "acid_gas",
        "description": "Basic gas scrubbed from fertilizer off-gas, SCR slip, and waste streams.",
    },
    "hcl": {
        "name": "Hydrogen Chloride",
        "formula": "HCl",
        "cas": "7647-01-0",
        "mw": 36.46,
        "category": "acid_gas",
        "description": "Strong acid gas from waste incineration and chlorinated feedstocks.",
    },
    "no": {
        "name": "Nitric Oxide",
        "formula": "NO",
        "cas": "10102-43-9",
        "mw": 30.01,
        "category": "acid_gas",
        "description": "Primary NOx component in combustion flue gas.",
    },
    "no2": {
        "name": "Nitrogen Dioxide",
        "formula": "NO\u2082",
        "cas": "10102-44-0",
        "mw": 46.01,
        "category": "acid_gas",
        "description": "Secondary NOx component; more soluble and reactive than NO.",
    },
    # -- Amine Solvents --------------------------------------------------
    "mea": {
        "name": "Monoethanolamine",
        "formula": "C\u2082H\u2087NO",
        "cas": "141-43-5",
        "mw": 61.08,
        "category": "amine_solvent",
        "description": "Primary amine, benchmark solvent for post-combustion CO\u2082 capture.",
    },
    "mdea": {
        "name": "Methyldiethanolamine",
        "formula": "C\u2085H\u2081\u2083NO\u2082",
        "cas": "105-59-9",
        "mw": 119.16,
        "category": "amine_solvent",
        "description": "Tertiary amine, selective for H\u2082S over CO\u2082 in gas sweetening.",
    },
    # -- Physical Solvents / Diluents ------------------------------------
    "water": {
        "name": "Water",
        "formula": "H\u2082O",
        "cas": "7732-18-5",
        "mw": 18.015,
        "category": "physical_solvent",
        "description": "Universal diluent for amine solutions; also used in SO\u2082/HCl scrubbing.",
    },
    "methanol": {
        "name": "Methanol",
        "formula": "CH\u2083OH",
        "cas": "67-56-1",
        "mw": 32.04,
        "category": "physical_solvent",
        "description": "Physical solvent (Rectisol process) for CO\u2082 and H\u2082S at low temperatures.",
    },
    # -- Carrier / Inert Gases -------------------------------------------
    "nitrogen": {
        "name": "Nitrogen",
        "formula": "N\u2082",
        "cas": "7727-37-9",
        "mw": 28.01,
        "category": "carrier_gas",
        "description": "Major component of flue gas (~79%% of air).",
    },
    "oxygen": {
        "name": "Oxygen",
        "formula": "O\u2082",
        "cas": "7782-44-7",
        "mw": 32.00,
        "category": "carrier_gas",
        "description": "Present in flue gas; causes amine degradation in absorbers.",
    },
    "methane": {
        "name": "Methane",
        "formula": "CH\u2084",
        "cas": "74-82-8",
        "mw": 16.04,
        "category": "carrier_gas",
        "description": "Primary component of natural gas streams being sweetened.",
    },
    # -- Validation Set (common organics) --------------------------------
    "ethanol": {
        "name": "Ethanol",
        "formula": "C\u2082H\u2085OH",
        "cas": "64-17-5",
        "mw": 46.07,
        "category": "organic",
        "description": "Common organic; used for model validation.",
    },
    "benzene": {
        "name": "Benzene",
        "formula": "C\u2086H\u2086",
        "cas": "71-43-2",
        "mw": 78.11,
        "category": "organic",
        "description": "Aromatic hydrocarbon; used for model validation.",
    },
    "toluene": {
        "name": "Toluene",
        "formula": "C\u2087H\u2088",
        "cas": "108-88-3",
        "mw": 92.14,
        "category": "organic",
        "description": "Aromatic hydrocarbon; used for model validation.",
    },
    "acetone": {
        "name": "Acetone",
        "formula": "C\u2083H\u2086O",
        "cas": "67-64-1",
        "mw": 58.08,
        "category": "organic",
        "description": "Ketone solvent; used for model validation.",
    },
    "n_hexane": {
        "name": "n-Hexane",
        "formula": "C\u2086H\u2081\u2084",
        "cas": "110-54-3",
        "mw": 86.18,
        "category": "organic",
        "description": "Alkane; used for model validation.",
    },
    "n_heptane": {
        "name": "n-Heptane",
        "formula": "C\u2087H\u2081\u2086",
        "cas": "142-82-5",
        "mw": 100.20,
        "category": "organic",
        "description": "Alkane; used for model validation.",
    },
    "chloroform": {
        "name": "Chloroform",
        "formula": "CHCl\u2083",
        "cas": "67-66-3",
        "mw": 119.38,
        "category": "organic",
        "description": "Chlorinated solvent; used for model validation.",
    },
}

# Category display metadata
CATEGORIES = {
    "acid_gas":         {"label": "Gases to Remove",      "order": 0},
    "amine_solvent":    {"label": "Amine Solvents",       "order": 1},
    "physical_solvent": {"label": "Physical Solvents",    "order": 2},
    "carrier_gas":      {"label": "Carrier / Inert",      "order": 3},
    "organic":          {"label": "Validation Compounds",  "order": 4},
}


# --- Lookup Functions -----------------------------------------------------

def _normalize_key(compound: str) -> str:
    return compound.lower().replace(" ", "_").replace("-", "_")


def get_antoine_coefficients(compound: str):
    return ANTOINE_COEFFICIENTS.get(_normalize_key(compound))


def get_critical_properties(compound: str):
    """Return (Tc_celsius, Pc_bar) or None."""
    return CRITICAL_PROPERTIES.get(_normalize_key(compound))


def get_compound_info(compound: str):
    """Return full compound metadata dict or None."""
    return COMPOUND_DATA.get(_normalize_key(compound))


def get_compounds_by_category(category: str):
    """Return list of compound keys in a given category."""
    return [k for k, v in COMPOUND_DATA.items() if v["category"] == category]


def get_all_compound_details():
    """
    Return full details for every compound: metadata + calculated properties.
    Used by the API to serve the component browser.
    """
    import math
    result = {}
    for key, info in COMPOUND_DATA.items():
        entry = dict(info)
        entry["key"] = key

        # Antoine data
        antoine = ANTOINE_COEFFICIENTS.get(key)
        if antoine:
            A, B, C, T_min, T_max = antoine
            entry["antoine"] = {"A": A, "B": B, "C": C, "T_min": T_min, "T_max": T_max}
            try:
                entry["boiling_point_c"] = round(B / (A - math.log10(760)) - C, 2)
            except (ValueError, ZeroDivisionError):
                entry["boiling_point_c"] = None
        else:
            entry["antoine"] = None
            entry["boiling_point_c"] = None

        # Critical properties
        crit = CRITICAL_PROPERTIES.get(key)
        if crit:
            entry["critical"] = {"Tc_celsius": crit[0], "Pc_bar": crit[1]}
        else:
            entry["critical"] = None

        result[key] = entry
    return result


def validate_conditions(compound: str, temperature_c: float = None, pressure_bar: float = None):
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

        if temperature_c is not None and temperature_c > Tc:
            return (
                f"{compound} is supercritical above {Tc:.1f} \u00b0C. "
                f"No liquid phase exists at {temperature_c} \u00b0C."
            )

        if pressure_bar is not None and pressure_bar > Pc:
            return (
                f"{compound} critical pressure is {Pc:.1f} bar. "
                f"No VLE exists at {pressure_bar} bar."
            )

        if pressure_bar is not None:
            try:
                bubble_T = antoine_temperature(pressure_bar * 1e5, A, B, C)
                if bubble_T > Tc:
                    return (
                        f"{compound} cannot be boiled at {pressure_bar:.4f} bar "
                        f"the required temperature ({bubble_T:.1f} \u00b0C) exceeds "
                        f"the critical point ({Tc:.1f} \u00b0C / {Pc:.1f} bar)."
                    )
            except (ValueError, ZeroDivisionError):
                pass

    if temperature_c is not None and (temperature_c < T_min or temperature_c > T_max):
        return (
            f"Temperature {temperature_c} \u00b0C is outside the Antoine valid range "
            f"for {compound} ({T_min} to {T_max} \u00b0C). Results may be inaccurate."
        )

    return None


def antoine_pressure(T_celsius: float, A: float, B: float, C: float) -> float:
    return MMHG_TO_PA * (10 ** (A - B / (C + T_celsius)))


def antoine_temperature(P_pa: float, A: float, B: float, C: float) -> float:
    import math
    P_mmhg = P_pa / MMHG_TO_PA
    return B / (A - math.log10(P_mmhg)) - C
