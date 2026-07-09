from ontology.objects import CriticalityLevel, ShipmentStatus, SupplierStatus
from ontology.relationships import SupplyChainGraph


def find_parts_from_watchlisted_suppliers(
    graph: SupplyChainGraph,
) -> list[dict]:
    """
    Find parts supplied by suppliers on the watchlist.
    """
    results = []

    for supplier in graph.suppliers_by_id.values():
        if supplier.status != SupplierStatus.WATCHLIST:
            continue

        parts = graph.get_parts_for_supplier(supplier)

        for part in parts:
            results.append(
                {
                    "supplier_id": supplier.supplier_id,
                    "supplier_name": supplier.supplier_name,
                    "supplier_status": supplier.status.value,
                    "part_id": part.part_id,
                    "part_name": part.part_name,
                    "criticality": part.criticality.value,
                }
            )

    return results


def find_delayed_shipments_with_part_details(
    graph: SupplyChainGraph,
) -> list[dict]:
    """
    Find delayed shipments and enrich them with supplier and part details.
    """
    results = []

    for shipment in graph.shipments_by_id.values():
        if shipment.status != ShipmentStatus.DELAYED:
            continue

        supplier = graph.get_supplier_for_shipment(shipment)
        part = graph.get_part_for_shipment(shipment)

        results.append(
            {
                "shipment_id": shipment.shipment_id,
                "status": shipment.status.value,
                "quantity": shipment.quantity,
                "expected_delivery_date": shipment.expected_delivery_date,
                "supplier_id": supplier.supplier_id if supplier else None,
                "supplier_name": supplier.supplier_name if supplier else None,
                "part_id": part.part_id if part else None,
                "part_name": part.part_name if part else None,
                "criticality": part.criticality.value if part else None,
            }
        )

    return results


def find_low_stock_inventory(
    graph: SupplyChainGraph,
) -> list[dict]:
    """
    Find inventory items where current stock is below the reorder threshold.
    """
    results = []

    for inventory_item in graph.inventory_by_part_id.values():
        if inventory_item.current_stock >= inventory_item.reorder_threshold:
            continue

        part = graph.parts_by_id.get(inventory_item.part_id)
        supplier = graph.get_supplier_for_part(part) if part else None

        results.append(
            {
                "inventory_id": inventory_item.inventory_id,
                "part_id": inventory_item.part_id,
                "part_name": part.part_name if part else None,
                "current_stock": inventory_item.current_stock,
                "reorder_threshold": inventory_item.reorder_threshold,
                "warehouse_location": inventory_item.warehouse_location,
                "supplier_id": supplier.supplier_id if supplier else None,
                "supplier_name": supplier.supplier_name if supplier else None,
            }
        )

    return results


def find_high_criticality_low_stock_parts(
    graph: SupplyChainGraph,
) -> list[dict]:
    """
    Find high-criticality parts that are currently below reorder threshold.
    """
    results = []

    for part in graph.parts_by_id.values():
        if part.criticality != CriticalityLevel.HIGH:
            continue

        inventory_item = graph.get_inventory_for_part(part)

        if inventory_item is None:
            continue

        if inventory_item.current_stock >= inventory_item.reorder_threshold:
            continue

        supplier = graph.get_supplier_for_part(part)

        results.append(
            {
                "part_id": part.part_id,
                "part_name": part.part_name,
                "criticality": part.criticality.value,
                "current_stock": inventory_item.current_stock,
                "reorder_threshold": inventory_item.reorder_threshold,
                "warehouse_location": inventory_item.warehouse_location,
                "supplier_id": supplier.supplier_id if supplier else None,
                "supplier_name": supplier.supplier_name if supplier else None,
            }
        )

    return results


def find_delayed_high_criticality_shipments(
    graph: SupplyChainGraph,
) -> list[dict]:
    """
    Find delayed shipments involving high-criticality parts.
    """
    results = []

    for shipment in graph.shipments_by_id.values():
        if shipment.status != ShipmentStatus.DELAYED:
            continue

        part = graph.get_part_for_shipment(shipment)

        if part is None:
            continue

        if part.criticality != CriticalityLevel.HIGH:
            continue

        supplier = graph.get_supplier_for_shipment(shipment)

        results.append(
            {
                "shipment_id": shipment.shipment_id,
                "quantity": shipment.quantity,
                "expected_delivery_date": shipment.expected_delivery_date,
                "part_id": part.part_id,
                "part_name": part.part_name,
                "criticality": part.criticality.value,
                "supplier_id": supplier.supplier_id if supplier else None,
                "supplier_name": supplier.supplier_name if supplier else None,
            }
        )

    return results