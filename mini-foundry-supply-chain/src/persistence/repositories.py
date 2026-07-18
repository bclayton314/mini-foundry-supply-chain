import json
from datetime import datetime, timezone
from typing import Any

from actions.action_models import ActionResult, ActionStatus, ActionType
from ontology.objects import AlertStatus, RiskAlert
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

    Existing alerts keep their lifecycle status. New alerts are created as OPEN.
    This prevents each pipeline run from resetting RESOLVED or DISMISSED alerts.
    """
    for alert in alerts:
        existing = session.get(RiskAlertRecord, alert.alert_id)

        if existing is not None:
            existing.alert_type = alert.alert_type.value
            existing.severity = alert.severity.value
            existing.message = alert.message
            existing.related_object_type = alert.related_object_type
            existing.related_object_id = alert.related_object_id
            existing.recommended_action = alert.recommended_action
            continue

        record = RiskAlertRecord(
            alert_id=alert.alert_id,
            alert_type=alert.alert_type.value,
            severity=alert.severity.value,
            message=alert.message,
            related_object_type=alert.related_object_type,
            related_object_id=alert.related_object_id,
            recommended_action=alert.recommended_action,
            status=AlertStatus.OPEN.value,
            status_note=None,
            acknowledged_by=None,
            acknowledged_at=None,
            resolved_by=None,
            resolved_at=None,
            dismissed_by=None,
            dismissed_at=None,
            created_at=datetime.now(timezone.utc),
        )

        session.add(record)

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

    if result.status != ActionStatus.SUCCESS:
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
    """
    save_action_result(session, result)
    save_reorder_request_from_action(session, result)


