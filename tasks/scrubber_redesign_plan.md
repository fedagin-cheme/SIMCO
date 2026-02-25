# Multi-Component Scrubber Redesign

## Architecture
User defines: gas mixture + solvent + packing + removal target → engine returns full column design.

## Backend Changes

### 1. Absorption kinetics data (add to DB)
- Enhancement factors E for amine solvents (CO2-MEA, CO2-MDEA, H2S-MEA, H2S-MDEA)
- For physical solvents (water, methanol): E = 1.0 (no reaction)
- Second-order rate constants k2 for CO2-MEA (~6000 m³/mol/s at 25°C)

### 2. Henry's law solver (engine/thermo/henry.py or extend mass_transfer.py)
- H_pa(T) = H_ref × exp(-dH_sol/R × (1/T - 1/T_ref))  — already have parameters
- m = H_pa / P_total  — equilibrium slope for each acid gas
- For amine solvents: effective Henry's = H_physical / E (enhanced absorption)

### 3. Multi-component scrubber engine (engine/thermo/scrubber.py)
- Input: gas mixture [{name, mol%}], solvent, packing, T, P, flows, removal%
- For each acid gas in mixture:
  - Look up H_pa → compute m
  - Apply enhancement factor if amine solvent
  - Compute A = L/(m·G) for this component
  - Kremser NTU for target removal
- Take the MAXIMUM NTU across all components → that sets the packed height
- Compute individual removals at that height for all components
- Return: exit gas composition, rich solvent loading, column dimensions

### 4. Well-known test case
**Flue gas scrubbing with 30% MEA:**
- Feed: N2 73%, CO2 12%, H2O 12%, O2 3%  (post-combustion)
- Solvent: 30 wt% MEA in water
- Target: 90% CO2 removal
- Packing: Mellapak 250Y
- T = 40°C, P = 1.01 bar

### 5. API endpoint
- POST /api/column/scrubber-design
- Returns full multi-component results + exit compositions

## UI Changes
- Packed Column page gets simplified: 2 panels
  - Left: Gas mixture builder + solvent selector + conditions
  - Right: Packing selection + results
- Single "Design Scrubber" button
- Results show: exit gas table, column dimensions, operating lines per component
