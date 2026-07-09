from ontology.build_ontology import build_ontology
from ontology.queries import (
    find_delayed_high_criticality_shipments,
    find_delayed_shipments_with_part_details,
    find_high_criticality_low_stock_parts,
    find_low_stock_inventory,
    find_parts_from_watchlisted_suppliers,
)
from ontology.relationships import build_supply_chain_graph
from transforms.run_transforms import run_all_transforms


def print_section(title: str) -> None:
    """
    Print a formatted section title.
    """
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_results(results: list[dict]) -> None:
    """
    Print query results.
    """
    if not results:
        print("No results found.")
        return

    for index, result in enumerate(results, start=1):
        print(f"{index}. {result}")


def main() -> None:
    """
    Run transforms, build ontology objects, build relationships,
    and run relationship-based business queries.
    """
    cleaned_data = run_all_transforms()
    ontology = build_ontology(cleaned_data)
    graph = build_supply_chain_graph(ontology)

    print()
    print("Supply chain relationship graph built successfully.")

    print_section("Parts From Watchlisted Suppliers")
    print_results(find_parts_from_watchlisted_suppliers(graph))

    print_section("Delayed Shipments With Supplier and Part Details")
    print_results(find_delayed_shipments_with_part_details(graph))

    print_section("Low Stock Inventory")
    print_results(find_low_stock_inventory(graph))

    print_section("High-Criticality Low-Stock Parts")
    print_results(find_high_criticality_low_stock_parts(graph))

    print_section("Delayed High-Criticality Shipments")
    print_results(find_delayed_high_criticality_shipments(graph))


if __name__ == "__main__":
    main()