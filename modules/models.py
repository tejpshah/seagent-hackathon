from pydantic import BaseModel
from typing import Dict, List, Optional

class FieldResult(BaseModel):
    status: str  # "Validated", "Needs Work", or "Incorrect"
    message: str
    source: Optional[List[str]] = []  # List of URLs

class ProviderValidation(BaseModel):
    provider: str
    results: Dict[str, FieldResult]
