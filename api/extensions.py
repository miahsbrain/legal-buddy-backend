import os

from flask_jwt_extended import JWTManager
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "legalbuddy")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB_NAME]
jwt = JWTManager()
