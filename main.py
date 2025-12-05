import os
import shutil
from typing import List
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.responses import FileResponse
# Import services
from app.services.crawler import CrawlerService
from app.services.ingestor import IngestionService
from app.services.rag_engine import RAGService
from app.config import settings

app = FastAPI(title="CampusMate AI")

# Mounts
app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files") 
from fastapi.staticfiles import StaticFiles

# serve uploaded PDFs at /files/<filename>
app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Services
crawler = CrawlerService()
ingestor = IngestionService()
rag = RAGService()

# --- SECURITY GUARD ---
async def verify_admin(x_admin_password: str = Header(...)):
    """
    Dependency: Checks if the request header contains the correct password.
    """
    if x_admin_password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid Admin Password")
    return True

# --- Models ---
class ChatRequest(BaseModel):
    query: str
    history: List[str] = []

class CrawlRequest(BaseModel):
    url: str

# --- Public Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return rag.get_answer(request.query, request.history)

# --- PROTECTED Admin Routes ---
# Notice: dependencies=[Depends(verify_admin)] locks these routes

@app.post("/api/admin/verify", dependencies=[Depends(verify_admin)])
async def check_password():
    """Simple endpoint to test if password is correct from UI"""
    return {"status": "ok"}

@app.post("/api/admin/crawl", dependencies=[Depends(verify_admin)])
async def trigger_crawl(req: CrawlRequest):
    try:
        results = crawler.crawl(req.url)
        return {"status": "success", "pages_crawled": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/upload", dependencies=[Depends(verify_admin)])
async def upload_pdf(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename, "status": "uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/retrain", dependencies=[Depends(verify_admin)])
async def retrain_knowledge_base():
    try:
        ingestor.build_vector_store()
        rag.reload_db() 
        return {"status": "success", "message": "Knowledge base updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/{file_path:path}")
async def serve_pdf(file_path: str):
    full_path = os.path.join(settings.BASE_DIR, file_path)
    if not os.path.exists(full_path):
        return {"error": "File not found"}
    return FileResponse(full_path, media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)