import os

API_BASE_URL = os.getenv(
    "AI_HIREMIND_API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

APP_TITLE = "AI HireMind"
APP_SUBTITLE = "Evidence-Driven Recruitment Intelligence"
