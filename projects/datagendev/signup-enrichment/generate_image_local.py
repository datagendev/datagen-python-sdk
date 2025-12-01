import google.generativeai as genai
import os
from PIL import Image
from io import BytesIO

# User provided API key
API_KEY = "AIzaSyBnh1meqyRrKh72gFdORz5KBCbA0nJagVo"
genai.configure(api_key=API_KEY)

def generate_image(prompt, output_file):
    print(f"Generating image with prompt: {prompt}")
    
    # Try gemini-2.5-flash-image first
    model_name = 'models/gemini-2.5-flash-image'
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_data = part.inline_data.data # bytes
                    img = Image.open(BytesIO(img_data))
                    img.save(output_file)
                    print(f"Image saved to {output_file}")
                    return True
        
        print("No image found in response.")
        print(response)
        
    except Exception as e:
        print(f"Error generating image: {e}")
        return False

# Prompt based on the specific Mermaid flow content
prompt = """
Create a professional, high-quality technical diagram visualizing the following architecture workflow:

1. **Universal Interface (Entry Points)**: Show three distinct users entering the system:
   - "AI Agent" (using MCP)
   - "Developer" (using SDK)
   - "Builder" (using UI)

2. **Tool Discovery**: The Agent path flows into a "Discovery" phase (Search Tools -> Get Details).

3. **Unified Execution Engine**: All three paths (Agent, Developer, Builder) converge into a central "Unified Execution Engine".

4. **Zero-Touch Auth Loop**: The Engine connects to a "Managed MCP Server". Show a loop for Authentication:
   - If Authenticated -> Success (Green path)
   - If 401 Error -> "User Connects Service" -> Retry (Red/Orange path looping back)

Style: Modern flat design, isometric view, tech-blue, purple and mint-green color palette. Clean white background. Professional software architecture diagram style.
"""

output_file = "datagen_workflow_flowchart.png"

generate_image(prompt, output_file)
