from random import choice

from tigreflix.movie_api import get_movie_details, search_movies
from tigreflix.repositories.movierepository import (
    add_movie,
    find_movie,
    list_movies,
    mark_watched,
    remove_movie,
)


def add_movie_to_list(query: str, added_by: str) -> tuple[bool, str | dict]:
    resultados = search_movies(query)
    if not resultados:
        return False, "Nenhum filme encontrado."

    chosen_title = resultados[0]["Title"]

    if find_movie(chosen_title):
        return False, f'"**{chosen_title}**" já está na lista!'

    detalhes = get_movie_details(chosen_title)
    if not detalhes:
        return False, "Não foi possível obter detalhes do filme."

    poster = detalhes.get("Poster") if detalhes.get("Poster") != "N/A" else None
    added = add_movie(detalhes["Title"], added_by, poster)

    if not added:
        return False, f'"**{detalhes["Title"]}**" já está na lista!'
    
    return True, detalhes


def search_and_select_movie(query: str) -> list[dict]:
    return search_movies(query)


def get_movie_list() -> list[dict]:
    """Retorna todos os filmes da lista."""
    return list_movies()


def remove_movie_from_list(title: str) -> bool:
    """Remove um filme pelo nome. Retorna True se foi removido."""
    return remove_movie(title)


def mark_movie_as_watched(title: str) -> bool:
    """Marca um filme como assistido. Retorna True se foi encontrado."""
    return mark_watched(title)


def suggest_unwatched_movie() -> dict | None:
    """Sorteia um filme não assistido. Retorna None se não houver opções."""
    movies = list_movies()
    unwatched_movies = [movie for movie in movies if not movie["watched"]]
    if not unwatched_movies:
        return None
    return choice(unwatched_movies)


def get_movie_details_by_title(title: str) -> dict | None:
    """Busca detalhes completos de um filme pelo título."""
    return get_movie_details(title)
