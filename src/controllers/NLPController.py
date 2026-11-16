from .BaseController import BaseController
from models.db_schemes import project
from models.db_schemes import DataChunk
from typing import List
from stores.LLM import DocumentTypeEnum
from stores.LLM.templates import TemplateParser
import json

class nlp_controller(BaseController):
    def __init__(self,generation_client,vectordb_client,embedding_client,template_parser):
        super().__init__()
        
        self.vectordb_client = vectordb_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client
        self.template_parser = template_parser

    def create_collection_name(self, project_id : str):
        return f"collection_name_{project_id}".strip()

    def Reset_vector_db_collection (self,project: project):
        collection_name =  self.create_collection_name(project_id = project.project_id)
        return self.vectordb_client.delete_collection(collection_name = collection_name)

    def get_vector_db_collection_info(self,project:project):
         collection_name =  self.create_collection_name(project_id = project.project_id)
         collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name) 
         return json.loads(
             json.dumps(collection_info,default=lambda x : x.__dict__)
         )
    

    def index_into_vector_db(
        self,
        project: project,
        chunks: List[DataChunk],
        chunks_ids : List[int],
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
            metadata=metadata,
            record_ids = chunks_ids
        )

        return True
    
    def search_vector_db_collection(self , project :project , text : str , limit :int = 5 ) :
        
        # get collection name 
         collection_name =  self.create_collection_name(project_id = project.project_id)

         # get vector embedding text 
         vector = self.embedding_client.embed_text(text=text, document_type=DocumentTypeEnum.QUERY.value) # seach على سؤال من اليوزر يعني  كويري

         if not vector or len(vector) ==0 :
             return False 

         # search 
         Results = self.vectordb_client.search_by_vector(collection_name= collection_name , vector=vector , limit = limit )
         if not Results :
             return False 

         return Results

    def answer_rag_question(self , project :project , query : str , limit :int = 5 ) :
       
        answer , full_prompt , chat_History = None , None ,None 

        Retrieved_documents = self.search_vector_db_collection(
            project=project,
            text = query,
            limit = limit
        )
        if not Retrieved_documents or len(Retrieved_documents) == 0 :
            return  answer , full_prompt , chat_History 

        system_prompt = self.template_parser.get("rag","system_prompt",{})

        #  document_prompt = []
        #  for idx, doc in enumerate(Retrieved_documents):
        #      document_prompt.append(self.template_parser.get("rag","document_prompt",{"doc_num" = idx+1 , "chunk_text"=doc.text, }))

        document_prompt = "\n".join([
            
            self.template_parser.get("rag","document_prompt",{
                                "doc_num" : idx+1 , 
                                "chunk_text":doc.text, 
                                })

           for idx, doc in enumerate(Retrieved_documents) 
        ])

        footer_prompt = self.template_parser.get("rag","footer_prompt",{})

        chat_History= [
             self.generation_client.construct_prompt(
                 prompt = system_prompt, 
                 role= self.generation_client.enums.SYSTEM.value
             )
        ]

        full_prompt="\n\n".join([document_prompt,footer_prompt])

        answer = self.generation_client.generate_text( 
            prompt = full_prompt , 
            chat_history=chat_History,
            )

        return answer ,full_prompt , chat_History




