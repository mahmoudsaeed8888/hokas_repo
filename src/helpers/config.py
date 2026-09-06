from pydantic_settings import BaseSettings, SettingsConfigDict
 
class Settings(BaseSettings): # settings هيورث كل حاجه من ال base settings 
# BaseSettings : ملف بيساعدنا نقرأ ال .env + validation 
 #بيربط 3 حاجات  vairable name , same vairable name in .env , type 

     # for validation
     APP_NAME:str
     APP_version:str
     OPENAI_API_KEY:str
     FILE_ALLOWED_TYPES: list 
     FILE_MAX_SIZE : int
     FILE_DEFAULT_CHUNK_SIZE :int

     model_config = SettingsConfigDict(env_file=".env")   # دا معناه هيروح يدور ف ملف اسمه .env

def get_settings():
    return Settings()
