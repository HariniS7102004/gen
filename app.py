from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header, Depends, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from generation.cover_letter_generator import CoverLetterGenerator
from generation.cv_generator import CVGenerator
from openai.prompt import build_cover_letter_prompt, build_resume_prompt
from openai.openai_service import generate_text
from openai.post_process import filter_skills
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from generation.resume_data_extraction import ResumeExtracter
import tempfile
import threading
import uuid
import os
import time
import json
import logging

load_dotenv()
print("CPU Count:", os.cpu_count())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume and Cover Letter Generator")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_TOKEN = os.getenv("SECRET_KEY")

executor = ThreadPoolExecutor(max_workers=15)
request_queue = Queue()

# ---------------------- Auth Dependency ----------------------

def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ")[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------------- File Cleanup Utilities ----------------------

def cleanup_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Cleaned up file: {filepath}")
    except Exception as e:
        print(f"Error cleaning up file {filepath}: {str(e)}")

def delayed_cleanup(filepath, delay=2):
    def cleanup_task():
        time.sleep(delay)
        cleanup_file(filepath)
    thread = threading.Thread(target=cleanup_task, daemon=True)
    thread.start()

# ---------------------- Queue Worker ----------------------

def worker():
    while True:
        func, args = request_queue.get()
        try:
            func(*args)
        finally:
            request_queue.task_done()

threading.Thread(target=worker, daemon=True).start()

# ---------------------- API Models ----------------------

class CoverLetterRequest(BaseModel):
    user_details: dict
    job_details: dict

class ResumeRequest(BaseModel):
    user_details: dict
    job_details: dict

# ---------------------- Routes ----------------------

@app.get("/")
def home():
    return {"message": "Resume and Cover Letter Generator (Text Mode) is running!"}

@app.post("/m2/generate/coverletter")
async def generate_coverletter(
    request: Request,
    background_tasks: BackgroundTasks,
    _: None = Depends(verify_token)
):
    data = await request.json()
    filename = f"cover_letter_{uuid.uuid4().hex[:8]}.pdf"
    prompt_content = build_cover_letter_prompt(data)
    result = {}

    def task():
        try:
            result["content"] = generate_text(prompt_content, OPENAI_API_KEY)
        except Exception as e:
            result["error"] = str(e)

    request_queue.put((task, []))
    request_queue.join()

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    paragraphs = result["content"].split("\n\n")
    data["paragraphs"] = paragraphs

    generator = CoverLetterGenerator()
    pdf_path = generator.generate_cover_letter(data, output_filename=filename)

    background_tasks.add_task(delayed_cleanup, pdf_path)
    return FileResponse(pdf_path, filename="cover_letter.pdf", media_type="application/pdf")

@app.post("/m2/generate/resume")
async def generate_resume(
    request: Request,
    background_tasks: BackgroundTasks,
    _: None = Depends(verify_token)
):
    data = await request.json()
    filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
    prompt_content = build_resume_prompt(data)
    result = {}

    def task():
        try:
            result["content"] = generate_text(prompt_content, OPENAI_API_KEY)
        except Exception as e:
            result["error"] = str(e)

    request_queue.put((task, []))
    request_queue.join()

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    try:
        parsed_content = json.loads(result["content"])
    except json.JSONDecodeError:
        return JSONResponse(status_code=500, content={
            "error": "Failed to parse response as JSON",
            "raw": result["content"]
        })

    # Filter skills from parsed_content
    filtered_data = filter_skills(parsed_content, data['user_details'], data['job_description'])

    data["content"] = filtered_data

    generator = CVGenerator()
    pdf_path = generator.generate_cv(data, filename=filename)

    background_tasks.add_task(delayed_cleanup, pdf_path)
    return FileResponse(pdf_path, filename="resume.pdf", media_type="application/pdf")

#----------------------new----------------------------

@app.post("/m2/extract-resume")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """
    Parse a resume file and extract structured information
    
    Accepts: PDF, DOCX, TXT files
    Returns: JSON with parsed resume data
    """
    resume_parser = ResumeExtracter()
    if not resume_parser:
        raise HTTPException(status_code=500, detail="Resume parser not initialized")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file_extension}. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (e.g., 10MB limit)
    max_file_size = 10 * 1024 * 1024  # 10MB
    if file.size and file.size > max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size allowed: {max_file_size // (1024*1024)}MB"
        )
    
    try:
        # Create a temporary file to save the uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Read and save the uploaded file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Processing file: {file.filename} (size: {len(content)} bytes)")
        
        # Parse the resume
        result = resume_parser.parse_resume(temp_file_path)
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        # Check if parsing was successful
        if "error" in result:
            raise HTTPException(status_code=422, detail=result["error"])
        
        logger.info(f"Successfully parsed resume: {file.filename}")
        
        return JSONResponse(content={"data": result})
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up temp file if it exists
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass
        
        logger.error(f"Error parsing resume {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing resume: {str(e)}"
        )

@app.exception_handler(413)
async def request_entity_too_large_handler(request, exc):
    """Handle file too large errors"""
    return JSONResponse(
        status_code=413,
        content={
            "success": False,
            "error": "File too large",
            "message": "The uploaded file exceeds the maximum allowed size of 10MB"
        }
    )