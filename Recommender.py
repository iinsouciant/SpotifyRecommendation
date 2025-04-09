"""
https://medium.com/@zilliz_learn/getting-started-with-voyager-spotifys-nearest-neighbor-search-library-0f2f9fc6c142
https://www.youtube.com/watch?v=sNa_uiqSlJo to get embeddings
"""

import os.path
import numpy as np
import pandas as pd
from pandas import DataFrame

from sentence_transformers import SentenceTransformer
from voyager import Index, Space

from lyricDB import LyricDB

type Row = tuple[str, str]
type LyricSet = list[Row]
type Songs = list[str]


class Recommender:
    def __init__(self, database: LyricDB) -> None:
        self.indexPath = "./index.voy"

        # get data
        self.lyrics: LyricDB = database
        self.df: DataFrame = self.lyrics.get_df()
        # pretrained model to get embeddings
        self.model: SentenceTransformer = SentenceTransformer("all-MiniLM-L6-v2")

        self.index: Index = self.get_index()

    def get_index(self) -> Index:
        if os.path.isfile(self.indexPath):
            self.index = Index.load(self.indexPath)
            return self.update_index(self.index)

        # first i need to get embeddings using pretrained model
        embedding_arr = self.model.encode(self.df["plainLyrics"])
        # print(embedding_arr.shape)

        # voyager index stores and manages the vectors
        # kinda like a dictionary that points the ids to vectors
        index = Index(Space.Euclidean, num_dimensions=384)
        index.add_items(vectors=embedding_arr, ids=self.df["item_id"])
        return index

    def update_index(self, index: Index) -> Index:
        for row in self.lyrics.get_all():
            # if the id is not in index, add data
            if row[0] not in index:
                embed = self.model.encode(row[1])
                index.add_item(vector=embed, id=self.df["item_id"])
        index.save("./index.voy")
        return index

    """ Index.query()
    Query this index to retrieve the k nearest neighbors of the provided vectors.

    Parameters:

            vectors – A 32-bit floating-point NumPy array, with shape (num_dimensions,) or (num_queries, num_dimensions).

            k – The number of neighbors to return.

            num_threads – If vectors contains more than one query vector, up to num_threads will be started to perform queries in parallel. If vectors contains only one query vector, num_threads will have no effect. Defaults to using one thread per CPU core.

            query_ef – The depth of search to perform for this query. Up to query_ef candidates will be searched through to try to find up the k nearest neighbors per query vector.

    Returns:

        A tuple of (neighbor_ids, distances). If a single query vector was provided, both neighbor_ids and distances will be of shape (k,).

        If multiple query vectors were provided, both neighbor_ids and distances will be of shape (num_queries, k), ordered such that the i-th result corresponds with the i-th query vector.
    """

    def search(self, lyrics: str, k: int = 10) -> DataFrame:
        """Search the index using song lyrics and get back k nearest neighbors"""
        # take our input song lyrics and embed
        vec = self.model.encode(lyrics)
        # limit to k here to save computing power and discard low scores
        ids, distances = self.index.query(vec, k)
        results = pd.DataFrame(
            [{"item_id": i, "score": d} for i, d in zip(ids, distances)]
        )
        # adds column for score into copy of self.df
        return self.df.merge(results, on="item_id", how="inner")

    def get_recommendations(self, data: LyricSet, n: int = 10) -> Songs:
        """Returns list of Spotify song ids for those with lowest score (distance)"""
        result = self.df.copy()
        result["score"] = None
        for row in data:
            a = self.search(row[1])
            result["score"] += a["score"]
        # get lowest score
        result.sort_values("score")
        return [(row[2], row[3]) for row in result.iloc[:n].itertuples(name=None)]


if __name__ == "__main__":
    db = LyricDB()
    rec = Recommender(db)
    for test in rec.get_recommendations(db.get_lyric_all()[:10]):
        print(test)
