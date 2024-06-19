import logging
import os
from openai import AsyncClient
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import settings
from functions import *

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.telegram_token)
dp = Dispatcher()

async_client = AsyncClient(api_key=settings.openai_api_key)


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

        transcription = await transcribe_voice(async_client, file_path)
        response_text = await generate_response(async_client, transcription)
        await message.answer(response_text)
        audio_file_path = await synthesize_speech(async_client, response_text, file_path)

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
