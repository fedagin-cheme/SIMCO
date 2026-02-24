# SIMCO Architecture

## Overview
SIMCO (Gas Scrubbing & Mass-transfer Calculator) is a desktop application for chemical absorption, gas scrubbing, and stripping simulation. It combines a rigorous Python calculation engine with an Electron + React desktop UI.

## Custom File Format
- Extension: `.smc`
- Format: JSON-based project file containing simulation parameters, results, and metadata (planned)

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Engine | Python 3.10+ / FastAPI | Thermodynamics, mass transfer, REST API |
| Frontend | React + TypeScript + Electron | Desktop UI |
| Styling | Tailwind CSS | Dark engineering theme |
| Build | Vite | Frontend bundling |
| Database | JSON (simco_chemdb.json) | Chemical properties — 89 components, 12 packings |
| VCS | GitHub | `fedagin-cheme/SIMCO` |

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│  Electron Main Process                       │
│  ├── Window management                       │
│  ├── File I/O (.smc save/load)              │
│  └── Spawns Python engine subprocess         │
└──────────────┬──────────────────────────────┘
               │ IPC (preload bridge)
┌──────────────▼──────────────────────────────┐
│  React Renderer (Vite + Tailwind)           │
│  ├── TitleBar (engine status indicator)      │
│  ├── Sidebar (page navigation)               │
│  └── Pages                                   │
│      ├── VLECalculatorPage                   │
│      │   ├── PureComponentView               │
│      │   │   ├── Category tabs (5 groups)    │
│      │   │   ├── Compound browser list       │
│      │   │   ├── Property card (6 sections)  │
│      │   │   └── Quick calculator            │
│      │   ├── BinaryMixtureView               │
│      │   │   ├── Txy / Pxy toggle            │
│      │   │   ├── Phase diagram chart         │
│      │   │   └── xy equilibrium chart        │
│      │   └── ScrubbingSolventView            │
│      │       ├── ElectrolyteView             │
│      │       │   ├── BPE curve chart         │
│      │       │   ├── VP depression chart     │
│      │       │   └── Operating point summary │
│      │       └── AmineSolventView            │
│      │           ├── Txy / Pxy diagrams      │
│      │           └── System summary           │
│      └── ComingSoonPage (placeholder)        │
└──────────────┬──────────────────────────────┘
               │ HTTP (localhost:8742)
