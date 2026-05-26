import sqlite3
from tigreflix.database import get_conn


def add_movie(
    guild_id: int, title: str, added_by_discord_id: int, poster: str | None = None
) -> bool:
    """Adiciona um filme. Retorna True se adicionado, False se já existia."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO movies (
            guild_id, title, added_by, added_by_discord_id, poster
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (guild_id, title, str(added_by_discord_id), added_by_discord_id, poster),
    )
    added = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return added


def remove_movie(guild_id: int, title: str) -> bool:
    """Remove um filme pelo nome (case-insensitive). Retorna True se removido."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM movies WHERE guild_id = ? AND LOWER(title) = LOWER(?)",
        (guild_id, title),
    )
    removed = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return removed


def mark_watched(guild_id: int, title: str) -> bool:
    """Marca um filme como assistido. Retorna True se encontrado."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE movies
        SET watched = 1
        WHERE guild_id = ? AND LOWER(title) = LOWER(?)
        """,
        (guild_id, title),
    )
    updated = cursor.rowcount == 1
    conn.commit()
    conn.close()
    return updated


def list_movies(guild_id: int) -> list[dict]:
    """Retorna todos os filmes como lista de dicts."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT title, added_by, added_by_discord_id, watched, poster
        FROM movies
        WHERE guild_id = ?
        ORDER BY id
        """,
        (guild_id,),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def find_movie(guild_id: int, title: str) -> dict | None:
    """Busca um filme pelo nome exato (case-insensitive)."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT title, added_by, added_by_discord_id, watched, poster
        FROM movies
        WHERE guild_id = ? AND LOWER(title) = LOWER(?)
        """,
        (guild_id, title),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
