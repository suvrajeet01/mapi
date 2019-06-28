# coding=utf-8

from mapi.compatibility import ustr
from mapi.endpoints.tmdb import *
from mapi.metadata import MetadataMovie
from mapi.providers import Provider

__all__ = ["TMDb"]


class TMDb(Provider):
    """ Queries the TMDb API
    """

    def __init__(self, **options):
        super(TMDb, self).__init__(**options)
        if not self.api_key:
            raise MapiProviderException("TMDb requires an API key")

    def search(self, id_key=None, **parameters):
        """ Searches TMDb for movie metadata
        """
        id_tmdb = parameters.get("id_tmdb") or id_key
        id_imdb = parameters.get("id_imdb")
        title = parameters.get("title")
        year = parameters.get("year")

        if id_tmdb:
            yield self._search_id_tmdb(id_tmdb)
        elif id_imdb:
            yield self._search_id_imdb(id_imdb)
        elif title:
            for result in self._search_title(title, year):
                yield result
        else:
            raise MapiNotFoundException

    def _search_id_imdb(self, id_imdb):
        response = tmdb_find(
            self.api_key, "imdb_id", id_imdb, cache=self.cache
        )["movie_results"][0]
        return MetadataMovie(
            title=response["title"],
            date=response["release_date"],
            synopsis=response["overview"],
            media="movie",
            id_tmdb=response["id"],
        )

    def _search_id_tmdb(self, id_tmdb):
        assert id_tmdb
        response = tmdb_movies(self.api_key, id_tmdb, cache=self.cache)
        return MetadataMovie(
            title=response["title"],
            date=response["release_date"],
            synopsis=response["overview"],
            media="movie",
            id_tmdb=ustr(id_tmdb),
        )

    def _search_title(self, title, year):
        assert title
        found = False
        year_from, year_to = self._year_expand(year)
        page = 1
        page_max = 10  # each page yields max of 20 results

        while True:
            response = tmdb_search_movies(
                self.api_key, title, year, page=page, cache=self.cache
            )
            for entry in response["results"]:
                try:
                    meta = MetadataMovie(
                        title=entry["title"],
                        date=entry["release_date"],
                        synopsis=entry["overview"],
                        media="movie",
                        id_tmdb=ustr(entry["id"]),
                    )
                except ValueError:
                    continue
                if year_from <= int(meta["year"]) <= year_to:
                    yield meta
                    found = True
            if page == response["total_pages"]:
                break
            elif page >= page_max:
                break
            page += 1
        if not found:
            raise MapiNotFoundException
