from fastapi import FastAPI
from app.routes import people  # make sure folder structure is correct

app = FastAPI()

app.include_router(people.router)
