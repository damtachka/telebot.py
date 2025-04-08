import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import sqlite3
from datetime import datetime, timedelta
import random

API_TOKEN = '8113509693:AAEGmIojIhyuIHxwdJpdq7xcpBaOLuujA_k'  # Твой Telegram Bot Token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Create a database connection
conn = sqlite3.connect('bot_database.db')
cursor = conn.cursor()

# Database schema setup
def setup_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        stars INTEGER,
                        xp INTEGER,
                        level INTEGER,
                        invites_count INTEGER,
                        premium BOOLEAN,
                        created_at TEXT,
                        last_daily_claim TEXT,
                        quest_refreshes_today INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS promo_codes (
                        code TEXT PRIMARY KEY,
                        creator_id INTEGER,
                        reward_user INTEGER,
                        reward_creator INTEGER,
                        activations INTEGER,
                        max_activations INTEGER,
                        expires_at TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_quests (
                        user_id INTEGER,
                        date TEXT,
                        quests TEXT,
                        refresh_count INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_achievements (
                        user_id INTEGER,
                        achievements TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_purchases (
                        user_id INTEGER,
                        item_id TEXT,
                        purchased_at TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
                        referrer_id INTEGER,
                        referred_id INTEGER,
                        reward_given BOOLEAN)''')
    conn.commit()

setup_db()

# Welcome message and inline buttons
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute('''INSERT INTO users (user_id, username, stars, xp, level, invites_count, premium, created_at, last_daily_claim, quest_refreshes_today)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (user_id, message.from_user.username, 0, 0, 1, 0, False, datetime.now().isoformat(), datetime.now().isoformat(), 0))
        conn.commit()

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton("⭐ Заработать", callback_data="earn_menu"),
                 InlineKeyboardButton("🎁 Ввести промокод", callback_data="enter_code"),
                 InlineKeyboardButton("📜 Квесты", callback_data="show_quests"),
                 InlineKeyboardButton("🏆 Ачивки", callback_data="show_achievements"),
                 InlineKeyboardButton("🛒 Магазин", callback_data="shop_menu"),
                 InlineKeyboardButton("📈 Уровень", callback_data="show_level"),
                 InlineKeyboardButton("👥 Пригласить", callback_data="invite_menu"),
                 InlineKeyboardButton("⚙️ Настройки", callback_data="settings_menu"))
    await message.answer(f"Привет, {message.from_user.first_name}!\nЗарабатывай звёзды, вводи промокоды, выполняй квесты, достигай уровней и попади в топ!", reply_markup=keyboard)

# Handle button presses
@dp.callback_query_handler(lambda c: c.data == 'earn_menu')
async def earn_menu(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("🔁 Ежедневный бонус", callback_data="daily_bonus"),
                 InlineKeyboardButton("💡 Выполнить квесты", callback_data="show_quests"),
                 InlineKeyboardButton("📨 Пригласить друзей", callback_data="invite_menu"),
                 InlineKeyboardButton("🔓 Создать свой промокод", callback_data="create_promo"),
                 InlineKeyboardButton("⬅️ Назад", callback_data="start"))
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Как ты хочешь заработать звёзды?", reply_markup=keyboard)

# Handle daily bonus
@dp.callback_query_handler(lambda c: c.data == 'daily_bonus')
async def daily_bonus(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    last_claim_time = datetime.fromisoformat(user[8])
    if datetime.now() - last_claim_time < timedelta(days=1):
        await bot.answer_callback_query(callback_query.id, "Ты уже забирал бонус сегодня.", show_alert=True)
        return

    stars_earned = 50  # Example reward
    cursor.execute('UPDATE users SET stars = stars + ?, last_daily_claim = ? WHERE user_id = ?', (stars_earned, datetime.now().isoformat(), user_id))
    conn.commit()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(user_id, f"Ты получил {stars_earned} звёзд за ежедневный бонус!")

# Handle entering promo code
@dp.callback_query_handler(lambda c: c.data == 'enter_code')
async def enter_code(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Отправь мне промокод одним сообщением.")

# Handle quest menu
@dp.callback_query_handler(lambda c: c.data == 'show_quests')
async def show_quests(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    cursor.execute('SELECT * FROM user_quests WHERE user_id = ? AND date = ?', (user_id, datetime.now().date()))
    user_quests = cursor.fetchone()

    if user_quests:
        quests = eval(user_quests[2])
    else:
        quests = []

    quest_text = "Твои активные квесты:\n"
    for quest in quests:
        quest_text += f"- {quest['type']} {quest['progress']}/{quest['goal']} ({'Завершён' if quest['completed'] else 'Не завершён'})\n"
    quest_text += "\nОбновить квесты (первый раз бесплатно):"
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, quest_text)

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
