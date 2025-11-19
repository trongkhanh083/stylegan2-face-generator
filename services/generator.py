import uuid
import os
import torch
from datetime import datetime
from typing import List, Optional
import numpy as np
from pathlib import Path
from PIL import Image

from models.stylegan2 import StyleGAN2Generator
from services.realesrgan_enhance import RealESRGANProcessor

class GenerationService:
    def __init__(self, model_path: str):
        self.generator = StyleGAN2Generator(model_path)
        self.enhancer = RealESRGANProcessor(
            model_name='RealESRGAN_x4plus',
            face_enhance=True,
            fp32=True if not torch.cuda.is_available() else False,
            gpu_id=None
        )
        
        # Create output directories
        os.makedirs("static/generated", exist_ok=True)

    async def enhance_with_realesrgan(self, image_path: Path, output_path: Path) -> Path:
        """Enhance image using Real-ESRGAN directly"""
        try:
            return Path(self.enhancer.enhance_image_file(str(image_path), str(output_path)))
        except Exception as e:
            raise Exception(f"Real-ESRGAN enhancement failed: {str(e)}")

    async def enhance_image_direct(self, pil_image: Image.Image) -> Image.Image:
        """Enhance a PIL Image directly in memory"""
        try:
            return self.enhancer.enhance_image(pil_image)
        except Exception as e:
            raise Exception(f"Real-ESRGAN enhancement failed: {str(e)}")
    
    async def generate_single_image(
        self,
        seed: Optional[int] = None,
        truncation_psi: float = 0.5,
        enhance_face: bool = True,
        save_to_disk: bool = True
    ) -> dict:
        """Generate a single image with optional enhancement"""
        
        if seed is None:
            seed = np.random.randint(0, 2147483648)
        
        # Check if image already exists in cache
        enhanced_filename = f"{seed}.png"
        cached_filepath = Path("static/generated") / enhanced_filename
        
        if cached_filepath.exists():
            # Return cached image
            final_image = Image.open(cached_filepath)
            return {
                "seed": seed,
                "filename": enhanced_filename,
                "url": f"/static/generated/{enhanced_filename}",
                "enhancement": "cached",
                "truncation_psi": truncation_psi,
                "timestamp": datetime.now().isoformat(),
                "image_data": final_image
            }
        
        # If not cached, generate new image
        try:
            # Generate base image
            base_image = self.generator.generate_from_seed(seed, truncation_psi)

            if save_to_disk:
                # File-based processing
                base_filename = f"{seed}_base.png"
                base_filepath = Path("static/generated") / base_filename
                enhanced_filepath = Path("static/generated") / enhanced_filename

                base_image.save(base_filepath)
                
                # Apply enhancement if requested
                if enhance_face:
                    enhanced_filepath = await self.enhance_with_realesrgan(base_filepath, enhanced_filepath)
                    enhancement_type = "face_enhanced"
                else:
                    # If no enhancement, just rename the base file
                    base_filepath.rename(enhanced_filepath)
                    enhancement_type = "none"
                
                final_image = Image.open(enhanced_filepath)
                
                # Clean up base file
                if base_filepath.exists():
                    base_filepath.unlink()

                image_url = f"/static/generated/{enhanced_filename}"
            else:
                # In-memory processing for direct responses
                if enhance_face:
                    final_image = await self.enhance_image_direct(base_image)
                    enhancement_type = "face_enhanced"
                else:
                    final_image = base_image
                    enhancement_type = "none"
                
                image_url = None
            
            return {
                "seed": seed,
                "filename": f"{seed}.png",
                "url": image_url,
                "enhancement": enhancement_type,
                "truncation_psi": truncation_psi,
                "timestamp": datetime.now().isoformat(),
                "image_data": final_image
            }
            
        except Exception as e:
            raise Exception(f"Image generation failed: {str(e)}")
    
    async def generate_grid_image(
        self,
        row_seeds: List[int],
        col_seeds: List[int],
        truncation_psi: float = 0.5,
        enhance_face: bool = True,
        save_to_disk: bool = True
    ) -> dict:
        """Generate grid image and then enhance the entire grid"""
        try:
            # Generate the complete grid image first
            grid_image = self.generator.generate_from_grid(
                row_seeds=row_seeds,
                col_seeds=col_seeds,
                truncation_psi=truncation_psi
            )

            job_id = uuid.uuid4().hex[:8]
            
            if save_to_disk:
                # File-based processing
                if enhance_face:
                    # Save base grid temporarily
                    base_filename = f"{job_id}_base.png"
                    enhanced_filename = f"{job_id}.png"

                    base_filepath = Path("static/generated") / base_filename
                    enhanced_filepath = Path("static/generated") / enhanced_filename
                    
                    grid_image.save(base_filepath)
                    
                    # Enhance the entire grid image
                    enhanced_filepath = await self.enhance_with_realesrgan(base_filepath, enhanced_filepath)
                    enhancement_type = "grid_enhanced"
                    
                    # Clean up base file
                    if base_filepath.exists():
                        base_filepath.unlink()
                        
                    final_image = Image.open(enhanced_filepath)
                else:
                    # Save without enhancement
                    final_filepath = Path("static/generated") / enhanced_filename
                    grid_image.save(final_filepath)
                    final_image = grid_image
                    enhancement_type = "none"

                image_url = f"/static/generated/{enhanced_filename}"
            else:
                # In-memory processing
                if enhance_face:
                    final_image = await self.enhance_image_direct(grid_image)
                    enhancement_type = "grid_enhanced"
                else:
                    final_image = grid_image
                    enhancement_type = "none"
                
                image_url = None
            
            return {
                "row_seeds": row_seeds,
                "col_seeds": col_seeds,
                "filename": f"{job_id}.png",
                "url": image_url,
                "enhancement": enhancement_type,
                "truncation_psi": truncation_psi,
                "grid_size": f"{len(row_seeds)}x{len(col_seeds)}",
                "timestamp": datetime.now().isoformat(),
                "image_data": final_image
            }

        except Exception as e:
            raise Exception(f"Style mixing generation failed: {str(e)}")
    
    async def generate_direct_image_response(
        self,
        seed: int,
        truncation_psi: float = 0.5,
        enhance_face: bool = True
    ) -> bytes:
        """Generate image and return as bytes for direct API response"""
        # Check if cached file exists
        cached_filename = f"{seed}.png"
        cached_filepath = Path("static/generated") / cached_filename
        
        if cached_filepath.exists():
            # Return cached file
            with open(cached_filepath, "rb") as f:
                return f.read()
        else:
            # Generate new image and cache it
            result = await self.generate_single_image(
                seed=seed,
                truncation_psi=truncation_psi,
                enhance_face=enhance_face,
                save_to_disk=True
            )
            
            return self.generator.image_to_bytes(result["image_data"])
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model"""
        return self.generator.get_network_info()