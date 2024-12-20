from urllib.parse import urljoin
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import F
import asyncio
from bs4 import BeautifulSoup
import requests
import g4f

# Токен бота
API_TOKEN = '7527969470:AAHkLn8RnbPqn7HtH27VNtMKDB_6saPYcVw'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обработка команды /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Отправь мне ссылку на сайт, и я помогу тебе с навигацией по нему.")

# Обработка текстовых сообщений (ссылок)
@dp.message(F.text)
async def handle_link(message: Message):
    url = message.text.strip()

    # Проверка валидности URL
    if not url.startswith(('http://', 'https://')):
        await message.answer("Пожалуйста, отправьте корректную ссылку (начинающуюся с http:// или https://).")
        return

    await message.answer("Исследую сайт...")  # Сообщение о начале анализа

    try:
        # Получение HTML-кода сайта
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение заголовков и ссылок
        headers = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])]
        links = []
        for a in soup.find_all('a', href=True):
            link_text = a.get_text(strip=True)
            href = a['href']
            absolute_url = urljoin(url, href)  # Преобразование в абсолютный URL
            if absolute_url.startswith(('http://', 'https://')):
                links.append((link_text, absolute_url))

        # Проверка, найдены ли ссылки
        if not links:
            await message.answer("Не удалось найти ссылки на указанном сайте.")
            return

        # Генерация описания сайта через g4f
        description = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"Ты интерактивный бот помощник для телеграм, в ответе ты должен будешь возвращать помощь в навигации по сайту, ссылку на который тебе передадут, должен генерировать интерактивную навигацию. Ничего лишнего в ответ не пиши"},
                {"role": "user", "content": f"Анализируй следующий сайт: {url}. "}
            ]
        )

        # Проверка типа данных description
        if isinstance(description, dict):
            summary = description.get('choices', [{}])[0].get('message', {}).get('content', 'Описание недоступно.')
        elif isinstance(description, str):
            summary = description
        else:
            summary = "Описание недоступно."

        # Формирование кнопок навигации
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=text, url=link)] for text, link in links[:10]  # Ограничение количества кнопок
        ])

        # Ответ пользователю
        await message.answer(
            f"Вот основные ссылки с сайта:",
            reply_markup=keyboard
        )

    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке сайта: {e}")

# Запуск бота
async def main():
    print("Бот запущен!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()  # Корректное завершение работы бота
        print("Бот остановлен.")

if __name__ == '__main__':
    asyncio.run(main())
