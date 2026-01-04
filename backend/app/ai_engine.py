from typing import Dict, Any
import random
import os
import boto3
import re
from urllib.parse import urlparse

from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_suggestions_with_llm(face_data: dict, body_type: str) -> dict:
    prompt = f"""
    You are a professional AI stylist. 
    Given the following facial and body details, suggest a hairstyle, beard style, and outfit ideas.

    Face Data: {face_data}

    Body Type: {body_type}

    Gender Data: {face_data.get("gender", "Unknown")}

    Skin Tone: {face_data.get("skin_tone", "medium")}

    Provide **only valid JSON** with the following structure:

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
                "type": "string",
                "items": ["string"]
            }}
        ]
    }},
    "skin_tone": "string",
    "explanation": "string"
    
    "gender": "string"
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
    response_text = re.sub(r"^```json\s*|```$", "", response_text, flags=re.IGNORECASE).strip()

    
    json_start = response_text.find("{")
    if json_start != -1:
        response_text = response_text[json_start:]
    else:
        response_text = response_text 

    # Parse JSON safely
    import json
    try:
        suggestions = json.loads(response_text)
    except json.JSONDecodeError:
        # fallback if LLM doesn’t return proper JSON
        suggestions = {
            "hairstyle": "sample - medium layered haircut",
            "beard": "sample - stubble",
            "outfit": "sample - tailored shirts, vertical stripes, darker tones",
            "skin_tone": "sample - medium",
            "explanation": response_text,
        }
    return suggestions
    
    # return {
    #     "hairstyle": suggestions.hairstyle.style,
    #     "beard": suggestions.beard.style,
    #     "outfit": suggestions.outfit.style,
    #     "explanation": suggestions,
    # }


def analyze_image_and_generate_features(image_path: str) -> Dict[str, Any]:
    """
    If image_path is a URL (uploaded), use AWS Rekognition.
    If image_path is local (like sample.png), read from local and upload to S3 temporarily for Rekognition.
    """
    if image_path.startswith("http"):
        # extract bucket/key from URL
        bucket_name = os.getenv("S3_BUCKET")
        # key = image_path.split(f"{bucket_name}/")[-1]
        parsed = urlparse(image_path)
        key = parsed.path.lstrip("/")  # removes leading "/"
    else:
        # Local file path
        base_dir = os.path.dirname(__file__)
        full_path = os.path.join(base_dir, image_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Image not found: {full_path}")

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

    # Map to your app features
    app_features = {
        "face_shape": "oval" if face["BoundingBox"]["Width"] < 0.4 else "round",
        "facial_hair_suitability": "high" if face.get("Beard", {}).get("Value") else "low",
        "skin_tone": "medium",  # you can refine
        "hair_texture": "straight",  # Rekognition doesn’t provide this
        "gender": face.get("Gender", {}).get("Value", "Unknown"),
        #"gender": face_data.get("Gender", {}).get("Value", "Unknown")


    }

    print("Detected Gender:", app_features["gender"])

    # Merge with Rekognition face details for richer data
    combined_features = {**face, **app_features}

    return combined_features

def dummy() :
    # rekognition = boto3.client("rekognition", region_name="us-east-1")
    # def analyze_image_and_generate_features(image_path: str):

    #     # resolve path relative to this file
    #     base_dir = os.path.dirname(__file__)  # folder of ai_engine.py
    #     full_path = os.path.join(base_dir, image_path)

    #     if not os.path.exists(full_path):
    #         raise FileNotFoundError(f"Image not found: {full_path}")

    #     with open(full_path, "rb") as image:
    #         response = rekognition.detect_faces(
    #             Image={'Bytes': image.read()},
    #             Attributes=['ALL']
    #         )

    #     if not response["FaceDetails"]:
    #         raise ValueError("No face detected in the image")

    #     face = response["FaceDetails"][0]
    #     return {
    #         "face_shape": "oval" if face["Confidence"] > 90 else "round",
    #         "facial_hair_suitability": "high" if face.get("Beard", {}).get("Value") else "low",
    #         "skin_tone": "medium",
    #         "hair_texture": "wavy",
    #     }



    # # -----------------------------
    # # 1. Image Analysis (Placeholder)
    # # -----------------------------
    # def analyze_image_and_generate_features(image_path: str) -> Dict[str, Any]:
    #     """
    #     Simulates AI-based facial analysis.
    #     In production, replace with OpenCV or DeepFace pipeline.
    #     """
    #     # resolve path relative to this file
    #     base_dir = os.path.dirname(__file__)  # folder of ai_engine.py
    #     full_path = os.path.join(base_dir, image_path)

    #     if not os.path.exists(full_path):
    #         raise FileNotFoundError(f"Image not found: {full_path}")

    #     # Placeholder facial analysis results
    #     return {
    #         "face_shape": random.choice(["oval", "square", "round", "heart"]),
    #         "facial_hair_suitability": random.choice(["high", "medium", "low"]),
    #         "skin_tone": random.choice(["fair", "medium", "dark"]),
    #         "hair_texture": random.choice(["straight", "wavy", "curly"]),
    #     }

    # -----------------------------
    # 2. Suggestion Generator
    # -----------------------------
    # def generate_suggestions(features: Dict[str, Any], body_type: str = None) -> Dict[str, Any]:
    #     """
    #     Generates styling suggestions from facial and body features.
    #     Replace rule-based logic with a model or LLM API for better recommendations.
    #     """
    #     face_shape = features.get("face_shape", "xxx")
    #     facial_hair_suitability = features.get("facial_hair_suitability", "yyy")
    #     skin_tone = features.get("skin_tone", "zzzz")
    #     hair_texture = features.get("hair_texture", "aaaa")

    #     # Hair and beard rules
    #     hairstyle_map = {
    #         "oval": "medium layered haircut",
    #         "square": "short textured crop",
    #         "round": "long on top fade",
    #         "heart": "side-part with volume"
    #     }
    #     hairstyle = hairstyle_map.get(face_shape, "classic clean style")

    #     beard_style = "stubble" if facial_hair_suitability == "high" else (
    #         "short boxed beard" if facial_hair_suitability == "medium" else "clean-shaven"
    #     )

    #     # Outfit recommendations
    #     if body_type in ["ectomorph", "mesomorph"]:
    #         outfit = "v-neck shirts, structured jackets, and slim jeans"
    #     else:
    #         outfit = "tailored shirts, vertical stripes, and darker tones"

    #     # Color palette suggestion
    #     color_map = {
    #         "fair": ["navy", "charcoal", "olive"],
    #         "medium": ["white", "beige", "burgundy"],
    #         "dark": ["pastel", "gray", "tan"]
    #     }
    #     color_palette = color_map.get(skin_tone, ["black", "white"])

    #     return {
    #         "hairstyle": hairstyle,
    #         "beard": beard_style,
    #         "outfit": outfit,
    #         "recommended_colors": color_palette,
    #         "explanation": (
    #             f"Face shape: {face_shape} → {hairstyle}. "
    #             f"Facial hair: {facial_hair_suitability} → {beard_style}. "
    #             f"Body type: {body_type or 'not specified'} → {outfit}. "
    #             f"Skin tone: {skin_tone} → try colors {', '.join(color_palette)}."
    #         )
    #     }
    return

