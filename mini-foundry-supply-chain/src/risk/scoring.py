from ontology.objects import (
    CriticalityLevel,
    RiskAlert,
    RiskAlertType,
    RiskSeverity,
    ShipmentStatus,
    SupplierStatus,
)
from ontology.relationships import SupplyChainGraph


def _make_alert_id(prefix: str, sequence_number: int) -> str:
    """
    Create a stable alert ID.

    Example:
    LOW-001
    DELAY-002
    """
    return f"{prefix}-{sequence_number:03d}"


def score_low_inventory(
    graph: SupplyChainGraph,
    starting_sequence: int = 1,
) -> list[RiskAlert]:
    """
    Generate alerts for inventory below reorder threshold.
    """
    alerts = []
    sequence = starting_sequence

    for inventory_item in graph.inventory_by_part_id.values():
        if inventory_item.current_stock >= inventory_item.reorder_threshold:
            continue

        part = graph.parts_by_id.get(inventory_item.part_id)

        severity = RiskSeverity.MEDIUM
        if part and part.criticality == CriticalityLevel.HIGH:
            severity = RiskSeverity.HIGH

        part_name = part.part_name if part else inventory_item.part_id

        alerts.append(
            RiskAlert(
                alert_id=_make_alert_id("LOWSTOCK", sequence),
                alert_type=RiskAlertType.LOW_INVENTORY,
                severity=severity,
                message=(
                    f"{part_name} is below reorder threshold at "
                    f"{inventory_item.warehouse_location}. "
                    f"Current stock: {inventory_item.current_stock}, "
                    f"threshold: {inventory_item.reorder_threshold}."
                ),
                related_object_type="InventoryItem",
                related_object_id=inventory_item.inventory_id,
                recommended_action="Review inventory and create a reorder request.",
            )
        )

        sequence += 1

    return alerts


def score_delayed_shipments(
    graph: SupplyChainGraph,
    starting_sequence: int = 1,
) -> list[RiskAlert]:
    """
    Generate alerts for delayed shipments.
    """
    alerts = []
    sequence = starting_sequence

    for shipment in graph.shipments_by_id.values():
        if shipment.status != ShipmentStatus.DELAYED:
            continue

        part = graph.get_part_for_shipment(shipment)
        supplier = graph.get_supplier_for_shipment(shipment)

        severity = RiskSeverity.MEDIUM

        if part and part.criticality == CriticalityLevel.HIGH:
            severity = RiskSeverity.HIGH

        if supplier and supplier.status == SupplierStatus.WATCHLIST:
            severity = RiskSeverity.HIGH

        part_name = part.part_name if part else shipment.part_id
        supplier_name = supplier.supplier_name if supplier else shipment.supplier_id

        alerts.append(
            RiskAlert(
                alert_id=_make_alert_id("DELAY", sequence),
                alert_type=RiskAlertType.DELAYED_SHIPMENT,
                severity=severity,
                message=(
                    f"Shipment {shipment.shipment_id} from {supplier_name} "
                    f"for {part_name} is delayed."
                ),
                related_object_type="Shipment",
                related_object_id=shipment.shipment_id,
                recommended_action="Contact supplier and evaluate whether the shipment should be expedited.",
            )
        )

        sequence += 1

    return alerts


def score_watchlisted_suppliers(
    graph: SupplyChainGraph,
    starting_sequence: int = 1,
) -> list[RiskAlert]:
    """
    Generate alerts for suppliers currently on the watchlist.
    """
    alerts = []
    sequence = starting_sequence

    for supplier in graph.suppliers_by_id.values():
        if supplier.status != SupplierStatus.WATCHLIST:
            continue

        parts = graph.get_parts_for_supplier(supplier)
        high_criticality_parts = [
            part for part in parts
            if part.criticality == CriticalityLevel.HIGH
        ]

        severity = RiskSeverity.MEDIUM
        if high_criticality_parts:
            severity = RiskSeverity.HIGH

        alerts.append(
            RiskAlert(
                alert_id=_make_alert_id("SUPPLIER", sequence),
                alert_type=RiskAlertType.WATCHLISTED_SUPPLIER,
                severity=severity,
                message=(
                    f"Supplier {supplier.supplier_name} is on the watchlist "
                    f"with reliability score {supplier.reliability_score}."
                ),
                related_object_type="Supplier",
                related_object_id=supplier.supplier_id,
                recommended_action="Review supplier performance and identify backup suppliers if needed.",
            )
        )

        sequence += 1

    return alerts


