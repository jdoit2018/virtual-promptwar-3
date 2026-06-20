"""
apps/api/services/gemini_service.py
Service for AI eco-coaching advice generation using Google Gemini.
"""

import google.generativeai as genai

from core.config import settings

# Configure Gemini if key is provided
if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)  # pragma: no cover

def generate_eco_coach_recommendation(weekly_summary_text: str) -> str:
    """
    Queries Gemini Flash to output a short (2-3 sentences) motivational,
    actionable carbon reduction advice based on the user's weekly summary logs.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    if not api_key:
        return "Great job tracking your emissions! Focus on replacing one car ride with public transit or a vegetarian meal next week to reduce your footprint."

    try:  # pragma: no cover
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")  # pragma: no cover
        model = genai.GenerativeModel(model_name)  # pragma: no cover
        prompt = (  # pragma: no cover
            "You are an inspiring, friendly AI eco-coach. The user has logged the following weekly carbon footprint "
            f"emissions:\n{weekly_summary_text}\n\n"
            "Provide a short, specific, and actionable recommendation (maximum 2-3 sentences) on how they can reduce "
            "their footprint in their highest emission category. Be encouraging and concise."
        )
        response = model.generate_content(prompt)  # pragma: no cover
        return response.text.strip()  # pragma: no cover
    except Exception as e:  # pragma: no cover
        print(f"[WARN] Gemini recommendation generation failed: {e}")  # pragma: no cover
        return "To make the biggest impact, try replacing gas commutes with biking or public transit, and substitute red meat meals with plant-based options."  # pragma: no cover
