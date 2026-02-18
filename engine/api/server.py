from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from engine.thermo.antoine import (
    antoine_pressure,
    antoine_temperature,
    get_antoine_coefficients,
    get_critical_properties,
    validate_conditions,
    ANTOINE_COEFFICIENTS,
    CRITICAL_PROPERTIES,
)
from engine.thermo.nrtl import get_nrtl_params, NRTL_BINARY_PARAMS
from engine.api.routes.vle import bubble_point_temperature, bubble_point_pressure, generate_txy_diagram, generate_pxy_diagram

app = FastAPI(title="SIMCO Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "engine": "SIMCO v0.1.0"}


# ─── Component Metadata ─────────────────────────────────────────────────────────

@app.get("/api/compounds")
def list_compounds():
    """List all compounds with Antoine coefficients and critical properties."""
    compounds = []
    for key, (A, B, C, T_min, T_max) in ANTOINE_COEFFICIENTS.items():
        if key == "water_high":
            continue  # skip alt-range entry
        entry = {
            "id": key,
            "T_min_c": T_min,
            "T_max_c": T_max,
        }
        crit = CRITICAL_PROPERTIES.get(key)
        if crit:
            entry["Tc_c"] = crit[0]
            entry["Pc_bar"] = crit[1]
        compounds.append(entry)
    return {"compounds": compounds}


@app.get("/api/vle/binary/pairs")
def list_binary_pairs():
    """List all binary pairs with NRTL parameters available for Txy diagrams."""
    pairs = []
    for (comp1, comp2), (dg12, dg21, alpha) in NRTL_BINARY_PARAMS.items():
        pairs.append({
            "comp1": comp1,
            "comp2": comp2,
            "alpha12": alpha,
        })
    return {"pairs": pairs}


# ─── Pure-Component VLE ──────────────────────────────────────────────────────────

class BubbleDewRequest(BaseModel):
    component: str
    temperature_c: float
    pressure_bar: float


@app.post("/api/vle/bubble-dew")
def bubble_dew(req: BubbleDewRequest):
    """Pure-component saturation calculation (Antoine forward/inverse) with validation."""
    try:
        coeffs = get_antoine_coefficients(req.component)
        if not coeffs:
            raise HTTPException(
                status_code=404,
                detail=f"Component '{req.component}' not found in database",
            )

        # Validate physical conditions
        error = validate_conditions(req.component, req.temperature_c, req.pressure_bar)
        if error:
            # Distinguish hard errors (supercritical) from soft warnings (out of range)
            is_warning = "inaccurate" in error
            if not is_warning:
                raise HTTPException(status_code=422, detail=error)
            # For warnings, we still calculate but include the warning
            warning = error
        else:
            warning = None

        A, B, C, T_min, T_max = coeffs
        P_pa = req.pressure_bar * 1e5
        bubble_T = antoine_temperature(P_pa, A, B, C)
        sat_P = antoine_pressure(req.temperature_c, A, B, C)

        result = {
            "component": req.component,
            "temperature_c": req.temperature_c,
            "pressure_bar": req.pressure_bar,
            "bubble_temperature_c": round(bubble_T, 3),
            "dew_temperature_c": round(bubble_T, 3),
            "bubble_pressure_bar": round(sat_P / 1e5, 5),
            "saturation_pressure_bar": round(sat_P / 1e5, 5),
        }

        if warning:
            result["warning"] = warning

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Binary Mixture VLE ─────────────────────────────────────────────────────────

class BinaryBubblePointRequest(BaseModel):
    comp1: str
    comp2: str
    x1: float
    pressure_bar: float


@app.post("/api/vle/binary/bubble-point")
def binary_bubble_point(req: BinaryBubblePointRequest):
    """Binary mixture bubble point at given x1 and pressure (modified Raoult's law + NRTL)."""
    try:
        P_pa = req.pressure_bar * 1e5
        result = bubble_point_temperature(req.x1, P_pa, req.comp1, req.comp2)
        result["comp1"] = req.comp1
        result["comp2"] = req.comp2
        result["x1"] = req.x1
        result["pressure_bar"] = req.pressure_bar
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TxyDiagramRequest(BaseModel):
    comp1: str
    comp2: str
    pressure_bar: float
    n_points: int = 51


@app.post("/api/vle/binary/txy")
def txy_diagram(req: TxyDiagramRequest):
    """Generate full Txy diagram data for a binary mixture at constant pressure."""
    try:
        P_pa = req.pressure_bar * 1e5
        data = generate_txy_diagram(P_pa, req.comp1, req.comp2, req.n_points)
        # Convert to pressure_bar for consistency
        data["pressure_bar"] = req.pressure_bar
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PxyDiagramRequest(BaseModel):
    comp1: str
    comp2: str
    temperature_c: float
    n_points: int = 51


@app.post("/api/vle/binary/pxy")
def pxy_diagram(req: PxyDiagramRequest):
    """Generate full Pxy diagram data for a binary mixture at constant temperature."""
    try:
        data = generate_pxy_diagram(req.temperature_c, req.comp1, req.comp2, req.n_points)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
