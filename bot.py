import asyncio
import logging
import os
import shlex
import requests
from telegram import BotCommand, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from camb_ai import CambAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Initialize CambAI
camb_ai = CambAI()

# Temporary storage for uploaded files
uploaded_files = {}


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Hi! Use /createvoice <name> <gender> <age> to create a voice. Gender can be "m" for Male or "f" for Female. Then upload the reference file.'
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Help! Use /createvoice <name> <gender> <age> to create a voice. Gender can be "m" for Male or "f" for Female. Then upload the reference file.'
    )


async def create_voice_command(update: Update, context: CallbackContext) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            'Usage: /createvoice <name> <gender> <age>. Gender can be "m" for Male or "f" for Female.'
        )
        return

    name = args[0]
    gender_input = args[1].lower()
    age = int(args[2])

    if gender_input not in ["m", "f"]:
        await update.message.reply_text(
            'Invalid gender. Use "m" for Male or "f" for Female.'
        )
        return

    gender = 1 if gender_input == "m" else 2
    user_id = update.message.from_user.id

    uploaded_files[user_id] = {
        "name": name,
        "gender": gender,
        "age": age,
        "file_path": None,
    }
    await update.message.reply_text("Please upload the reference file now.")


async def handle_file_upload(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in uploaded_files:
        await update.message.reply_text("Please use the /createvoice command first.")
        return

    file = update.message.document or update.message.audio or update.message.voice
    if not file:
        await update.message.reply_text("Please upload a valid file.")
        return

    file = await file.get_file()  # Await this coroutine
    local_file_path = f"./{file.file_unique_id}.ogg"  # Construct the local file path

    await file.download_to_drive(
        local_file_path
    )  # Download the file to the local file path
    uploaded_files[user_id]["file_path"] = local_file_path

    name = uploaded_files[user_id]["name"]
    gender = uploaded_files[user_id]["gender"]
    age = uploaded_files[user_id]["age"]

    try:
        voice = camb_ai.create_voice(name, gender, age, local_file_path)
        await update.message.reply_text(
            f'Voice created successfully! Voice ID: {voice["voice_id"]}'
        )
        os.remove(local_file_path)  # Clean up the local file
    except Exception as e:
        logger.error(f"Error creating voice: {e}")
        await update.message.reply_text(
            "Failed to create voice. Please try again later."
        )


async def voice_command(update: Update, context: CallbackContext) -> None:
    # args = context.args
    args = shlex.split(update.message.text)
    if len(args) < 6:
        await update.message.reply_text(
            'Usage: /voice "<text>" <voice_id> <language> <gender> <age>'
        )
        return

    text = args[1]
    voice_id = int(args[2])
    language_id = int(args[3])
    gender_id = int(args[4])
    age = int(args[5])

    print("text", text)
    print("voice_id", voice_id)
    print("language_id", language_id)
    print("gender_id", gender_id)
    print("age", age)

    try:
        # Create TTS task
        response = camb_ai.create_tts(text, voice_id, language_id, gender_id, age)
        print("Create task response:", response)
        task_id = response["task_id"]

        await context.bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.RECORD_VOICE)

        # Check the task status every second until it's done
        while True:
            status_response = camb_ai.get_tts_status(task_id)
            if status_response["status"] == "SUCCESS":
                run_id = status_response["run_id"]
                print("STATUS RESPONSE", status_response)
                break
            await asyncio.sleep(1)

        # Fetch the TTS task result
        result_response = camb_ai.get_tts_result(run_id)
        
        audio_path = "voice_message.wav"
        with open(audio_path, "wb") as f:
            for chunk in result_response.iter_content(chunk_size=1024):
                f.write(chunk)

        # Send the audio file to the user
        with open(audio_path, "rb") as audio:
            await context.bot.send_voice(chat_id=update.message.chat_id, voice=audio)

        # Clean up the local file
        os.remove(audio_path)

    except Exception as e:
        logger.error(f"Error generating voice: {e}")
        await update.message.reply_text(
            "Failed to generate voice. Please try again later."
        )


async def list_voices_command(update: Update, context: CallbackContext) -> None:
    try:
        voices = camb_ai.list_voices()
        message = "Available Voices:\n"
        for voice in voices:
            message += f"ID: {voice['id']}, Name: {voice['voice_name']}\n"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error fetching voices: {e}")
        await update.message.reply_text(
            "Failed to fetch voices. Please try again later."
        )


async def list_languages_command(update: Update, context: CallbackContext) -> None:
    try:
        languages = camb_ai.get_target_languages()
        print(languages)
        message = "Available Languages:\n"
        for lang in languages:
            message += f"ID: {lang['id']}, Name: {lang['language']}\n"
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error fetching languages: {e}")
        await update.message.reply_text(
            "Failed to fetch languages. Please try again later."
        )


# async def set_bot_commands(application):
#     commands = [
#         BotCommand("start", "Start the bot"),
#         BotCommand("help", "Get help"),
#         BotCommand("createvoice", "Create a custom voice"),
#         BotCommand("voice", "Generate voice message"),
#         BotCommand("listvoices", "List available voices"),
#     ]
#     await application.bot.set_my_commands(commands)


def main():
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(telegram_bot_token).build()

    # await set_bot_commands(application)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("createvoice", create_voice_command))
    application.add_handler(CommandHandler("voice", voice_command))
    application.add_handler(CommandHandler("listvoices", list_voices_command))
    application.add_handler(CommandHandler("listlanguages", list_languages_command))

    application.add_handler(
        MessageHandler(
            filters.Document.ALL | filters.AUDIO | filters.VOICE,
            handle_file_upload,
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()
