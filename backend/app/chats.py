from openai import OpenAI
from app.config import settings
from typing import List, Dict, Optional, Any
import json
import re
from app.ai_engine import get_current_season

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_chat_response(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    current_suggestions: Optional[Dict[str, Any]] = None,
    season: Optional[str] = None,
    location: Optional[str] = None,
    age: Optional[int] = None
) -> tuple[str, Optional[Dict[str, Any]]]:
    """
    Takes a user prompt and optional conversation history, returns AI-generated styling suggestions.
    """
    # Get current season if not provided
    if season is None:
        season = get_current_season()
    
    # Extract season, location, and age from current suggestions if available
    if current_suggestions:
        if "season" in current_suggestions:
            season = current_suggestions.get("season", season)
        if "location" in current_suggestions:
            location = current_suggestions.get("location", location)
        if "age" in current_suggestions:
            age = current_suggestions.get("age", age)
    
    location_context = location or "general"
    
    # Build age-based styling guidance
    age_guidance = ""
    if age is not None:
        if age < 18:
            age_guidance = """
AGE-BASED STYLING (Teens): Trendy, modern styles. Can experiment with bold cuts and streetwear. Avoid overly formal styles.
"""
        elif age < 25:
            age_guidance = """
AGE-BASED STYLING (Young Adults 18-24): Modern, versatile styles balancing trendiness with professionalism. Smart-casual ideal.
"""
        elif age < 35:
            age_guidance = """
AGE-BASED STYLING (Adults 25-34): Polished, professional styles. Quality basics with contemporary touches. Smart-casual and business-casual appropriate.
"""
        elif age < 50:
            age_guidance = """
AGE-BASED STYLING (Mature Adults 35-49): Classic, refined styles with modern updates. Timeless pieces with contemporary fits. Emphasize sophistication.
"""
        else:
            age_guidance = """
AGE-BASED STYLING (50+): Classic, elegant styles. Refined, comfortable, well-fitted pieces. Timeless classics with modern fits. Emphasize elegance and comfort.
"""
    
    # Build location-specific guidance
    location_guidance = ""
    if location:
        location_guidance = f"""
LOCATION-BASED STYLING for {location}:
- Consider the climate and local fashion trends of {location}
- Tropical/Equatorial: Lighter fabrics even in winter, year-round summer styles
- Desert: Temperature-regulating layers, hot days/cool nights
- Temperate: Standard seasonal guidelines apply
- Cold/Polar: Heavy insulation in winter, mild summers
- Coastal: Breathable, humidity-resistant fabrics
- Urban: Trend-aware, fashion-forward suggestions
- Rural: Practical, durable, comfortable suggestions
Adjust the "casual" outfit based on location climate combined with season.
"""
    
    # Build system prompt based on whether we have current suggestions
    if current_suggestions:
        system_prompt = f"""
    You are an AI Personal Styling Assistant. The user has current styling suggestions that you can modify or update based on their requests.
    
    Current season: {season}
    Location: {location_context}
    Age: {age if age is not None else "Not specified"}
    
    {age_guidance}
    {location_guidance}
    
    When the user asks to change, modify, or update their suggestions, you MUST respond with:
    1. A conversational text response explaining the changes
    2. A JSON object with the updated suggestions in this exact format:
    
    {{
      "hairstyle": {{
        "style": "string",
        "description": "string"
      }},
      "beard": {{
        "style": "string",
        "description": "string"
      }},
      "outfit": {{
        "suggestions": [
          {{
            "type": "casual",
            "season": "{season}",
            "location": "{location_context}",
            "items": ["string"],
            "description": "string (optional)"
          }},
          {{
            "type": "smart-casual",
            "season": "{season}",
            "location": "{location_context}",
            "items": ["string"],
            "description": "string (optional)"
          }},
          {{
            "type": "formal",
            "season": "{season}",
            "location": "{location_context}",
            "items": ["string"],
            "description": "string (optional)"
          }}
        ]
      }},
      "skin_tone": "string",
      "explanation": "string",
            "gender": "string",
      "season": "{season}",
      "location": "{location_context}",
      "age": {age if age is not None else "null"}
    }}
    
    IMPORTANT OUTFIT RULES:
    - You MUST include exactly THREE outfit types: "casual", "smart-casual", and "formal"
    - ALL three outfits must be season-appropriate AND location-appropriate AND age-appropriate:
      * Winter: Consider location - tropical needs lighter layers, cold locations need heavy insulation
      * Spring: Light layers, transitional pieces - adjust for location's spring climate
      * Summer: Light fabrics, breathable materials - tropical may need year-round summer styles
      * Fall: Medium layers, cozy pieces - adjust for location's fall climate
    - Location considerations: Urban = trendier, Coastal = humidity-resistant, Desert = temperature-regulating, etc.
    - Age considerations: Ensure all outfits are age-appropriate (teens = trendier, mature adults = more refined)
    - If user asks to change season, location, or age, update ALL three outfit types accordingly
    - Always maintain all three outfit types: casual, smart-casual, and formal

    If the user is just asking questions (not requesting changes), respond conversationally without JSON.
    If they ARE requesting changes, include the updated JSON at the end of your response, wrapped in <SUGGESTIONS> tags like this:
    <SUGGESTIONS>
    {{json here}}
    </SUGGESTIONS>
    """
        # Add current suggestions to context
        suggestions_context = f"\n\nCurrent suggestions:\n{json.dumps(current_suggestions, indent=2)}"
        user_message_with_context = user_message + suggestions_context
    else:
        system_prompt = f"""
    You are an AI Personal Styling Assistant.
    
    Current season: {season}
    Location: {location_context}
    Age: {age if age is not None else "Not specified"}
    
    {age_guidance}
    {location_guidance}

    For any user request, generate a complete styling response:
    - Hairstyle
    - Beard style (if applicable)
    - Outfit (MUST include exactly THREE types: "casual", "smart-casual", and "formal")
    - Accessories
    - Grooming tips

    IMPORTANT: When generating outfit suggestions, you MUST include exactly THREE outfit types: "casual", "smart-casual", and "formal". ALL three must be season-appropriate AND location-appropriate AND age-appropriate:
    - Winter: Consider location climate - tropical = lighter layers, cold = heavy insulation
    - Spring: Light layers, transitional pieces - adjust for location's spring climate
    - Summer: Light fabrics, breathable materials - tropical may need year-round summer styles
    - Fall: Medium layers, cozy pieces - adjust for location's fall climate
    - Location factors: Urban = trendier, Coastal = humidity-resistant, Desert = temperature-regulating
    - Age factors: Ensure all suggestions are age-appropriate. Teens can be trendier, mature adults should emphasize sophistication and timelessness.

    Adapt suggestions to the user's situation, current season, location, and age. Be conversational, helpful, and provide detailed, 
    personalized styling advice. If the user asks follow-up questions, reference previous context 
    when relevant.
    """
        user_message_with_context = user_message

    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user message
    messages.append({"role": "user", "content": user_message_with_context})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.8,
        )
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract updated suggestions if present
        updated_suggestions = None
        suggestions_match = re.search(r'<SUGGESTIONS>\s*(\{.*?\})\s*</SUGGESTIONS>', response_text, re.DOTALL)
        if suggestions_match:
            try:
                suggestions_json = suggestions_match.group(1)
                updated_suggestions = json.loads(suggestions_json)
                # Remove the JSON from the response text for cleaner display
                response_text = re.sub(r'<SUGGESTIONS>.*?</SUGGESTIONS>', '', response_text, flags=re.DOTALL).strip()
            except json.JSONDecodeError:
                pass
        
        return response_text, updated_suggestions
    except Exception as e:
        print(f"Error generating chat response: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again later.", None


def get_styling_suggestions(
    user_message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    current_suggestions: Optional[Dict[str, Any]] = None,
    season: Optional[str] = None,
    location: Optional[str] = None,
    age: Optional[int] = None
) -> tuple[str, Optional[Dict[str, Any]]]:
    """
    Takes a user prompt, optional conversation history, optional current suggestions, optional season, optional location, and optional age.
    Returns tuple of (response_text, updated_suggestions).
    """
    return generate_chat_response(user_message, conversation_history, current_suggestions, season, location, age)
