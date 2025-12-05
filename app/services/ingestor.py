# app/services/ingestor.py
import os
import re
import json
from typing import List, Any

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

try:
    from langchain.schema import Document
except:
    try:
        from langchain.docstore.document import Document
    except:
        Document = Any

from app.config import settings

FILEMAP_PATH = os.path.join(settings.BASE_DIR, "data", "file_maps.json")

class IngestionService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text or '')
        return text.strip()

    def extract_pdf_text(self, pdf_path: str) -> str:
        text = ""
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            print(f"[PDF ERROR] {pdf_path}: {e}")
        return self.clean_text(text)

    def update_filemap(self, original_name, saved_path, extracted_text, file_type="pdf"):
        if os.path.exists(FILEMAP_PATH):
            with open(FILEMAP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        # Append new
        data.append({
            "original_name": original_name,
            "saved_path": saved_path.replace("\\","/"),
            "display_name": original_name,
            "type": file_type,
            "text": extracted_text[:5000]
        })

        with open(FILEMAP_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_and_chunk(self) -> List[Document]:
        docs = []
        # directories to scan
        pdf_dirs = [settings.RAW_DATA_DIR, settings.UPLOAD_DIR]

        for pdf_dir in pdf_dirs:
            if not os.path.exists(pdf_dir):
                continue
            for root, _, files in os.walk(pdf_dir):
                for file in files:
                    if not file.lower().endswith((".pdf", ".txt")):
                        continue
                    file_path = os.path.join(root, file)
                    meta = {"source": file}
                    content = ""

                    if file.lower().endswith(".txt"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = self.clean_text(f.read())
                        meta["type"] = "text"
                        rel_path = os.path.relpath(file_path, settings.BASE_DIR).replace("\\","/")
                        # update filemap for txt too if desired
                        self.update_filemap(file, rel_path, content, file_type="text")

                    else:  # pdf
                        content = self.extract_pdf_text(file_path)
                        meta["type"] = "pdf"
                        rel_path = os.path.relpath(file_path, settings.BASE_DIR).replace("\\","/")
                        self.update_filemap(file, rel_path, content, file_type="pdf")

                    if not content:
                        # skip indexing empty text (but still filemap entry exists with empty text)
                        continue

                    chunks = self.text_splitter.create_documents([content], metadatas=[meta])
                    docs.extend(chunks)

        return docs

    def build_vector_store(self):
        print("[INGEST] Loading & chunking...")
        docs = self.load_and_chunk()
        if not docs:
            print("[INGEST] No docs found for indexing.")
            return
        print(f"[INGEST] Creating embeddings for {len(docs)} chunks...")
        vector_store = FAISS.from_documents(docs, self.embeddings)
        vector_store.save_local(settings.VECTOR_DB_DIR)
        print("[INGEST] Vector store saved.")
        # debug
        debug_path = os.path.join(settings.CLEAN_DATA_DIR, "chunks.json")
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump([{"content": d.page_content, "meta": d.metadata} for d in docs], f, indent=2, ensure_ascii=False)
