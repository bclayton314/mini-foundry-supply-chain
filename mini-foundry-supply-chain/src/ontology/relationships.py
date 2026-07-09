from dataclasses import dataclass

from ontology.objects import InventoryItem, Part, Shipment, Supplier


@dataclass
class SupplyChainGraph:
    """
    Relationship layer for the supply chain ontology.

    This class acts like a small in-memory graph.

    It stores:
    - Suppliers by supplier_id
    - Parts by part_id
    - Shipments by shipment_id
    - Inventory items by part_id

    It also provides relationship lookups such as:
    - Get a supplier for a part
    - Get shipments for a part
    - Get inventory for a part
    """

    suppliers_by_id: dict[str, Supplier]
    parts_by_id: dict[str, Part]
    shipments_by_id: dict[str, Shipment]
    inventory_by_part_id: dict[str, InventoryItem]

    parts_by_supplier_id: dict[str, list[Part]]
    shipments_by_supplier_id: dict[str, list[Shipment]]
    shipments_by_part_id: dict[str, list[Shipment]]

    def get_supplier_for_part(self, part: Part) -> Supplier | None:
        """
        Return the Supplier connected to a Part.
        """
        return self.suppliers_by_id.get(part.supplier_id)

    def get_supplier_for_shipment(self, shipment: Shipment) -> Supplier | None:
        """
        Return the Supplier connected to a Shipment.
        """
        return self.suppliers_by_id.get(shipment.supplier_id)

    def get_part_for_shipment(self, shipment: Shipment) -> Part | None:
        """
        Return the Part connected to a Shipment.
        """
        return self.parts_by_id.get(shipment.part_id)

    def get_inventory_for_part(self, part: Part) -> InventoryItem | None:
        """
        Return the InventoryItem connected to a Part.
        """
        return self.inventory_by_part_id.get(part.part_id)

    def get_parts_for_supplier(self, supplier: Supplier) -> list[Part]:
        """
        Return all Parts supplied by a Supplier.
        """
        return self.parts_by_supplier_id.get(supplier.supplier_id, [])

    def get_shipments_for_supplier(self, supplier: Supplier) -> list[Shipment]:
        """
        Return all Shipments connected to a Supplier.
        """
        return self.shipments_by_supplier_id.get(supplier.supplier_id, [])

    def get_shipments_for_part(self, part: Part) -> list[Shipment]:
        """
        Return all Shipments connected to a Part.
        """
        return self.shipments_by_part_id.get(part.part_id, [])


def build_supply_chain_graph(ontology: dict[str, list]) -> SupplyChainGraph:
    """
    Build relationship indexes from ontology objects.

    These indexes let us quickly traverse relationships between objects.
    """
    suppliers: list[Supplier] = ontology["suppliers"]
    parts: list[Part] = ontology["parts"]
    shipments: list[Shipment] = ontology["shipments"]
    inventory_items: list[InventoryItem] = ontology["inventory_items"]

    suppliers_by_id = {supplier.supplier_id: supplier for supplier in suppliers}
    parts_by_id = {part.part_id: part for part in parts}
    shipments_by_id = {
        shipment.shipment_id: shipment
        for shipment in shipments
    }

    inventory_by_part_id = {
        item.part_id: item
        for item in inventory_items
    }

    parts_by_supplier_id: dict[str, list[Part]] = {}
    for part in parts:
        parts_by_supplier_id.setdefault(part.supplier_id, []).append(part)

    shipments_by_supplier_id: dict[str, list[Shipment]] = {}
    for shipment in shipments:
        shipments_by_supplier_id.setdefault(
            shipment.supplier_id,
            [],
        ).append(shipment)

    shipments_by_part_id: dict[str, list[Shipment]] = {}
    for shipment in shipments:
        shipments_by_part_id.setdefault(
            shipment.part_id,
            [],
        ).append(shipment)

    return SupplyChainGraph(
        suppliers_by_id=suppliers_by_id,
        parts_by_id=parts_by_id,
        shipments_by_id=shipments_by_id,
        inventory_by_part_id=inventory_by_part_id,
        parts_by_supplier_id=parts_by_supplier_id,
        shipments_by_supplier_id=shipments_by_supplier_id,
        shipments_by_part_id=shipments_by_part_id,
    )