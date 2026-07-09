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


def main() -> None:
    """
    Run transforms, build ontology objects, build relationships,
    and generate risk alerts.
    """
    cleaned_data = run_all_transforms()
    ontology = build_ontology(cleaned_data)
    graph = build_supply_chain_graph(ontology)
    alerts = generate_risk_alerts(graph)

    print()
    print("Risk scoring completed successfully.")

    print_section("Prioritized Risk Alerts")
    print_alerts(alerts)


if __name__ == "__main__":
    main()