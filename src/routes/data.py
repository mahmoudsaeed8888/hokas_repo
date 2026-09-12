from fastapi import FastAPI, APIRouter, Depends, UploadFile, File,status , Request 
from fastapi.responses import JSONResponse
from helpers import get_settings, Settings
import os
import aiofiles
from controllers import Data_Controller, ProjectController , process_controller
from models import ResponseSignal
from models.ProjectDataModel import ProjectModel
from models .ChunkDataModel import ChunkModel
from models . db_schemes import DataChunk
import logging

from .schemes import processRequest

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile ,
                       app_settings: Settings = Depends(get_settings)):


    Project_Data_Model = await ProjectModel.create_instance(
        db_client = request.app.db_client
    )
    project = await Project_Data_Model.get_project_or_create_one(project_id = project_id)


    data_controller = Data_Controller()
    is_valid, message = data_controller.validate_upload_File(file=file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=message
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)

    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name = file.filename,
        project_id = project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file : {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ResponseSignal.FILE_UPLOAD_FAILED.value
        )

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id ,
            # "project_id": str(project.id) 
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request , project_id: str, process_request: processRequest):

    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset
    
    Project_Data_Model = await ProjectModel.create_instance(
        db_client = request.app.db_client
    )

    chunk_Data_Model = await ChunkModel.create_instance(
        db_client = request.app.db_client
    )
    project = await Project_Data_Model.get_project_or_create_one(project_id = project_id)
    if do_reset==1:
       await chunk_Data_Model.delete_chunks_by_project_id(
           project_id=project.id
       )
 


    processController= process_controller(project_id = project_id)
    
    file_extension = processController.get_file_extension(file_id = file_id)
    
    file_content =processController.get_file_content(file_id = file_id)
   

    file_chunks = processController.process_file_content(
      file_content = file_content, 
      file_id = file_id , 
      chunk_size = chunk_size ,
      overlap_size = overlap_size

    )

    if file_chunks is None or len(file_chunks)==0 :
       return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ResponseSignal.PROCCESSING_FAILD.value
    
       )
    #return file_chunks
    file_chunks_record = [
        DataChunk(
            chunk_text = chunk.page_content,
            chunk_metadata = chunk.metadata,
            chunk_order = i+1,
            chunk_project_id = project.id,
        )
        for i,chunk in enumerate(file_chunks)
        ]


    no_records = await chunk_Data_Model.insert_many_chunks(chunks=file_chunks_record)
    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCCESSING_SUCCESS.value,
            "Inserted chunks ": no_records ,
        }
    )
    





    