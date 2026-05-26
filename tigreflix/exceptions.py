class MovieAlreadyExistsError(Exception):
    def __init__(self, title: str):
        self.title = title
        super().__init__(title)


class MovieNotFoundError(Exception):
    def __init__(self, title: str):
        self.title = title
        super().__init__(title)


class MovieDetailsNotFoundError(Exception):
    def __init__(self, title: str):
        self.title = title
        super().__init__(title)


class PermissionDeniedError(Exception):
    def __init__(self, title: str):
        self.title = title
        super().__init__(title)


class NoUnwatchedMoviesError(Exception):
    pass
