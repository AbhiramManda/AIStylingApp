from pydantic import BaseModel, EmailStr
from typing import Optional, Any, Dict

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    class Config:
        orm_mode = True

class UploadResponse(BaseModel):
    url: str

class SuggestionIn(BaseModel):
    image_url: Optional[str]
    body_type: Optional[str]

class SuggestionOut(BaseModel):
    id: int
    suggestion: Dict[str, Any]
