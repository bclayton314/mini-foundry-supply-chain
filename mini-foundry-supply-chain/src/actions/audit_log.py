import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from actions.action_models import ActionResult


AUDIT_LOG_PATH = Path("data/audit/action_log.jsonl")


def _to_json_safe(value: Any) -> Any:
    """
    Convert Pydantic objects and datetime-like values into JSON-safe values.
    """
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    if isinstance(value, dict):
        return {key: _to_json_safe(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_to_json_safe(item) for item in value]

    return value


def write_audit_log(action_result: ActionResult) -> None:
    """
    Append an action result to the audit log as one JSON line.
    """
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = _to_json_safe(action_result)

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def read_audit_log() -> list[dict]:
    """
    Read the full audit log.

    Returns an empty list if the log file does not exist yet.
    """
    if not AUDIT_LOG_PATH.exists():
        return []

    records = []

    with AUDIT_LOG_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            records.append(json.loads(line))

    return records