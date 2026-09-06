from fastapi import FastAPI,APIRouter,Depends
from dotenv import load_dotenv
from helpers.config import get_settings , Settings
#import os
#load_dotenv(".env")

base_router = APIRouter(
   prefix = "/api/v1",
   tags = ["api_v1"]


) #بنعمل تعريف لل ROuters 

@base_router.get("/")
async def welcome(app_settings : Settings = Depends(get_settings)):
    # علشان ال app_settings مش هتشتغل غير لو get_settings شغاله 
   # app_settings = get_settings() 
   
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_version

    return {
        "App_name": app_name, 
        "APP_version" : app_version,
    }