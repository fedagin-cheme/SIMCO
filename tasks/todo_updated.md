# SIMCO — Current Sprint

## Phase 1: Foundation ✅
- [x] Antoine equation with built-in coefficients (21 compounds, 5 categories)
- [x] NRTL activity coefficient model (8 binary pairs + 2 amine pairs)
- [x] Ideal gas law utilities
- [x] Henry's law with temperature correction (10 gas-water systems)
- [x] SQLite chemical database schema + seed script
- [x] VLE API routes (bubble/dew point, Txy diagram, Pxy diagram)
- [x] Database browsing API route
- [x] Comprehensive test suite — 49 tests passing

## Phase 2: Desktop Shell ✅
- [x] Electron + React + TypeScript scaffold
- [x] FastAPI backend on port 8742
- [x] Dark-themed engineering UI with sidebar navigation
- [x] VLE Calculator: Pure Component mode with compound browser
- [x] VLE Calculator: Binary Mixture mode (8 pairs, Txy + Pxy)

## Phase 2A: Component Browser ✅
- [x] 21 compounds across 5 categories (acid gas, amine, physical, carrier, organic)
- [x] Categorized compound browser with property cards
- [x] NH₃, HCl, NO, NO₂ added with verified Antoine coefficients

## Phase 2B: Scrubbing Solvent VLE ✅
- [x] Electrolyte BPE engine (NaOH-H₂O, K₂CO₃-H₂O)
- [x] MEA-Water and MDEA-Water NRTL pairs
- [x] Electrolyte API endpoints (bpe-curve, vp-curve, operating-point)
- [x] "Scrubbing Solvents" tab with Electrolyte + Amine sub-views
- [x] Dual charts: BPE curve + VP depression with operating point markers
- [x] Amine Txy/Pxy diagrams via existing binary VLE engine
- [x] 15 new tests (9 electrolyte + 6 amine) — all passing

## Phase 3: Next Up
- [ ] Packed column hydraulics (pressure drop, flooding, HETP)
- [ ] Mass transfer correlations (kLa, KGa)
- [ ] Column sizing calculator
- [ ] Process flowsheet (absorber + stripper)
- [ ] Specific energy consumption (GJ/ton CO₂)

## Phase 5: Future
- [ ] Reactive VLE — loaded amine systems (Kent-Eisenberg or eNRTL)
- [ ] CO₂ loading curves
- [ ] Heat of absorption
- [ ] Plugin/registry system for new solvents

---

## Test Summary: 49 passing

| Suite | Tests | Status |
|-------|-------|--------|
| Antoine (pure component) | 9 | ✅ |
| NRTL (activity coefficients) | 5 | ✅ |
| Ideal Gas | 5 | ✅ |
| Henry's Law | 5 | ✅ |
| Database | 8 | ✅ |
| Electrolyte VLE | 9 | ✅ |
| Amine-Water VLE | 6 | ✅ |
| Binary VLE (implicit) | 2 | ✅ |
