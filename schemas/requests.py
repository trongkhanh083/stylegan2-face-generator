from pydantic import BaseModel, Field
from typing import Optional, List

class GenerateFaceRequest(BaseModel):
    seed: Optional[int] = Field(None, description="Random seed for generation")
    truncation: float = Field(0.5, ge=0.0, le=1.0, description="Truncation psi value")

class GenerateGridRequest(BaseModel):
    row_seeds: List[int] = Field(..., description="List of row seeds for style mixing")
    col_seeds: List[int] = Field(..., description="List of column seeds for style mixing")
    truncation: float = Field(0.5, ge=0.0, le=1.0, description="Truncation psi value")
