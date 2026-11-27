import json
from sqlalchemy import select, Table, Column, Integer, Text, MetaData
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text as sql_text
from pgvector.sqlalchemy import Vector

from models.db_schemes.RAG.schemes.datachunk import RetrievedDocument
from ..VectorDBEnums import DistanceMethodEnums


class PGVectorProvider:

    def __init__(self, db_client, distance_method: str = "cosine"):
        self.db_client = db_client
        self.distance_method = distance_method

        if distance_method == DistanceMethodEnums.DOT.value:
            self.ops = "vector_ip_ops"
        else:
            self.ops = "vector_cosine_ops"

    # ---------- connection ----------
    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))

    async def disconnect(self):
        pass

    # ---------- collections ----------
    async def is_collection_existed(self, collection_name: str) -> bool:
        async with self.db_client() as session:
            res = await session.execute(
                sql_text("SELECT 1 FROM pg_tables WHERE tablename = :name"),
                {"name": collection_name},
            )
            return res.scalar_one_or_none() is not None

    async def delete_collection(self, collection_name: str) -> bool:
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text(f'DROP TABLE IF EXISTS "{collection_name}"'))
        return True

    async def create_collection(self, collection_name: str, embedding_size: int,
                                do_reset: bool = False) -> bool:
        if do_reset:
            await self.delete_collection(collection_name)

        if await self.is_collection_existed(collection_name):
            return False

        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text(f'''
                    CREATE TABLE "{collection_name}" (
                        id SERIAL PRIMARY KEY,
                        chunk_id INTEGER,
                        chunk_text TEXT,
                        metadata JSONB,
                        vector vector({int(embedding_size)})
                    )
                '''))
                await session.execute(sql_text(f'''
                    CREATE INDEX "{collection_name}_vec_idx"
                    ON "{collection_name}" USING hnsw (vector {self.ops})
                '''))
        return True

    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client() as session:
            res = await session.execute(sql_text(f'SELECT COUNT(*) FROM "{collection_name}"'))
            return {"table_name": collection_name, "records_count": res.scalar_one()}

    # ---------- insert ----------
    async def insert_many(self, collection_name: str, texts: list, vectors: list,
                          metadata: list | None = None, record_ids: list | None = None,
                          batch_size: int = 50) -> bool:

        metadata = metadata or [None] * len(texts)
        record_ids = record_ids or [None] * len(texts)

        rows = [
            {
                "chunk_id": record_ids[i],
                "chunk_text": texts[i],
                "metadata": json.dumps(metadata[i]) if metadata[i] is not None else None,
                "vector": "[" + ",".join(str(float(x)) for x in vectors[i]) + "]",
            }
            for i in range(len(texts))
        ]

        stmt = sql_text(f'''
            INSERT INTO "{collection_name}" (chunk_id, chunk_text, metadata, vector)
            VALUES (:chunk_id, :chunk_text, CAST(:metadata AS jsonb), CAST(:vector AS vector))
        ''')

        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(rows), batch_size):
                    await session.execute(stmt, rows[i:i + batch_size])
        return True

    # ---------- search ----------
    def _get_table(self, collection_name: str, embedding_size: int) -> Table:
        return Table(
            collection_name,
            MetaData(),
            Column("id", Integer, primary_key=True),
            Column("chunk_id", Integer),
            Column("chunk_text", Text),
            Column("metadata", JSONB),
            Column("vector", Vector(embedding_size)),
        )

    async def search_by_vector(self, collection_name: str, vector: list,
                               limit: int = 5, score_threshold: float | None = None):

        table = self._get_table(collection_name, embedding_size=len(vector))

        if self.distance_method == DistanceMethodEnums.DOT.value:
            distance = table.c.vector.max_inner_product(vector)   # أقل = أقرب
            score = (-distance).label("score")
        else:
            distance = table.c.vector.cosine_distance(vector)
            score = (1 - distance).label("score")

        stmt = (
            select(table.c.chunk_id, table.c.chunk_text, table.c.metadata, score)
            .order_by(distance)
            .limit(limit)
        )

        if score_threshold is not None:
            stmt = stmt.where(score >= score_threshold) if False else stmt.where(
                (1 - distance) >= score_threshold
            )

        async with self.db_client() as session:
            res = await session.execute(stmt)
            return [
                RetrievedDocument(
                    chunk_id=r.chunk_id,
                    text=r.chunk_text,
                    score=float(r.score),
                    metadata=r.metadata,
                )
                for r in res.fetchall()
            ]