def list_recent_alerts(
    session: Session,
    limit: int = 10,
    status: str | None = None,
) -> list[RiskAlertRecord]:
    """
    Return recent risk alerts, optionally filtered by lifecycle status.
    """
    query = session.query(RiskAlertRecord)

    if status is not None:
        query = query.filter(RiskAlertRecord.status == status)

    return (
        query
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


def get_alert_by_id(
    session: Session,
    alert_id: str,
) -> RiskAlertRecord | None:
    """
    Fetch a persisted alert by ID.
    """
    return session.get(RiskAlertRecord, alert_id)


def acknowledge_alert(
    session: Session,
    alert_id: str,
    user: str,
    note: str,
) -> ActionResult:
    """
    Mark an alert as ACKNOWLEDGED.
    """
    alert = get_alert_by_id(session, alert_id)

    if alert is None:
        result = ActionResult(
            action_type=ActionType.ACKNOWLEDGE_ALERT,
            status=ActionStatus.FAILED,
            message=f"Alert {alert_id} was not found.",
            user=user,
            related_object_type="RiskAlert",
            related_object_id=alert_id,
            metadata={"note": note},
        )
        save_action_result(session, result)
        return result

    if alert.status in {AlertStatus.RESOLVED.value, AlertStatus.DISMISSED.value}:
        result = ActionResult(
            action_type=ActionType.ACKNOWLEDGE_ALERT,
            status=ActionStatus.FAILED,
            message=f"Alert {alert_id} is already {alert.status}.",
            user=user,
            related_object_type="RiskAlert",
            related_object_id=alert_id,
            metadata={"current_status": alert.status, "note": note},
        )
        save_action_result(session, result)
        return result

    now = datetime.now(timezone.utc)

    alert.status = AlertStatus.ACKNOWLEDGED.value
    alert.acknowledged_by = user
    alert.acknowledged_at = now
    alert.status_note = note

    result = ActionResult(
        action_type=ActionType.ACKNOWLEDGE_ALERT,
        status=ActionStatus.SUCCESS,
        message=f"Alert {alert_id} was acknowledged.",
        user=user,
        related_object_type="RiskAlert",
        related_object_id=alert_id,
        metadata={
            "new_status": alert.status,
            "note": note,
        },
    )

    save_action_result(session, result)
    session.commit()
    return result


def resolve_alert_record(
    session: Session,
    alert_id: str,
    user: str,
    note: str,
) -> ActionResult:
    """
    Mark an alert as RESOLVED.
    """
    alert = get_alert_by_id(session, alert_id)

    if alert is None:
        result = ActionResult(
            action_type=ActionType.RESOLVE_ALERT,
            status=ActionStatus.FAILED,
            message=f"Alert {alert_id} was not found.",
            user=user,
            related_object_type="RiskAlert",
            related_object_id=alert_id,
            metadata={"note": note},
        )
        save_action_result(session, result)
        return result

    if alert.status == AlertStatus.RESOLVED.value:
        result = ActionResult(
            action_type=ActionType.RESOLVE_ALERT,
            status=ActionStatus.FAILED,
            message=f"Alert {alert_id} is already resolved.",
            user=user,
            related_object_type="RiskAlert",
            related_object_id=alert_id,
            metadata={"current_status": alert.status, "note": note},
        )
        save_action_result(session, result)
        return result

    if alert.status == AlertStatus.DISMISSED.value:
        result = ActionResult(
            action_type=ActionType.RESOLVE_ALERT,
            status=ActionStatus.FAILED,
            message=f"Alert {alert_id} was dismissed and cannot be resolved.",
            user=user,
            related_object_type="RiskAlert",
            related_object_id=alert_id,
            metadata={"current_status": alert.status, "note": note},
        )
        save_action_result(session, result)
        return result

    now = datetime.now(timezone.utc)

    alert.status = AlertStatus.RESOLVED.value
    alert.resolved_by = user
    alert.resolved_at = now
    alert.status_note = note

    result = ActionResult(
        action_type=ActionType.RESOLVE_ALERT,
        status=ActionStatus.SUCCESS,
        message=f"Alert {alert_id} was resolved.",
        user=user,
        related_object_type="RiskAlert",
        related_object_id=alert_id,
        metadata={
            "new_status": alert.status,
            "note": note,
        },
    )

    save_action_result(session, result)
    session.commit()
    return result


def dismiss_alert(
    session: Session,
    alert_id: str,
    user: str,
    note: str,
) -> ActionResult:
    """
    Mark an alert as DISMISSED.
    """
    alert = get_alert_by_id(session, alert_id)

    if alert is None:
        result = ActionResult(
            action_type=ActionType.DISMISS_ALERT,
            status=ActionStatus.FAILED,
            message=f"Alert {alert_id} was not found.",
            user=user,
            related_object_type="RiskAlert",
            related_object_id=alert_id,
            metadata={"note": note},
        )
        save_action_result(session, result)
        return result

    if alert.status == AlertStatus.RESOLVED.value:
        result = ActionResult(
            action_type=ActionType.DISMISS_ALERT,
            status=ActionStatus.FAILED,
            message=f"Alert {alert_id} is already resolved and cannot be dismissed.",
            user=user,
            related_object_type="RiskAlert",
            related_object_id=alert_id,
            metadata={"current_status": alert.status, "note": note},
        )
        save_action_result(session, result)
        return result

    if alert.status == AlertStatus.DISMISSED.value:
        result = ActionResult(
            action_type=ActionType.DISMISS_ALERT,
            status=ActionStatus.FAILED,
            message=f"Alert {alert_id} is already dismissed.",
            user=user,
            related_object_type="RiskAlert",
            related_object_id=alert_id,
            metadata={"current_status": alert.status, "note": note},
        )
        save_action_result(session, result)
        return result

    now = datetime.now(timezone.utc)

    alert.status = AlertStatus.DISMISSED.value
    alert.dismissed_by = user
    alert.dismissed_at = now
    alert.status_note = note

    result = ActionResult(
        action_type=ActionType.DISMISS_ALERT,
        status=ActionStatus.SUCCESS,
        message=f"Alert {alert_id} was dismissed.",
        user=user,
        related_object_type="RiskAlert",
        related_object_id=alert_id,
        metadata={
            "new_status": alert.status,
            "note": note,
        },
    )

    save_action_result(session, result)
    session.commit()
    return result