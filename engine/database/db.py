"""
Chemical property database backed by SQLite.

Stores:
    - Compound properties (MW, Tc, Pc, omega, etc.)
    - Antoine coefficients
    - NRTL binary interaction parameters
    - Henry's law constants
    - Packing characteristics (HETP, specific surface area, void fraction)
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "simco_chemicals.db")


class ChemicalDatabase:
    """Interface to the SIMCO chemical property database."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn = None

    def connect(self):
        """Open connection and ensure tables exist."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        return self

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ── Schema ────────────────────────────────────────────

    def _create_tables(self):
        cur = self._conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS compounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                formula TEXT,
                cas_number TEXT,
                mw REAL,              -- g/mol
                tc REAL,              -- Critical temperature [K]
                pc REAL,              -- Critical pressure [Pa]
                omega REAL,           -- Acentric factor
                tb REAL,              -- Normal boiling point [K]
                category TEXT         -- 'solvent', 'gas', 'acid', etc.
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS antoine_coefficients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compound_name TEXT NOT NULL,
                A REAL NOT NULL,
                B REAL NOT NULL,
                C REAL NOT NULL,
                T_min REAL,           -- Valid range [°C]
                T_max REAL,
                source TEXT,
                FOREIGN KEY (compound_name) REFERENCES compounds(name)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS nrtl_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comp1 TEXT NOT NULL,
                comp2 TEXT NOT NULL,
                dg12 REAL NOT NULL,   -- J/mol
                dg21 REAL NOT NULL,   -- J/mol
                alpha12 REAL NOT NULL,
                T_ref REAL,           -- Reference temperature [K]
                source TEXT,
                UNIQUE(comp1, comp2)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS henry_constants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gas TEXT NOT NULL,
                solvent TEXT NOT NULL DEFAULT 'water',
                H_pa REAL NOT NULL,   -- Henry's constant [Pa]
                dH_sol REAL,          -- Enthalpy of dissolution [J/mol]
                T_ref REAL DEFAULT 298.15,
                source TEXT,
                UNIQUE(gas, solvent)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS packing_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT,            -- 'random', 'structured'
                material TEXT,        -- 'metal', 'ceramic', 'plastic'
                nominal_size_mm REAL,
                specific_area REAL,   -- m²/m³
                void_fraction REAL,
                packing_factor REAL,  -- 1/m
                hetp REAL,            -- m (typical)
                source TEXT
            )
        """)

        self._conn.commit()

    # ── Compound queries ──────────────────────────────────

    def get_compound(self, name: str) -> Optional[Dict[str, Any]]:
        """Get compound properties by name."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM compounds WHERE LOWER(name) = LOWER(?)", (name,))
        row = cur.fetchone()
        return dict(row) if row else None

    def search_compounds(self, query: str) -> List[Dict[str, Any]]:
        """Search compounds by name or formula (partial match)."""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM compounds WHERE LOWER(name) LIKE ? OR LOWER(formula) LIKE ?",
            (f"%{query.lower()}%", f"%{query.lower()}%"),
        )
        return [dict(row) for row in cur.fetchall()]

    def list_compounds(self, category: str = None) -> List[Dict[str, Any]]:
        """List all compounds, optionally filtered by category."""
        cur = self._conn.cursor()
        if category:
            cur.execute(
                "SELECT * FROM compounds WHERE LOWER(category) = LOWER(?) ORDER BY name",
                (category,),
            )
        else:
            cur.execute("SELECT * FROM compounds ORDER BY name")
        return [dict(row) for row in cur.fetchall()]

    # ── Antoine queries ───────────────────────────────────

    def get_antoine(self, compound_name: str) -> Optional[Dict[str, Any]]:
        """Get Antoine coefficients for a compound."""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM antoine_coefficients WHERE LOWER(compound_name) = LOWER(?)",
            (compound_name,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    # ── NRTL queries ──────────────────────────────────────

    def get_nrtl(self, comp1: str, comp2: str) -> Optional[Dict[str, Any]]:
        """Get NRTL binary parameters (handles order automatically)."""
        cur = self._conn.cursor()
        cur.execute(
            """SELECT * FROM nrtl_parameters
               WHERE (LOWER(comp1)=LOWER(?) AND LOWER(comp2)=LOWER(?))
                  OR (LOWER(comp1)=LOWER(?) AND LOWER(comp2)=LOWER(?))""",
            (comp1, comp2, comp2, comp1),
        )
        row = cur.fetchone()
        if not row:
            return None
        result = dict(row)
        # If the pair is reversed, swap dg12/dg21
        if result["comp1"].lower() != comp1.lower():
            result["dg12"], result["dg21"] = result["dg21"], result["dg12"]
            result["comp1"], result["comp2"] = comp1, comp2
        return result

    # ── Henry queries ─────────────────────────────────────

    def get_henry(self, gas: str, solvent: str = "water") -> Optional[Dict[str, Any]]:
        """Get Henry's law constant for a gas-solvent pair."""
        cur = self._conn.cursor()
        cur.execute(
            """SELECT * FROM henry_constants
               WHERE LOWER(gas)=LOWER(?) AND LOWER(solvent)=LOWER(?)""",
            (gas, solvent),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def list_henry(self, solvent: str = "water") -> List[Dict[str, Any]]:
        """List all Henry's constants for a solvent."""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM henry_constants WHERE LOWER(solvent)=LOWER(?) ORDER BY gas",
            (solvent,),
        )
        return [dict(row) for row in cur.fetchall()]

    # ── Packing queries ───────────────────────────────────

    def get_packing(self, name: str) -> Optional[Dict[str, Any]]:
        """Get packing characteristics by name."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM packing_data WHERE LOWER(name) = LOWER(?)", (name,))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_packings(self, packing_type: str = None) -> List[Dict[str, Any]]:
        """List all packings, optionally filtered by type."""
        cur = self._conn.cursor()
        if packing_type:
            cur.execute(
                "SELECT * FROM packing_data WHERE LOWER(type)=LOWER(?) ORDER BY name",
                (packing_type,),
            )
        else:
            cur.execute("SELECT * FROM packing_data ORDER BY name")
        return [dict(row) for row in cur.fetchall()]

    # ── Bulk insert helpers ───────────────────────────────

    def add_compound(self, **kwargs):
        """Insert a compound. kwargs: name, formula, cas_number, mw, tc, pc, omega, tb, category."""
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self._conn.execute(
            f"INSERT OR REPLACE INTO compounds ({cols}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        self._conn.commit()

    def add_antoine(self, **kwargs):
        """Insert Antoine coefficients."""
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self._conn.execute(
            f"INSERT OR REPLACE INTO antoine_coefficients ({cols}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        self._conn.commit()

    def add_nrtl(self, **kwargs):
        """Insert NRTL binary parameters."""
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self._conn.execute(
            f"INSERT OR REPLACE INTO nrtl_parameters ({cols}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        self._conn.commit()

    def add_henry(self, **kwargs):
        """Insert Henry's law constant."""
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self._conn.execute(
            f"INSERT OR REPLACE INTO henry_constants ({cols}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        self._conn.commit()

    def add_packing(self, **kwargs):
        """Insert packing data."""
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        self._conn.execute(
            f"INSERT OR REPLACE INTO packing_data ({cols}) VALUES ({placeholders})",
            tuple(kwargs.values()),
        )
        self._conn.commit()
