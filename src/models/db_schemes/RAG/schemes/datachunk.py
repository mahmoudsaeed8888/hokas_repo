from .Rag_base import SQLAlchemyBase
from sqlalchemy import Column, Integer, DateTime, func, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from pydantic import BaseModel
from typing import Optional

import uuid

class DataChunk(SQLAlchemyBase):

    __tablename__ = "chunks"

    chunk_id = Column(Integer , primary_key=True , autoincrement=True)
    chunk_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True , nullable=False) 
    
    chunk_text = Column(String ,nullable=False )
    chunk_metadata = Column(JSONB ,nullable=True )
    chunk_order =Column(Integer , nullable=False )
    
    chunk_project_id = Column(Integer , ForeignKey("projects.project_id"), nullable=False )
    chunk_asset_id = Column(Integer , ForeignKey("assets.asset_id"), nullable=False )

    chunk_parent_id = Column(Integer, ForeignKey("chunks.chunk_id"), nullable=True) # تبع بيرنت ايه 
    chunk_is_parent = Column(Boolean, default=False, nullable=False) #نوعي parent ولا child؟

    project  = relationship("Project", back_populates="chunks")
    asset  = relationship("Asset", back_populates="chunks")

    created_at = Column(DateTime(timezone=True),server_default=func.now(), nullable=False)  
    updated_at =Column(DateTime(timezone=True),onupdate=func.now(), nullable=True)  

    __table_args__=(
          Index('ix_chunk_project_id',chunk_project_id),
          Index('ix_chunk_asset_id',chunk_asset_id)
     )

    

class RetrievedDocument(BaseModel):
        text :str 
        score :float
        metadata: Optional[dict] = None





