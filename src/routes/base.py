from fastapi import FastAPI,APIRouter
from dotenv import load_dotenv
import os
load_dotenv(".env")

base_router = APIRouter(
   prefix = "/api/v1",
   tags = ["api_v1"]


) #بنعمل تعريف لل ROuters 

@base_router.get("/")
async def welcome():
    app_name = os.getenv("APP_NAME")
    app_version = os.getenv("APP_version")
    return {
        "App_name": app_name, 
        "APP_version" : app_version,
    }