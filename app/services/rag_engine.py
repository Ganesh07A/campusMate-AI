# app/services/rag_engine.py
import os
import json
import math
import traceback
import google.generativeai as genai

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import settings

# configure Gemini safely (won't crash if key missing)
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
except Exception:
    pass


class RAGService:
    def __init__(self):
        # embeddings used by FAISS and by PDF matching
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.vector_store = None
        self.load_db()

        # Gemini model wrapper
        try:
            self.model = genai.GenerativeModel("gemini-2.0-flash")
        except Exception:
            self.model = None

        # file map (list format produced by ingestion)
        self.map_path = os.path.join(settings.BASE_DIR, "data", "file_maps.json")
        self.file_entries = []
        self.load_filemap()

        # cache of embeddings for files {saved_path: {text_emb: [...], name_emb: [...]} }
        self._file_emb_cache = {}

        # keywords to detect file intent
        self.pdf_keywords = [
            "pdf", "document", "file", "syllabus", "hod", "hod list",
            "prospectus", "brochure", "seat matrix", "vacant", "admission",
            "fees", "fee structure", "curriculum", "syllabus", "scheme"
        ]

        # matching threshold (tune if needed)
        self.match_threshold = 0.22

    # -------------------------
    # Utilities
    # -------------------------
    def load_db(self):
        try:
            self.vector_store = FAISS.load_local(
                settings.VECTOR_DB_DIR,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception:
            self.vector_store = None

    def load_filemap(self):
        if os.path.exists(self.map_path):
            try:
                with open(self.map_path, "r", encoding="utf-8") as f:
                    self.file_entries = json.load(f)
            except Exception:
                self.file_entries = []
        else:
            self.file_entries = []

    def reload_db(self):
        self.load_db()
        self.load_filemap()
        self._file_emb_cache = {}

    def _cosine(self, a, b):
        try:
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            if na == 0 or nb == 0:
                return 0.0
            return dot / (na * nb)
        except Exception:
            return 0.0

    def _embed_text(self, text):
        """
        Use HuggingFaceEmbeddings wrapper safely. Returns list/None.
        """
        if not text:
            return None
        try:
            if hasattr(self.embeddings, "embed_query"):
                emb = self.embeddings.embed_query(text)
                return list(emb)
            if hasattr(self.embeddings, "embed_documents"):
                # embed_documents expects a list -> returns list of vectors
                emb_list = self.embeddings.embed_documents([text])
                if emb_list and len(emb_list) > 0:
                    return list(emb_list[0])
            # fallback: try generic call
            emb = self.embeddings.embed([text])
            if emb and len(emb) > 0:
                return list(emb[0])
        except Exception:
            return None

    def _prepare_file_embedding(self, entry):
        """
        Compute and cache embeddings for file name and file text snippet.
        entry: dict with saved_path, original_name/display_name, text
        """
        key = entry.get("saved_path") or entry.get("original_name")
        if not key:
            return

        if key in self._file_emb_cache:
            return

        cache = {"name_emb": None, "text_emb": None}
        # name/display embedding
        name = entry.get("display_name") or entry.get("original_name") or ""
        try:
            name_emb = self._embed_text(name)
            cache["name_emb"] = name_emb
        except Exception:
            cache["name_emb"] = None

        # text snippet embedding for speed (first N chars)
        snippet = (entry.get("text") or "")[:2000]
        try:
            text_emb = self._embed_text(snippet) if snippet.strip() else None
            cache["text_emb"] = text_emb
        except Exception:
            cache["text_emb"] = None

        self._file_emb_cache[key] = cache

    # -------------------------
    # PDF intent detection
    # -------------------------
    def is_pdf_query(self, query: str) -> bool:
        q = (query or "").lower()
        return any(k in q for k in self.pdf_keywords)

    # -------------------------
    # Find best PDF (one)
    # -------------------------
    def find_best_pdf(self, query: str):
        """
        Return the best matching file entry (or None).
        Scoring: semantic similarity between query and file text (primary),
                 plus filename lexical boost.
        """
        if not self.file_entries:
            return None

        # embed query
        q_emb = self._embed_text(query)

        best = None
        best_score = -1.0

        q_lower = (query or "").lower()
        q_tokens = set(q_lower.split())

        for entry in self.file_entries:

            # --- Filter: Only allow PDF files ---
            saved = entry.get("saved_path") or entry.get("original_name") or ""
            if not saved.lower().endswith(".pdf"):
                continue
            
            # prepare embeddings lazily
            self._prepare_file_embedding(entry)
            key = entry.get("saved_path") or entry.get("original_name")

            # semantic score (text)
            sem_score = 0.0
            cache = self._file_emb_cache.get(key, {})
            if q_emb is not None and cache.get("text_emb"):
                sem_score = self._cosine(q_emb, cache["text_emb"])  # between 0..1
            # fallback: if no embeddings, try lexical containment in text
            else:
                text_lower = (entry.get("text") or "").lower()
                if q_lower in text_lower:
                    sem_score = 0.45

            # name-based boost (small)
            name_lower = (entry.get("display_name") or entry.get("original_name") or "").lower()
            name_score = 0.0
            # exact token matches give small boost
            token_matches = sum(1 for t in q_tokens if t and t in name_lower)
            name_score = min(0.6, token_matches * 0.12)

            # combined (weights favor semantic text)
            final_score = (0.75 * sem_score) + (0.25 * name_score)

            # slight heuristic: if filename contains readable words (not UUID), increase weight
            if len(name_lower) > 0 and any(c.isalpha() for c in name_lower) and not all(ch in "0123456789-_. " for ch in name_lower):
                final_score += 0.02

            if final_score > best_score:
                best_score = final_score
                best = entry

        # threshold gate
        if best_score >= self.match_threshold:
            return best
        return None

    # -------------------------
    # LLM call helper (safe)
    # -------------------------
    def _call_llm(self, prompt: str) -> str:
        if not self.model:
            raise RuntimeError("LLM not configured")

        try:
            # try generate_content
            resp = self.model.generate_content(prompt)
            # try common fields
            if hasattr(resp, "text") and resp.text:
                return resp.text
            if hasattr(resp, "candidates") and resp.candidates:
                try:
                    return resp.candidates[0].content.parts[0].text
                except Exception:
                    return str(resp.candidates[0])
            # fallback
            return str(resp)
        except Exception as e:
            # try generate_text as fallback
            try:
                resp = self.model.generate_text(prompt)
                if hasattr(resp, "text"):
                    return resp.text
                return str(resp)
            except Exception:
                # bubble up a simplified error
                raise RuntimeError(f"LLM call failed: {e}\n{traceback.format_exc()}")

    # -------------------------
    # Main: get_answer
    # -------------------------
    def get_answer(self, query: str, history: list = []):
        query = (query or "").strip()
        if not query:
            return {"answer": "Please ask something.", "files": [], "sources": []}

        # 1) If user asked for a file, try to find best PDF
        try:
            if self.is_pdf_query(query):
                best = self.find_best_pdf(query)
                if best:
                    # build URL - we will serve via static mount /files -> settings.UPLOAD_DIR
                    saved = best.get("saved_path") or best.get("original_name")
                    # normalize path to filename only for static mount
                    filename = os.path.basename(saved)
                    url = f"/files/{filename}"

                    file_obj = {"name": best.get("display_name") or filename, "url": url, "type": best.get("type", "pdf")}
                    # short informative answer
                    answer_text = f"I found a document that matches your request: {file_obj['name']}. See the PDF card below."
                    return {"answer": answer_text, "files": [file_obj], "sources": []}
        except Exception:
            # if PDF matching fails unexpectedly, continue to normal RAG flow
            pass

        # 2) Standard RAG flow (vector retrieval + LLM)
        context_parts = []
        sources = []
        if self.vector_store:
            try:
                docs = self.vector_store.similarity_search_with_score(query, k=4)
            except Exception:
                docs = []

            for doc, score in docs:
                # include all retrieved; optionally filter by score
                context_parts.append(doc.page_content)
                src = doc.metadata.get("source", None)
                if src:
                    sources.append(src)

        context_str = "\n\n".join(context_parts)

        # system prompt
        system_prompt = f"""You are Sahayak, a helpful college assistant for Shreeyash College of Engineering & Technology (SYCET).
Rules:
1) Detect user language and reply appropriately.
2) Use the known college facts when needed.
3) Use the retrieved context below to answer precisely and concisely.

College profile:
{settings.COLLEGE_PROFILE}
"""

        full_prompt = f"{system_prompt}\n\nContext:\n{context_str}\n\nChat history:\n{history}\n\nUser: {query}"

        try:
            answer = self._call_llm(full_prompt)
        except Exception:
            answer = "I'm having trouble generating a response right now."

        return {"answer": answer, "files": [], "sources": list(set(sources))}
