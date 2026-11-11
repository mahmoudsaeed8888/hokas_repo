import logging
from ..VectordbInterface import VectordbInterface
from ..VectordbEnums import DistanceMethodEnums
from qdrant_client import QdrantClient, models


class QdrantDB(VectordbInterface):
    def __init__(self, db_path: str, distance_method:str):
        self.client = None
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT
        else:
            self.distance_method = models.Distance.COSINE

    def connect(self):
        self.client = QdrantClient(path=self.db_path)

    def disconnect(self):
        self.client = None

    def is_collection_existed(self, collection_name: str):
        return self.client.collection_exists(collection_name=collection_name)

    def list_all_collections(self):
        return self.client.get_collections()

    def get_collection_info(self, collection_name: str):
        return self.client.get_collection(collection_name=collection_name)

    def delete_collection(self, collection_name: str):
        if self.is_collection_existed(collection_name):
            self.client.delete_collection(collection_name=collection_name)
        else:
            self.logger.error("No collection to delete")
            return None

    def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
        if do_reset:
            self.delete_collection(collection_name=collection_name)

        if not self.is_collection_existed(collection_name=collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": models.VectorParams(size=embedding_size, distance=self.distance_method)
                },
                sparse_vectors_config={
                    "minicoil": models.SparseVectorParams(
                        modifier=models.Modifier.IDF
                    )
                }
            )
            return True
        return False

    def insert_one(self, collection_name: str, text: str, vector: list, metadata: dict = None, record_id: str = None):
        if not self.is_collection_existed(collection_name):
            self.logger.error("No collection exist to insert one record")
            return None
        try:
            self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.Record(
                        id=record_id,
                        vector=vector,
                        payload={"text": text, "metadata": metadata}
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error while insert: {e}")
            return False
        return True

    def insert_many(self, collection_name: str, texts: list, vectors: list,
                     metadata: list = None, record_ids: list = None, batch_size: int = 50):
        if not self.is_collection_existed(collection_name):
            self.logger.error("No collection exist to insert records")
            return None

        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            record_ids = [None] * len(texts)

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_ids = record_ids[i:batch_end]

            batch_records = [
                models.Record(
                    id=batch_ids[j],
                    vector=batch_vectors[j],
                    payload={"text": batch_texts[j], "metadata": batch_metadata[j]}
                )
                for j in range(len(batch_texts))
            ]

            try:
                self.client.upload_records(
                    collection_name=collection_name,
                    records=batch_records
                )
            except Exception as e:
                self.logger.error(f"Error while insert batch: {e}")
                return False

        return True

    def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
         return self.client.search(
            collection_name = collection_name,
            query_vector = vector,
            limit = limit
         )
