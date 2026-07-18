import json

from actions.action_models import ActionResult
from actions.operations import (
    create_reorder_request,
    expedite_shipment,
    mark_supplier_watchlist,
)
from ontology.build_ontology import build_ontology
from ontology.relationships import build_supply_chain_graph
from persistence.db import get_session, init_db
from persistence.models import ActionResultRecord, ReorderRequestRecord, RiskAlertRecord
from persistence.repositories import (
    acknowledge_alert,
    dismiss_alert,
    list_open_reorder_requests,
    list_recent_actions,
    list_recent_alerts,
    resolve_alert_record,
    save_action_and_side_effects,
    save_risk_alerts,
)
from risk.scoring import generate_risk_alerts
from transforms.run_transforms import run_all_transforms


VALID_ALERT_STATUSES = {
    "OPEN",
    "ACKNOWLEDGED",
    "RESOLVED",
    "DISMISSED",
}


def build_current_graph_and_alerts():
    """
    Run the current local data pipeline and return graph + generated alerts.
    """
    cleaned_data = run_all_transforms()
    ontology = build_ontology(cleaned_data)
    graph = build_supply_chain_graph(ontology)
    alerts = generate_risk_alerts(graph)

    return graph, alerts


def run_pipeline_and_save_alerts() -> tuple[int, int]:
    """
    Run transforms, build ontology, generate alerts, and save alerts to SQLite.
    """
    init_db()
    _, alerts = build_current_graph_and_alerts()

    with get_session() as session:
        save_risk_alerts(session, alerts)

    return len(alerts), len(alerts)


def serialize_alert_record(record: RiskAlertRecord) -> dict:
    """
    Convert a RiskAlertRecord ORM object into an API-safe dictionary.
    """
    return {
        "alert_id": record.alert_id,
        "alert_type": record.alert_type,
        "severity": record.severity,
        "message": record.message,
        "related_object_type": record.related_object_type,
        "related_object_id": record.related_object_id,
        "recommended_action": record.recommended_action,
        "status": record.status,
        "status_note": record.status_note,
        "acknowledged_by": record.acknowledged_by,
        "acknowledged_at": record.acknowledged_at,
        "resolved_by": record.resolved_by,
        "resolved_at": record.resolved_at,
        "dismissed_by": record.dismissed_by,
        "dismissed_at": record.dismissed_at,
        "created_at": record.created_at,
    }


def serialize_action_record(record: ActionResultRecord) -> dict:
    """
    Convert an ActionResultRecord ORM object into an API-safe dictionary.
    """
    try:
        metadata = json.loads(record.metadata_json)
    except json.JSONDecodeError:
        metadata = {}

    return {
        "id": record.id,
        "action_type": record.action_type,
        "status": record.status,
        "message": record.message,
        "user": record.user,
        "related_object_type": record.related_object_type,
        "related_object_id": record.related_object_id,
        "timestamp": record.timestamp,
        "metadata": metadata,
    }


def serialize_reorder_request_record(record: ReorderRequestRecord) -> dict:
    """
    Convert a ReorderRequestRecord ORM object into an API-safe dictionary.
    """
    return {
        "id": record.id,
        "part_id": record.part_id,
        "part_name": record.part_name,
        "supplier_id": record.supplier_id,
        "supplier_name": record.supplier_name,
        "requested_quantity": record.requested_quantity,
        "requested_by": record.requested_by,
        "status": record.status,
        "created_at": record.created_at,
    }


def get_alert_records(
    limit: int = 20,
    status: str | None = None,
) -> list[dict]:
    """
    Return recent alert records from SQLite.

    Optionally filter by lifecycle status.
    """
    init_db()

    normalized_status = status.upper() if status else None

    with get_session() as session:
        records = list_recent_alerts(
            session,
            limit=limit,
            status=normalized_status,
        )
        return [serialize_alert_record(record) for record in records]


def get_action_records(limit: int = 20) -> list[dict]:
    """
    Return recent action records from SQLite.
    """
    init_db()

    with get_session() as session:
        records = list_recent_actions(session, limit=limit)
        return [serialize_action_record(record) for record in records]


def get_open_reorder_requests(limit: int = 20) -> list[dict]:
    """
    Return open reorder requests from SQLite.
    """
    init_db()

    with get_session() as session:
        records = list_open_reorder_requests(session, limit=limit)
        return [serialize_reorder_request_record(record) for record in records]


def save_action_result(result: ActionResult) -> None:
    """
    Persist an action result and related side effects.
    """
    init_db()

    with get_session() as session:
        save_action_and_side_effects(session, result)


def execute_reorder_action(
    part_id: str,
    quantity: int,
    user: str,
) -> ActionResult:
    """
    Execute and persist a reorder action.
    """
    graph, _ = build_current_graph_and_alerts()
    result = create_reorder_request(
        graph=graph,
        part_id=part_id,
        quantity=quantity,
        user=user,
    )
    save_action_result(result)
    return result


def execute_expedite_action(
    shipment_id: str,
    user: str,
) -> ActionResult:
    """
    Execute and persist an expedite shipment action.
    """
    graph, _ = build_current_graph_and_alerts()
    result = expedite_shipment(
        graph=graph,
        shipment_id=shipment_id,
        user=user,
    )
    save_action_result(result)
    return result


def execute_mark_supplier_watchlist_action(
    supplier_id: str,
    user: str,
    reason: str,
) -> ActionResult:
    """
    Execute and persist a mark-supplier-watchlist action.
    """
    graph, _ = build_current_graph_and_alerts()
    result = mark_supplier_watchlist(
        graph=graph,
        supplier_id=supplier_id,
        user=user,
        reason=reason,
    )
    save_action_result(result)
    return result


def execute_acknowledge_alert_action(
    alert_id: str,
    user: str,
    note: str,
) -> ActionResult:
    """
    Acknowledge a persisted alert.
    """
    init_db()

    with get_session() as session:
        return acknowledge_alert(
            session=session,
            alert_id=alert_id,
            user=user,
            note=note,
        )


def execute_resolve_alert_action(
    alert_id: str,
    user: str,
    resolution_note: str,
) -> ActionResult:
    """
    Resolve a persisted alert.
    """
    init_db()

    with get_session() as session:
        return resolve_alert_record(
            session=session,
            alert_id=alert_id,
            user=user,
            note=resolution_note,
        )


def execute_dismiss_alert_action(
    alert_id: str,
    user: str,
    note: str,
) -> ActionResult:
    """
    Dismiss a persisted alert.
    """
    init_db()

    with get_session() as session:
        return dismiss_alert(
            session=session,
            alert_id=alert_id,
            user=user,
            note=note,
        )


def serialize_action_result(result: ActionResult) -> dict:
    """
    Convert an in-memory ActionResult into an API response dictionary.

    id is set to 0 because the inserted SQLAlchemy id is generated after insert.
    """
    return {
        "id": 0,
        "action_type": result.action_type.value,
        "status": result.status.value,
        "message": result.message,
        "user": result.user,
        "related_object_type": result.related_object_type,
        "related_object_id": result.related_object_id,
        "timestamp": result.timestamp,
        "metadata": result.metadata,
    }