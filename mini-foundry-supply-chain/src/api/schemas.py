from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class PipelineRunResponse(BaseModel):
    message: str
    alerts_generated: int
    alerts_saved: int


class RiskAlertResponse(BaseModel):
    alert_id: str
    alert_type: str
    severity: str
    message: str
    related_object_type: str
    related_object_id: str
    recommended_action: str
    status: str
    status_note: str | None
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    resolved_by: str | None
    resolved_at: datetime | None
    dismissed_by: str | None
    dismissed_at: datetime | None
    created_at: datetime


class ActionResultResponse(BaseModel):
    id: int
    action_type: str
    status: str
    message: str
    user: str
    related_object_type: str
    related_object_id: str
    timestamp: datetime
    metadata: dict[str, Any]


class ReorderRequestResponse(BaseModel):
    id: int
    part_id: str
    part_name: str
    supplier_id: str | None
    supplier_name: str | None
    requested_quantity: int
    requested_by: str
    status: str
    created_at: datetime


class ReorderRequestCreate(BaseModel):
    part_id: str = Field(..., examples=["PART-004"])
    quantity: int = Field(..., gt=0, examples=[200])
    user: str = Field(..., examples=["clayton"])


class ExpediteShipmentRequest(BaseModel):
    shipment_id: str = Field(..., examples=["SHIP-003"])
    user: str = Field(..., examples=["clayton"])


class MarkSupplierWatchlistRequest(BaseModel):
    supplier_id: str = Field(..., examples=["SUP-003"])
    user: str = Field(..., examples=["clayton"])
    reason: str = Field(..., examples=["Repeated shipment delays."])


class AcknowledgeAlertRequest(BaseModel):
    user: str = Field(..., examples=["clayton"])
    note: str = Field(..., examples=["Review started."])


class ResolveAlertRequest(BaseModel):
    user: str = Field(..., examples=["clayton"])
    resolution_note: str = Field(
        ...,
        examples=["Mitigation action created and assigned for follow-up."],
    )


class DismissAlertRequest(BaseModel):
    user: str = Field(..., examples=["clayton"])
    note: str = Field(..., examples=["Duplicate of another alert."])