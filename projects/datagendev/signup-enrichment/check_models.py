import google.generativeai as genai
import os

# User provided API key
API_KEY = "AIzaSyBnh1meqyRrKh72gFdORz5KBCbA0nJagVo"
genai.configure(api_key=API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Content Generation Model: {m.name}")
        if 'generateImages' in m.supported_generation_methods: # hypothetical method check
            print(f"Image Generation Model: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

# Try to check if Imagen is available directly
try:
    from google.generativeai import ImageGenerationModel
    print("ImageGenerationModel class is available.")
except ImportError:
    print("ImageGenerationModel class is NOT available in this SDK version.")
