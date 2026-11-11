from .VectordbEnums import VectordbEnums
from .providers import QdrantDB
from BaseController import BaseController

class VectordbProviderFactory():
    def __init__(self, config: dict):
        self.config = config
        self.Base_Controller = BaseController()

    def create(self, provider: str):
        if provider == VectordbEnums.QDRANT.value:
         
            return QdrantDB(
                   db_path = self.Base_Controller.get_database_path(db_name =self.config.VECTOR_DATABASE_PATH)
                distance_method = self.confing.VECTOR_DATABASE_DISTANCE_METHOD.value
            )

        return None