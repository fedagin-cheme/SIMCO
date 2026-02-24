"""
Database browsing API routes.

Handles requests for:
    - Compound lookup/search
    - Antoine coefficient retrieval
    - NRTL parameter retrieval
    - Henry's constant retrieval
    - Packing data retrieval
"""

from typing import Dict, Any, List, Optional
from ...database.db import ChemicalDatabase, get_db


def _get_instance(db_path: str = None) -> ChemicalDatabase:
    """Return a DB instance — singleton for default path, fresh for custom paths."""
    if db_path:
        db = ChemicalDatabase(db_path)
        db.connect()
        return db
    return get_db()


def search_compounds(query: str, db_path: str = None) -> List[Dict[str, Any]]:
    """Search compounds by name or formula."""
    return _get_instance(db_path).search_compounds(query)


def get_compound_details(name: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get full compound properties."""
    return _get_instance(db_path).get_compound(name)


def list_all_compounds(category: str = None, db_path: str = None) -> List[Dict[str, Any]]:
    """List all compounds, optionally by category."""
    return _get_instance(db_path).list_compounds(category)


def get_antoine_data(compound: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get Antoine coefficients for a compound."""
    return _get_instance(db_path).get_antoine(compound)


def get_nrtl_data(comp1: str, comp2: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get NRTL binary interaction parameters."""
    return _get_instance(db_path).get_nrtl(comp1, comp2)


def get_henry_data(gas: str, solvent: str = "water", db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get Henry's law constant."""
    return _get_instance(db_path).get_henry(gas, solvent)


def list_packings(packing_type: str = None, db_path: str = None) -> List[Dict[str, Any]]:
    """List available packing types."""
    return _get_instance(db_path).list_packings(packing_type)
