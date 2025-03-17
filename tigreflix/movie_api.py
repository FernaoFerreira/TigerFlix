# movie_api.py
import requests
from tigreflix.config import OMDB_API_KEY

def search_movies(query):
    """Fetches a list of movies from OMDB API"""
    url = f"http://www.omdbapi.com/?s={query}&apikey={OMDB_API_KEY}"
    response = requests.get(url).json()
    return response.get("Search", []) if response.get("Response") == "True" else []
    