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
        url = f"{self.base_url}/tts-result/{run_id}"
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        return response

    def create_custom_voice(self, file_path, voice_name, gender, age,
                            description=None, language=None,
                            is_published=False, enhance_audio=True):
        """
        Creates a custom voice clone from an audio sample

        Parameters:
            file_path (str): Path to the audio file containing the voice sample
            voice_name (str): Name to assign to the custom voice
            gender (int): Gender identifier (1=male, 2=female, etc.)
            age (int): Approximate age of the speaker
            description (str, optional): Detailed description of the voice
            language (str, optional): Language code of the voice (e.g., "en-US")
            is_published (bool, optional): Whether to make the voice publicly
                available
            enhance_audio (bool, optional): Whether to apply enhancement to the
                reference audio for better voice cloning accuracy.

        Returns:
            dict: Response from the API containing voice details
        """
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at: {file_path}")

        # Prepare file for upload
        files = {'file': open(file_path, 'rb')}

        # Prepare metadata
        data = {
            'voice_name': voice_name,
            'gender': gender,
            'age': age
        }

        # Add optional parameters if provided
        if description:
            data['description'] = description
        if language:
            data['language'] = language
        if is_published:
            data['is_published'] = is_published

        if enhance_audio:
            data["enhance_audio"] = enhance_audio

        try:
            # Make API request
            response = requests.post(
                f"{self.base_url}/create-custom-voice",
                files=files,
                data=data,
                headers={
                    "x-api-key": self.api_key
                }
            )

            # Close file handle
            files['file'].close()

            # Check for errors
            response.raise_for_status()

            # Return response data
            return response.json()

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            if response.text:
                print(f"Response details: {response.text}")
            return None
        except Exception as err:
            print(f"Error creating custom voice: {err}")
            return None
        finally:
            # Ensure file is closed even if an error occurs
            if 'file' in files and not files['file'].closed:
                files['file'].close()

    def list_voices(self):
        url = f"{self.base_url}/list-voices"
        headers = {"Accept": "application/json", "x-api-key": self.api_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(response.json())
            return response.json()
        else:
            response.raise_for_status()


# Initialize CambAI
camb_ai = CambAI()
