import telebot
from telebot import types
import json
import os
from datetime import datetime, date, timedelta
import threading
import time
from flask import Flask

# ===== НАСТРОЙКИ (ЗАМЕНИ НА СВОИ!) =====
BOT_TOKEN = "8751228912:AAEnI38Jgcin65R1cbDU0kSbIslOgtAMcSs"  # Вставь токен от BotFather
CHAT_ID = "211062224"       # Вставь свой ID

# ===== СОЗДАЁМ ВЕБ-СЕРВЕР ДЛЯ RENDER =====
# Это нужно, чтобы Render не отключал бота
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

@app.route('/health')
def health():
    return "OK"

# ===== ИНИЦИАЛИЗИРУЕМ ТЕЛЕГРАМ-БОТА =====
bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения данных
DATA_FILE = "checkup_data_new.json"

# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ =====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== СОЗДАНИЕ КЛАВИАТУРЫ =====
def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("🌅 Подъём")
    btn2 = types.KeyboardButton("🏢 Приход на работу")
    btn3 = types.KeyboardButton("🚽 Стул")
    btn4 = types.KeyboardButton("🤕 Мигрень")
    btn5 = types.KeyboardButton("🌙 Отбой")
    btn6 = types.KeyboardButton("📊 Статистика за сегодня")
    btn7 = types.KeyboardButton("📅 Статистика за неделю")
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return keyboard

# ===== ВСЕ ОСТАЛЬНЫЕ ФУНКЦИИ БОТА =====
# ( data = load_data()
    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M")
    
    if today not in data:
        data[today] = {}
    
    # ===== ПОДЪЁМ =====
    if message.text == "🌅 Подъём":
        if "подъем" in data[today]:
            bot.send_message(message.chat.id, "❌ Подъём уже записан сегодня!")
            return
        
        data[today]["подъем"] = {
            "время": now,
            "текст": f"🌅 Подъём в {now}"
        }
        save_data(data)
        bot.send_message(
            message.chat.id,
            f"✅ Записано! 🌅 Подъём в {now}",
            reply_markup=get_main_keyboard()
        )
    
    # ===== ПРИХОД НА РАБОТУ =====
    elif message.text == "🏢 Приход на работу":
        if "приход" in data[today]:
            bot.send_message(message.chat.id, "❌ Приход на работу уже записан сегодня!")
            return
        
        data[today]["приход"] = {
            "время": now,
            "текст": f"🏢 Приход на работу в {now}"
        }
        save_data(data)
        bot.send_message(
            message.chat.id,
            f"✅ Записано! 🏢 Приход на работу в {now}",
            reply_markup=get_main_keyboard()
        )
    
    # ===== СТУЛ =====
    elif message.text == "🚽 Стул":
        # Создаём список для стула, если его нет
        if "ступ" not in data[today]:
            data[today]["ступ"] = []
        
        # Добавляем новый стул
        data[today]["ступ"].append({
            "время": now,
            "текст": f"🚽 Стул в {now}"
        })
        save_data(data)
        
        # Считаем сколько раз сегодня было
        count = len(data[today]["ступ"])
        bot.send_message(
            message.chat.id,
            f"✅ Записано! 🚽 Стул в {now} (сегодня {count} раз)",
            reply_markup=get_main_keyboard()
        )
    
    # ===== МИГРЕНЬ =====
    elif message.text == "🤕 Мигрень":
        # Создаём клавиатуру для выбора силы
        keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        btn1 = types.KeyboardButton("🤕 Слабая")
        btn2 = types.KeyboardButton("🤕 Средняя")
        btn3 = types.KeyboardButton("🤕 Сильная")
        btn4 = types.KeyboardButton("🔙 Назад")
        keyboard.add(btn1, btn2, btn3, btn4)
        
        msg = bot.send_message(
            message.chat.id,
            "Выбери силу мигрени:",
            reply_markup=keyboard
        )
        bot.register_next_step_handler(msg, process_migraine)
    
    # ===== ОТБОЙ =====
    elif message.text == "🌙 Отбой":
        if "отбой" in data[today]:
            bot.send_message(message.chat.id, "❌ Отбой уже записан сегодня!")
            return
        
        data[today]["отбой"] = {
            "время": now,
            "текст": f"🌙 Отбой в {now}"
        }
        save_data(data)
        bot.send_message(
            message.chat.id,
            f"✅ Записано! 🌙 Отбой в {now}",
            reply_markup=get_main_keyboard()
        )
    
    # ===== СТАТИСТИКА ЗА СЕГОДНЯ =====
    elif message.text == "📊 Статистика за сегодня":
        show_today_stats(message.chat.id)
    
    # ===== СТАТИСТИКА ЗА НЕДЕЛЮ =====
    elif message.text == "📅 Статистика за неделю":
        show_week_stats(message.chat.id)
    
    # ===== НАЗАД =====
    elif message.text == "🔙 Назад":
        bot.send_message(
            message.chat.id,
            "Главное меню:",
            reply_markup=get_main_keyboard()
        )

