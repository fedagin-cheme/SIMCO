# SIMCO

**Gas Scrubbing & Mass-transfer Calculator** — a professional simulation tool for scrubbing, stripping, and chemical absorption processes.

## Overview

SIMCO provides rigorous thermodynamic and mass-transfer calculations for gas absorption/stripping column design. Built for process engineers, students, and consultants who need accurate results without the overhead of full-suite process simulators like Aspen or ProMax.

## Current Status

**Phase 1 (Python Engine): Complete** — 49 passing tests  
**Phase 2 (Desktop Shell): Complete** — VLE calculator with three modes (Pure Component, Binary Mixture, Scrubbing Solvents)

## Core Capabilities

- **Component Database**: 89 compounds in JSON-backed database (simco_chemdb.json) — acid gases, amine solvents, physical solvents, carrier gases, organics. 46 with Antoine coefficients, 12 packings.
- **VLE (Vapor-Liquid Equilibrium)**: Antoine equation, NRTL activity coefficients (11 binary pairs), ideal gas law, Henry's law (10 gas-water systems)
- **Phase Diagrams**: Binary Txy (constant pressure) and Pxy (constant temperature) diagrams with xy equilibrium curves
- **Electrolyte VLE**: Boiling point elevation and vapor pressure depression for NaOH-H₂O and K₂CO₃-H₂O systems using polynomial fits to handbook data with Dühring rule pressure correction
- **Amine-Water VLE**: MEA-Water and MDEA-Water binary systems with temperature-dependent NRTL parameters

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Engine | Python 3.10+ / FastAPI | Thermodynamics, mass transfer, API on port 8742 |
| Frontend | Electron + React + TypeScript | Desktop UI with dark engineering theme |
| Styling | Tailwind CSS | Utility-first design system |
| Build | Vite | Fast frontend bundling |
| Database | JSON (simco_chemdb.json) | Chemical property storage — singleton cached |
| VCS | GitHub | Version control |

## Project Structure

```
SIMCO/
├── engine/                        # Python calculation engine
│   ├── thermo/                    # Thermodynamic models
│   │   ├── antoine.py             # Antoine equation (46 compounds)
│   │   ├── nrtl.py                # NRTL activity coefficients (11 binary pairs)
│   │   ├── henry.py               # Henry's law (10 gas-water systems)
│   │   ├── ideal_gas.py           # Ideal gas utilities
│   │   └── electrolyte_vle.py     # BPE/VP depression (NaOH, K₂CO₃)
│   ├── database/                  # JSON-backed chemical property database
│   │   ├── db.py                  # ChemicalDatabase class + get_db() singleton
│   │   ├── simco_chemdb.json      # Canonical data source (89 components)
│   │   └── seed.py                # Creates writable copies for testing
│   ├── api/                       # FastAPI backend
│   │   ├── server.py              # App setup, endpoints, CORS
│   │   └── routes/
│   │       ├── vle.py             # VLE calculations (bubble/dew, Txy, Pxy)
│   │       └── database_browse.py # DB query helpers
│   └── tests/
│       └── test_engine.py         # 49 tests against literature values
├── desktop/                       # Electron + React frontend
│   ├── src/
│   │   ├── main/index.ts          # Electron main process
│   │   ├── preload/index.ts       # Context bridge
│   │   └── renderer/
│   │       ├── App.tsx            # Root component with routing
│   │       ├── hooks/useEngine.ts # HTTP hook for FastAPI calls
│   │       ├── components/        # Sidebar, TitleBar
│   │       └── pages/
│   │           ├── VLECalculatorPage.tsx  # 3 modes: Pure, Binary, Scrubbing
│   │           └── ComingSoonPage.tsx     # Placeholder for future modules
│   └── vite.config.ts
├── tasks/                         # Project management
│   ├── architecture.md            # System architecture
│   ├── todo.md                    # Current sprint tasks
│   └── lessons.md                 # Patterns & lessons learned
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Engine health check |
| GET | `/api/compounds` | Full compound registry (grouped by category) |
| GET | `/api/vle/binary/pairs` | Available NRTL binary pairs |
| POST | `/api/vle/bubble-dew` | Pure component bubble/dew point + Psat |
| POST | `/api/vle/binary/bubble-point` | Binary bubble point at given x₁ and P |
| POST | `/api/vle/binary/txy` | Txy diagram data (constant P) |
| POST | `/api/vle/binary/pxy` | Pxy diagram data (constant T) |
| GET | `/api/vle/electrolyte/solutes` | Available electrolyte solutes |
| POST | `/api/vle/electrolyte/bpe-curve` | Boiling point elevation curve |
| POST | `/api/vle/electrolyte/vp-curve` | Vapor pressure depression curve |
| POST | `/api/vle/electrolyte/operating-point` | Single operating point calculation |

## NRTL Binary Pairs (11)

| System | Form |
|--------|------|
| MEA / H₂O | tau_AplusBoverT |
| MEA / Water | dg_const |
| MDEA / Water | dg_const |
| Methanol / Water | dg_const |
| Ethanol / Water | dg_const |
| Acetone / Water | dg_const |
| Acetone / Methanol | dg_const |
| Benzene / Toluene | dg_const |
| Methanol / Benzene | dg_const |
| Ethanol / Benzene | dg_const |
| Chloroform / Methanol | dg_const |

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Engine
```bash
cd engine
pip install fastapi uvicorn numpy
python -m pytest tests/ -v          # Run 49 tests
uvicorn api.server:app --port 8742  # Start API
```

### Desktop
```bash
cd desktop
npm install
npm run dev     # Start Electron + Vite dev server
```

**Note**: Both the Python engine (port 8742) and the Vite dev server must be running for the desktop app.

## License

MIT
