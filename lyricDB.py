"""
Quick basic DB to store lyrics by spotify song ID.
Check first for data in ___ class for song lyrics, then grab from
https://lrclib.net/docs if it does not exist. This way the process
will not have to wait forever in between API responses.
Ref: https://docs.python.org/3/library/sqlite3.html
"""

import sqlite3
from typing import Iterable, Any
from pandas import read_sql, DataFrame

type Row = sqlite3.Row
type Lyrics = list[Row]
type Song = Any


class LyricDB:
    def __init__(self, dbName: str = "lyrics.db") -> None:
        if dbName[-3:] != ".db":
            dbName += ".db"
        self.dbName = dbName
        self.connect()
        # use cursor to send commands to the sql db
        self.cursor = self.get_cursor()
        self.__create_table()

    def close(self) -> None:
        self.connection.close()

    def connect(self) -> sqlite3.Connection:
        self.connection = sqlite3.connect(self.dbName)
        return self.connection

    def get_cursor(self) -> sqlite3.Cursor:
        self.cursor = self.connect().cursor()
        return self.cursor

    def execute(self, query: str, params: tuple[str, str] | None = None) -> None:
        if params is not None:
            with self.connect():
                self.cursor = self.connection.execute(query, params)
            self.close()
            return
        with self.connect():
            self.cursor = self.connection.execute(query)
        self.close()

    def executemany(self, query: str, data: Iterable) -> None:
        with self.connect():
            self.cursor = self.get_cursor().executemany(query, data)
        self.close()

    def __create_table(self) -> None:
        self.execute(
            "CREATE TABLE IF NOT EXISTS lyrics(item_id INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT, plainLyrics TEXT)"
        )

    def insert_many(self, query: str, data: list[tuple[str, str]]) -> None:
        self.executemany(query, data)

    def insert_lyric(self, id: str, lyrics: str) -> None:
        # check if song id already exists. if so, ignore
        self.execute("INSERT or IGNORE INTO lyrics(id, plainLyrics) VALUES (?, ?)", (id, lyrics))

    def replace_lyric(self, id: str, lyrics: str) -> None:
        # check if song id already exists. if so, overwrite
        self.execute("INSERT or REPLACE INTO lyrics(id, plainLyrics) VALUES (?, ?)", (id, lyrics))

    def insert_lyric_many(self, songs: list[dict[Any, Any]]) -> None:
        data = [(song["id"], song["plainLyrics"]) for song in songs]
        self.insert_many("INSERT or IGNORE INTO lyrics(id, plainLyrics) VALUES (?, ?)", data)

    def get_lyric_all(self) -> list[tuple[str, str]]:
        # self.connect().row_factory = sqlite3.Row
        with self.connect():
            rows = (
                self.connection.cursor()
                .execute("SELECT id, plainLyrics from lyrics")
                .fetchall()
            )
        self.close()
        return rows

    def get_all(self) -> list[tuple[str, str, int]]:
        # self.connect().row_factory = sqlite3.Row
        with self.connect():
            rows = (
                self.connection.cursor()
                .execute("SELECT id, plainLyrics, item_id from lyrics")
                .fetchall()
            )
        self.close()
        return rows

    def search_lyric(self, song: Song) -> str | None:
        with self.connect():
            self.cursor = self.connection.execute(
                'SELECT * FROM lyrics WHERE "id" = (?)', [song["id"]]
            )
            response = self.cursor.fetchall()
        if len(response) > 0:
            return response[0][1]

    def remove_lyric(self, id: str) -> None:
        with self.connect():
            self.cursor = self.connection.execute(
                "DELETE FROM lyrics WHERE id = (?)", [id]
            )
            # doesn't look like there's a way to retrieve that data w/o query select beforehand
            # response = self.cursor.fetchall()
    
    def get_df(self) -> DataFrame:
        """ Get DataFrame from pandas to get embeddings for semantic search"""
        return read_sql('SELECT * FROM lyrics',self.connect())
    

if __name__ == "__main__":
    lyrics = LyricDB()
    example = [{"id": str(i), "plainLyrics": str(i)} for i in range(100)]
    for test in example[:49]:
        lyrics.insert_lyric(test["id"], test["plainLyrics"])
    for item in lyrics.get_lyric_all():
        print(item)
    lyrics.insert_lyric_many(example[49:])
    print(lyrics.get_lyric_all())
    testSong = {"id": 23}
    print(lyrics.search_lyric(testSong))
    testSong = {"id": 90}
    print(lyrics.search_lyric(testSong))
    for test in example:
        lyrics.remove_lyric(test["id"])
        print(lyrics.search_lyric(test))
