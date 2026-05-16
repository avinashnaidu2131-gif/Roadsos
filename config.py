import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "roadsos-dev-key")
    DEBUG = os.environ.get("FLASK_ENV", "development") == "development"
    DATA_DIR = os.path.join(BASE_DIR, "data")
    DB_PATH = os.path.join(DATA_DIR, "roadsos.db")
    EMERGENCY_NUMBERS_PATH = os.path.join(DATA_DIR, "emergency_numbers.json")
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT = 15
    DEFAULT_RADIUS = 5000
    MAX_RADIUS = 20000
    OFFLINE_MODE = os.environ.get("OFFLINE_MODE", "false").lower() == "true"
    MAX_RESULTS = 5
