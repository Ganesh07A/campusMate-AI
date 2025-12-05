import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Sahayak AI"
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
    CLEAN_DATA_DIR = os.path.join(BASE_DIR, "data", "clean")
    VECTOR_DB_DIR = os.path.join(BASE_DIR, "data", "vector_store")
    UPLOAD_DIR = os.path.join(BASE_DIR, "data", "raw", "uploads")

    # Model Config
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    # --- THE GOLDEN CONTEXT (Cheat Sheet) ---
    # These facts are ALWAYS fed to the AI, ensuring it knows the basics.
    COLLEGE_PROFILE = """
    [CRITICAL KNOWLEDGE - USE THIS IF NOT FOUND IN DOCUMENTS]
    Name of Institute: Shreeyash College of Engineering & Technology (SYCET), chhatrapati Sambhajinagar.
    Principal: Dr. B.M. Patil
    Academic Dean: Dr. P.M. Ardhapurkar.
    President/Chairman: Mr. Baswaraj Mangrule.
    Departments/Branches Offered: 
    - Computer Science & Engineering (CSE)
    - Artificial Intelligence & Machine Learning (AI & ML)
    - Civil Engineering
    - Mechanical Engineering
    - Electrical Engineering
    - Electronics & Telecommunication (E&TC)
    - 5G Technology
    - VLSI Design
    - Data Science (DS)
    Address: Gut No. 258(P), Satara Parisar, Beed By Pass Road, Near SRPF Camp, Chhatrapati Sambhajinagar - 431010.
    Contact: 0240-6608701 / 8702.
    Website: www.sycet.org / www.syp.ac.in
    """

settings = Settings()

# Ensure dirs exist
for path in [settings.RAW_DATA_DIR, settings.CLEAN_DATA_DIR, settings.VECTOR_DB_DIR, settings.UPLOAD_DIR]:
    os.makedirs(path, exist_ok=True)