┌──────────────▼──────────────────────────────┐
│  FastAPI Engine                              │
│  ├── GET  /health                            │
│  ├── GET  /api/compounds                     │
│  ├── GET  /api/vle/binary/pairs              │
│  ├── POST /api/vle/bubble-dew                │
│  ├── POST /api/vle/binary/bubble-point       │
│  ├── POST /api/vle/binary/txy                │
│  ├── POST /api/vle/binary/pxy                │
│  ├── GET  /api/vle/electrolyte/solutes       │
│  ├── POST /api/vle/electrolyte/bpe-curve     │
│  ├── POST /api/vle/electrolyte/vp-curve      │
│  └── POST /api/vle/electrolyte/operating-point│
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Calculation Modules                         │
│  ├── thermo/antoine.py                       │
│  │   ├── antoine_pressure/temperature()      │
│  │   ├── get_antoine_coefficients() → DB     │
│  │   ├── get_critical_properties() → DB      │
│  │   ├── get_all_compound_details() → DB     │
│  │   └── CATEGORIES (5 UI groups)            │
│  ├── thermo/nrtl.py                          │
│  │   ├── nrtl_gamma() (pure computation)     │
│  │   └── get_nrtl_params() → DB              │
│  ├── thermo/henry.py                         │
│  │   ├── henry_solubility/pressure()         │
│  │   ├── henry_temperature_correction()      │
│  │   └── get_henry_data() → DB              │
│  ├── thermo/electrolyte_vle.py               │
│  │   ├── _BPE_DATA (NaOH, K₂CO₃ handbook)   │
│  │   ├── boiling_point() with Dühring rule   │
│  │   ├── vapor_pressure() via water activity │
│  │   └── generate_bpe/vp_curve()            │
│  └── thermo/ideal_gas.py                     │
│      └── PVnRT utilities (no DB dependency)  │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  JSON Database (simco_chemdb.json)           │
│  ├── components[] (89 entries)               │
│  │   ├── id, name, formula, mw              │
│  │   ├── identifiers (CAS, InChI, SMILES)   │
│  │   ├── critical (Tc_K, Pc_Pa, omega)      │
│  │   ├── category, description              │
│  │   └── correlations[]                     │
│  │       ├── Psat: Antoine_log10_PmmHg_TdegC │
│  │       ├── Tb: constant                    │
│  │       └── Henry_Hpa: Henry constants      │
│  ├── binary_interactions[] (12 entries)      │
│  │   ├── NRTL dg_const (9 pairs)            │
│  │   ├── NRTL tau_AplusBoverT (1 pair: MEA) │
│  │   └── PR kij_const (1 pair: H₂O-CO₂)    │
│  └── packings[] (12 entries)                │
│      ├── type: random | structured           │
│      └── a_m2m3, epsilon, Fp, etc.          │
│                                              │
│  Access: get_db() singleton → cached indices │
│  Indices rebuilt once, reused across calls    │
└─────────────────────────────────────────────┘
```

## Data Architecture

### JSON Database (simco_chemdb.json)
The canonical data source. All thermodynamic parameters live here — no hardcoded dictionaries in Python modules. The `ChemicalDatabase` class provides indexed access with:
- `get_db()` module-level singleton (avoids repeated JSON parsing)
- Class-level `_cache` for the raw JSON data
- Instance-level indices (`_comp_index`, `_name_index`) built once per connect

### Compound Lookup Resolution
Keys are normalized (lowercase, underscores). Resolution order:
1. Component ID (e.g., `WATER`, `CO2`)
2. Name (e.g., `Water`, `Carbon Dioxide`)
3. CAS number (e.g., `7732-18-5`)
4. Formula (e.g., `H₂O`, `CO₂`)

### Categories
| Key | Label | Count | Purpose |
|-----|-------|-------|---------|
| acid_gas | Gases to Remove | 7 | CO₂, H₂S, SO₂, NH₃, HCl, NO, NO₂ |
| amine_solvent | Amine Solvents | 2 | MEA, MDEA |
| physical_solvent | Physical Solvents | 2 | Water, Methanol |
| carrier_gas | Carrier / Inert | 3 | N₂, O₂, CH₄ |
| organic | Validation Compounds | 7 | Ethanol, Benzene, Toluene, etc. |
| (uncategorized) | Other | 68 | Extended compound library |

### Electrolyte BPE Data
Stored as Python constants in `electrolyte_vle.py` (not in JSON DB) because:
- Polynomial fits to handbook curves (NaOH: OxyChem, K₂CO₃: Armand Products)
- Fitted once at module import, evaluated cheaply at runtime
- Pressure correction via Dühring rule scaling

## Phase Roadmap

### Phase 1 — Foundation ✅
- [x] VLE engine (Antoine, NRTL, ideal gas, Henry's law)
- [x] Chemical database (JSON-backed) with 89 compounds
- [x] Test suite (49 tests against literature values)
- [x] GitHub repo setup

### Phase 2 — Desktop Shell ✅
- [x] Electron + React scaffold with dark engineering theme
- [x] FastAPI HTTP bridge (port 8742) with useEngine hook
- [x] VLE Calculator — pure component with categorized browser + property cards
- [x] VLE Calculator — binary Txy/Pxy diagrams + xy curves
- [x] Electrolyte VLE — BPE/VP depression (NaOH, K₂CO₃)
- [x] Amine-Water VLE — MEA/MDEA Txy/Pxy diagrams
- [x] Dynamic binary pair fetching from DB (no hardcoded lists)
- [x] Performance optimization (singleton DB, O(n) list operations)

### Phase 2.5 — Component Data Expansion
- [x] Phase A: Basic + Thermodynamic (MW, formula, CAS, Tb, Tc, Pc, Antoine)
- [ ] Phase B: Transport properties (density, viscosity, Cp)
- [ ] Phase C: Safety & regulatory (NFPA, TLV/TWA)

### Phase 3 — Column Design
- [ ] Packed column sizing (HTU/NTU, HETP, flooding)
- [ ] Operating/equilibrium line diagrams
- [ ] Column diameter calculation
- [ ] Packing selection from database (12 packings available)

### Phase 4 — Advanced Features
- [ ] Tray column design (McCabe-Thiele, Kremser)
- [ ] Multi-component flash
- [ ] .smc project save/load
- [ ] PDF report generation

### Phase 5 — Acid Gas Scrubbing
- [ ] Kent-Eisenberg model (MVP for CO₂/H₂S + amine)
- [ ] Loading curves (P_CO₂ vs mol CO₂/mol amine)
- [ ] Specific energy (GJ/ton CO₂)
- [ ] eNRTL for reactive systems (full rigor)

### Phase 6 — Polish
- [ ] Sensitivity analysis
- [ ] Unit conversion system
- [ ] User-defined compounds/packings (plugin registry)
- [ ] Build/package pipeline

## Key Design Decisions

1. **HTTP over IPC**: FastAPI on localhost:8742 instead of stdin/stdout IPC. Enables independent testing, curl debugging, and potential web UI in future.

2. **JSON DB with singleton caching**: `simco_chemdb.json` is the single source of truth. `get_db()` caches the connected instance with pre-built indices. No SQLite dependency — simpler deployment, no driver issues.

3. **Category-first UX**: Compounds organized by gas scrubbing role (what to remove, what to use, what's inert) rather than alphabetical or by chemical family.

4. **Reactive VLE as separate mode**: Acid gas + amine equilibrium requires specialized models (Kent-Eisenberg, eNRTL) and will be a distinct calculation mode, not forced into the standard binary VLE framework.

5. **BPE polynomials over rigorous models**: For electrolyte MVP, 3rd-order polynomial fits to handbook data give ±0.5°C accuracy without Pitzer or eNRTL complexity. Fit once at import, evaluate cheaply.

6. **Dual NRTL forms**: Database supports both `dg_const` (direct Δg₁₂/Δg₂₁) and `tau_AplusBoverT` (τ = A + B/T) parameter forms with generic key resolution.
