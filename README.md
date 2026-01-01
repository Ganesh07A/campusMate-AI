# 🎓 CampusMate AI

**CampusMate AI** (internal persona: **Sahayak**) is an intelligent **Retrieval-Augmented Generation (RAG)** chatbot designed to simplify information access for educational institutions.

Built with **FastAPI** and powered by **Google Gemini 2.0 Flash**, CampusMate AI provides precise, contextual answers by querying a custom knowledge base created from **crawled website data** and **uploaded PDF documents**.

> **Note:**
> The project is currently configured with institution-specific prompts for **Shreeyash College of Engineering & Technology (SYCET)**, but the architecture is **modular and easily adaptable** to any university, college, or organization.

---

## 📑 Table of Contents

* [Why CampusMate AI?](#-why-campusmate-ai)
* [Key Features](#-key-features)
* [Tech Stack](#-tech-stack)
* [Project Structure](#-project-structure)
* [Getting Started](#-getting-started)

  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
  * [Configuration](#configuration)
  * [Run the Server](#run-the-server)
* [API Reference](#-api-reference)
* [How It Works](#-how-it-works)
* [Contributing](#-contributing)
* [License](#-license)

---

## 🚀 Why CampusMate AI?

Navigating institutional information can be overwhelming. Students often struggle to find:

* Admission details
* Fee structures
* Syllabi
* Academic brochures

These are usually buried deep within websites or locked inside static PDFs.

**CampusMate AI solves this by:**

* 🗣️ **Natural Interaction**
  Ask questions in plain language

  > *“What are the fees for CSE?”*

* 📄 **Smart Document Delivery**
  Detects when users are requesting a document (syllabus, fee structure, brochure) and provides a **direct PDF download**, not just a summary.

* 🔄 **Automated Knowledge Base**
  Includes a built-in crawler that scrapes the institution’s website to keep information **up-to-date**.

---

## ✨ Key Features

| Feature                  | Description                                                                 |
| ------------------------ | --------------------------------------------------------------------------- |
| **Generative AI Chat**   | Powered by Gemini 2.0 Flash for accurate, context-aware responses           |
| **RAG Engine**           | Uses FAISS and HuggingFace embeddings to retrieve answers from private data |
| **Intelligent Crawler**  | Admin tool to crawl websites, scrape text, and auto-download PDFs           |
| **PDF Intent Detection** | Recognizes document-based queries and returns direct download links         |
| **Admin Panel**          | Secure routes for uploading files, triggering crawls, and retraining data   |
| **Multimodal Ready**     | Architecture supports future text-to-speech and voice extensions            |

---

## 🛠️ Tech Stack

* **Backend Framework:** FastAPI
* **LLM Integration:** Google Generative AI (Gemini)
* **Orchestration:** LangChain
* **Vector Store:** FAISS (Facebook AI Similarity Search)
* **Embeddings:** HuggingFace (`sentence-transformers`)
* **Web Crawling:** `requests`, `BeautifulSoup4`
* **PDF Processing:** `pypdf`

---

## 📂 Project Structure

```bash
campusmate-ai/
├── app/
│   ├── config.py             # Configuration settings
│   ├── services/
│   │   ├── crawler.py        # Web scraping & PDF downloading logic
│   │   ├── ingestor.py       # Data processing & vector DB builder
│   │   └── rag_engine.py     # RAG logic & LLM interaction
├── data/
│   ├── raw/                  # Scraped text files and uploads
│   ├── vector_store/         # FAISS index files
│   └── file_maps.json        # Metadata mapping for documents
├── static/                   # CSS, JS (voice/PDF logic), images
├── templates/                # Jinja2 HTML templates
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
└── ...
```

---

## ⚡ Getting Started

### Prerequisites

* **Python 3.10+**
* **Google AI Studio API Key** (for Gemini)

---

### Installation

Clone the repository:

```bash
git clone https://github.com/ganesh07a/campusmate-ai.git
cd campusmate-ai
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### Configuration

Update environment variables in `app/config.py` (or via a `.env` file if supported):

* `GOOGLE_API_KEY` – Your Gemini API key
* `ADMIN_PASSWORD` – Password to protect admin routes
* `UPLOAD_DIR` – Directory for storing downloaded/uploaded PDFs

---

### Run the Server

```bash
uvicorn main:app --reload
```

Access the application at:

```
http://localhost:8000
```

---

## 🕹️ API Reference

### Public Endpoints

#### `GET /`

Landing page with the chat interface.

#### `POST /api/chat`

Send user queries to the chatbot.

**Payload:**

```json
{
  "query": "What are the admission fees?",
  "history": []
}
```

---

### Admin Endpoints (Protected)

> Requires `x-admin-password` header authentication

* `POST /api/admin/crawl`
  Trigger website crawling for a given URL

* `POST /api/admin/upload`
  Upload a PDF manually to the knowledge base

* `POST /api/admin/retrain`
  Reprocess all data and rebuild the FAISS index

---

## 🧠 How It Works

1. **Ingestion**

   * The crawler scrapes target URLs and downloads PDFs
   * Admins can also upload documents manually

2. **Processing**

   * Text is cleaned, chunked, and embedded using HuggingFace models

3. **Indexing**

   * Embeddings are stored locally in a FAISS vector index

4. **Retrieval (RAG)**

   * User queries are converted into vectors
   * Relevant chunks are retrieved from FAISS

5. **Special Logic**

   * If a query implies a document request (e.g., *“download syllabus”*), the system immediately returns a direct file link

6. **Generation**

   * Retrieved context is sent to Gemini 2.0 Flash
   * The model generates a clear, institution-specific response

---

## 🤝 Contributing

Contributions are welcome and appreciated!

1. Fork the repository
2. Create your feature branch

   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit your changes

   ```bash
   git commit -m "Add AmazingFeature"
   ```
4. Push to the branch

   ```bash
   git push origin feature/AmazingFeature
   ```
5. Open a Pull Request

---

## 📜 License

This project is licensed under the **MIT License**.
Feel free to use, modify, and distribute it as needed.

---

<p align="center">
  Made with ❤️ by <strong>Ganesh Suvarnakar</strong>
</p>

Just tell me 👍
