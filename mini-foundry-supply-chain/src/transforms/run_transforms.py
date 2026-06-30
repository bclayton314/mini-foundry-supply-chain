from pathlib import Path

import pandas as pd

from transforms.clean_inventory import clean_inventory
from transforms.clean_parts import clean_parts
from transforms.clean_shipments import clean_shipments
from transforms.clean_suppliers import clean_suppliers


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PACKAGE_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PACKAGE_ROOT / "data" / "processed"


def run_all_transforms() -> dict[str, pd.DataFrame]:
    """
    Run every cleaning transform and return the cleaned datasets.

    This function represents the project's local version of a Foundry-style
    transform pipeline.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    suppliers = clean_suppliers(
        input_path=RAW_DATA_DIR / "suppliers.csv",
        output_path=PROCESSED_DATA_DIR / "suppliers_clean.csv",
    )

    parts = clean_parts(
        input_path=RAW_DATA_DIR / "parts.csv",
        output_path=PROCESSED_DATA_DIR / "parts_clean.csv",
    )

    shipments = clean_shipments(
        input_path=RAW_DATA_DIR / "shipments.csv",
        output_path=PROCESSED_DATA_DIR / "shipments_clean.csv",
    )

    inventory = clean_inventory(
        input_path=RAW_DATA_DIR / "inventory.csv",
        output_path=PROCESSED_DATA_DIR / "inventory_clean.csv",
    )

    return {
        "suppliers_clean": suppliers,
        "parts_clean": parts,
        "shipments_clean": shipments,
        "inventory_clean": inventory,
    }