from app.lib.Env import environment
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
import sys
from app.lib import JsonSchemas

app = FastAPI()

# Always use /api prefix in both dev and prod
prefix = "/api"

if environment == "dev":
    logger = logging.getLogger("uvicorn")
    logger.warning("Running in development mode - allowing CORS for all origins")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://lyrics-frontend.onrender.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=prefix)

if __name__ == "__main__":
    if "--save-json-schemas" in sys.argv:
        JsonSchemas.save_all()
    else:
        uvicorn.run(app="main:app", host="0.0.0.0", reload=True)
