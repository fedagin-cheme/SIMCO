# SIMCO — Current Sprint

## Phase 1: Foundation ✅
- [x] Antoine equation with built-in coefficients
- [x] NRTL activity coefficient model
- [x] Ideal gas law utilities
- [x] Henry's law with temperature correction
- [x] SQLite chemical database schema
- [x] Database seed script (20 compounds, 9 Antoine sets, 8 NRTL pairs, 10 Henry constants, 12 packings)
- [x] VLE API route (bubble point, Txy diagram generation)
- [x] Database browsing API route
- [x] Test suite — 27+ tests passing
- [x] GitHub repo created (SIMCO)
- [x] Initial commit with full project structure

## Phase 2: Desktop Shell (Next)
- [ ] Initialize Electron + React project in `ui/`
- [ ] Set up IPC bridge (Electron main → Python child process)
- [ ] Build VLE calculator page
  - [ ] Compound selection dropdowns (from database)
  - [ ] Pressure/temperature input
  - [ ] Txy diagram with interactive chart (Recharts or Plotly)
  - [ ] Results table
- [ ] Build chemical database browser page
  - [ ] Compound search/filter
  - [ ] Property detail cards
  - [ ] Packing data table
- [ ] Basic navigation (sidebar or tabs)
- [ ] App window configuration (title, icon, min size)

## Backlog
- [ ] Packed column design module
- [ ] .smc file save/load
- [ ] Dark mode / theme system