def generate_suggestions(face_data: dict, body_type: str) -> dict:
    # Extract values safely
    print("Face Data:", face_data)
    age_low = face_data.get("AgeRange", {}).get("Low", 25)
    age_high = face_data.get("AgeRange", {}).get("High", 35)
    smile = face_data.get("Smile", {}).get("Value", False)
    eyeglasses = face_data.get("Eyeglasses", {}).get("Value", False)
    eyesopen = face_data.get("EyesOpen", {}).get("Value", False)
    beard_detected = face_data.get("Beard", {}).get("Value", False)
    face_shape = face_data.get("FaceShape", {}).get("Value", "Oval")
    gender = face_data.get("Gender", {}).get("Value", "Unknown")


    # Simple rule-based suggestions
    hairstyle = "medium layered haircut" if face_shape == "Oval" else "classic cut"
    beard = "stubble" if beard_detected else "clean"
    outfit = "tailored shirts, vertical stripes, darker tones" if body_type == "average" else "casual wear"
    skin_tone = "medium"  # could be refined if SkinTone is available


    explanation = (
        f"Face shape: {face_shape} → {hairstyle}. "
        f"Facial hair: {'high' if beard_detected else 'low'} → {beard}. "
        f"Body type: {body_type} → {outfit}. "
        f"Skin tone: {skin_tone} → try colors white, beige, burgundy. "
        f"Eyeglasses: {'Yes' if eyeglasses else 'No'};  eyesopen: {'Yes' if eyesopen else 'No'}; Smile: {'Yes' if smile else 'No'}"
        f"Gender: {gender}. "
    )

    return {
        "hairstyle": hairstyle,
        "beard": beard,
        "outfit": outfit,
        "skin_tone": skin_tone,
        "age_range": {"low": age_low, "high": age_high},
        "explanation": explanation,
        "Gender": gender
    }


# -----------------------------
# 3. Example Runner
# -----------------------------
if __name__ == "__main__":
    test_image = "sample_face.jpg"  # Replace with a real image path

    # try:
    #     print("Analyzing image...")
    #     features = analyze_image_and_generate_features(test_image)
    #     print("Detected features:", features)

    #     print("\nGenerating suggestions...")
    #     suggestions = generate_suggestions(features, body_type="mesomorph")

    #     print("\n--- Personal Style Suggestions ---")
    #     for key, val in suggestions.items():
    #         print(f"{key.capitalize()}: {val}")

    # except FileNotFoundError as e:
    #     print(e)
# def generate_chat_response(user_message: str) -> str:
    #"""
   # Simple chat endpoint for your ChatBox.
    #Takes user text → sends to OpenAI → returns response string.
    #"""

    #response = client.chat.completions.create(
       # model="gpt-4o-mini",
      #  messages=[
       #     {"role": "system", "content": "You are an AI stylist assistant."},
       #     {"role": "user", "content": user_message}
       # ],
       # temperature=0.7,
   # )

    #return response.choices[0].message.content.strip()