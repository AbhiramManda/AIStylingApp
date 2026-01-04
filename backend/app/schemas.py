from pydantic import BaseModel, EmailStr
from typing import Optional, Any, Dict
from datetime import datetime

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
    image_url: Optional[str] = None
    body_type: Optional[str] = None
    location: Optional[str] = None
    age: Optional[int] = None

class SuggestionOut(BaseModel):
    id: int
    suggestion: Dict[str, Any]

class ChatMessageIn(BaseModel):
    message: str
    current_suggestions: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    age: Optional[int] = None

class ChatMessageOut(BaseModel):
    id: int
    message: str
    response: str
    created_at: datetime
    class Config:
        orm_mode = True
