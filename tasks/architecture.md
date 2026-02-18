# SIMCO Architecture

## Overview
SIMCO (Scrubbing & Mass-transfer Calculator) is a desktop application for chemical absorption, gas scrubbing, and stripping simulation. It combines a rigorous Python calculation engine with an Electron + React desktop UI.

## Custom File Format
- Extension: `.smc`
- Format: JSON-based project file containing simulation parameters, results, and metadata

## Tech Stack
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Engine | Python 3.10+ | Thermodynamics, mass transfer, database |
| Frontend | React + Electron | Desktop UI |
| Database | SQLite | Chemical property storage |
| IPC | Electron ↔ Python bridge | UI-engine communication |

## Architecture Layers

### 1. Calculation Engine (Python)
- **thermo/** — Antoine, NRTL, ideal gas, Henry's law
- **database/** — SQLite chemical property database with seed data
- **api/routes/** — Route handlers for VLE, database browsing

### 2. Desktop Shell (Electron)
- Main process: window management, IPC bridge, file I/O
- Renderer: React app with calculation pages

### 3. IPC Bridge
- Electron main process spawns Python child process
- JSON-based request/response over stdin/stdout
- Async handling with promise-based API

## Phase Roadmap

### Phase 1 — Foundation ✅
- [x] VLE engine (Antoine, NRTL, ideal gas, Henry's law)
- [x] Chemical database (SQLite) with seed data
- [x] Test suite (27+ tests)
- [x] GitHub repo setup

### Phase 2 — Desktop Shell
- [ ] Electron + React scaffold
- [ ] IPC bridge (UI → Python engine)
- [ ] VLE calculator page with interactive Txy/Pxy charts
- [ ] Chemical database browser page

### Phase 3 — Column Design
- [ ] Packed column sizing (HTU/NTU method)
- [ ] Operating/equilibrium line diagrams
- [ ] Flooding correlation (Generalized Pressure Drop Correlation)
- [ ] Column diameter calculation

### Phase 4 — Advanced Features
- [ ] Tray column design (McCabe-Thiele)
- [ ] Multi-component systems
- [ ] .smc project save/load
- [ ] Report generation (PDF export)

### Phase 5 — Polish
- [ ] Amine scrubbing module (MEA, DEA, MDEA)
- [ ] Sensitivity analysis tools
- [ ] Unit conversion system
- [ ] User-defined compounds/packings
