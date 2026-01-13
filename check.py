# check.py - Только мониторинг, без polling
import os
import sqlite3
import requests
from datetime import datetime
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')  # Добавьте в Secrets

bot = Bot(token=TELEGRAM_TOKEN)

DB_PATH = '/tmp/bills.db'  # Временная БД

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bills (number TEXT PRIMARY KEY, title TEXT, last_date TEXT, stage_id TEXT)''')
    conn.commit()
    conn.close()

def get_api_data(number):
    url = f"http://api.duma.gov.ru/api/search.json?number={number}"
    resp = requests.get(url, timeout=10).json()
    if resp.get('laws'):
        bill = resp['laws'][0]
        latest = bill['lastEvent']
        return {
            'last_date': latest['date'],
            'stage_name': latest['name'],
            'stage_id': latest['stage']['id']
        }
    return None

def check_bills():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM bills")
    bills = c.fetchall()
    
    updates = []
    for bill in bills:
        number, title, saved_date, saved_stage = bill[:4]
        data = get_api_data(number)
        if data and (data['last_date'] > saved_date or data['stage_id'] != saved_stage):
            updates.append(f"🔄 {number}: {data['stage_name']} ({data['last_date']})")
            c.execute("UPDATE bills SET last_date=?, stage_id=? WHERE number=?", 
                     (data['last_date'], data['stage_id'], number))
    conn.commit()
    conn.close()
    
    if updates:
        msg = "📋 <b>Обновления законопроектов:</b>\n\n" + "\n".join(updates)
        bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        print("✅ Уведомления отправлены")
    else:
        print("ℹ️ Нет обновлений")

if __name__ == "__main__":
    init_db()
    check_bills()
