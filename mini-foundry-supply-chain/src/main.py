from actions.audit_log import read_audit_log
from actions.operations import (
    create_action_for_alert,
    create_reorder_request,
    expedite_shipment,
    mark_supplier_watchlist,
    resolve_alert,
)
from ontology.build_ontology import build_ontology
from ontology.relationships import build_supply_chain_graph
from risk.scoring import generate_risk_alerts
from transforms.run_transforms import run_all_transforms


def print_section(title: str) -> None:
    """
    Print a formatted section title.
    """
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def print_alerts(alerts: list) -> None:
    """
    Print risk alerts in priority order.
    """
    if not alerts:
        print("No risk alerts found.")
        return

    for index, alert in enumerate(alerts, start=1):
        print(f"{index}. [{alert.severity.value}] {alert.alert_type.value}")
        print(f"   Alert ID: {alert.alert_id}")
        print(f"   Message: {alert.message}")
        print(f"   Related Object: {alert.related_object_type} {alert.related_object_id}")
        print(f"   Recommended Action: {alert.recommended_action}")
        print()


def print_action_result(result) -> None:
    """
    Print one action result.
    """
    print(f"[{result.status.value}] {result.action_type.value}")
    print(f"Message: {result.message}")
    print(f"User: {result.user}")
    print(f"Related Object: {result.related_object_type} {result.related_object_id}")
    print(f"Timestamp: {result.timestamp}")
    print(f"Metadata: {result.metadata}")
    print()


def print_audit_log_summary() -> None:
    """
    Print a small summary of the audit log.
    """
    records = read_audit_log()

    print(f"Audit records found: {len(records)}")

    for record in records[-5:]:
        print(record)


def main() -> None:
    """
    Run transforms, build ontology objects, build relationships,
    generate risk alerts, and execute operational actions.
    """
    cleaned_data = run_all_transforms()
    ontology = build_ontology(cleaned_data)
    graph = build_supply_chain_graph(ontology)
    alerts = generate_risk_alerts(graph)

    print()
    print("Operational action demo started successfully.")

    print_section("Prioritized Risk Alerts")
    print_alerts(alerts)

    print_section("Manual Action: Create Reorder Request")
    reorder_result = create_reorder_request(
        graph=graph,
        part_id="PART-004",
        quantity=200,
        user="clayton",
    )
    print_action_result(reorder_result)

    print_section("Manual Action: Expedite Delayed Shipment")
    expedite_result = expedite_shipment(
        graph=graph,
        shipment_id="SHIP-003",
        user="clayton",
    )
    print_action_result(expedite_result)

    print_section("Manual Action: Mark Supplier Watchlist")
    supplier_result = mark_supplier_watchlist(
        graph=graph,
        supplier_id="SUP-003",
        user="clayton",
        reason="Reliability score review after repeated delays.",
    )
    print_action_result(supplier_result)

    print_section("Automated Action From Highest-Priority Alert")
    if alerts:
        auto_action_result = create_action_for_alert(
            graph=graph,
            alert=alerts[0],
            user="clayton",
        )
        print_action_result(auto_action_result)

    print_section("Resolve First Alert")
    if alerts:
        resolve_result = resolve_alert(
            alert=alerts[0],
            user="clayton",
            resolution_note="Initial mitigation action was created and assigned for follow-up.",
        )
        print_action_result(resolve_result)

    print_section("Audit Log Summary")
    print_audit_log_summary()


if __name__ == "__main__":
    main()