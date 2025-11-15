import os
from dotenv import load_dotenv
from google import genai
from prompts import EXPLANATION_SCORING_PROMPT

load_dotenv()
api_key = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")

# Don't raise error immediately, just store the API key status
def has_api_key():
    # Reload environment variables to check for newly saved API keys
    load_dotenv(override=True)
    current_api_key = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
    return bool(current_api_key)

# Only create client if API key is available
client = None
if api_key:
    client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-2.5-flash"

# - - - - - - - - - - - - - - - -

def generate_score(prompt):
    if not has_api_key():
        raise ValueError("API key is required for this operation")
    
    # Reload client if API key was added after startup
    global client
    if not client:
        current_api_key = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
        if current_api_key:
            client = genai.Client(api_key=current_api_key)
        else:
            raise ValueError("API key is required for this operation")
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )
    return response.text
