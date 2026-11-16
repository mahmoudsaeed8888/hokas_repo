from fastapi import FastAPI, APIRouter, status, Request
from fastapi.responses import JSONResponse
import logging
from .schemes import PushRequest, SearchRequest
from models import ProjectModel, ChunkModel
from controllers import nlp_controller
from models.enums import ResponseSignal

logger = logging.getLogger("uvicorn.error")

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"]
)


@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: str, push_request: PushRequest):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value},
        )

    controller = nlp_controller(
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        vectordb_client=request.app.vectordb_client,
        template_parser = request.app.template_parser,
    )

    page_no = 1
    inserted_items_count = 0
    idx = 0
    is_first_page = True

    while True:
        page_chunks = await chunk_model.get_project_chunks(
            project_id=project.id,
            page_no=page_no,
        )

        if not page_chunks:
            break

        page_no += 1

        chunk_ids = list(range(idx, idx + len(page_chunks)))
        idx += len(page_chunks)

        # الـ reset يتعمل مرة واحدة بس في أول صفحة
        is_inserted = controller.index_into_vector_db(
            project=project,
            chunks=page_chunks,
            chunk_ids=chunk_ids,
            do_reset=(push_request.do_reset and is_first_page),
        )
        is_first_page = False

        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"Signal": ResponseSignal.INSER_INTO_VECTORDB_ERROR.value},
            )

        inserted_items_count += len(page_chunks)

    return JSONResponse(
        content={
            "Signal": ResponseSignal.INSER_INTO_VECTORDB_SUCCESS.value,
            "Inserted_items_count": inserted_items_count,
        }
    )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: str):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    controller = nlp_controller(
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        vectordb_client=request.app.vectordb_client,
        template_parser = request.app.template_parser,
    )

    collection_info = controller.get_vector_collection_info(project=project)

    return JSONResponse(
        content={
            "Signal": ResponseSignal.VECTOR_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info,
        }
    )


@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: str, search_request: SearchRequest):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    controller = nlp_controller(
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        vectordb_client=request.app.vectordb_client,
        template_parser=request.app.template_parser
    )

    results = controller.search_vector_db_collection(
        project=project,
        text=search_request.text,
        limit=search_request.limit,
    )

    if not results:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value},
        )

    return JSONResponse(
        content={
            "Signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
            "Results": [result.dict() for result in results]
        }
    )

@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: str, search_request: SearchRequest):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    controller = nlp_controller(
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        vectordb_client=request.app.vectordb_client,
        template_parser = request.app.template_parser,
        
    )


    answer, full_prompt, chat_history = controller.answer_rag_question(
        project=project,
        query=search_request.text,
        limit=search_request.limit,
    )

    if not answer:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.RAG_ANSWER_ERROR.value
                }
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }
    )