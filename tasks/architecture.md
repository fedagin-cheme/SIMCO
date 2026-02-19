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
| Database | SQLite | Chemical property storage (user data, bulk data) |
| Runtime Data | Python dicts | Core compound registry, Antoine/NRTL/Henry constants |
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
│      │   └── BinaryMixtureView               │
│      │       ├── Txy / Pxy toggle            │
│      │       ├── Phase diagram chart         │
│      │       └── xy equilibrium chart        │
│      └── ComingSoonPage (placeholder)        │
└──────────────┬──────────────────────────────┘
               │ HTTP (localhost:8742)
┌──────────────▼──────────────────────────────┐
│  FastAPI Engine                              │
│  ├── GET  /health                            │
│  ├── GET  /api/compounds (registry + meta)   │
│  ├── GET  /api/vle/binary/pairs              │
│  ├── POST /api/vle/bubble-dew                │
│  ├── POST /api/vle/binary/bubble-point       │
│  ├── POST /api/vle/binary/txy                │
│  └── POST /api/vle/binary/pxy               │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  Calculation Modules                         │
│  ├── thermo/antoine.py                       │
│  │   ├── ANTOINE_COEFFICIENTS (21 compounds) │
│  │   ├── CRITICAL_PROPERTIES                 │
│  │   ├── COMPOUND_DATA (registry)            │
│  │   ├── CATEGORIES (5 groups)               │
│  │   └── antoine_pressure/temperature()      │
│  ├── thermo/nrtl.py                          │
│  │   ├── NRTL_BINARY_PARAMS (8 pairs)        │
│  │   └── nrtl_gamma()                        │
│  ├── thermo/henry.py                         │
│  │   ├── HENRY_CONSTANTS_WATER_25C (10 gases)│
│  │   └── henry_solubility()                  │
│  └── thermo/ideal_gas.py                     │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│  SQLite Database                             │
│  ├── compounds (properties)                  │
│  ├── antoine_coefficients                    │
│  ├── nrtl_binary_params                      │
│  ├── henry_constants                         │
│  └── packings (12 packing types)             │
│  Note: .db regenerated from seed.py          │
└─────────────────────────────────────────────┘
```

## Data Architecture

### Compound Registry (antoine.py)
The `COMPOUND_DATA` dict is the single source of truth for compound metadata at runtime. Each entry contains:
- Identity: name, formula, CAS, molecular weight
- Classification: category (acid_gas | amine_solvent | physical_solvent | carrier_gas | organic)
- Description: engineering context for gas scrubbing relevance

Thermodynamic data is cross-referenced from separate dicts (`ANTOINE_COEFFICIENTS`, `CRITICAL_PROPERTIES`) and assembled by `get_all_compound_details()` for API responses.

### Categories
| Key | Label | Purpose |
|-----|-------|---------|
| acid_gas | Gases to Remove | CO₂, H₂S, SO₂, NH₃, HCl, NO, NO₂ |
| amine_solvent | Amine Solvents | MEA, MDEA (future: DEA, AMP, piperazine) |
| physical_solvent | Physical Solvents | Water, Methanol (Rectisol) |
| carrier_gas | Carrier / Inert | N₂, O₂, CH₄ |
| organic | Validation Compounds | Ethanol, Benzene, Toluene, etc. |

## Phase Roadmap

### Phase 1 — Foundation ✅
- [x] VLE engine (Antoine, NRTL, ideal gas, Henry's law)
- [x] Chemical database (SQLite) with seed data
- [x] Compound registry (21 compounds, 5 categories)
- [x] Test suite (34 tests against literature values)
- [x] GitHub repo setup

### Phase 2 — Desktop Shell (~75%) 🔧
- [x] Electron + React scaffold with dark engineering theme
- [x] FastAPI HTTP bridge (port 8742) with useEngine hook
- [x] VLE Calculator — pure component with categorized browser + property cards
- [x] VLE Calculator — binary Txy/Pxy diagrams + xy curves
- [ ] Chemical database browser page
- [ ] Build/package pipeline

### Phase 2.5 — Component Data Expansion
- [x] Phase A: Basic + Thermodynamic (MW, formula, CAS, Tb, Tc, Pc, Antoine)
- [ ] Phase B: Transport properties (density, viscosity, Cp)
- [ ] Phase C: Safety & regulatory (NFPA, TLV/TWA)

### Phase 3 — Column Design
- [ ] Packed column sizing (HTU/NTU, HETP, flooding)
- [ ] Operating/equilibrium line diagrams
- [ ] Column diameter calculation
- [ ] Packing selection from database

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

## Key Design Decisions

1. **HTTP over IPC**: FastAPI on localhost:8742 instead of stdin/stdout IPC. Enables independent testing, curl debugging, and potential web UI in future.

2. **In-code registry over pure SQLite**: Core compound data lives in Python dicts for speed and type safety. SQLite reserved for user-added data and bulk storage.

3. **Category-first UX**: Compounds organized by gas scrubbing role (what to remove, what to use, what's inert) rather than alphabetical or by chemical family.

4. **Reactive VLE as separate mode**: Acid gas + amine equilibrium requires specialized models (Kent-Eisenberg, eNRTL) and will be a distinct calculation mode, not forced into the standard binary VLE framework.
