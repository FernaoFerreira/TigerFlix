import sqlite3
import json
import os

DB_PATH = os.getenv("DB_PATH", "tigreflix.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Cria as tabelas se não existirem e migra dados do JSON legado."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            title TEXT NOT NULL,
            added_by TEXT NOT NULL,
            added_by_discord_id INTEGER,
            watched INTEGER NOT NULL DEFAULT 0,
            poster TEXT,
            UNIQUE(guild_id, title)
        )
    """)
    _migrate_movies_schema(cursor)
    conn.commit()
    conn.close()

    _migrate_from_json()


def _column_exists(cursor, table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def _has_global_title_unique(cursor) -> bool:
    cursor.execute("PRAGMA index_list(movies)")
    for index in cursor.fetchall():
        index_name = index[1]
        is_unique = bool(index[2])
        if not is_unique:
            continue
        cursor.execute(f"PRAGMA index_info({index_name})")
        columns = [row[2] for row in cursor.fetchall()]
        if columns == ["title"]:
            return True
    return False


def _migrate_movies_schema(cursor):
    """Aplica migrações pequenas e preserva os dados existentes."""
    if not _column_exists(cursor, "movies", "guild_id"):
        cursor.execute("ALTER TABLE movies ADD COLUMN guild_id INTEGER")

    if not _column_exists(cursor, "movies", "added_by_discord_id"):
        cursor.execute("ALTER TABLE movies ADD COLUMN added_by_discord_id INTEGER")

    if _has_global_title_unique(cursor):
        cursor.execute("ALTER TABLE movies RENAME TO movies_old")
        cursor.execute("""
            CREATE TABLE movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                title TEXT NOT NULL,
                added_by TEXT NOT NULL,
                added_by_discord_id INTEGER,
                watched INTEGER NOT NULL DEFAULT 0,
                poster TEXT,
                UNIQUE(guild_id, title)
            )
        """)
        cursor.execute("""
            INSERT INTO movies (
                id, guild_id, title, added_by, added_by_discord_id, watched, poster
            )
            SELECT id, guild_id, title, added_by, added_by_discord_id, watched, poster
            FROM movies_old
        """)
        cursor.execute("DROP TABLE movies_old")


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

