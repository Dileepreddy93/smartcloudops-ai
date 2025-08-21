from flask import Blueprint, Request, Response, request

from app.main import get_chat_response
from app.utils.response import make_response
from app.utils.validation import require_json_keys, sanitize_string


bp = Blueprint("chatops", __name__)


@bp.post("/query")
def query():
    json = request.get_json(silent=True) or {}
    ok, err = require_json_keys(json, ["query"])
    if not ok:
        # Preserve legacy error body expected by tests
        from flask import Response
        return Response("Invalid request", status=400)

    user_query = sanitize_string(json.get("query"))
    try:
        answer = get_chat_response(user_query)
    except Exception as e:
        return make_response(error="Failed to process query", http_status=400)

    # Preserve legacy shape: top-level 'response'
    from flask import jsonify
    return jsonify({"response": answer})


