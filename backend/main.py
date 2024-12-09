from app.lib.Env import environment
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
import sys
from app.lib import JsonSchemas

app = FastAPI()

# We want this service's endpoints to be available from /api.
#
# In production, Digital Ocean handles that for us. In development,
# we add the prefix ourselves.
prefix = ""
if environment == "dev":
    prefix = "/api"
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
    # Production CORS settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://lyrics-frontend.onrender.com"
        ],  # Update with your frontend URL
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
