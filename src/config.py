import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") or ""
AHREFS_API_KEY = os.getenv("AHREFS_API_KEY")
