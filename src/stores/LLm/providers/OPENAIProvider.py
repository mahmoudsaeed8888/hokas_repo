from ..LLMInterface import LLMInterface
from ..LLMEnums import OpenAIEnums
import logging
from openai import OpenAI 
class OPENAIProvider(LLMInterface):
    
    def __init__(self,api_key : str , api_url :str =None ,
               default_input_max_characters : int=1000,
               default_generation_max_output_tokens :int= 1000,
               default_generation_temperature : float = 0.1 ): 

        
        self.api_key = api_key
        self.api_url = api_url

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None 

        self.embedding_model_id = None 
        self.embedding_size = None 

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )
        
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self,model_id :str):
       self.generation_model_id = model_id 
     
    def set_embedding_model(self, model_id :str , embedding_size :int ):
         self.embedding_model_id = model_id 
         self.embedding_size = embedding_size 

    def construct_prompt(self , prompt : str , role : str):
        return{
            "role":role,
            "content": self.process_text(prompt) 
        }


    def generate_text(self , prompt :str , chat_history: list = None ,max_output_token : int =None , temperature : float =None):
        
        if chat_history is None:
            chat_history = []

        if not self.client :
            self.logger.error(" OPENAI client not set ")
            return None 

        if not self.generation_model_id:
            self.logger.error("Generation model not set")
            return None 
        
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        chat_history.append(
            self.construct_prompt(prompt = prompt ,role = OPENAIEnums.USER.value )
        )
        
        
        response = self.client.responses.create(
             model=self.generation_model_id,
             input=chat_history,
             max_output_tokens=max_output_tokens,
             temperature=temperature
    )

        if not response or not response.output_text:
            self.logger.error("Error while generating text with OPENAI")
            return None
    
        return response.output_text
        

    def embedding_text(self , text : str , document_type : str = None):
        if not self.client :
            self.logger.error(" OPENAI client not set ")
            return None 
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model not set")
            return None 
        
        if len(text) > self.default_max_input_characters:
            self.logger.error("Text length exceeds the maximum size allowed for embedding")
            return None

        response = self.client.embeddings.create(
            model = self.embedding_model_id,  
            input = text                     
        )
        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Error while embedding text with OPENAI")
            return None 
        return response.data[0].embedding
    
    def process_text(self ,text :str):
        return text[:self.default_max_input_characters].strip()


        