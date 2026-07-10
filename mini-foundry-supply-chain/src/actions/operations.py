from ontology.objects import RiskAlert, ShipmentStatus, SupplierStatus
from ontology.relationships import SupplyChainGraph

from actions.action_models import ActionResult, ActionStatus, ActionType
from actions.audit_log import write_audit_log


def create_reorder_request(
    graph: SupplyChainGraph,
    part_id: str,
    quantity: int,
    user: str,
) -> ActionResult:
    """
    Create a reorder request for a part.

    For now, this does not write to a real orders database.
    It creates an auditable action result.
    """
    part = graph.parts_by_id.get(part_id)

    if part is None:
        result = ActionResult(
            action_type=ActionType.CREATE_REORDER_REQUEST,
            status=ActionStatus.FAILED,
            message=f"Could not create reorder request. Part {part_id} was not found.",
            user=user,
            related_object_type="Part",
            related_object_id=part_id,
            metadata={"requested_quantity": quantity},
        )
        write_audit_log(result)
        return result

    if quantity <= 0:
        result = ActionResult(
            action_type=ActionType.CREATE_REORDER_REQUEST,
            status=ActionStatus.FAILED,
            message="Could not create reorder request. Quantity must be greater than zero.",
            user=user,
            related_object_type="Part",
            related_object_id=part_id,
            metadata={"requested_quantity": quantity},
        )
        write_audit_log(result)
        return result

    supplier = graph.get_supplier_for_part(part)

    result = ActionResult(
        action_type=ActionType.CREATE_REORDER_REQUEST,
        status=ActionStatus.SUCCESS,
        message=(
            f"Created reorder request for {quantity} units of {part.part_name}."
        ),
        user=user,
        related_object_type="Part",
        related_object_id=part.part_id,
        metadata={
            "part_name": part.part_name,
            "supplier_id": supplier.supplier_id if supplier else None,
            "supplier_name": supplier.supplier_name if supplier else None,
            "requested_quantity": quantity,
        },
    )

    write_audit_log(result)
    return result


def expedite_shipment(
    graph: SupplyChainGraph,
    shipment_id: str,
    user: str,
) -> ActionResult:
    """
    Mark a shipment as expedited.

    Since ShipmentStatus does not currently include EXPEDITED, we keep the
    original shipment status and record the expedited state in metadata.
    """
    shipment = graph.shipments_by_id.get(shipment_id)

    if shipment is None:
        result = ActionResult(
            action_type=ActionType.EXPEDITE_SHIPMENT,
            status=ActionStatus.FAILED,
            message=f"Could not expedite shipment. Shipment {shipment_id} was not found.",
            user=user,
            related_object_type="Shipment",
            related_object_id=shipment_id,
        )
        write_audit_log(result)
        return result

    part = graph.get_part_for_shipment(shipment)
    supplier = graph.get_supplier_for_shipment(shipment)

    result = ActionResult(
        action_type=ActionType.EXPEDITE_SHIPMENT,
        status=ActionStatus.SUCCESS,
        message=f"Shipment {shipment.shipment_id} was marked for expedition.",
        user=user,
        related_object_type="Shipment",
        related_object_id=shipment.shipment_id,
        metadata={
            "current_status": shipment.status.value,
            "part_id": part.part_id if part else None,
            "part_name": part.part_name if part else None,
            "supplier_id": supplier.supplier_id if supplier else None,
            "supplier_name": supplier.supplier_name if supplier else None,
        },
    )

    write_audit_log(result)
    return result


def mark_supplier_watchlist(
    graph: SupplyChainGraph,
    supplier_id: str,
    user: str,
    reason: str,
) -> ActionResult:
    """
    Mark a supplier as WATCHLIST in memory.

    Because Pydantic models are mutable by default, this updates the Supplier
    object currently stored in the graph.
    """
    supplier = graph.suppliers_by_id.get(supplier_id)

    if supplier is None:
        result = ActionResult(
            action_type=ActionType.MARK_SUPPLIER_WATCHLIST,
            status=ActionStatus.FAILED,
            message=f"Could not update supplier. Supplier {supplier_id} was not found.",
            user=user,
            related_object_type="Supplier",
            related_object_id=supplier_id,
            metadata={"reason": reason},
        )
        write_audit_log(result)
        return result

    old_status = supplier.status
    supplier.status = SupplierStatus.WATCHLIST

    result = ActionResult(
        action_type=ActionType.MARK_SUPPLIER_WATCHLIST,
        status=ActionStatus.SUCCESS,
        message=f"Supplier {supplier.supplier_name} was marked as WATCHLIST.",
        user=user,
        related_object_type="Supplier",
        related_object_id=supplier.supplier_id,
        metadata={
            "supplier_name": supplier.supplier_name,
            "old_status": old_status.value,
            "new_status": supplier.status.value,
            "reason": reason,
        },
    )

    write_audit_log(result)
    return result


def resolve_alert(
    alert: RiskAlert,
    user: str,
    resolution_note: str,
) -> ActionResult:
    """
    Resolve a risk alert.

    For now, RiskAlert does not have lifecycle state, so this action records
    a resolution event in the audit log.
    """
    result = ActionResult(
        action_type=ActionType.RESOLVE_ALERT,
        status=ActionStatus.SUCCESS,
        message=f"Resolved alert {alert.alert_id}.",
        user=user,
        related_object_type="RiskAlert",
        related_object_id=alert.alert_id,
        metadata={
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "resolution_note": resolution_note,
            "original_message": alert.message,
        },
    )

    write_audit_log(result)
    return result


def create_action_for_alert(
    graph: SupplyChainGraph,
    alert: RiskAlert,
    user: str,
) -> ActionResult:
    """
    Choose a reasonable default action based on the alert's recommended action.

    This gives us a simple automation-style helper for Stage 6.
    """
    if alert.related_object_type == "Part":
        return create_reorder_request(
            graph=graph,
            part_id=alert.related_object_id,
            quantity=100,
            user=user,
        )

    if alert.related_object_type == "InventoryItem":
        inventory_item = None

        for item in graph.inventory_by_part_id.values():
            if item.inventory_id == alert.related_object_id:
                inventory_item = item
                break

        if inventory_item is None:
            result = ActionResult(
                action_type=ActionType.CREATE_REORDER_REQUEST,
                status=ActionStatus.FAILED,
                message=(
                    "Could not create action for alert. "
                    f"Inventory item {alert.related_object_id} was not found."
                ),
                user=user,
                related_object_type="InventoryItem",
                related_object_id=alert.related_object_id,
            )
            write_audit_log(result)
            return result

        reorder_quantity = max(
            inventory_item.reorder_threshold - inventory_item.current_stock,
            1,
        )

        return create_reorder_request(
            graph=graph,
            part_id=inventory_item.part_id,
            quantity=reorder_quantity,
            user=user,
        )

    if alert.related_object_type == "Shipment":
        return expedite_shipment(
            graph=graph,
            shipment_id=alert.related_object_id,
            user=user,
        )

    result = ActionResult(
        action_type=ActionType.RESOLVE_ALERT,
        status=ActionStatus.FAILED,
        message=(
            "Could not infer an action for alert related object type "
            f"{alert.related_object_type}."
        ),
        user=user,
        related_object_type=alert.related_object_type,
        related_object_id=alert.related_object_id,
    )

    write_audit_log(result)
    return result