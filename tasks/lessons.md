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

5. **Database is regenerated from seed** — the .db file is gitignored. The seed script is the source of truth for baseline data. However, the in-code dictionaries (ANTOINE_COEFFICIENTS, NRTL_BINARY_PARAMS, HENRY_CONSTANTS) are the runtime source of truth for the calculation engine.

6. **Export what tests import** — test suite imported `MMHG_TO_PA` from antoine.py but it was only used as a magic number (133.322). Always define constants as named exports when other modules reference them.

## Architecture & Development

7. **FastAPI on port 8742, not IPC stdin/stdout** — the original plan was Electron↔Python IPC over stdin/stdout. Switched to FastAPI HTTP server which is simpler, debuggable (curl), and allows independent engine testing.

8. **Windows Store Python breaks Node.js PATH** — the Microsoft Store Python installation created PATH conflicts with Node.js child process spawning. Use standard Python installer or pyenv instead.

9. **Compound registry belongs in code, not just SQLite** — putting compound metadata (MW, formula, CAS, category) in the Python module (antoine.py COMPOUND_DATA dict) is faster and more maintainable than SQLite for the core set. SQLite is for user-defined compounds and bulk data.

## Frontend Patterns

10. **Fetch compound data from API, don't hardcode in TSX** — the original VLE page had a hardcoded COMPOUNDS array that drifted from the backend. Now the frontend fetches `/api/compounds` on mount and gets categorized, typed data.

11. **Font sizes for engineering apps need to be readable** — initial design used text-[10px] which is too small for data-dense property cards. Minimum text-xs (12px) for labels, text-sm (14px) for values.

## Gas Scrubbing Domain

12. **Acid gas + amine VLE is reactive, not simple physical equilibrium** — CO₂ + MEA → carbamate. Standard NRTL cannot model this. Need Kent-Eisenberg (MVP) or eNRTL (full rigor) for acid gas equilibrium. Binary VLE mode is only valid for non-reactive pairs.

13. **Component categories matter for UX** — grouping compounds into Gases to Remove / Amine Solvents / Physical Solvents / Carrier-Inert / Validation makes the tool immediately navigable for process engineers vs. a flat alphabetical list.
