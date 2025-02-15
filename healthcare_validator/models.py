from pydantic import BaseModel
from typing import Dict

class FieldResult(BaseModel):
    status: str
    message: str

class ProviderValidation(BaseModel):
    provider: str
    results: Dict[str, FieldResult]
