from enum import Enum

#class VectorDBEnums(Enum):
#    QDRANT = "QDRANT"

class DistanceMethodEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"
    VECTOR_IB="vector_ip_ops"
    VECTOR_CONSINE="vector_cosine_ops"


class VectorDBEnums(Enum):
    PGVECTOR = "PGVECTOR"
