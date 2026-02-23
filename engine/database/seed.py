"""engine.database.seed

The engine database is now JSON-backed and shipped with the repository at:
    engine/database/simco_chemdb.json

This seeding script is kept for test parity and for creating a writable copy of
that JSON database (e.g. for experimentation).

Usage:
    python -m engine.database.seed              # writes a copy next to this file
    python -m engine.database.seed /path/to/db.json

Note:
    The in-engine ChemicalDatabase is treated as read-only.
"""

from __future__ import annotations

import os
import shutil
import sys


def seed_database(db_path: str | None = None) -> str:
    """Create a copy of the shipped JSON DB at db_path.

    Tests pass a temporary path (often ending in .db). We still write JSON to
    that path, because the DB backend is JSON.

    Returns the path written.
    """

    src = os.path.join(os.path.dirname(__file__), "simco_chemdb.json")

    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), "simco_chemdb_copy.json")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    shutil.copyfile(src, db_path)
    return db_path


if __name__ == "__main__":
    out = seed_database(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"Wrote DB copy: {out}")
