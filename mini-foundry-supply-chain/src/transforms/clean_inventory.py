from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "inventory_id",
    "part_id",
    "current_stock",
    "reorder_threshold",
    "warehouse_location",
]


def clean_inventory(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """
    Clean the raw inventory dataset.

    Responsibilities:
    - Normalize column names
    - Validate required columns
    - Clean IDs and warehouse names
    - Convert stock values to integers
    - Save cleaned output to CSV
    """
    df = pd.read_csv(input_path)

    df.columns = [column.strip().lower() for column in df.columns]

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Inventory file is missing columns: {missing_columns}")

    df["inventory_id"] = df["inventory_id"].astype(str).str.strip().str.upper()
    df["part_id"] = df["part_id"].astype(str).str.strip().str.upper()
    df["warehouse_location"] = df["warehouse_location"].astype(str).str.strip()

    df["current_stock"] = pd.to_numeric(
        df["current_stock"],
        errors="coerce",
    ).fillna(0)

    df["reorder_threshold"] = pd.to_numeric(
        df["reorder_threshold"],
        errors="coerce",
    ).fillna(0)

    df["current_stock"] = df["current_stock"].clip(lower=0).astype(int)
    df["reorder_threshold"] = df["reorder_threshold"].clip(lower=0).astype(int)

    df = df.dropna(subset=["inventory_id", "part_id"])
    df = df.drop_duplicates(subset=["inventory_id"])

    df.to_csv(output_path, index=False)

    return df