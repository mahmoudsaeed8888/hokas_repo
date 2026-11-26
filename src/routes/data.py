from fastapi import FastAPI, APIRouter, Depends, UploadFile, File, status, Request
from fastapi.responses import JSONResponse
from helpers import get_settings, Settings
import os
import aiofiles
from typing import List
from controllers import Data_Controller, ProjectController, process_controller
from models import ResponseSignal
from models.ProjectDataModel import ProjectModel
from models.ChunkDataModel import ChunkModel
from models.AssetsDataModel import AssetsModel

from models.db_schemes import DataChunk
from models.db_schemes import Asset
from models import Assets_Enums
import logging

from .schemes import processRequest

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: int, files: List[UploadFile],
                      app_settings: Settings = Depends(get_settings)):

    Project_Model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    project = await Project_Model.get_project_or_create_one(project_id=project_id)

    Assets_model = await AssetsModel.create_instance(
        db_client=request.app.db_client
    )

    data_controller = Data_Controller()

    uploaded_files = []
    failed_files = []

    for file in files:

        # 1) validate
        is_valid, message = data_controller.validate_upload_File(file=file)
        if not is_valid:
            failed_files.append({
                "file_name": file.filename,
                "signal": message
            })
            continue

        # 2) generate path + id
        file_path, file_id = data_controller.generate_unique_filepath(
            orig_file_name=file.filename,
            project_id=project_id
        )

        # 3) save on disk
        try:
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                    await f.write(chunk)
        except Exception as e:
            logger.error(f"Error while uploading file {file.filename}: {e}")
            failed_files.append({
                "file_name": file.filename,
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            })
            continue

        # 4) store the asset
        Asset_Resources = Asset(
            asset_project_id=project.project_id,
            asset_type=Assets_Enums.FILE.value,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path)
        )
        await Assets_model.create_asset(asset=Asset_Resources)

        uploaded_files.append({
            "file_name": file.filename,
            "file_id": file_id
        })

    return JSONResponse(
        status_code=status.HTTP_200_OK if uploaded_files else status.HTTP_400_BAD_REQUEST,
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value if uploaded_files
                      else ResponseSignal.FILE_UPLOAD_FAILED.value,
            "uploaded": uploaded_files,
            "failed": failed_files
        }
    )

@data_router.post("/process/{project_id}")
async def process_endpoint(request: Request, project_id: int, process_request: processRequest):

    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    Project_Model = await ProjectModel.create_instance( db_client=request.app.db_client )

    chunk_Model = await ChunkModel.create_instance( db_client=request.app.db_client  )
    
    Assets_model = await AssetsModel.create_instance( db_client=request.app.db_client  )

    project = await Project_Model.get_project_or_create_one(project_id=project_id)

    if do_reset == 1:
       await chunk_Model.delete_chunks_by_project_id(project_id=project.project_id)
  
    # Determine which files to process
    project_file_ids = {}

    if process_request.file_id:
        asset_record = await Assets_model.get_one_assets(
            asset_project_id = project.project_id,
            asset_name = process_request.file_id
        )
        if asset_record is None :
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ResponseSignal.NO_FILE_ID_ERROR.value
            )

        project_file_ids = {
            asset_record.asset_id : asset_record.asset_name
        }

    else:


        project_mdels = await Assets_model.get_all_project_assets(
            asset_project_id=project.project_id,
            asset_type=Assets_Enums.FILE.value
        )

        project_file_ids = {
           record.asset_id : record.asset_name
            for record in project_mdels
        }

    if len(project_file_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ResponseSignal.NO_FILES_ERROR.value
        )

    processController = process_controller(project_id=project_id)
    no_records = 0
    no_files = 0

    for id,file_id in project_file_ids.items():

        file_content = processController.get_file_content(file_id=file_id)

        if file_content is None:
            logger.error(f"Error while processing file: {file_id}")
            continue

        file_chunks = processController.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )

        if file_chunks is None or len(file_chunks) == 0:
            logger.error(f"Empty chunks for file: {file_id}")
            continue

        file_chunks_record = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i + 1,
                chunk_project_id=project.project_id,
                chunk_asset_id=id
            )
            for i, chunk in enumerate(file_chunks)
        ]

        no_records += await chunk_Model.insert_many_chunks(chunks=file_chunks_record)
        no_files += 1

    # single response after processing ALL files, not just the first one
    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files
        }
    )