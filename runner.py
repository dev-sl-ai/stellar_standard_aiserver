import os
import uvicorn


WORKERS = int(os.getenv("WEB_CONCURRENCY", "4"))

if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8080,
        timeout_keep_alive=90,
        ws="auto",
        workers=WORKERS,
    )