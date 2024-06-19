import logging
import os
import openai
from openai import OpenAI
from aiogram import Bot, Dispatcher, types
from aiogram.types import *
from aiogram.filters import Command
from config import settings
import asyncio

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.telegram_token)
dp = Dispatcher()

openai.api_key = settings.openai_api_key

client = OpenAI(api_key=settings.openai_api_key)

async def transcribe_voice(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="json"
        )
    return transcript.text

async def generate_response(text):
    try:
        assistant = client.beta.assistants.create(
            name="Assistant",
            instructions="Ответь кратко и понятно",
            model="gpt-4-1106-preview"
        )

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=text
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        while run.status in ["queued", "in_progress"]:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            await asyncio.sleep(0.5)

        messages = client.beta.threads.messages.list(thread_id=thread.id)

        assistant_response = None
        for message in messages.data:
            if message.role == 'assistant':
                assistant_response = message.content[0].text.value
                break

        return assistant_response

    except Exception as e:
        logging.error(f"Failed to generate response: {e}")
        return "Failed to generate a response. Please try again later."

async def synthesize_speech(text, file_path):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    new_path = file_path.replace(".ogg", "2.ogg")
    response.stream_to_file(new_path)
    return new_path

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")

@dp.message(lambda message: message.voice is not None)
async def handle_voice_message(message: types.Message):
    voice = message.voice
    file_path = f"downloads/{voice.file_id}.ogg"

    try:
        file = await bot.get_file(voice.file_id)
        await bot.download_file(file.file_path, file_path)

        transcription = await transcribe_voice(file_path)
        response_text = await generate_response(transcription)
        await message.answer(response_text)
        audio_file_path = await synthesize_speech(response_text, file_path)

        await message.answer_voice(types.FSInputFile(audio_file_path))

    except Exception as e:
        logging.error(f"Failed to process voice message: {e}")
        await message.answer("Failed to process the voice message. Please try again later.")

async def main():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
