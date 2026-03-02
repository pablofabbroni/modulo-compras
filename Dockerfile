FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer el puerto que Railway/Render suelen usar
EXPOSE 8000

# Usar uvicorn directamente para simplificar el debug en Railway
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
