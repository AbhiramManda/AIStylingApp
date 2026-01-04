from typing import Dict, Any, Optional
import os
import math
import re
from urllib.parse import urlparse
from datetime import datetime

import boto3
from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# ============================
# SEASON DETECTION UTILITY
# ============================

def get_current_season() -> str:
    """
    Determines the current season based on the date.
    Returns: "winter", "spring", "summer", or "fall"
    """
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:  # 9, 10, 11
        return "fall"


# ============================
# 0. LLM SUGGESTION GENERATOR
# ============================

def generate_suggestions_with_llm(face_data: dict, body_type: str, season: Optional[str] = None, location: Optional[str] = None, age: Optional[int] = None) -> dict:
    import json

    # Get current season if not provided
    if season is None:
        season = get_current_season()

    # Extract age from AgeRange if not provided
    if age is None:
        age_range = face_data.get("AgeRange", {})
        if age_range and isinstance(age_range, dict):
            age_low = age_range.get("Low")
            age_high = age_range.get("High")
            if age_low is not None and age_high is not None:
                age = (age_low + age_high) // 2  # Use midpoint of detected age range
        elif isinstance(age_range, (int, float)):
            age = int(age_range)

    # Build a compact, normalized profile to send to the LLM
    llm_profile = {
        # High-impact metrics
        "face_shape_detailed": face_data.get("face_shape_detailed"),
        "jawline": face_data.get("jawline", {}),
        "cheekbones": face_data.get("cheekbones", {}),
        "forehead": face_data.get("forehead", {}),
        "hair": face_data.get("hair", {}),
        "skin": face_data.get("skin", {}),

        # Legacy/raw cues
        "raw_face_shape": face_data.get("FaceShape", {}).get("Value"),
        "age_range": face_data.get("AgeRange"),
        "smile": face_data.get("Smile", {}),
        "eyeglasses": face_data.get("Eyeglasses", {}),
        "eyes_open": face_data.get("EyesOpen", {}),
        "beard": face_data.get("Beard", {}),
        "mustache": face_data.get("Mustache", {}),
        "gender": face_data.get("Gender", {}),
        "body_type": body_type,
        "season": season,
        "location": location or "general",
        "age": age,
    }

    # Best-effort gender & skin tone
    gender = (
        face_data.get("Gender", {}).get("Value")
        or face_data.get("gender")
        or "Unknown"
    )
    skin_block = face_data.get("skin", {})
    skin_tone = (
        skin_block.get("skin_tone")
        or face_data.get("skin_tone")
        or "medium"
    )
    skin_undertone = skin_block.get("skin_undertone", "neutral")

    profile_json = json.dumps(llm_profile, ensure_ascii=False)
    print("profile_json:" , profile_json)
    location_context = location or "general"
    
    # Build age-based styling guidance
    age_guidance = ""
    if age is not None:
        if age < 18:
            age_category = "teen"
            age_guidance = """
AGE-BASED STYLING GUIDANCE (Teens):
- Hairstyles: Trendy, modern cuts that reflect current youth culture. Can experiment with bold styles, colors, and lengths.
- Outfits: Fashion-forward, streetwear-influenced, casual and comfortable. Can incorporate trendy items, sneakers, graphic tees.
- Avoid overly formal or conservative styles unless specifically requested.
"""
        elif age < 25:
            age_category = "young adult"
            age_guidance = """
AGE-BASED STYLING GUIDANCE (Young Adults 18-24):
- Hairstyles: Modern, versatile styles that balance trendiness with professionalism. Can experiment with contemporary cuts.
- Outfits: Mix of trendy and classic pieces. Smart-casual is ideal. Can incorporate current fashion trends while maintaining versatility.
- Balance youthful energy with emerging professional needs.
"""
        elif age < 35:
            age_category = "adult"
            age_guidance = """
AGE-BASED STYLING GUIDANCE (Adults 25-34):
- Hairstyles: Polished, professional styles that are modern but timeless. Focus on well-maintained, versatile cuts.
- Outfits: Professional-casual balance. Quality basics with contemporary touches. Smart-casual and business-casual appropriate.
- Emphasize sophistication while staying current.
"""
        elif age < 50:
            age_category = "mature adult"
            age_guidance = """
AGE-BASED STYLING GUIDANCE (Mature Adults 35-49):
- Hairstyles: Classic, refined styles with modern updates. Focus on sophistication and low-maintenance elegance.
- Outfits: Timeless pieces with contemporary fits. Quality over quantity. Professional and polished casual wear.
- Emphasize refined, age-appropriate sophistication.
"""
        else:
            age_category = "senior"
            age_guidance = """
AGE-BASED STYLING GUIDANCE (50+):
- Hairstyles: Classic, elegant styles that are easy to maintain. Focus on sophistication and timeless appeal.
- Outfits: Refined, comfortable, and well-fitted pieces. Timeless classics with modern fits. Quality materials and construction.
- Emphasize elegance, comfort, and timeless style over trends.
"""
    else:
        age_category = "unknown"
        age_guidance = ""
    
    location_guidance = ""
    if location:
        location_guidance = f"""
LOCATION-BASED STYLING GUIDANCE for {location}:
Consider the climate, cultural norms, and local fashion trends of {location} when suggesting outfits.
- Tropical/Equatorial locations: Even in "winter", suggest lighter fabrics. Summer is year-round hot and humid.
- Desert locations: Hot days, cool nights - suggest layering even in summer. Winters are mild.
- Temperate locations: Follow standard seasonal guidelines.
- Cold/Polar locations: Winters are extremely cold - suggest heavy insulation. Summers are short and mild.
- Coastal locations: Consider humidity, wind, and salt air - suggest breathable, durable fabrics.
- Urban locations: More fashion-forward, trend-aware suggestions.
- Rural locations: Practical, durable, comfortable suggestions.
Adjust the "casual" outfit based on these location-specific considerations combined with the season.
"""

    prompt = f"""
You are a professional AI stylist and grooming consultant.

I will give you a structured JSON profile describing a person's facial geometry, hair, skin, body type, current season, location, and age.
Use that profile to recommend:
- A specific hairstyle (by name) with a short explanation
- A beard style (or no beard) with a short explanation
- Outfit suggestions (types of outfits + example items) - MUST include exactly THREE outfit types: "casual", "smart-casual", and "formal"
- A suggested skin tone label (for color palette) and a brief explanation tying everything together

Current season: {season}
Location: {location_context}
Age: {age if age is not None else "Not specified"}

{age_guidance}
{location_guidance}

{location_guidance}

Here is the profile (JSON):

{profile_json}

Key fields you can rely on:
- face_shape_detailed: overall face shape (oval, square, round, heart, triangle, diamond, oblong, rectangle)
- jawline: {{
    "strength": "strong | medium | soft",
    "chin_shape": "pointed | rounded | square"
  }}
- cheekbones: {{
    "prominence": "high | medium | low"
  }}
- forehead: {{
    "height_category": "low | medium | high | unknown"
  }}
- hair: {{
    "hair_density": "low | medium | high | unknown",
    "hair_texture": "straight | wavy | curly | coily | unknown"
  }}
- skin: {{
    "skin_tone": a coarse tone like "fair", "medium", "tan", "deep",
    "skin_undertone": "cool | warm | neutral"
  }}
- body_type: overall body type (ectomorph, mesomorph, endomorph, average, etc.)
- season: current season (winter, spring, summer, fall)
- location: user's location (consider climate and local fashion)
- age: user's age (use this to ensure age-appropriate styling)

IMPORTANT OUTFIT REQUIREMENTS:
- You MUST include exactly THREE outfit types: "casual", "smart-casual", and "formal"
- ALL three outfits MUST be season-appropriate AND location-appropriate AND age-appropriate:
  * Winter: Consider location climate - tropical locations need lighter layers, cold locations need heavy insulation
  * Spring: Light layers, transitional pieces - adjust based on location's spring climate
  * Summer: Light fabrics, breathable materials - tropical locations may need year-round summer styles
  * Fall: Medium layers, cozy pieces - adjust for location's fall climate
- Location considerations: Urban areas may prefer trendier items, coastal areas need humidity-resistant fabrics, desert areas need temperature-regulating layers
- Age considerations: Ensure all outfits are age-appropriate (teens = trendier, mature adults = more refined)
- Each outfit suggestion should include specific items that are season-appropriate, location-appropriate, and age-appropriate

Important:
- If a field is missing or "unknown", make a reasonable, neutral recommendation and do not mention that the data is missing.
- For forehead/forehead_height_category, if it is "unknown", do NOT base your hairstyle solely on forehead height.

Use the following output format and return ONLY valid JSON (no backticks, no extra text):

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
      "age": {age if age is not None else "null"}
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert stylist and grooming consultant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
    )

    response_text = response.choices[0].message.content.strip()
    # Strip code fences if present
    response_text = re.sub(r"^```json\s*|^```\s*|```$", "", response_text, flags=re.IGNORECASE).strip()

    # Try to find the first '{' to skip any stray preamble
    json_start = response_text.find("{")
    if json_start != -1:
        response_text = response_text[json_start:]

    import json as _json
    try:
        suggestions = _json.loads(response_text)
        print("suggestions from openAI:", suggestions)
    except _json.JSONDecodeError:
        # Fallback if LLM doesn’t return proper JSON
        suggestions = {
            "hairstyle": {
                "style": "medium layered haircut",
                "description": "Fallback suggestion because the AI response was not valid JSON.",
            },
            "beard": {
                "style": "light stubble",
                "description": "Safe, versatile beard suggestion.",
            },
            "outfit": {
                "suggestions": [
                    {
                        "type": "casual",
                        "season": get_current_season(),
                        "location": location or "general",
                        "age": age if age is not None else None,
                        "items": [
                            "comfortable t-shirt or casual shirt",
                            "jeans or casual pants",
                            "sneakers or casual shoes",
                        ],
                        "description": "Casual outfit for hanging out with friends"
                    },
                    {
                        "type": "smart-casual",
                        "season": get_current_season(),
                        "location": location or "general",
                        "age": age if age is not None else None,
                        "items": [
                            "well-fitted shirt or polo",
                            "dark jeans or chinos",
                            "minimal sneakers or casual loafers",
                        ],
                        "description": "Smart-casual outfit for semi-formal occasions"
                    },
                    {
                        "type": "formal",
                        "season": get_current_season(),
                        "location": location or "general",
                        "age": age if age is not None else None,
                        "items": [
                            "dress shirt and suit jacket",
                            "dress pants or suit pants",
                            "dress shoes",
                        ],
                        "description": "Formal outfit for business or formal events"
                    }
                ]
            },
            "skin_tone": skin_tone,
            "explanation": response_text,
            "gender": str(gender),
        }

    # Ensure skin_tone and gender fields are filled even if model omitted them
    # suggestions.setdefault("skin_tone", skin_tone)
    # suggestions.setdefault("gender", str(gender))

    return suggestions


# ============================
# 1. FACIAL GEOMETRY HELPERS
# ============================

def _get_landmark(face: Dict[str, Any], name: str) -> Optional[Dict[str, float]]:
    """
    Safely get a landmark by Type from Rekognition FaceDetails.
    Returns dict with keys X, Y if found, else None.
    """
    for lm in face.get("Landmarks", []):
        if lm.get("Type") == name:
            return lm
    return None


def _dist(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Euclidean distance between two normalized landmarks."""
    return math.hypot(a["X"] - b["X"], a["Y"] - b["Y"])


