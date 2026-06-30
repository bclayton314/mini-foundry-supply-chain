from ontology.build_ontology import build_ontology
from transforms.run_transforms import run_all_transforms


def print_object_summary(object_name: str, objects: list) -> None:
    """
    Print a simple summary of ontology objects.
    """
    print("=" * 60)
    print(f"Ontology Object Type: {object_name}")
    print(f"Count: {len(objects)}")
    print()

    for obj in objects[:3]:
        print(obj)
    print()


def main() -> None:
    """
    Run transforms, build ontology objects, and print summaries.
    """
    cleaned_data = run_all_transforms()
    ontology = build_ontology(cleaned_data)

    print()
    print("Ontology build completed successfully.")
    print()

    for object_name, objects in ontology.items():
        print_object_summary(object_name, objects)


if __name__ == "__main__":
    main()