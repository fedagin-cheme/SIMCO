# SIMCO

**Gas Scrubbing & Mass-transfer Calculator** — a robust chemical and mechanical simulation tool for scrubbing, stripping, and chemical absorption processes.

## Overview

SIMCO provides rigorous thermodynamic and mass-transfer calculations for gas absorption/stripping column design. Built for process engineers, students, and consultants who need accurate results without the overhead of full-suite process simulators.

## Current Status

**Phase 1 (Python Engine): Complete** — 34 passing tests
**Phase 2 (Desktop Shell): ~75% complete** — VLE calculator fully functional, component browser live

## Core Capabilities

- **VLE (Vapor-Liquid Equilibrium)**: Antoine equation (21 compounds), NRTL activity coefficients (8 binary pairs), ideal gas law, Henry's law (10 gas-water systems)
- **Component Database**: 21 compounds across 5 categories — acid gases, amine solvents, physical solvents, carrier/inert gases, and validation organics. Full metadata: MW, formula, CAS, boiling point, critical properties, Antoine coefficients.
- **Phase Diagrams**: Binary Txy (constant pressure) and Pxy (constant temperature) diagrams with xy equilibrium curves
- **Column Design**: Packed column sizing (HTU/NTU), tray column design (planned)
- **Project Files**: Save/load simulation configurations as `.smc` files (planned)

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Engine | Python 3.10+ / FastAPI | Thermodynamics, mass transfer, API on port 8742 |
| Frontend | Electron + React + TypeScript | Desktop UI with dark engineering theme |
| Styling | Tailwind CSS | Utility-first design system |
| Build | Vite | Fast frontend bundling |
| Database | SQLite | Chemical property storage |
| VCS | GitHub | Version control |

## Project Structure

```
SIMCO/
├── engine/                     # Python calculation engine
│   ├── thermo/                 # Thermodynamic models
│   │   ├── antoine.py          # Antoine equation + compound registry (21 compounds)
│   │   ├── nrtl.py             # NRTL activity coefficients (8 binary pairs)
│   │   ├── henry.py            # Henry's law (10 gas-water systems)
│   │   └── ideal_gas.py        # Ideal gas utilities
│   ├── database/               # SQLite chemical property database
│   │   ├── db.py               # Database connection
│   │   └── seed.py             # Seed script (source of truth)
│   ├── api/                    # FastAPI backend
│   │   ├── server.py           # App setup, endpoints, CORS
│   │   └── routes/
│   │       ├── vle.py          # VLE calculations (bubble/dew, Txy, Pxy)
│   │       └── database_browse.py
│   └── tests/
│       └── test_engine.py      # 34 tests against literature values
├── desktop/                    # Electron + React frontend
│   ├── src/
│   │   ├── main/index.ts       # Electron main process
│   │   ├── preload/index.ts    # Context bridge
│   │   └── renderer/
│   │       ├── App.tsx          # Root component with routing
│   │       ├── main.tsx         # Entry point
│   │       ├── hooks/
│   │       │   └── useEngine.ts # HTTP hook for FastAPI calls
│   │       ├── components/
│   │       │   ├── Sidebar.tsx  # Navigation sidebar
│   │       │   └── TitleBar.tsx # Custom titlebar + engine status
│   │       └── pages/
│   │           ├── VLECalculatorPage.tsx  # Pure component + binary mixture
│   │           └── ComingSoonPage.tsx     # Placeholder for future modules
│   └── vite.config.ts
├── tasks/                      # Project management
│   ├── architecture.md         # System architecture
│   ├── todo.md                 # Current sprint tasks
│   └── lessons.md              # Patterns & lessons learned
└── docs/                       # Documentation
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Engine health check |
| GET | `/api/compounds` | Full compound registry (grouped by category) |
| GET | `/api/vle/binary/pairs` | Available NRTL binary pairs |
| POST | `/api/vle/bubble-dew` | Pure component bubble/dew point + Psat |
| POST | `/api/vle/binary/bubble-point` | Binary bubble point at given x, T or P |
| POST | `/api/vle/binary/txy` | Txy diagram data (constant P) |
| POST | `/api/vle/binary/pxy` | Pxy diagram data (constant T) |

## Compound Inventory (21)

| Category | Count | Compounds |
|----------|-------|-----------|
| Gases to Remove | 7 | CO₂, H₂S, SO₂, NH₃, HCl, NO, NO₂ |
| Amine Solvents | 2 | MEA, MDEA |
| Physical Solvents | 2 | Water, Methanol |
| Carrier / Inert | 3 | N₂, O₂, CH₄ |
| Validation | 7 | Ethanol, Benzene, Toluene, Acetone, n-Hexane, n-Heptane, Chloroform |

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Engine
```bash
cd engine
pip install fastapi uvicorn
python -m pytest tests/ -v          # Run 34 tests
uvicorn api.server:app --port 8742  # Start API
```

### Desktop
```bash
cd desktop
npm install
npm run dev     # Start Electron + Vite dev server
```

## License

MIT
