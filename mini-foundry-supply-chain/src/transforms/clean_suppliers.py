from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "supplier_id",
    "supplier_name",
    "country",
    "reliability_score",
    "status",
]


VALID_STATUSES = {"ACTIVE", "WATCHLIST", "INACTIVE"}


def clean_suppliers(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """
    Clean the raw suppliers dataset.

    Responsibilities:
    - Normalize column names
    - Validate required columns
    - Clean string fields
    - Convert reliability_score to numeric
    - Normalize supplier status
    - Save cleaned output to CSV
    """
    df = pd.read_csv(input_path)

    df.columns = [column.strip().lower() for column in df.columns]

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Suppliers file is missing columns: {missing_columns}")

    df["supplier_id"] = df["supplier_id"].astype(str).str.strip().str.upper()
    df["supplier_name"] = df["supplier_name"].astype(str).str.strip()
    df["country"] = df["country"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip().str.upper()

    df["reliability_score"] = pd.to_numeric(
        df["reliability_score"],
        errors="coerce",
    )

    df = df.dropna(subset=["supplier_id", "supplier_name", "reliability_score"])

    df["reliability_score"] = df["reliability_score"].clip(lower=0.0, upper=1.0)

    df.loc[~df["status"].isin(VALID_STATUSES), "status"] = "WATCHLIST"

    df = df.drop_duplicates(subset=["supplier_id"])

    df.to_csv(output_path, index=False)

    return df