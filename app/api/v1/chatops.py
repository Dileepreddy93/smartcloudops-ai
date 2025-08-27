from flask import Blueprint, request

from app.services.chatops_service import chat
from app.utils.response import error_response, success_response
from app.utils.validation import validate_user_input, sanitize_string


bp = Blueprint("chatops", __name__)


@bp.post("/query")
def query():
    json = request.get_json(silent=True) or {}
    try:
        validated_data = validate_user_input(json, ["query"])
        user_query = validated_data["query"]
    except ValueError:
        # Preserve legacy error body expected by tests
        from flask import Response
        return Response("Invalid request", status=400)

    user_query = sanitize_string(user_query)
    try:
        answer = chat(user_query)
    except Exception:
        return error_response(message="Failed to process query", status_code=400)

    # Preserve legacy shape: top-level 'response'
    from flask import jsonify

    return jsonify({"response": answer})
