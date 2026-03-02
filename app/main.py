import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import io
import os

try:
    # Intentamos importación relativa y absoluta para cubrir todos los escenarios de contenedores
    try:
        from .processor import leer_csv_robusto, preparar_df, procesar_csv, crear_zip
    except (ImportError, ValueError):
        from app.processor import leer_csv_robusto, preparar_df, procesar_csv, crear_zip
    logger.info("✅ Processor module loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading processor module: {str(e)}")

app = FastAPI(title="Procesador módulo de compras")

# Obtener la ruta del directorio actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

logger.info(f"📁 BASE_DIR: {BASE_DIR}")
logger.info(f"📁 STATIC_DIR: {STATIC_DIR}")
logger.info(f"🏠 Archivos en STATIC_DIR: {os.listdir(STATIC_DIR) if os.path.exists(STATIC_DIR) else 'No existe'}")

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = leer_csv_robusto(content)
        df_prepared, tipo = preparar_df(df)
        
        return {
            "filename": file.filename,
            "columns": df.shape[1],
            "type": tipo,
            "rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = leer_csv_robusto(content)
        df_prepared, tipo = preparar_df(df)
        
        files_dict = procesar_csv(df_prepared, tipo)
        zip_buffer = crear_zip(files_dict)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename=LIBRO_IVA_DIGITAL_SALIDA.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
