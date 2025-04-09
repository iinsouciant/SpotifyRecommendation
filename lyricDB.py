"""
Quick basic DB to store lyrics by spotify song ID.
Check first for data in ___ class for song lyrics, then grab from 
https://lrclib.net/docs if it does not exist. This way the process 
will not have to wait forever in between API responses.
"""

import sqlite3
from typing import Iterable, Any

type Row = sqlite3.Row
type Lyrics = list[Row]
type Song = dict[str, Any]

class LyricDB:
    def __init__(self, dbName:str = 'lyrics.db') -> None:
        if dbName[-3:] != '.db':
            dbName += '.db'
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

    def execute(self, query:str, params:tuple[int, str]|None=None) -> None:
        if params is not None:
            with self.connect():
                self.cursor = self.connection.execute(query, params)
            self.close()
            return
        with self.connect():
            self.cursor = self.connection.execute(query)
        self.close()

    def executemany(self, query:str, data:Iterable) -> None:
        with self.connect():
            self.cursor = self.get_cursor().executemany(query, data)
        self.close()

    def __create_table(self) -> None:
        self.execute('CREATE TABLE IF NOT EXISTS lyrics(id INTEGER PRIMARY KEY, plainLyrics TEXT)')

    def insert_many(self, query:str, data:list[tuple[int,str]]) -> None:
        self.executemany(query, data)

    def insert_lyric(self, id: int, lyrics: str) -> None:
        # check if song id already exists. if so, overwrite
        self.execute('INSERT or IGNORE INTO lyrics VALUES (?, ?)', (id, lyrics))

    def insert_lyric_many(self, songs:list[dict[Any, Any]]) -> None:
        data = [(song['id'], song['plainLyrics']) for song in songs]
        self.insert_many('INSERT or IGNORE INTO lyrics VALUES (?, ?)',data)

    def get_lyric_all(self) -> list[tuple[int, str]]:
        # self.connect().row_factory = sqlite3.Row
        with self.connect():
            rows = self.connection.cursor().execute('SELECT id, plainLyrics from lyrics').fetchall()
        self.close()
        return rows
    
    def search_lyric(self, song:Song) -> str|None:
        with self.connect():
            self.cursor = self.connection.execute('SELECT * FROM lyrics WHERE "id" = (?)', [song['id']])
            response = self.cursor.fetchall()
        if len(response) > 0:
            return response[0][1]



if __name__ == "__main__":
    lyrics = LyricDB()
    example = [{'id':i, 'plainLyrics':str(i)} for i in range(100)]
    for test in example[:49]:
        lyrics.insert_lyric(test['id'], test['plainLyrics'])
    for item in lyrics.get_lyric_all():
        print(item)
    lyrics.insert_lyric_many(example[49:])
    print(lyrics.get_lyric_all())
    testSong = {'id':23}
    print(lyrics.search_lyric(testSong))
    testSong = {'id':90}
    print(lyrics.search_lyric(testSong))