def _classify_face_shape(
    aspect_ratio: float,
    cheek_width: Optional[float],
    jaw_width: Optional[float],
    forehead_width: Optional[float],
) -> str:
    """
    Heuristic classification into common face shapes using a few ratios.

    aspect_ratio ~ face_height / face_width
    widths are normalized distances between left/right points.
    """
    # Default when data is missing
    if cheek_width is None or jaw_width is None or forehead_width is None:
        if aspect_ratio > 1.35:
            return "rectangle"
        elif aspect_ratio < 1.1:
            return "round"
        else:
            return "oval"

    cheek_to_jaw = cheek_width / jaw_width if jaw_width and jaw_width > 0 else 1.0
    forehead_to_jaw = forehead_width / jaw_width if jaw_width and jaw_width > 0 else 1.0

    # Very tall, not super wide → oblong / rectangle
    if aspect_ratio > 1.4:
        return "oblong"
    # Broader than tall-ish and soft → round
    if aspect_ratio < 1.15 and abs(cheek_to_jaw - 1.0) < 0.08:
        return "round"
    # Cheekbones clearly widest
    if cheek_to_jaw > 1.1 and abs(forehead_to_jaw - 1.0) < 0.08:
        return "diamond"
    # Forehead distinctly wider than jaw
    if forehead_to_jaw > 1.08 and cheek_to_jaw >= 1.0:
        return "heart"
    # Jaw noticeably wider than forehead
    if forehead_to_jaw < 0.92 and cheek_to_jaw <= 1.0:
        return "triangle"
    # Between square and oval → use aspect ratio
    if 1.15 <= aspect_ratio <= 1.35:
        # Slightly taller → oval, otherwise square
        return "oval" if aspect_ratio > 1.23 else "square"

    # Fallback
    return "oval"


