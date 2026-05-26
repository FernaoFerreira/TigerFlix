from random import choice

from tigreflix.exceptions import (
    MovieAlreadyExistsError,
    MovieDetailsNotFoundError,
    MovieNotFoundError,
    NoUnwatchedMoviesError,
    PermissionDeniedError,
)
from tigreflix.movie_api import get_movie_details, search_movies
from tigreflix.repositories.movierepository import (
    add_movie,
    find_movie,
    list_movies,
    mark_watched,
    remove_movie,
)


def add_movie_to_list(
    guild_id: int, query: str, added_by_discord_id: int
) -> dict:
    resultados = search_movies(query)
    if not resultados:
        raise MovieNotFoundError(query)

    chosen_title = resultados[0]["Title"]

    if find_movie(guild_id, chosen_title):
        raise MovieAlreadyExistsError(chosen_title)

    detalhes = get_movie_details(chosen_title)
    if not detalhes:
        raise MovieDetailsNotFoundError(chosen_title)

    poster = detalhes.get("Poster") if detalhes.get("Poster") != "N/A" else None
    added = add_movie(guild_id, detalhes["Title"], added_by_discord_id, poster)

    if not added:
        raise MovieAlreadyExistsError(detalhes["Title"])
    
    return detalhes


def search_and_select_movie(query: str) -> list[dict]:
    return search_movies(query)


def get_movie_list(guild_id: int) -> list[dict]:
    """Retorna todos os filmes da lista."""
    return list_movies(guild_id)


def remove_movie_from_list(
    guild_id: int, title: str, requester_discord_id: int, is_admin: bool
) -> None:
    """Remove um filme se o solicitante for quem adicionou ou admin."""
    movie = find_movie(guild_id, title)
    if not movie:
        raise MovieNotFoundError(title)

    if not is_admin and movie.get("added_by_discord_id") != requester_discord_id:
        raise PermissionDeniedError(title)

    if not remove_movie(guild_id, title):
        raise MovieNotFoundError(title)


def mark_movie_as_watched(guild_id: int, title: str) -> bool:
    """Marca um filme como assistido. Retorna True se foi encontrado."""
    if not mark_watched(guild_id, title):
        raise MovieNotFoundError(title)
    return True


def suggest_unwatched_movie(guild_id: int) -> dict:
    """Sorteia um filme não assistido. Retorna None se não houver opções."""
    movies = list_movies(guild_id)
    unwatched_movies = [movie for movie in movies if not movie["watched"]]
    if not unwatched_movies:
        raise NoUnwatchedMoviesError()
    return choice(unwatched_movies)


def get_movie_details_by_title(title: str) -> dict:
    """Busca detalhes completos de um filme pelo título."""
    details = get_movie_details(title)
    if not details:
        raise MovieDetailsNotFoundError(title)
    return details
