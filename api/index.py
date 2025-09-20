import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS  # <-- add this

from api.config import Config
from api.extensions import db, jwt
from api.routes.auth_routes import auth_bp
from api.routes.contract_routes import contract_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # convert expiry seconds to timedelta expected by flask-jwt-extended
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_EXPIRES_SECONDS", 3600))
    )
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_EXPIRES_SECONDS", 60 * 60 * 24 * 30))
    )

    # --- CORS setup ---
    allowed_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS", "*"
    )  # e.g. "http://localhost:5173,http://127.0.0.1:3000"
    origins_list = [origin.strip() for origin in allowed_origins.split(",")]
    CORS(app, resources={r"/*": {"origins": origins_list}}, supports_credentials=True)

    # init extensions
    jwt.init_app(app)

    # blocklist loader uses mongo collection token_blacklist
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload.get("jti")
        if not jti:
            return True
        entry = db["token_blacklist"].find_one({"jti": jti})
        return bool(entry)

    # register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(contract_bp, url_prefix="/contracts")

    @app.route("/")
    def index():
        return "Legal Buddy is working"

    # consistent JSON error handler
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Not Found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal Server Error"}), 500

    return app


# export app for Vercel
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
