# Phase 3B — Packed Column Mass Transfer & Packed Height

## Objective
Calculate the packed height Z required for a given separation, using two methods:
1. **HETP method**: Z = N_stages × HETP (simple, uses DB HETP values)
2. **HTU-NTU method**: Z = H_OG × N_OG (rigorous, for dilute gas absorption)

## Engineering Scope

### Method 1: HETP (Height Equivalent to a Theoretical Plate)
- User specifies number of theoretical stages N
- Z = N × HETP (HETP from packing database)
- Quick preliminary estimate, widely used in industry

### Method 2: HTU-NTU for Dilute Gas Absorption
For dilute systems (y_in < ~5 mol%), the Kremser equation gives NTU analytically:

  N_OG = ln[(y_in/y_out)(1 - 1/A) + 1/A] / ln(A)

where A = L_mol/(m·G_mol) is the absorption factor, m = slope of equilibrium line (Henry's law or y=mx).

HTU from Onda correlation (1968) for gas-phase overall:
  H_OG = H_G + (m·G_mol/L_mol)·H_L

Individual HTUs from Onda mass transfer coefficients:
  k_G·a from gas-phase correlation
  k_L·a from liquid-phase correlation

### Inputs
- y_in: inlet gas mole fraction of target component
- y_out: outlet gas mole fraction (target removal)
- m: equilibrium slope (Henry's constant / P_total, or user-specified)
- L_mol, G_mol: molar flow rates [mol/s]
- Physical properties: rho_G, rho_L, mu_G, mu_L, D_G, D_L, sigma
- Packing: a_p, epsilon, nominal_size

### Outputs
- N_stages (for HETP) or N_OG (for NTU)
- HTU components: H_G, H_L, H_OG
- Packed height Z [m]
- Absorption factor A
- Operating & equilibrium line data for plotting
- Total column pressure drop: ΔP_total = ΔP/Z × Z

---

## Implementation Plan

### Backend (engine/thermo/mass_transfer.py)
- [x] `kremser_NTU(y_in, y_out, A)` — analytical NTU for dilute absorption
- [x] `hetp_height(N_stages, HETP)` — simple Z = N × HETP
- [x] `onda_kG_a(...)` — Onda gas-phase mass transfer coefficient
- [x] `onda_kL_a(...)` — Onda liquid-phase mass transfer coefficient
- [x] `overall_HTU(...)` — H_OG from individual HTUs
- [x] `design_packed_height(...)` — orchestrator for full mass transfer design
- [x] `operating_equilibrium_lines(...)` — generate x-y data for plotting

### API (engine/api/server.py)
- [x] POST `/api/column/mass-transfer` — full mass transfer calculation
- [x] POST `/api/column/hetp-height` — simple HETP-based height

### Tests
- [x] Kremser NTU against hand-calculated examples
- [x] HETP height trivial check
- [x] Onda kG·a and kL·a order of magnitude
- [x] Overall HTU reasonable range (0.3–2.0 m typical)
- [x] Full design integration test
- [x] Operating/equilibrium line data shape
