import aiogram




bot = aiogram.Bot(token=TOKEN)
dp = aiogram.Dispatcher(bot)

async def on_startup(dp):
    print('Бот вышел в онлайн')

