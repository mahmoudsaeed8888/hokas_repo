from .BaseController import BaseController
from  models.db_schemes import Project
from models.db_schemes import DataChunk
from models import ChunkModel
from typing import List
from stores.LLM import DocumentTypeEnum
from stores.LLM.templates import TemplateParser
import json
import asyncio

from sentence_transformers import CrossEncoder   

from rank_bm25 import BM25Okapi

class nlp_controller(BaseController):
    def __init__(self,generation_client,vectordb_client,embedding_client,template_parser):
        super().__init__()
        
        self.vectordb_client = vectordb_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client
        self.template_parser = template_parser

        self.reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

    def create_collection_name(self, project_id: str):
       return f"collection_{self.embedding_client.embedding_size}_{project_id}".strip()
 

    async def Reset_vector_db_collection (self,project: Project):
        collection_name =  self.create_collection_name(project_id = project.project_id)
        return await self.vectordb_client.delete_collection(collection_name = collection_name)

    async def get_vector_db_collection_info(self,project:Project):
         collection_name =  self.create_collection_name(project_id = project.project_id)
         collection_info = await self.vectordb_client.get_collection_info(collection_name=collection_name) 
         return json.loads(
             json.dumps(collection_info,default=lambda x : x.__dict__)
         )
    

   
    async def index_into_vector_db(self, project: Project, chunks: List[DataChunk],
                               chunks_ids: List[int], do_reset: bool = False):

        collection_name = self.create_collection_name(project_id=project.project_id)

        texts = [c.chunk_text for c in chunks]
        metadata = [
            {**(c.chunk_metadata or {}), "chunk_parent_id": c.chunk_parent_id}
            for c in chunks
        ]

        # asyncio.to_thread عشان الـ sleep جوه الـ retry ما يجمّدش السيرفر
        vectors = await asyncio.to_thread(
            self.embedding_client.embed_texts,
            text=texts,
            document_type=DocumentTypeEnum.DOCUMENT.value,
        )
        if not vectors:
            return False

        await self.vectordb_client.create_collection(
            collection_name=collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )

        return await self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            vectors=vectors,
            metadata=metadata,
            record_ids=chunks_ids,
        )
    
    async def search_vector_db_collection(self, project: Project, text: str, limit: int = 5, candidates_k: int = 30):
        collection_name = self.create_collection_name(project_id=project.project_id)

        vector = self.embedding_client.embed_text(
            text=text, document_type=DocumentTypeEnum.QUERY.value
        )
        if not vector or len(vector) == 0:
            return False

        # 1) Semantic
        dense_results = await self.vectordb_client.search_by_vector(
            collection_name=collection_name, vector=vector, limit=candidates_k
        )

        # 2) Traditional (BM25)
        sparse_results = await self.keyword_search(collection_name, text, candidates_k)

        if not dense_results and not sparse_results:
            return False

        # 3) Fusion
       
        fused = self.reciprocal_rank_fusion([dense_results or [], sparse_results])[:candidates_k]

        dense_ids  = [r.chunk_id for r in (dense_results or [])]
        sparse_ids = [r.chunk_id for r in sparse_results]
        fused_ids  = [r.chunk_id for r in fused]

        print("DENSE  :", dense_ids[:10])
        print("SPARSE :", sparse_ids[:10])
        print("FUSED  :", fused_ids[:10])
        print("only in sparse:", len(set(sparse_ids) - set(dense_ids)))
        print("only in dense :", len(set(dense_ids) - set(sparse_ids)))
        print("overlap       :", len(set(dense_ids) & set(sparse_ids)))

        # 4) Rerank
        pairs = [(text, r.text) for r in fused]
        scores = await asyncio.to_thread(self.reranker.predict, pairs)
        ranked = sorted(zip(fused, scores), key=lambda x: x[1], reverse=True)

        return [
            {
                "chunk_id": r.chunk_id,
                "text": r.text,
                "score": float(s),
                "metadata": r.metadata,
            }
            for r, s in ranked[:limit]
        ]
    

    async def answer_rag_question(self, project: Project, query: str, limit: int = 8, chunk_model=None):
    
        answer , full_prompt , chat_History = None , None ,None 

        Retrieved_documents = await self.search_vector_db_collection(
            project=project,
            text = query,
            limit = limit
        )
        if not Retrieved_documents or len(Retrieved_documents) == 0 :
            return  answer , full_prompt , chat_History 

        parent_ids = []
        for doc in Retrieved_documents:
            pid = (doc.get("metadata") or {}).get("chunk_parent_id")
            if pid is not None and pid not in parent_ids:
                parent_ids.append(pid)
            if len(parent_ids) == 3:
                break

        parents = await chunk_model.get_chunks_by_ids(parent_ids)
        if not parents:
                 return answer, full_prompt, chat_History 
         
        system_prompt = self.template_parser.get("rag","system_prompt",{})


        document_prompt = "\n".join([
        self.template_parser.get("rag", "document_prompt", {
        "doc_num": idx + 1,
        "chunk_text": p.chunk_text,
    })
    for idx, p in enumerate(parents)
])

        footer_prompt = self.template_parser.get("rag","footer_prompt",{
            "query": query
        })

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


    def reciprocal_rank_fusion(self ,results_lists, k=60):
        scores = {}
        items = {}
        for results in results_lists:
            for rank, r in enumerate(results, start=1):
                key = r.chunk_id  
                items[key] = r
                scores[key] = scores.get(key, 0) + 1 / (k + rank)
        ranked = sorted(scores, key=scores.get, reverse=True)
        return [items[key] for key in ranked]

    

    async def keyword_search(self, collection_name: str, text: str, limit: int):
        # بتجيب كل chunks الـ collection (حسب الـ API عندك)
        all_chunks = await self.vectordb_client.get_all_chunks(collection_name)
        if not all_chunks:
            return []

        tokenized_corpus = [c.text.lower().split() for c in all_chunks]
        bm25 = BM25Okapi(tokenized_corpus)

        scores = bm25.get_scores(text.lower().split())
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
        return [all_chunks[i] for i in top_idx if scores[i] > 0]

