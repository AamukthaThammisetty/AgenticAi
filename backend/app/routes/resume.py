# routes/resume.py
from fastapi import File, UploadFile, HTTPException, APIRouter
from app.model import ResumeDetails
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import fitz
import re
from app.db import collection 

load_dotenv()

router = APIRouter(prefix="/resume", tags=["Resume"])

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text and hyperlinks from a PDF file."""
    text = ""
    links = []
    
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                # Extract text
                text += page.get_text("text")
                
                # Extract all hyperlinks
                for link in page.get_links():
                    if 'uri' in link:
                        uri = link['uri']
                        links.append(uri)
                        print(f"Found link: {uri}")
        
        # Append extracted links to text so Gemini can see them
        if links:
            text += "\n\nExtracted Hyperlinks:\n" + "\n".join(links)
        
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting PDF text: {str(e)}")


def extract_details_with_gemini(pdf_text: str) -> dict:
    """Send text to Gemini model and get JSON-formatted resume details."""
    try:
        # Configure model with JSON output
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )
        
        prompt = f"""
Extract information from this resume and return ONLY a valid JSON object with these exact fields:

{{
  "full_name": "person's name",
  "skills": ["list", "of", "skills"],
  "linkedin_url": "linkedin url",
  "github_url": "github url"
}}

CRITICAL RULES:
1. Return ONLY raw JSON - no markdown, no code blocks, no explanation
2. Do NOT wrap in ```json or ``` 
3. If information is missing, use "" for strings or [] for arrays
4. Ensure all JSON is properly formatted with quotes

Resume Text:
{pdf_text[:5000]}

JSON OUTPUT ONLY:"""
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Aggressive cleaning of the response
        # Remove markdown code blocks
        result_text = re.sub(r'^```json\s*', '', result_text, flags=re.IGNORECASE)
        result_text = re.sub(r'^```\s*', '', result_text)
        result_text = re.sub(r'\s*```$', '', result_text)
        
        # Remove any text before the first {
        first_brace = result_text.find('{')
        if first_brace > 0:
            result_text = result_text[first_brace:]
        
        # Remove any text after the last }
        last_brace = result_text.rfind('}')
        if last_brace > 0:
            result_text = result_text[:last_brace + 1]
        
        result_text = result_text.strip()
        
        # Debug logging
        print(f"Cleaned Gemini response: {result_text[:200]}...")
        
        # Parse JSON
        parsed_data = json.loads(result_text)
        return parsed_data
        
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Raw response text: {result_text}")
        
        # Try to extract JSON more aggressively
        try:
            # Find content between first { and last }
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                json_str = result_text[start:end+1]
                parsed_data = json.loads(json_str)
                return parsed_data
        except:
            pass
            
        raise HTTPException(
            status_code=500, 
            detail=f"Invalid JSON from Gemini. Raw response: {result_text[:500]}"
        )
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        # Fallback to empty response
        return {
            "full_name": "",
            "skills": [],
            "linkedin_url": "",
            "github_url": ""
        }


@router.post("/upload")
async def upload_resume(resume: UploadFile = File(...)):
    """
    Upload and process a resume PDF file.
    Extracts name, skills, LinkedIn, and GitHub URLs.
    """
    # Validate file type
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    file_path = None
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, resume.filename)
        with open(file_path, "wb") as f:
            content = await resume.read()
            f.write(content)

        # Extract text from PDF
        pdf_text = extract_text_from_pdf(file_path)
        
        if not pdf_text:
            raise HTTPException(status_code=400, detail="No text found in PDF")

        # Send to Gemini and get structured data
        parsed_data = extract_details_with_gemini(pdf_text)

        # Validate with Pydantic model
        resume_data = ResumeDetails(**parsed_data)

        collection.insert_one(resume_data.dict())

        return {
            "message": "Resume processed successfully",
            "data": resume_data.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    finally:
        # Optional: Clean up uploaded file after processing
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {e}")

