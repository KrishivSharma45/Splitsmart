import json
from decimal import Decimal
from typing import Any


def _default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return format(obj, "f")
    raise TypeError(f"Object of type {type(obj).__name__} is not canonical-JSON serializable")


def canonical_json(data: dict) -> str:
    """Deterministic JSON encoding: sorted keys, no extraneous whitespace.

    Used as the input to hash computations so the same logical event always
    produces the same byte string regardless of dict insertion order.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=_default)
