"""
Seed script: creates demo user and a demo contract summary
Run: python -m api.scripts.seed_demo
"""

import os

from api.services.contract_service import ContractService
from api.services.user_service import UserService


def seed():
    us = UserService()
    cs = ContractService()
    email = os.getenv("DEMO_EMAIL", "demo@example.com")
    password = os.getenv("DEMO_PASSWORD", "password123")
    existing = us.get_by_email(email)
    if existing:
        uid = str(existing["_id"])
        print("Demo user exists:", uid)
    else:
        uid = us.create_user(email, password)
        print("Created demo user:", uid)

    demo_summary = {
        "title": "Demo Service Agreement - Acme",
        "keyObligations": ["Pay $100/month", "Provide access to service"],
        "risks": [
            {
                "id": "1",
                "title": "Auto-renew",
                "description": "Auto-renews every year",
                "severity": "high",
            }
        ],
        "suggestedEdits": ["Negotiate cancellation terms"],
        "rights": ["Access during subscription"],
    }

    doc = cs.create_contract(
        user_id=uid, title="Demo Service Agreement - Acme", summary=demo_summary
    )
    print("Inserted demo contract:", doc["id"])


if __name__ == "__main__":
    seed()
