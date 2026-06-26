import os
from time import sleep
from google import genai
from google.genai import types
import itertools
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

key_iterator = itertools.cycle(config.gemini_api_keys)

class Agent:
    prompt_store = None

    def __init__(self) -> None:
        self.model_name = config.llm

    # MODIFICATION: we use a json schema
    def send_message(self, messages, response_schema=None):
        worked = 0
        sleep_time = 1
        
        system_instruction = None
        gemini_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
                )

        while worked == 0:
            current_key = next(key_iterator)
            client = genai.Client(api_key=current_key)
            
            try:
                gen_config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,
                    safety_settings=[
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    ]
                )

                # MODIFICATION:
                # use the google schemas to never worry about wrong jsons again
                if response_schema:
                    gen_config.response_mime_type = "application/json"
                    gen_config.response_schema = response_schema

                response = client.models.generate_content(
                    model=self.model_name,
                    contents=gemini_messages,
                    config=gen_config
                )
                text = response.text
                worked = 1
            except Exception as e:
                print(f"\n[API Error with Key {current_key[:10]}...] {e}")
                sleep(sleep_time)
                sleep_time = min(sleep_time + 1, 5) 

        return text
    
    def get_action_shorthands(self):
        sh = []
        for action in self.get_actions():
            actor = action.split("|")[0].strip()
            description = action.split("|")[3].strip()
            sh.append(actor + " , " + description)
        return sh

    def parse(self, text):
        return self.send_message(self.prompt_store.get_project_init_prompt(text))