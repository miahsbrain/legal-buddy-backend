import datetime

from bson.objectid import ObjectId

from api.extensions import db


class ContractService:
    def __init__(self):
        self.col = db["contracts"]

    # create: userId is string
    def create_contract(
        self, user_id: str, title: str, summary: dict, status: str = "summarized"
    ):
        doc = {
            "userId": ObjectId(user_id),
            "title": title,
            "uploadDate": datetime.datetime.utcnow().isoformat(),
            "status": status,
            "summary": summary,
        }
        res = self.col.insert_one(doc)
        doc["_id"] = res.inserted_id
        doc["id"] = str(res.inserted_id)
        doc["userId"] = user_id
        doc.pop("_id", None)
        return doc

    def list_by_user(self, user_id: str):
        cursor = self.col.find({"userId": ObjectId(user_id)}).sort("uploadDate", -1)
        out = []
        for c in cursor:
            out.append(
                {
                    "id": str(c["_id"]),
                    "title": c.get("title"),
                    "status": c.get("status"),
                    "uploadDate": c.get("uploadDate"),
                    "summary": c.get("summary"),
                }
            )
        return out

    def get_by_id_and_user(self, contract_id: str, user_id: str):
        c = self.col.find_one(
            {"_id": ObjectId(contract_id), "userId": ObjectId(user_id)}
        )
        return c

    def update_contract(self, contract_id: str, updates: dict):
        result = self.col.update_one({"_id": ObjectId(contract_id)}, {"$set": updates})
        return result.modified_count

    def delete_contract(self, contract_id: str):
        return self.col.delete_one({"_id": ObjectId(contract_id)}).deleted_count

    def attach_summary_and_set_status(
        self, contract_id: str, summary: dict, status: str
    ):
        self.col.update_one(
            {"_id": ObjectId(contract_id)},
            {"$set": {"summary": summary, "status": status}},
        )
        return self.col.find_one({"_id": ObjectId(contract_id)})