def _estimate_jawline_metrics(face: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use jawline landmarks to estimate jawline strength and chin shape.
    """
    upper_left = _get_landmark(face, "upperJawlineLeft")
    upper_right = _get_landmark(face, "upperJawlineRight")
    mid_left = _get_landmark(face, "midJawlineLeft")
    mid_right = _get_landmark(face, "midJawlineRight")
    chin = _get_landmark(face, "chinBottom")

    metrics = {
        "jaw_width": None,
        "jaw_strength": "unknown",  # strong / medium / soft
        "chin_shape": "unknown",    # pointed / rounded / square (approx)
    }

    if upper_left and upper_right:
        jaw_width = _dist(upper_left, upper_right)
        metrics["jaw_width"] = jaw_width

    # Jaw strength: primarily based on width (very crude)
    if metrics["jaw_width"]:
        if metrics["jaw_width"] > 0.23:
            metrics["jaw_strength"] = "strong"
        elif metrics["jaw_width"] > 0.18:
            metrics["jaw_strength"] = "medium"
        else:
            metrics["jaw_strength"] = "soft"

    # Chin shape: vertical vs horizontal proportions near chin
    mouth_down = _get_landmark(face, "mouthDown")
    if chin and mouth_down:
        vertical = abs(chin["Y"] - mouth_down["Y"])
        if mid_left and mid_right:
            chin_width = _dist(mid_left, mid_right)
        else:
            chin_width = None

        if chin_width and vertical:
            ratio = vertical / chin_width
            if ratio > 0.7:
                metrics["chin_shape"] = "pointed"
            elif ratio < 0.45:
                metrics["chin_shape"] = "square"
            else:
                metrics["chin_shape"] = "rounded"

    return metrics


def _estimate_cheekbone_metrics(face: Dict[str, Any]) -> Dict[str, Any]:
    """
    Approximate cheekbone prominence using cheek vs jaw vs forehead widths.
    """
    # Use eyebrow outer corners as forehead-ish width
    brow_left = _get_landmark(face, "leftEyeBrowLeft")
    brow_right = _get_landmark(face, "rightEyeBrowRight")

    # Mid-jawline for lower width
    mid_left = _get_landmark(face, "midJawlineLeft")
    mid_right = _get_landmark(face, "midJawlineRight")

    # Mouth corners as cheek-ish (mid-face) width
    mouth_left = _get_landmark(face, "mouthLeft")
    mouth_right = _get_landmark(face, "mouthRight")

    forehead_width = _dist(brow_left, brow_right) if (brow_left and brow_right) else None
    cheek_width = _dist(mouth_left, mouth_right) if (mouth_left and mouth_right) else None
    jaw_width = _dist(mid_left, mid_right) if (mid_left and mid_right) else None

    prominence = "unknown"
    if cheek_width and jaw_width:
        cheek_to_jaw = cheek_width / jaw_width
        if cheek_to_jaw > 1.1:
            prominence = "high"
        elif cheek_to_jaw > 0.98:
            prominence = "medium"
        else:
            prominence = "low"

    return {
        "forehead_width": forehead_width,
        "cheek_width": cheek_width,
        "jaw_width_for_cheek": jaw_width,
        "cheekbone_prominence": prominence,
    }


def _estimate_forehead_metrics(face: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate forehead height relative to face height using eyebrow position
    and the top of the bounding box. If the face is heavily occluded (e.g. hair down),
    we may mark the height as 'unknown'.
    """
    bbox = face.get("BoundingBox", {})
    top_y = bbox.get("Top", 0.0)
    face_height = bbox.get("Height", 1.0) or 1.0

    brow_up_left = _get_landmark(face, "leftEyeBrowUp")
    brow_up_right = _get_landmark(face, "rightEyeBrowUp")

    if brow_up_left and brow_up_right:
        avg_brow_y = (brow_up_left["Y"] + brow_up_right["Y"]) / 2.0
    else:
        # Fall back to eye center if brow is missing
        eye_left = _get_landmark(face, "eyeLeft")
        eye_right = _get_landmark(face, "eyeRight")
        if eye_left and eye_right:
            avg_brow_y = (eye_left["Y"] + eye_right["Y"]) / 2.0
        else:
            avg_brow_y = top_y + 0.2 * face_height  # crude fallback

    forehead_height = max(0.0, avg_brow_y - top_y)
    ratio = forehead_height / face_height if face_height > 0 else 0.3

    occluded = face.get("FaceOccluded", {}).get("Value", False)

    # If occluded (hair/objects) and ratio is extremely small,
    # treat this as unreliable instead of forcing "low".
    if occluded and ratio < 0.18:
        height_category = "unknown"
    else:
        if ratio < 0.22:
            height_category = "low"
        elif ratio > 0.32:
            height_category = "high"
        else:
            height_category = "medium"

    hairline_shape = "unknown"  # needs a dedicated model to be meaningful

    return {
        "forehead_height_ratio": ratio,
        "forehead_height_category": height_category,
        "hairline_shape": hairline_shape,
    }


def _estimate_hair_metrics(face: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for hair density/texture.
    Rekognition landmarks do NOT provide robust hair data.
    """
    return {
        "hair_density": "unknown",  # "low" / "medium" / "high" (TODO)
        "hair_texture": "unknown",  # "straight" / "wavy" / "curly" / "coily" (TODO)
    }


def _estimate_skin_tone_and_undertone(face: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rekognition doesn't expose raw pixel colors here, so we can't compute a
    real undertone. For now, keep a coarse default and add an 'undertone' placeholder.
    """
    return {
        "skin_tone": "medium",       # TODO: replace with real classifier
        "skin_undertone": "neutral", # "cool" / "warm" / "neutral" (TODO)
    }


def extract_high_impact_face_metrics(face: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the 6 key metrics bundle from Rekognition FaceDetails.
    """
    bbox = face.get("BoundingBox", {})
    face_width = bbox.get("Width", 1.0) or 1.0
    face_height = bbox.get("Height", 1.0) or 1.0
    aspect_ratio = face_height / face_width if face_width > 0 else 1.0

    # Jaw & chin
    jaw_metrics = _estimate_jawline_metrics(face)
    # Cheekbones / widths
    cheek_metrics = _estimate_cheekbone_metrics(face)
    # Forehead
    forehead_metrics = _estimate_forehead_metrics(face)
    # Hair (stub)
    hair_metrics = _estimate_hair_metrics(face)
    # Skin tone + undertone (stub)
    skin_metrics = _estimate_skin_tone_and_undertone(face)

    face_shape = _classify_face_shape(
        aspect_ratio=aspect_ratio,
        cheek_width=cheek_metrics.get("cheek_width"),
        jaw_width=cheek_metrics.get("jaw_width_for_cheek") or jaw_metrics.get("jaw_width"),
        forehead_width=cheek_metrics.get("forehead_width"),
    )

    return {
        # 1) Face shape (refined)
        "face_shape_detailed": face_shape,

        # 2) Jawline definition + chin shape
        "jawline": {
            "width": jaw_metrics.get("jaw_width"),
            "strength": jaw_metrics.get("jaw_strength"),
            "chin_shape": jaw_metrics.get("chin_shape"),
        },

        # 3) Cheekbone prominence
        "cheekbones": {
            "width": cheek_metrics.get("cheek_width"),
            "prominence": cheek_metrics.get("cheekbone_prominence"),
        },

        # 4) Forehead height + hairline
        "forehead": {
            "height_ratio": forehead_metrics.get("forehead_height_ratio"),
            "height_category": forehead_metrics.get("forehead_height_category"),
            "hairline_shape": forehead_metrics.get("hairline_shape"),
        },

        # 5) Hair density + texture (stub)
        "hair": hair_metrics,

        # 6) Skin tone + undertone
        "skin": skin_metrics,

        # Extra: aspect ratio for debugging
        "face_aspect_ratio": aspect_ratio,
    }


# ============================
# 2. IMAGE ANALYSIS + FEATURES
# ============================

def analyze_image_and_generate_features(image_path: str) -> Dict[str, Any]:
    """
    If image_path is a URL (uploaded), use AWS Rekognition.
    If image_path is local (like sample.png), read from local and upload to S3 temporarily for Rekognition.
    """
    if image_path.startswith("http"):
        # extract bucket/key from URL
        bucket_name = os.getenv("S3_BUCKET")
        parsed = urlparse(image_path)
        key = parsed.path.lstrip("/")  # removes leading "/"
        print("getting object from S3:")
    else:
        # Local file path
        base_dir = os.path.dirname(__file__)
        full_path = os.path.join(base_dir, image_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Image not found: {full_path}")
        print("uploading to S3:")
        # Upload to S3/MinIO first so Rekognition can read it
        s3 = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            endpoint_url=os.getenv("S3_ENDPOINT"),
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
        )
        bucket_name = os.getenv("S3_BUCKET")
        key = f"temp/{image_path}"
        with open(full_path, "rb") as f:
            s3.upload_fileobj(f, bucket_name, key)

    # Call Rekognition
    rekognition = boto3.client(
        "rekognition",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    response = rekognition.detect_faces(
        Image={"S3Object": {"Bucket": bucket_name, "Name": key}},
        Attributes=["ALL"],
    )

    if not response["FaceDetails"]:
        raise ValueError("No face detected in the image.")

    print("Rekognition DetectFaces Response:", response)

    face = response["FaceDetails"][0]

    # Legacy/basic app features (kept for backward compatibility)
    app_features_basic = {
        "face_shape": "oval" if face["BoundingBox"]["Width"] < 0.4 else "round",
        "facial_hair_suitability": "high" if face.get("Beard", {}).get("Value") else "low",
        "skin_tone": "medium",  # placeholder
        "hair_texture": "straight",  # placeholder
        "gender": face.get("Gender", {}).get("Value", "Unknown"),
    }

    # NEW: high-impact metrics
    high_impact = extract_high_impact_face_metrics(face)

    # Merge with Rekognition face details for richer data
    combined_features = {
        **face,               # raw Rekognition details
        **app_features_basic, # legacy fields
        **high_impact,        # detailed geometry & skin/hair metrics
    }

    return combined_features


def dummy():
    # Intentionally left as a no-op to preserve original symbol
    return


# ============================
# 3. RULE-BASED SUGGESTIONS
# ============================

# def generate_suggestions(face_data: dict, body_type: str) -> dict:
#     # ---- Raw Rekognition / legacy fields ----
#     print("Face Data:", face_data)
#     age_low = face_data.get("AgeRange", {}).get("Low", 25)
#     age_high = face_data.get("AgeRange", {}).get("High", 35)
#     smile = face_data.get("Smile", {}).get("Value", False)
#     eyeglasses = face_data.get("Eyeglasses", {}).get("Value", False)
#     eyesopen = face_data.get("EyesOpen", {}).get("Value", False)
#     beard_detected = face_data.get("Beard", {}).get("Value", False)
#     gender = face_data.get("Gender", {}).get("Value", face_data.get("gender", "Unknown"))

#     # ---- New high-impact metrics with safe fallbacks ----
#     # Face shape
#     face_shape_detailed = face_data.get("face_shape_detailed")
#     base_face_shape = face_data.get("FaceShape", {}).get("Value", "Oval")
#     face_shape = (face_shape_detailed or base_face_shape or "Oval").lower()

#     # Jawline & chin
#     jaw_info = face_data.get("jawline", {}) or {}
#     jaw_strength = jaw_info.get("strength", "unknown")           # strong / medium / soft
#     chin_shape = jaw_info.get("chin_shape", "unknown")           # pointed / rounded / square

#     # Cheekbones
#     cheek_info = face_data.get("cheekbones", {}) or {}
#     cheek_prominence = cheek_info.get("prominence", "unknown")   # high / medium / low

#     # Forehead
#     forehead_info = face_data.get("forehead", {}) or {}
#     forehead_height_category = forehead_info.get("height_category", "medium")  # low / medium / high / unknown
#     hairline_shape = forehead_info.get("hairline_shape", "unknown")           # placeholder

#     # Hair
#     hair_info = face_data.get("hair", {}) or {}
#     hair_density = hair_info.get("hair_density", "unknown")      # low / medium / high / unknown
#     hair_texture = hair_info.get("hair_texture",
#                                  face_data.get("hair_texture", "unknown"))  # straight / wavy / curly / coily

#     # Skin
#     skin_info = face_data.get("skin", {}) or {}
#     skin_tone = skin_info.get("skin_tone", face_data.get("skin_tone", "medium"))
#     skin_undertone = skin_info.get("skin_undertone", "neutral")  # warm / cool / neutral

#     # ======================
#     # Hairstyle suggestion
#     # ======================

#     # Base style from detailed face shape
#     hairstyle_base_map = {
#         "oval": "medium layered haircut with balanced volume",
#         "square": "short textured crop with softer edges to avoid extra boxiness",
#         "round": "longer on top with a taper or fade on the sides to add height",
#         "heart": "side-part with volume around the temples to balance a wider forehead",
#         "triangle": "fuller sides and a bit of volume on top to balance a stronger jaw",
#         "diamond": "medium length with fullness at the crown and softer sides to reduce cheek width",
#         "oblong": "medium length with minimal extra height on top to avoid elongating the face",
#         "rectangle": "medium length with low vertical volume and some width at the sides",
#     }
#     hairstyle = hairstyle_base_map.get(face_shape, "classic clean, medium-length style")

#     # Adjust for forehead height and hairline, **only if not unknown**
#     if forehead_height_category == "high":
#         hairstyle += " and a light fringe or forward styling to soften a higher forehead"
#     elif forehead_height_category == "low":
#         hairstyle += " with the hair styled upward or back to open up the face"
#     # if "unknown": do nothing special

#     if hairline_shape in ["widows_peak", "straight"]:
#         hairstyle += " while respecting your natural hairline rather than fighting it"

#     # Adjust for hair density
#     if hair_density == "low":
#         hairstyle += " avoiding extremely tight fades to keep the scalp from showing through"
#     elif hair_density == "high":
#         hairstyle += " with some texturizing to reduce bulk and make styling easier"

#     # Adjust for hair texture
#     if hair_texture in ["wavy", "curly"]:
#         hairstyle += " that works with your natural waves/curls using layered, shape-focused cuts"
#     elif hair_texture == "coily":
#         hairstyle += " with shape-focused, coil-friendly structure rather than trying to straighten everything"

#     # ======================
#     # Beard suggestion
#     # ======================
#     if gender and str(gender).lower().startswith("f"):
#         # if Rekognition labels as female, default to no beard rec
#         beard = "no beard recommendation (focus on hair and outfit instead)"
#     else:
#         if beard_detected:
#             # Already has facial hair → tune based on jaw + chin
#             if jaw_strength == "soft":
#                 beard = "short boxed beard to carve in more jaw definition"
#             elif jaw_strength == "strong":
#                 # already a strong jaw, don't over-bulk it
#                 beard = "light to medium stubble to keep definition without adding too much bulk"
#             else:
#                 beard = "neatly maintained stubble, shaped along the natural jawline"
#         else:
#             # No beard currently → suggestion based on jaw/chin
#             if jaw_strength == "soft":
#                 beard = "try short stubble or a short boxed beard to give the jaw more structure"
#             elif chin_shape == "pointed":
#                 beard = "a slightly fuller goatee or rounded beard to visually soften a very pointed chin"
#             else:
#                 beard = "clean-shaven or short stubble for a sharp, low-maintenance look"

#     # ======================
#     # Outfit + color palette
#     # ======================
#     if body_type in ["ectomorph", "mesomorph"]:
#         outfit = "v-neck or crew-neck shirts, structured jackets, and slim/straight-fit jeans or chinos"
#     elif body_type == "average":
#         outfit = "tailored shirts, vertical stripes, and mid-to-dark tones to streamline the silhouette"
#     else:
#         outfit = "well-fitted basics (not too tight, not baggy) with layering pieces like overshirts or light jackets"

#     # Color palette from tone + undertone
#     base_palette_map = {
#         "fair": ["navy", "charcoal", "olive"],
#         "medium": ["white", "beige", "burgundy"],
#         "tan": ["cream", "forest green", "rust"],
#         "deep": ["pastel blue", "gray", "tan"],
#     }
#     base_palette = base_palette_map.get(skin_tone, ["black", "white", "navy"])

#     if skin_undertone == "warm":
#         base_palette = [c for c in base_palette if c not in ["gray"]] + ["mustard", "warm brown"]
#     elif skin_undertone == "cool":
#         base_palette = [c for c in base_palette if c not in ["mustard", "rust"]] + ["cool blue", "true red"]

#     # ======================
#     # Explanation string
#     # ======================
#     explanation = (
#         f"Face shape: {face_shape} → hairstyle: {hairstyle}. "
#         f"Jawline: strength={jaw_strength}, chin={chin_shape} → beard suggestion: {beard}. "
#         f"Cheekbone prominence: {cheek_prominence}; forehead height: {forehead_height_category}; "
#         f"hairline shape: {hairline_shape}. "
#         f"Hair density: {hair_density}, texture: {hair_texture}. "
#         f"Body type: {body_type} → outfit: {outfit}. "
#         f"Skin tone: {skin_tone}, undertone: {skin_undertone} → suggested colors: {', '.join(base_palette)}. "
#         f"Eyeglasses: {'Yes' if eyeglasses else 'No'}; eyes open: {'Yes' if eyesopen else 'No'}; "
#         f"smile: {'Yes' if smile else 'No'}. "
#         f"Gender: {gender}."
#     )

#     return {
#         "hairstyle": hairstyle,
#         "beard": beard,
#         "outfit": outfit,
#         "skin_tone": skin_tone,
#         "color_palette": base_palette,
#         "age_range": {"low": age_low, "high": age_high},
#         "explanation": explanation,
#         "Gender": gender,
#         "used_metrics": {
#             "face_shape_detailed": face_shape_detailed,
#             "jaw_strength": jaw_strength,
#             "chin_shape": chin_shape,
#             "cheek_prominence": cheek_prominence,
#             "forehead_height": forehead_height_category,
#             "hairline_shape": hairline_shape,
#             "hair_density": hair_density,
#             "hair_texture": hair_texture,
#             "skin_tone": skin_tone,
#             "skin_undertone": skin_undertone,
#         },
#     }


# ============================
# 4. EXAMPLE RUNNER
# ============================

if __name__ == "__main__":
    print("calling twice:")
    # test_image = "sample_face.jpg"  # Replace with a real image path

    # try:
    #     print("Analyzing image...")
    #     features = analyze_image_and_generate_features(test_image)
    #     print("Detected features:", features)

    #     print("\nGenerating rule-based suggestions...")
    #     suggestions_rule = generate_suggestions(features, body_type="mesomorph")
    #     print("\n--- Rule-based Personal Style Suggestions ---")
    #     for key, val in suggestions_rule.items():
    #         print(f"{key.capitalize()}: {val}")

    #     print("\nGenerating LLM-based suggestions...")
    #     suggestions_llm = generate_suggestions_with_llm(features, body_type="mesomorph")
    #     print("\n--- LLM-based Personal Style Suggestions ---")
    #     print(suggestions_llm)

    # except FileNotFoundError as e:
    #     print(e)
