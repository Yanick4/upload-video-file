FROM python:3.12-slim

WORKDIR /

# Copie les fichiers nécessaires dans le conteneur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
