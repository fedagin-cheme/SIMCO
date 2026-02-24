# SIMCO Engine — Post-DB-Migration Optimization

## Completed ✅

### 1. Singleton DB access pattern
- [x] Added `get_db()` module-level singleton in `db.py`
- [x] Updated `antoine.py`, `nrtl.py`, `henry.py`, `server.py`, `database_browse.py`
- [x] Eliminates repeated JSON parsing on hot paths (Txy: 50+ DB lookups → <2ms)

### 2. Index rebuild elimination
- [x] Added `_indices_built` flag to skip redundant `_build_indices()` calls
- [x] Indices only rebuilt when `_cache` changes (new db_path)

### 3. `list_compounds()` O(n²) → O(n)
- [x] Extracted `_build_compound_record()` helper
- [x] Inlined record building — single pass through components

### 4. `search_compounds()` O(n²) → O(n)
- [x] Same pattern — direct `_build_compound_record()` on raw component

### 5. NRTL `tau_AplusBoverT` generic key resolution
- [x] Removed hardcoded `MEA_to_H2O` / `H2O_to_MEA` fallbacks
- [x] Generic: try named keys → positional keys → scan for {A,B} dict values

### 6. Documentation & housekeeping
- [x] `database/__init__.py`: Fixed stale "SQLite" docstring, exported `get_db`
- [x] Removed dead `BINARY_PAIRS` / `AMINE_PAIRS` constants from VLECalculatorPage.tsx
- [x] Consolidated `lessons.md` / `lessons_updated.md` (kept superset)
- [x] Consolidated `todo.md` / `todo_updated.md`
- [x] Updated outdated lessons (#5, #9) to reflect JSON DB architecture

### Verification
- [x] 49/49 tests passing (0.32s, down from 0.38s)
- [x] No API contract changes
- [x] Txy diagram generation: 1.6ms warm path (51 points)

## Data Integrity Notes (future work — needs literature lookup)
- 6 components have mw=0: CHLOROETHYLENE, CYANIC_ACID, DIETHYLAMINE, DIOXANE_1_4, PEGDME, VINYL_ACETATE
- Many components lack category/description fields
- H2O-CO2 binary has `form=kij_const` (Peng-Robinson) — correctly excluded from NRTL pair listing

## Files Modified
- `engine/database/__init__.py` — docstring fix, get_db export
- `engine/database/db.py` — singleton, index guard, _build_compound_record, generic NRTL keys
- `engine/thermo/antoine.py` — get_db() singleton
- `engine/thermo/nrtl.py` — get_db() singleton
- `engine/thermo/henry.py` — get_db() singleton
- `engine/api/server.py` — get_db() singleton
- `engine/api/routes/database_browse.py` — get_db() singleton + _get_instance helper
- `desktop/src/renderer/pages/VLECalculatorPage.tsx` — removed dead code
- `tasks/lessons.md` — consolidated + new entries
- `tasks/todo.md` — this file
