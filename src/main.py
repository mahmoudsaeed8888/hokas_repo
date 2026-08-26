from fastapi import FastAPI
from routes import data
#from dotenv import load_dotenv
# load_dotenv(".env") # هتروح على .env وتخزن القيم اللي موجوده فيه عالسيستم 

from routes import base

app = FastAPI()
#app.include_router(base.base_router)

app.include_router(data.data_router)
