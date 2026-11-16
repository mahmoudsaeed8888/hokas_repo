from enum import Enum 

class ResponseSignal(Enum):
     
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    PROCCESSING_SUCCESS = "Process Success"
    PROCCESSING_FAILD = "Process Faild"
    NO_FILES_ERROR = "No_found_files"
    NO_FILE_ID_ERROR = "No_found_file_id"
    PROJECT_NOT_FOUND_ERROR = "Project_not_found"
    INSER_INTO_VECTORDB_ERROR = "Error while insert into vectordb"
    INSER_INTO_VECTORDB_SUCCESS = "Successful insert inot vectordb"
    VECTOR_COLLECTION_RETRIEVED = "Vector_collection_retrieved"
    VECTORDB_SEARCH_ERROR = "Vecotrdb_search_error"
    VECTORDB_SEARCH_SUCCESS = "Vecotrdb_search_success"
    RAG_ANSWER_ERROR = "rag_answer_error"
    RAG_ANSWER_SUCCESS = "rag_answer_success"
