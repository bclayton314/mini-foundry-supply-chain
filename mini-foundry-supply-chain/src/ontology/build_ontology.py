from typing import Any

import pandas as pd

from ontology.objects import InventoryItem, Part, Shipment, Supplier


def _clean_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Convert Pandas NaN values to None before creating Pydantic objects.

    Pandas uses NaN for missing values, but Pydantic models generally expect
    None for optional fields.
    """
    cleaned = {}

    for key, value in record.items():
        if pd.isna(value):
            cleaned[key] = None
        else:
            cleaned[key] = value

    return cleaned


def build_suppliers(df: pd.DataFrame) -> list[Supplier]:
    """
    Build Supplier ontology objects from a cleaned suppliers DataFrame.
    """
    suppliers = []

    for record in df.to_dict(orient="records"):
        cleaned_record = _clean_record(record)
        supplier = Supplier(**cleaned_record)
        suppliers.append(supplier)

    return suppliers


def build_parts(df: pd.DataFrame) -> list[Part]:
    """
    Build Part ontology objects from a cleaned parts DataFrame.
    """
    parts = []

    for record in df.to_dict(orient="records"):
        cleaned_record = _clean_record(record)
        part = Part(**cleaned_record)
        parts.append(part)

    return parts


def build_shipments(df: pd.DataFrame) -> list[Shipment]:
    """
    Build Shipment ontology objects from a cleaned shipments DataFrame.
    """
    shipments = []

    for record in df.to_dict(orient="records"):
        cleaned_record = _clean_record(record)
        shipment = Shipment(**cleaned_record)
        shipments.append(shipment)

    return shipments


def build_inventory_items(df: pd.DataFrame) -> list[InventoryItem]:
    """
    Build InventoryItem ontology objects from a cleaned inventory DataFrame.
    """
    inventory_items = []

    for record in df.to_dict(orient="records"):
        cleaned_record = _clean_record(record)
        inventory_item = InventoryItem(**cleaned_record)
        inventory_items.append(inventory_item)

    return inventory_items


def build_ontology(cleaned_data: dict[str, pd.DataFrame]) -> dict[str, list]:
    """
    Build all ontology objects from cleaned DataFrames.
    """
    suppliers = build_suppliers(cleaned_data["suppliers_clean"])
    parts = build_parts(cleaned_data["parts_clean"])
    shipments = build_shipments(cleaned_data["shipments_clean"])
    inventory_items = build_inventory_items(cleaned_data["inventory_clean"])

    return {
        "suppliers": suppliers,
        "parts": parts,
        "shipments": shipments,
        "inventory_items": inventory_items,
    }