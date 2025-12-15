from openai import OpenAI
from app.config import settings
from typing import List, Dict, Optional

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_chat_response(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Takes a user prompt and optional conversation history, returns AI-generated styling suggestions.
    """
    system_prompt = """
    You are an AI Personal Styling Assistant.

    For any user request, generate a complete styling response:
    - Hairstyle
    - Beard style (if applicable)
    - Outfit
    - Accessories
    - Grooming tips

    Adapt suggestions to the user's situation. Be conversational, helpful, and provide detailed, 
    personalized styling advice. If the user asks follow-up questions, reference previous context 
    when relevant.
    """

    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating chat response: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later."


def get_styling_suggestions(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Takes a user prompt and optional conversation history, returns AI-generated styling suggestions.
    """
    return generate_chat_response(user_message, conversation_history)
