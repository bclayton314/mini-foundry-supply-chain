from fastapi import FastAPI, HTTPException, Query

from api.schemas import (
    AcknowledgeAlertRequest,
    ActionResultResponse,
    DismissAlertRequest,
    ExpediteShipmentRequest,
    HealthResponse,
    MarkSupplierWatchlistRequest,
    PipelineRunResponse,
    ReorderRequestCreate,
    ReorderRequestResponse,
    ResolveAlertRequest,
    RiskAlertResponse,
)
from api.service import (
    VALID_ALERT_STATUSES,
    execute_acknowledge_alert_action,
    execute_dismiss_alert_action,
    execute_expedite_action,
    execute_mark_supplier_watchlist_action,
    execute_reorder_action,
    execute_resolve_alert_action,
    get_action_records,
    get_alert_records,
    get_open_reorder_requests,
    run_pipeline_and_save_alerts,
    serialize_action_result,
)
from persistence.db import init_db


app = FastAPI(
    title="Mini Foundry Supply Chain API",
    description=(
        "A Foundry-inspired operational ontology API for supply chain risk, "
        "actions, alert lifecycle state, and auditability."
    ),
    version="0.2.0",
)


@app.on_event("startup")
def startup() -> None:
    """
    Initialize database tables when the API starts.
    """
    init_db()


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="mini-foundry-supply-chain",
    )


@app.post("/pipeline/run", response_model=PipelineRunResponse)
def run_pipeline() -> PipelineRunResponse:
    alerts_generated, alerts_saved = run_pipeline_and_save_alerts()

    return PipelineRunResponse(
        message="Pipeline completed successfully.",
        alerts_generated=alerts_generated,
        alerts_saved=alerts_saved,
    )


@app.get("/alerts", response_model=list[RiskAlertResponse])
def list_alerts(
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(
        default=None,
        description="Optional lifecycle status: OPEN, ACKNOWLEDGED, RESOLVED, or DISMISSED.",
    ),
) -> list[dict]:
    if status is not None and status.upper() not in VALID_ALERT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid alert status. Expected one of: "
                "OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED."
            ),
        )

    return get_alert_records(
        limit=limit,
        status=status,
    )


@app.get("/actions", response_model=list[ActionResultResponse])
def list_actions(
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return get_action_records(limit=limit)


@app.get("/reorder-requests", response_model=list[ReorderRequestResponse])
def list_reorder_requests(
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    return get_open_reorder_requests(limit=limit)


@app.post("/actions/reorder", response_model=ActionResultResponse)
def create_reorder(
    request: ReorderRequestCreate,
) -> dict:
    result = execute_reorder_action(
        part_id=request.part_id,
        quantity=request.quantity,
        user=request.user,
    )
    return serialize_action_result(result)


@app.post("/actions/expedite-shipment", response_model=ActionResultResponse)
def expedite_shipment_endpoint(
    request: ExpediteShipmentRequest,
) -> dict:
    result = execute_expedite_action(
        shipment_id=request.shipment_id,
        user=request.user,
    )
    return serialize_action_result(result)


@app.post("/actions/mark-supplier-watchlist", response_model=ActionResultResponse)
def mark_supplier_watchlist_endpoint(
    request: MarkSupplierWatchlistRequest,
) -> dict:
    result = execute_mark_supplier_watchlist_action(
        supplier_id=request.supplier_id,
        user=request.user,
        reason=request.reason,
    )
    return serialize_action_result(result)


@app.post("/alerts/{alert_id}/acknowledge", response_model=ActionResultResponse)
def acknowledge_alert_endpoint(
    alert_id: str,
    request: AcknowledgeAlertRequest,
) -> dict:
    result = execute_acknowledge_alert_action(
        alert_id=alert_id,
        user=request.user,
        note=request.note,
    )

    if result.status.value == "FAILED" and "not found" in result.message.lower():
        raise HTTPException(status_code=404, detail=result.message)

    return serialize_action_result(result)


@app.post("/alerts/{alert_id}/resolve", response_model=ActionResultResponse)
def resolve_alert_endpoint(
    alert_id: str,
    request: ResolveAlertRequest,
) -> dict:
    result = execute_resolve_alert_action(
        alert_id=alert_id,
        user=request.user,
        resolution_note=request.resolution_note,
    )

    if result.status.value == "FAILED" and "not found" in result.message.lower():
        raise HTTPException(status_code=404, detail=result.message)

    return serialize_action_result(result)


@app.post("/alerts/{alert_id}/dismiss", response_model=ActionResultResponse)
def dismiss_alert_endpoint(
    alert_id: str,
    request: DismissAlertRequest,
) -> dict:
    result = execute_dismiss_alert_action(
        alert_id=alert_id,
        user=request.user,
        note=request.note,
    )

    if result.status.value == "FAILED" and "not found" in result.message.lower():
        raise HTTPException(status_code=404, detail=result.message)

    return serialize_action_result(result)