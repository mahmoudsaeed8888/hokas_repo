import json
import logging
import re
from typing import List

from sqlalchemy import text

from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from models.db_schemes import RetrievedDocument


class PGVectorProvider(VectorDBInterface):

    def __init__(self, db_client, distance_method: str):
        self.db_client = db_client
        self.logger = logging.getLogger(__name__)

        if distance_method == DistanceMethodEnums.DOT.value:
            self.operator = "<#>"      # negative inner product
            self.is_dot = True
        else:
            self.operator = "<=>"      # cosine distance
            self.is_dot = False

    @staticmethod
    def _safe_name(name: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid collection name: {name}")
        return name

    @staticmethod
    def _vec(vector: list) -> str:
        return "[" + ",".join(str(float(x)) for x in vector) + "]"

    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    async def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name: str) -> bool:
        async with self.db_client() as session:
            res = await session.execute(
                text("SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename=:t"),
                {"t": collection_name},
            )
            return res.scalar_one_or_none() is not None

    async def list_all_collections(self) -> List:
        async with self.db_client() as session:
            res = await session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'collection\\_%'")
            )
            return [row[0] for row in res.fetchall()]

    async def get_collection_info(self, collection_name: str) -> dict:
        name = self._safe_name(collection_name)
        async with self.db_client() as session:
            count = await session.execute(text(f"SELECT COUNT(*) FROM {name}"))
            return {"table_name": name, "record_count": count.scalar_one()}

    async def delete_collection(self, collection_name: str):
        name = self._safe_name(collection_name)
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(text(f"DROP TABLE IF EXISTS {name}"))
        return True

    async def create_collection(self, collection_name: str,
                                embedding_size: int,
                                do_reset: bool = False):
        name = self._safe_name(collection_name)

        if do_reset:
            await self.delete_collection(name)

        if not await self.is_collection_existed(name):
            async with self.db_client() as session:
                async with session.begin():
                    await session.execute(text(f"""
                        CREATE TABLE {name} (
                            id BIGSERIAL PRIMARY KEY,
                            text TEXT,
                            vector vector({int(embedding_size)}),
                            metadata JSONB DEFAULT '{{}}'::jsonb,
                            chunk_id INTEGER
                        )
                    """))
            return True

        return False

    async def insert_one(self, collection_name: str, text_: str = None, vector: list = None,
                         metadata: dict = None, record_id: str = None, **kwargs):
        # accepts `text` too, to match the interface's parameter name
        text_value = text_ if text_ is not None else kwargs.get("text")
        return await self.insert_many(
            collection_name=collection_name,
            texts=[text_value],
            vectors=[vector],
            metadata=[metadata],
            record_ids=[record_id],
        )

    async def insert_many(self, collection_name: str, texts: list,
                          vectors: list, metadata: list = None,
                          record_ids: list = None, batch_size: int = 50):
        name = self._safe_name(collection_name)

        if not await self.is_collection_existed(name):
            self.logger.error(f"Can not insert into non-existed collection: {name}")
            return False

        if metadata is None:
            metadata = [None] * len(texts)
        if record_ids is None:
            record_ids = [None] * len(texts)

        stmt = text(f"""
            INSERT INTO {name} (text, vector, metadata, chunk_id)
            VALUES (:text, CAST(:vector AS vector), CAST(:metadata AS jsonb), :chunk_id)
        """)

        try:
            async with self.db_client() as session:
                async with session.begin():
                    for i in range(0, len(texts), batch_size):
                        end = i + batch_size
                        rows = [
                            {
                                "text": texts[x],
                                "vector": self._vec(vectors[x]),
                                "metadata": json.dumps(metadata[x] or {}),
                                "chunk_id": record_ids[x],
                            }
                            for x in range(i, min(end, len(texts)))
                        ]
                        await session.execute(stmt, rows)
        except Exception as e:
            self.logger.error(f"Error while inserting batch: {e}")
            return False

        return True

    async def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
        name = self._safe_name(collection_name)

        if not await self.is_collection_existed(name):
            return None

        score_expr = (
            f"-(vector {self.operator} CAST(:v AS vector))" if self.is_dot
            else f"1 - (vector {self.operator} CAST(:v AS vector))"
        )

        async with self.db_client() as session:
            res = await session.execute(
                text(f"""
                    SELECT text, {score_expr} AS score
                    FROM {name}
                    ORDER BY vector {self.operator} CAST(:v AS vector)
                    LIMIT :limit
                """),
                {"v": self._vec(vector), "limit": limit},
            )
            rows = res.fetchall()

        if not rows:
            return None

        return [RetrievedDocument(score=row.score, text=row.text) for row in rows]