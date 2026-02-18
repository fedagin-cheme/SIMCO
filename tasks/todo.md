# SIMCO — Current Sprint

## Phase 1: Foundation ✅
- [x] Antoine equation with built-in coefficients (18 compounds)
- [x] NRTL activity coefficient model (8 binary pairs)
- [x] Ideal gas law utilities
- [x] Henry's law with temperature correction
- [x] SQLite chemical database schema
- [x] Database seed script (20 compounds, 9 Antoine sets, 8 NRTL pairs, 10 Henry constants, 12 packings)
- [x] VLE API route (bubble point, Txy diagram generation)
- [x] Database browsing API route
- [x] Test suite — 27+ tests passing
- [x] GitHub repo created (SIMCO)
- [x] Initial commit with full project structure

## Phase 2: Desktop Shell (In Progress)
- [x] Initialize Electron + React project in `desktop/`
- [x] Vite + Tailwind + TypeScript config
- [x] Custom titlebar with engine status indicator
- [x] Sidebar navigation (Calculations / bottom nav)
- [x] App window configuration (title, frame, min size)
- [x] IPC bridge (preload, main process, engine spawn/health)
- [x] `useEngine` hook — HTTP calls to FastAPI backend
- [x] VLE Calculator page — pure-component bubble/dew point working
- [x] Placeholder pages for upcoming modules
- [x] **Wire binary Txy/Pxy diagram endpoint into server.py** ✅
- [ ] Connect VLE page chart to real engine data (replace mocked curve)
- [ ] Add binary mixture selection (two-component dropdowns) to VLE page
- [ ] Build chemical database browser page (compound search, property cards, packing table)
- [ ] Update README project structure (ui/ → desktop/)

## Backlog (Phase 3+)
- [ ] Packed column design module (HTU/NTU, HETP, flooding)
- [ ] Tray column design (McCabe-Thiele, Kremser)
- [ ] .smc file save/load
- [ ] Multi-component systems
- [ ] Report generation (PDF export)
- [ ] Amine scrubbing module (MEA, DEA, MDEA)
- [ ] Sensitivity analysis tools
- [ ] Unit conversion system
- [ ] User-defined compounds/packings
