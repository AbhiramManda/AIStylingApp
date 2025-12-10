from fastapi import APIRouter, Depends, HTTPException
from ..schemas import SuggestionIn, SuggestionOut
from ..db import SessionLocal
from sqlalchemy.orm import Session
from ..models import StyleSuggestion
from ..ai_engine import analyze_image_and_generate_features, generate_suggestions_with_llm
from ..auth import decode_token
from fastapi import Header

router = APIRouter(tags=["suggestions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_from_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing auth")
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return int(payload.get("sub"))

@router.post("/suggestions", response_model=SuggestionOut)
def create_suggestion(payload: SuggestionIn, db: Session = Depends(get_db), user_id: int = Depends(get_user_from_token)):
    # fetch image (if provided), run analysis and generate suggestion
    features = {}
    if payload.image_url:
        # In production, download image, pass path to model
        print("calling once")
        features = analyze_image_and_generate_features(payload.image_url)
    # else:
    #     features = analyze_image_and_generate_features("sample.png")
    # suggestion = generate_suggestions(features, payload.body_type)
    suggestion = generate_suggestions_with_llm(features, payload.body_type)

    db_record = StyleSuggestion(user_id=user_id, suggestion=suggestion)
    db.add(db_record); db.commit(); db.refresh(db_record)
    return db_record

@router.get("/suggestions/history", response_model=list[SuggestionOut])
def list_suggestions(db: Session = Depends(get_db), user_id: int = Depends(get_user_from_token)):
    results = db.query(StyleSuggestion).filter(StyleSuggestion.user_id == user_id).all()
    return results
