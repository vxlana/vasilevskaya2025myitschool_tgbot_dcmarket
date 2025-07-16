import aiohttp
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import os

import asyncio
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State

from io import BytesIO

import config #Импорт файла config
import keyboard #Импорт файла config keyboard
import logging #Модуль для вывода информации


storage = MemoryStorage() # FSM
bot = Bot(token=config.botkey, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage) # хранилище состояний в оперативной памяти

logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.INFO,
                    )


# ================== ОБРАБОТЧИК КОМАНДЫ START ===================
@dp.message_handler(Command('start'), state=None) # задаем название команды start
async def welcome(message):
    joinedFile = open('user.txt', 'r') #
    joinedUsers = set()
    for line in joinedFile: # цикл в котором проверяем имеется ли такой id в файле user
        joinedUsers.add(line.strip())

    if not str(message.chat.id) in joinedUsers: # делаем запись в файл user нового id
        joinedFile = open('user.txt', 'a')
        joinedFile.write(str(message.chat.id) + '\n')
        joinedUsers.add(message.chat.id)

    await bot.send_message(message.chat.id, f'Добро пожаловать, * {message.from_user.first_name} *! Выбирай товары, следи за статусом заказов и будь в тренде вместе с нами!',
                           reply_markup=keyboard.start, parse_mode='Markdown')

# ===================== РЕЖИМ РАБОТЫ =====================

@dp.message_handler(lambda message: message.text == '🕒 Режим работы')
async def market_open_command(message: types.Message):
    await bot.send_message(message.from_user.id, 'Режим работы: Пн-Чт с 11:00 до 22:00, Пт-Вс с 10:00 до 23:00')

# ======================== АДРЕС =========================

@dp.message_handler(lambda message: message.text == '📍 Адрес')
async def market_place_command(message: types.Message):
    await bot.send_message(message.from_user.id, 'пр. Победителей, 115')
    await bot.send_location(message.from_user.id, latitude=53.936433, longitude=27.477624)


# ==================== Каталог товаров ====================

# Получение категорий
async def get_categories():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:8000/api/categories/') as resp:
            return await resp.json()


# Получение товаров по категории
async def get_products(category_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://127.0.0.1:8000/api/clothing/category/{category_id}/') as resp:
            return await resp.json()


# Кнопка: Каталог товаров
@dp.message_handler(lambda message: message.text == 'Каталог товаров')
async def show_categories(message: types.Message):
    categories = await get_categories()

    keyboard = InlineKeyboardMarkup(row_width=1)
    for category in categories:
        keyboard.add(InlineKeyboardButton(category['name'], callback_data=f"category_{category['id']}"))

    await message.answer('Выберите категорию:', reply_markup=keyboard)


# Показ товаров
user_products = {}

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('category_'))
async def show_products(callback_query: types.CallbackQuery):
    category_id = int(callback_query.data.split('_')[1])
    products = await get_products(category_id)

    if products:
        user_products[callback_query.from_user.id] = {'products': products, 'index': 0}
        await send_product(callback_query.from_user.id)
    else:
        await bot.send_message(callback_query.from_user.id, 'В этой категории пока нет товаров.')




async def send_product(user_id):
    user_data = user_products[user_id]
    products = user_data['products']
    index = user_data['index']
    product = products[index]

    keyboard = InlineKeyboardMarkup()
    if index + 1 < len(products):
        keyboard.add(InlineKeyboardButton('Следующий товар', callback_data='next_product'))

    if product['image']:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(product['image']) as resp:
                    if resp.status == 200:
                        photo = BytesIO(await resp.read())
                        photo.name = 'image.jpg'
                        await bot.send_photo(user_id, photo=photo,
                            caption=f"{product['name']}\nЦена: {product['price']} $\nСкидка: {product['discount']}%\nЦена со скидкой: {product['price_with_discount']} $\n\n{product['description']}",
                            reply_markup=keyboard)
                    else:
                        await bot.send_message(user_id, f"Не удалось загрузить фото товара: {product['name']}")
        except Exception as e:
            await bot.send_message(user_id, f"Ошибка при отправке фото товара: {product['name']}\n{str(e)}")
    else:
        await bot.send_message(user_id, f"Фото для товара {product['name']} не найдено.")



@dp.callback_query_handler(lambda c: c.data == 'next_product')
async def next_product(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_products[user_id]['index'] += 1
    await send_product(user_id)

# ===============================================

@dp.message_handler()
async def echo_send(message: types.Message):
    await message.answer('Выберите действие из меню.')

# ===============================================

if __name__ == '__main__':
    print('Бот запущен')
    executor.start_polling(dp, skip_updates=True)

