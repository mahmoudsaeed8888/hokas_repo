from enum import Enum

class LLMEnums(Enum):
    OPENAI = "OPENAI"
    COHERE = "COHERE"
    NILECHAT = "NILECHAT"  
    BGEM3 = "BGEM3"

class OpenAIEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class CoHereEnums(Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"

    DOCUMENT = "search_document"
    QUERY = "search_query"


class DocumentTypeEnum(Enum):
    DOCUMENT = "document"
    QUERY = "query"

class NileChatEnums(Enum):    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class BGEM3Enums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"