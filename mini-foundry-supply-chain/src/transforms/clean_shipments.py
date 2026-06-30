from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "shipment_id",
    "supplier_id",
    "part_id",
    "quantity",
    "status",
    "expected_delivery_date",
]


VALID_STATUSES = {"IN_TRANSIT", "DELIVERED", "DELAYED", "CANCELLED"}


def clean_shipments(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """
    Clean the raw shipments dataset.

    Responsibilities:
    - Normalize column names
    - Validate required columns
    - Clean IDs
    - Convert quantity to integer
    - Normalize shipment status
    - Parse expected delivery dates
    - Save cleaned output to CSV
    """
    df = pd.read_csv(input_path)

    df.columns = [column.strip().lower() for column in df.columns]

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Shipments file is missing columns: {missing_columns}")

    df["shipment_id"] = df["shipment_id"].astype(str).str.strip().str.upper()
    df["supplier_id"] = df["supplier_id"].astype(str).str.strip().str.upper()
    df["part_id"] = df["part_id"].astype(str).str.strip().str.upper()
    df["status"] = df["status"].astype(str).str.strip().str.upper()

    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["quantity"] = df["quantity"].clip(lower=0).astype(int)

    df["expected_delivery_date"] = pd.to_datetime(
        df["expected_delivery_date"],
        errors="coerce",
    )

    df.loc[~df["status"].isin(VALID_STATUSES), "status"] = "IN_TRANSIT"

    df = df.dropna(subset=["shipment_id", "supplier_id", "part_id"])
    df = df.drop_duplicates(subset=["shipment_id"])

    df.to_csv(output_path, index=False)

    return df