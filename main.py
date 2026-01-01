import dotenv
import os
import mcp_server as mcp_s
import mcp_client as mcp_c
import openrouter as ortr
import src.mcp_server as server
import src.tasks as tasks
from google.cloud import *
import s2t as s2t
import datetime as dt
dotenv.load_dotenv() # Load environment variables from .env file


ortr_api_key = os.getenv("ORTR_API_KEY")
ortr_model_full_name = os.getenv("OPENROUTER_MODEL_FULL_NAME")


def 
def initialize_w_gui():
    import src.gui as gui
    

def initialization():
    ortr.init(ortr_api_key)
    ortr.set_default_model(ortr_model_full_name)
    ortr.ChatCompletion.set_default_params({
        "temperature": 0.2,
        "max_new_tokens": 2048,
        "top_p": 0.7,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    })
    print(f"OpenRouter initialized with model {ortr_model_full_name}")
    print("JARVIS AI Assistant - Speech Recognition System")
    print("=" * 60)
    print("\nInitializing wake word detection...")
    print("Say 'Hey Jarvis' to activate\n")
    
    try:
        s2t.main()
    except KeyboardInterrupt:
        print("\n\nShutting down JARVIS...")
if __name__ == "__main__":
    initialization()