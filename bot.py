import logging
import os
import io
import aiohttp
import openai
from openai import OpenAI
from aiogram import Bot, Dispatcher, types
from aiogram.types import *
from aiogram.filters import Command
from config import settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=settings.telegram_token)
dp = Dispatcher()

# Настройка OpenAI API
openai.api_key = settings.openai_api_key


async def transcribe_voice(file_path):
    client = OpenAI(api_key=settings.openai_api_key)
    audio_file = open(file_path, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )
    return transcript


async def generate_response(text):
    try:
        client = OpenAI(
            api_key=settings.openai_api_key
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": text,
                }
            ],
            model="gpt-3.5-turbo",
        )
    except Exception as e:
        print(e)
    return chat_completion.choices[0].message.content


async def synthesize_speech(text, file_path):
    client = OpenAI(api_key=settings.openai_api_key)

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
        file_url = f"https://api.telegram.org/file/bot{settings.telegram_token}/{file.file_path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await resp.read())
                else:
                    logging.error(f"Failed to download file: {resp.status}")
                    await message.answer("Failed to download the voice message. Please try again later.")
                    return

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
    import asyncio

    asyncio.run(main())
