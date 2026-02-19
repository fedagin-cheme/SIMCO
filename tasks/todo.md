# SIMCO — Current Sprint

## Phase 1: Foundation ✅
- [x] Antoine equation with built-in coefficients (21 compounds, 5 categories)
- [x] NRTL activity coefficient model (8 binary pairs)
- [x] Ideal gas law utilities
- [x] Henry's law with temperature correction (10 gas-water systems)
- [x] SQLite chemical database schema + seed script
- [x] VLE API routes (bubble/dew point, Txy diagram, Pxy diagram)
- [x] Database browsing API route
- [x] Compound registry with full metadata (MW, formula, CAS, category, Tc, Pc)
- [x] Test suite — 34 tests passing (validated against NIST/Perry's)
- [x] GitHub repo created

## Phase 2: Desktop Shell (~75% Complete)
- [x] Initialize Electron + React project in `desktop/`
- [x] Vite + Tailwind + TypeScript config
- [x] Custom titlebar with engine status indicator (Wifi/WifiOff)
- [x] Sidebar navigation (VLE Calculator, placeholder pages)
- [x] App window configuration (title, frameless, min size)
- [x] `useEngine` hook — HTTP calls to FastAPI backend (port 8742)
- [x] VLE Calculator: Pure Component mode
  - [x] Categorized compound browser (5 category tabs)
  - [x] Rich property card (Basic, Thermodynamic, Transport placeholder, Safety placeholder)
  - [x] Quick Calculate panel (boiling point at P, Psat at T)
  - [x] Fetches compound registry from `/api/compounds` on mount
- [x] VLE Calculator: Binary Mixture mode
  - [x] Txy diagrams (constant pressure) with bubble/dew curves
  - [x] Pxy diagrams (constant temperature) with toggle
  - [x] xy equilibrium diagram
  - [x] 8 binary pairs from NRTL data
- [x] Placeholder pages for upcoming modules (ComingSoonPage)
- [ ] **Chemical database browser page** (compound search, packing table, Henry's data view)
- [ ] Update README project structure in repo
- [ ] Package/build pipeline (electron-builder)

## Phase 2.5: Component Data Expansion
- [x] Phase A — Basic + Thermodynamic properties (MW, formula, CAS, Tb, Tc, Pc, Antoine)
- [ ] Phase B — Transport properties (density, viscosity, Cp vs T correlations from Perry's/DIPPR)
- [ ] Phase C — Safety & regulatory (NFPA diamond, TLV/TWA, exposure limits)

## Backlog (Phase 3+)

### Phase 3: Column Design
- [ ] Packed column sizing (HTU/NTU method, HETP)
- [ ] Operating/equilibrium line diagrams
- [ ] Flooding correlation (Generalized Pressure Drop Correlation)
- [ ] Column diameter calculation
- [ ] Packing selection tool (existing packing database: 12 packings)

### Phase 4: Advanced Features
- [ ] Tray column design (McCabe-Thiele, Kremser)
- [ ] Multi-component flash calculations
- [ ] .smc project save/load
- [ ] Report generation (PDF export)

### Phase 5: Acid Gas Scrubbing
- [ ] Kent-Eisenberg model (CO₂/H₂S + amine equilibrium — MVP)
- [ ] P_CO₂ vs loading curves at given T and amine concentration
- [ ] Specific energy consumption (GJ/ton CO₂) calculator
- [ ] Deshmukh-Mather model (ionic activity coefficients)
- [ ] eNRTL for reactive acid gas systems (full rigor — roadmap)
- [ ] Amine solution configuration in process setup

### Phase 6: Polish
- [ ] Sensitivity analysis tools
- [ ] Unit conversion system
- [ ] User-defined compounds/packings (plugin registry)
- [ ] Dark/light theme toggle
