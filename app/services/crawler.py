
import os
import uuid
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
from collections import deque
from app.config import settings

class CrawlerService:
    def __init__(self):
        self.visited = set()
        self.headers = {"User-Agent": "Sahayak-AI-Crawler/2.1"}
        self.map_file = os.path.join(settings.BASE_DIR, "data", "file_map.json")
        
        # Load existing map or create new
        if os.path.exists(self.map_file):
            with open(self.map_file, "r") as f:
                self.file_map = json.load(f)
        else:
            self.file_map = {}

        self.noise_keywords = [
            "home", "menu", "navbar", "privacy", "login", "register", "©"
        ]
        self.remove_tags = ["script", "style", "nav", "footer", "img", "form"]

    def save_map(self):
        """Saves the UUID -> Real Name mapping to JSON"""
        with open(self.map_file, "w") as f:
            json.dump(self.file_map, f, indent=2)

    def get_filename_from_url(self, url):
        """Extracts 'syllabus.pdf' from 'http://college.edu/data/syllabus.pdf'"""
        parsed = urlparse(url)
        path = unquote(parsed.path)
        name = os.path.basename(path)
        if not name.endswith(".pdf"):
            name = "document.pdf"
        return name

    def download_pdf(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # Generate ID
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}.pdf"
            save_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

            # Save File
            with open(save_path, "wb") as f:
                f.write(response.content)

            # Save Metadata to Map
            original_name = self.get_filename_from_url(url)
            
            self.file_map[safe_filename] = {
                "display_name": original_name,
                "url": url,
                "type": "pdf"
            }
            self.save_map() # Save immediately

            print(f"[PDF] Saved: {original_name} -> {safe_filename}")
            return save_path

        except Exception as e:
            print(f"[ERROR] PDF Failed {url}: {e}")
            return None

    def clean_text(self, text):
        cleaned = []
        for line in text.split("\n"):
            line = line.strip()
            if len(line) < 3: continue
            if any(kw in line.lower() for kw in self.noise_keywords): continue
            cleaned.append(line)
        return "\n".join(cleaned)

    def crawl(self, start_url, max_depth=2):
        queue = deque([(start_url, 0)])
        results = []

        while queue:
            url, depth = queue.popleft()
            if depth > max_depth or url in self.visited:
                continue

            self.visited.add(url)
            print(f"[CRAWL] Processing: {url}")

            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                soup = BeautifulSoup(response.content, "html.parser")

                # 1. Look for PDFs FIRST (Priority)
                for link in soup.find_all("a", href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    if href.lower().endswith(".pdf"):
                        if full_url not in self.visited:
                            self.visited.add(full_url)
                            pdf_path = self.download_pdf(full_url)
                            if pdf_path:
                                results.append({"url": full_url, "type": "pdf"})

                # 2. Extract Text
                for tag in self.remove_tags:
                    for element in soup.find_all(tag):
                        element.decompose()
                
                text = self.clean_text(soup.get_text("\n"))
                if len(text) > 50:
                    file_id = str(uuid.uuid4())
                    filename = f"{file_id}.txt"
                    save_path = os.path.join(settings.RAW_DATA_DIR, filename)
                    
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(f"URL: {url}\n\n{text}")
                    
                    # Add text files to map too (optional, but good for linking)
                    self.file_map[filename] = {
                        "display_name": "Web Page",
                        "url": url,
                        "type": "web"
                    }
                    self.save_map()
                    results.append({"url": url, "type": "web"})

                # 3. Find next links
                for link in soup.find_all("a", href=True):
                    full_url = urljoin(url, link['href'])
                    if urlparse(full_url).netloc == urlparse(start_url).netloc:
                        if full_url not in self.visited:
                            queue.append((full_url, depth + 1))

            except Exception as e:
                print(f"[ERROR] {url}: {e}")

        return results