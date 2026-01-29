from flask import request, jsonify, make_response

def get_json():
    """Returns the JSON payload from the request or an empty dict if it fails."""
    try:
        return request.get_json() or {}
    except Exception:
        return {}

def success(data, code=200):
    """Returns a success JSON response."""
    return make_response(jsonify({
        "status": "success",
        "data": data
    }), code)

def bad_request(message, code=400):
    """Returns an error JSON response."""
    return make_response(jsonify({
        "status": "error",
        "message": message
    }), code)