def score_critical_part_low_stock(
    graph: SupplyChainGraph,
    starting_sequence: int = 1,
) -> list[RiskAlert]:
    """
    Generate critical alerts for high-criticality parts below reorder threshold.
    """
    alerts = []
    sequence = starting_sequence

    for part in graph.parts_by_id.values():
        if part.criticality != CriticalityLevel.HIGH:
            continue

        inventory_item = graph.get_inventory_for_part(part)

        if inventory_item is None:
            continue

        if inventory_item.current_stock >= inventory_item.reorder_threshold:
            continue

        supplier = graph.get_supplier_for_part(part)
        supplier_name = supplier.supplier_name if supplier else part.supplier_id

        alerts.append(
            RiskAlert(
                alert_id=_make_alert_id("CRITSTOCK", sequence),
                alert_type=RiskAlertType.CRITICAL_PART_LOW_STOCK,
                severity=RiskSeverity.CRITICAL,
                message=(
                    f"High-criticality part {part.part_name} is below reorder "
                    f"threshold. Supplier: {supplier_name}. "
                    f"Current stock: {inventory_item.current_stock}, "
                    f"threshold: {inventory_item.reorder_threshold}."
                ),
                related_object_type="Part",
                related_object_id=part.part_id,
                recommended_action="Create urgent reorder request and evaluate alternate suppliers.",
            )
        )

        sequence += 1

    return alerts


def score_critical_part_delayed_shipments(
    graph: SupplyChainGraph,
    starting_sequence: int = 1,
) -> list[RiskAlert]:
    """
    Generate critical alerts for delayed shipments involving high-criticality parts.
    """
    alerts = []
    sequence = starting_sequence

    for shipment in graph.shipments_by_id.values():
        if shipment.status != ShipmentStatus.DELAYED:
            continue

        part = graph.get_part_for_shipment(shipment)

        if part is None:
            continue

        if part.criticality != CriticalityLevel.HIGH:
            continue

        supplier = graph.get_supplier_for_shipment(shipment)
        supplier_name = supplier.supplier_name if supplier else shipment.supplier_id

        alerts.append(
            RiskAlert(
                alert_id=_make_alert_id("CRITDELAY", sequence),
                alert_type=RiskAlertType.CRITICAL_PART_DELAYED_SHIPMENT,
                severity=RiskSeverity.CRITICAL,
                message=(
                    f"Delayed shipment {shipment.shipment_id} affects "
                    f"high-criticality part {part.part_name}. "
                    f"Supplier: {supplier_name}."
                ),
                related_object_type="Shipment",
                related_object_id=shipment.shipment_id,
                recommended_action="Escalate shipment delay and evaluate operational impact.",
            )
        )

        sequence += 1

    return alerts


def generate_risk_alerts(graph: SupplyChainGraph) -> list[RiskAlert]:
    """
    Run all risk scoring rules and return a prioritized list of alerts.
    """
    alerts = []

    alerts.extend(score_low_inventory(graph))
    alerts.extend(score_delayed_shipments(graph))
    alerts.extend(score_watchlisted_suppliers(graph))
    alerts.extend(score_critical_part_low_stock(graph))
    alerts.extend(score_critical_part_delayed_shipments(graph))

    severity_rank = {
        RiskSeverity.CRITICAL: 0,
        RiskSeverity.HIGH: 1,
        RiskSeverity.MEDIUM: 2,
        RiskSeverity.LOW: 3,
    }

    return sorted(
        alerts,
        key=lambda alert: severity_rank[alert.severity],
    )