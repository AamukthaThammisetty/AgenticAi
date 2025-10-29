from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes import router as api_router

app = FastAPI(
    title="AgenticAI Talent Finder API",
    description="AI-powered GitHub Candidate Matching",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Welcome to AgenticAI Talent Finder API 🚀"}
