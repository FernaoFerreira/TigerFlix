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


# ── CRUD ────────────────────────────────────────────────────────────────────


def add_movie(title: str, added_by: str, poster: str | None = None) -> bool:
    """Adiciona um filme. Retorna True se adicionado, False se já existia."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO movies (title, added_by, poster) VALUES (?, ?, ?)",
        (title, added_by, poster),
    )
    added = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return added


def remove_movie(title: str) -> bool:
    """Remove um filme pelo nome (case-insensitive). Retorna True se removido."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE LOWER(title) = LOWER(?)", (title,))
    removed = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return removed


def mark_watched(title: str) -> bool:
    """Marca um filme como assistido. Retorna True se encontrado."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE movies SET watched = 1 WHERE LOWER(title) = LOWER(?)", (title,)
    )
    updated = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return updated


def list_movies() -> list[dict]:
    """Retorna todos os filmes como lista de dicts."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT title, added_by, watched, poster FROM movies ORDER BY id")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def find_movie(title: str) -> dict | None:
    """Busca um filme pelo nome exato (case-insensitive)."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, added_by, watched, poster FROM movies WHERE LOWER(title) = LOWER(?)",
        (title,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
