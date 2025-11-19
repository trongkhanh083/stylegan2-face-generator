from pydantic import BaseModel
from typing import List
from datetime import datetime

class GenerateFaceResponse(BaseModel):
    seed: int
    filename: str
    url: str
    enhancement: str
    truncation_psi: float
    timestamp: datetime
