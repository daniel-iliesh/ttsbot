import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CambAI:
    def __init__(self):
        self.api_key = os.getenv("CAMB_AI_API_KEY")
        self.base_url = os.getenv("CAMB_AI_BASE_URL", "https://api.camb.ai/apis")

    def get_target_languages(self):
        url = f"{self.base_url}/target_languages"
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()

    def create_tts(self, text, voice_id, language, gender, age):
        url = f"{self.base_url}/tts"
        data = {
            "text": text,
            "voice_id": voice_id,
            "language": language,
            "gender": gender,
            "age": age,
        }
        headers = {"x-api-key": self.api_key}
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_tts_status(self, task_id):
        url = f"{self.base_url}/tts/{task_id}"
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_tts_result(self, run_id):
        url = f"{self.base_url}/tts_result/{run_id}"
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        return response

    def create_voice(self, name, gender, age, file_path):
        url = f"{self.base_url}/create_custom_voice"
        headers = {"x-api-key": self.api_key}
        data = {"voice_name": name, "gender": gender, "age": age}
        files = {"file": open(file_path, "rb")}
        response = requests.post(url, headers=headers, data=data, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def list_voices(self):
        url = f"{self.base_url}/list_voices"
        headers = {"Accept": "application/json", "x-api-key": self.api_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(response.json())
            return response.json()
        else:
            response.raise_for_status()


# Initialize CambAI
camb_ai = CambAI()
