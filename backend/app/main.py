from fastapi import FastAPI
from .db import engine, Base
from .models import User, UserProfile, StyleSuggestion, Chat, Base
from fastapi.middleware.cors import CORSMiddleware
from app.routes import chats_routes

# This will create all tables defined in models.py if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Personal Styling App API", redirect_slashes=False)
# ✅ Add this section
origins = [
    "http://localhost:8080",   # frontend (vite/nginx)
    "http://127.0.0.1:8080",   # sometimes used by browsers
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],            # allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],            # allow all headers
)

# ... existing imports, routers, etc.
from app.routes import auth_routes, upload_routes, suggestions_routes, user_routes

app.include_router(auth_routes.router, prefix="/api", tags=["Auth"])
app.include_router(upload_routes.router, prefix="/api", tags=["Upload"])
app.include_router(suggestions_routes.router, prefix="/api", tags=["Suggestions"])
app.include_router(user_routes.router, prefix="/api", tags=["User"])
app.include_router(chats_routes.router, prefix="/api")

