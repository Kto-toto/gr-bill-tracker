# main.py - Telegram бот для мониторинга законопроектов Госдумы
# Залейте на GitHub, настройте GitHub Actions для cron или запустите на VPS/Heroku

import os
import logging
import sqlite3
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Конфиг (используйте .env или secrets)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # YOUR_BOT_TOKEN от @BotFather
CHAT_ID = None  # Будет установлен автоматически

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = 'bills.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bills
                 (number TEXT PRIMARY KEY, title TEXT, last_date TEXT, stage_id TEXT, added_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT)''')
    conn.commit()
    conn.close()

def get_api_data(number):
    url = f"http://api.duma.gov.ru/api/search.json?number={number}"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get('laws'):
            bill = resp['laws'][0]
            latest = bill['lastEvent']
            return {
                'title': bill['name'],
                'last_date': latest['date'],
                'stage_name': latest['name'],
                'stage_id': latest['stage']['id']
            }
    except Exception as e:
        logger.error(f"API error for {number}: {e}")
    return None

def add_bill(user_id, number, title):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO bills VALUES (?, ?, ?, ?, ?)",
              (number, title, '1970-01-01', '', datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return f"✅ Добавлен законопроект: <b>{number}</b>\n📝 {title}"

def list_bills():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT number, title FROM bills")
    bills = c.fetchall()
    conn.close()
    if not bills:
        return "📭 База пуста. Добавьте законопроекты командой /add"
    msg = "📋 Ваши законопроекты:\n\n"
    for num, title in bills:
        msg += f"• {num}: {title}\n"
    return msg

def check_updates():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM bills")
    bills = c.fetchall()
    updates = []
    for bill in bills:
        number, title, saved_date, saved_stage, _ = bill
        data = get_api_data(number)
        if data and (data['last_date'] > saved_date or data['stage_id'] != saved_stage):
            change = f"{number}: {data['stage_name']} ({data['last_date']})"
            updates.append(change)
            # Обновить БД
            c.execute("UPDATE bills SET last_date=?, stage_id=? WHERE number=?",
                      (data['last_date'], data['stage_id'], number))
    conn.commit()
    conn.close()
    return updates

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    user = update.effective_user
    CHAT_ID = user.id
    # Сохранить пользователя
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", (user.id, user.username))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        "🚀 <b>GR Bill Tracker</b>\n\n"
        "Команды:\n"
        "/add 123456-8 Название - добавить законопроект\n"
        "/list - список\n"
        "/check - проверить обновления\n"
        "/help - помощь",
        parse_mode='HTML')

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Формат: /add НОМЕР Название")
        return
    number = context.args[0]
    title = ' '.join(context.args[1:])
    msg = add_bill(update.effective_user.id, number, title)
    await update.message.reply_text(msg, parse_mode='HTML')

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = list_bills()
    await update.message.reply_text(msg, parse_mode='HTML')

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    updates = check_updates()
    if updates:
        msg = "🔄 <b>Обновления:</b>\n\n" + '\n'.join(updates)
    else:
        msg = "✅ Нет обновлений"
    await update.message.reply_text(msg, parse_mode='HTML')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>Помощь:</b>\n"
        "• /add номер название - добавить\n"
        "• /list - просмотреть\n"
        "• /check - мониторинг\n"
        "Бот проверяет статусы по API Госдумы автоматически.[web:10]",
        parse_mode='HTML')

def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("help", help_cmd))
    
    logger.info("Бот запущен")
    app.run_polling()

if __name__ == '__main__':
    main()
