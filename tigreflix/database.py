import sqlite3
import json
import os
from tigreflix.config import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Cria as tabelas se não existirem e migra dados do JSON legado."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            added_by TEXT NOT NULL,
            watched INTEGER NOT NULL DEFAULT 0,
            poster TEXT
        )
    """)
    conn.commit()
    conn.close()

    _migrate_from_json()


def _migrate_from_json(path="filmes.json"):
    """Importa os filmes do filmes.json para o banco, se o arquivo existir."""
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        filmes = json.load(f)

    conn = get_conn()
    cursor = conn.cursor()
    migrated = 0
    for f in filmes:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO movies (title, added_by, watched, poster) VALUES (?, ?, ?, ?)",
                (
                    f.get("nome", "").strip(),
                    f.get("adicionado_por", "desconhecido"),
                    1 if f.get("assistido") else 0,
                    f.get("capa"),
                ),
            )
            if cursor.rowcount:
                migrated += 1
        except Exception as e:
            print(f"[migrate] Pulando '{f.get('nome')}': {e}")

    conn.commit()
    conn.close()

    if migrated:
        os.rename(path, path + ".migrado")
        print(f"[migrate] {migrated} filmes importados do JSON. Arquivo renomeado para {path}.migrado")


