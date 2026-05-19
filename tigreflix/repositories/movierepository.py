import sqlite3
from tigreflix.database import get_conn


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
