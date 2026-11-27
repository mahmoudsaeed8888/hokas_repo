from .BaseController import BaseController
from .ProjectController import ProjectController
import os 
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader 
from models import processEnums

from langchain_text_splitters import RecursiveCharacterTextSplitter 

class process_controller(BaseController):
    def __init__(self,project_id : str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
    

    def get_file_extension(self,file_id:str):
        return os.path.splitext(file_id)[-1]

    def get_file_loader(self,file_id:str ):
        
        file_extension=self.get_file_extension(file_id=file_id)
        file_path = os.path.join(
            self.project_path,
            file_id
        )

        if not os.path.exists(file_path):
           return None 

        if file_extension==processEnums.TXT.value :
           return TextLoader(file_path,encoding="utf-8")

        if file_extension==processEnums.PDF.value :
           return PyMuPDFLoader(file_path)
        
        return None 

    def get_file_content(self,file_id :str ):
        loader = self.get_file_loader(file_id=file_id)
        if loader : #(علشان لو الفايل مش موجود)
            return loader.load()
        else :
            return None 

   # def process_file_content(self , file_content:list , file_id : str , chunk_size:int=100 ,
   # overlap_size : int=20) :
   #      
   #      text_splitter =RecursiveCharacterTextSplitter(
   #         chunk_size=chunk_size,
   #         chunk_overlap=overlap_size,
   #         length_function=len,
   #      )
   #      
   #      file_content_texts = [
   #         rec.page_content
   #         for rec in file_content
   #      ]
   #      # List Comprehension
#
   #      file_content_metadata = [
   #         rec.metadata
   #         for rec in file_content
   #      ]
#
   #      chunks = text_splitter.create_documents(
   #         file_content_texts, 
   #         metadatas =file_content_metadata
   #      )
   #      return chunks 

    def process_file_content(self, file_content: list, file_id: str,
                         parent_size: int = 1500, parent_overlap: int = 0,
                         child_size: int = 300, child_overlap: int = 50):

          parent_splitter = RecursiveCharacterTextSplitter(
              chunk_size=parent_size,
              chunk_overlap=parent_overlap,
              length_function=len,
          )
          child_splitter = RecursiveCharacterTextSplitter(
              chunk_size=child_size,
              chunk_overlap=child_overlap,
              length_function=len,
          )

          texts = [rec.page_content for rec in file_content]
          metadatas = [rec.metadata for rec in file_content]

          # 1) parents
          parents = parent_splitter.create_documents(texts, metadatas=metadatas)

          # 2) children لكل parent
          children = []
          for parent_idx, parent in enumerate(parents):
              parent.metadata["parent_idx"] = parent_idx
              kids = child_splitter.create_documents(
                  [parent.page_content],
                  metadatas=[{**parent.metadata, "parent_idx": parent_idx}],
              )
              children.extend(kids)

          return parents, children
