"""Default reference tables (to be replaced or persisted later). Edited in the Reference section."""

from __future__ import annotations

import pandas as pd


def default_solution_mass_by_category() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "product_category": ["Example A", "Example B", "Example C"],
            "min_solution_mass_mg": [0.0, 10.0, 5.0],
            "max_solution_mass_mg": [50.0, 200.0, 100.0],
            "notes": ["", "placeholder", ""],
        }
    )


def default_isotope_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "isotope": ["F-18", "I-123", "Tc-99m"],
            "unit_default": ["GBq", "MBq", "mCi"],
            "active": [True, True, True],
        }
    )
