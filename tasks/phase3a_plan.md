# Phase 3A — Packed Column Hydraulic Design

## Objective
Size a packed absorption column: given gas/liquid flow rates and a packing selection,
calculate column diameter, flooding velocity, and pressure drop.

## Engineering Scope

### Core Calculations
1. **Flooding velocity** via Generalized Pressure Drop Correlation (GPDC)
   - Sherwood/Eckert flooding line: Y_flood = f(X_flow)
   - X_flow = (L/G) × (ρ_G / ρ_L)^0.5  (flow parameter)
   - Y_flood = (u_G² × F_p × ρ_G) / (g × (ρ_L - ρ_G))  (capacity parameter)
   - Uses packing factor (F_p) from DB

2. **Column diameter** from gas velocity at design % of flooding
   - u_design = fraction × u_flood  (typically 0.6–0.8)
   - A_column = Q_G / u_design
   - D_column = sqrt(4 × A / π)

3. **Pressure drop** via Robbins correlation or GPDC curves
   - ΔP/Z at design conditions (Pa/m or inH₂O/ft)
   - Dry vs irrigated pressure drop

### Input Parameters
- Gas flow rate (kmol/h or m³/s)
- Liquid flow rate (kmol/h or kg/s)
- Gas density ρ_G (kg/m³) — from ideal gas or specified
- Liquid density ρ_L (kg/m³) — specified
- Gas viscosity μ_G (Pa·s) — optional, for pressure drop
- Liquid viscosity μ_L (Pa·s) — optional, for pressure drop
- Operating temperature (°C)
- Operating pressure (bar)
- Packing selection (from DB)
- Design flooding fraction (default 0.7)

### Output
- Flow parameter X
- Flooding velocity u_flood (m/s)
- Design velocity u_design (m/s)
- Column cross-section area (m²)
- Column diameter (m)
- Pressure drop ΔP/Z (Pa/m)
- Minimum wetting rate check

---

## Implementation Plan

### Backend (engine/thermo/column_hydraulics.py)
- [x] `flooding_velocity(F_p, rho_G, rho_L, L_mass, G_mass, mu_L=1e-3, g=9.81)`
- [x] `column_diameter(Q_gas_m3s, u_flood, flooding_fraction=0.7)`
- [x] `pressure_drop_irrigated(u_G, F_p, rho_G, rho_L, L_mass, G_mass, mu_L=1e-3)`
- [x] `minimum_wetting_rate(a_p, sigma=0.072, mu_L=1e-3, rho_L=1000)`
- [x] `design_column(...)` — orchestrator returning full design summary dict

### API (engine/api/server.py)
- [x] POST `/api/column/hydraulic-design` — full design calculation
- [x] GET `/api/packings` — list packings from DB (with ?packing_type= filter)
- [x] GET `/api/packings/{name}` — single packing details

### Tests (engine/tests/test_engine.py)
- [x] Test flooding velocity against Perry's example (Pall Ring 50mm, air-water) — 2.45 m/s ✓
- [x] Test column diameter calculation (round-trip consistency)
- [x] Test pressure drop order of magnitude (100–1000 Pa/m typical range)
- [x] Test minimum wetting rate > 0
- [x] Test with structured packing (Mellapak 250Y from DB)
- [x] 12 new tests, 61 total — all passing

### Verification Data
- Perry's 8th ed., Table 14-16: flooding correlations
- Air-water system at 20°C, 1 atm: ρ_G=1.2 kg/m³, ρ_L=998 kg/m³
- Typical absorber: L/G mass ratio 1–10, column diameter 0.5–3 m
