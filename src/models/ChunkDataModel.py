from .BaseDatamodel import BaseDataModel
from .db_schemes import DataChunk
from .enums.ResponseEnums import ResponseSignal
from .enums.Database_Enums import Database_Enums
from bson.objectid import ObjectId
from pymongo import InsertOne
from sqlalchemy.future import select
from sqlalchemy import func, delete


class ChunkModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client = db_client


    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        return instance

    async def create_chunk(self, chunk: DataChunk):

        async with self.db_client() as session:
            async with session.begin():
                session.add(chunk)
            await session.commit()
            await session.refresh(chunk)
        return chunk

    async def get_chunk(self, chunk_id: str):

        async with self.db_client() as session:
            result = await session.execute(select(DataChunk).where(DataChunk.chunk_id == chunk_id))
            chunk = result.scalar_one_or_none()
        return chunk

    
    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
    
        async with self.db_client() as session:
            async with session.begin():
                for i in range(0, len(chunks), batch_size):
                    session.add_all(chunks[i:i + batch_size])
                await session.flush()      # بيملّي chunk_id في كل object
    
        return chunks                   


    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        async with self.db_client() as session:
            stmt = delete(DataChunk).where(DataChunk.chunk_project_id == project_id)
            result = await session.execute(stmt)
            await session.commit()
        return result.rowcount

    async def get_poject_chunks(self, project_id: int, page_no: int = 1,
                                page_size: int = 50, is_parent: bool | None = None):
        async with self.db_client() as session:
            stmt = select(DataChunk).where(DataChunk.chunk_project_id == project_id)

            if is_parent is not None:
                stmt = stmt.where(DataChunk.chunk_is_parent == is_parent)

            stmt = (
                stmt.order_by(DataChunk.chunk_id)
                .offset((page_no - 1) * page_size)
                .limit(page_size)
            )

            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_chunks_by_ids(self, chunk_ids: list[int]):
        if not chunk_ids:
            return []

        async with self.db_client() as session:
            stmt = select(DataChunk).where(DataChunk.chunk_id.in_(chunk_ids))
            result = await session.execute(stmt)
            rows = result.scalars().all()

        by_id = {r.chunk_id: r for r in rows}
        return [by_id[i] for i in chunk_ids if i in by_id]


     