# SIMCO — Lessons Learned

## Patterns & Rules

1. **Always validate against known literature values** — every thermo function should have at least one test against a published reference value (NIST, Perry's, DECHEMA).

2. **Handle pure-component limits explicitly** — NRTL and other activity coefficient models can have numerical issues at x=0 or x=1. Always check boundary conditions.

3. **Use SI units internally, convert at boundaries** — engine uses Pa, K, mol, m³ internally. All unit conversions happen at the API/UI boundary.

4. **Database is regenerated from seed** — the .db file is gitignored. The seed script is the source of truth for baseline data.
