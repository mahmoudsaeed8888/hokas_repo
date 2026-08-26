
# from controllers.BaseController import BaseController # دي غلط علشان ال base, data جوا نفس الفولدر ف مش هيعرف يقرأ controllers
from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSignal
from .ProjectController import ProjectController
import re
import os 
class Data_Controller(BaseController):
    def __init__(self):  # self = DataController
        super().__init__() # super = Base , معناه ان السوبر هينادي على ال base , وال base هينادي على ال init 
        self.size_scale = 1048576

    def validate_upload_File(self,file : UploadFile) :
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES :
            return False , ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value
        if file.size> self.app_settings.FILE_MAX_SIZE * self.size_scale :
            return False , ResponseSignal.file_size_exceeded.value

        return True , ResponseSignal.FILE_UPLOAD_SUCCESS.value

    def generate_unique_filename(self,orig_file_name :str ,project_id :str ):

        random_key= self.generate_random_string()
        
        project_path = ProjectController().get_project_pass(project_id = project_id)
        
        cleaned_file_name= self.get_clean_file_name(orig_file_name=orig_file_name )
        
        new_file_path = os.path.join(project_path , random_key + "_" + cleaned_file_name)

        while os.path.exists("new_file_path"):
            random_key= self.generate_random_string()
            new_file_path = os.path.join(project_path , random_key + "_" + cleaned_file_name)
        
        return new_file_path



    def get_clean_file_name(self,orig_file_name : str) :
        cleaned_file_name = re.sub(f'[^\w.]','',orig_file_name.strip())
        cleaned_file_name = cleaned_file_name.replace(" ","_")
        return cleaned_file_name

        