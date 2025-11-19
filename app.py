from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from core.config import settings
from api.endpoints import router

app = FastAPI(
    title="StyleGAN2 Face Generator API",
    description="Generate and enhance AI faces using StyleGAN2",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# add router
app.include_router(router, prefix="/api/v1/generate", tags=["generation"])

@app.get("/")
async def root():
    return {"message": "StyleGAN2 Face Generator API."}

@app.get("/health")
async def health_check():
    return {"status": "API is running."}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = "static/favicon.png"
    if Path(favicon_path).exists():
        return FileResponse(favicon_path)
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")