import json
from models.db_schemes.RAG.schemes.datachunk import RetrievedDocument
from sqlalchemy.sql import text as sql_text
from ..VectorDBEnums import DistanceMethodEnums


class PGVectorProvider:
    def __init__(self, db_client, distance_method: str = "cosine"):
        self.db_client = db_client
        if distance_method == DistanceMethodEnums.DOT.value:
            self.ops = "vector_ip_ops"
            self.op = "<#>"
            self.score_expr = "-(vector <#> CAST(:vec AS vector))"
        else:
            self.ops = "vector_cosine_ops"
            self.op = "<=>"
            self.score_expr = "1 - (vector <=> CAST(:vec AS vector))"

    async def connect(self):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))

    async def disconnect(self):
        pass

    async def is_collection_existed(self, collection_name: str) -> bool:
        async with self.db_client() as session:
            res = await session.execute(
                sql_text("SELECT 1 FROM pg_tables WHERE tablename = :name"),
                {"name": collection_name},
            )
            return res.scalar_one_or_none() is not None

    async def delete_collection(self, collection_name: str):
        async with self.db_client() as session:
            async with session.begin():
                await session.execute(sql_text(f'DROP TABLE IF EXISTS "{collection_name}"'))
        return True

    async def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):
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

    async def get_collection_info(self, collection_name: str):
        async with self.db_client() as session:
            res = await session.execute(sql_text(f'SELECT COUNT(*) FROM "{collection_name}"'))
            return {"table_name": collection_name, "records_count": res.scalar_one()}

    async def insert_many(self, collection_name, texts, vectors, metadata=None,
                          record_ids=None, batch_size: int = 50):
        metadata = metadata or [None] * len(texts)
        record_ids = record_ids or [None] * len(texts)

        rows = [
            {
                "chunk_id": record_ids[i],
                "chunk_text": texts[i],
                "metadata": json.dumps(metadata[i]) if metadata[i] is not None else None,
                "vector": "[" + ",".join(str(x) for x in vectors[i]) + "]",
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

    async def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
        vec = "[" + ",".join(str(x) for x in vector) + "]"
        async with self.db_client() as session:
            res = await session.execute(sql_text(f'''
                SELECT chunk_text, metadata, {self.score_expr} AS score
                FROM "{collection_name}"
                ORDER BY vector {self.op} CAST(:vec AS vector)
                LIMIT :limit
            '''), {"vec": vec, "limit": limit})
            return [
                RetrievedDocument(text=r.chunk_text, metadata=r.metadata, score=float(r.score))
                for r in res.fetchall()
            ]