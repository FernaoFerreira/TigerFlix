# database.py
import sqlite3

def init_db():
    """Creates the database and tables if they don’t exist"""
    conn = sqlite3.connect("zeroflix.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            added_by TEXT,
            watched BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_movie(title, user):
    """Adds a movie to the database"""
    conn = sqlite3.connect("zeroflix.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movies (title, added_by) VALUES (?, ?)", (title, user))
    conn.commit()
    conn.close()


def list_movies():
    conn = sqlite3.connect("zeroflix.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, added_by FROM movies")
    movies = cursor.fetchall
    conn.close
    return movies

