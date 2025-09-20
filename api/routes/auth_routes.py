import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from api.services.user_service import UserService

auth_bp = Blueprint("auth", __name__)
user_service = UserService()


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400
    try:
        uid = user_service.create_user(
            email=email, password=password, first_name=first_name, last_name=last_name
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    access = create_access_token(identity=uid)
    refresh = create_refresh_token(identity=uid)
    return jsonify(
        {
            "success": True,
            "data": {"userId": uid, "accessToken": access, "refreshToken": refresh},
        }
    ), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"success": False, "error": "Email and password required"}), 400

    user = user_service.get_by_email(email)
    if not user:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    if not user_service.verify_password(password, user["password"]):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    uid = str(user["_id"])
    access = create_access_token(identity=uid)
    refresh = create_refresh_token(identity=uid)
    return jsonify(
        {
            "success": True,
            "data": {
                # "userId": uid,
                # "email": user["email"],
                # "first_name": user.get("first_name"),
                # "last_name": user.get("last_name"),
                "accessToken": access,
                "refreshToken": refresh,
            },
        }
    ), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    uid = get_jwt_identity()  # this is the user id you stored in the token
    user = user_service.get_by_id(uid)

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    return jsonify(
        {
            "success": True,
            "data": {
                "userId": str(user["_id"]),
                "email": user["email"],
                "firstName": user.get("first_name"),
                "lastName": user.get("last_name"),
            },
        }
    ), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)
    return jsonify({"success": True, "data": {"accessToken": access}}), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    # This endpoint will revoke whatever token is presented (access or refresh)
    claims = get_jwt()
    jti = claims.get("jti")
    token_type = claims.get("type") or claims.get("token_type") or "access"
    expires = claims.get("exp")
    user_service.revoke_token(jti=jti, token_type=token_type, expires_at_ts=expires)
    return jsonify({"success": True, "message": "Token revoked"}), 200
