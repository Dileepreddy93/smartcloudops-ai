from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import jsonify


def now_iso() -> str:
    """Return current UTC time in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat()


def make_response(
    data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    http_status: int = 200,
    compatibility: Optional[Dict[str, Any]] = None,
):
    """Create a unified JSON response with DTO and optional compatibility fields.

    The payload always includes keys: status, data, error.
    Additional top-level fields can be merged via `compatibility` to avoid breaking
    existing clients/tests during migration.
    """

    payload: Dict[str, Any] = {
        "status": "success" if error is None else "error",
        "data": data if error is None else None,
        "error": None if error is None else {"message": str(error)},
    }

    if compatibility:
        payload.update(compatibility)

    return jsonify(payload), http_status


