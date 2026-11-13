from .BaseController import BaseController
from models.db_schemes import project
from models.db_schemes import DataChunk
from typing import List
from stores.LLM import DocumentTypeEnum


class nlp_controller(BaseController):
    def __init__(self,generation_client,vectordb_client,embedding_client):
        super().__init__()
        
        self.vectordb_client = vectordb_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client

    def create_collection_name(self, project_id : str):
        return f"collection_name_{project_id}".strip()

    def Reset_vector_db_collection (self,project: project):
        collection_name =  self.create_collection_name(project_id = project.project_id)
        return self.vectordb_client.delete_collection(collection_name = collection_name)

    def get_vector_collection_info(self,project:project):
         collection_name =  self.create_collection_name(project_id = project.project_id)
         collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name) 
         return collection_info

    def index_into_vector_db(
        self,
        project: project,
        chunks: List[DataChunk],
        do_reset: bool = False
    ):
        # Create collection
        collection_name = self.create_collection_name(
            project_id=project.project_id
        )

        # Manage items
        texts = [c.chunk_text for c in chunks]
        metadata = [c.chunk_metadata for c in chunks]

        # Generate embeddings
        vectors = [
            self.embedding_client.embed_text(text=text,document_type=DocumentTypeEnum.DOCUMENT.value)
            for text in texts
        ]

        # Create collection
        _ = self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset
        )

        # Insert data into vector database
        _ = self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata
        )

        return True


