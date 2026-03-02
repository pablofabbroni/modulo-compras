FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exponer el puerto que Railway/Render suelen usar
EXPOSE 8000

# Usar el script run.py que maneja dinámicamente el puerto de Railway
CMD ["python", "run.py"]
