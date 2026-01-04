from fastapi import APIRouter, Depends, HTTPException, Header
from ..schemas import SuggestionIn, SuggestionOut
from ..db import SessionLocal
from sqlalchemy.orm import Session
from ..models import StyleSuggestion, Chat
from ..ai_engine import analyze_image_and_generate_features, generate_suggestions_with_llm, get_current_season
from ..auth import decode_token
from ..chats import get_styling_suggestions

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
    season = get_current_season()
    location = payload.location if hasattr(payload, 'location') and payload.location else None
    age = payload.age if hasattr(payload, 'age') and payload.age else None
    suggestion = generate_suggestions_with_llm(features, payload.body_type, season, location, age)

    db_record = StyleSuggestion(user_id=user_id, suggestion=suggestion)
    db.add(db_record); db.commit(); db.refresh(db_record)
    return db_record

@router.get("/suggestions/history", response_model=list[SuggestionOut])
def list_suggestions(db: Session = Depends(get_db), user_id: int = Depends(get_user_from_token)):
    results = db.query(StyleSuggestion).filter(StyleSuggestion.user_id == user_id).all()
    return results

@router.post("/suggestions/prompt")
def chat_prompt(
    payload: dict,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_from_token)
):
    """
    POST endpoint for chat prompts (compatibility with frontend).
    Expects JSON: { "prompt": "<user_message>" }
    Returns: { "explanation": "<ai_response>" }
    """
    user_message = payload.get("prompt", "")
    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # Get recent conversation history for context
    recent_chats = db.query(Chat).filter(
        Chat.user_id == user_id
    ).order_by(Chat.created_at.desc()).limit(10).all()
    
    conversation_history = []
    for chat in reversed(recent_chats):
        conversation_history.append({"role": "user", "content": chat.message})
        conversation_history.append({"role": "assistant", "content": chat.response})

    # Get current suggestions if provided
    current_suggestions = payload.get("current_suggestions")
    
    # Get season, location, and age from current suggestions, payload, or use defaults
    from ..ai_engine import get_current_season
    season = None
    location = payload.get("location")
    age = payload.get("age")
    
    if current_suggestions:
        if "season" in current_suggestions:
            season = current_suggestions.get("season")
        if "location" in current_suggestions and not location:
            location = current_suggestions.get("location")
        if "age" in current_suggestions and not age:
            age = current_suggestions.get("age")
    
    if season is None:
        season = get_current_season()

    # Generate AI response
    response_text, updated_suggestions = get_styling_suggestions(
        user_message, 
        conversation_history,
        current_suggestions,
        season,
        location,
        age
    )

    # Save chat to database
    chat_record = Chat(
        user_id=user_id,
        message=user_message,
        response=response_text
    )
    db.add(chat_record)
    db.commit()

    result = {"explanation": response_text}
    if updated_suggestions:
        result["updated_suggestions"] = updated_suggestions
    
    return result
