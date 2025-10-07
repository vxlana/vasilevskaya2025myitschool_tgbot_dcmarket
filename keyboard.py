from aiogram import Bot, types
from aiogram.types import (ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
                           InlineKeyboardButton)

b1 = KeyboardButton('🕒 Режим работы')
b2 = KeyboardButton('📍 Адрес')
b3 = KeyboardButton('Каталог товаров')

start = ReplyKeyboardMarkup(resize_keyboard=True)
start.add(b1, b2).add(b3)