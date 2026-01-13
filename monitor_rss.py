#!/usr/bin/env python3
"""
GR Bill Tracker v2.1 - УМНЫЙ мониторинг + SECRETS
🔥 ВНЕСЁН → ➡️ Стадия → 🔔 События
"""

import asyncio
import feedparser
import json
import os
from datetime import datetime
import telegram
from telegram import Bot
import os

# Конфигурация из SECRETS
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN и CHAT_ID в secrets!")

STATE_FILE = ".bill_status.json"  # В Git!
BILLS_FILE = "bills.txt"

bot = Bot(token=TELEGRAM_TOKEN)

def load_bills():
    """Загрузить RSS из bills.txt"""
    if not os.path.exists(BILLS_FILE):
        return []
    with open(BILLS_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def load_state():
    """Загрузить статус законопроектов"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_state(state):
    """Сохранить статус"""
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

async def send_telegram(messages):
    """Отправить отчет"""
    report = "📊 <b>ОТЧЕТ МОНИТОРИНГА</b>\n\n"
    report += f"<i>{datetime.now().strftime('%d.%m.%Y %H:%M')}</i>\n\n"
    report += "\n".join(messages)
    
    await bot.send_message(chat_id=CHAT_ID, text=report, parse_mode='HTML')
    print("✅ Отчет отправлен!")

def check_rss():
    """УМНАЯ проверка с памятью стадий"""
    state = load_state()
    messages = []
    urls = load_bills()
    
    if not urls:
        messages.append("⚠️ bills.txt пустой!")
        return messages
    
    for url in urls:
        bill_num = url.split('/bill/')[1].split('/')[0]
        print(f"🔍 {bill_num}")
        
        feed = feedparser.parse(url)
        if not feed.entries:
            messages.append(f"📄 <b>{bill_num}</b>\n⚠️ Нет событий")
            continue
        
        # Текущая стадия и события
        latest = feed.entries[0]
        current_stage = latest.get('sozd_bill_stage', latest.get('title', 'Неизвестно'))[:50]
        event_count = len(feed.entries)
        
        # ПЕРВЫЙ запуск
        if bill_num not in state:
            title = latest.title[:100] + "..." if len(latest.title) > 100 else latest.title
            messages.append(f"🔥 <b>{bill_num}</b> ВНЕСЁН!\n"
                          f"📋 Стадия: {current_stage}\n"
                          f"📄 {title}")
            state[bill_num] = {"stage": current_stage, "events": event_count, "first_seen": datetime.now().isoformat()}
        
        # ИЗМЕНЕНИЯ
        else:
            prev = state[bill_num]
            
            # Новая стадия
            if current_stage != prev["stage"]:
                messages.append(f"➡️ <b>{bill_num}</b>\n"
                              f"Стадия: {current_stage} ← {prev['stage']}")
                state[bill_num]["stage"] = current_stage
            
            # Новые события
            if event_count > prev["events"]:
                new_events = event_count - prev["events"]
                messages.append(f"🔔 <b>{bill_num}</b>\n"
                              f"+{new_events} новых событий ({event_count} всего)")
                state[bill_num]["events"] = event_count
        
        # СТАБИЛЬНО
        else:
            messages.append(f"📄 <b>{bill_num}</b>\n✅ Без изменений")
    
    save_state(state)
    return messages

async def main():
    print("🚀 GR Bill Tracker v2.1 (SECURE)")
    messages = check_rss()
    if messages:
        await send_telegram(messages)
    else:
        print("ℹ️ Нет законопроектов для проверки")

if __name__ == "__main__":
    asyncio.run(main())
