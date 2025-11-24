from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timedelta

# Secret key (you can later move this to environment variables)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

router = APIRouter(prefix="/users", tags=["Users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Temporary in-memory "database"
fake_users_db = {}


# ========================
# Pydantic Models
# ========================
class User(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ========================
# Helper Functions
# ========================
def get_password_hash(password: str) -> str:
    # Ensure input is a string
    if not isinstance(password, str):
        password = str(password)
    # Truncate to 72 chars to satisfy bcrypt
    return pwd_context.hash(password[:72])


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ========================
# Routes
# ========================
@router.post("/register")
def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pw = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_pw
    }

    return {"message": "User registered successfully"}


@router.post("/login", response_model=Token)
def login(user: UserLogin):
    db_user = fake_users_db.get(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/profile")
def get_profile(username: str):
    db_user = fake_users_db.get(username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": db_user["username"],
        "email": db_user["email"]
    }
