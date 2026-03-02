import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
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
