import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
DB_PATH = "tigreflix.db"
if not TOKEN:
    raise ValueError("DISCORD_TOKEN não encontrado no arquivo .env")
if not OMDB_API_KEY:
    raise ValueError("OMDB_API_KEY não encontrado no arquivo .env")
if not DB_PATH:
    raise ValueError("DB_PATH não encontrado no arquivo .env")