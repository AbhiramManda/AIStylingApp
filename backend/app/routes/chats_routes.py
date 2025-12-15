from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.chats import get_styling_suggestions
from app.db import SessionLocal
from app.models import Chat
from app.schemas import ChatMessageIn, ChatMessageOut
from app.auth import decode_token
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_from_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload.get("sub"))

@router.post("/chat", response_model=dict)
async def chat_endpoint(
    payload: ChatMessageIn,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_from_token)
):
    """
    POST endpoint for chat prompts with authentication.
    Expects JSON: { "message": "<user_prompt>" }
    Returns: { "response": "<ai_response>" }
    """
    user_message = payload.message
    if not user_message or not user_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Get recent conversation history (last 10 messages) for context
    recent_chats = db.query(Chat).filter(
        Chat.user_id == user_id
    ).order_by(Chat.created_at.desc()).limit(10).all()
    
    # Build conversation history in the format expected by OpenAI
    conversation_history = []
    for chat in reversed(recent_chats):  # Reverse to get chronological order
        conversation_history.append({"role": "user", "content": chat.message})
        conversation_history.append({"role": "assistant", "content": chat.response})

    # Generate AI response
    response_text = get_styling_suggestions(user_message, conversation_history)

    # Save chat to database
    chat_record = Chat(
        user_id=user_id,
        message=user_message,
        response=response_text
    )
    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)

    return {"response": response_text}

@router.get("/chat/history", response_model=List[ChatMessageOut])
async def get_chat_history(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_from_token)
):
    """
    GET endpoint to retrieve chat history for the authenticated user.
    Returns list of chat messages ordered by creation time (newest first).
    """
    chats = db.query(Chat).filter(
        Chat.user_id == user_id
    ).order_by(Chat.created_at.desc()).limit(50).all()
    return chats
