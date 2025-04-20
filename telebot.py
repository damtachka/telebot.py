import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from datetime import datetime

# ТВОЙ ТОКЕН
BOT_TOKEN = "7611120747:AAEykNg1YUGmHtDKkOlp_8qfmcaDhAS0ay0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_orders = {}

# === Клавиатуры ===
main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton("❔ Как это работает", callback_data="how_it_works")],
    [InlineKeyboardButton("⚖️ Обменять Robux", callback_data="exchange")],
    [InlineKeyboardButton("👔 Профиль", callback_data="profile")]
])

amount_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=str(i), callback_data=f"amount_{i}")]
    for i in [5, 10, 25, 35, 50, 100, 250, 500, 1000, 1500]
])

# === /start ===
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    msg = await message.answer("💬 Хей! Я 2XRBX, я помогу тебе получить большие суммы robux.")
    await asyncio.sleep(2)
    await msg.edit_text("❔ Как это работает\n\nВсе просто! Ты донатишь в нашего бота от 5 Robux до 1500, а бот увеличивает их на 2x и отправляет тебе.🧨")
    await asyncio.sleep(3)
    await msg.edit_text("Ну что❔😉", reply_markup=main_kb)

# === Как это работает ===
@dp.callback_query_handler(lambda c: c.data == "how_it_works")
async def how_it_works(callback: types.CallbackQuery):
    await callback.message.edit_text("❔ Как это работает\n\nВсе просто! Ты донатишь в нашего бота от 5 Robux до 1500, а бот увеличивает их на 2x и отправляет тебе.🧨", reply_markup=main_kb)

# === Обменять Robux ===
@dp.callback_query_handler(lambda c: c.data == "exchange")
async def exchange(callback: types.CallbackQuery):
    await callback.message.edit_text("Отличный выбор, выбери кол-во Robux и я удвою это на 2x.", reply_markup=amount_kb)

# === Выбор суммы ===
@dp.callback_query_handler(lambda c: c.data.startswith("amount_"))
async def choose_amount(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    # Сохраняем "заказ"
    order_id = len(user_orders.get(user_id, [])) + 1
    order = {
        "id": order_id,
        "amount": amount,
        "date": datetime.now().strftime("%d.%m.%y"),
        "status": "⏳ На модерации"
    }
    user_orders.setdefault(user_id, []).append(order)

    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🛒 Купить геймпасс", url="https://roblox.com"))  # Вставь ссылку на свой геймпасс
    await callback.message.edit_text("Хорошо, чтобы купить геймпасс нажми на кнопку.", reply_markup=kb)

    # Имитируем переход и проверку
    await asyncio.sleep(2)
    await bot.send_message(user_id, "Проверка…")
    await asyncio.sleep(2)
    await bot.send_message(user_id, "Отлично, проверка геймпасса и начисление Robux пойдут на модерацию. Ты можешь отслеживать это в своем профиле в пункте заказов.🛍️")

# === Профиль ===
@dp.callback_query_handler(lambda c: c.data == "profile")
async def profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "Пользователь"
    orders = user_orders.get(user_id, [])
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🏬 Мои заказы", callback_data="orders"))
    await callback.message.edit_text(f"👤 @{username}\nКоличество заказов: {len(orders)}", reply_markup=kb)

# === Мои заказы ===
@dp.callback_query_handler(lambda c: c.data == "orders")
async def show_orders(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    orders = user_orders.get(user_id, [])
    
    if not orders:
        await callback.message.edit_text("У тебя пока нет заказов.")
        return

    text = ""
    for o in orders:
        text += f"Заказ #{o['id']}\n{o['date']}\n{o['amount']} R$\n{o['status']}\n\n"

    await callback.message.edit_text(text)

    # "Анимация" ⏳ → ⌛️
    for _ in range(5):
        await asyncio.sleep(1)
        for o in user_orders[user_id]:
            if "⏳" in o["status"]:
                o["status"] = o["status"].replace("⏳", "⌛️")
            else:
                o["status"] = o["status"].replace("⌛️", "⏳")
        text = ""
        for o in orders:
            text += f"Заказ #{o['id']}\n{o['date']}\n{o['amount']} R$\n{o['status']}\n\n"
        await callback.message.edit_text(text)

# === Запуск ===
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
