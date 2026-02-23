"""engine.database.db

JSON-backed chemical property database.

This replaces the earlier SQLite-backed implementation. The public API is kept
stable so the rest of the engine and the desktop UI can remain thin:

- compounds
- Antoine coefficients (possibly multiple ranges)
- NRTL binary parameters
- Henry constants

Data source:
    engine/database/simco_chemdb.json

The DB format is the SIMCO JSON format produced for the scrubbing/stripping
simulator.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "simco_chemdb.json")


def _norm(s: str) -> str:
    return s.strip().lower().replace(" ", "_").replace("-", "_")


@dataclass(frozen=True)
class _Antoine:
    A: float
    B: float
    C: float
    Tmin_C: float
    Tmax_C: float
    source: str


class ChemicalDatabase:
    """In-process DB wrapper.

    Usage:
        with ChemicalDatabase() as db:
            db.get_compound("water")
    """

    _cache: Optional[Dict[str, Any]] = None

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._db: Dict[str, Any] = {}
        self._comp_index: Dict[str, Dict[str, Any]] = {}
        self._name_index: Dict[str, Dict[str, Any]] = {}

    # Context manager parity with old SQLite version
    def connect(self) -> "ChemicalDatabase":
        if ChemicalDatabase._cache is None or ChemicalDatabase._cache.get("__path") != self.db_path:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["__path"] = self.db_path
            ChemicalDatabase._cache = data
        self._db = ChemicalDatabase._cache
        self._build_indices()
        return self

    def close(self) -> None:
        # No persistent connection to close.
        return

    def __enter__(self) -> "ChemicalDatabase":
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ── Indexing ─────────────────────────────────────────────────────────

    def _build_indices(self) -> None:
        self._comp_index.clear()
        self._name_index.clear()
        for comp in self._db.get("components", []):
            cid = _norm(comp.get("id", ""))
            name = _norm(comp.get("name", ""))
            cas = _norm(comp.get("identifiers", {}).get("cas", ""))
            if cid:
                self._comp_index[cid] = comp
            if name:
                self._name_index[name] = comp
            if cas:
                self._comp_index[cas] = comp
            # convenience: allow lookup by formula-like ids (CO2, H2S) and by common keys
            formula = _norm(comp.get("formula", ""))
            if formula:
                self._comp_index[formula] = comp

    def _resolve_component(self, key: str) -> Optional[Dict[str, Any]]:
        k = _norm(key)
        return self._comp_index.get(k) or self._name_index.get(k)

    # ── Compound queries ────────────────────────────────────────────────

    def get_compound(self, name: str) -> Optional[Dict[str, Any]]:
        """Get compound metadata.

        Returns a dict shaped similarly to the old SQLite record.
        """
        c = self._resolve_component(name)
        if not c:
            return None

        identifiers = c.get("identifiers", {}) or {}
        critical = c.get("critical", {}) or {}

        tb_K = None
        # Tb is stored as a correlation in the SIMCO JSON; keep compatibility here.
        for corr in c.get("correlations", []) or []:
            if corr.get("property") == "Tb" and corr.get("model") == "constant":
                tb_K = corr.get("parameters", {}).get("Tb_K")
                break

        return {
            "name": c.get("name", ""),
            "formula": c.get("formula", ""),
            "cas_number": identifiers.get("cas", ""),
            "mw": c.get("mw"),
            "tc": critical.get("Tc_K"),
            "pc": critical.get("Pc_Pa"),
            "omega": critical.get("omega"),
            "tb": tb_K,
            "category": c.get("category", ""),
            "description": c.get("description", ""),
            "id": c.get("id", ""),
        }

    def search_compounds(self, query: str) -> List[Dict[str, Any]]:
        q = _norm(query)
        out: List[Dict[str, Any]] = []
        for c in self._db.get("components", []):
            if q in _norm(c.get("name", "")) or q in _norm(c.get("formula", "")):
                out.append(self.get_compound(c.get("id", c.get("name", ""))) or {})
        return [x for x in out if x]

    def list_compounds(self, category: str = None) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        cat_norm = _norm(category) if category else None
        for c in self._db.get("components", []):
            rec = self.get_compound(c.get("id", c.get("name", "")))
            if not rec:
                continue
            if category:
                rec_cat = _norm(rec.get("category", ""))
                # Backward-compatible grouping used in tests and some UI pieces.
                if cat_norm == "gas":
                    if "gas" not in rec_cat:
                        continue
                elif cat_norm == "solvent":
                    # Treat common liquid categories as solvents.
                    if (
                        "solvent" not in rec_cat
                        and rec_cat not in {"organic", "amine_solvent", "physical_solvent"}
                    ):
                        # Heuristic fallback: if Tb exists and is near/above room temperature,
                        # consider it a solvent-like liquid.
                        tb = rec.get("tb")
                        if tb is None or tb < 273.15 + 20.0:
                            continue
                else:
                    if rec_cat != cat_norm:
                        continue
            out.append(rec)
        out.sort(key=lambda r: (r.get("category", ""), r.get("name", "")))
        return out

    # ── Antoine queries ────────────────────────────────────────────────

    def _antoine_sets(self, comp: Dict[str, Any]) -> List[_Antoine]:
        sets: List[_Antoine] = []
        for corr in comp.get("correlations", []) or []:
            if corr.get("property") != "Psat":
                continue
            if corr.get("model") != "Antoine_log10_PmmHg_TdegC":
                continue
            p = corr.get("parameters", {}) or {}
            v = corr.get("validity", {}) or {}
            Tmin_K = v.get("Tmin_K")
            Tmax_K = v.get("Tmax_K")
            if Tmin_K is None or Tmax_K is None:
                continue
            sets.append(
                _Antoine(
                    A=float(p.get("A")),
                    B=float(p.get("B")),
                    C=float(p.get("C")),
                    Tmin_C=float(Tmin_K) - 273.15,
                    Tmax_C=float(Tmax_K) - 273.15,
                    source=str(corr.get("source_ref", "")),
                )
            )
        # sort by Tmin
        sets.sort(key=lambda s: s.Tmin_C)
        return sets

    def get_antoine(self, compound_name: str, T_celsius: float = None) -> Optional[Dict[str, Any]]:
        """Return a single Antoine set.

        If T_celsius is provided, choose the set whose validity range contains T.
        Otherwise return the first set.
        """
        comp = self._resolve_component(compound_name)
        if not comp:
            return None

        sets = self._antoine_sets(comp)
        if not sets:
            return None

        # Default behavior (no temperature provided): prefer the set that spans
        # the highest temperatures (most useful for boiling/operating points).
        chosen = max(sets, key=lambda s: s.Tmax_C)
        if T_celsius is not None:
            for s in sets:
                if s.Tmin_C <= T_celsius <= s.Tmax_C:
                    chosen = s
                    break

        return {
            "compound_name": comp.get("name", ""),
            "A": chosen.A,
            "B": chosen.B,
            "C": chosen.C,
            "T_min": chosen.Tmin_C,
            "T_max": chosen.Tmax_C,
            "source": chosen.source,
        }

    # ── NRTL queries ───────────────────────────────────────────────────

    def get_nrtl(self, comp1: str, comp2: str, T_kelvin: float = 298.15) -> Optional[Dict[str, Any]]:
        """Return NRTL parameters for (comp1, comp2).

        Supports:
            - form=dg_const: parameters {dg12, dg21, alpha}
            - form=tau_AplusBoverT: parameters {comp1_to_comp2:{A,B}, comp2_to_comp1:{A,B}, alpha}

        Always returns dg12/dg21/alpha12 at the provided T.
        """
        k1 = _norm(comp1)
        k2 = _norm(comp2)

        for rec in self._db.get("binary_interactions", []) or []:
            if rec.get("model_family") != "NRTL":
                continue
            comps = rec.get("components", []) or []
            if len(comps) != 2:
                continue
            a = _norm(comps[0])
            b = _norm(comps[1])
            if not ((a == k1 and b == k2) or (a == k2 and b == k1)):
                continue

            form = rec.get("form")
            params = rec.get("parameters", {}) or {}
            alpha = float(params.get("alpha", params.get("alpha12", 0.3)))

            if form == "dg_const":
                dg12 = float(params.get("dg12"))
                dg21 = float(params.get("dg21"))
            elif form == "tau_AplusBoverT":
                # tau = A + B/T
                key12 = f"{comps[0]}_to_{comps[1]}"
                key21 = f"{comps[1]}_to_{comps[0]}"
                p12 = params.get(key12) or params.get("comp1_to_comp2") or params.get("MEA_to_H2O")
                p21 = params.get(key21) or params.get("comp2_to_comp1") or params.get("H2O_to_MEA")
                if not p12 or not p21:
                    return None
                tau12 = float(p12.get("A")) + float(p12.get("B")) / float(T_kelvin)
                tau21 = float(p21.get("A")) + float(p21.get("B")) / float(T_kelvin)
                R = 8.314
                dg12 = tau12 * R * float(T_kelvin)
                dg21 = tau21 * R * float(T_kelvin)
            else:
                return None

            # If order is reversed, swap
            if a != k1:
                dg12, dg21 = dg21, dg12

            return {
                "comp1": comp1,
                "comp2": comp2,
                "dg12": dg12,
                "dg21": dg21,
                "alpha12": alpha,
                "T_ref": T_kelvin,
                "source": rec.get("source_ref", ""),
            }

        return None

    # ── Henry queries ──────────────────────────────────────────────────

    def get_henry(self, gas: str, solvent: str = "water") -> Optional[Dict[str, Any]]:
        comp = self._resolve_component(gas)
        if not comp:
            return None
        for corr in comp.get("correlations", []) or []:
            if corr.get("property") != "Henry_Hpa":
                continue
            p = corr.get("parameters", {}) or {}
            if _norm(p.get("solvent", "water")) != _norm(solvent):
                continue
            return {
                "gas": gas,
                "solvent": solvent,
                "H_pa": float(p.get("H_pa")),
                "dH_sol": float(p.get("dH_sol_J_mol", 0.0)),
                "T_ref": float(p.get("T_ref_K", 298.15)),
                "source": corr.get("source_ref", ""),
            }
        return None

    def list_henry(self, solvent: str = "water") -> List[Dict[str, Any]]:
        out = []
        for c in self._db.get("components", []) or []:
            rec = self.get_henry(c.get("id", ""), solvent=solvent)
            if rec:
                out.append(rec)
        out.sort(key=lambda r: _norm(r.get("gas", "")))
        return out

    # ── Packing queries (not yet in JSON DB) ────────────────────────────

    def get_packing(self, name: str) -> Optional[Dict[str, Any]]:
        n = _norm(name)
        for p in self._db.get("packings", []) or []:
            if _norm(p.get("name", "")) == n:
                return dict(p)
        return None

    def list_packings(self, packing_type: str = None) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for p in self._db.get("packings", []) or []:
            if packing_type and _norm(p.get("type", "")) != _norm(packing_type):
                continue
            out.append(dict(p))
        out.sort(key=lambda r: _norm(r.get("name", "")))
        return out

    # ── Interaction listing helpers ────────────────────────────────────

    def list_nrtl_pairs(self) -> List[Dict[str, Any]]:
        """List all NRTL binary interaction pairs.

        Returns a list of dicts:
            {comp1, comp2, alpha12, comp1_name, comp2_name, source}

        Notes:
            - comp1/comp2 are returned as stored in the DB.
            - comp*_name are resolved via component lookup when possible.
        """
        out: List[Dict[str, Any]] = []
        for rec in self._db.get("binary_interactions", []) or []:
            if rec.get("model_family") != "NRTL":
                continue
            comps = rec.get("components", []) or []
            if len(comps) != 2:
                continue
            c1, c2 = str(comps[0]), str(comps[1])
            p = rec.get("parameters", {}) or {}
            alpha = float(p.get("alpha", p.get("alpha12", 0.3)))
            r1 = self.get_compound(c1) or {}
            r2 = self.get_compound(c2) or {}
            out.append(
                {
                    "comp1": c1,
                    "comp2": c2,
                    "alpha12": alpha,
                    "comp1_name": r1.get("name", c1),
                    "comp2_name": r2.get("name", c2),
                    "source": rec.get("source_ref", ""),
                }
            )

        out.sort(key=lambda r: (_norm(r.get("comp1", "")), _norm(r.get("comp2", ""))))
        return out

    # ── Mutating methods (DB is treated as read-only in-engine) ─────────

    def add_compound(self, **kwargs):
        raise NotImplementedError("JSON DB is read-only in-engine")

    def add_antoine(self, **kwargs):
        raise NotImplementedError("JSON DB is read-only in-engine")

    def add_nrtl(self, **kwargs):
        raise NotImplementedError("JSON DB is read-only in-engine")

    def add_henry(self, **kwargs):
        raise NotImplementedError("JSON DB is read-only in-engine")

    def add_packing(self, **kwargs):
        raise NotImplementedError("JSON DB is read-only in-engine")
