import requests
from urllib.parse import quote
from tigreflix.config import OMDB_API_KEY


def search_movies(query: str) -> list[dict]:
    """Busca filmes por nome. Retorna lista com Title, Year, Poster, imdbID."""
    url = f"http://www.omdbapi.com/?s={quote(query)}&apikey={OMDB_API_KEY}"
    try:
        resp = requests.get(url, timeout=5).json()
        if resp.get("Response") == "True":
            return resp.get("Search", [])
    except Exception as e:
        print(f"[movie_api] Erro na busca: {e}")
    return []


def get_movie_details(title: str) -> dict | None:
    """Busca detalhes completos de um filme pelo título exato (Plot, Director, etc.)."""
    url = f"http://www.omdbapi.com/?t={quote(title)}&apikey={OMDB_API_KEY}"
    try:
        resp = requests.get(url, timeout=5).json()
        if resp.get("Response") == "True":
            return resp
    except Exception as e:
        print(f"[movie_api] Erro nos detalhes: {e}")
    return None
