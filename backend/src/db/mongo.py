from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://aamukthasetty2005:PqcAS1cmmtm1uCjR@cluster0.vn74e.mongodb.net/?appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "AgenticAI")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

JD_COLLECTION_NAME = "job_descriptions"
CANDIDATES_COLLECTION_NAME = "candidates"

existing_collections = db.list_collection_names()

if JD_COLLECTION_NAME not in existing_collections:
    db.create_collection(JD_COLLECTION_NAME)
    print(f"Created collection: {JD_COLLECTION_NAME}")

if CANDIDATES_COLLECTION_NAME not in existing_collections:
    db.create_collection(CANDIDATES_COLLECTION_NAME)
    print(f"Created collection: {CANDIDATES_COLLECTION_NAME}")

jd_collection = db[JD_COLLECTION_NAME]
candidates_collection = db[CANDIDATES_COLLECTION_NAME]
