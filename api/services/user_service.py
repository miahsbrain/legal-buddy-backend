import datetime

import bcrypt
from bson.objectid import ObjectId

from api.extensions import db


class UserService:
    def __init__(self):
        self.col = db["users"]
        self.blacklist = db["token_blacklist"]

    # ---------- CRUD ----------
    def create_user(
        self, email: str, password: str, first_name: str = None, last_name: str = None
    ):
        if self.col.find_one({"email": email}):
            raise ValueError("Email already registered")
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        res = self.col.insert_one(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": hashed.decode("utf-8"),
                "createdAt": datetime.datetime.utcnow().isoformat(),
            }
        )
        return str(res.inserted_id)

    def get_by_email(self, email: str):
        return self.col.find_one({"email": email})

    def get_by_id(self, user_id: str):
        return self.col.find_one({"_id": ObjectId(user_id)})

    def update_user(self, user_id: str, updates: dict):
        result = self.col.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        return result.modified_count

    def delete_user(self, user_id: str):
        return self.col.delete_one({"_id": ObjectId(user_id)}).deleted_count

    # ---------- Password ----------
    def verify_password(self, password_plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(
                password_plain.encode("utf-8"), hashed.encode("utf-8")
            )
        except Exception:
            return False

    # ---------- Token blacklist ----------
    def revoke_token(self, jti: str, token_type: str, expires_at_ts: int = None):
        doc = {
            "jti": jti,
            "token_type": token_type,
            "revokedAt": datetime.datetime.utcnow().isoformat(),
        }
        if expires_at_ts:
            doc["expiresAt"] = expires_at_ts
        self.blacklist.insert_one(doc)

    def is_token_revoked(self, jti: str) -> bool:
        return bool(self.blacklist.find_one({"jti": jti}))
