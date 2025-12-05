FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for extensions
RUN apt-get update && apt-get install -y build-essential

# Copy Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy App
COPY . .

# Environment Variables (Override these in production)
ENV PORT=8000

# Expose Port
EXPOSE 8000

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]