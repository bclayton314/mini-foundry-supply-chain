from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PACKAGE_ROOT / "data" / "raw"


def load_csv(filename: str) -> pd.DataFrame:
    """
    Load a single CSV file from the raw data directory.
    """
    file_path = RAW_DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Could not find raw data file: {file_path}")

    return pd.read_csv(file_path)


def load_suppliers() -> pd.DataFrame:
    """
    Load the raw suppliers dataset.
    """
    return load_csv("suppliers.csv")


def load_parts() -> pd.DataFrame:
    """
    Load the raw parts dataset.
    """
    return load_csv("parts.csv")


def load_shipments() -> pd.DataFrame:
    """
    Load the raw shipments dataset.
    """
    return load_csv("shipments.csv")


def load_inventory() -> pd.DataFrame:
    """
    Load the raw inventory dataset.
    """
    return load_csv("inventory.csv")


def load_all_raw_data() -> dict[str, pd.DataFrame]:
    """
    Load all raw datasets and return them in a dictionary.

    The dictionary keys represent dataset names.
    The values are Pandas DataFrames.
    """
    return {
        "suppliers": load_suppliers(),
        "parts": load_parts(),
        "shipments": load_shipments(),
        "inventory": load_inventory(),
    }