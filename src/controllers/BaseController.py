from helpers import get_settings , Settings
import os 
import random ,string

class BaseController: 
    def __init__(self):
        self.app_settings = get_settings() # app_version, app_key

        # __file__ = "/home/user/hokas_repo/src/controllers/base_controller.py"
        self.base_dir = os.path.dirname(os.path.dirname(__file__)) # base_dir= home/user/hokas_repo/src

        self.file_dir =os.path.join(self.base_dir,"assets/files") # file_dir = "src/assets/files" 
        #إحنا مكناش عايزين نكتب مسار مجلد assets/files يدوي وثابت (Hardcoded)، زي كده:
        #المكان اللي هيتخزن فيه الفايل
   
        self.database_dir = os.path.join(self.base_dir, "assets/database"  )
    def generate_random_string(self, length: int=12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    
    def get_database_path(self, db_name: str):
   
           database_path = os.path.join(
               self.database_dir, db_name
           )
   
           if not os.path.exists(database_path):
               os.makedirs(database_path)
   
           return database_path