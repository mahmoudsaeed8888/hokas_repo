from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
import logging
from schemes import PushRequest
from models import ProjectModel , ChunkModel
from controllers import nlp_controller
from models.enums import ResponseSignal

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"]
)

@nlp_router.post("/index/push/{project_id}")
async def index_poject(request : Request, project_id :str , push_Request :PushRequest):

    Project_Model = await ProjectModel.create_instance(  db_client=request.app.db_client )
    chunk_Model = await ChunkModel.create_instance( db_client=request.app.db_client   )

    project = await Project_Model.get_project_or_create_one(project_id=project_id)


    if not project :
         return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
                )
    
    nlp_controller= nlp_controller(
        request.app.generation_client , 
        request.app.embedding_client , 
        request.app.vectordb_client
        )


    records = True 
    page_no =1 
    Inserted_items_count = 0

    while records :  
      Page_chunks = chunk_Model.get_project_chunks(project_id=project.id, page_no=page_no)
      if len(records):
          page_no+=1

      if not Page_chunks or len(records) == 0 :
          records = False 
          break  

      is_inserted = nlp_controller.index_into_vector_db(
          project=project, 
          chunks = Page_chunks, 
          do_reset =push_Request.do_reset)
        

      if not is_inserted:
            return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=ResponseSignal.INSER_INTO_VECTORDB_ERROR.value
                )
      
      Inserted_items_count+=len(Page_chunks)

    return JSONResponse(
        "Signal": ResponseSignal.INSER_INTO_VECTORDB_SUCCESS.value,
        "Inserted_items_count" : Inserted_items_count

                )






    


