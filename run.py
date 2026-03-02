import os
import uvicorn

if __name__ == "__main__":
    # Railway provee la variable de entorno PORT
    port = int(os.environ.get("PORT", 8000))
    # Ejecutamos la app apuntando al path correcto
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
