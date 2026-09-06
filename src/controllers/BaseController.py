from helpers import get_settings , Settings
import os 
import random ,string
class BaseController: 
    def __init__(self):
        self.app_settings = get_settings() # app_version, app_key
        self.base_dir = os.path.dirname(os.path.dirname(__file__)) # base_dir= src 
        self.file_dir =os.path.join(self.base_dir,"assets/files") # file_dir = "src/assets/files" 
        #إحنا مكناش عايزين نكتب مسار مجلد assets/files يدوي وثابت (Hardcoded)، زي كده:
        #المكان اللي هيتخزن فيه الفايل
   
    def generate_random_string(self,length:int=12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