# ===== ОБРАБОТКА ВЫБОРА СИЛЫ МИГРЕНИ =====
def process_migraine(message):
    if str(message.chat.id) != CHAT_ID:
        return
    
    data = load_data()
    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M")
    
    if today not in data:
        data[today] = {}
    
    if "мигрень" not in data[today]:
        data[today]["мигрень"] = []
    
    # Сохраняем мигрень с указанием силы
    strength = message.text.replace("🤕 ", "")
    data[today]["мигрень"].append({
        "время": now,
        "сила": strength,
        "текст": f"🤕 Мигрень ({strength}) в {now}"
    })
    save_data(data)
    
    bot.send_message(
        message.chat.id,
        f"✅ Записано! 🤕 Мигрень ({strength}) в {now}",
        reply_markup=get_main_keyboard()
    )

# ===== СТАТИСТИКА ЗА СЕГОДНЯ =====
def show_today_stats(chat_id):
    data = load_data()
    today = date.today().isoformat()
    
    if today not in data or not data[today]:
        bot.send_message(chat_id, "📭 Сегодня пока нет записей.")
        return
    
    stats = f"📊 **Статистика за {today}**\n\n"
    
    # Подъём
    if "подъем" in data[today]:
        stats += f"{data[today]['подъем']['текст']}\n"
    
    # Приход
    if "приход" in data[today]:
        stats += f"{data[today]['приход']['текст']}\n"
    
    # Стул (может быть несколько)
    if "ступ" in data[today] and data[today]["ступ"]:
        for i, item in enumerate(data[today]["ступ"], 1):
            stats += f"{i}. {item['текст']}\n"
    
    # Мигрень (может быть несколько)
    if "мигрень" in data[today] and data[today]["мигрень"]:
        for item in data[today]["мигрень"]:
            stats += f"{item['текст']}\n"
    
    # Отбой
    if "отбой" in data[today]:
        stats += f"{data[today]['отбой']['текст']}\n"
    
    if stats == f"📊 **Статистика за {today}**\n\n":
        stats += "Нет записей"
    
    bot.send_message(chat_id, stats)

# ===== СТАТИСТИКА ЗА НЕДЕЛЮ =====
def show_week_stats(chat_id):
    data = load_data()
    response = "📅 **Статистика за неделю**\n\n"
    
    for i in range(7):
        day = (date.today() - timedelta(days=i)).isoformat()
        if day in data and data[day]:
            # Считаем количество записей за день
            count = 0
            day_data = data[day]
            
            if "подъем" in day_data: count += 1
            if "приход" in day_data: count += 1
            if "ступ" in day_data: count += len(day_data["ступ"])
            if "мигрень" in day_data: count += len(day_data["мигрень"])
            if "отбой" in day_data: count += 1
            
            response += f"📆 {day}: {count} записей\n"
        else:
            response += f"📆 {day}: нет данных\n"
    
    bot.send_message(chat_id, response)

# ===== КОМАНДА /STATS =====
@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    if str(message.chat.id) != CHAT_ID:
        return
    show_today_stats(message.chat.id)

# ===== КОМАНДА /WEEK =====
@bot.message_handler(commands=['week'])
def cmd_week(message):
    if str(message.chat.id) != CHAT_ID:
        return
    show_week_stats(message.chat.id)

# ===== ЕЖЕДНЕВНОЕ НАПОМИНАНИЕ В 8:00 =====
def send_daily_reminder():
    bot.send_message(
        CHAT_ID,
        "🌅 Доброе утро! Не забудь отметить свой день:\n"
        "• Подъём\n"
        "• Приход на работу\n"
        "• Стул (если будет)\n"
        "• Мигрень (если будет)\n"
        "• Отбой вечером\n\n"
        "Просто нажимай кнопки внизу! 👇",
        reply_markup=get_main_keyboard()
    )

def check_daily_reminder():
    now = datetime.now().strftime("%H:%M")
    if now == "08:00":
        send_daily_reminder()
        time.sleep(60)  # Ждём минуту, чтобы не дублировать

def run_reminder_scheduler():
    while True:
        check_daily_reminder()
        time.sleep(30)

# ===== ЗАПУСК БОТА =====
if __name__ == "__main__":
    print("🤖 Новый бот-чекап запускается...")
    print("✅ Бот работает! Напиши /start в Telegram")
    print("⚠️ Не закрывай это окно — бот работает только пока оно открыто!")
    
    # Запускаем планировщик напоминаний
    reminder_thread = threading.Thread(target=run_reminder_scheduler, daemon=True)
    reminder_thread.start()
    
    # Запускаем бота
    bot.infinity_polling())

# ===== ЗАПУСК БОТА В ОТДЕЛЬНОМ ПОТОКЕ =====
def run_bot():
    print("🤖 Бот запускается...")
    # Запускаем планировщик напоминаний
    reminder_thread = threading.Thread(target=run_reminder_scheduler, daemon=True)
    reminder_thread.start()
    # Запускаем бота
    def run_reminder_scheduler()

if __name__ == "__main__":
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем веб-сервер для Render
    print("✅ Веб-сервер запущен для Render")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))