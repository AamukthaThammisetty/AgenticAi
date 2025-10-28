from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import resume,job,github_extract,linkedin

app = FastAPI(title="Resume Parser API")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(resume.router)
app.include_router(job.router)
app.include_router(github_extract.router)
app.include_router(linkedin.router)


@app.get("/")
def root():
    return {"message": "Resume Parser API is running"}
