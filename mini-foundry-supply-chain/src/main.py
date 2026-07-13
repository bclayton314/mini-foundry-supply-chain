from actions.operations import (
    create_action_for_alert,
    create_reorder_request,
    expedite_shipment,
    mark_supplier_watchlist,
    resolve_alert,
)
from ontology.build_ontology import build_ontology
from ontology.relationships import build_supply_chain_graph
from persistence.db import get_session, init_db
from persistence.repositories import (
    count_records,
    list_open_reorder_requests,
    list_recent_actions,
    list_recent_alerts,
    save_action_and_side_effects,
    save_risk_alerts,
)
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


def print_database_summary(session) -> None:
    """
    Print counts from persistence tables.
    """
    counts = count_records(session)

    print("Database record counts:")
    for table_name, count in counts.items():
        print(f"- {table_name}: {count}")


def print_recent_alert_records(session) -> None:
    """
    Print recent alert records stored in SQLite.
    """
    records = list_recent_alerts(session, limit=5)

    if not records:
        print("No alert records found.")
        return

    for record in records:
        print(
            {
                "alert_id": record.alert_id,
                "alert_type": record.alert_type,
                "severity": record.severity,
                "related_object": (
                    f"{record.related_object_type} {record.related_object_id}"
                ),
            }
        )


def print_recent_action_records(session) -> None:
    """
    Print recent action records stored in SQLite.
    """
    records = list_recent_actions(session, limit=5)

    if not records:
        print("No action records found.")
        return

    for record in records:
        print(
            {
                "id": record.id,
                "action_type": record.action_type,
                "status": record.status,
                "user": record.user,
                "related_object": (
                    f"{record.related_object_type} {record.related_object_id}"
                ),
            }
        )


def print_open_reorder_requests(session) -> None:
    """
    Print open reorder requests stored in SQLite.
    """
    records = list_open_reorder_requests(session, limit=5)

    if not records:
        print("No open reorder requests found.")
        return

    for record in records:
        print(
            {
                "id": record.id,
                "part_id": record.part_id,
                "part_name": record.part_name,
                "supplier_name": record.supplier_name,
                "requested_quantity": record.requested_quantity,
                "requested_by": record.requested_by,
                "status": record.status,
            }
        )


def main() -> None:
    """
    Run the full mini Foundry pipeline and persist results to SQLite.
    """
    init_db()

    cleaned_data = run_all_transforms()
    ontology = build_ontology(cleaned_data)
    graph = build_supply_chain_graph(ontology)
    alerts = generate_risk_alerts(graph)

    with get_session() as session:
        save_risk_alerts(session, alerts)

        print()
        print("SQLite persistence demo started successfully.")

        print_section("Prioritized Risk Alerts")
        print_alerts(alerts)

        print_section("Manual Action: Create Reorder Request")
        reorder_result = create_reorder_request(
            graph=graph,
            part_id="PART-004",
            quantity=200,
            user="clayton",
        )
        save_action_and_side_effects(session, reorder_result)
        print_action_result(reorder_result)

        print_section("Manual Action: Expedite Delayed Shipment")
        expedite_result = expedite_shipment(
            graph=graph,
            shipment_id="SHIP-003",
            user="clayton",
        )
        save_action_and_side_effects(session, expedite_result)
        print_action_result(expedite_result)

        print_section("Manual Action: Mark Supplier Watchlist")
        supplier_result = mark_supplier_watchlist(
            graph=graph,
            supplier_id="SUP-003",
            user="clayton",
            reason="Reliability score review after repeated delays.",
        )
        save_action_and_side_effects(session, supplier_result)
        print_action_result(supplier_result)

        print_section("Automated Action From Highest-Priority Alert")
        if alerts:
            auto_action_result = create_action_for_alert(
                graph=graph,
                alert=alerts[0],
                user="clayton",
            )
            save_action_and_side_effects(session, auto_action_result)
            print_action_result(auto_action_result)

        print_section("Resolve First Alert")
        if alerts:
            resolve_result = resolve_alert(
                alert=alerts[0],
                user="clayton",
                resolution_note=(
                    "Initial mitigation action was created and assigned "
                    "for follow-up."
                ),
            )
            save_action_and_side_effects(session, resolve_result)
            print_action_result(resolve_result)

        print_section("Database Summary")
        print_database_summary(session)

        print_section("Recent Alert Records")
        print_recent_alert_records(session)

        print_section("Recent Action Records")
        print_recent_action_records(session)

        print_section("Open Reorder Requests")
        print_open_reorder_requests(session)


if __name__ == "__main__":
    main()