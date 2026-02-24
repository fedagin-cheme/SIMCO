# SIMCO — Lessons Learned

## Data & Units

1. **Always validate against known literature values** — every thermo function should have at least one test against a published reference value (NIST, Perry's, DECHEMA). All 21 compounds verify boiling points within 1.3°C of literature.

2. **Antoine coefficient unit systems are treacherous** — NIST uses log10(P_bar) with T in Kelvin; Coulson uses ln(P_mmHg) with T in Kelvin; our engine uses log10(P_mmHg) with T in Celsius. Mixing these up produces boiling points off by 200-400°C with no obvious error signal.
   - NIST → ours: A' = A + 2.87506, B' = B, C' = C + 273.15
   - Coulson → ours: A' = ANTA/2.302585, B' = ANTB/2.302585, C' = ANTC + 273.15
   - **Always verify each new compound's Tb at 1 atm before committing.**

3. **Use SI units internally, convert at boundaries** — engine uses Pa, K, mol, m³ internally. All unit conversions happen at the API/UI boundary. The Antoine module is an exception (uses mmHg/°C for coefficient compatibility with literature).

4. **Supercritical compounds need special handling** — CO₂ (Tc = 31°C) has no liquid phase at room conditions. Antoine extrapolation beyond the valid range gives nonsense. Always check critical properties before calculating.

## Database & Data Management

5. **simco_chemdb.json is the single source of truth** — all compound metadata, Antoine coefficients, NRTL parameters, Henry constants, and packing data live in the JSON database. The seed script creates copies for testing. No thermodynamic data is hardcoded in Python modules.

6. **Export what tests import** — test suite imported `MMHG_TO_PA` from antoine.py but it was only used as a magic number (133.322). Always define constants as named exports when other modules reference them.

## Architecture & Development

7. **FastAPI on port 8742, not IPC stdin/stdout** — the original plan was Electron↔Python IPC over stdin/stdout. Switched to FastAPI HTTP server which is simpler, debuggable (curl), and allows independent engine testing.

8. **Windows Store Python breaks Node.js PATH** — the Microsoft Store Python installation created PATH conflicts with Node.js child process spawning. Use standard Python installer or pyenv instead.

9. **JSON DB with class-level cache beats SQLite for read-only data** — simco_chemdb.json is parsed once into a class-level cache. Module-level `get_db()` singleton avoids re-indexing. This is simpler than SQLite (no driver deps, no .db file management) and fast enough for real-time calculations.

## Frontend Patterns

10. **Fetch compound data from API, don't hardcode in TSX** — the original VLE page had a hardcoded COMPOUNDS array that drifted from the backend. Now the frontend fetches `/api/compounds` on mount and gets categorized, typed data.

11. **Font sizes for engineering apps need to be readable** — initial design used text-[10px] which is too small for data-dense property cards. Minimum text-xs (12px) for labels, text-sm (14px) for values.

## Gas Scrubbing Domain

12. **Acid gas + amine VLE is reactive, not simple physical equilibrium** — CO₂ + MEA → carbamate. Standard NRTL cannot model this. Need Kent-Eisenberg (MVP) or eNRTL (full rigor) for acid gas equilibrium. Binary VLE mode is only valid for non-reactive pairs.

13. **Component categories matter for UX** — grouping compounds into Gases to Remove / Amine Solvents / Physical Solvents / Carrier-Inert / Validation makes the tool immediately navigable for process engineers vs. a flat alphabetical list.

## Electrolyte VLE (Phase 2B)

14. **BPE polynomial correlations beat rigorous models for engineering MVP** — for NaOH-H₂O and K₂CO₃-H₂O, 3rd-order polynomial fits to handbook data give excellent accuracy (±0.5°C) without the complexity of Pitzer or eNRTL. Fit once on import, evaluate cheaply at runtime.

15. **Dühring rule is a practical pressure-scaling tool** — BPE(P) ≈ BPE(1atm) × (T_sat(P) + 273.15) / 373.15 provides reasonable pressure correction without needing full thermodynamic models across pressure ranges.

16. **Electrolyte and volatile-binary VLE need fundamentally different UI** — electrolytes show BPE curves (T vs w/w%) and VP depression (P vs w/w%), not Txy phase envelopes. The "Scrubbing Solvents" tab correctly splits into Electrolyte Solution and Amine Solution sub-views with distinct input/output patterns.

17. **Water activity from BPE is self-consistent** — deriving a_w from the BPE data using a_w = P°_water(100°C) / P°_water(T_boil) ensures the vapor pressure depression and boiling point elevation calculations agree. This avoids the need for separate activity coefficient models.

18. **Always check before building — code may already exist** — when resuming from a compacted conversation, the implementation may already be complete from a previous session. Run tests and verify the codebase state before writing new code.

## JSON DB Migration (Phase 2C)

19. **Singleton DB pattern eliminates repeated JSON parsing** — `with ChemicalDatabase() as db:` rebuilds indices on every call. Module-level `get_db()` singleton caches the connected instance. Hot-path calls (Txy generation: 50+ DB lookups) went from redundant parsing to <2ms total.

20. **Index rebuild guard with `_indices_built` flag** — even with class-level `_cache`, `_build_indices()` was called every `connect()`. Adding a simple boolean flag skips re-indexing when data hasn't changed.

21. **Inline record-building in list/search to avoid O(n²)** — `list_compounds()` called `get_compound()` per component (each doing `_resolve_component` lookup). Extracting `_build_compound_record()` and calling it directly on the raw JSON component avoids the index lookup overhead.

22. **Remove hardcoded fallback keys** — NRTL `tau_AplusBoverT` had `params.get("MEA_to_H2O")` fallbacks that only worked for one specific pair. Generic dict-value scanning works for any pair.

23. **Dead frontend constants after API migration** — when the frontend switches from hardcoded arrays to dynamic API fetches, remove the old constants immediately to prevent confusion.
