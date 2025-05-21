import google.generativeai as genai
import requests
from deep_translator import GoogleTranslator
from PIL import Image
from io import BytesIO
import base64
from src.config import settings

# Operações do Gemini
def chat_with_gemini(prompt):
    """Envia prompt para o Gemini e retorna a resposta"""
    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    response = model.generate_content(prompt)
    return response.text

# Operações do Stable Diffusion
def generate_stable_diffusion_image(prompt, width=512, height=512, style_preset=None):
    """Gera imagem a partir de texto"""
    # Tradução automática
    translated_prompt = GoogleTranslator(source="auto", target="en").translate(prompt)

    response = requests.post(
        "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
        headers={
            "Authorization": f"Bearer {settings.STABILITY_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "text_prompts": [{"text": translated_prompt}],
            "cfg_scale": 7,
            "width": width,
            "height": height,
            "samples": 1,
            "steps": 30,
            "style_preset": style_preset
        },
    )

    if response.status_code != 200:
        raise Exception(f"Erro na API: {response.status_code} - {response.text}")

    image_data = base64.b64decode(response.json()["artifacts"][0]["base64"])
    return Image.open(BytesIO(image_data))