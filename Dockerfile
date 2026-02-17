FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model to cache it in the image layer
COPY download_model.py .
RUN python download_model.py
# Verify files in build log
RUN echo "Checking /root/.cache after download:" && ls -R /root/.cache

COPY . .

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000"]
