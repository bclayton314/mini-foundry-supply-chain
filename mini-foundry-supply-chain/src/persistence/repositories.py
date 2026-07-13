import json
from datetime import datetime, timezone
from typing import Any

from actions.action_models import ActionResult, ActionType
from ontology.objects import RiskAlert
from persistence.models import (
    ActionResultRecord,
    ReorderRequestRecord,
    RiskAlertRecord,
)
from sqlalchemy.orm import Session


def _json_safe_metadata(metadata: dict[str, Any]) -> str:
    """
    Convert metadata into a JSON string safe for database storage.
    """
    return json.dumps(metadata, default=str)


def save_risk_alerts(
    session: Session,
    alerts: list[RiskAlert],
) -> None:
    """
    Save risk alerts to the database.

    This uses merge() so rerunning the program updates existing alert IDs
    instead of crashing on duplicate primary keys.
    """
    for alert in alerts:
        record = RiskAlertRecord(
            alert_id=alert.alert_id,
            alert_type=alert.alert_type.value,
            severity=alert.severity.value,
            message=alert.message,
            related_object_type=alert.related_object_type,
            related_object_id=alert.related_object_id,
            recommended_action=alert.recommended_action,
            created_at=datetime.now(timezone.utc),
        )

        session.merge(record)

    session.commit()


def save_action_result(
    session: Session,
    result: ActionResult,
) -> None:
    """
    Save an action result to the database.
    """
    record = ActionResultRecord(
        action_type=result.action_type.value,
        status=result.status.value,
        message=result.message,
        user=result.user,
        related_object_type=result.related_object_type,
        related_object_id=result.related_object_id,
        timestamp=result.timestamp,
        metadata_json=_json_safe_metadata(result.metadata),
    )

    session.add(record)
    session.commit()


def save_reorder_request_from_action(
    session: Session,
    result: ActionResult,
) -> None:
    """
    Create a reorder_requests database row from a successful reorder action.
    """
    if result.action_type != ActionType.CREATE_REORDER_REQUEST:
        return

    if result.status.value != "SUCCESS":
        return

    record = ReorderRequestRecord(
        part_id=result.related_object_id,
        part_name=result.metadata.get("part_name", "UNKNOWN"),
        supplier_id=result.metadata.get("supplier_id"),
        supplier_name=result.metadata.get("supplier_name"),
        requested_quantity=int(result.metadata.get("requested_quantity", 0)),
        requested_by=result.user,
        status="OPEN",
        created_at=result.timestamp,
    )

    session.add(record)
    session.commit()


def save_action_and_side_effects(
    session: Session,
    result: ActionResult,
) -> None:
    """
    Save an action result and any related side-effect records.

    Example:
    - CREATE_REORDER_REQUEST action also creates a reorder_requests row.
    """
    save_action_result(session, result)
    save_reorder_request_from_action(session, result)


def list_recent_alerts(
    session: Session,
    limit: int = 10,
) -> list[RiskAlertRecord]:
    """
    Return recent risk alerts.
    """
    return (
        session.query(RiskAlertRecord)
        .order_by(RiskAlertRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def list_recent_actions(
    session: Session,
    limit: int = 10,
) -> list[ActionResultRecord]:
    """
    Return recent action records.
    """
    return (
        session.query(ActionResultRecord)
        .order_by(ActionResultRecord.timestamp.desc())
        .limit(limit)
        .all()
    )


def list_open_reorder_requests(
    session: Session,
    limit: int = 10,
) -> list[ReorderRequestRecord]:
    """
    Return recent open reorder requests.
    """
    return (
        session.query(ReorderRequestRecord)
        .filter(ReorderRequestRecord.status == "OPEN")
        .order_by(ReorderRequestRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def count_records(session: Session) -> dict[str, int]:
    """
    Count records in each persistence table.
    """
    return {
        "risk_alerts": session.query(RiskAlertRecord).count(),
        "action_results": session.query(ActionResultRecord).count(),
        "reorder_requests": session.query(ReorderRequestRecord).count(),
    }