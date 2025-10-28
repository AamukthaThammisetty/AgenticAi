# app/db.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

client = AsyncIOMotorClient(MONGODB_URI)
db = client["linkedin_ai_db"]  # Your database name
collection = db["resumes"]      # Your collection name
jobs_collection = db["jobs"]
candidates_collection = db["candidates"]

# Optional: Test connection
try:
    client.server_info()
    print("✓ MongoDB connected successfully")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")


async def create_indexes():
    await jobs_collection.create_index("job_id", unique=True)
    await candidates_collection.create_index([("job_id", 1), ("github_username", 1)], unique=True)
    await candidates_collection.create_index([("job_id", 1), ("score", -1)])
