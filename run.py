import os
import uvicorn

import sys

# Asegurar que el directorio raíz está en el path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Usar 8000 como default para coincidir con el EXPOSE del Dockerfile
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Iniciando servidor en puerto: {port}")
    # Añadimos proxy_headers y forwarded_allow_ips para que Railway pueda pasar las peticiones correctamente
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
