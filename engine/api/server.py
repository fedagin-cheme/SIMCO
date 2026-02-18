from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="SIMCO Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "engine": "SIMCO v0.1.0"}

class BubbleDewRequest(BaseModel):
    component: str
    temperature_c: float
    pressure_bar: float

@app.post("/api/vle/bubble-dew")
def bubble_dew(req: BubbleDewRequest):
    try:
        from engine.thermo.antoine import antoine_pressure, antoine_temperature, get_antoine_coefficients
        coeffs = get_antoine_coefficients(req.component)
        if not coeffs:
            raise HTTPException(status_code=404, detail=f"Component '{req.component}' not found in database")
        A, B, C, T_min, T_max = coeffs
        P_pa = req.pressure_bar * 1e5
        bubble_T = antoine_temperature(P_pa, A, B, C)
        sat_P = antoine_pressure(req.temperature_c, A, B, C)
        return {
            "component": req.component,
            "temperature_c": req.temperature_c,
            "pressure_bar": req.pressure_bar,
            "bubble_temperature_c": round(bubble_T, 3),
            "dew_temperature_c": round(bubble_T, 3),
            "bubble_pressure_bar": round(sat_P / 1e5, 5),
            "saturation_pressure_bar": round(sat_P / 1e5, 5),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
