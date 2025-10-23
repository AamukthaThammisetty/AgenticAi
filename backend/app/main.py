# app/main.py
from fastapi import FastAPI
from app.routes import jobs  # adjust if your filename is different

app = FastAPI()

app.include_router(jobs.router)
