FROM python:3.11-slim

WORKDIR /code
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr libgl1 \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ocr.txt requirements-postgres.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-ocr.txt -r requirements-postgres.txt

COPY app ./app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
