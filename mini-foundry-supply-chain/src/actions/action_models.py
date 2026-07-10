from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ActionType(str, Enum):
    CREATE_REORDER_REQUEST = "CREATE_REORDER_REQUEST"
    EXPEDITE_SHIPMENT = "EXPEDITE_SHIPMENT"
    MARK_SUPPLIER_WATCHLIST = "MARK_SUPPLIER_WATCHLIST"
    RESOLVE_ALERT = "RESOLVE_ALERT"


class ActionResult(BaseModel):
    action_type: ActionType
    status: ActionStatus
    message: str
    user: str
    related_object_type: str
    related_object_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = Field(default_factory=dict)