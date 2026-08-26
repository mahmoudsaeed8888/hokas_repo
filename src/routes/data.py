from fastapi import FastAPI,APIRouter,Depends,UploadFile,status
from fastapi.responses import JSONResponse
from helpers import get_settings , Settings
import os
import aiofiles
from controllers import Data_Controller,ProjectController
from models import ResponseSignal
import logging
logger = logging.get("Uvicorn.errors")
data_router = APIRouter(
   prefix = "/api/v1/data",
   tags = ["api_v1","data"]

)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id : str , file: UploadFile ,
                      app_settings : Settings = Depends(get_settings)):
    
      data_Controller=Data_Controller()
      is_valid, message = data_Controller.validate_upload_File(file = file)

      if not is_valid :
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = message
        )


      project_dir_path = ProjectController().get_project_pass(project_id = project_id)

      file_path = data_Controller.generate_unique_filename(orig_file_name=file.filename , project_id = project_id)
      
    try :
      async with aiofiles.open(file_path,"wb")as f :
        while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
              await f.write(chunk)
    except Exception as e:
              
              logger.error(f"Error while upoloading file : {e}")

              return JSONResponse(
                 status_code = status.HTTP_400_BAD_REQUEST,
                 content = ResponseSignal.FILE_UPLOAD_FAILED.value
        )

    return JSONResponse(
      content = ResponseSignal.FILE_UPLOAD_SUCCESS.value
    )
