import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Mongo
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/everyday_legal_buddy")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")

    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_API_URL = os.getenv(
        "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions"
    )

    # Token expiration (seconds)
    JWT_ACCESS_EXPIRES_SECONDS = int(os.getenv("JWT_ACCESS_EXPIRES_SECONDS", 3600))
    JWT_REFRESH_EXPIRES_SECONDS = int(
        os.getenv("JWT_REFRESH_EXPIRES_SECONDS", 2592000)
    )  # 30 days
