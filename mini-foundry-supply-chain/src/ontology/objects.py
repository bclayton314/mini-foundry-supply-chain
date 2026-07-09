from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class SupplierStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WATCHLIST = "WATCHLIST"
    INACTIVE = "INACTIVE"


class CriticalityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ShipmentStatus(str, Enum):
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class RiskSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskAlertType(str, Enum):
    LOW_INVENTORY = "LOW_INVENTORY"
    DELAYED_SHIPMENT = "DELAYED_SHIPMENT"
    WATCHLISTED_SUPPLIER = "WATCHLISTED_SUPPLIER"
    CRITICAL_PART_LOW_STOCK = "CRITICAL_PART_LOW_STOCK"
    CRITICAL_PART_DELAYED_SHIPMENT = "CRITICAL_PART_DELAYED_SHIPMENT"


class Supplier(BaseModel):
    supplier_id: str
    supplier_name: str
    country: str
    reliability_score: float = Field(ge=0.0, le=1.0)
    status: SupplierStatus


class Part(BaseModel):
    part_id: str
    part_name: str
    category: str
    criticality: CriticalityLevel
    supplier_id: str


class Shipment(BaseModel):
    shipment_id: str
    supplier_id: str
    part_id: str
    quantity: int = Field(ge=0)
    status: ShipmentStatus
    expected_delivery_date: date | None = None


class InventoryItem(BaseModel):
    inventory_id: str
    part_id: str
    current_stock: int = Field(ge=0)
    reorder_threshold: int = Field(ge=0)
    warehouse_location: str


class RiskAlert(BaseModel):
    alert_id: str
    alert_type: RiskAlertType
    severity: RiskSeverity
    message: str
    related_object_type: str
    related_object_id: str
    recommended_action: str