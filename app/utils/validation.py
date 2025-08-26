from __future__ import annotations

from typing import Any, Dict, List, Tuple


def require_json_keys(obj: Dict[str, Any], keys: List[str]) -> Tuple[bool, str | None]:
    if not isinstance(obj, dict):
        return False, "Invalid JSON payload"
    missing = [k for k in keys if k not in obj]
    if missing:
        return False, f"Missing keys: {', '.join(missing)}"
    return True, None


def sanitize_string(s: Any, max_len: int = 2048) -> str:
    try:
        value = str(s).strip()
    except Exception:
        value = ""
    return value[:max_len]
