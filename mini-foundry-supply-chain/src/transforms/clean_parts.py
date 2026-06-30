from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "part_id",
    "part_name",
    "category",
    "criticality",
    "supplier_id",
]


VALID_CRITICALITY_LEVELS = {"LOW", "MEDIUM", "HIGH"}


def clean_parts(input_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """
    Clean the raw parts dataset.

    Responsibilities:
    - Normalize column names
    - Validate required columns
    - Clean IDs and text fields
    - Normalize criticality values
    - Save cleaned output to CSV
    """
    df = pd.read_csv(input_path)

    df.columns = [column.strip().lower() for column in df.columns]

    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Parts file is missing columns: {missing_columns}")

    df["part_id"] = df["part_id"].astype(str).str.strip().str.upper()
    df["part_name"] = df["part_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["criticality"] = df["criticality"].astype(str).str.strip().str.upper()
    df["supplier_id"] = df["supplier_id"].astype(str).str.strip().str.upper()

    df.loc[
        ~df["criticality"].isin(VALID_CRITICALITY_LEVELS),
        "criticality",
    ] = "MEDIUM"

    df = df.dropna(subset=["part_id", "part_name", "supplier_id"])
    df = df.drop_duplicates(subset=["part_id"])

    df.to_csv(output_path, index=False)

    return df