from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from .processor import leer_csv_robusto, preparar_df, procesar_csv, crear_zip
import io

app = FastAPI(title="Módulo AFIP Compras/Importación")

# Servir archivos estáticos (frontend)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("app/static/index.html")

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
