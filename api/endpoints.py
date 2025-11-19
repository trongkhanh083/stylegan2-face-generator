from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from datetime import datetime
from pathlib import Path

from services.generator import GenerationService
from schemas.requests import GenerateFaceRequest, GenerateGridRequest
from schemas.responses import GenerateFaceResponse
from core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Initialize the service
generation_service = GenerationService(settings.STYLEGAN2_MODEL_PATH)

# ===== WEB UI ENDPOINTS =====

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Main landing page with generation interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/grid", response_class=HTMLResponse)
async def grid_page(request: Request):
    """Grid generation page"""
    return templates.TemplateResponse("grid.html", {"request": request})

# ===== API ENDPOINTS =====

@router.post("/single", response_model=GenerateFaceResponse)
async def generate_single_face(request: GenerateFaceRequest):
    """Generate a single face image"""
    try:
        result = await generation_service.generate_single_image(
            seed=request.seed,
            truncation_psi=request.truncation,
            enhance_face=True
        )
        return GenerateFaceResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Single image generation failed: {str(e)}")

@router.post("/style-mix")
async def generate_face_grid(request: GenerateGridRequest):
    """Generate a style-mixing of faces"""
    try:
        result = await generation_service.generate_grid_image(
            row_seeds=request.row_seeds,
            col_seeds=request.col_seeds,
            truncation_psi=request.truncation,
            enhance_face=True
        )
        if result.get("url"):
            result["url"] = result["url"] + f"?t={int(datetime.now().timestamp())}"

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Style mixing generation failed: {str(e)}")

@router.get("/single/direct")
async def generate_single_face_direct(
    seed: int = Query(..., description="Random seed for generation"),
    truncation: float = Query(0.5, ge=0.0, le=1.0, description="Truncation psi"),
):
    """Generate and return image directly"""
    try:
        image_bytes = await generation_service.generate_direct_image_response(
            seed=seed,
            truncation_psi=truncation,
            enhance_face=True
        )
        
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={seed}.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Direct generation failed: {str(e)}")
    
from fastapi.responses import FileResponse

@router.get("/single/download")
async def download_cached_single_face(
    seed: int = Query(..., description="Random seed for generation"),
):
    """Download cached single face image if exists, otherwise generate new"""
    try:
        # Check if cached file exists
        cached_path = Path("static/generated") / f"{seed}.png"
        
        if cached_path.exists():
            # Return cached file instantly
            return FileResponse(
                cached_path,
                media_type="image/png",
                filename=f"face_{seed}.png"
            )
        else:
            # Generate and cache the image
            result = await generation_service.generate_single_image(
                seed=seed,
                truncation_psi=0.5,
                enhance_face=True,
                save_to_disk=True
            )
            
            # Return the cached file
            return FileResponse(
                Path("static/generated") / result["filename"],
                media_type="image/png",
                filename=f"face_{seed}.png"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    