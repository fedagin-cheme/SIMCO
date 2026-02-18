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
from ...database.db import ChemicalDatabase


def search_compounds(query: str, db_path: str = None) -> List[Dict[str, Any]]:
    """Search compounds by name or formula."""
    kwargs = {"db_path": db_path} if db_path else {}
    with ChemicalDatabase(**kwargs) as db:
        return db.search_compounds(query)


def get_compound_details(name: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get full compound properties."""
    kwargs = {"db_path": db_path} if db_path else {}
    with ChemicalDatabase(**kwargs) as db:
        return db.get_compound(name)


def list_all_compounds(category: str = None, db_path: str = None) -> List[Dict[str, Any]]:
    """List all compounds, optionally by category."""
    kwargs = {"db_path": db_path} if db_path else {}
    with ChemicalDatabase(**kwargs) as db:
        return db.list_compounds(category)


def get_antoine_data(compound: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get Antoine coefficients for a compound."""
    kwargs = {"db_path": db_path} if db_path else {}
    with ChemicalDatabase(**kwargs) as db:
        return db.get_antoine(compound)


def get_nrtl_data(comp1: str, comp2: str, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get NRTL binary interaction parameters."""
    kwargs = {"db_path": db_path} if db_path else {}
    with ChemicalDatabase(**kwargs) as db:
        return db.get_nrtl(comp1, comp2)


def get_henry_data(gas: str, solvent: str = "water", db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get Henry's law constant."""
    kwargs = {"db_path": db_path} if db_path else {}
    with ChemicalDatabase(**kwargs) as db:
        return db.get_henry(gas, solvent)


def list_packings(packing_type: str = None, db_path: str = None) -> List[Dict[str, Any]]:
    """List available packing types."""
    kwargs = {"db_path": db_path} if db_path else {}
    with ChemicalDatabase(**kwargs) as db:
        return db.list_packings(packing_type)
